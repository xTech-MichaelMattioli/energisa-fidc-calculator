"""
Módulo de Visualização para Distribuidoras Gerais
Responsável por exibir resultados das demais distribuidoras (não VOLTZ) com DI-PRE
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from .exportacao_csv_brasil import salvar_csv_brasil


class VisualizadorDistribuidoras:
    """
    Classe responsável pela visualização dos resultados de cálculo das distribuidoras gerais
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
    
    def exibir_resultados_distribuidoras(self, df_final: pd.DataFrame):
        """
        Exibe os resultados completos para distribuidoras gerais
        """
        st.markdown("---")
        st.subheader("💰 Resultados da Correção Monetária e Valor Justo")
        
        # Verificar colunas disponíveis
        colunas_basicas = ['valor_principal', 'valor_liquido', 'valor_corrigido']
        colunas_recuperacao = ['aging_taxa', 'taxa_recuperacao', 'prazo_recebimento', 'valor_recuperavel_ate_recebimento']
        colunas_valor_justo = ['valor_justo']
        colunas_valor_justo_reajustado = ['valor_justo_reajustado', 'desconto_aging_perc', 'desconto_aging_valor']
        colunas_di_pre = ['fator_correcao_ate_recebimento', 'taxa_di_pre_mensal_efetiva', 'taxa_di_pre_aplicada', 'spread_risco_aplicado']
        
        tem_basicas = all(col in df_final.columns for col in colunas_basicas)
        tem_recuperacao = all(col in df_final.columns for col in colunas_recuperacao)
        tem_valor_justo = all(col in df_final.columns for col in colunas_valor_justo)
        tem_valor_justo_reajustado = all(col in df_final.columns for col in colunas_valor_justo_reajustado)
        tem_di_pre = all(col in df_final.columns for col in colunas_di_pre)
        
        # Exibir métricas principais
        self._exibir_metricas_distribuidoras(df_final, tem_basicas, tem_recuperacao, tem_valor_justo, tem_valor_justo_reajustado)
        
        # Exibir detalhes do cálculo DI-PRE se disponível
        if tem_di_pre:
            self._exibir_detalhes_di_pre(df_final)
        
        # Exibir tabelas agrupadas
        self._exibir_tabelas_agrupadas_distribuidoras(df_final, tem_recuperacao, tem_valor_justo, tem_valor_justo_reajustado, tem_di_pre)
        
        # Exibir resumo consolidado
        self._exibir_resumo_consolidado_distribuidoras(df_final, tem_recuperacao, tem_valor_justo, tem_valor_justo_reajustado)
    
    def _exibir_metricas_distribuidoras(self, df_final: pd.DataFrame, tem_basicas: bool, tem_recuperacao: bool, tem_valor_justo: bool, tem_valor_justo_reajustado: bool):
        """
        Exibe métricas principais das distribuidoras
        """
        st.write("**📊 Métricas Principais:**")

        total_registros = len(df_final)
        empresas = df_final['empresa'].nunique() if 'empresa' in df_final.columns else 0

        coluna_principal = 'valor_principal_limpo' if 'valor_principal_limpo' in df_final.columns else 'valor_principal'
        total_principal = df_final[coluna_principal].sum() if coluna_principal in df_final.columns else 0

        if 'correcao_monetaria' in df_final.columns:
            total_correcao_monetaria = df_final['correcao_monetaria'].sum()
        else:
            total_corrigido = df_final['valor_corrigido'].sum() if 'valor_corrigido' in df_final.columns else 0
            total_liquido = df_final['valor_liquido'].sum() if 'valor_liquido' in df_final.columns else 0
            total_correcao_monetaria = max(total_corrigido - total_liquido, 0)

        coluna_valor_justo = None
        if tem_valor_justo_reajustado and 'valor_justo_reajustado' in df_final.columns:
            coluna_valor_justo = 'valor_justo_reajustado'
        elif tem_valor_justo and 'valor_justo' in df_final.columns:
            coluna_valor_justo = 'valor_justo'

        total_valor_justo = df_final[coluna_valor_justo].sum() if coluna_valor_justo else 0

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("📊 Total Registros", f"{total_registros:,}")

        with col2:
            st.metric("📊 Valor Principal", f"R$ {total_principal:,.2f}")

        with col3:
            st.metric("⚡ Correção Monetária", f"R$ {total_correcao_monetaria:,.2f}")

        with col4:
            if coluna_valor_justo:
                st.metric("💎 Valor Justo", f"R$ {total_valor_justo:,.2f}")
            else:
                st.metric("💎 Valor Justo", "N/A")

        with col5:
            st.metric("🏢 Empresas", f"{empresas}")

        if coluna_valor_justo == 'valor_justo_reajustado':
            st.caption("Valor Justo exibido com base em valor_justo_reajustado (pós-RV).")
    
    def _exibir_detalhes_di_pre(self, df_final: pd.DataFrame):
        """
        Exibe detalhes específicos dos cálculos DI-PRE
        """
        st.markdown("---")
        st.subheader("📊 Detalhes dos Cálculos DI-PRE")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'taxa_di_pre_aplicada' in df_final.columns:
                taxa_di_pre_media = df_final['taxa_di_pre_aplicada'].mean()
                st.metric("📈 Taxa DI-PRE Média", f"{taxa_di_pre_media:.2f}%")
        
        with col2:
            if 'spread_risco_aplicado' in df_final.columns:
                spread_medio = df_final['spread_risco_aplicado'].mean()
                st.metric("⚠️ Spread Risco Médio", f"{spread_medio:.2f}%")
        
        with col3:
            if 'fator_correcao_ate_recebimento' in df_final.columns:
                fator_correcao_medio = df_final['fator_correcao_ate_recebimento'].mean()
                st.metric("📊 Fator Correção Médio", f"{fator_correcao_medio:.4f}")
        
        with col4:
            if 'prazo_recebimento' in df_final.columns:
                prazo_medio = df_final['prazo_recebimento'].mean()
                st.metric("⏰ Prazo Médio (meses)", f"{prazo_medio:.1f}")
        
        # Mostrar distribuição das taxas DI-PRE
        if 'taxa_di_pre_aplicada' in df_final.columns:
            st.write("**📊 Distribuição das Taxas DI-PRE:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Estatísticas descritivas
                taxa_min = df_final['taxa_di_pre_aplicada'].min()
                taxa_max = df_final['taxa_di_pre_aplicada'].max()
                taxa_std = df_final['taxa_di_pre_aplicada'].std()
                
                st.write(f"• **Mínima:** {taxa_min:.2f}%")
                st.write(f"• **Máxima:** {taxa_max:.2f}%")
                st.write(f"• **Desvio Padrão:** {taxa_std:.2f}%")
            
            with col2:
                # Mostrar quantos registros por faixa de prazo
                if 'prazo_recebimento' in df_final.columns:
                    distribuicao_prazo = df_final['prazo_recebimento'].value_counts().sort_index()
                    st.write("**Distribuição por Prazo:**")
                    for prazo, count in distribuicao_prazo.head(5).items():
                        st.write(f"• **{prazo} meses:** {count:,} registros")
    
    def _exibir_tabelas_agrupadas_distribuidoras(self, df_final: pd.DataFrame, tem_recuperacao: bool, tem_valor_justo: bool, tem_valor_justo_reajustado: bool, tem_di_pre: bool):
        """
        Exibe tabelas agrupadas para distribuidoras
        """
        st.markdown("---")
        st.subheader("📊 Agrupamento Detalhado - Por Empresa, Tipo, Classe, Status e Situação")
        
        # Definir colunas de agregação
        colunas_agg_1 = {
            'valor_principal': 'sum',
            'valor_liquido': 'sum',
            'valor_corrigido': 'sum'
        }
        
        if tem_recuperacao:
            colunas_agg_1['valor_recuperavel_ate_recebimento'] = 'sum'
        
        if tem_valor_justo:
            colunas_agg_1['valor_justo'] = 'sum'
        
        if tem_valor_justo_reajustado:
            colunas_agg_1['valor_justo_reajustado'] = 'sum'
            colunas_agg_1['desconto_aging_valor'] = 'sum'
        
        if tem_di_pre:
            colunas_agg_1['taxa_di_pre_aplicada'] = 'mean'
            colunas_agg_1['fator_correcao_ate_recebimento'] = 'mean'
        
        # Definir colunas de agrupamento
        colunas_groupby = ['empresa', 'aging', 'aging_taxa']
        
        # Adicionar colunas opcionais se existirem
        colunas_opcionais = ['tipo', 'classe', 'status', 'situacao']
        for col in colunas_opcionais:
            if col in df_final.columns:
                colunas_groupby.append(col)
        
        df_agg1 = (
            df_final
            .groupby(colunas_groupby, dropna=False)
            .agg(colunas_agg_1)
            .reset_index()
        )
        
        df_agg1['aging'] = pd.Categorical(df_agg1['aging'], categories=self.ordem_aging, ordered=True)
        df_agg1 = df_agg1.sort_values(['empresa'] + [col for col in colunas_opcionais if col in df_agg1.columns] + ['aging'])
        
        st.dataframe(df_agg1, use_container_width=True, hide_index=True)
        
        # Visão Consolidada por Empresa e Aging
        st.subheader("🎯 Agrupamento Consolidado - Por Empresa e Aging")
        st.caption("Valores consolidados por empresa e faixa de aging, incluindo valor principal, líquido, corrigido, recuperável e valor justo")
        
        df_agg2 = (
            df_final
            .groupby(['empresa', 'aging', 'aging_taxa'], dropna=False)
            .agg(colunas_agg_1)
            .reset_index()
        )
        
        df_agg2['aging'] = pd.Categorical(df_agg2['aging'], categories=self.ordem_aging, ordered=True)
        df_agg2 = df_agg2.sort_values(['empresa'])
        
        st.dataframe(df_agg2, use_container_width=True, hide_index=True)
        
        # Visão Geral por Aging
        st.subheader("📈 Agrupamento Geral - Por Aging e Taxa de Recuperação")
        st.caption("Visão consolidada geral agrupada apenas por faixa de aging, mostrando totais gerais incluindo valor justo")
        
        df_agg3 = (
            df_final
            .groupby(['aging_taxa'], dropna=False)
            .agg(colunas_agg_1)
            .reset_index()
        )
        
        st.dataframe(df_agg3, use_container_width=True, hide_index=True)
    
    def _exibir_resumo_consolidado_distribuidoras(self, df_final: pd.DataFrame, tem_recuperacao: bool, tem_valor_justo: bool, tem_valor_justo_reajustado: bool):
        """
        Exibe resumo consolidado por empresa para distribuidoras
        """
        st.markdown("---")
        st.subheader("💰 Resumo Total Consolidado por Empresa")
        
        # Calcular totais por empresa
        colunas_resumo_empresa = {
            'valor_principal': 'sum',
            'valor_liquido': 'sum',
            'valor_corrigido': 'sum'
        }
        
        if tem_recuperacao:
            colunas_resumo_empresa['valor_recuperavel_ate_recebimento'] = 'sum'
        
        if tem_valor_justo:
            colunas_resumo_empresa['valor_justo'] = 'sum'
        
        if tem_valor_justo_reajustado:
            colunas_resumo_empresa['valor_justo_reajustado'] = 'sum'
            colunas_resumo_empresa['desconto_aging_valor'] = 'sum'
        
        df_resumo_empresa = (
            df_final
            .groupby('empresa', dropna=False)
            .agg(colunas_resumo_empresa)
            .reset_index()
        )
        
        # Ordenar por empresa
        df_resumo_empresa = df_resumo_empresa.sort_values('empresa')
        
        # Formatação dos valores para exibição
        df_resumo_display = df_resumo_empresa.copy()
        
        # Aplicar formatação brasileira a todas as colunas de valor
        colunas_valor = ['valor_principal', 'valor_liquido', 'valor_corrigido']
        if tem_recuperacao:
            colunas_valor.append('valor_recuperavel_ate_recebimento')
        if tem_valor_justo:
            colunas_valor.append('valor_justo')
        if tem_valor_justo_reajustado:
            colunas_valor.extend(['valor_justo_reajustado', 'desconto_aging_valor'])
        
        for col in colunas_valor:
            if col in df_resumo_display.columns:
                df_resumo_display[col] = df_resumo_display[col].apply(
                    lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                )
        
        # Renomear colunas para exibição
        nomes_colunas = {
            'empresa': '🏢 Empresa',
            'valor_principal': '📊 Valor Principal',
            'valor_liquido': '💧 Valor Líquido',
            'valor_corrigido': '⚡ Valor Corrigido',
            'valor_recuperavel_ate_recebimento': '📈 Valor Recuperável',
            'valor_justo': '💎 Valor Justo',
            'valor_justo_reajustado': '🔥 Valor Justo Reajustado',
            'desconto_aging_valor': '📉 Desconto Aging'
        }
        
        df_resumo_display = df_resumo_display.rename(columns=nomes_colunas)
        
        # Exibir tabela resumo por empresa
        st.dataframe(df_resumo_display, use_container_width=True, hide_index=True)
        
        # Calcular e exibir totais gerais
        st.markdown("---")
        st.subheader("📊 Totais Gerais")
        
        total_principal = df_resumo_empresa['valor_principal'].sum()
        total_liquido = df_resumo_empresa['valor_liquido'].sum()
        total_corrigido = df_resumo_empresa['valor_corrigido'].sum()
        
        # Calcular totais condicionais
        if tem_recuperacao:
            total_recuperavel = df_resumo_empresa['valor_recuperavel_ate_recebimento'].sum()
        else:
            total_recuperavel = 0
        
        if tem_valor_justo:
            total_valor_justo = df_resumo_empresa['valor_justo'].sum()
        else:
            total_valor_justo = 0
        
        if tem_valor_justo_reajustado:
            total_valor_justo_reaj = df_resumo_empresa['valor_justo_reajustado'].sum()
            total_desconto = df_resumo_empresa['desconto_aging_valor'].sum()
        else:
            total_valor_justo_reaj = 0
            total_desconto = 0
        
        # Criar colunas para as métricas
        if tem_valor_justo_reajustado:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
        elif tem_valor_justo:
            col1, col2, col3, col4, col5 = st.columns(5)
        else:
            col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Total Principal", f"R$ {total_principal:,.2f}")
        
        with col2:
            st.metric("💧 Total Líquido", f"R$ {total_liquido:,.2f}")
        
        with col3:
            st.metric("⚡ Total Corrigido", f"R$ {total_corrigido:,.2f}")
        
        with col4:
            st.metric("📈 Total Recuperável", f"R$ {total_recuperavel:,.2f}")
        
        # Quinta coluna só aparece se tivermos valor justo
        if tem_valor_justo:
            with col5:
                st.metric("💎 Total Valor Justo", f"R$ {total_valor_justo:,.2f}")
        
        # Sexta coluna só aparece se tivermos valor justo reajustado
        if tem_valor_justo_reajustado:
            with col6:
                st.metric("🔥 Total VJ Reajustado", f"R$ {total_valor_justo_reaj:,.2f}")
    
    def exibir_exportacao_distribuidoras(self, df_final: pd.DataFrame):
        """
        Exibe opções de exportação para distribuidoras
        """
        st.markdown("---")
        st.subheader("💾 Exportação dos Dados Finais")
        
        st.info(f"""
        **📋 Dados prontos para exportação:**
        - **Total de registros:** {len(df_final):,}
        - **Total de colunas:** {len(df_final.columns)}
        - **Conteúdo:** Todos os registros processados com aging, correção monetária, taxa de recuperação e valor justo com DI-PRE
        
        **💡 Opções de exportação:**
        - **📋 Preview:** Mostra 10 linhas para validar formato
        - **💾 Completo:** Salva todos os dados na pasta 'data'
        """)
        
        # Ordenação para distribuidoras gerais
        colunas_ordem_usuario = [
            'nome_cliente', 'documento', 'contrato', 'classe', 'situacao',
            'valor_principal', 'valor_nao_cedido', 'valor_terceiro', 'valor_cip',
            'data_vencimento', 'empresa', 'tipo', 'status', 'id_padronizado',
            'base_origem', 'data_base', 'data_vencimento_limpa', 'dias_atraso',
            'aging', 'valor_principal_limpo', 'valor_nao_cedido_limpo',
            'valor_terceiro_limpo', 'valor_cip_limpo', 'valor_liquido',
            'multa', 'meses_atraso', 'juros_moratorios', 'indice_vencimento',
            'indice_base', 'fator_correcao_ate_data_base', 'correcao_monetaria', 'valor_corrigido',
            'aging_taxa', 'taxa_recuperacao', 'prazo_recebimento',
            'di_pre_taxa_anual', 'taxa_di_pre_total_anual', 'taxa_desconto_mensal',
            'data_recebimento_estimada', 'meses_ate_recebimento', 'ipca_mensal',
            'fator_de_desconto', 'multa_atraso', 'multa_final', 'fator_correcao_ate_recebimento',
            'mora_ate_recebimento', 'valor_corrigido_ate_recebimento',
            'valor_recuperavel_ate_data_base', 'valor_recuperavel_ate_recebimento', 'valor_justo',
            'valor_justo_reajustado', 'desconto_aging_perc', 'desconto_aging_valor'
        ]
        
        preview_df = df_final.head(10).copy()
        
        # Identificar colunas que existem na ordem especificada
        colunas_existentes = [col for col in colunas_ordem_usuario if col in preview_df.columns]
        colunas_restantes = [col for col in preview_df.columns if col not in colunas_ordem_usuario]
        
        # Reordenar DataFrame conforme especificação do usuário
        preview_df = preview_df[colunas_existentes + colunas_restantes]
        
        st.dataframe(preview_df, use_container_width=True, hide_index=True)
        
        # Botão para exportar dados completos
        if st.button("💾 Salvar Dados Completos na Pasta 'data'", type="primary", use_container_width=True, key="salvar_dados_distribuidoras"):
            try:
                # Criar timestamp para nome do arquivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo = f"FIDC_Dados_Finais_{timestamp}.csv"
                caminho_arquivo = f"data/{nome_arquivo}"
                
                # Reordenar DataFrame completo
                df_export = df_final.copy()
                colunas_existentes_completo = [col for col in colunas_ordem_usuario if col in df_export.columns]
                colunas_restantes_completo = [col for col in df_export.columns if col not in colunas_ordem_usuario]
                df_export = df_export[colunas_existentes_completo + colunas_restantes_completo]
                
                # Salvar arquivo no formato brasileiro com truncamento para 2 casas
                df_export = salvar_csv_brasil(df_export, caminho_arquivo, casas_decimais=4)
                
                st.success(f"✅ **Dados salvos com sucesso!**")
                st.info(f"📄 **Arquivo:** `{nome_arquivo}`")
                st.info(f"📂 **Local:** `{caminho_arquivo}`")
                st.info(f"📊 **Registros:** {len(df_export):,}")
                st.info(f"📋 **Colunas:** {len(df_export.columns)}")
                
            except Exception as e:
                st.error(f"❌ Erro ao salvar arquivo: {str(e)}")
    
    def exibir_info_processo_distribuidoras(self):
        """
        Exibe informações sobre o processo das distribuidoras
        """
        st.markdown("---")
        st.subheader("ℹ️ Informações sobre o Processo")
        
        with st.expander("⚙️ Etapas do Processo de Correção", expanded=False):
            st.write("""
            **🔄 Processo de Correção Monetária e Valor Justo:**
            
            **1. 📊 Cálculo do Aging:**
            - Classificação por faixas de vencimento
            - Aplicação das taxas de recuperação correspondentes
            
            **2. 📈 Correção Monetária:**
            - IPCA para contratos até 2021
            - IGP-M para contratos após 2021  
            - Aplicada até a data base de cálculo
            
            **3. 💰 Taxa de Recuperação:**
            - Baseada no aging e empresa
            - Aplicada sobre o valor corrigido
            
            **4. 🎯 Valor Justo com DI-PRE:**
            - Correção IPCA até data de recebimento estimada
            - Aplicação da taxa DI-PRE + spread de risco (2,5%)
            - Desconto a valor presente
            
            **5. 📉 Reajuste por Aging:**
            - Desconto adicional baseado no aging
            - Valor justo final reajustado
            """)
        
        with st.expander("💡 Fórmulas Utilizadas", expanded=False):
            st.write("""
            **📐 Fórmulas do Cálculo:**
            
            **1. Correção Monetária:**
            ```
            Fator = Índice(data_base) / Índice(vencimento)
            Valor Corrigido = Valor Líquido × Fator
            ```
            
            **2. Valor Recuperável:**
            ```
            Valor Recuperável = Valor Corrigido × Taxa Recuperação
            ```
            
            **3. Valor Justo:**
            ```
            VJ = (Valor Recuperável × Fator IPCA × (1 + Multa)) / Fator Desconto DI-PRE
            Onde: Fator Desconto = (1 + Taxa DI-PRE + Spread)^(prazo/12)
            ```
            
            **4. Valor Justo Reajustado:**
            ```
            VJ Reajustado = Valor Justo × (1 - Desconto Aging)
            ```
            """)
    
    def exibir_limpar_cache(self):
        """
        Exibe botão para limpar cache
        """
        if st.button("🗑️ Limpar Cache", key="limpar_cache_distribuidoras"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache limpo com sucesso!")
            st.experimental_rerun()
