"""
FIDC Financial Calculator
Porta fiel da lógica TypeScript dos serviços:
  - aging-calculator.service.ts
  - correction-calculator.service.ts
  - fair-value-calculator.service.ts
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
import math

# ─── Tabelas de referência ────────────────────────────────────────

AGING_BUCKETS: list[tuple[str, int | None]] = [
    ("A vencer",           0),
    ("Menor que 30 dias",  30),
    ("De 31 a 59 dias",    59),
    ("De 60 a 89 dias",    89),
    ("De 90 a 119 dias",   119),
    ("De 120 a 359 dias",  359),
    ("De 360 a 719 dias",  719),
    ("De 720 a 1080 dias", 1080),
    ("Maior que 1080 dias", None),
]

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

# ─── Helpers de data ──────────────────────────────────────────────

def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s)[:10]).date()
    except Exception:
        return None


def calc_dias_atraso(data_vencimento: Optional[str], data_base: Optional[str]) -> int:
    venc = _parse_date(data_vencimento)
    base = _parse_date(data_base)
    if not venc or not base:
        return 0
    return (base - venc).days


# ─── Aging ────────────────────────────────────────────────────────

def classify_aging(dias: int) -> str:
    for bucket, limit in AGING_BUCKETS:
        if limit is None or dias <= limit:
            return bucket
    return "Maior que 1080 dias"


# ─── Índices econômicos ───────────────────────────────────────────

def find_index_value(indices: list[dict], date_str: Optional[str]) -> float:
    if not indices or not date_str:
        return 1.0
    target = _parse_date(date_str)
    if not target:
        return 1.0
    closest = min(
        indices,
        key=lambda x: abs((_parse_date(x["date"]) or target) - target),
    )
    return float(closest["value"])


def get_ipca_monthly(indices: list[dict]) -> float:
    """Calcula taxa IPCA mensal com base nos últimos 13 pontos da série."""
    if len(indices) < 13:
        return 0.004  # fallback ~5% a.a.
    sorted_idx = sorted(indices, key=lambda x: str(x["date"]))
    current = float(sorted_idx[-1]["value"])
    prev12  = float(sorted_idx[-13]["value"])
    if prev12 <= 0:
        return 0.004
    return (1 + (current / prev12 - 1)) ** (1 / 12) - 1


def get_di_pre_rate(rates: list[dict], horizonte: int) -> float:
    """Retorna taxa DI-PRE anual (252 d.u.) para o prazo mais próximo."""
    if not rates:
        return 0.12
    match = next((r for r in rates if int(r["meses_futuros"]) == horizonte), None)
    if match:
        return float(match["taxa_252"]) / 100
    closest = min(rates, key=lambda r: abs(int(r["meses_futuros"]) - horizonte))
    return float(closest["taxa_252"]) / 100


# ─── Taxa de recuperação ──────────────────────────────────────────

def find_recovery_rate(
    rates: list[dict],
    empresa: str,
    tipo: str,
    aging_taxa: str,
    is_voltz: bool,
) -> dict:
    if is_voltz:
        return VOLTZ_DEFAULT_RATES.get(aging_taxa, {"taxa": 0.15, "prazo": 36})

    match = next(
        (
            r for r in rates
            if r["empresa"].upper() == empresa.upper()
            and r["tipo"].lower() == tipo.lower()
            and r["aging"] == aging_taxa
        ),
        None,
    )
    if match:
        return {
            "taxa": float(match["taxa_recuperacao"]),
            "prazo": int(match["prazo_recebimento"]),
        }

    # fallback: mesma empresa, qualquer tipo
    fallback = next(
        (r for r in rates
         if r["empresa"].upper() == empresa.upper() and r["aging"] == aging_taxa),
        None,
    )
    if fallback:
        return {
            "taxa": float(fallback["taxa_recuperacao"]),
            "prazo": int(fallback["prazo_recebimento"]),
        }

    return {"taxa": 0.0, "prazo": 6}


# ─── Cálculo principal por linha ─────────────────────────────────

def calculate_row(
    row: dict,
    indices: list[dict],
    recovery_rates: list[dict],
    di_pre_rates: list[dict],
    spread_percent: float = 0.025,
    prazo_horizonte: int = 6,
    ipca_monthly: Optional[float] = None,
    taxa_desconto_mensal: Optional[float] = None,
) -> dict:
    """
    Calcula todos os valores derivados para uma linha bruta do DB.
    Retorna um dict com todos os campos originais + calculados.
    """
    empresa = str(row.get("empresa") or "")
    tipo    = str(row.get("tipo")    or "")
    is_voltz = bool(row.get("is_voltz", False)) or empresa.upper() == "VOLTZ"

    data_vencimento = row.get("data_vencimento")
    data_base       = row.get("data_base")

    # ── Aging ──────────────────────────────────────────────────────
    dias_atraso = calc_dias_atraso(data_vencimento, data_base)
    aging       = classify_aging(dias_atraso)
    aging_taxa  = AGING_TAXA_MAP[aging]
    is_overdue  = dias_atraso > 0

    # ── Valores base ───────────────────────────────────────────────
    vp   = float(row.get("valor_principal",  0) or 0)
    vnc  = float(row.get("valor_nao_cedido", 0) or 0)
    vt   = float(row.get("valor_terceiro",   0) or 0)
    vcip = float(row.get("valor_cip",        0) or 0)

    juros_remuneratorios = None
    saldo_devedor_vencimento = None

    # ── Correção monetária ─────────────────────────────────────────
    if is_voltz:
        # VOLTZ: sem deduções, juros remuneratórios de 4,65%, mora composta
        taxa_jr = 0.0465
        valor_liquido = vp
        juros_remuneratorios = valor_liquido * taxa_jr
        sdv = valor_liquido + juros_remuneratorios
        saldo_devedor_vencimento = sdv

        fator_correcao    = 1.0
        correcao_monetaria = 0.0
        if is_overdue and indices:
            idx_base = find_index_value(indices, data_base)
            idx_venc = find_index_value(indices, data_vencimento)
            fator_correcao = idx_base / idx_venc if idx_venc > 0 else 1.0
            correcao_monetaria = max(sdv * (fator_correcao - 1), 0.0)

        saldo_corrigido = sdv + correcao_monetaria
        multa = sdv * 0.02 if is_overdue else 0.0
        meses = dias_atraso / 30.44
        juros_moratorios = sdv * ((1.01 ** meses) - 1) if is_overdue else 0.0
        valor_corrigido  = saldo_corrigido + multa + juros_moratorios

    else:
        # Distribuidoras padrão
        valor_liquido      = max(vp - vnc - vt - vcip, 0.0)
        multa              = valor_liquido * 0.02 if is_overdue else 0.0
        meses_atraso       = dias_atraso / 30
        juros_moratorios   = valor_liquido * 0.01 * meses_atraso if is_overdue else 0.0

        fator_correcao     = 1.0
        correcao_monetaria = 0.0
        if is_overdue and indices:
            idx_base = find_index_value(indices, data_base)
            idx_venc = find_index_value(indices, data_vencimento)
            fator_correcao = idx_base / idx_venc if idx_venc > 0 else 1.0
            correcao_monetaria = max(valor_liquido * (fator_correcao - 1), 0.0)

        valor_corrigido = valor_liquido + multa + juros_moratorios + correcao_monetaria

    # ── Valor Justo ────────────────────────────────────────────────
    if ipca_monthly is None:
        ipca_monthly = get_ipca_monthly(indices)
    if taxa_desconto_mensal is None:
        di_pre_anual        = get_di_pre_rate(di_pre_rates, prazo_horizonte)
        taxa_di_pre_total   = (1 + di_pre_anual) * (1 + spread_percent) - 1
        taxa_desconto_mensal = (1 + taxa_di_pre_total) ** (1 / 12) - 1

    rr = find_recovery_rate(recovery_rates, empresa, tipo, aging_taxa, is_voltz)
    taxa_rec = rr["taxa"]
    prazo_rec = rr["prazo"]

    meses_ate_receb     = prazo_rec
    valor_recuperavel   = valor_corrigido * taxa_rec
    fc_receb            = (1 + ipca_monthly) ** meses_ate_receb
    mora                = meses_ate_receb * 0.01
    fator_desconto      = (1 + taxa_desconto_mensal) ** meses_ate_receb
    valor_justo_bruto   = (
        (valor_corrigido * taxa_rec * (fc_receb + mora)) / fator_desconto
        if fator_desconto > 0 else 0.0
    )
    desconto_aging = REMUNERATION_DISCOUNTS.get(aging, 0.50)
    valor_justo    = valor_justo_bruto * (1 - desconto_aging)

    result = {
        **row,
        "dias_atraso":       dias_atraso,
        "aging":             aging,
        "aging_taxa":        aging_taxa,
        "valor_liquido":     valor_liquido,
        "multa":             multa,
        "juros_moratorios":  juros_moratorios,
        "fator_correcao":    fator_correcao,
        "correcao_monetaria": correcao_monetaria,
        "valor_corrigido":   valor_corrigido,
        "taxa_recuperacao":  taxa_rec,
        "prazo_recebimento": prazo_rec,
        "valor_recuperavel": valor_recuperavel,
        "valor_justo":       valor_justo,
    }
    if juros_remuneratorios is not None:
        result["juros_remuneratorios"]      = juros_remuneratorios
    if saldo_devedor_vencimento is not None:
        result["saldo_devedor_vencimento"]  = saldo_devedor_vencimento

    return result
