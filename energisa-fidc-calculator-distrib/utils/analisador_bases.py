"""
Analisador de bases de dados
Baseado no notebook original
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import streamlit as st
from utils.gerenciador_arquivos import (
    gerar_caminho_parquet,
    remover_arquivo_se_existir
)


class AnalisadorBases:
    """
    Classe para carregar e analisar as estruturas das bases ESS e Voltz.
    """
    
    def __init__(self, params):
        self.params = params
    
    def carregar_base_excel(self, caminho_excel: str, nome_distribuidora: str) -> dict:
        """
        Carrega a base Excel, converte para Parquet e retorna apenas metadados.
        A base completa deixa de ser mantida no session_state.
        """

        if not caminho_excel or not os.path.exists(caminho_excel):
            st.error("❌ Arquivo não encontrado para processamento.")
            return {}

        try:
            extensao = os.path.splitext(caminho_excel)[1].lower()

            if extensao not in [".xlsx", ".xls"]:
                st.error(
                    "❌ Formato de arquivo não suportado. "
                    "Use apenas arquivos Excel (.xlsx, .xls)"
                )
                return {}

            # Tentar usar calamine; se não estiver instalado, usar engine padrão
            try:
                xl_file = pd.ExcelFile(caminho_excel, engine="calamine")
            except Exception:
                xl_file = pd.ExcelFile(caminho_excel)

            # Definir aba principal
            if len(xl_file.sheet_names) > 1:
                st.info(f"📋 Abas disponíveis: {xl_file.sheet_names}")

                abas_comuns = [
                    "Base",
                    "Dados",
                    "Principal",
                    nome_distribuidora.title()
                ]

                aba_principal = xl_file.sheet_names[0]

                for aba_comum in abas_comuns:
                    if aba_comum in xl_file.sheet_names:
                        aba_principal = aba_comum
                        break

                st.info(f"📄 Aba utilizada: {aba_principal}")
            else:
                aba_principal = xl_file.sheet_names[0]

            # Ler a aba escolhida
            df = xl_file.parse(sheet_name=aba_principal)
            xl_file.close()

            if df.empty:
                st.warning(f"⚠️ A base {nome_distribuidora} está vazia.")
                return {}

            # Calcular valor total
            valor_total = self._calcular_valor_total(df)

            # Detectar data base apenas uma vez
            data_base_info = self._detectar_data_base(df)

            # Criar preview pequeno
            preview = df.head(3).copy()

            # Converter para Parquet
            caminho_parquet = gerar_caminho_parquet(nome_distribuidora)

            df.to_parquet(
                caminho_parquet,
                index=False,
                engine="pyarrow",
                compression="snappy"
            )

            registros = len(df)
            colunas = len(df.columns)
            nomes_colunas = df.columns.tolist()

            # Fechar ExcelFile antes de remover temporário
            try:
                xl_file.close()
            except Exception:
                pass

            # Liberar DataFrame grande da memória
            del df

            # Tentar remover o Excel temporário sem quebrar o processamento
            try:
                remover_arquivo_se_existir(caminho_excel)
            except Exception as e:
                st.warning(
                    f"⚠️ A base foi processada com sucesso, "
                    f"mas o arquivo temporário não pôde ser removido: {e}"
                )

            return {
                "caminho_parquet": caminho_parquet,
                "registros": registros,
                "colunas": colunas,
                "nome_arquivo": nome_distribuidora,
                "valor_total": valor_total,
                "preview": preview,
                "data_base_info": data_base_info,
                "nomes_colunas": nomes_colunas
            }

        except Exception as e:
            st.error(f"❌ Erro ao carregar base {nome_distribuidora}: {e}")
            return {}

    def _calcular_valor_total(self, df: pd.DataFrame) -> float:
        """
        Procura uma coluna monetária provável e calcula o total.
        """
        valor_total = 0

        colunas_candidatas = [
            col for col in df.columns
            if isinstance(col, str)
            and any(
                termo in col.lower()
                for termo in ["valor", "principal", "liquido", "líquido"]
            )
            and pd.api.types.is_numeric_dtype(df[col])
        ]

        if colunas_candidatas:
            coluna_escolhida = colunas_candidatas[0]
            valor_total = df[coluna_escolhida].sum()

        return valor_total


    def _detectar_data_base(self, df: pd.DataFrame) -> dict:
        """
        Detecta a data base com base em:
        1. Datas presentes no cabeçalho;
        2. Colunas de data/vencimento.
        """

        colunas_data = []

        for col in df.columns:
            try:
                # Tentar converter o nome da coluna em data
                data_header = pd.to_datetime(col, errors="coerce")

                if not pd.isna(data_header):
                    colunas_data.append({
                        "coluna": col,
                        "data_detectada": data_header,
                        "tipo": "Data no cabeçalho",
                        "eh_data_base": True
                    })
                    continue

                # Identificar possíveis colunas de data
                if isinstance(col, str) and any(
                    termo in col.lower()
                    for termo in ["data", "vencimento", "venc", "date"]
                ):
                    datas_validas = pd.to_datetime(
                        df[col],
                        errors="coerce"
                    ).dropna()

                    percentual_valido = (
                        len(datas_validas) / len(df)
                        if len(df) > 0
                        else 0
                    )

                    if len(datas_validas) > 0 and percentual_valido >= 0.1:
                        colunas_data.append({
                            "coluna": col,
                            "data_detectada": datas_validas.max(),
                            "tipo": "Coluna de vencimento",
                            "eh_data_base": False,
                            "registros_validos": len(datas_validas),
                            "percentual_valido": percentual_valido
                        })

            except Exception:
                continue

        if not colunas_data:
            return {
                "detectada": False,
                "coluna_preferida": None,
                "data_base_detectada": None,
                "colunas_data": []
            }

        # Priorizar data no cabeçalho
        data_base_header = [
            item for item in colunas_data
            if item["eh_data_base"]
        ]

        if data_base_header:
            coluna_preferida = max(
                data_base_header,
                key=lambda x: x["data_detectada"]
            )
        else:
            colunas_vencimento = [
                item for item in colunas_data
                if not item["eh_data_base"]
            ]

            coluna_preferida = max(
                colunas_vencimento,
                key=lambda x: x["data_detectada"]
            )

        return {
            "detectada": True,
            "coluna_preferida": coluna_preferida,
            "data_base_detectada": coluna_preferida["data_detectada"],
            "colunas_data": colunas_data
        }

    def analisar_estrutura(self, df: pd.DataFrame, nome_distribuidora: str) -> None:
        """
        Exibe análise da estrutura da base.
        """
        if df.empty:
            return
        
        st.subheader(f"📋 Estrutura da Base {nome_distribuidora.upper()}")
        
        # Mostrar primeiras 15 colunas
        cols_to_show = min(15, len(df.columns))
        col_info = []
        
        for i, col in enumerate(df.columns[:cols_to_show]):
            col_info.append(f"{i+1:2d}. {col}")
        
        if len(df.columns) > 15:
            col_info.append(f"... e mais {len(df.columns) - 15} colunas")
        
        st.text("\n".join(col_info))
    
    def analisar_campos_chave(self, df: pd.DataFrame, nome_distribuidora: str) -> Dict:
        """
        Analisa campos chave para identificar mapeamentos necessários.
        """
        if df.empty:
            return {}
        
        # Campos que procuramos (variações possíveis)
        campos_procurados = {
            'identificacao': ['id', 'codigo', 'numero', 'seq', 'sequencial'],
            'cliente': ['cliente', 'nome', 'razao', 'consumidor'],
            'documento': ['cpf', 'cnpj', 'documento', 'doc'],
            'contrato': ['contrato', 'conta', 'instalacao', 'uc'],
            'valor': ['valor', 'debito', 'saldo', 'divida', 'total', 'fatura'],
            'vencimento': ['vencimento', 'venc', 'data', 'prazo'],
            'classe': ['classe', 'categoria', 'tipo', 'grupo'],
            'situacao': ['situacao', 'status', 'estado']
        }
        
        mapeamento = {}
        resultados = []
        
        for categoria, termos in campos_procurados.items():
            encontrados = []
            for termo in termos:
                matches = [col for col in df.columns if isinstance(col, str) and termo.lower() in col.lower()]
                encontrados.extend(matches)
            
            if encontrados:
                # Remover duplicatas mantendo ordem
                encontrados = list(dict.fromkeys(encontrados))
                mapeamento[categoria] = encontrados
                status = "✅"
                campos_str = ", ".join(encontrados[:3])
                if len(encontrados) > 3:
                    campos_str += "..."
            else:
                status = "❌"
                campos_str = "Não encontrado"
            
            resultados.append(f"{status} **{categoria.upper()}**: {campos_str}")
        
        st.subheader(f"🔍 Campos Chave Identificados - {nome_distribuidora.upper()}")
        for resultado in resultados:
            st.markdown(resultado)
        
        return mapeamento
    
    def exibir_amostra_dados(self, df: pd.DataFrame, nome_distribuidora: str, n_linhas: int = 3):
        """
        Exibe amostra dos dados para entendimento.
        """
        if df.empty:
            return
        
        st.subheader(f"📊 Amostra de Dados - {nome_distribuidora.upper()}")
        
        # Mostrar primeiras 8 colunas
        colunas_importantes = df.columns[:8]
        amostra = df[colunas_importantes].head(n_linhas)
        
        st.dataframe(amostra, use_container_width=True)
        
        return amostra
