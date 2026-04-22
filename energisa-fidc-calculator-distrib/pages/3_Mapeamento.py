"""
Página de Mapeamento - FIDC Calculator
Mapeamento automático e manual de campos dos arquivos
"""

import streamlit as st
import pandas as pd
from utils.mapeador_campos import MapeadorCampos

def detectar_voltz(arquivos_processados, mapeador):
    """
    Função unificada para detectar se algum arquivo é VOLTZ
    """
    for nome_arquivo in arquivos_processados.keys():
        if hasattr(mapeador, 'identificar_tipo_distribuidora'):
            if mapeador.identificar_tipo_distribuidora(nome_arquivo) == "VOLTZ":
                return True
        # Fallback - verificar pelo nome
        if 'VOLTZ' in nome_arquivo.upper():
            return True
    return False

def obter_campos_obrigatorios_voltz():
    """
    Retorna lista de campos obrigatórios para VOLTZ
    """
    return ['empresa', 'nome_cliente', 'contrato', 'valor_principal', 'valor_nao_cedido', 'valor_terceiro', 'valor_cip', 'data_vencimento']

def obter_campos_obrigatorios_padrao():
    """
    Retorna lista de campos obrigatórios para distribuidoras padrão
    """
    return ['empresa', 'tipo', 'status', 'situacao', 'nome_cliente', 'classe', 'contrato', 'valor_principal', 'valor_nao_cedido', 'valor_terceiro', 'valor_cip', 'data_vencimento']

def show():
    """Página de Mapeamento de Campos"""
    st.header("🗺️ Mapeamento de Campos")
    
    # Verificar se há arquivos carregados
    if 'df_carregado' not in st.session_state or not st.session_state.df_carregado:
        st.warning("⚠️ Carregue um ou mais arquivos antes de prosseguir para o mapeamento.")
        st.info("💡 Vá para a página de **Carregamento** e faça upload dos arquivos Excel primeiro.")
        return
    
    # Verificar se os parâmetros estão inicializados
    if 'params' not in st.session_state:
        from utils.parametros_correcao import ParametrosCorrecao
        st.session_state.params = ParametrosCorrecao()
    
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
    with col3:
        st.metric("📊 Total de Registros", f"{total_registros:,}")
    
    st.markdown("---")
    
    # Inicializar estado dos mapeamentos
    if 'mapeamentos_finais' not in st.session_state:
        st.session_state.mapeamentos_finais = {}
    
    # Processar cada arquivo individualmente
    for nome_arquivo, info_arquivo in arquivos_processados.items():
        st.subheader(f"📄 Mapeamento: {nome_arquivo}")
        
        df_arquivo = info_arquivo['dataframe']
        
        # Informações do arquivo
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📊 **Registros:** {len(df_arquivo):,}")
        with col2:
            st.info(f"📋 **Colunas:** {len(df_arquivo.columns)}")
        
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
                nome_arquivo,  # Passar nome do arquivo para detecção VOLTZ
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
    if st.button("🚀 Aplicar Todos os Mapeamentos", type="primary", key="aplicar_todos_mapeamentos"):
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
                        nome_arquivo_unico = list(dataframes_padronizados.keys())[0]
                    else:
                        # Múltiplos arquivos - combinar
                        df_final_padronizado = pd.concat(
                            dataframes_padronizados.values(), 
                            ignore_index=True
                        )
                        nome_arquivo_unico = None
                    
                    # ========== VERIFICAÇÃO DE DUPLICATAS ESPECÍFICA PARA VOLTZ ==========
                    st.info("🔍 Verificando duplicatas...")
                    
                    # Usar função unificada para detectar VOLTZ
                    eh_voltz = detectar_voltz(dataframes_padronizados, mapeador)
                    
                    registros_antes = len(df_final_padronizado)
                    
                    if eh_voltz:
                        st.info("⚡ **VOLTZ detectado** - Usando critério específico: nome + data_vencimento + documento")
                        
                        # Verificar se temos as colunas necessárias para VOLTZ
                        colunas_voltz = ['nome_cliente', 'data_vencimento', 'documento']
                        colunas_disponiveis = [col for col in colunas_voltz if col in df_final_padronizado.columns]
                        
                        if len(colunas_disponiveis) >= 2:  # Pelo menos 2 das 3 colunas
                            # Criar chave de duplicata usando as colunas disponíveis
                            colunas_para_duplicata = []
                            
                            if 'nome_cliente' in df_final_padronizado.columns:
                                colunas_para_duplicata.append('nome_cliente')
                                # Limpar e padronizar nome de forma mais rigorosa para VOLTZ
                                df_final_padronizado['nome_cliente_limpo'] = (
                                    df_final_padronizado['nome_cliente']
                                    .astype(str)
                                    .str.strip()
                                    .str.upper()
                                    .str.replace(r'\s+', ' ', regex=True)
                                    .str.replace(r'[^\w\s]', '', regex=True)  # Remove pontuação
                                    .str.replace(r'\b(LTDA|S\.?A\.?|ME|EPP|EIRELI)\b', '', regex=True)  # Remove sufixos empresariais
                                    .str.strip()
                                )
                                colunas_para_duplicata.append('nome_cliente_limpo')
                            
                            if 'data_vencimento' in df_final_padronizado.columns:
                                # Padronizar data de vencimento
                                df_final_padronizado['data_vencimento_limpa'] = pd.to_datetime(
                                    df_final_padronizado['data_vencimento'], 
                                    errors='coerce'
                                ).dt.date
                                colunas_para_duplicata.append('data_vencimento_limpa')
                            
                            if 'documento' in df_final_padronizado.columns:
                                # Limpar e padronizar documento (CPF/CNPJ)
                                df_final_padronizado['documento_limpo'] = (
                                    df_final_padronizado['documento']
                                    .astype(str)
                                    .str.replace(r'[^\d]', '', regex=True)
                                    .str.strip()
                                )
                                colunas_para_duplicata.append('documento_limpo')
                            
                            # Usar apenas as colunas relevantes (remover as auxiliares do subset)
                            subset_final = ['nome_cliente_limpo'] if 'nome_cliente_limpo' in colunas_para_duplicata else []
                            if 'data_vencimento_limpa' in colunas_para_duplicata:
                                subset_final.append('data_vencimento_limpa')
                            if 'documento_limpo' in colunas_para_duplicata:
                                subset_final.append('documento_limpo')
                            
                            if subset_final:
                                # VOLTZ: Não remover duplicatas - manter todos os registros
                                # Apenas limpar colunas auxiliares
                                colunas_auxiliares = ['nome_cliente_limpo', 'data_vencimento_limpa', 'documento_limpo']
                                df_final_padronizado = df_final_padronizado.drop(
                                    columns=[col for col in colunas_auxiliares if col in df_final_padronizado.columns]
                                )
                                
                                st.success("✅ **VOLTZ**: Todos os registros mantidos (duplicatas não removidas)")
                            else:
                                st.warning("⚠️ **VOLTZ**: Colunas necessárias não encontradas para verificação de duplicatas")
                        else:
                            st.warning(f"⚠️ **VOLTZ**: Apenas {len(colunas_disponiveis)} de 3 colunas necessárias encontradas: {colunas_disponiveis}")
                    else:
                        st.info("📊 **Distribuidora padrão** - Usando critério padrão de duplicatas")
                        
                        # Verificação padrão de duplicatas para outras distribuidoras
                        # Usar critério mais abrangente: nome + valor_principal + data_vencimento
                        colunas_padrao = []
                        
                        if 'nome_cliente' in df_final_padronizado.columns:
                            df_final_padronizado['nome_cliente_limpo'] = (
                                df_final_padronizado['nome_cliente']
                                .astype(str).str.strip().str.upper()
                            )
                            colunas_padrao.append('nome_cliente_limpo')
                        
                        if 'valor_principal' in df_final_padronizado.columns:
                            colunas_padrao.append('valor_principal')
                        
                        if 'data_vencimento' in df_final_padronizado.columns:
                            df_final_padronizado['data_vencimento_limpa'] = pd.to_datetime(
                                df_final_padronizado['data_vencimento'], 
                                errors='coerce'
                            ).dt.date
                            colunas_padrao.append('data_vencimento_limpa')
                        
                        if len(colunas_padrao) >= 2:
                            df_final_padronizado = df_final_padronizado.drop_duplicates(
                                subset=colunas_padrao, 
                                keep='first'
                            ).reset_index(drop=True)
                            
                            # Limpar colunas auxiliares
                            colunas_auxiliares = ['nome_cliente_limpo', 'data_vencimento_limpa']
                            df_final_padronizado = df_final_padronizado.drop(
                                columns=[col for col in colunas_auxiliares if col in df_final_padronizado.columns]
                            )
                            
                            registros_depois = len(df_final_padronizado)
                            duplicatas_removidas = registros_antes - registros_depois
                            
                            if duplicatas_removidas > 0:
                                st.warning(f"⚠️ **Padrão**: {duplicatas_removidas:,} duplicatas removidas")
                            else:
                                st.success("✅ **Padrão**: Nenhuma duplicata encontrada")
                        else:
                            st.info("ℹ️ Verificação de duplicatas não aplicada - colunas insuficientes")
                    
                    # Salvar resultado
                    st.session_state.df_padronizado = df_final_padronizado
                    st.session_state.dataframes_individuais = dataframes_padronizados
                    
                    st.success(f"🎯 **Mapeamento e verificação de duplicatas concluídos!** {len(df_final_padronizado):,} registros finais de {len(dataframes_padronizados)} arquivo(s)")
                    
                    if registros_antes != len(df_final_padronizado):
                        duplicatas_removidas = registros_antes - len(df_final_padronizado)
                        st.info(f"📊 Registros processados: {registros_antes:,} → {len(df_final_padronizado):,} (removidas {duplicatas_removidas:,} duplicatas)")
                    
                    # Mostrar preview do resultado final
                    st.subheader("📊 Preview dos Dados Padronizados Consolidados")
                    
                    # Métricas do resultado
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 Total de Registros", f"{len(df_final_padronizado):,}")
                    with col2:
                        st.metric("📁 Arquivos Processados", len(dataframes_padronizados))
                    with col3:
                        # Verificar campos essenciais no resultado final usando função unificada
                        eh_voltz_metricas = detectar_voltz(arquivos_processados, mapeador)
                        
                        if eh_voltz_metricas:
                            # Campos obrigatórios para VOLTZ
                            campos_obrigatorios = obter_campos_obrigatorios_voltz()
                        else:
                            # Campos obrigatórios para outras distribuidoras
                            campos_obrigatorios = obter_campos_obrigatorios_padrao()
                        
                        campos_ok = sum(1 for campo in campos_obrigatorios if campo in df_final_padronizado.columns)
                        st.metric("✅ Campos Obrigatórios", f"{campos_ok}/{len(campos_obrigatorios)}")
                    
                    # Preview da tabela consolidada
                    st.dataframe(df_final_padronizado.head(10), use_container_width=True)
                    
                    # Validação final considerando VOLTZ
                    problemas = []
                    
                    # Usar função unificada para detectar VOLTZ
                    tem_voltz = detectar_voltz(arquivos_processados, mapeador)
                    
                    # Definir campos obrigatórios baseado no tipo
                    if tem_voltz:
                        campos_obrigatorios_validacao = obter_campos_obrigatorios_voltz()
                    else:
                        campos_obrigatorios_validacao = obter_campos_obrigatorios_padrao()
                    
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
                        
                        # Mostrar próximo passo
                        st.info("✨ **Próximo passo:** Vá para a página de **Correção** para calcular os valores corrigidos.")
                else:
                    st.error("❌ Nenhum arquivo foi processado com sucesso. Verifique os mapeamentos.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao aplicar mapeamentos: {str(e)}")
    
    # Status do mapeamento geral
    if 'df_padronizado' in st.session_state and not st.session_state.df_padronizado.empty:
        st.markdown("---")
        st.success(f"✅ **Mapeamento concluído:** {len(st.session_state.df_padronizado):,} registros padronizados de {len(st.session_state.get('dataframes_individuais', {})):,} arquivo(s)")
        
        # Resumo dos campos mapeados
        st.subheader("📋 Resumo dos Campos Mapeados")
        
        df_padronizado = st.session_state.df_padronizado
        campos_mapeados = list(df_padronizado.columns)
        
        # Detectar se é VOLTZ para ajustar campos principais usando função unificada
        eh_voltz_resumo = detectar_voltz(st.session_state.df_carregado, mapeador)
        
        # Agrupar campos por categoria
        if eh_voltz_resumo:
            # Para VOLTZ: não incluir tipo, status, situacao, classe
            campos_principais = [col for col in campos_mapeados if col in ['empresa', 'nome_cliente', 'contrato']]
        else:
            # Para outras distribuidoras: incluir todos
            campos_principais = [col for col in campos_mapeados if col in ['empresa', 'tipo', 'status', 'situacao', 'nome_cliente', 'classe', 'contrato']]
        
        campos_valores = [col for col in campos_mapeados if 'valor' in col.lower()]
        campos_datas = [col for col in campos_mapeados if 'data' in col.lower()]
        campos_outros = [col for col in campos_mapeados if col not in campos_principais + campos_valores + campos_datas]
        
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
            for campo in campos_outros[:5]:  # Limitar para não poluir
                st.write(f"• {campo}")
            if len(campos_outros) > 5:
                st.caption(f"... e mais {len(campos_outros) - 5} campos")
    
    # Informações sobre o mapeamento
    st.markdown("---")
    st.subheader("ℹ️ Informações sobre Mapeamento")
    
    with st.expander("🗺️ Como funciona o Mapeamento Automático", expanded=False):
        st.info("""
        **Processo automático:**
        1. **Análise das colunas:** O sistema analisa os nomes das colunas
        2. **Correspondência por palavras-chave:** Busca por termos como "empresa", "valor", "data", etc.
        3. **Validação de conteúdo:** Verifica se o tipo de dados corresponde ao esperado
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
        """)
    
    with st.expander("✏️ Mapeamento Manual", expanded=False):
        st.info("""
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
        """)

if __name__ == "__main__":
    show()
