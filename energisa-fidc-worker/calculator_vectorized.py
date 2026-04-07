"""
FIDC Financial Calculator — Vetorizado (Pandas / NumPy)

Porta fiel de toda a lógica dos serviços TypeScript, reescrita para
operar sobre DataFrames inteiros em vez de linha-a-linha.

Ganho típico para 500 k linhas: de ~120 s (loop Python) → ~2-4 s.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional

# ─── Tabelas de referência ────────────────────────────────────────────

AGING_TAXA_MAP: dict[str, str] = {
    "A vencer":            "A vencer",
    "Menor que 30 dias":   "Primeiro ano",
    "De 31 a 59 dias":     "Primeiro ano",
    "De 60 a 89 dias":     "Primeiro ano",
    "De 90 a 119 dias":    "Primeiro ano",
    "De 120 a 359 dias":   "Primeiro ano",
    "De 360 a 719 dias":   "Segundo ano",
    "De 720 a 1080 dias":  "Terceiro ano",
    "Maior que 1080 dias": "Demais anos",
}

REMUNERATION_DISCOUNTS: dict[str, float] = {
    "A vencer":            0.065,
    "Menor que 30 dias":   0.065,
    "De 31 a 59 dias":     0.065,
    "De 60 a 89 dias":     0.065,
    "De 90 a 119 dias":    0.08,
    "De 120 a 359 dias":   0.15,
    "De 360 a 719 dias":   0.22,
    "De 720 a 1080 dias":  0.36,
    "Maior que 1080 dias": 0.50,
}

VOLTZ_DEFAULT_RATES: dict[str, dict] = {
    "A vencer":     {"taxa": 0.98, "prazo": 6},
    "Primeiro ano": {"taxa": 0.90, "prazo": 6},
    "Segundo ano":  {"taxa": 0.75, "prazo": 12},
    "Terceiro ano": {"taxa": 0.60, "prazo": 18},
    "Quarto ano":   {"taxa": 0.45, "prazo": 24},
    "Quinto ano":   {"taxa": 0.30, "prazo": 30},
    "Demais anos":  {"taxa": 0.15, "prazo": 36},
}

# pd.cut bins e labels — right=True significa (left, right]
# (-inf, 0]  → A vencer   (dias_atraso ≤ 0, não vencido)
# (0, 30]    → Menor que 30 dias
# ...
AGING_BINS: list[float] = [-np.inf, 0, 30, 59, 89, 119, 359, 719, 1080, np.inf]
AGING_LABELS: list[str] = [
    "A vencer",
    "Menor que 30 dias",
    "De 31 a 59 dias",
    "De 60 a 89 dias",
    "De 90 a 119 dias",
    "De 120 a 359 dias",
    "De 360 a 719 dias",
    "De 720 a 1080 dias",
    "Maior que 1080 dias",
]

# ─── Escalares compartilhados ─────────────────────────────────────────

def get_ipca_monthly(indices: list[dict]) -> float:
    """Taxa IPCA mensal com base nos últimos 13 pontos da série."""
    if len(indices) < 13:
        return 0.004  # fallback ~5% a.a.
    sorted_idx = sorted(indices, key=lambda x: str(x["date"]))
    current = float(sorted_idx[-1]["value"])
    prev12  = float(sorted_idx[-13]["value"])
    if prev12 <= 0:
        return 0.004
    return (1 + (current / prev12 - 1)) ** (1 / 12) - 1


def get_di_pre_rate(rates: list[dict], horizonte: int) -> float:
    """Taxa DI-PRE anual (252 d.u.) para o prazo mais próximo."""
    if not rates:
        return 0.12
    match = next((r for r in rates if int(r["meses_futuros"]) == horizonte), None)
    if match:
        return float(match["taxa_252"]) / 100
    closest = min(rates, key=lambda r: abs(int(r["meses_futuros"]) - horizonte))
    return float(closest["taxa_252"]) / 100


# ─── Lookup vetorizado de índices econômicos ──────────────────────────

def _build_index_df(indices: list[dict]) -> Optional[pd.DataFrame]:
    if not indices:
        return None
    df = pd.DataFrame(indices)
    df["date"]  = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = df["value"].astype(float)
    return df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)


def _lookup_index_values(dates: pd.Series, idx_df: pd.DataFrame) -> np.ndarray:
    """
    Para cada data em `dates`, encontra o valor mais próximo em `idx_df`
    usando merge_asof (O(n log n), totalmente vetorizado).
    Retorna array float de mesmo comprimento que `dates`.
    """
    dates_ts = pd.to_datetime(dates, errors="coerce")
    nat_mask  = dates_ts.isna().values

    dates_filled = dates_ts.fillna(pd.Timestamp("2000-01-01"))

    # merge_asof exige ambos ordenados pela chave
    temp = pd.DataFrame({
        "date":      dates_filled.values,
        "_orig_pos": np.arange(len(dates_filled), dtype=np.intp),
    }).sort_values("date")

    merged = pd.merge_asof(
        temp,
        idx_df[["date", "value"]],
        on="date",
        direction="nearest",
    )

    # Restaura ordem original
    result = merged.sort_values("_orig_pos")["value"].to_numpy(dtype=float)
    result[nat_mask] = 1.0   # datas inválidas → fator neutro
    return result


# ─── Lookup vetorizado de taxas de recuperação ───────────────────────

def _build_rates_df(recovery_rates: list[dict]) -> pd.DataFrame:
    if not recovery_rates:
        return pd.DataFrame(
            columns=["empresa", "tipo", "aging", "taxa_recuperacao", "prazo_recebimento"]
        )
    df = pd.DataFrame(recovery_rates)
    df["_emp"] = df["empresa"].str.upper()
    df["_tip"] = df["tipo"].str.lower()
    df["taxa_recuperacao"]  = df["taxa_recuperacao"].astype(float)
    df["prazo_recebimento"] = df["prazo_recebimento"].astype(int)
    return df


def _apply_recovery_rates(df: pd.DataFrame, rates_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge vetorizado de taxas de recuperação com dois níveis de fallback:
      1. empresa + tipo + aging_taxa (exato)
      2. empresa + aging_taxa (qualquer tipo)
      3. VOLTZ defaults para linhas is_voltz=True
    """
    df = df.copy()
    df["_emp"] = df["empresa"].str.upper()
    df["_tip"] = df["tipo"].str.lower()

    if not rates_df.empty:
        # Nível 1 — match exato
        exact = rates_df[["_emp", "_tip", "aging", "taxa_recuperacao", "prazo_recebimento"]].rename(
            columns={"aging": "aging_taxa", "taxa_recuperacao": "_te", "prazo_recebimento": "_pe"}
        )
        df = df.merge(exact, on=["_emp", "_tip", "aging_taxa"], how="left")

        # Nível 2 — fallback por empresa (qualquer tipo), primeiro registro
        fallback = (
            rates_df.sort_values(["_emp", "aging"])
            .groupby(["_emp", "aging"], as_index=False)
            .first()[["_emp", "aging", "taxa_recuperacao", "prazo_recebimento"]]
            .rename(columns={
                "aging":           "aging_taxa",
                "taxa_recuperacao": "_tf",
                "prazo_recebimento": "_pf",
            })
        )
        df = df.merge(fallback, on=["_emp", "aging_taxa"], how="left")

        no_exact = df["_te"].isna()
        df.loc[no_exact, "_te"] = df.loc[no_exact, "_tf"]
        df.loc[no_exact, "_pe"] = df.loc[no_exact, "_pf"]
    else:
        df["_te"] = np.nan
        df["_pe"] = np.nan

    # VOLTZ defaults — merge por aging_taxa
    voltz_df = pd.DataFrame([
        {"aging_taxa": k, "_tv": v["taxa"], "_pv": v["prazo"]}
        for k, v in VOLTZ_DEFAULT_RATES.items()
    ])
    df = df.merge(voltz_df, on="aging_taxa", how="left")

    is_voltz = df["is_voltz"].fillna(False).astype(bool)
    df["taxa_recuperacao"]  = np.where(is_voltz, df["_tv"],          df["_te"].fillna(0.0)).astype(float)
    df["prazo_recebimento"] = np.where(is_voltz, df["_pv"].fillna(6), df["_pe"].fillna(6)).astype(int)

    # Remove colunas temporárias
    tmp_cols = [c for c in df.columns if c.startswith("_")]
    return df.drop(columns=tmp_cols, errors="ignore")


# ─── Cálculo principal vetorizado ────────────────────────────────────

def calculate_vectorized(
    df: pd.DataFrame,
    indices:        list[dict],
    recovery_rates: list[dict],
    di_pre_rates:   list[dict],
    spread_percent:  float = 0.025,
    prazo_horizonte: int   = 6,
) -> pd.DataFrame:
    """
    Aplica todo o pipeline de cálculo FIDC sobre um DataFrame completo.

    Entrada : colunas brutas de fidc_session_data
    Saída   : mesmo DataFrame + todas as colunas calculadas
    """
    df = df.copy()

    # ── Escalares compartilhados ────────────────────────────────────
    ipca_monthly        = get_ipca_monthly(indices)
    di_pre_anual        = get_di_pre_rate(di_pre_rates, prazo_horizonte)
    taxa_di_pre_total   = (1 + di_pre_anual) * (1 + spread_percent) - 1
    taxa_desconto_mensal = (1 + taxa_di_pre_total) ** (1 / 12) - 1

    # ── Parse de datas ──────────────────────────────────────────────
    dt_venc = pd.to_datetime(df["data_vencimento"], errors="coerce")
    dt_base = pd.to_datetime(df["data_base"],       errors="coerce")

    # ── Aging (vetorizado com pd.cut) ───────────────────────────────
    dias = (dt_base - dt_venc).dt.days.fillna(0).astype(int)
    df["dias_atraso"] = dias

    df["aging"] = pd.cut(
        dias, bins=AGING_BINS, labels=AGING_LABELS, right=True
    ).astype(str)
    df["aging_taxa"] = df["aging"].map(AGING_TAXA_MAP).fillna("Demais anos")

    is_overdue = dias > 0
    is_voltz   = (
        df["is_voltz"].fillna(False).astype(bool)
        | df["empresa"].str.upper().eq("VOLTZ")
    )
    df["is_voltz"] = is_voltz  # normaliza a coluna

    # ── Valores base ────────────────────────────────────────────────
    vp   = df["valor_principal"].fillna(0).astype(float)
    vnc  = df["valor_nao_cedido"].fillna(0).astype(float)
    vt   = df["valor_terceiro"].fillna(0).astype(float)
    vcip = df["valor_cip"].fillna(0).astype(float)

    # ── Fator de correção (lookup vetorizado) ───────────────────────
    idx_df = _build_index_df(indices)
    if idx_df is not None and is_overdue.any():
        arr_base = _lookup_index_values(dt_base, idx_df)
        arr_venc = _lookup_index_values(dt_venc, idx_df)
        arr_venc_safe = np.where(arr_venc > 0, arr_venc, 1.0)
        fator_raw = np.where(is_overdue, arr_base / arr_venc_safe, 1.0)
    else:
        fator_raw = np.ones(len(df))

    df["fator_correcao"] = fator_raw

    # ── Correção monetária — distribuidoras padrão ──────────────────
    vl_std    = np.maximum(vp - vnc - vt - vcip, 0.0)
    multa_std = np.where(is_overdue, vl_std * 0.02, 0.0)
    jm_std    = np.where(is_overdue, vl_std * 0.01 * (dias / 30), 0.0)
    cm_std    = np.where(is_overdue, np.maximum(vl_std * (fator_raw - 1), 0.0), 0.0)
    vc_std    = vl_std + multa_std + jm_std + cm_std

    # ── Correção monetária — VOLTZ ──────────────────────────────────
    jr_v  = vp * 0.0465
    sdv   = vp + jr_v
    cm_v  = np.where(is_overdue, np.maximum(sdv * (fator_raw - 1), 0.0), 0.0)
    sc_ig = sdv + cm_v
    multa_v = np.where(is_overdue, sdv * 0.02, 0.0)
    meses_v = dias / 30.44
    jm_v    = np.where(is_overdue, sdv * ((1.01 ** meses_v) - 1), 0.0)
    vc_v    = sc_ig + multa_v + jm_v

    # ── Merge baseado em is_voltz ───────────────────────────────────
    df["valor_liquido"]            = np.where(is_voltz, vp,      vl_std)
    df["multa"]                    = np.where(is_voltz, multa_v, multa_std)
    df["juros_moratorios"]         = np.where(is_voltz, jm_v,    jm_std)
    df["correcao_monetaria"]       = np.where(is_voltz, cm_v,    cm_std)
    df["valor_corrigido"]          = np.where(is_voltz, vc_v,    vc_std)
    df["juros_remuneratorios"]     = np.where(is_voltz, jr_v,    np.nan)
    df["saldo_devedor_vencimento"] = np.where(is_voltz, sdv,     np.nan)

    # ── Taxas de recuperação (merge vetorizado) ─────────────────────
    rates_df = _build_rates_df(recovery_rates)
    df = _apply_recovery_rates(df, rates_df)

    # ── Valor justo (vetorizado) ────────────────────────────────────
    prazo_rec = df["prazo_recebimento"].astype(float)
    taxa_rec  = df["taxa_recuperacao"].astype(float)
    vc        = df["valor_corrigido"].astype(float)

    df["valor_recuperavel"] = vc * taxa_rec

    fc_receb   = (1 + ipca_monthly) ** prazo_rec
    mora       = prazo_rec * 0.01
    fator_desc = (1 + taxa_desconto_mensal) ** prazo_rec

    vj_bruto = np.where(
        fator_desc > 0,
        (vc * taxa_rec * (fc_receb + mora)) / fator_desc,
        0.0,
    )
    desconto_aging = df["aging"].map(REMUNERATION_DISCOUNTS).fillna(0.50).astype(float)
    df["valor_justo"] = vj_bruto * (1 - desconto_aging)

    return df


# ─── Summary computation ──────────────────────────────────────────────

def compute_summary(df: pd.DataFrame) -> dict:
    """
    Computa o resumo estatístico do DataFrame resultado para os cards do frontend.
    Retorna estrutura compatível com FidcSummary do TypeScript.
    """

    def _safe_sum(col: str) -> float:
        return float(df[col].fillna(0).sum()) if col in df.columns else 0.0

    # ── By aging ────────────────────────────────────────────────────
    by_aging: dict = {}
    if "aging" in df.columns:
        for aging_val, grp in df.groupby("aging", sort=False):
            by_aging[str(aging_val)] = {
                "count":           int(len(grp)),
                "valor_principal": float(grp["valor_principal"].fillna(0).sum()),
                "valor_corrigido": float(grp["valor_corrigido"].fillna(0).sum()),
                "valor_justo":     float(grp["valor_justo"].fillna(0).sum()),
            }

    # ── By empresa ──────────────────────────────────────────────────
    by_empresa: dict = {}
    if "empresa" in df.columns:
        for emp_val, grp in df.groupby("empresa", sort=False):
            by_empresa[str(emp_val)] = {
                "count":           int(len(grp)),
                "valor_principal": float(grp["valor_principal"].fillna(0).sum()),
                "valor_corrigido": float(grp["valor_corrigido"].fillna(0).sum()),
                "valor_justo":     float(grp["valor_justo"].fillna(0).sum()),
            }

    return {
        "total_rows":               int(len(df)),
        "total_valor_principal":    _safe_sum("valor_principal"),
        "total_valor_liquido":      _safe_sum("valor_liquido"),
        "total_multa":              _safe_sum("multa"),
        "total_juros_moratorios":   _safe_sum("juros_moratorios"),
        "total_correcao_monetaria": _safe_sum("correcao_monetaria"),
        "total_valor_corrigido":    _safe_sum("valor_corrigido"),
        "total_valor_recuperavel":  _safe_sum("valor_recuperavel"),
        "total_valor_justo":        _safe_sum("valor_justo"),
        "by_aging":                 by_aging,
        "by_empresa":               by_empresa,
    }
