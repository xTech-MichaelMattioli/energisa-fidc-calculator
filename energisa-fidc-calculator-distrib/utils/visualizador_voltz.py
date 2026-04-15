"""
Módulo de Visualização para VOLTZ
Responsável por exibir resultados específicos da VOLTZ de forma clara e organizada
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from .checkpoint_manager import checkpoint_manager
from .exportacao_csv_brasil import salvar_csv_brasil


class VisualizadorVoltz:
    """
    Classe responsável pela visualização dos resultados de cálculo da VOLTZ
    """
    
    def __init__(self):
        self.ordem_aging = [
            'Menor que 30 dias',
            'De 31 a 59 dias', 
            'De 60 a 89 dias',
            'De 90 a 119 dias',
            'De 120 a 359 dias',
            'De 360 a 719 dias',
            'De 720 a 1080 dias',
            'Maior que 1080 dias',
            'A vencer'
        ]
    
    def exibir_resultados_voltz(self, df_final: pd.DataFrame):
        """
        Exibe os resultados completos específicos para VOLTZ
        """
        st.markdown("---")
        st.subheader("⚡ Resultados da Correção VOLTZ")
        
        # Verificar colunas disponíveis
        colunas_voltz_basicas = ['valor_principal', 'juros_remuneratorios', 'saldo_devedor_vencimento']
        colunas_voltz_correcao = ['fator_igpm', 'correcao_monetaria', 'valor_corrigido']
        colunas_voltz_encargos = ['multa', 'juros_moratorios', 'esta_vencido']
        colunas_recuperacao = ['aging_taxa', 'taxa_recuperacao', 'valor_recuperavel_ate_data_base']
        
        tem_basicas = all(col in df_final.columns for col in colunas_voltz_basicas)
        tem_correcao = all(col in df_final.columns for col in colunas_voltz_correcao)
        tem_encargos = all(col in df_final.columns for col in colunas_voltz_encargos)
        tem_recuperacao = all(col in df_final.columns for col in colunas_recuperacao)
        
        # Exibir métricas principais da VOLTZ
        self._exibir_metricas_voltz(df_final, tem_basicas, tem_correcao, tem_encargos, tem_recuperacao)
        
        # Exibir resumo por status de contrato
        # self._exibir_resumo_por_status(df_final)
        
        # Exibir tabelas agrupadas
        self._exibir_tabelas_agrupadas_voltz(df_final, tem_recuperacao)
        
        # Exibir resumo consolidado
        self._exibir_resumo_consolidado_voltz(df_final, tem_recuperacao)
        
        # Exibir informações do processo VOLTZ
        self._exibir_info_processo_voltz()
    
    def _exibir_metricas_voltz(self, df_final: pd.DataFrame, tem_basicas: bool, tem_correcao: bool, tem_encargos: bool, tem_recuperacao: bool):
        """
        Exibe métricas principais específicas da VOLTZ
        """
        st.write("**📊 Métricas Principais - VOLTZ:**")
        
        # Primeira linha de métricas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if tem_basicas:
                total_principal = df_final['valor_principal'].sum()
                st.metric("💰 Valor Principal", f"R$ {total_principal:,.2f}")
            else:
                st.metric("💰 Valor Principal", "N/A")
        
        with col2:
            if tem_basicas:
                total_juros_rem = df_final['juros_remuneratorios'].sum()
                st.metric("⚡ Juros Remuneratórios", f"R$ {total_juros_rem:,.2f}")
            else:
                st.metric("⚡ Juros Remuneratórios", "N/A")
        
        with col3:
            if tem_basicas:
                total_saldo_venc = df_final['saldo_devedor_vencimento'].sum()
                st.metric("🎯 Saldo no Vencimento", f"R$ {total_saldo_venc:,.2f}")
            else:
                st.metric("🎯 Saldo no Vencimento", "N/A")

        # Segunda linha de métricas (apenas se tiver dados de correção/encargos)
        if tem_correcao or tem_encargos:
            st.write("")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if tem_encargos:
                    total_multa = df_final['multa'].sum()
                    st.metric("🚨 Multas", f"R$ {total_multa:,.2f}")
                else:
                    st.metric("🚨 Multas", "N/A")
            
            with col2:
                if tem_encargos:
                    total_juros_mora = df_final['juros_moratorios'].sum()
                    st.metric("⏰ Juros Moratórios", f"R$ {total_juros_mora:,.2f}")
                else:
                    st.metric("⏰ Juros Moratórios", "N/A")
            with col4:
                if tem_correcao:
                    total_corrigido = df_final['valor_corrigido'].sum()
                    st.metric("🔥 Valor Corrigido Final", f"R$ {total_corrigido:,.2f}")
                else:
                    st.metric("🔥 Valor Corrigido Final", "N/A")

            with col3:
                if tem_correcao:
                    total_corr_igpm = df_final['correcao_monetaria'].sum()
                    st.metric("📈 Correção IGP-M", f"R$ {total_corr_igpm:,.2f}")
                else:
                    st.metric("📈 Correção IGP-M", "N/A")
            
        # Segunda linha de métricas (apenas se tiver dados de correção/encargos)
        if tem_correcao or tem_encargos:
            st.write("")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if tem_recuperacao:
                    total_recuperavel = df_final['valor_recuperavel_ate_data_base'].sum()
                    st.metric("💎 Valor Recuperável", f"R$ {total_recuperavel:,.2f}")
                else:
                    st.metric("💎 Valor Recuperável", "N/A")
    
    def _exibir_resumo_por_status(self, df_final: pd.DataFrame):
        """
        Exibe resumo separando contratos vencidos e a vencer
        """
        if 'esta_vencido' not in df_final.columns:
            return
        
        st.markdown("---")
        
    
    def _exibir_tabelas_agrupadas_voltz(self, df_final: pd.DataFrame, tem_recuperacao: bool):
        """
        Exibe tabelas agrupadas específicas para VOLTZ
        """
        st.markdown("---")
        st.subheader("📊 Agrupamento Detalhado - VOLTZ")
        
        # Definir colunas de agregação para VOLTZ
        colunas_agg = {
            'valor_principal': 'sum',
            'valor_corrigido': 'sum'
        }
        
        # Adicionar colunas específicas da VOLTZ se disponíveis
        if 'juros_remuneratorios' in df_final.columns:
            colunas_agg['juros_remuneratorios'] = 'sum'
        
        if 'saldo_devedor_vencimento' in df_final.columns:
            colunas_agg['saldo_devedor_vencimento'] = 'sum'
        
        if 'correcao_monetaria' in df_final.columns:
            colunas_agg['correcao_monetaria'] = 'sum'
        
        if 'multa' in df_final.columns:
            colunas_agg['multa'] = 'sum'
        
        if 'juros_moratorios' in df_final.columns:
            colunas_agg['juros_moratorios'] = 'sum'
        
        if tem_recuperacao:
            colunas_agg['valor_recuperavel_ate_data_base'] = 'sum'
        
        # Definir colunas de agrupamento
        colunas_groupby = ['empresa']
        
        # Adicionar aging se disponível
        if 'aging' in df_final.columns:
            colunas_groupby.append('aging')
        
        if 'aging_taxa' in df_final.columns:
            colunas_groupby.append('aging_taxa')
        
        # Criar agrupamento
        df_agg = (
            df_final
            .groupby(colunas_groupby, dropna=False)
            .agg(colunas_agg)
            .reset_index()
        )
        
        # Ordenar se tiver aging
        if 'aging' in df_agg.columns:
            df_agg['aging'] = pd.Categorical(df_agg['aging'], categories=self.ordem_aging, ordered=True)
            df_agg = df_agg.sort_values(['empresa', 'aging'])
        else:
            df_agg = df_agg.sort_values(['empresa'])
        
        st.dataframe(df_agg, use_container_width=True, hide_index=True)
        
        # Exibir tabela consolidada por aging (se disponível)
        if 'aging_taxa' in df_final.columns:
            st.subheader("🎯 Consolidado por Aging - VOLTZ")
            
            df_agg_aging = (
                df_final
                .groupby(['aging_taxa'], dropna=False)
                .agg(colunas_agg)
                .reset_index()
            )
            
            st.dataframe(df_agg_aging, use_container_width=True, hide_index=True)
    
    def _exibir_resumo_consolidado_voltz(self, df_final: pd.DataFrame, tem_recuperacao: bool):
        """
        Exibe resumo consolidado por empresa para VOLTZ
        """
        st.markdown("---")
        st.subheader("💰 Resumo Consolidado por Empresa - VOLTZ")
        
        # Definir colunas para resumo por empresa
        colunas_resumo = {
            'valor_principal': 'sum',
            'valor_corrigido': 'sum'
        }
        
        if 'juros_remuneratorios' in df_final.columns:
            colunas_resumo['juros_remuneratorios'] = 'sum'
        
        if 'saldo_devedor_vencimento' in df_final.columns:
            colunas_resumo['saldo_devedor_vencimento'] = 'sum'
        
        if 'correcao_monetaria' in df_final.columns:
            colunas_resumo['correcao_monetaria'] = 'sum'
        
        if 'multa' in df_final.columns:
            colunas_resumo['multa'] = 'sum'
        
        if 'juros_moratorios' in df_final.columns:
            colunas_resumo['juros_moratorios'] = 'sum'
        
        if tem_recuperacao:
            colunas_resumo['valor_recuperavel_ate_data_base'] = 'sum'
        
        # Criar resumo por empresa
        df_resumo = (
            df_final
            .groupby('empresa', dropna=False)
            .agg(colunas_resumo)
            .reset_index()
        )
        
        # Formatação para exibição
        df_display = df_resumo.copy()
        
        # Aplicar formatação brasileira
        colunas_valor = [col for col in colunas_resumo.keys()]
        for col in colunas_valor:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        # Renomear colunas para exibição
        nomes_colunas = {
            'empresa': '🏢 Empresa',
            'valor_principal': '💰 Valor Principal',
            'juros_remuneratorios': '⚡ Juros Remuneratórios',
            'saldo_devedor_vencimento': '🎯 Saldo no Vencimento',
            'correcao_monetaria': '📈 Correção IGP-M',
            'multa': '🚨 Multas',
            'juros_moratorios': '⏰ Juros Moratórios',
            'valor_corrigido': '🔥 Valor Corrigido Final',
            'valor_recuperavel_ate_data_base': '💎 Valor Recuperável'
        }
        
        df_display = df_display.rename(columns=nomes_colunas)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Totais gerais
        st.markdown("---")
        st.subheader("📊 Totais Gerais - VOLTZ")
        
        # Calcular totais
        total_principal = df_resumo['valor_principal'].sum()
        total_corrigido = df_resumo['valor_corrigido'].sum()
        
        # Criar métricas de totais baseado no que está disponível
        if tem_recuperacao and 'valor_recuperavel_ate_data_base' in df_resumo.columns:
            col1, col2, col3 = st.columns(3)
            total_recuperavel = df_resumo['valor_recuperavel_ate_data_base'].sum()
        else:
            col1, col2 = st.columns(2)
        
        with col1:
            st.metric("💰 Total Principal", f"R$ {total_principal:,.2f}")
        
        with col2:
            st.metric("🔥 Total Corrigido", f"R$ {total_corrigido:,.2f}")
        
        if tem_recuperacao and 'valor_recuperavel_ate_data_base' in df_resumo.columns:
            with col3:
                st.metric("💎 Total Recuperável", f"R$ {total_recuperavel:,.2f}")
    
    def _exibir_info_processo_voltz(self):
        """
        Exibe informações específicas do processo VOLTZ
        """
        st.markdown("---")
        st.subheader("ℹ️ Informações do Processo VOLTZ")
        
        with st.expander("⚡ Características Específicas da VOLTZ", expanded=False):
            st.info("""
            **🔍 Regras VOLTZ Aplicadas:**
            
            **📋 ETAPA 1 - Cálculo Base:**
            - ✅ Juros Remuneratórios: 4,65% aplicados diretamente sobre valor principal (taxa fixa)
            - ✅ Saldo Devedor no Vencimento = Valor Principal + Juros Remuneratórios
            
            **📋 ETAPA 2 - Correção Monetária:**
            - ✅ Correção IGP-M: aplicada sobre saldo devedor (do vencimento até data base)
            - ✅ Fonte: Aba específica 'IGPM' do arquivo de índices
            
            **📋 ETAPA 3A - Contratos A VENCER:**
            - ✅ Valor Final = Saldo Devedor + Correção IGP-M
            
            **📋 ETAPA 3B - Contratos VENCIDOS:**
            - ✅ Multa: 2% sobre saldo devedor no vencimento  
            - ✅ Juros Moratórios: 1,0% a.m. sobre saldo devedor no vencimento (período: vencimento → data base)
            - ✅ Valor Final = Saldo Corrigido IGP-M + Multa + Juros Moratórios
            
            **🎯 CARACTERÍSTICAS ESPECIAIS:**
            - 📍 Sempre IGP-M (nunca IPCA, mesmo após 2021)
            - 💼 Contratos CCBs (Cédulas de Crédito Bancário)
            - ⚡ Sistema otimizado com processamento vetorizado
            - 🎯 Não utiliza DI-PRE (específico da VOLTZ)
            """)
        
        with st.expander("💡 Fórmulas VOLTZ", expanded=False):
            st.write("""
            **📐 Fórmulas Utilizadas na VOLTZ:**
            
            **1. Juros Remuneratórios:**
            ```
            Juros Remuneratórios = Valor Principal × 4,65%
            ```
            
            **2. Saldo no Vencimento:**
            ```
            Saldo Devedor = Valor Principal + Juros Remuneratórios
            ```
            
            **3. Correção IGP-M:**
            ```
            Fator Correção = IGP-M(data_base) / IGP-M(vencimento)
            Correção Monetária = Saldo Devedor × (Fator - 1)
            ```
            
            **4. Para Contratos Vencidos:**
            ```
            Multa = Saldo Devedor × 2%
            Juros Moratórios = Saldo Devedor × [(1 + 1%)^meses_atraso - 1]
            ```
            
            **5. Valor Final:**
            ```
            A Vencer: Saldo Corrigido IGP-M
            Vencidos: Saldo Corrigido IGP-M + Multa + Juros Moratórios
            ```
            """)
    
    def exibir_exportacao_voltz(self, df_final: pd.DataFrame):
        """
        Exibe opções de exportação específicas para VOLTZ
        """
        st.markdown("---")
        st.subheader("💾 Exportação dos Dados VOLTZ")
        
        st.info(f"""
        **📋 Dados VOLTZ prontos para exportação:**
        - **Total de registros:** {len(df_final):,}
        - **Total de colunas:** {len(df_final.columns)}
        - **Conteúdo:** Registros processados com cálculos específicos VOLTZ
        """)
        
        # Ordenação específica para VOLTZ
        colunas_ordem_voltz = [
            'nome_cliente', 'documento', 'contrato', 'classe', 'situacao',
            'valor_principal', 'juros_remuneratorios', 'saldo_devedor_vencimento',
            'data_vencimento', 'empresa', 'tipo', 'status', 'esta_vencido',
            'dias_atraso', 'meses_atraso', 'aging', 'aging_taxa',
            'indice_vencimento', 'indice_base', 'fator_igpm', 
            'correcao_monetaria', 'multa', 'juros_moratorios', 'valor_corrigido',
            'taxa_recuperacao', 'valor_recuperavel_ate_data_base'
        ]
        
        # Preview dos dados
        preview_df = df_final.head(10).copy()
        
        # Reordenar conforme especificação VOLTZ
        colunas_existentes = [col for col in colunas_ordem_voltz if col in preview_df.columns]
        colunas_restantes = [col for col in preview_df.columns if col not in colunas_ordem_voltz]
        preview_df = preview_df[colunas_existentes + colunas_restantes]
        
        st.dataframe(preview_df, use_container_width=True, hide_index=True)
        
        # Botão para salvar
        if st.button("💾 Salvar Dados VOLTZ Completos", type="primary", use_container_width=True, key="salvar_dados_voltz"):
            try:
                # Criar timestamp para nome do arquivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo = f"FIDC_VOLTZ_Dados_Finais_{timestamp}.csv"
                caminho_arquivo = f"data/{nome_arquivo}"
                
                # Reordenar DataFrame completo
                df_export = df_final.copy()
                colunas_existentes_completo = [col for col in colunas_ordem_voltz if col in df_export.columns]
                colunas_restantes_completo = [col for col in df_export.columns if col not in colunas_ordem_voltz]
                df_export = df_export[colunas_existentes_completo + colunas_restantes_completo]
                
                # Salvar arquivo no formato brasileiro com truncamento para 2 casas
                df_export = salvar_csv_brasil(df_export, caminho_arquivo, casas_decimais=4)
                
                st.success(f"✅ **Dados VOLTZ salvos com sucesso!**")
                st.info(f"📄 **Arquivo:** `{nome_arquivo}`")
                st.info(f"📂 **Local:** `{caminho_arquivo}`")
                st.info(f"📊 **Registros:** {len(df_export):,}")
                st.info(f"📋 **Colunas:** {len(df_export.columns)}")
                
            except Exception as e:
                st.error(f"❌ Erro ao salvar arquivo: {str(e)}")
    
    def exibir_limpar_cache(self):
        """
        Exibe botão para limpar cache
        """
        if st.button("🗑️ Limpar Cache", key="limpar_cache_voltz"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache limpo com sucesso!")
            st.experimental_rerun()
    
    def exibir_gerenciamento_checkpoints(self):
        """
        Exibe interface para gerenciar checkpoints de dados
        """
        st.markdown("---")
        st.subheader("📋 Gerenciamento de Checkpoints")
        
        st.info("""
        **🚀 Sistema de Checkpoints Inteligentes**
        
        Os checkpoints evitam reprocessamento desnecessário dos dados quando:
        - Os DataFrames não mudaram (detectado via hash MD5)
        - Os parâmetros de cálculo são os mesmos
        - Os dados de entrada são idênticos
        
        **Benefícios:**
        - ⚡ **Performance**: Até 95% mais rápido em recálculos
        - 🧠 **Memória**: Otimização automática de uso
        - 🔄 **Consistência**: Resultados sempre consistentes
        """)
        
        # Exibir status dos checkpoints
        checkpoint_manager.exibir_status_checkpoints()
