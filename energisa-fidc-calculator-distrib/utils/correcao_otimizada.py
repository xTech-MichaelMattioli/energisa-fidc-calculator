"""
Utilitarios vetorizados para calculos de correcao monetaria.
"""

from datetime import datetime

import numpy as np
import pandas as pd


def otimizar_curva_di_pre(df_di_pre: pd.DataFrame) -> pd.DataFrame:
    """Mantem apenas um ponto por mes futuro, escolhendo o mais proximo do inteiro."""
    if df_di_pre is None or df_di_pre.empty:
        return df_di_pre

    df = df_di_pre.copy()
    if "dias_corridos" in df.columns:
        dias_corridos = pd.to_numeric(df["dias_corridos"], errors="coerce")
        df["meses_futuros"] = dias_corridos / 30.44
    elif "meses_futuros" in df.columns:
        df["meses_futuros"] = pd.to_numeric(df["meses_futuros"], errors="coerce")
    else:
        return df

    df = df.dropna(subset=["meses_futuros"]).copy()
    df = df[df["meses_futuros"] > 0].copy()

    df["mes_ref"] = df["meses_futuros"].round().astype(int)
    df["dist_mes_ref"] = (df["meses_futuros"] - df["mes_ref"]).abs()

    ordenacao = ["mes_ref", "dist_mes_ref"]
    if "dias_corridos" in df.columns:
        df["dias_corridos"] = pd.to_numeric(df["dias_corridos"], errors="coerce")
        ordenacao.append("dias_corridos")

    df = (
        df.sort_values(ordenacao)
        .drop_duplicates(subset=["mes_ref"], keep="first")
        .sort_values("mes_ref")
        .reset_index(drop=True)
    )

    df["meses_futuros"] = df["mes_ref"]

    if "data_arquivo" in df.columns and "dias_corridos" in df.columns:
        data_arquivo = pd.to_datetime(df["data_arquivo"], errors="coerce")
        dias_corridos = pd.to_numeric(df["dias_corridos"], errors="coerce").fillna(0)
        data_futura = data_arquivo + pd.to_timedelta(dias_corridos, unit="d")
        df["data_arquivo"] = data_arquivo
        df["ano_atual"] = data_futura.dt.year
        df["mes_atual"] = data_futura.dt.month

    return df.drop(columns=["mes_ref", "dist_mes_ref"], errors="ignore")


def calcular_indice_diario_vetorizado(
    df: pd.DataFrame,
    coluna_data: str,
    coluna_indice_mes: str,
    coluna_indice_mes_anterior: str,
    coluna_taxa_mensal: str,
    coluna_taxa_diaria: str,
) -> pd.Series:
    """Calcula indice diario sem apply linha a linha."""
    data = pd.to_datetime(df[coluna_data], errors="coerce")
    indice_mes = pd.to_numeric(df[coluna_indice_mes], errors="coerce")
    indice_mes_anterior = pd.to_numeric(df[coluna_indice_mes_anterior], errors="coerce")
    taxa_mensal = pd.to_numeric(df[coluna_taxa_mensal], errors="coerce")
    taxa_diaria = pd.to_numeric(df[coluna_taxa_diaria], errors="coerce")

    resultado = pd.Series(np.nan, index=df.index, dtype="float64")

    mask_sem_calculo = data.isna() | indice_mes.isna() | taxa_mensal.isna()
    resultado.loc[mask_sem_calculo] = indice_mes.loc[mask_sem_calculo]

    dia_mes = data.dt.day
    ultimo_dia = data.dt.days_in_month

    mask_ultimo_dia = (~mask_sem_calculo) & (dia_mes == ultimo_dia)
    resultado.loc[mask_ultimo_dia] = indice_mes.loc[mask_ultimo_dia]

    mask_calcular = (~mask_sem_calculo) & (~mask_ultimo_dia)
    if mask_calcular.any():
        fator_periodo = np.power(
            1 + taxa_diaria.loc[mask_calcular],
            dia_mes.loc[mask_calcular],
        )
        resultado.loc[mask_calcular] = (
            indice_mes_anterior.loc[mask_calcular] * fator_periodo
        )

    return resultado


def aplicar_correcao_monetaria_vetorizada(
    df: pd.DataFrame,
    coluna_fator: str = "fator_correcao",
) -> pd.DataFrame:
    """Aplica correcao monetaria e valores derivados de forma vetorizada."""
    df_result = df.copy()

    fator = pd.to_numeric(df_result.get(coluna_fator, 1.0), errors="coerce").fillna(1.0)
    valor_liquido = pd.to_numeric(df_result.get("valor_liquido", 0.0), errors="coerce").fillna(0.0)
    multa = pd.to_numeric(df_result.get("multa", 0.0), errors="coerce").fillna(0.0)
    juros_moratorios = pd.to_numeric(df_result.get("juros_moratorios", 0.0), errors="coerce").fillna(0.0)

    df_result["correcao_monetaria"] = np.maximum(
        valor_liquido * (fator - 1),
        0,
    )
    df_result["valor_corrigido"] = (
        valor_liquido
        + multa
        + juros_moratorios
        + df_result["correcao_monetaria"]
    )

    if "taxa_recuperacao" in df_result.columns:
        taxa_recuperacao = pd.to_numeric(df_result["taxa_recuperacao"], errors="coerce").fillna(0.0)
        df_result["valor_recuperavel_ate_data_base"] = (
            df_result["valor_corrigido"] * taxa_recuperacao
        )

    return df_result


def calcular_valor_justo_di_pre_vetorizado(
    df_corrigido: pd.DataFrame,
    df_di_pre: pd.DataFrame,
    coluna_valor_corrigido: str = "valor_corrigido",
    data_base: datetime | None = None,
) -> pd.DataFrame:
    """Calcula valor justo com DI-PRE sem iteracao linha a linha."""
    if data_base is None:
        data_base = datetime.now()

    df_resultado = df_corrigido.copy()

    if "prazo_recebimento" not in df_resultado.columns:
        df_resultado["prazo_recebimento"] = 6

    prazo = pd.to_numeric(df_resultado["prazo_recebimento"], errors="coerce").fillna(6).round().astype(int)
    prazo = prazo.clip(lower=1)
    df_resultado["prazo_recebimento"] = prazo

    di_pre = df_di_pre.copy() if df_di_pre is not None else pd.DataFrame()
    if not di_pre.empty and {"meses_futuros", "252"}.issubset(di_pre.columns):
        di_pre["meses_futuros"] = pd.to_numeric(di_pre["meses_futuros"], errors="coerce").round()
        di_pre["252"] = pd.to_numeric(di_pre["252"], errors="coerce")
        di_pre = di_pre.dropna(subset=["meses_futuros", "252"]).copy()
        di_pre["meses_futuros"] = di_pre["meses_futuros"].astype(int)
        di_pre = di_pre.sort_values("meses_futuros").drop_duplicates(subset=["meses_futuros"], keep="first")
    else:
        di_pre = pd.DataFrame(columns=["meses_futuros", "252"])

    if di_pre.empty:
        taxa_di_pre = pd.Series(0.005, index=df_resultado.index, dtype="float64")
    else:
        mapa_taxas = di_pre.set_index("meses_futuros")["252"] / 100
        taxa_di_pre = prazo.map(mapa_taxas)

        faltantes = taxa_di_pre.isna()
        if faltantes.any():
            meses_disponiveis = di_pre["meses_futuros"].to_numpy()
            prazo_faltante = prazo.loc[faltantes].to_numpy()

            indices_proximos = np.abs(
                prazo_faltante[:, None] - meses_disponiveis[None, :]
            ).argmin(axis=1)
            meses_proximos = meses_disponiveis[indices_proximos]

            taxa_fallback = pd.Series(meses_proximos, index=prazo.loc[faltantes].index).map(mapa_taxas)
            taxa_di_pre.loc[faltantes] = taxa_fallback

        taxa_di_pre = taxa_di_pre.fillna(0.005)

    df_resultado["taxa_di_pre"] = taxa_di_pre.astype(float)
    df_resultado["fator_exponencial_di_pre"] = np.power(
        1 + df_resultado["taxa_di_pre"],
        prazo / 12,
    )

    data_vencimento_ref = pd.Timestamp(data_base) + pd.DateOffset(months=6)
    df_resultado["data_vencimento"] = data_vencimento_ref
    df_resultado["dias_atraso"] = (
        pd.Timestamp.now() - pd.to_datetime(df_resultado["data_vencimento"], errors="coerce")
    ).dt.days.clip(lower=0)

    df_resultado["multa_para_justo"] = np.where(
        df_resultado["dias_atraso"] > 0,
        (0.01 / 30) * df_resultado["dias_atraso"],
        0.06,
    )

    if "taxa_recuperacao" not in df_resultado.columns:
        raise KeyError("taxa_recuperacao")

    taxa_recuperacao = pd.to_numeric(df_resultado["taxa_recuperacao"], errors="coerce").fillna(0.0)
    valor_corrigido = pd.to_numeric(df_resultado[coluna_valor_corrigido], errors="coerce").fillna(0.0)

    df_resultado["valor_justo_ate_recebimento"] = (
        valor_corrigido
        * taxa_recuperacao
        * (df_resultado["fator_exponencial_di_pre"] + df_resultado["multa_para_justo"])
    )

    return df_resultado
