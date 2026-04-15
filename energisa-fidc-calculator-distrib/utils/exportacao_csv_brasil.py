"""
Utilitarios para exportacao CSV no formato brasileiro.
"""

from pathlib import Path

import numpy as np
import pandas as pd


PALAVRAS_NUMERICAS = (
    "valor",
    "multa",
    "juros",
    "indice",
    "fator",
    "taxa",
    "spread",
    "ipca",
    "desconto",
    "cdi",
    "rv",
    "remuneracao",
)

PALAVRAS_EXCLUIDAS = (
    "documento",
    "cpf",
    "cnpj",
    "contrato",
    "id",
)

COLUNAS_REMOVER_EXPORTACAO = (
    "documento",
)

COLUNAS_PRECISAO_LIVRE_EXATAS = (
    "ipca_mensal",
)

CASAS_DECIMAIS_SUBUNITARIO = 8
CASAS_DECIMAIS_FORA_FAIXA = 4


def _preservar_precisao_coluna(nome_coluna: str) -> bool:
    """
    Define colunas que nao devem ser truncadas por regra de casas decimais.
    Regra atual:
    - ipca_mensal
    - qualquer coluna com prefixo fator_
    """
    nome = str(nome_coluna).lower().strip()
    if nome in COLUNAS_PRECISAO_LIVRE_EXATAS:
        return True
    return nome.startswith("fator_")


def _coluna_candidata_por_nome(nome_coluna: str) -> bool:
    nome = str(nome_coluna).lower().strip()
    if _preservar_precisao_coluna(nome):
        return False
    if any(palavra in nome for palavra in PALAVRAS_EXCLUIDAS):
        return False
    return any(palavra in nome for palavra in PALAVRAS_NUMERICAS)


def _parse_numero_robusto(serie: pd.Series) -> pd.Series:
    """Converte serie para float tratando formatos pt-BR e formato com ponto decimal."""
    texto = serie.astype(str).str.strip()
    texto = texto.replace({"": np.nan, "nan": np.nan, "None": np.nan, "NaN": np.nan})

    numero = pd.to_numeric(texto, errors="coerce")
    mask_faltante = numero.isna() & texto.notna()

    if mask_faltante.any():
        texto_br = (
            texto.loc[mask_faltante]
            .str.replace(r"\s", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        numero.loc[mask_faltante] = pd.to_numeric(texto_br, errors="coerce")

    return numero


def _remover_colunas_exportacao(
    df: pd.DataFrame,
    colunas_remover: tuple[str, ...] = COLUNAS_REMOVER_EXPORTACAO,
) -> pd.DataFrame:
    """Remove colunas sensiveis/indesejadas da exportacao, sem alterar o DataFrame original."""
    if df is None or df.empty:
        return df

    mapa_colunas = {str(coluna).strip().lower(): coluna for coluna in df.columns}
    colunas_encontradas = [
        mapa_colunas[nome.lower().strip()]
        for nome in colunas_remover
        if nome.lower().strip() in mapa_colunas
    ]

    if not colunas_encontradas:
        return df.copy()

    return df.drop(columns=colunas_encontradas, errors="ignore")


def truncar_numericos(df: pd.DataFrame, casas_decimais: int = CASAS_DECIMAIS_FORA_FAIXA) -> pd.DataFrame:
    """
    Trunca (nao arredonda) colunas numericas com duas regras:
    - valores fora do intervalo (-1, 1): casas_decimais (padrao 4)
    - valores dentro do intervalo (-1, 1): ate 8 casas decimais
    """
    if df is None or df.empty:
        return df

    df_saida = df.copy()
    colunas_float = [
        coluna
        for coluna in df_saida.select_dtypes(include=["float", "float32", "float64"]).columns
        if not _preservar_precisao_coluna(coluna)
    ]
    colunas_int_candidatas = [
        coluna
        for coluna in df_saida.select_dtypes(include=["int", "int32", "int64"]).columns
        if _coluna_candidata_por_nome(coluna)
    ]

    colunas_objetivo_texto = []
    for coluna in df_saida.select_dtypes(include=["object", "string"]).columns:
        if not _coluna_candidata_por_nome(coluna):
            continue

        serie_convertida = _parse_numero_robusto(df_saida[coluna])
        taxa_convertida = serie_convertida.notna().mean()
        if taxa_convertida >= 0.60:
            df_saida[coluna] = serie_convertida
            colunas_objetivo_texto.append(coluna)

    colunas_numericas = list(dict.fromkeys(colunas_float + colunas_int_candidatas + colunas_objetivo_texto))
    if len(colunas_numericas) == 0:
        return df_saida

    fator = 10 ** casas_decimais
    fator_subunitario = 10 ** CASAS_DECIMAIS_SUBUNITARIO

    for coluna in colunas_numericas:
        serie = _parse_numero_robusto(df_saida[coluna])
        valores = serie.to_numpy(dtype="float64", copy=True)

        mask_validos = ~np.isnan(valores)
        mask_subunitario = mask_validos & (np.abs(valores) < 1)
        mask_padrao = mask_validos & (~mask_subunitario)

        if mask_padrao.any():
            valores[mask_padrao] = np.trunc(valores[mask_padrao] * fator) / fator

        if mask_subunitario.any():
            valores[mask_subunitario] = (
                np.trunc(valores[mask_subunitario] * fator_subunitario) / fator_subunitario
            )

        df_saida[coluna] = valores

    return df_saida


def salvar_csv_brasil(
    df: pd.DataFrame,
    caminho_arquivo: str | Path,
    casas_decimais: int = CASAS_DECIMAIS_FORA_FAIXA,
    remover_documento: bool = True,
) -> pd.DataFrame:
    """
    Salva CSV com separador ';', decimal ','.
    Regras de truncamento:
    - valor fora de (-1, 1): 4 casas decimais
    - valor dentro de (-1, 1): ate 8 casas decimais
    Excecao: colunas ipca_mensal e fator_* preservam precisao original.
    Por padrao, remove a coluna 'documento' para evitar identificadores extensos no arquivo final.
    """
    df_base = _remover_colunas_exportacao(df) if remover_documento else df.copy()
    df_export = truncar_numericos(df_base, casas_decimais=casas_decimais)
    df_export.to_csv(
        caminho_arquivo,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        decimal=",",
    )
    return df_export
