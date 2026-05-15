"""
Página de Carregamento - FIDC Calculator
Upload e análise de arquivos Excel das distribuidoras

Fluxo atualizado:
1. Recebe arquivos XLSX/XLS;
2. Salva temporariamente em disco;
3. Envia o caminho do Excel para o AnalisadorBases;
4. O analisador converte para Parquet e retorna metadados;
5. A aplicação mantém no session_state apenas informações leves.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from utils.analisador_bases import AnalisadorBases
from utils.gerenciador_arquivos import salvar_upload_temporario


def show():
    """Página de Carregamento da Base"""

    st.header("📂 Carregamento da Base")

    # ============================================================
    # 1. Inicialização dos parâmetros e estados
    # ============================================================

    if "params" not in st.session_state:
        from utils.parametros_correcao import ParametrosCorrecao
        st.session_state.params = ParametrosCorrecao()

    if "arquivos_para_processar" not in st.session_state:
        st.session_state.arquivos_para_processar = {}

    if "arquivos_processados" not in st.session_state:
        st.session_state.arquivos_processados = {}

    if "processamento_confirmado" not in st.session_state:
        st.session_state.processamento_confirmado = False

    if "analisador" not in st.session_state:
        st.session_state.analisador = AnalisadorBases(st.session_state.params)

    # ============================================================
    # 2. Estilização do uploader
    # ============================================================

    st.markdown(
        """
        <style>
        div[data-testid="stFileUploader"] label p {
            font-size: 115% !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ============================================================
    # 3. Upload dos arquivos
    # ============================================================

    uploaded_files = st.file_uploader(
        "📤 Selecione os arquivos Excel das distribuidoras:",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        help=(
            "Você pode carregar múltiplos arquivos Excel. "
            "Cada um será processado individualmente e convertido para Parquet."
        )
    )

    # ============================================================
    # 4. Salvar uploads temporariamente em disco
    # ============================================================

    if uploaded_files:
        for uploaded_file in uploaded_files:
            nome_arquivo = uploaded_file.name

            # Evita adicionar novamente o mesmo arquivo
            if (
                nome_arquivo not in st.session_state.arquivos_para_processar
                and nome_arquivo not in st.session_state.arquivos_processados
            ):
                caminho_temp = salvar_upload_temporario(uploaded_file)

                st.session_state.arquivos_para_processar[nome_arquivo] = {
                    "nome_arquivo": nome_arquivo,
                    "caminho_excel": caminho_temp
                }

                st.success(f"✅ Arquivo adicionado: {nome_arquivo}")

    # ============================================================
    # 5. Mostrar arquivos aguardando processamento
    # ============================================================

    if st.session_state.arquivos_para_processar:
        st.markdown("---")
        st.subheader("📋 Arquivos Aguardando Processamento")

        for nome_arquivo in st.session_state.arquivos_para_processar.keys():
            st.info(
                f"📄 **{nome_arquivo}** - "
                "Aguardando confirmação para processamento"
            )

        st.markdown("---")

        if st.button(
            "🔄 Confirmar e Processar Todos os Arquivos",
            type="primary",
            key="confirmar_processar_arquivos"
        ):
            st.session_state.processamento_confirmado = True

    # ============================================================
    # 6. Processar arquivos confirmados
    # ============================================================

    if (
        st.session_state.processamento_confirmado
        and st.session_state.arquivos_para_processar
    ):
        with st.spinner("🔄 Processando, analisando e convertendo arquivos para Parquet..."):

            for nome_arquivo, arquivo_info in st.session_state.arquivos_para_processar.items():

                if nome_arquivo not in st.session_state.arquivos_processados:
                    try:
                        st.write(f"🔄 Processando **{nome_arquivo}**...")

                        caminho_excel = arquivo_info["caminho_excel"]

                        # O método agora retorna metadados + caminho do parquet
                        info_processamento = (
                            st.session_state.analisador.carregar_base_excel(
                                caminho_excel,
                                nome_arquivo
                            )
                        )

                        if info_processamento:
                            st.session_state.arquivos_processados[nome_arquivo] = (
                                info_processamento
                            )

                            st.success(
                                f"✅ {nome_arquivo} processado e convertido com sucesso!"
                            )

                        else:
                            st.error(
                                f"❌ Erro ao processar {nome_arquivo}. "
                                "Verifique se é um arquivo Excel válido."
                            )

                    except Exception as e:
                        st.error(
                            f"❌ Erro ao processar {nome_arquivo}: {str(e)}"
                        )

            # Limpa fila de processamento após concluir
            st.session_state.arquivos_para_processar = {}
            st.session_state.processamento_confirmado = False

            st.success("✅ Processamento concluído!")

    # ============================================================
    # 7. Exibir resumo dos arquivos processados
    # ============================================================

    if st.session_state.arquivos_processados:
        st.markdown("---")
        st.subheader("📋 Arquivos Processados")

        total_registros = 0
        total_valor = 0

        for nome_arquivo, info in st.session_state.arquivos_processados.items():

            registros = info.get("registros", 0)
            colunas = info.get("colunas", 0)
            valor_total = info.get("valor_total", 0)

            total_registros += registros

            try:
                total_valor += float(valor_total or 0)
            except Exception:
                pass

            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.success(f"**📄 {nome_arquivo}**")

            with col2:
                st.metric("📊 Registros", f"{registros:,}")

            with col3:
                st.metric("📋 Colunas", colunas)

            # ============================================================
            # 7.1. Exibir data base detectada
            # ============================================================

            data_base_info = info.get("data_base_info", {})

            if data_base_info.get("detectada"):
                coluna_preferida = data_base_info.get("coluna_preferida", {})
                data_base_detectada = data_base_info.get("data_base_detectada")

                with st.expander(
                    f"📅 Data Base: {nome_arquivo}",
                    expanded=False
                ):
                    col_data1, col_data2 = st.columns(2)

                    with col_data1:
                        if coluna_preferida.get("eh_data_base"):
                            st.info(
                                f"""
                                **🔍 Data Base Detectada no Cabeçalho**

                                📋 **Coluna:** {coluna_preferida.get('coluna')}  
                                📅 **Data Base:** {data_base_detectada.strftime('%d/%m/%Y')}  
                                🎯 **Tipo:** Data real no cabeçalho do Excel  
                                ✅ **Status:** Data base oficial detectada
                                """
                            )
                        else:
                            registros_validos = coluna_preferida.get(
                                "registros_validos",
                                0
                            )
                            percentual_valido = coluna_preferida.get(
                                "percentual_valido",
                                0
                            )

                            st.info(
                                f"""
                                **🔍 Data Base Derivada de Vencimentos**

                                📋 **Coluna:** {coluna_preferida.get('coluna')}  
                                📅 **Data Base:** {data_base_detectada.strftime('%d/%m/%Y')}  
                                🎯 **Tipo:** Maior data de vencimento  
                                ✅ **Registros válidos:** {registros_validos:,} ({percentual_valido:.1%})
                                """
                            )

                    with col_data2:
                        st.write("**🛠️ Ajustar data base**")

                        nova_data = st.date_input(
                            f"Nova data base para {nome_arquivo}:",
                            value=data_base_detectada.date(),
                            key=f"data_base_{nome_arquivo}"
                        )

                        if st.button(
                            "💾 Salvar Data Base",
                            key=f"salvar_data_{nome_arquivo}"
                        ):
                            st.session_state.params.data_base_padrao = (
                                pd.to_datetime(nova_data)
                            )

                            st.success(
                                f"✅ Data base atualizada: "
                                f"{nova_data.strftime('%d/%m/%Y')}"
                            )

                            st.rerun()

            else:
                # ============================================================
                # 7.2. Caso nenhuma data seja detectada
                # ============================================================

                with st.expander(
                    f"⚠️ Data Base: {nome_arquivo}",
                    expanded=False
                ):
                    st.warning(
                        "⚠️ **Nenhuma data foi detectada automaticamente.**"
                    )

                    st.info(
                        "**💡 Dica:** verifique se o arquivo possui:\n"
                        "- Uma coluna com data no cabeçalho "
                        "(ex: 2025-02-15)\n"
                        "- Uma coluna de vencimento com datas válidas"
                    )

                    st.write("**🛠️ Definir Data Base Manualmente**")

                    data_manual = st.date_input(
                        f"Data base para {nome_arquivo}:",
                        value=datetime.now().date(),
                        key=f"data_manual_{nome_arquivo}"
                    )

                    if st.button(
                        "💾 Definir Data Base",
                        key=f"definir_data_{nome_arquivo}"
                    ):
                        st.session_state.params.data_base_padrao = (
                            pd.to_datetime(data_manual)
                        )

                        st.success(
                            f"✅ Data base definida: "
                            f"{data_manual.strftime('%d/%m/%Y')}"
                        )

                        st.rerun()

            # ============================================================
            # 7.3. Preview leve salvo durante o processamento
            # ============================================================

            with st.expander(
                f"👀 Preview: {nome_arquivo}",
                expanded=False
            ):
                preview = info.get("preview")

                if preview is not None and not preview.empty:
                    st.dataframe(
                        preview,
                        use_container_width=True
                    )
                else:
                    st.info("ℹ️ Nenhum preview disponível para este arquivo.")

        # ============================================================
        # 8. Resumo consolidado
        # ============================================================

        st.markdown("---")
        st.subheader("📊 Resumo Consolidado")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "📁 Total de Arquivos",
                len(st.session_state.arquivos_processados)
            )

        with col2:
            st.metric(
                "📊 Total de Registros",
                f"{total_registros:,}"
            )

        # Mantém a chave esperada pelas próximas páginas,
        # mas agora contendo metadados e caminhos Parquet
        st.session_state.df_carregado = (
            st.session_state.arquivos_processados
        )

    else:
        st.info(
            "ℹ️ Inicie o processo carregando arquivos Excel "
            "para ver os resultados."
        )

    # ============================================================
    # 9. Informações complementares da página
    # ============================================================

    st.markdown("---")
    st.subheader("ℹ️ Informações sobre Upload")

    with st.expander("📖 Formatos suportados", expanded=False):
        st.info(
            """
            **Formatos de arquivo aceitos:**
            - `.xlsx` - Excel moderno, recomendado para upload
            - `.xls` - Excel legado

            **Fluxo interno otimizado:**
            - O arquivo é recebido em Excel
            - O sistema o salva temporariamente
            - A base é convertida para `.parquet`
            - As próximas etapas passam a usar o Parquet internamente

            **Estrutura esperada:**
            - Dados organizados em tabela
            - Primeira linha como cabeçalho
            - Colunas com informações de empresa, cliente, valor, vencimento, etc.
            - Data base preferencialmente no cabeçalho

            **Tamanho máximo:** 200MB por arquivo

            **Múltiplos arquivos:** Suportado - todos serão processados individualmente
            """
        )

    with st.expander("🔍 Como o Sistema Detecta Dados", expanded=False):
        st.info(
            """
            **Detecção automática de data base:**
            1. Procura por datas nos nomes das colunas
            2. Identifica colunas de vencimento com datas válidas
            3. Permite ajuste manual se necessário

            **Análise de estrutura:**
            - Conta registros e colunas
            - Identifica valores monetários prováveis
            - Detecta data base
            - Gera preview de amostra

            **Validações realizadas:**
            - Arquivo não vazio
            - Estrutura de tabela válida
            - Pelo menos uma coluna de dados
            - Conversão para Parquet concluída
            """
        )


if __name__ == "__main__":
    show()