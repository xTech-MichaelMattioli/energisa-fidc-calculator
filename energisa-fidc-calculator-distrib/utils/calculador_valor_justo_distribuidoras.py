"""
Módulo específico para cálculo de valor justo de distribuidoras padrão (não-VOLTZ)
Este módulo contém toda a lógica específica para distribuidoras tradicionais
que precisam do cálculo completo de valor justo após a correção monetária base.
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
import time

class CalculadorValorJusto:
    """Classe auxiliar para estatísticas do DI-PRE"""
    
    def obter_estatisticas_di_pre(self, df_di_pre):
        """Obtém estatísticas do DataFrame DI-PRE"""
        if df_di_pre is None or df_di_pre.empty:
            return {}
        
        return {
            'total_registros': len(df_di_pre),
            'prazo_min': df_di_pre['meses_futuros'].min(),
            'prazo_max': df_di_pre['meses_futuros'].max(),
            'taxa_media': df_di_pre['252'].mean(),
            'taxa_min': df_di_pre['252'].min(),
            'taxa_max': df_di_pre['252'].max()
        }

class CalculadorValorJustoDistribuidoras:
    """
    Classe responsável pelo cálculo completo de valor justo para distribuidoras padrão
    (todas exceto VOLTZ, que tem seu próprio fluxo otimizado)
    """
    
    def __init__(self, params):
        self.params = params
    
    def processar_valor_justo_distribuidoras(self, df_final_temp, log_container, progress_main):
        """
        Processa o cálculo completo de valor justo para distribuidoras padrão
        
        Args:
            df_final_temp: DataFrame com dados básicos já processados
            log_container: Container do Streamlit para logs
            progress_main: Barra de progresso principal
            
        Returns:
            DataFrame com valor justo calculado
        """
        
        try:
            # ============= PREPARAR DADOS BASE (ULTRA-RÁPIDO) =============
            # Garantir que data_base seja datetime
            if 'data_base' not in df_final_temp.columns:
                df_final_temp['data_base'] = datetime.now()
            df_final_temp['data_base'] = pd.to_datetime(df_final_temp['data_base'], errors='coerce')
            
            progress_main.progress(0.82)

            progress_main.progress(0.85)
            
            # ============= CÁLCULO DO PERÍODO ATÉ RECEBIMENTO (MERGE OTIMIZADO) =============
            with log_container:
                st.info("📊 **Merge dinâmico** de prazos de recebimento...")
            
            df_final_temp = self._calcular_meses_recebimento(df_final_temp, log_container)
            
            # ============= MERGE OTIMIZADO COM TAXAS DI-PRE (VETORIZADO) =============
            with log_container:
                st.info("📊 **Merge vetorizado** com taxas DI-PRE por prazo...")
            
            df_final_temp = self._aplicar_taxas_di_pre(df_final_temp, log_container)
            
            # ============= CÁLCULO DA TAXA DI-PRE ANUALIZADA (VETORIZADO) =============
            df_final_temp = self._calcular_taxas_anualizadas(df_final_temp)
            
            # ============= CÁLCULO DO IPCA MENSAL REAL DOS DADOS DO EXCEL =============
            df_final_temp = self._calcular_ipca_mensal(df_final_temp, log_container)
            
            # ============= CÁLCULO FINAL DO VALOR JUSTO =============
            progress_main.progress(0.88)
            
            with log_container:
                st.info("💰 **Calculando Valor Justo** conforme orientação do Thiago...")
            
            df_final_temp = self._calcular_valor_justo_final(df_final_temp, log_container)
            
            progress_main.progress(0.92)
            
            return df_final_temp
            
        except Exception as e:
            st.error(f"❌ Erro no cálculo do valor justo para distribuidoras: {str(e)}")
            raise e
    
    def _calcular_meses_recebimento(self, df_final_temp, log_container):
        """Calcula os meses até recebimento baseado na taxa de recuperação"""
        
        try:
            # Verificar se temos dados de taxa de recuperação carregados
            if 'df_taxa_recuperacao' in st.session_state and not st.session_state.df_taxa_recuperacao.empty:
                df_taxa = st.session_state.df_taxa_recuperacao.copy()
                
                # Fazer merge para pegar o prazo_recebimento baseado em empresa, tipo e aging
                df_final_temp = df_final_temp.merge(
                    df_taxa[['Empresa', 'Tipo', 'Aging', 'Prazo de recebimento']],
                    left_on=['empresa', 'tipo', 'aging_taxa'],
                    right_on=['Empresa', 'Tipo', 'Aging'],
                    how='left'
                )
                
                # Usar prazo_recebimento do merge, com fallback para valor padrão
                df_final_temp['meses_ate_recebimento'] = df_final_temp['Prazo de recebimento'].fillna(6).astype(int)
                
                # Limpar colunas auxiliares do merge
                colunas_merge = ['Empresa', 'Tipo', 'Aging', 'Prazo de recebimento']
                df_final_temp = df_final_temp.drop(columns=[col for col in colunas_merge if col in df_final_temp.columns])
                
                # Mostrar estatísticas do mapeamento
                contagem_meses = df_final_temp['meses_ate_recebimento'].value_counts().sort_index()
                
                with log_container:
                    st.success(f"✅ **Meses de recebimento** obtidos dinamicamente!")
                
                # Mostrar distribuição em um formato mais compacto
                distribuicao_str = ", ".join([f"{meses}m: {count:,}" for meses, count in contagem_meses.items()])
                with log_container:
                    st.info(f"📊 **Distribuição:** {distribuicao_str}")
            else:
                raise Exception("Dados de taxa de recuperação não encontrados no session_state")
                        
        except Exception as e:
            with log_container:
                st.warning(f"⚠️ Erro ao usar dados da taxa de recuperação: {str(e)}")
                st.info("📊 Usando valores padrão para meses de recebimento...")
            
            # Fallback para valores padrão baseados no aging_taxa
            def calcular_meses_fallback(row):
                aging_taxa = str(row.get('aging_taxa', 'Geral')).strip().lower()
                if 'vencer' in aging_taxa:
                    return 6
                elif 'primeiro' in aging_taxa:
                    return 6
                elif 'segundo' in aging_taxa:
                    return 6
                elif 'terceiro' in aging_taxa:
                    return 6
                elif 'quarto' in aging_taxa:
                    return 6
                elif 'quinto' in aging_taxa:
                    return 6
                elif 'demais' in aging_taxa:
                    return 6
                else:
                    return 6
            
            df_final_temp['meses_ate_recebimento'] = df_final_temp.apply(calcular_meses_fallback, axis=1)
        
        return df_final_temp
    
    def _aplicar_taxas_di_pre(self, df_final_temp, log_container):
        """Aplica as taxas DI-PRE baseadas no prazo de recebimento"""
        
        # Verificar se temos dados DI-PRE disponíveis
        if 'df_di_pre' in st.session_state and not st.session_state.df_di_pre.empty:
            df_di_pre = st.session_state.df_di_pre.copy()
            
            # Preparar dados DI-PRE para merge
            df_di_pre_merge = df_di_pre[['meses_futuros', '252']].copy()
            df_di_pre_merge.rename(columns={
                'meses_futuros': 'meses_ate_recebimento',
                '252': 'taxa_di_pre_percentual'
            }, inplace=True)
            
            # Merge direto usando meses_ate_recebimento (ULTRA-RÁPIDO)
            df_final_temp = df_final_temp.merge(
                df_di_pre_merge,
                on='meses_ate_recebimento',
                how='left'
            )
            
            # Para registros sem match exato, buscar o mais próximo
            mask_sem_taxa = df_final_temp['taxa_di_pre_percentual'].isna()
            registros_sem_taxa = mask_sem_taxa.sum()
            
            if registros_sem_taxa > 0:
                with log_container:
                    st.info(f"📊 **Buscando taxas mais próximas** para {registros_sem_taxa:,} registros...")
                
                # Para cada prazo único sem taxa, encontrar o mais próximo
                prazos_sem_taxa = df_final_temp[mask_sem_taxa]['meses_ate_recebimento'].unique()
                
                for prazo in prazos_sem_taxa:
                    # Calcular distância para todos os prazos disponíveis no DI-PRE
                    df_di_pre['diferenca'] = abs(df_di_pre['meses_futuros'] - prazo)
                    linha_mais_proxima = df_di_pre.loc[df_di_pre['diferenca'].idxmin()]
                    taxa_proxima = linha_mais_proxima['252']
                    
                    # Aplicar para todos os registros com esse prazo
                    mask_prazo = (df_final_temp['meses_ate_recebimento'] == prazo) & mask_sem_taxa
                    df_final_temp.loc[mask_prazo, 'taxa_di_pre_percentual'] = taxa_proxima
                    
                    with log_container:
                        st.info(f"📊 Prazo {prazo}m → CDI {taxa_proxima:.3f}% (mais próximo: {linha_mais_proxima['meses_futuros']}m)")
            
            # Converter percentual para decimal
            df_final_temp['taxa_di_pre_decimal'] = df_final_temp['taxa_di_pre_percentual'] / 100
            
            # Estatísticas do merge
            registros_com_taxa = (~df_final_temp['taxa_di_pre_decimal'].isna()).sum()
            taxa_media = df_final_temp['taxa_di_pre_decimal'].mean() * 100
            
            with log_container:
                st.success(f"✅ **Merge DI-PRE concluído:** {registros_com_taxa:,}/{len(df_final_temp):,} registros com taxa (média: {taxa_media:.3f}%)")
        
        else:
            # Fallback para taxa padrão
            with log_container:
                st.warning("⚠️ Dados DI-PRE não disponíveis. Usando taxa padrão.")
            df_final_temp['taxa_di_pre_decimal'] = 0.10  # 10% ao ano como fallback
            df_final_temp['taxa_di_pre_percentual'] = 10.0
        
        return df_final_temp
    
    def _calcular_taxas_anualizadas(self, df_final_temp):
        """Calcula as taxas anualizadas com spread de risco"""
        
        # Aplicar spread de risco de 2.5% sobre a taxa DI-PRE
        spread_risco = 2.5  # 2.5%
        df_final_temp['taxa_di_pre_total_anual'] = (1 + df_final_temp['taxa_di_pre_decimal']) * (1 + spread_risco / 100) - 1

        # Converter taxa anual para mensal: (1 + taxa_anual)^(1/12) - 1
        df_final_temp['taxa_desconto_mensal'] = (1 + df_final_temp['taxa_di_pre_total_anual']) ** (1/12) - 1
            
        # Data estimada de recebimento (data_base + meses_ate_recebimento)
        def calcular_data_recebimento(row):
            try:
                data_base = row.get('data_base', datetime.now())
                meses = row.get('meses_ate_recebimento', 30)
                return pd.to_datetime(data_base) + pd.DateOffset(months=int(meses))
            except:
                return datetime.now() + pd.DateOffset(months=30)
        
        df_final_temp['data_recebimento_estimada'] = df_final_temp.apply(calcular_data_recebimento, axis=1)
        
        return df_final_temp
    
    def _calcular_ipca_mensal(self, df_final_temp, log_container):
        """Calcula o IPCA mensal baseado nos índices carregados"""
        
        st.info("📊 Calculando IPCA/IGPM mensal real baseado nos índices carregados...")

        # Buscar data atual e data de 12 meses atrás nos dados carregados
        data_hoje = datetime.now()
        data_12m_atras = data_hoje - pd.DateOffset(months=12)
        
        # Formatar datas para busca (YYYY.MM)
        data_hoje_formatada = data_hoje.strftime('%Y.%m')
        data_12m_formatada = data_12m_atras.strftime('%Y.%m')
        
        # ========== SELEÇÃO INTELIGENTE DOS ÍNDICES PARA CÁLCULO IPCA ==========
        if 'df_indices_economicos' in st.session_state:
            df_indices = st.session_state.df_indices_economicos.copy()
            tipo_calculo = "IGPM_IPCA (Distribuidoras)"
        elif 'df_indices_igpm' in st.session_state:
            df_indices = st.session_state.df_indices_igpm.copy()
            tipo_calculo = "IGPM (Fallback)"
        else:
            raise Exception("Nenhum índice disponível para cálculo do IPCA")
        
        st.info(f"📊 Usando {tipo_calculo} para cálculo do IPCA mensal")
        df_indices['data_formatada'] = df_indices['data'].dt.strftime('%Y.%m')
        
        # Buscar índice atual (mais próximo da data de hoje)
        indice_atual = None
        indice_12m = None
        
        # Tentar encontrar índice exato, senão buscar o mais próximo
        filtro_atual = df_indices[df_indices['data_formatada'] == data_hoje_formatada]
        if not filtro_atual.empty:
            indice_atual = filtro_atual.iloc[0]['indice']
        else:
            # Buscar o mais recente disponível
            df_indices_ordenado = df_indices.sort_values('data', ascending=False)
            indice_atual = df_indices_ordenado.iloc[0]['indice']
            st.info(f"📅 Usando índice mais recente disponível: {df_indices_ordenado.iloc[0]['data'].strftime('%Y-%m')}")
        
        # Buscar índice de 12 meses atrás
        filtro_12m = df_indices[df_indices['data_formatada'] == data_12m_formatada]
        if not filtro_12m.empty:
            indice_12m = filtro_12m.iloc[0]['indice']
        else:
            # Buscar o mais próximo de 12 meses atrás
            df_indices['diferenca_12m'] = abs((df_indices['data'] - data_12m_atras).dt.days)
            indice_mais_proximo_12m = df_indices.loc[df_indices['diferenca_12m'].idxmin()]
            indice_12m = indice_mais_proximo_12m['indice']
            st.info(f"📅 Usando índice mais próximo de 12m atrás: {indice_mais_proximo_12m['data'].strftime('%Y-%m')}")
        
        # Calcular IPCA anual e mensal
        if indice_atual and indice_12m and indice_12m > 0:
            # IPCA anual = (índice_atual / índice_12m_atrás) - 1
            ipca_anual = (indice_atual / indice_12m) - 1
            
            # IPCA mensal = (1 + ipca_anual)^(1/12) - 1
            ipca_mensal_calculado = ((1 + ipca_anual) ** (1/12)) - 1
            
            # Aplicar o IPCA mensal calculado para todos os registros
            df_final_temp['ipca_mensal'] = ipca_mensal_calculado
            
            st.success(f"""
            ✅ **IPCA mensal calculado com dados reais do Excel!**
            📊 Índice Atual: {indice_atual:.2f}
            📊 Índice 12m Atrás: {indice_12m:.2f}
            📈 IPCA Anual: {ipca_anual*100:.2f}%
            🔢 IPCA Mensal: {ipca_mensal_calculado*100:.4f}%
            """)
            
        else:
            # Fallback se não conseguir calcular
            df_final_temp['ipca_mensal'] = 0.0037  # 4.5% ao ano
            st.warning("⚠️ Não foi possível calcular IPCA dos dados. Usando taxa padrão de 4.5% a.a.")
        
        # Calcular o fator de correção com IPCA
        df_final_temp['fator_correcao_ate_recebimento'] = (1 + df_final_temp['ipca_mensal']) ** df_final_temp['meses_ate_recebimento']

        # Aplicar taxa de desconto
        df_final_temp['fator_de_desconto'] = (1 + df_final_temp['taxa_desconto_mensal'] ) ** df_final_temp['meses_ate_recebimento']
        
        # Calcular multa por atraso
        data_atual = datetime.now()
        df_final_temp['dias_atraso'] = (data_atual - df_final_temp['data_recebimento_estimada']).dt.days.clip(lower=0)
        
        # Multa por atraso: 1% ao mês = 0.01/30 por dia
        taxa_multa_diaria = 0.01 / 30
        df_final_temp['multa_atraso'] = df_final_temp['dias_atraso'] * taxa_multa_diaria
        
        # Aplicar multa mínima de 6% mesmo sem atraso (margem de segurança)
        multa_minima = 0.06
        df_final_temp['multa_final'] = df_final_temp['multa_atraso'].clip(lower=multa_minima)
        
        return df_final_temp
    
    def _calcular_valor_justo_final(self, df_final_temp, log_container):
        """Calcula o valor justo final conforme orientação do Thiago"""
        
        # ===== PASSO 1: VERIFICAR SE TEMOS VALOR RECUPERÁVEL =====
        if 'valor_recuperavel_ate_recebimento' not in df_final_temp.columns:
            if 'taxa_recuperacao' in df_final_temp.columns:
                # Calcular valor recuperável = valor_corrigido × taxa_recuperacao
                df_final_temp['valor_recuperavel_ate_recebimento'] = df_final_temp['valor_corrigido'] * df_final_temp['taxa_recuperacao']
            else:
                # Fallback: valor recuperável = valor corrigido (100% de recuperação)
                df_final_temp['valor_recuperavel_ate_recebimento'] = df_final_temp['valor_corrigido']
        
        # ===== PASSO 2: USAR TAXAS CDI JÁ CALCULADAS NO MERGE OTIMIZADO =====
        with log_container:
            st.info("📊 **Usando taxas CDI** já calculadas no merge vetorizado...")
        
        # As taxas CDI já foram calculadas no merge otimizado acima
        # Usamos 'taxa_di_pre_decimal' que já contém as taxas específicas por prazo
        df_final_temp['cdi_taxa_prazo'] = df_final_temp['taxa_di_pre_decimal']
        
        # ===== PASSO 3: APLICAR SPREAD DE RISCO DE 2.5% =====
        spread_risco = 0.025  # 2.5% a.a.
        df_final_temp['taxa_desconto_total'] = df_final_temp['cdi_taxa_prazo'] + spread_risco
        
        # ===== PASSO 4: CALCULAR FATOR DE DESCONTO CONFORME THIAGO =====
        # Fórmula: (1 + CDI + 2,5%)^(prazo_recebimento/12)
        df_final_temp['anos_ate_recebimento'] = df_final_temp['meses_ate_recebimento'] / 12
        df_final_temp['fator_desconto_thiago'] = (1 + df_final_temp['taxa_desconto_total']) ** df_final_temp['anos_ate_recebimento']
        
        # ===== PASSO 5: CÁLCULO FINAL DO VALOR JUSTO =====
        # Fórmula do Thiago: Valor Justo = Valor Recuperável ÷ (1 + CDI + 2,5%)^(prazo_recebimento/12)
        df_final_temp['valor_justo_ate_recebimento'] = df_final_temp['valor_recuperavel_ate_recebimento'] / df_final_temp['fator_desconto_thiago']
        
        # ===== PASSO 6: ESTATÍSTICAS DO CÁLCULO =====
        with log_container:
            valor_total_recuperavel = df_final_temp['valor_recuperavel_ate_recebimento'].sum()
            valor_total_justo = df_final_temp['valor_justo_ate_recebimento'].sum()
            desconto_percentual = (1 - valor_total_justo / valor_total_recuperavel) * 100
            
            st.success(f"""
            ✅ **Valor Justo calculado conforme Thiago!**
            💰 Total Recuperável: R$ {valor_total_recuperavel:,.2f}
            💎 Total Valor Justo: R$ {valor_total_justo:,.2f}
            📉 Desconto Aplicado: {desconto_percentual:.2f}%
            
            🔢 **Fórmula:** Valor Recuperável ÷ (1 + CDI + 2,5%)^(meses/12)
            📊 **Spread:** CDI + 2,5% a.a.
            📅 **Base:** 18/09/2025 + prazo recuperação
            """)
            
            # Mostrar distribuição por prazo
            distribuicao_prazo = df_final_temp.groupby('meses_ate_recebimento').agg({
                'valor_justo_ate_recebimento': 'sum',
                'taxa_desconto_total': 'first'
            }).reset_index()
            
            st.write("**📊 Distribuição por Prazo:**")
            for _, row in distribuicao_prazo.iterrows():
                prazo = int(row['meses_ate_recebimento'])
                valor = row['valor_justo_ate_recebimento']
                taxa = row['taxa_desconto_total'] * 100
                st.info(f"📅 {prazo}m: R$ {valor:,.2f} (taxa {taxa:.2f}%)")
        
        # ===== ADICIONAR COLUNAS DE CONTROLE =====
        df_final_temp['data_calculo'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Calcular valor_recuperavel_ate_recebimento
        df_final_temp['valor_recuperavel_ate_recebimento'] = (
            df_final_temp['valor_recuperavel_ate_data_base'] * (df_final_temp['fator_correcao_ate_recebimento'] + df_final_temp['multa_final'])
        )

        # Remove a coluna 'valor_recuperavel_ate_recebimento' se existir
        if 'valor_recuperavel_ate_recebimento' in df_final_temp.columns:
            df_final_temp = df_final_temp.drop(columns=['valor_recuperavel_ate_recebimento'])
        
        return df_final_temp
