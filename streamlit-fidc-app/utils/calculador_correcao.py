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
    
    def mapear_aging_para_taxa(self, aging: str) -> str:
        """
        Mapeia aging detalhado para categorias de taxa de recuperação.
        """
        # Dicionário de mapeamento aging -> categoria taxa
        mapeamento = {
            'A vencer': 'A vencer',
            'Menor que 30 dias': 'Primeiro ano',
            'De 31 a 59 dias': 'Primeiro ano',
            'De 60 a 89 dias': 'Primeiro ano',
            'De 90 a 119 dias': 'Primeiro ano',
            'De 120 a 359 dias': 'Primeiro ano',
            'De 360 a 719 dias': 'Segundo ano',
            'De 720 a 1080 dias': 'Terceiro ano',
            'Maior que 1080 dias': 'Demais anos'
        }
        
        return mapeamento.get(aging, 'Não identificado')
    
    def adicionar_taxa_recuperacao(self, df: pd.DataFrame, df_taxa_recuperacao: pd.DataFrame) -> pd.DataFrame:
        """
        Adiciona taxa de recuperação e prazo de recebimento cruzando Empresa, Tipo e Aging.
        """
        if df.empty or df_taxa_recuperacao.empty:
            st.warning("⚠️ Dados insuficientes para calcular taxa de recuperação")
            df['aging_taxa'] = 'Não identificado'
            df['taxa_recuperacao'] = 0.0
            df['prazo_recebimento'] = 0
            df['valor_recuperavel'] = 0.0
            return df
        
        with st.spinner("🔄 Aplicando taxas de recuperação..."):
            df = df.copy()
            
            # Mapear aging detalhado para categorias de taxa
            df['aging_taxa'] = df['aging'].apply(self.mapear_aging_para_taxa)
            
            # Fazer merge com dados de taxa de recuperação
            # Chaves: Empresa, Tipo, Aging (mapeado)
            

            df_merged = df.merge(
                df_taxa_recuperacao,
                left_on=['empresa', 'tipo', 'aging_taxa'],
                right_on=['Empresa', 'Tipo', 'Aging'],
                how='left'
            )
            # st.dataframe(df[['empresa', 'tipo', 'aging_taxa']].drop_duplicates(), use_container_width=True)
            # st.dataframe(df_taxa_recuperacao[['Empresa', 'Tipo', 'Aging']].drop_duplicates(), use_container_width=True)
            # st.dataframe(df_merged, use_container_width=True)
            
            # Preencher valores não encontrados
            df_merged['Taxa de recuperação'] = df_merged['Taxa de recuperação'].fillna(0.0)
            df_merged['Prazo de recebimento'] = df_merged['Prazo de recebimento'].fillna(0)
            
            # Renomear colunas para padrão
            df_merged = df_merged.rename(columns={
                'Taxa de recuperação': 'taxa_recuperacao',
                'Prazo de recebimento': 'prazo_recebimento'
            })
            
            # Calcular valor recuperável (valor corrigido * taxa de recuperação)
            df_merged['valor_recuperavel'] = df_merged['valor_corrigido'] * (df_merged['taxa_recuperacao'])
            
            # Remover colunas duplicadas do merge
            colunas_para_remover = ['Empresa', 'Tipo', 'Aging']
            for col in colunas_para_remover:
                if col in df_merged.columns:
                    df_merged = df_merged.drop(columns=[col])
            
            # Estatísticas de match
            total_registros = len(df)
            registros_com_taxa = (df_merged['taxa_recuperacao'] > 0).sum()
            percentual_match = (registros_com_taxa / total_registros) * 100
            
            st.success(f"✅ Taxa de recuperação aplicada: {registros_com_taxa:,}/{total_registros:,} registros ({percentual_match:.1f}%)")
            
            # Mostrar estatísticas por categoria
            if registros_com_taxa > 0:
                stats_taxa = df_merged[df_merged['taxa_recuperacao'] > 0].groupby('aging_taxa').agg({
                    'taxa_recuperacao': ['count', 'mean'],
                    'valor_recuperavel': 'sum'
                }).round(2)
        
        return df_merged
    
    def gerar_resumo_recuperacao(self, df: pd.DataFrame, nome_base: str):
        """
        Gera resumo da recuperação.
        """
        if 'valor_recuperavel' not in df.columns:
            return
        
        # st.subheader(f"🎯 Resumo da Recuperação - {nome_base.upper()}")
        
        valor_corrigido = df['valor_corrigido'].sum()
        valor_recuperavel = df['valor_recuperavel'].sum()
        percentual_recuperacao = (valor_recuperavel / valor_corrigido) * 100 if valor_corrigido > 0 else 0
        
        # Breakdown por aging
        if 'aging_taxa' in df.columns:
            # st.subheader("📈 Recuperação por Aging")
            
            recovery_breakdown = df.groupby('aging_taxa').agg({
                'valor_corrigido': 'sum',
                'valor_recuperavel': 'sum',
                'taxa_recuperacao': 'mean'
            }).round(2)
            
            recovery_breakdown['percentual_recuperacao'] = (
                recovery_breakdown['valor_recuperavel'] / 
                recovery_breakdown['valor_corrigido'] * 100
            ).round(1)
            
            recovery_breakdown.columns = [
                'Valor Corrigido', 
                'Valor Recuperável', 
                'Taxa Média (%)', 
                'Recuperação (%)'
            ]
            
            # st.dataframe(recovery_breakdown, use_container_width=True)
    
    def processar_correcao_completa_com_recuperacao(self, df: pd.DataFrame, nome_base: str, df_taxa_recuperacao: pd.DataFrame = None) -> pd.DataFrame:
        """
        Executa todo o processo de correção monetária incluindo taxa de recuperação.
        """
        if df.empty:
            return df
        
        # Processamento padrão de correção
        df = self.processar_correcao_completa(df, nome_base)
        
        # Adicionar taxa de recuperação se disponível
        if df_taxa_recuperacao is not None and not df_taxa_recuperacao.empty:
            df = self.adicionar_taxa_recuperacao(df, df_taxa_recuperacao)
            
            # Gerar resumo com recuperação
            self.gerar_resumo_recuperacao(df, nome_base)
        else:
            # Gerar resumo padrão
            self.gerar_resumo_correcao(df, nome_base)
        
        return df
