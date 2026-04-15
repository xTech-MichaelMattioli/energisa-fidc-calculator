"""
Utilitario para exportacao automatica do resultado final em Excel.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

from utils.exportacao_csv_brasil import truncar_numericos


def _chave_resultado(df_final: pd.DataFrame) -> str:
    """Gera uma chave simples para evitar exportacoes duplicadas em reruns."""
    registros = str(len(df_final))
    total_colunas = str(len(df_final.columns))

    agregados = []
    for coluna in ("valor_principal", "valor_corrigido", "valor_justo"):
        if coluna in df_final.columns:
            serie = pd.to_numeric(df_final[coluna], errors="coerce")
            agregados.append(f"{serie.sum(skipna=True):.2f}")
        else:
            agregados.append("NA")

    return "|".join([registros, total_colunas] + agregados)


def _resolver_pasta_data() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


def exportar_resultado_final_excel(
    df_final: pd.DataFrame,
    eh_voltz: bool = False,
) -> Tuple[Optional[str], bool]:
    """
    Exporta o resultado final para Excel automaticamente.

    Retorna:
    - caminho do arquivo (ou None se nao houver dados)
    - indicador se um novo arquivo foi criado nesta chamada
    """
    if df_final is None or df_final.empty:
        return None, False

    execucao_id = st.session_state.get("calculo_execucao_id")
    ultimo_execucao_id = st.session_state.get("auto_export_execucao_id")
    ultimo_caminho = st.session_state.get("auto_export_caminho")

    if execucao_id and execucao_id == ultimo_execucao_id and ultimo_caminho:
        return str(ultimo_caminho), False

    chave_atual = _chave_resultado(df_final)
    ultima_chave = st.session_state.get("auto_export_chave_resultado")
    if not execucao_id and ultima_chave == chave_atual and ultimo_caminho:
        return str(ultimo_caminho), False

    pasta_data = _resolver_pasta_data()
    pasta_data.mkdir(parents=True, exist_ok=True)

    prefixo = "FIDC_VOLTZ_Dados_Finais" if eh_voltz else "FIDC_Dados_Finais"
    sufixo = execucao_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_arquivo = pasta_data / f"{prefixo}_{sufixo}.xlsx"

    df_export = df_final.copy()
    if "documento" in df_export.columns:
        df_export = df_export.drop(columns=["documento"], errors="ignore")

    # No arquivo Excel final, expor o nome da coluna alinhado ao conceito de data base.
    if "valor_corrigido" in df_export.columns and "valor_corrigido_ate_data_base" not in df_export.columns:
        df_export = df_export.rename(columns={"valor_corrigido": "valor_corrigido_ate_data_base"})

    df_export = truncar_numericos(df_export, casas_decimais=4)

    with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="resultado")

    st.session_state.auto_export_caminho = str(caminho_arquivo)
    st.session_state.auto_export_chave_resultado = chave_atual
    st.session_state.auto_export_execucao_id = execucao_id
    st.session_state.auto_export_registros = len(df_final)
    st.session_state.auto_export_data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return str(caminho_arquivo), True


def exportar_resultado_final_csv(
    df_final: pd.DataFrame,
    eh_voltz: bool = False,
) -> Tuple[Optional[str], bool]:
    """
    Compatibilidade retroativa: encaminha para exportacao automatica em Excel.
    """
    return exportar_resultado_final_excel(df_final=df_final, eh_voltz=eh_voltz)
