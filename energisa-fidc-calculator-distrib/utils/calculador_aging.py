"""
Calculador de aging (tempo de inadimplência)
Baseado no notebook original
COM CHECKPOINT: Sistema inteligente de cache para evitar reprocessamento
"""

import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
from .checkpoint_manager import usar_checkpoint


class CalculadorAging:
    """
    Calcula aging (tempo de inadimplência) para as bases padronizadas.
    """
    
    def __init__(self, params):
        self.params = params
    
    def limpar_e_converter_data(self, serie_data: pd.Series) -> pd.Series:
        """
        Limpa e converte série de datas para datetime.
        """
        # Tentar conversão direta
        try:
            datas_convertidas = pd.to_datetime(serie_data, errors='coerce')
            validas = datas_convertidas.notna().sum()
            total = len(serie_data)
            return datas_convertidas
        except Exception as e:
            st.error(f"❌ Erro na conversão de datas: {e}")
            return pd.Series([pd.NaT] * len(serie_data))
    
    def calcular_dias_atraso(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula dias de atraso entre vencimento e data base.
        """
        
        df = df.copy()
        
        # Verificar se temos campo de data de vencimento
        if 'data_vencimento' not in df.columns:
            st.error("❌ Campo data_vencimento não encontrado")
            df['dias_atraso'] = 0
            df['aging'] = 'Não calculado'
            return df
        
        with st.spinner("📊 Calculando dias de atraso..."):
            # Limpar e converter datas de vencimento
            df['data_vencimento_limpa'] = self.limpar_e_converter_data(df['data_vencimento'])
            
            # Calcular dias de atraso
            df['dias_atraso'] = (df['data_base'] - df['data_vencimento_limpa']).dt.days
            
            # Tratar valores inválidos
            df['dias_atraso'] = df['dias_atraso'].fillna(0)           
        
        return df
    
    def classificar_aging(self, dias_atraso: float) -> str:
        """
        Classifica aging baseado nos dias de atraso.
        Replica lógica SE() aninhada do Excel Parte10.
        """
        if pd.isna(dias_atraso):
            return 'Não calculado'
        
        dias = int(dias_atraso)
        
        if dias <= 0:
            return 'A vencer'
        elif dias <= 30:
            return 'Menor que 30 dias'
        elif dias <= 59:
            return 'De 31 a 59 dias'
        elif dias <= 89:
            return 'De 60 a 89 dias'
        elif dias <= 119:
            return 'De 90 a 119 dias'
        elif dias <= 359:
            return 'De 120 a 359 dias'  # Categoria principal FIDC
        elif dias <= 719:
            return 'De 360 a 719 dias'
        elif dias <= 1080:
            return 'De 720 a 1080 dias'
        else:
            return 'Maior que 1080 dias'

    def aplicar_classificacao_aging(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica classificação de aging para todo o DataFrame.
        """
        with st.spinner("🏷️ Aplicando classificação de aging..."):
            df = df.copy()

            # Aplicar classificação
            df['aging'] = df['dias_atraso'].apply(self.classificar_aging)
        
        return df
    
    def processar_aging_completo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executa todo o processo de cálculo de aging.
        COM CHECKPOINT: Evita reprocessamento se dados não mudaram.
        """
        if df.empty:
            st.warning("⚠️ DataFrame vazio - não é possível calcular aging")
            return df
        
        return usar_checkpoint(
            checkpoint_name="aging_completo",
            funcao_processamento=self._processar_aging_completo_interno,
            dataframes={"df_principal": df},
            parametros={
                "data_base": self.params.data_base.isoformat() if hasattr(self.params, 'data_base') else None
            },
            df=df
        )
    
    def _processar_aging_completo_interno(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Implementação interna do processamento de aging (sem checkpoint)
        """
        # Calcular dias de atraso
        df = self.calcular_dias_atraso(df)
        
        # Aplicar classificação
        df = self.aplicar_classificacao_aging(df)
        
        st.success("✅ Cálculo de aging concluído!")
        
        return df
