"""
Calculador de correção monetária e valor corrigido final
Baseado no notebook original
"""

import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st


class CalculadorCorrecao:
    """
    Calcula correção monetária e valor corrigido final.
    """
    
    def __init__(self, params):
        self.params = params
    
    def limpar_e_converter_valor(self, serie_valor: pd.Series) -> pd.Series:
        """
        Limpa e converte série de valores para numérico.
        """
        # Converter para numérico
        valores_convertidos = pd.to_numeric(serie_valor, errors='coerce')
        
        # Substituir valores inválidos por 0
        valores_convertidos = valores_convertidos.fillna(0)
        
        return valores_convertidos
    
    def calcular_valor_liquido(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula valor líquido = valor_principal - valor_nao_cedido - valor_terceiro - valor_cip
        """
        # Limpar valor principal
        if 'valor_principal' not in df.columns:
            df['valor_liquido'] = 0
            return df
        
        df['valor_principal_limpo'] = self.limpar_e_converter_valor(df['valor_principal'])
        
        # Limpar valores de dedução
        # Valor não cedido
        if 'valor_nao_cedido' in df.columns:
            df['valor_nao_cedido_limpo'] = self.limpar_e_converter_valor(df['valor_nao_cedido'].fillna(0))
        else:
            df['valor_nao_cedido_limpo'] = 0
        
        # Valor terceiro
        if 'valor_terceiro' in df.columns:
            df['valor_terceiro_limpo'] = self.limpar_e_converter_valor(df['valor_terceiro'].fillna(0))
        else:
            df['valor_terceiro_limpo'] = 0
        
        # Valor CIP
        if 'valor_cip' in df.columns:
            df['valor_cip_limpo'] = self.limpar_e_converter_valor(df['valor_cip'].fillna(0))
        else:
            df['valor_cip_limpo'] = 0
        
        # Calcular valor líquido
        df['valor_liquido'] = (
            df['valor_principal_limpo'] - 
            df['valor_nao_cedido_limpo'] - 
            df['valor_terceiro_limpo'] - 
            df['valor_cip_limpo']
        )
        
        # Garantir que valor líquido não seja negativo
        df['valor_liquido'] = np.maximum(df['valor_liquido'], 0)
        
        return df
    
    def calcular_multa(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula multa de 2% sobre valor líquido.
        """
        df = df.copy()
        
        # Calcular valor líquido se não foi calculado
        if 'valor_liquido' not in df.columns:
            df = self.calcular_valor_liquido(df)
        
        # Calcular multa apenas para valores em atraso
        df['multa'] = np.where(
            df['dias_atraso'] > 0,
            df['valor_liquido'] * self.params.taxa_multa,
            0
        )
        
        return df
    
    def calcular_juros_moratorios(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula juros moratórios de 1% ao mês proporcional sobre valor líquido.
        """
        df = df.copy()
        
        # Calcular meses de atraso
        df['meses_atraso'] = df['dias_atraso'] / 30
        
        # Calcular juros proporcionais apenas para valores em atraso
        df['juros_moratorios'] = np.where(
            df['dias_atraso'] > 0,
            df['valor_liquido'] * self.params.taxa_juros_mensal * df['meses_atraso'],
            0
        )
        
        return df
    
    def calcular_correcao_monetaria(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula correção monetária baseada em IGPM/IPCA sobre valor líquido.
        """
        df = df.copy()
        
        # Buscar índices
        df['indice_vencimento'] = df['data_vencimento_limpa'].apply(
            lambda x: self.params.buscar_indice_correcao(x) if pd.notna(x) else 624.40
        )
        
        df['indice_base'] = df['data_base'].apply(self.params.buscar_indice_correcao)
        
        # Calcular fator de correção
        df['fator_correcao'] = df['indice_base'] / df['indice_vencimento']
        
        # Aplicar correção monetária apenas para valores em atraso
        df['correcao_monetaria'] = np.where(
            df['dias_atraso'] > 0,
            df['valor_liquido'] * (df['fator_correcao'] - 1),
            0
        )
        
        # Garantir que correção não seja negativa
        df['correcao_monetaria'] = np.maximum(df['correcao_monetaria'], 0)
        
        return df
    
    def calcular_valor_corrigido_final(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula valor corrigido final somando todos os componentes.
        """
        df = df.copy()
        
        # Somar todos os componentes
        df['valor_corrigido'] = (
            df['valor_liquido'] +
            df['multa'] +
            df['juros_moratorios'] +
            df['correcao_monetaria']
        )
        
        return df
    
    def gerar_resumo_correcao(self, df: pd.DataFrame, nome_base: str):
        """
        Gera resumo da correção monetária.
        """
        st.subheader(f"📊 Resumo da Correção - {nome_base.upper()}")
        
        valor_principal = df['valor_principal_limpo'].sum()
        valor_deducoes = (df['valor_nao_cedido_limpo'].sum() + 
                         df['valor_terceiro_limpo'].sum() + 
                         df['valor_cip_limpo'].sum())
        valor_liquido = df['valor_liquido'].sum()
        multa_total = df['multa'].sum()
        juros_total = df['juros_moratorios'].sum()
        correcao_total = df['correcao_monetaria'].sum()
        valor_corrigido = df['valor_corrigido'].sum()
        
        percentual_total = ((valor_corrigido / valor_liquido) - 1) * 100 if valor_liquido > 0 else 0
        
        # Exibir em formato de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💵 Valor Principal", f"R$ {valor_principal:,.2f}")
            st.metric("⚖️ Multa (2%)", f"R$ {multa_total:,.2f}")
        
        with col2:
            st.metric("➖ Deduções Totais", f"R$ {valor_deducoes:,.2f}")
            st.metric("📈 Juros Moratórios", f"R$ {juros_total:,.2f}")
        
        with col3:
            st.metric("💎 Valor Líquido", f"R$ {valor_liquido:,.2f}")
            st.metric("💹 Correção Monetária", f"R$ {correcao_total:,.2f}")
        
        with col4:
            st.metric("🎯 Valor Corrigido", f"R$ {valor_corrigido:,.2f}")
            st.metric("📊 Correção Total", f"{percentual_total:.2f}%")
    
    def processar_correcao_completa(self, df: pd.DataFrame, nome_base: str) -> pd.DataFrame:
        """
        Executa todo o processo de correção monetária.
        """
        if df.empty:
            return df
        
        # Calcular valor líquido
        df = self.calcular_valor_liquido(df)
        
        # Calcular multa
        df = self.calcular_multa(df)
        
        # Calcular juros moratórios
        df = self.calcular_juros_moratorios(df)
        
        # Calcular correção monetária
        df = self.calcular_correcao_monetaria(df)
        
        # Calcular valor corrigido final
        df = self.calcular_valor_corrigido_final(df)
        
        return df
