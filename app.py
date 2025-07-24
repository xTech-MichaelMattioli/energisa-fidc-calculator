"""
FIDC Calculator - Energisa
Aplicação Streamlit para Cálculo de Valor Corrigido
Baseado no notebook FIDC_Calculo_Valor_Corrigido_CORRIGIDO.ipynb
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# Importar classes utilitárias
from utils.parametros_correcao import ParametrosCorrecao
from utils.analisador_bases import AnalisadorBases
from utils.mapeador_campos import MapeadorCampos
from utils.calculador_aging import CalculadorAging
from utils.calculador_correcao import CalculadorCorrecao
from utils.exportador_resultados import ExportadorResultados

# Configuração da página
st.set_page_config(
    page_title="FIDC Calculator - Distribuidoras",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para identidade visual da Energisa
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #00A859 0%, #28C76F 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 8px rgba(0, 168, 89, 0.3);
    }
    
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #00A859;
        margin: 0.5rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .stProgress .st-bo {
        background: linear-gradient(90deg, #00A859 0%, #28C76F 100%);
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>⚡ FIDC Calculator - Distribuidoras</h1>
        <h3>Sistema de Cálculo de Valor Justo</h3>
        <p><strong>Objetivo:</strong> Processar bases de distribuidoras até o cálculo do valor justo<br>
        <strong>Escopo:</strong> Carregamento → Mapeamento → Aging → Correção Monetária → Valor Justo</p>
        <p><em>Data: {}</em></p>
    </div>
    """.format(datetime.now().strftime('%d de %B de %Y')), unsafe_allow_html=True)
    
    # Inicializar estado da sessão
    if 'params' not in st.session_state:
        st.session_state.params = ParametrosCorrecao()
    
    # Sidebar com navegação
    with st.sidebar:
        st.header("🧭 Navegação")
        
        etapa = st.selectbox(
            "Selecione a etapa:",
            [
                "📋 1. Configurações",
                "📂 2. Carregamento de Dados",
                "🗺️ 3. Mapeamento de Campos", 
                "💰 4. Correção Monetária e Valor Justo"
            ]
        )
        
        st.markdown("---")
        
        # Status do processamento
        st.subheader("📊 Status do Processamento")
        
        # Verificar cada etapa
        if 'arquivos_processados' in st.session_state and st.session_state.arquivos_processados:
            st.success("✅ Arquivos processados")
            total_registros = sum(info['registros'] for info in st.session_state.arquivos_processados.values())
            total_arquivos = len(st.session_state.arquivos_processados)
            st.caption(f"📁 {total_arquivos} arquivo(s)")
        else:
            st.warning("⏳ Arquivos não processados")
        
        if 'df_padronizado' in st.session_state and not st.session_state.df_padronizado.empty:
            st.success("✅ Campos mapeados")
        else:
            st.warning("⏳ Mapeamento pendente")
        
        if 'df_com_aging' in st.session_state and not st.session_state.df_com_aging.empty:
            st.success("✅ Correção concluída")
        else:
            st.warning("⏳ Correção pendente")
        
        if 'df_final' in st.session_state and not st.session_state.df_final.empty:
            st.success("✅ Resultados prontos")
        else:
            st.warning("⏳ Resultados pendentes")
        
        if 'df_taxa_recuperacao' in st.session_state and not st.session_state.df_taxa_recuperacao.empty:
            st.success("✅ Taxa de recuperação configurada")
        else:
            st.error("❌ Taxa de recuperação OBRIGATÓRIA")
        
        st.markdown("---")
        
        # Exibir parâmetros atuais
        st.subheader("⚙️ Parâmetros Atuais")
        params_info = st.session_state.params.exibir_parametros()
        for key, value in params_info.items():
            st.text(f"{key}: {value}")
    
    # Executar etapa selecionada
    if etapa.startswith("📋 1"):
        etapa_configuracoes()
    elif etapa.startswith("📂 2"):
        etapa_carregamento()
    elif etapa.startswith("🗺️ 3"):
        etapa_mapeamento()
    elif etapa.startswith("💰 4"):
        etapa_correcao()

def etapa_configuracoes():
    """Etapa 1: Configurações e Parâmetros"""
    st.header("📋 CONFIGURAÇÕES E PARÂMETROS")
    
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
    
    # Adicionar controles para o gráfico
    col_controles1, col_controles2 = st.columns(2)
    

    # Obter dados dos índices novamente para a tabela
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
    
    try:
        
        
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

def etapa_carregamento():
    """Etapa 2: Carregamento da Base"""
    st.header("📂 CARREGAMENTO DA BASE")
    
    # Inicializar estados
    if 'arquivos_para_processar' not in st.session_state:
        st.session_state.arquivos_para_processar = {}
    if 'arquivos_processados' not in st.session_state:
        st.session_state.arquivos_processados = {}
    if 'processamento_confirmado' not in st.session_state:
        st.session_state.processamento_confirmado = False
    
    # Upload de múltiplos arquivos
    uploaded_files = st.file_uploader(
        "📤 Selecione os arquivos Excel das distribuidoras",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="Você pode carregar múltiplos arquivos Excel. Cada um será processado individualmente."
    )
    
    # Armazenar arquivos carregados (sem processar ainda)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.arquivos_para_processar:
                st.session_state.arquivos_para_processar[uploaded_file.name] = uploaded_file
                st.success(f"✅ Arquivo adicionado: {uploaded_file.name}")
    
    # Mostrar arquivos aguardando processamento
    if st.session_state.arquivos_para_processar:
        st.markdown("---")
        st.subheader("📋 Arquivos Aguardando Processamento")
        
        for nome_arquivo in st.session_state.arquivos_para_processar.keys():
            st.info(f"📄 **{nome_arquivo}** - Aguardando confirmação para processamento")
        
        # Botão de confirmação para processar
        st.markdown("---")
        
        if st.button("🔄 Confirmar e Processar Todos os Arquivos", type="primary"):
            st.session_state.processamento_confirmado = True
            st.rerun()
    
    # Processar arquivos após confirmação
    if st.session_state.processamento_confirmado and st.session_state.arquivos_para_processar:
        
        with st.spinner("🔄 Processando e analisando arquivos Excel..."):
            # Inicializar analisador
            if 'analisador' not in st.session_state:
                analisador = AnalisadorBases(st.session_state.params)
                st.session_state.analisador = analisador
            
            # Processar cada arquivo
            for nome_arquivo, uploaded_file in st.session_state.arquivos_para_processar.items():
                if nome_arquivo not in st.session_state.arquivos_processados:
                    try:
                        st.write(f"🔄 Processando {nome_arquivo}...")
                        
                        # Carregar e processar arquivo
                        df = st.session_state.analisador.carregar_base_excel(uploaded_file, nome_arquivo)
                        
                        if not df.empty:
                            # Calcular valor total se possível
                            valor_total = 0
                            for col in df.columns:
                                if any(termo in col.lower() for termo in ['valor', 'principal', 'liquido']):
                                    try:
                                        valor_total = df[col].sum()
                                        break
                                    except:
                                        continue
                            
                            # Armazenar com o nome do arquivo
                            st.session_state.arquivos_processados[nome_arquivo] = {
                                'dataframe': df,
                                'registros': len(df),
                                'colunas': len(df.columns),
                                'nome_arquivo': nome_arquivo,
                                'valor_total': valor_total
                            }
                            
                            st.success(f"✅ {nome_arquivo} processado com sucesso!")
                        else:
                            st.error(f"❌ Erro ao processar {nome_arquivo}. Verifique se é um arquivo Excel válido.")
                            
                    except Exception as e:
                        st.error(f"❌ Erro ao processar {nome_arquivo}: {str(e)}")
            
            # Limpar arquivos para processar
            st.session_state.arquivos_para_processar = {}
            st.session_state.processamento_confirmado = False
            
        st.rerun()
    
    # Exibir resumo dos arquivos processados
    if st.session_state.arquivos_processados:
        st.markdown("---")
        st.subheader("📋 Arquivos Processados")
        
        total_registros = 0
        total_valor = 0
        
        for nome_arquivo, info in st.session_state.arquivos_processados.items():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.success(f"**📄 {nome_arquivo}**")
            
            with col2:
                st.metric("📊 Registros", f"{info['registros']:,}")
                total_registros += info['registros']
            
            with col3:
                st.metric("📋 Colunas", info['colunas'])
            
            # Identificar e exibir data base
            df_arquivo = info['dataframe']
            
            # Procurar data base no cabeçalho (nomes das colunas)
            colunas_data = []
            data_base_detectada = None
            
            for col in df_arquivo.columns:
                try:
                    # Tentar converter o NOME da coluna para data
                    data_header = pd.to_datetime(col, errors='coerce')
                    
                    if not pd.isna(data_header):
                        # Encontrou uma data no cabeçalho
                        colunas_data.append({
                            'coluna': col,
                            'data_detectada': data_header,
                            'tipo': 'Data no cabeçalho',
                            'eh_data_base': True
                        })
                    else:
                        # Verificar se é coluna de data tradicional (por nome)
                        if any(termo in col.lower() for termo in ['data', 'vencimento', 'venc', 'date']):
                            # Verificar se tem datas válidas no conteúdo
                            datas_validas = pd.to_datetime(df_arquivo[col], errors='coerce').dropna()
                            percentual_valido = len(datas_validas) / len(df_arquivo) if len(df_arquivo) > 0 else 0
                            
                            if len(datas_validas) > 0 and percentual_valido >= 0.1:
                                colunas_data.append({
                                    'coluna': col,
                                    'data_detectada': datas_validas.max(),
                                    'tipo': 'Coluna de vencimento',
                                    'eh_data_base': False,
                                    'registros_validos': len(datas_validas),
                                    'percentual_valido': percentual_valido
                                })
                except:
                    continue
            
            # Determinar melhor data base
            if colunas_data:
                # Priorizar data no cabeçalho (data base real)
                data_base_header = [item for item in colunas_data if item['eh_data_base']]
                
                if data_base_header:
                    # Usar a data mais recente do cabeçalho
                    coluna_preferida = max(data_base_header, key=lambda x: x['data_detectada'])
                else:
                    # Usar coluna de vencimento como alternativa
                    colunas_vencimento = [item for item in colunas_data if not item['eh_data_base']]
                    if colunas_vencimento:
                        coluna_preferida = max(colunas_vencimento, key=lambda x: x['data_detectada'])
                    else:
                        coluna_preferida = colunas_data[0]
                
                data_base_detectada = coluna_preferida['data_detectada']
                
                # Exibir informações da data base
                with st.expander(f"📅 Data Base: {nome_arquivo}", expanded=False):
                    col_data1, col_data2 = st.columns(2)
                    
                    with col_data1:
                        if coluna_preferida['eh_data_base']:
                            st.info(f"""
                            **🔍 Data Base Detectada no Cabeçalho**
                            
                            📋 **Coluna:** {coluna_preferida['coluna']}  
                            📅 **Data Base:** {data_base_detectada.strftime('%d/%m/%Y')}  
                            🎯 **Tipo:** Data real no cabeçalho do Excel  
                            ✅ **Status:** Data base oficial detectada
                            """)
                        else:
                            st.info(f"""
                            **🔍 Data Base Derivada de Vencimentos**
                            
                            📋 **Coluna:** {coluna_preferida['coluna']}  
                            📅 **Data Base:** {data_base_detectada.strftime('%d/%m/%Y')}  
                            🎯 **Tipo:** Maior data de vencimento  
                            ✅ **Registros válidos:** {coluna_preferida.get('registros_validos', 0):,} ({coluna_preferida.get('percentual_valido', 0):.1%})
                            """)
                    
                    with col_data2:
                        st.write("**🛠️ Ajustar Data Base**")
                        
                        # Input para modificar a data base
                        nova_data = st.date_input(
                            f"Nova data base para {nome_arquivo}:",
                            value=data_base_detectada.date(),
                            key=f"data_base_{nome_arquivo}"
                        )
                        
                        if st.button(f"💾 Salvar Data Base", key=f"salvar_data_{nome_arquivo}"):
                            # Atualizar a data base nos parâmetros
                            st.session_state.params.data_base_padrao = pd.to_datetime(nova_data)
                            st.success(f"✅ Data base atualizada: {nova_data.strftime('%d/%m/%Y')}")
                            st.rerun()
                        
            else:
                # Não encontrou datas no cabeçalho nem em colunas
                with st.expander(f"⚠️ Data Base: {nome_arquivo}", expanded=False):
                    st.warning("⚠️ **Nenhuma data foi detectada automaticamente.**")
                    st.info("**💡 Dica:** Verifique se o arquivo possui:\n- Uma coluna com data no cabeçalho (ex: 2025-02-15)\n- Uma coluna de vencimento com datas válidas")
                    
                    st.write("**🛠️ Definir Data Base Manualmente**")
                    data_manual = st.date_input(
                        f"Data base para {nome_arquivo}:",
                        value=datetime.now().date(),
                        key=f"data_manual_{nome_arquivo}"
                    )
                    
                    if st.button(f"💾 Definir Data Base", key=f"definir_data_{nome_arquivo}"):
                        st.session_state.params.data_base_padrao = pd.to_datetime(data_manual)
                        st.success(f"✅ Data base definida: {data_manual.strftime('%d/%m/%Y')}")
                        st.rerun()
            
            # Preview opcional de cada arquivo
            with st.expander(f"👀 Preview: {nome_arquivo}", expanded=False):
                st.dataframe(info['dataframe'].head(3), use_container_width=True)
        
        # Resumo consolidado
        st.markdown("---")
        st.subheader("📊 Resumo Consolidado")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📁 Total de Arquivos", len(st.session_state.arquivos_processados))
        
        with col2:
            st.metric("📊 Total de Registros", f"{total_registros:,}")
        
        # Preparar dados para as próximas etapas automaticamente
        st.session_state.df_carregado = st.session_state.arquivos_processados
    
    else:
        st.info("ℹ️ Inicie o processo para ver os resultados.")

def etapa_mapeamento():
    """Etapa 3: Mapeamento de Campos"""
    st.header("🗺️ MAPEAMENTO DE CAMPOS")
    
    # Verificar se há arquivos carregados
    if 'df_carregado' not in st.session_state or not st.session_state.df_carregado:
        st.warning("⚠️ Carregue um ou mais arquivos antes de prosseguir para o mapeamento.")
        return
    
    arquivos_processados = st.session_state.df_carregado
    mapeador = MapeadorCampos(st.session_state.params)
    
    st.write("Mapeie as colunas dos arquivos para os campos padrão do sistema.")
    
    # Informações gerais
    total_arquivos = len(arquivos_processados)
    total_registros = sum(info['registros'] for info in arquivos_processados.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📁 Arquivos para Mapear", total_arquivos)
    with col2:
        # Verificar se já temos mapeamentos salvos
        mapeamentos_salvos = 0
        if 'mapeamentos_finais' in st.session_state:
            mapeamentos_salvos = len(st.session_state.mapeamentos_finais)
        st.metric("✅ Mapeamentos Salvos", f"{mapeamentos_salvos}/{total_arquivos}")
    
    st.markdown("---")
    
    # Inicializar estado dos mapeamentos
    if 'mapeamentos_finais' not in st.session_state:
        st.session_state.mapeamentos_finais = {}
    
    # Processar cada arquivo individualmente
    for nome_arquivo, info_arquivo in arquivos_processados.items():
        st.subheader(f"� Mapeamento: {nome_arquivo}")
        
        df_arquivo = info_arquivo['dataframe']
        
        # Informações do arquivo
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📊 **Registros:** {len(df_arquivo):,}")
        with col2:
            st.info(f"�📋 **Colunas:** {len(df_arquivo.columns)}")
        
        # Mostrar estrutura do arquivo
        with st.expander(f"📋 Ver estrutura de {nome_arquivo}", expanded=False):
            st.dataframe(df_arquivo.head(3), use_container_width=True)
            
            # Mostrar todas as colunas
            st.write("**📋 Lista de Colunas:**")
            colunas_formatadas = [f"• {col}" for col in df_arquivo.columns]
            st.write("\n".join(colunas_formatadas[:15]))  # Mostrar primeiras 15
            if len(df_arquivo.columns) > 15:
                st.caption(f"... e mais {len(df_arquivo.columns) - 15} colunas")
        
        # Mapeamento automático para este arquivo
        try:
            with st.spinner(f"🔍 Analisando colunas de {nome_arquivo}..."):
                mapeamento_auto = mapeador.criar_mapeamento_automatico(df_arquivo, nome_arquivo)
        except Exception as e:
            st.error(f"❌ Erro no mapeamento automático de {nome_arquivo}: {str(e)}")
            mapeamento_auto = {}
        
        # Usar mapeamento salvo se existir, senão usar o automático
        if nome_arquivo in st.session_state.mapeamentos_finais:
            mapeamento_inicial = st.session_state.mapeamentos_finais[nome_arquivo]
        else:
            mapeamento_inicial = mapeamento_auto if mapeamento_auto else {}
        
        try:
            mapeamento_manual = mapeador.permitir_mapeamento_manual(
                df_arquivo, 
                mapeamento_inicial,
                key_suffix=f"_{nome_arquivo.replace('.', '_').replace(' ', '_')}"
            )
            
            # Botões de ação para este arquivo
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"💾 Salvar Mapeamento", key=f"salvar_{nome_arquivo}", type="secondary"):
                    st.session_state.mapeamentos_finais[nome_arquivo] = mapeamento_manual
                    st.success(f"✅ Mapeamento salvo para {nome_arquivo}!")
                    st.rerun()
            
            with col2:
                # Verificar se o mapeamento está salvo
                if nome_arquivo in st.session_state.mapeamentos_finais:
                    st.success("✅ Mapeamento salvo")
                else:
                    st.warning("⏳ Mapeamento não salvo")
        
        except Exception as e:
            st.error(f"❌ Erro no mapeamento manual de {nome_arquivo}: {str(e)}")
        
        st.markdown("---")
    
    # Aplicar todos os mapeamentos
    st.subheader("🔄 Aplicar Todos os Mapeamentos")
    
    # Verificar quantos mapeamentos estão salvos
    mapeamentos_salvos = len(st.session_state.mapeamentos_finais)
    
    if mapeamentos_salvos == 0:
        st.warning("⚠️ Nenhum mapeamento foi salvo ainda.")
    elif mapeamentos_salvos < total_arquivos:
        st.warning(f"⚠️ Apenas {mapeamentos_salvos} de {total_arquivos} mapeamentos foram salvos.")
    else:
        st.success(f"✅ Todos os {total_arquivos} mapeamentos foram salvos!")
    
    # Botão para aplicar todos os mapeamentos
    if st.button("� Aplicar Todos os Mapeamentos", type="primary"):
        if not st.session_state.mapeamentos_finais:
            st.error("❌ Nenhum mapeamento foi salvo. Salve pelo menos um mapeamento antes de prosseguir.")
            return
        
        with st.spinner("🔄 Aplicando mapeamentos e padronizando dados..."):
            try:
                # Dicionário para armazenar os dataframes padronizados
                dataframes_padronizados = {}
                total_registros_processados = 0
                
                for nome_arquivo, mapeamento_final in st.session_state.mapeamentos_finais.items():
                    if nome_arquivo in arquivos_processados:
                        df_arquivo = arquivos_processados[nome_arquivo]['dataframe']
                        
                        # Aplicar mapeamento
                        df_padronizado = mapeador.aplicar_mapeamento(df_arquivo, mapeamento_final, nome_arquivo)
                        
                        if not df_padronizado.empty:
                            dataframes_padronizados[nome_arquivo] = df_padronizado
                            total_registros_processados += len(df_padronizado)
                            st.success(f"✅ {nome_arquivo}: {len(df_padronizado):,} registros padronizados")
                        else:
                            st.error(f"❌ Erro ao aplicar mapeamento em {nome_arquivo}")
                
                if dataframes_padronizados:
                    # Combinar todos os dataframes padronizados
                    if len(dataframes_padronizados) == 1:
                        # Apenas um arquivo
                        df_final_padronizado = list(dataframes_padronizados.values())[0]
                    else:
                        # Múltiplos arquivos - combinar
                        df_final_padronizado = pd.concat(
                            dataframes_padronizados.values(), 
                            ignore_index=True
                        )
                    
                    # Salvar resultado
                    st.session_state.df_padronizado = df_final_padronizado
                    st.session_state.dataframes_individuais = dataframes_padronizados
                    
                    st.success(f"🎯 **Mapeamento concluído!** {total_registros_processados:,} registros de {len(dataframes_padronizados)} arquivo(s) padronizados")
                    
                    # Mostrar preview do resultado final
                    st.subheader("📊 Preview dos Dados Padronizados Consolidados")
                    
                    # Métricas do resultado
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 Total de Registros", f"{len(df_final_padronizado):,}")
                    with col2:
                        st.metric("� Arquivos Processados", len(dataframes_padronizados))
                    with col3:
                        # Verificar campos essenciais no resultado final
                        campos_obrigatorios = ['empresa', 'tipo', 'status', 'situacao', 'nome_cliente', 'classe', 'contrato', 'valor_principal', 'valor_nao_cedido', 'valor_terceiro', 'valor_cip', 'data_vencimento']
                        campos_ok = sum(1 for campo in campos_obrigatorios if campo in df_final_padronizado.columns)
                        st.metric("✅ Campos Obrigatórios", f"{campos_ok}/{len(campos_obrigatorios)}")
                    
                    # Preview da tabela consolidada
                    st.dataframe(df_final_padronizado.head(10), use_container_width=True)
                    
                    # Validação final
                    problemas = []
                    campos_obrigatorios_validacao = ['empresa', 'tipo', 'status', 'situacao', 'nome_cliente', 'classe', 'contrato', 'valor_principal', 'valor_nao_cedido', 'valor_terceiro', 'valor_cip', 'data_vencimento']
                    
                    for campo in campos_obrigatorios_validacao:
                        if campo not in df_final_padronizado.columns:
                            problemas.append(f"❌ Campo {campo.replace('_', ' ').title()} não identificado")
                    
                    if problemas:
                        st.warning("⚠️ **Atenção:** Alguns campos obrigatórios não foram identificados:")
                        for problema in problemas:
                            st.write(problema)
                        st.write("Revise os mapeamentos antes de prosseguir.")
                    else:
                        st.success("🎯 **Perfeito!** Todos os campos obrigatórios foram identificados corretamente.")
                else:
                    st.error("❌ Nenhum arquivo foi processado com sucesso. Verifique os mapeamentos.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao aplicar mapeamentos: {str(e)}")
    
    # Status do mapeamento geral
    if 'df_padronizado' in st.session_state and not st.session_state.df_padronizado.empty:
        st.markdown("---")
        st.success(f"✅ **Mapeamento concluído:** {len(st.session_state.df_padronizado):,} registros padronizados de {len(st.session_state.get('dataframes_individuais', {})):,} arquivo(s)")

def etapa_correcao():
    """Etapa 4: Correção Monetária (inclui cálculo automático de aging)"""
    st.header("💰 CORREÇÃO MONETÁRIA e VALOR JUSTO")
    
    # Verificar se temos dados padronizados
    if 'df_padronizado' not in st.session_state or st.session_state.df_padronizado.empty:
        st.warning("⚠️ Realize o mapeamento de campos antes de calcular a correção monetária.")
        return
    
    df_padronizado = st.session_state.df_padronizado
    calc_aging = CalculadorAging(st.session_state.params)
    calc_correcao = CalculadorCorrecao(st.session_state.params)
    
    # Verificar se temos dados de taxa de recuperação (OBRIGATÓRIO)
    tem_taxa_recuperacao = 'df_taxa_recuperacao' in st.session_state and not st.session_state.df_taxa_recuperacao.empty
    
    # Seção OBRIGATÓRIA para upload de taxa de recuperação
    st.subheader("📈 Configurar Taxa de Recuperação (OBRIGATÓRIO)")
    
    if not tem_taxa_recuperacao:
        st.warning("⚠️ **ATENÇÃO:** O arquivo de taxa de recuperação é obrigatório para realizar os cálculos de correção monetária.")
    
    with st.expander("📤 Upload da Taxa de Recuperação", expanded=not tem_taxa_recuperacao):
        st.info("""
        **📋 Instruções:** 
        
        Faça o upload do arquivo Excel com as taxas de recuperação. O arquivo deve conter:
        - Uma aba chamada "Input" 
        - Estrutura com empresas marcadas com "x" 
        - Tipos: Privada, Público, Hospital
        - Aging: A vencer, Primeiro ano, Segundo ano, Terceiro ano, Demais anos
        - Taxas e prazos de recebimento
        """)
        
        # Upload do arquivo
        uploaded_file_taxa = st.file_uploader(
            "📤 Selecione o arquivo de Taxa de Recuperação",
            type=['xlsx', 'xls'],
            help="Arquivo Excel com as taxas de recuperação por empresa, tipo e aging",
            key="upload_taxa_modulo4"
        )
        
        if uploaded_file_taxa is not None:
            try:
                with st.spinner("🔄 Processando arquivo de taxa de recuperação..."):
                    # Ler a aba "input"
                    df_taxa_upload = pd.read_excel(uploaded_file_taxa, sheet_name="Input", header=None)
                    
                    # Parâmetros para processamento
                    tipos = ["Privado", "Público", "Hospital"]
                    aging_labels = ["A vencer", "Primeiro ano", "Segundo ano", "Terceiro ano", "Demais anos"]
                    
                    empresa = None
                    dados_taxa = []
                    
                    # Processar o DataFrame conforme a lógica fornecida
                    for i in range(len(df_taxa_upload)):
                        row = df_taxa_upload.iloc[i]

                        # Detectar empresa pelo "x"
                        for j in range(len(row) - 1):
                            if str(row[j]).strip().lower() == "x":
                                empresa = str(row[j + 1]).strip()

                        # Se não tiver empresa atual, pula
                        if not empresa:
                            continue

                        # Cada linha pode ter até 3 blocos: Privada, Público, Hospital
                        for offset, tipo in zip([1, 5, 9], tipos):  # colunas: aging, taxa, prazo
                            try:
                                aging = str(row[offset]).strip()
                                taxa = row[offset + 1]
                                prazo = row[offset + 2]

                                if aging in aging_labels and pd.notna(taxa) and pd.notna(prazo):
                                    dados_taxa.append({
                                        "Empresa": empresa,
                                        "Tipo": tipo,
                                        "Aging": aging,
                                        "Taxa de recuperação": float(str(taxa).replace(",", ".")),
                                        "Prazo de recebimento": int(prazo)
                                    })
                            except (IndexError, ValueError):
                                continue
                    
                    # Criar DataFrame final
                    if dados_taxa:
                        df_taxa_recuperacao_nova = pd.DataFrame(dados_taxa)
                        st.session_state.df_taxa_recuperacao = df_taxa_recuperacao_nova
                        
                        # Resetar flag de cálculo para forçar recálculo
                        if 'df_final' in st.session_state:
                            del st.session_state.df_final
                        if 'df_com_aging' in st.session_state:
                            del st.session_state.df_com_aging
                        
                        st.success(f"✅ Taxa de recuperação carregada! {len(df_taxa_recuperacao_nova)} registros de {df_taxa_recuperacao_nova['Empresa'].nunique()} empresa(s).")
                        
                        # Preview dos dados carregados
                        st.subheader("📊 Preview da Taxa de Recuperação Carregada")
                        # Exibir amostra balanceada por empresa
                        empresas = df_taxa_recuperacao_nova['Empresa'].unique()
                        amostra = pd.concat([
                            df_taxa_recuperacao_nova[df_taxa_recuperacao_nova['Empresa'] == emp].head(1)
                            for emp in empresas
                        ])

                        # Se ainda quiser limitar a 10 linhas no máximo
                        amostra = amostra.head(10)

                        st.dataframe(amostra, use_container_width=True)
                        
                        # st.rerun()  # Atualizar a interface
                    else:
                        st.error("❌ Nenhum dado válido encontrado no arquivo. Verifique a estrutura do arquivo.")
                        
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")
                st.error("Verifique se o arquivo possui uma aba 'Input' e se a estrutura está correta.")
    
    # uploaded_file_taxa = None
    # del st.session_state.df_taxa_recuperacao

    # Atualizar variável após possível upload
    tem_taxa_recuperacao = 'df_taxa_recuperacao' in st.session_state and not st.session_state.df_taxa_recuperacao.empty

    # st.code(tem_taxa_recuperacao)
    # st.session_state.df_taxa_recuperacao
    
    st.markdown("---")
    
    # SÓ PERMITIR CÁLCULO SE TIVER TAXA DE RECUPERAÇÃO
    if not tem_taxa_recuperacao:
        st.error("❌ **Não é possível prosseguir sem a taxa de recuperação.**")
        st.info("� Faça o upload do arquivo de taxa de recuperação acima para continuar.")
        return
    
    # Botão para calcular correção (SÓ APARECE SE TIVER TAXA)
    if st.button("💰 Calcular Correção Monetária com Taxa de Recuperação", type="primary"):
        try:
            with st.spinner("⚙️ Processando aging e calculando correção monetária..."):
                # Primeiro, calcular aging automaticamente
                df_com_aging = calc_aging.processar_aging_completo(df_padronizado.copy())
                
                if df_com_aging.empty:
                    st.error("❌ Erro ao calcular aging. Verifique os dados de entrada.")
                    return
                
                # Sempre usar método com taxa de recuperação (já que é obrigatória)
                df_final = calc_correcao.processar_correcao_completa_com_recuperacao(
                    df_com_aging.copy(), 
                    "Distribuidora", 
                    st.session_state.df_taxa_recuperacao
                )
                
                if not df_final.empty:
                    st.session_state.df_com_aging = df_com_aging
                    df_final = df_final.dropna(subset=['empresa'])
                    st.session_state.df_final = df_final
                    
                    st.success("✅ Correção monetária com taxa de recuperação calculada com sucesso!")
                else:
                    st.error("❌ Erro ao calcular correção monetária.")
                    return
                    
        except Exception as e:
            st.error(f"❌ Erro ao processar correção: {str(e)}")

    # Mostrar resultados se já foram calculados
    if 'df_final' in st.session_state and not st.session_state.df_final.empty:
       
        st.markdown("---")
        
        # 2. Correção Monetária - Tabela de Resultados
        st.subheader("💰 Resultados da Correção Monetária e Valor Justo")
        
        # Verificar se temos colunas de taxa de recuperação (sempre deveria ter)
        colunas_taxa = ['aging_taxa', 'taxa_recuperacao', 'prazo_recebimento', 'valor_recuperavel']
        tem_colunas_recuperacao = all(col in st.session_state.df_final.columns for col in colunas_taxa)
        
        if tem_colunas_recuperacao:
            st.success("✅ **Resultados com taxa de recuperação**")
        else:
            st.warning("⚠️ **Resultados sem taxa de recuperação** - Recalcule para incluir as taxas")
        
        # Mostrar colunas principais + taxa de recuperação
        colunas_principais = [
            'empresa', 'tipo', 'nome_cliente', 'contrato', 
            'valor_liquido', 'aging', 'aging_taxa',
            'valor_corrigido', 'taxa_recuperacao', 'valor_recuperavel'
        ]

        ordem_aging = [
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

        # 📊 Visão Detalhada por Empresa, Tipo e Classificação
        st.subheader("📊 Agrupamento Detalhado - Por Empresa, Tipo, Classe, Status e Situação")
        
        df_agg1 = (
            st.session_state.df_final
            .groupby(['empresa', 'tipo', 'classe', 'status', 'situacao', 'aging', 'aging_taxa'], dropna=False)
            .agg({
                'valor_corrigido': 'sum',
                'taxa_recuperacao': 'mean',
                'valor_recuperavel': 'sum'
            })
            .reset_index()
        )

        df_agg1['aging'] = pd.Categorical(df_agg1['aging'], categories=ordem_aging, ordered=True)
        df_agg1 = df_agg1.sort_values(['empresa', 'tipo', 'classe', 'status', 'situacao', 'aging'])

        st.dataframe(df_agg1, use_container_width=True, hide_index=True)

        # 🎯 Visão Consolidada por Empresa e Aging
        st.subheader("🎯 Agrupamento Consolidado - Por Empresa e Aging")
        st.caption("Valores consolidados por empresa e faixa de aging, incluindo valor principal, líquido, corrigido e recuperável")
        
        df_agg2 = (
            st.session_state.df_final
            .groupby(['empresa', 'aging', 'aging_taxa'], dropna=False)
            .agg({
                'valor_principal': 'sum',
                'valor_liquido': 'sum',
                'valor_corrigido': 'sum',
                'valor_recuperavel': 'sum'
            })
            .reset_index()
        )

        df_agg2['aging'] = pd.Categorical(df_agg2['aging'], categories=ordem_aging, ordered=True)
        df_agg2 = df_agg2.sort_values(['empresa', 'aging'])

        st.dataframe(df_agg2, use_container_width=True, hide_index=True)

        # 📈 Visão Geral por Aging
        st.subheader("📈 Agrupamento Geral - Por Aging e Taxa de Recuperação")
        st.caption("Visão consolidada geral agrupada apenas por faixa de aging, mostrando totais gerais")
        
        df_agg3 = (
            st.session_state.df_final
            .groupby(['aging', 'aging_taxa'], dropna=False)
            .agg({
                'valor_principal': 'sum',
                'valor_liquido': 'sum',
                'valor_corrigido': 'sum',
                'valor_recuperavel': 'sum'
            })
            .reset_index()
        )

        df_agg3['aging'] = pd.Categorical(df_agg3['aging'], categories=ordem_aging, ordered=True)
        df_agg3 = df_agg3.sort_values(['aging'])

        st.dataframe(df_agg3, use_container_width=True, hide_index=True)

        # 💰 Resumo Total Consolidado
        st.markdown("---")
        st.subheader("💰 Resumo Total Consolidado")
        
        # Calcular totais gerais
        total_principal = df_agg3['valor_principal'].sum()
        total_liquido = df_agg3['valor_liquido'].sum()
        total_corrigido = df_agg3['valor_corrigido'].sum()
        total_recuperavel = df_agg3['valor_recuperavel'].sum()
        
        # Criar 4 colunas para as métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 Valor Principal Total",
                f"R$ {total_principal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                help="Soma total dos valores principais de todas as faixas de aging"
            )
        
        with col2:
            st.metric(
                "💧 Valor Líquido Total",
                f"R$ {total_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                help="Soma total dos valores líquidos de todas as faixas de aging"
            )
        
        with col3:
            st.metric(
                "⚡ Valor Corrigido Total",
                f"R$ {total_corrigido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                help="Soma total dos valores corrigidos monetariamente"
            )
        
        with col4:
            st.metric(
                "🎯 Valor Recuperável Total",
                f"R$ {total_recuperavel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                help="Soma total dos valores esperados de recuperação"
            )

        # st.code(st.session_state.df_final.columns)
        
    # Status da correção
    if 'df_final' in st.session_state and not st.session_state.df_final.empty:
        st.success(f"✅ Processamento concluído")

if __name__ == "__main__":
    main()
