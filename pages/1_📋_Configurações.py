"""
Página de Configurações - FIDC Calculator
Configuração de parâmetros financeiros e índices de correção
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def show():
    """Página de Configurações e Parâmetros"""
    st.header("📋 CONFIGURAÇÕES E PARÂMETROS")
    
    # Verificar se os parâmetros estão inicializados
    if 'params' not in st.session_state:
        from utils.parametros_correcao import ParametrosCorrecao
        st.session_state.params = ParametrosCorrecao()
    
    # Parâmetros financeiros com destaque
    st.subheader("💰 Parâmetros Financeiros")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Taxa de Multa",
            value=f"{st.session_state.params.taxa_multa:.1%}",
            help="Taxa de multa por inadimplência aplicada sobre o valor líquido"
        )
        
        taxa_multa = st.number_input(
            "Nova Taxa de Multa (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.params.taxa_multa * 100,
            step=0.1,
            format="%.1f",
            key="input_multa"
        ) / 100
    
    with col2:
        st.metric(
            label="Taxa de Juros Moratórios",
            value=f"{st.session_state.params.taxa_juros_mensal:.1%}",
            help="Taxa de juros moratórios aplicada mensalmente"
        )
        
        taxa_juros = st.number_input(
            "Nova Taxa de Juros (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.params.taxa_juros_mensal * 100,
            step=0.1,
            format="%.1f",
            key="input_juros"
        ) / 100
    
    # Botão para atualizar parâmetros
    if st.button("💾 Atualizar Parâmetros", type="primary"):
        st.session_state.params.taxa_multa = taxa_multa
        st.session_state.params.taxa_juros_mensal = taxa_juros
        st.success("✅ Parâmetros atualizados com sucesso!")
        st.rerun()
    
    st.markdown("---")
    
    # Gráficos dos índices de correção
    st.subheader("📊 Evolução do Índice de Correção Monetária")
    
    try:
        # Obter dados dos índices para visualização
        dados_igpm = st.session_state.params.indices_igpm
        df_igpm = pd.DataFrame(list(dados_igpm.items()), columns=['Periodo', 'Valor'])
        df_igpm['Data'] = pd.to_datetime(df_igpm['Periodo'], format='%Y.%m', errors='coerce')
        df_igpm = df_igpm.dropna(subset=['Data'])
        df_igpm['Indice'] = 'IGP-M'
        df_igpm = df_igpm.sort_values('Data')
        
        dados_ipca = st.session_state.params.indices_ipca
        df_ipca = pd.DataFrame(list(dados_ipca.items()), columns=['Periodo', 'Valor'])
        df_ipca['Data'] = pd.to_datetime(df_ipca['Periodo'], format='%Y.%m', errors='coerce')
        df_ipca = df_ipca.dropna(subset=['Data'])
        df_ipca['Indice'] = 'IPCA'
        df_ipca = df_ipca.sort_values('Data')
        
        # Combinar todos os dados
        df_completo = pd.concat([
            df_igpm[['Periodo', 'Valor', 'Indice']],
            df_ipca[['Periodo', 'Valor', 'Indice']]
        ], ignore_index=True)
        
        # Ordenar por período
        df_completo['Data_ord'] = pd.to_datetime(df_completo['Periodo'], format='%Y.%m', errors='coerce')
        df_completo = df_completo.dropna(subset=['Data_ord'])
        df_completo = df_completo.sort_values('Data_ord')
        
        # Preparar tabela de exibição com valores formatados
        df_tabela = df_completo[['Periodo', 'Valor', 'Indice']].copy()
        df_tabela['Valor'] = df_tabela['Valor'].round(2).astype(int)  # Converter para inteiro
        df_tabela.columns = ['Período', 'Índice', 'Tipo']

        # Converter Período para datetime se necessário
        df_tabela['Período'] = pd.to_datetime(df_tabela['Período'].str.replace('.', '-'), format='%Y-%m')

        # Gráfico
        fig = px.line(
            df_tabela,
            x='Período',
            y='Índice',
            color='Tipo',
            markers=True,
            title='Evolução dos Índices por Período'
        )

        fig.update_layout(xaxis_title='Período', yaxis_title='Índice (%)')

        # Streamlit
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela consolidada com todos os valores
        st.subheader("📋 Tabela dos Índices de Correção")
        
        # Exibir informação sobre todos os registros
        st.write(f"**Total de {len(df_tabela)} registros disponíveis** (agosto/1994 até {df_completo['Periodo'].iloc[-1]})")
        
        st.dataframe(
            df_tabela, 
            use_container_width=True, 
            hide_index=True,
            height=min(800, len(df_tabela) * 35 + 100)
        )
    
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar dados dos índices para tabela: {e}")
        
        # Informação básica caso a tabela não carregue
        st.info("**Tabela de índices temporariamente indisponível**\n\nOs índices serão utilizados normalmente durante os cálculos.")
    
    # Informações adicionais sobre os parâmetros
    st.markdown("---")
    st.subheader("ℹ️ Informações dos Parâmetros")
    
    with st.expander("📖 Sobre os Índices de Correção", expanded=False):
        st.info("""
        **IGP-M (Índice Geral de Preços - Mercado)**
        - Índice de correção monetária oficial
        - Utilizado para contratos e atualizações financeiras
        - Calculado pela Fundação Getúlio Vargas (FGV)
        
        **IPCA (Índice Nacional de Preços ao Consumidor Amplo)**
        - Índice oficial de inflação do Brasil
        - Utilizado pelo Banco Central para metas de inflação
        - Calculado pelo IBGE
        
        **Observação:** Os dados são carregados automaticamente e atualizados mensalmente.
        """)
    
    with st.expander("💰 Sobre as Taxas Financeiras", expanded=False):
        st.info("""
        **Taxa de Multa**
        - Aplicada sobre o valor líquido em caso de inadimplência
        - Valor padrão: 2% (configurável)
        - Base legal: Código Civil Brasileiro
        
        **Taxa de Juros Moratórios**
        - Aplicada mensalmente sobre débitos em atraso
        - Valor padrão: 1% ao mês (configurável)
        - Utilizada para cálculo de juros compostos
        
        **Observação:** As taxas podem ser ajustadas conforme necessidades específicas do cálculo.
        """)

if __name__ == "__main__":
    show()
