"""
Página de Carregamento - FIDC Calculator
Upload e análise de arquivos Excel das distribuidoras
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.analisador_bases import AnalisadorBases

def show():
    """Página de Carregamento da Base"""
    st.header("📂 CARREGAMENTO DA BASE")
    
    # Verificar se os parâmetros estão inicializados
    if 'params' not in st.session_state:
        from utils.parametros_correcao import ParametrosCorrecao
        st.session_state.params = ParametrosCorrecao()
    
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
            col1, col2, col3 = st.columns([2, 1, 1])
            
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📁 Total de Arquivos", len(st.session_state.arquivos_processados))
        
        with col2:
            st.metric("📊 Total de Registros", f"{total_registros:,}")
        
        # Preparar dados para as próximas etapas automaticamente
        st.session_state.df_carregado = st.session_state.arquivos_processados
    
    else:
        st.info("ℹ️ Inicie o processo carregando arquivos Excel para ver os resultados.")
    
    # Informações sobre tipos de arquivo suportados
    st.markdown("---")
    st.subheader("ℹ️ Informações sobre Upload")
    
    with st.expander("📖 Formatos Suportados", expanded=False):
        st.info("""
        **Formatos de arquivo aceitos:**
        - `.xlsx` - Excel moderno (recomendado)
        - `.xls` - Excel legado
        
        **Estrutura esperada:**
        - Dados organizados em tabela
        - Primeira linha como cabeçalho
        - Colunas com informações de empresa, cliente, valor, vencimento, etc.
        - Data base preferencialmente no cabeçalho (nome da coluna)
        
        **Tamanho máximo:** 200MB por arquivo
        
        **Múltiplos arquivos:** Suportado - todos serão processados e consolidados
        """)
    
    with st.expander("🔍 Como o Sistema Detecta Dados", expanded=False):
        st.info("""
        **Detecção automática de data base:**
        1. Procura por datas nos nomes das colunas (cabeçalho)
        2. Identifica colunas de vencimento com datas válidas
        3. Permite ajuste manual se necessário
        
        **Análise de estrutura:**
        - Conta registros e colunas
        - Identifica tipos de dados
        - Detecta valores monetários
        - Valida formato da tabela
        
        **Validações realizadas:**
        - Arquivo não vazio
        - Estrutura de tabela válida
        - Pelo menos uma coluna de dados
        - Encoding compatível
        """)

if __name__ == "__main__":
    show()
