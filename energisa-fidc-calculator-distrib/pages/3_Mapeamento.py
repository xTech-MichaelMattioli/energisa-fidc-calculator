"""
Página de Mapeamento - FIDC Calculator
Mapeamento automático e manual de campos dos arquivos

Fluxo atualizado:
1. Recebe os arquivos já convertidos para Parquet na etapa de carregamento;
2. Usa apenas preview e lista de colunas para montar a interface de mapeamento;
3. Lê o Parquet completo apenas ao aplicar os mapeamentos;
4. Salva o resultado final padronizado em Parquet;
5. Mantém no session_state apenas metadados, previews e caminhos dos arquivos.
"""

import os
import tempfile
from pathlib import Path

import streamlit as st
import pandas as pd

from utils.mapeador_campos import MapeadorCampos


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def detectar_voltz(arquivos_processados, mapeador):
    """
    Função unificada para detectar se algum arquivo é VOLTZ.
    """
    for nome_arquivo in arquivos_processados.keys():
        if hasattr(mapeador, "identificar_tipo_distribuidora"):
            if mapeador.identificar_tipo_distribuidora(nome_arquivo) == "VOLTZ":
                return True

        # Fallback - verificar pelo nome
        if "VOLTZ" in nome_arquivo.upper():
            return True

    return False


def obter_campos_obrigatorios_voltz():
    """
    Retorna lista de campos obrigatórios para VOLTZ.
    """
    return [
        "empresa",
        "nome_cliente",
        "contrato",
        "valor_principal",
        "valor_nao_cedido",
        "valor_terceiro",
        "valor_cip",
        "data_vencimento",
    ]


def obter_campos_obrigatorios_padrao():
    """
    Retorna lista de campos obrigatórios para distribuidoras padrão.
    """
    return [
        "empresa",
        "tipo",
        "status",
        "situacao",
        "nome_cliente",
        "classe",
        "contrato",
        "valor_principal",
        "valor_nao_cedido",
        "valor_terceiro",
        "valor_cip",
        "data_vencimento",
    ]


def obter_pasta_parquet_mapeamento() -> str:
    """
    Retorna pasta temporária para arquivos Parquet gerados no mapeamento.
    """
    pasta = Path(tempfile.gettempdir()) / "fidc_calculator" / "mapeamento"
    pasta.mkdir(parents=True, exist_ok=True)
    return str(pasta)


def gerar_caminho_parquet_padronizado(nome_arquivo: str) -> str:
    """
    Gera caminho para salvar o Parquet padronizado de um arquivo individual.
    """
    pasta = obter_pasta_parquet_mapeamento()
    nome_sem_extensao = os.path.splitext(nome_arquivo)[0]
    return os.path.join(pasta, f"{nome_sem_extensao}_padronizado.parquet")


def gerar_caminho_parquet_final() -> str:
    """
    Gera caminho do Parquet consolidado final.
    """
    pasta = obter_pasta_parquet_mapeamento()
    return os.path.join(pasta, "base_final_padronizada.parquet")


def obter_dataframe_referencia_mapeamento(info_arquivo: dict) -> pd.DataFrame:
    """
    Retorna um DataFrame leve para uso no mapeamento automático/manual.

    Prioridade:
    1. Preview salvo no carregamento;
    2. DataFrame vazio apenas com as colunas da base.
    """
    preview = info_arquivo.get("preview")

    if preview is not None and not preview.empty:
        return preview.copy()

    nomes_colunas = info_arquivo.get("nomes_colunas", [])
    return pd.DataFrame(columns=nomes_colunas)


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def show():
    """Página de Mapeamento de Campos"""

    st.header("🗺️ Mapeamento de Campos")

    # ============================================================
    # 1. Validar carregamento prévio
    # ============================================================

    if "df_carregado" not in st.session_state or not st.session_state.df_carregado:
        st.warning(
            "⚠️ Carregue um ou mais arquivos antes de prosseguir para o mapeamento."
        )
        st.info(
            "💡 Vá para a página de **Carregamento** e faça upload dos arquivos Excel primeiro."
        )
        return

    # ============================================================
    # 2. Inicializar parâmetros e mapeador
    # ============================================================

    if "params" not in st.session_state:
        from utils.parametros_correcao import ParametrosCorrecao
        st.session_state.params = ParametrosCorrecao()

    arquivos_processados = st.session_state.df_carregado
    mapeador = MapeadorCampos(st.session_state.params)

    st.write(
        "Mapeie as colunas dos arquivos para os campos padrão do sistema."
    )

    # ============================================================
    # 3. Informações gerais
    # ============================================================

    total_arquivos = len(arquivos_processados)
    total_registros = sum(
        info.get("registros", 0)
        for info in arquivos_processados.values()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📁 Arquivos para Mapear", total_arquivos)

    with col2:
        mapeamentos_salvos = 0

        if "mapeamentos_finais" in st.session_state:
            mapeamentos_salvos = len(st.session_state.mapeamentos_finais)

        st.metric(
            "✅ Mapeamentos Salvos",
            f"{mapeamentos_salvos}/{total_arquivos}"
        )

    with col3:
        st.metric("📊 Total de Registros", f"{total_registros:,}")

    st.markdown("---")

    # ============================================================
    # 4. Inicializar estado dos mapeamentos
    # ============================================================

    if "mapeamentos_finais" not in st.session_state:
        st.session_state.mapeamentos_finais = {}

    # ============================================================
    # 5. Mapeamento individual por arquivo
    # ============================================================

    for nome_arquivo, info_arquivo in arquivos_processados.items():
        st.subheader(f"📄 Mapeamento: {nome_arquivo}")

        registros = info_arquivo.get("registros", 0)
        colunas = info_arquivo.get("colunas", 0)
        preview = info_arquivo.get("preview")
        nomes_colunas = info_arquivo.get("nomes_colunas", [])

        # DataFrame leve apenas para montar interface e sugestões
        df_referencia = obter_dataframe_referencia_mapeamento(info_arquivo)

        # ============================================================
        # 5.1. Informações do arquivo
        # ============================================================

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"📊 **Registros:** {registros:,}")

        with col2:
            st.info(f"📋 **Colunas:** {colunas}")

        # ============================================================
        # 5.2. Estrutura do arquivo
        # ============================================================

        with st.expander(
            f"📋 Ver estrutura de {nome_arquivo}",
            expanded=False
        ):
            if preview is not None and not preview.empty:
                st.dataframe(preview, use_container_width=True)
            else:
                st.info("ℹ️ Nenhum preview disponível para este arquivo.")

            st.write("**📋 Lista de Colunas:**")

            colunas_formatadas = [f"• {col}" for col in nomes_colunas]
            st.write("\n".join(colunas_formatadas[:15]))

            if len(nomes_colunas) > 15:
                st.caption(f"... e mais {len(nomes_colunas) - 15} colunas")

        # ============================================================
        # 5.3. Mapeamento automático
        # ============================================================

        try:
            with st.spinner(f"🔍 Analisando colunas de {nome_arquivo}..."):
                mapeamento_auto = mapeador.criar_mapeamento_automatico(
                    df_referencia,
                    nome_arquivo
                )

        except Exception as e:
            st.error(
                f"❌ Erro no mapeamento automático de {nome_arquivo}: {str(e)}"
            )
            mapeamento_auto = {}

        # Usar mapeamento salvo se existir, senão usar o automático
        if nome_arquivo in st.session_state.mapeamentos_finais:
            mapeamento_inicial = st.session_state.mapeamentos_finais[nome_arquivo]
        else:
            mapeamento_inicial = mapeamento_auto if mapeamento_auto else {}

        # ============================================================
        # 5.4. Mapeamento manual
        # ============================================================

        try:
            mapeamento_manual = mapeador.permitir_mapeamento_manual(
                df_referencia,
                mapeamento_inicial,
                nome_arquivo,
                key_suffix=f"_{nome_arquivo.replace('.', '_').replace(' ', '_')}"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "💾 Salvar Mapeamento",
                    key=f"salvar_{nome_arquivo}",
                    type="secondary"
                ):
                    st.session_state.mapeamentos_finais[nome_arquivo] = (
                        mapeamento_manual
                    )

                    st.success(
                        f"✅ Mapeamento salvo para {nome_arquivo}!"
                    )

                    st.rerun()

            with col2:
                if nome_arquivo in st.session_state.mapeamentos_finais:
                    st.success("✅ Mapeamento salvo")
                else:
                    st.warning("⏳ Mapeamento não salvo")

        except Exception as e:
            st.error(
                f"❌ Erro no mapeamento manual de {nome_arquivo}: {str(e)}"
            )

        st.markdown("---")

    # ============================================================
    # 6. Aplicar todos os mapeamentos
    # ============================================================

    st.subheader("🔄 Aplicar Todos os Mapeamentos")

    mapeamentos_salvos = len(st.session_state.mapeamentos_finais)

    if mapeamentos_salvos == 0:
        st.warning("⚠️ Nenhum mapeamento foi salvo ainda.")

    elif mapeamentos_salvos < total_arquivos:
        st.warning(
            f"⚠️ Apenas {mapeamentos_salvos} de {total_arquivos} mapeamentos foram salvos."
        )

    else:
        st.success(
            f"✅ Todos os {total_arquivos} mapeamentos foram salvos!"
        )

    # ============================================================
    # 6.1. Botão de aplicação final
    # ============================================================

    if st.button(
        "🚀 Aplicar Todos os Mapeamentos",
        type="primary",
        key="aplicar_todos_mapeamentos"
    ):
        if not st.session_state.mapeamentos_finais:
            st.error(
                "❌ Nenhum mapeamento foi salvo. "
                "Salve pelo menos um mapeamento antes de prosseguir."
            )
            return

        with st.spinner("🔄 Aplicando mapeamentos e padronizando dados..."):
            try:
                dataframes_padronizados = {}
                arquivos_padronizados_info = {}
                total_registros_processados = 0

                # ============================================================
                # 6.2. Aplicar mapeamento por arquivo
                # ============================================================

                for nome_arquivo, mapeamento_final in st.session_state.mapeamentos_finais.items():

                    if nome_arquivo not in arquivos_processados:
                        continue

                    info_arquivo = arquivos_processados[nome_arquivo]
                    caminho_parquet = info_arquivo.get("caminho_parquet")

                    if not caminho_parquet or not os.path.exists(caminho_parquet):
                        st.error(
                            f"❌ Parquet não encontrado para {nome_arquivo}."
                        )
                        continue

                    # Lê o arquivo completo apenas aqui, no processamento final
                    df_arquivo = pd.read_parquet(caminho_parquet)

                    # Aplicar mapeamento
                    df_padronizado = mapeador.aplicar_mapeamento(
                        df_arquivo,
                        mapeamento_final,
                        nome_arquivo
                    )

                    # Libera DataFrame original
                    del df_arquivo

                    if not df_padronizado.empty:
                        dataframes_padronizados[nome_arquivo] = df_padronizado
                        total_registros_processados += len(df_padronizado)

                        caminho_parquet_padronizado = (
                            gerar_caminho_parquet_padronizado(nome_arquivo)
                        )

                        df_padronizado.to_parquet(
                            caminho_parquet_padronizado,
                            index=False,
                            engine="pyarrow",
                            compression="snappy"
                        )

                        arquivos_padronizados_info[nome_arquivo] = {
                            "caminho_parquet": caminho_parquet_padronizado,
                            "registros": len(df_padronizado),
                            "colunas": len(df_padronizado.columns),
                            "nomes_colunas": df_padronizado.columns.tolist(),
                            "preview": df_padronizado.head(5).copy()
                        }

                        st.success(
                            f"✅ {nome_arquivo}: "
                            f"{len(df_padronizado):,} registros padronizados"
                        )

                    else:
                        st.error(
                            f"❌ Erro ao aplicar mapeamento em {nome_arquivo}"
                        )

                # ============================================================
                # 6.3. Consolidar bases padronizadas
                # ============================================================

                if dataframes_padronizados:

                    if len(dataframes_padronizados) == 1:
                        df_final_padronizado = list(
                            dataframes_padronizados.values()
                        )[0]

                    else:
                        df_final_padronizado = pd.concat(
                            dataframes_padronizados.values(),
                            ignore_index=True
                        )

                    # ============================================================
                    # 6.4. Verificação de duplicatas
                    # ============================================================

                    st.info("🔍 Verificando duplicatas...")

                    eh_voltz = detectar_voltz(
                        arquivos_processados,
                        mapeador
                    )

                    registros_antes = len(df_final_padronizado)

                    if eh_voltz:
                        st.info(
                            "⚡ **VOLTZ detectado** - "
                            "Usando critério específico: nome + data_vencimento + documento"
                        )

                        colunas_voltz = [
                            "nome_cliente",
                            "data_vencimento",
                            "documento"
                        ]

                        colunas_disponiveis = [
                            col for col in colunas_voltz
                            if col in df_final_padronizado.columns
                        ]

                        if len(colunas_disponiveis) >= 2:
                            colunas_para_duplicata = []

                            if "nome_cliente" in df_final_padronizado.columns:
                                df_final_padronizado["nome_cliente_limpo"] = (
                                    df_final_padronizado["nome_cliente"]
                                    .astype(str)
                                    .str.strip()
                                    .str.upper()
                                    .str.replace(r"\s+", " ", regex=True)
                                    .str.replace(r"[^\w\s]", "", regex=True)
                                    .str.replace(
                                        r"\b(LTDA|S\.?A\.?|ME|EPP|EIRELI)\b",
                                        "",
                                        regex=True
                                    )
                                    .str.strip()
                                )

                                colunas_para_duplicata.append(
                                    "nome_cliente_limpo"
                                )

                            if "data_vencimento" in df_final_padronizado.columns:
                                df_final_padronizado["data_vencimento_limpa"] = (
                                    pd.to_datetime(
                                        df_final_padronizado["data_vencimento"],
                                        errors="coerce"
                                    ).dt.date
                                )

                                colunas_para_duplicata.append(
                                    "data_vencimento_limpa"
                                )

                            if "documento" in df_final_padronizado.columns:
                                df_final_padronizado["documento_limpo"] = (
                                    df_final_padronizado["documento"]
                                    .astype(str)
                                    .str.replace(r"[^\d]", "", regex=True)
                                    .str.strip()
                                )

                                colunas_para_duplicata.append(
                                    "documento_limpo"
                                )

                            if colunas_para_duplicata:
                                # VOLTZ: manter todos os registros
                                colunas_auxiliares = [
                                    "nome_cliente_limpo",
                                    "data_vencimento_limpa",
                                    "documento_limpo"
                                ]

                                df_final_padronizado = (
                                    df_final_padronizado.drop(
                                        columns=[
                                            col for col in colunas_auxiliares
                                            if col in df_final_padronizado.columns
                                        ]
                                    )
                                )

                                st.success(
                                    "✅ **VOLTZ**: Todos os registros mantidos "
                                    "(duplicatas não removidas)"
                                )

                            else:
                                st.warning(
                                    "⚠️ **VOLTZ**: Colunas necessárias não encontradas "
                                    "para verificação de duplicatas"
                                )

                        else:
                            st.warning(
                                f"⚠️ **VOLTZ**: Apenas "
                                f"{len(colunas_disponiveis)} de 3 colunas necessárias encontradas: "
                                f"{colunas_disponiveis}"
                            )

                    else:
                        st.info(
                            "📊 **Distribuidora padrão** - "
                            "Usando critério padrão de duplicatas"
                        )

                        colunas_padrao = []

                        if "nome_cliente" in df_final_padronizado.columns:
                            df_final_padronizado["nome_cliente_limpo"] = (
                                df_final_padronizado["nome_cliente"]
                                .astype(str)
                                .str.strip()
                                .str.upper()
                            )

                            colunas_padrao.append("nome_cliente_limpo")

                        if "valor_principal" in df_final_padronizado.columns:
                            colunas_padrao.append("valor_principal")

                        if "data_vencimento" in df_final_padronizado.columns:
                            df_final_padronizado["data_vencimento_limpa"] = (
                                pd.to_datetime(
                                    df_final_padronizado["data_vencimento"],
                                    errors="coerce"
                                ).dt.date
                            )

                            colunas_padrao.append(
                                "data_vencimento_limpa"
                            )

                        if len(colunas_padrao) >= 2:
                            df_final_padronizado = (
                                df_final_padronizado.drop_duplicates(
                                    subset=colunas_padrao,
                                    keep="first"
                                ).reset_index(drop=True)
                            )

                            colunas_auxiliares = [
                                "nome_cliente_limpo",
                                "data_vencimento_limpa"
                            ]

                            df_final_padronizado = (
                                df_final_padronizado.drop(
                                    columns=[
                                        col for col in colunas_auxiliares
                                        if col in df_final_padronizado.columns
                                    ]
                                )
                            )

                            registros_depois = len(df_final_padronizado)
                            duplicatas_removidas = (
                                registros_antes - registros_depois
                            )

                            if duplicatas_removidas > 0:
                                st.warning(
                                    f"⚠️ **Padrão**: "
                                    f"{duplicatas_removidas:,} duplicatas removidas"
                                )
                            else:
                                st.success(
                                    "✅ **Padrão**: Nenhuma duplicata encontrada"
                                )

                        else:
                            st.info(
                                "ℹ️ Verificação de duplicatas não aplicada - "
                                "colunas insuficientes"
                            )

                    # ============================================================
                    # 6.5. Salvar base final em Parquet
                    # ============================================================

                    caminho_parquet_final = gerar_caminho_parquet_final()

                    df_final_padronizado.to_parquet(
                        caminho_parquet_final,
                        index=False,
                        engine="pyarrow",
                        compression="snappy"
                    )

                    preview_final = df_final_padronizado.head(10).copy()
                    campos_finais = df_final_padronizado.columns.tolist()
                    total_final_registros = len(df_final_padronizado)
                    total_final_colunas = len(df_final_padronizado.columns)

                    st.session_state.df_padronizado_info = {
                        "caminho_parquet": caminho_parquet_final,
                        "registros": total_final_registros,
                        "colunas": total_final_colunas,
                        "nomes_colunas": campos_finais,
                        "preview": preview_final
                    }

                    st.session_state.dataframes_individuais_info = (
                        arquivos_padronizados_info
                    )

                    # Remove estruturas antigas, caso existam
                    if "df_padronizado" in st.session_state:
                        del st.session_state.df_padronizado

                    if "dataframes_individuais" in st.session_state:
                        del st.session_state.dataframes_individuais

                    # ============================================================
                    # 6.6. Mensagens de sucesso e métricas
                    # ============================================================

                    st.success(
                        "🎯 **Mapeamento e verificação de duplicatas concluídos!** "
                        f"{total_final_registros:,} registros finais de "
                        f"{len(dataframes_padronizados)} arquivo(s)"
                    )

                    if registros_antes != total_final_registros:
                        duplicatas_removidas = (
                            registros_antes - total_final_registros
                        )

                        st.info(
                            f"📊 Registros processados: "
                            f"{registros_antes:,} → "
                            f"{total_final_registros:,} "
                            f"(removidas {duplicatas_removidas:,} duplicatas)"
                        )

                    st.subheader(
                        "📊 Preview dos Dados Padronizados Consolidados"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "📊 Total de Registros",
                            f"{total_final_registros:,}"
                        )

                    with col2:
                        st.metric(
                            "📁 Arquivos Processados",
                            len(dataframes_padronizados)
                        )

                    with col3:
                        eh_voltz_metricas = detectar_voltz(
                            arquivos_processados,
                            mapeador
                        )

                        if eh_voltz_metricas:
                            campos_obrigatorios = (
                                obter_campos_obrigatorios_voltz()
                            )
                        else:
                            campos_obrigatorios = (
                                obter_campos_obrigatorios_padrao()
                            )

                        campos_ok = sum(
                            1 for campo in campos_obrigatorios
                            if campo in campos_finais
                        )

                        st.metric(
                            "✅ Campos Obrigatórios",
                            f"{campos_ok}/{len(campos_obrigatorios)}"
                        )

                    st.dataframe(
                        preview_final,
                        use_container_width=True
                    )

                    # ============================================================
                    # 6.7. Validação final
                    # ============================================================

                    problemas = []

                    tem_voltz = detectar_voltz(
                        arquivos_processados,
                        mapeador
                    )

                    if tem_voltz:
                        campos_obrigatorios_validacao = (
                            obter_campos_obrigatorios_voltz()
                        )
                    else:
                        campos_obrigatorios_validacao = (
                            obter_campos_obrigatorios_padrao()
                        )

                    for campo in campos_obrigatorios_validacao:
                        if campo not in campos_finais:
                            problemas.append(
                                f"❌ Campo {campo.replace('_', ' ').title()} "
                                "não identificado"
                            )

                    if problemas:
                        st.warning(
                            "⚠️ **Atenção:** Alguns campos obrigatórios "
                            "não foram identificados:"
                        )

                        for problema in problemas:
                            st.write(problema)

                        st.write(
                            "Revise os mapeamentos antes de prosseguir."
                        )

                    else:
                        st.success(
                            "🎯 **Perfeito!** Todos os campos obrigatórios "
                            "foram identificados corretamente."
                        )

                        st.info(
                            "✨ **Próximo passo:** Vá para a página de "
                            "**Correção** para calcular os valores corrigidos."
                        )

                    # Libera DataFrame final após salvar Parquet e preview
                    del df_final_padronizado

                else:
                    st.error(
                        "❌ Nenhum arquivo foi processado com sucesso. "
                        "Verifique os mapeamentos."
                    )

            except Exception as e:
                st.error(
                    f"❌ Erro ao aplicar mapeamentos: {str(e)}"
                )

    # ============================================================
    # 7. Status do mapeamento geral
    # ============================================================

    if (
        "df_padronizado_info" in st.session_state
        and st.session_state.df_padronizado_info
    ):
        st.markdown("---")

        info_final = st.session_state.df_padronizado_info
        registros_finais = info_final.get("registros", 0)
        campos_mapeados = info_final.get("nomes_colunas", [])

        total_arquivos_individuais = len(
            st.session_state.get("dataframes_individuais_info", {})
        )

        st.success(
            f"✅ **Mapeamento concluído:** "
            f"{registros_finais:,} registros padronizados de "
            f"{total_arquivos_individuais:,} arquivo(s)"
        )

        st.subheader("📋 Resumo dos Campos Mapeados")

        eh_voltz_resumo = detectar_voltz(
            st.session_state.df_carregado,
            mapeador
        )

        if eh_voltz_resumo:
            campos_principais = [
                col for col in campos_mapeados
                if col in ["empresa", "nome_cliente", "contrato"]
            ]
        else:
            campos_principais = [
                col for col in campos_mapeados
                if col in [
                    "empresa",
                    "tipo",
                    "status",
                    "situacao",
                    "nome_cliente",
                    "classe",
                    "contrato"
                ]
            ]

        campos_valores = [
            col for col in campos_mapeados
            if "valor" in col.lower()
        ]

        campos_datas = [
            col for col in campos_mapeados
            if "data" in col.lower()
        ]

        campos_outros = [
            col for col in campos_mapeados
            if col not in campos_principais + campos_valores + campos_datas
        ]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.write("**👥 Campos Principais:**")
            for campo in campos_principais:
                st.write(f"• {campo}")

        with col2:
            st.write("**💰 Campos de Valor:**")
            for campo in campos_valores:
                st.write(f"• {campo}")

        with col3:
            st.write("**📅 Campos de Data:**")
            for campo in campos_datas:
                st.write(f"• {campo}")

        with col4:
            st.write("**📋 Outros Campos:**")
            for campo in campos_outros[:5]:
                st.write(f"• {campo}")

            if len(campos_outros) > 5:
                st.caption(
                    f"... e mais {len(campos_outros) - 5} campos"
                )

    # ============================================================
    # 8. Informações sobre o mapeamento
    # ============================================================

    st.markdown("---")
    st.subheader("ℹ️ Informações sobre Mapeamento")

    with st.expander(
        "🗺️ Como funciona o Mapeamento Automático",
        expanded=False
    ):
        st.info(
            """
            **Processo automático:**
            1. **Análise das colunas:** O sistema analisa os nomes das colunas
            2. **Correspondência por palavras-chave:** Busca por termos como "empresa", "valor", "data", etc.
            3. **Validação de conteúdo:** Utiliza a amostra disponível para auxiliar a sugestão
            4. **Sugestão de mapeamento:** Propõe o melhor mapeamento encontrado

            **Campos obrigatórios (Distribuidoras padrão):**
            - Empresa/Distribuidora
            - Tipo de cliente
            - Status da conta
            - Situação
            - Nome do cliente
            - Classe do cliente
            - Contrato/Conta
            - Valor principal
            - Data de vencimento

            **Campos obrigatórios (VOLTZ):**
            - Empresa/Distribuidora
            - Nome do cliente
            - Contrato/Conta
            - Valor principal
            - Data de vencimento

            **Campos opcionais mas importantes:**
            - Valor não cedido
            - Valor terceiro
            - Valor CIP
            """
        )

    with st.expander("✏️ Mapeamento Manual", expanded=False):
        st.info(
            """
            **Quando usar:**
            - Mapeamento automático não encontrou correspondência
            - Nomes de colunas não padronizados
            - Estrutura de arquivo diferente do padrão

            **Como funciona:**
            - Selecione a coluna correta para cada campo
            - Opção "-- Não disponível --" para campos inexistentes
            - Validação em tempo real dos tipos de dados
            - Possibilidade de ajustar mapeamentos automáticos

            **Dicas:**
            - Sempre valide o preview após o mapeamento
            - Campos obrigatórios devem ser mapeados
            - Salve cada mapeamento antes de prosseguir
            """
        )


if __name__ == "__main__":
    show()