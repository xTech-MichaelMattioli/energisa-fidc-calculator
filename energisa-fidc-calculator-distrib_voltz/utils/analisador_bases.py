"""
Analisador de bases de dados
Baseado no notebook original
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import streamlit as st


class AnalisadorBases:
    """
    Classe para carregar e analisar as estruturas das bases ESS e Voltz.
    """
    
    def __init__(self, params):
        self.params = params
    
    def carregar_base_excel(self, uploaded_file, nome_distribuidora: str) -> pd.DataFrame:
        """
        Carrega base do arquivo Excel enviado.
        """
        if uploaded_file is None:
            return pd.DataFrame()
        
        try:
            # Verificar se é arquivo Excel
            if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
                # Verificar se tem múltiplas abas
                xl_file = pd.ExcelFile(uploaded_file)
                
                if len(xl_file.sheet_names) > 1:
                    st.info(f"📋 Abas disponíveis: {xl_file.sheet_names}")
                    
                    # Usar primeira aba ou buscar por nomes comuns
                    abas_comuns = ['Base', 'Dados', 'Principal', nome_distribuidora.title()]
                    aba_principal = xl_file.sheet_names[0]  # Default
                    
                    for aba_comum in abas_comuns:
                        if aba_comum in xl_file.sheet_names:
                            aba_principal = aba_comum
                            break
                    
                    df = pd.read_excel(uploaded_file, sheet_name=aba_principal)
                    st.info(f"📄 Aba utilizada: {aba_principal}")
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ Base {nome_distribuidora} carregada: {len(df):,} registros x {len(df.columns)} colunas")
                return df
                
            else:
                st.error("❌ Formato de arquivo não suportado. Use apenas arquivos Excel (.xlsx, .xls)")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"❌ Erro ao carregar base {nome_distribuidora}: {e}")
            return pd.DataFrame()
    
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
