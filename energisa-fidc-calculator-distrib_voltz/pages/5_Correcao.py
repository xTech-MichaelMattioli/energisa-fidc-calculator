"""
Página de Correção - FIDC Calculator
Cálculo de aging, correção monetária e valor justo
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
import math
from utils.calculador_aging import CalculadorAging
from utils.calculador_correcao import CalculadorCorrecao

import requests
from dateutil.relativedelta import relativedelta
import numpy as np

# Funções auxiliares para divisão de arquivos CSV
def calcular_numero_arquivos(total_linhas, limite_por_arquivo=700000):
    """
    Calcula quantos arquivos serão necessários baseado no limite de linhas por arquivo
    
    Args:
        total_linhas (int): Total de linhas no DataFrame
        limite_por_arquivo (int): Limite máximo de linhas por arquivo (padrão: 700.000)
    
    Returns:
        int: Número de arquivos necessários
    """
    if total_linhas <= limite_por_arquivo:
        return 1
    return math.ceil(total_linhas / limite_por_arquivo)

def dividir_dataframe_em_chunks(df, limite_por_arquivo=700000):
    """
    Divide um DataFrame em chunks de no máximo limite_por_arquivo linhas cada
    
    Args:
        df (pd.DataFrame): DataFrame a ser dividido
        limite_por_arquivo (int): Limite máximo de linhas por arquivo (padrão: 700.000)
    
    Returns:
        list: Lista de DataFrames divididos
    """
    if len(df) <= limite_por_arquivo:
        return [df]
    
    chunks = []
    total_linhas = len(df)
    
    for i in range(0, total_linhas, limite_por_arquivo):
        chunk = df.iloc[i:i + limite_por_arquivo].copy()
        chunks.append(chunk)
    
    return chunks

def gerar_nomes_arquivos_csv(nome_base, numero_arquivos, timestamp):
    """
    Gera lista de nomes de arquivos CSV com numeração sequencial
    
    Args:
        nome_base (str): Nome base do arquivo (ex: "FIDC_Dados_Finais")
        numero_arquivos (int): Número de arquivos que serão gerados
        timestamp (str): Timestamp para adicionar ao nome
    
    Returns:
        list: Lista de nomes de arquivos
    """
    if numero_arquivos == 1:
        return [f"{nome_base}_{timestamp}.csv"]
    
    nomes = []
    for i in range(1, numero_arquivos + 1):
        nome = f"{nome_base}_{timestamp}_parte_{i}.csv"
        nomes.append(nome)
    
    return nomes

class CalculadorIndicesEconomicos:
    """
    Classe para cálculo de índices econômicos a partir de arquivo Excel
    """
    
    def __init__(self):
        self.df_indices = None
        self.ipca_12m_real = None
        self.data_base = None
    
    def carregar_indices_do_excel(self, arquivo_excel):
        """
        Carrega dados de IGP-M/IPCA do arquivo Excel
        Estrutura esperada: Coluna C (Ano), Coluna D (Mês) e Coluna F (Índice IGP-M)
        """
        try:
            import pandas as pd
            import streamlit as st
            import numpy as np
            from datetime import datetime
            
            print("🔄 Carregando índices do arquivo Excel...")
            
            # Ler o arquivo Excel completo primeiro para analisar
            try:
                df_completo = pd.read_excel(arquivo_excel)
                print(f"📊 Arquivo carregado com {df_completo.shape[0]} linhas e {df_completo.shape[1]} colunas")
                
                # Verificar se tem pelo menos 6 colunas (A até F)
                if df_completo.shape[1] < 6:
                    raise ValueError(f"Arquivo tem apenas {df_completo.shape[1]} colunas, mas precisa de pelo menos 6 (A-F)")
                
                # Extrair colunas C (2), D (3) e F (5) - Ano, Mês e Índice IGP-M
                df = df_completo.iloc[:, [2, 3, 5]].copy()
                
            except Exception as e:
                print(f"❌ Erro ao ler arquivo Excel: {e}")
                raise e
            
            # Renomear colunas para padronização
            df.columns = ['ano', 'mes', 'indice']
            print(f"📊 Dados extraídos - Coluna C (ano), Coluna D (mês) e Coluna F (índice)")
            
            # Limpar dados nulos
            df_original_len = len(df)
            df = df.dropna()
            print(f"📊 Removidas {df_original_len - len(df)} linhas com valores nulos")
            
            # Processar colunas de ano e mês
            print("🔄 Processando colunas de ano e mês...")
            
            # Converter ano e mês para inteiros
            try:
                print(f"📊 Antes da conversão - Tipo ano: {df['ano'].dtype}, Tipo mês: {df['mes'].dtype}")
                print(f"📊 Exemplos ano: {df['ano'].head(3).tolist()}")
                print(f"📊 Exemplos mês: {df['mes'].head(3).tolist()}")
                
                df['ano'] = pd.to_numeric(df['ano'], errors='coerce').astype('Int64')
                df['mes'] = pd.to_numeric(df['mes'], errors='coerce').astype('Int64')
                
                print(f"📊 Após conversão - Valores únicos ano: {sorted(df['ano'].dropna().unique())[:10]}")
                print(f"📊 Após conversão - Valores únicos mês: {sorted(df['mes'].dropna().unique())}")
                
            except Exception as conv_error:
                print(f"⚠️ Erro ao converter ano/mês para números: {conv_error}")
                # Tentar conversão manual
                try:
                    df['ano'] = df['ano'].astype(str).str.extract(r'(\d{4})')[0].astype(float).astype('Int64')
                    df['mes'] = df['mes'].astype(str).str.extract(r'(\d{1,2})')[0].astype(float).astype('Int64')
                    print("✅ Conversão manual bem-sucedida")
                except:
                    raise ValueError("Não foi possível converter ano (coluna C) e mês (coluna D) para números")
            
            # Remover linhas com ano/mês inválidos
            df_limpo = df.dropna(subset=['ano', 'mes']).copy()
            
            # Validar valores de ano e mês
            mask_ano_valido = (df_limpo['ano'] >= 1990) & (df_limpo['ano'] <= 2030)
            mask_mes_valido = (df_limpo['mes'] >= 1) & (df_limpo['mes'] <= 12)
            
            df_filtrado = df_limpo[mask_ano_valido & mask_mes_valido].copy()
            
            if len(df_filtrado) == 0:
                raise ValueError("Nenhuma data válida encontrada nas colunas C (ano) e D (mês)")
            
            print(f"📊 {len(df_filtrado)} registros com ano/mês válidos")
            
            # Criar coluna de data a partir do ano e mês
            try:
                # Criar data no primeiro dia do mês usando uma abordagem mais robusta
                df_filtrado['data'] = pd.to_datetime(
                    df_filtrado['ano'].astype(str) + '-' + df_filtrado['mes'].astype(str).str.zfill(2) + '-01',
                    format='%Y-%m-%d'
                )
            except Exception as e:
                print(f"❌ Erro ao criar datas (método 1): {e}")
                # Método alternativo
                try:
                    datas_list = []
                    for idx, row in df_filtrado.iterrows():
                        ano = int(row['ano'])
                        mes = int(row['mes'])
                        data = datetime(ano, mes, 1)
                        datas_list.append(data)
                    df_filtrado['data'] = datas_list
                except Exception as e2:
                    print(f"❌ Erro ao criar datas (método 2): {e2}")
                    raise ValueError("Erro ao combinar ano e mês em datas válidas")
            
            print(f"📊 {len(df_filtrado)} datas criadas com sucesso")
            
            # Processar coluna de índice
            print("🔄 Processando coluna de índice...")
            
            # Converter índice para float, tratando vírgulas decimais brasileiras
            if df_filtrado['indice'].dtype == 'object':
                # Se for texto, pode ter vírgulas como separador decimal (formato brasileiro)
                df_filtrado['indice'] = df_filtrado['indice'].astype(str).str.replace(',', '.')
            
            # Converter para numérico
            df_filtrado['indice'] = pd.to_numeric(df_filtrado['indice'], errors='coerce')
            
            # Remover linhas com índices inválidos
            df_final = df_filtrado.dropna(subset=['indice']).copy()
            
            # Verificar se temos valores válidos após conversão
            if len(df_final) == 0:
                raise ValueError("Nenhum índice válido encontrado após conversão numérica")
            
            print(f"📊 Conversão de índices: {len(df_filtrado)} → {len(df_final)} registros válidos")
            print(f"📊 Exemplo de índices convertidos: {df_final['indice'].head(3).tolist()}")
            
            # Manter apenas colunas necessárias
            df_final = df_final[['data', 'indice']].copy()
            
            # Ordenar por data
            df_final = df_final.sort_values('data').reset_index(drop=True)
            
            # Validar se temos dados válidos
            if len(df_final) == 0:
                raise ValueError("Nenhum registro válido encontrado após processamento")
            
            # Verificar se os valores de índice fazem sentido (IGP-M base 100 em ago/1994)
            indice_min = df_final['indice'].min()
            indice_max = df_final['indice'].max()
            
            if indice_min < 50 or indice_max > 10000:
                print(f"⚠️ Atenção: Valores de índice fora do esperado (min: {indice_min:.2f}, max: {indice_max:.2f})")
            
            # Verificar continuidade temporal
            periodo_min = df_final['data'].min()
            periodo_max = df_final['data'].max()
            meses_esperados = ((periodo_max.year - periodo_min.year) * 12) + (periodo_max.month - periodo_min.month) + 1
            meses_encontrados = len(df_final)
            
            if meses_encontrados < (meses_esperados * 0.8):  # Pelo menos 80% dos meses esperados
                print(f"⚠️ Atenção: Possível descontinuidade nos dados ({meses_encontrados} de {meses_esperados} meses esperados)")
            
            # Salvar resultado
            self.df_indices = df_final
            
            print(f"✅ {len(df_final)} registros de índices carregados com sucesso!")
            print(f"📊 Período: {df_final['data'].min().strftime('%Y-%m')} a {df_final['data'].max().strftime('%Y-%m')}")
            print(f"📊 Índice inicial: {df_final['indice'].iloc[0]:.2f}")
            print(f"📊 Índice final: {df_final['indice'].iloc[-1]:.2f}")
            print(f"📊 Média do índice: {df_final['indice'].mean():.2f}")
            
            return self.df_indices
            
        except Exception as e:
            error_msg = f"❌ Erro ao carregar índices do Excel: {str(e)}"
            print(error_msg)
            if 'st' in locals():
                st.error(f"Erro ao processar arquivo Excel: {str(e)}")
            return None
    
    
    def buscar_indice_para_data(self, data_busca):
        """
        Busca o índice para uma data específica
        """
        if self.df_indices is None or self.df_indices.empty:
            print("⚠️ Dados de índices não carregados")
            return None
        
        try:
            # Converter data para período mensal para busca
            periodo_busca = pd.Period(data_busca, freq='M')
            
            # Adicionar coluna de período ao dataframe se não existir
            if 'periodo' not in self.df_indices.columns:
                self.df_indices['periodo'] = self.df_indices['data'].dt.to_period('M')
            
            # Buscar índice exato para o período
            resultado = self.df_indices[self.df_indices['periodo'] == periodo_busca]
            
            if not resultado.empty:
                return resultado.iloc[0]['indice']
            else:
                # Se não encontrar exato, buscar o mais próximo anterior
                indices_anteriores = self.df_indices[self.df_indices['periodo'] <= periodo_busca]
                if not indices_anteriores.empty:
                    return indices_anteriores.iloc[-1]['indice']
                else:
                    print(f"⚠️ Não foi possível encontrar índice para {data_busca.strftime('%Y-%m')}")
                    return None
                    
        except Exception as e:
            print(f"❌ Erro ao buscar índice para {data_busca}: {e}")
            return None
    
    def calcular_fator_correcao(self, data_vencimento, data_base):
        """
        Calcula o fator de correção entre duas datas usando os índices carregados
        """
        try:
            indice_vencimento = self.buscar_indice_para_data(data_vencimento)
            indice_base = self.buscar_indice_para_data(data_base)
            
            if indice_vencimento is None or indice_base is None:
                print(f"⚠️ Não foi possível encontrar índices para calcular correção")
                return 1.0  # Retorna fator neutro
            
            # Fator de correção = índice_base / índice_vencimento
            fator = indice_base / indice_vencimento
            
            return fator
            
        except Exception as e:
            print(f"❌ Erro ao calcular fator de correção: {e}")
            return 1.0

class CalculadorValorJusto:
    """
    Classe para cálculo do valor justo usando índices do Excel
    """
    
    def __init__(self):
        self.calculador_indices = CalculadorIndicesEconomicos()
        
    def carregar_dados_indices(self, arquivo_excel):
        """
        Carrega dados de índices do arquivo Excel
        """
        return self.calculador_indices.carregar_indices_do_excel(arquivo_excel)
    
    def obter_indice_para_data(self, data_busca):
        """
        Obtém índice para uma data específica
        """
        return self.calculador_indices.buscar_indice_para_data(data_busca)
    
    def calcular_fator_correcao_indices(self, data_vencimento, data_base):
        """
        Calcula fator de correção usando os índices carregados
        """
        return self.calculador_indices.calcular_fator_correcao(data_vencimento, data_base)
    
    def calcular_valor_justo_com_di_pre(self, df_corrigido, df_di_pre, coluna_valor_corrigido='valor_corrigido', data_base=None):
        """
        Calcula valor justo aplicando taxas DI-PRE com progressão exponencial sobre valor corrigido
        """
        if data_base is None:
            data_base = datetime.now()
        
        df_resultado = df_corrigido.copy()
        
        # Verificar se temos coluna prazo_recebimento, senão usar 6 meses como padrão
        if 'prazo_recebimento' not in df_resultado.columns:
            df_resultado['prazo_recebimento'] = 6
        
        # Inicializar colunas para DI-PRE
        df_resultado['taxa_di_pre'] = 0.0
        df_resultado['fator_exponencial_di_pre'] = 1.0
        
        # Para cada linha do df_resultado, buscar a taxa DI-PRE correspondente
        for idx, row in df_resultado.iterrows():
            meses_recebimento = row['prazo_recebimento']
            
            # Buscar no df_di_pre a linha onde meses_futuros é igual ao prazo_recebimento
            linha_di_pre = df_di_pre[df_di_pre['meses_futuros'] == meses_recebimento]
            
            if not linha_di_pre.empty:
                # Pegar a primeira linha correspondente e usar a coluna '252' (taxa para 252 dias úteis)
                taxa_di_pre = linha_di_pre.iloc[0]['252'] / 100  # Converter de % para decimal
                df_resultado.at[idx, 'taxa_di_pre'] = taxa_di_pre
                
                # Calcular fator exponencial com DI-PRE: (1 + taxa_di_pre)^(meses_recebimento/12)
                fator_exponencial = (1 + taxa_di_pre) ** (meses_recebimento / 12)
                df_resultado.at[idx, 'fator_exponencial_di_pre'] = fator_exponencial
            else:
                # Se não encontrar correspondência, usar taxa padrão de 0.5% ao mês
                taxa_padrao = 0.005
                df_resultado.at[idx, 'taxa_di_pre'] = taxa_padrao
                fator_exponencial = (1 + taxa_padrao) ** (meses_recebimento / 12)
                df_resultado.at[idx, 'fator_exponencial_di_pre'] = fator_exponencial
        
        # Meses até recebimento (prazo_recebimento)
        if 'prazo_recebimento' in df_resultado.columns:
            df_resultado['meses_ate_recebimento'] = df_resultado['prazo_recebimento']
        else:
            # Fallback: usar 6 meses como padrão se não tiver prazo_recebimento
            df_resultado['meses_ate_recebimento'] = 6

        # Mora: 1% ao mês multiplicado pelo prazo de recebimento em meses
        taxa_mora_mensal = 0.01  # 1% ao mês
        df_resultado['mora'] = df_resultado['meses_ate_recebimento'] * taxa_mora_mensal
        
        # DEBUG: Mostrar estatísticas da mora no valor justo
        print("\n=== DEBUG MORA NO VALOR JUSTO ===")
        print(f"Registros processados: {len(df_resultado)}")
        print(f"Mora mínima: {df_resultado['mora'].min():.4f}")
        print(f"Mora máxima: {df_resultado['mora'].max():.4f}")
        print(f"Mora média: {df_resultado['mora'].mean():.4f}")
        print(f"Registros com mora > 0: {(df_resultado['mora'] > 0).sum()}")
        print("=== FIM DEBUG MORA NO VALOR JUSTO ===\n")
        
        # Verificar se temos coluna de taxa_recuperacao
        if 'taxa_recuperacao' in df_resultado.columns:            
            # Fórmula com DI-PRE: valor_justo = valor_corrigido * taxa_recuperacao * (fator_exponencial_di_pre + mora)
            df_resultado['valor_justo'] = df_resultado[coluna_valor_corrigido] * df_resultado['taxa_recuperacao'] * (df_resultado['fator_exponencial_di_pre'] + df_resultado['mora'])
        else:
            # Fallback sem taxa de recuperação
            df_resultado['valor_justo'] = df_resultado[coluna_valor_corrigido] * (df_resultado['fator_exponencial_di_pre'] + df_resultado['mora'])
        
        return df_resultado
    
    def obter_estatisticas_di_pre(self, df_di_pre):
        """
        Retorna estatísticas do DI-PRE calculado incluindo informações sobre progressão exponencial
        """
        if df_di_pre.empty:
            return None
        
        # Calcular estatísticas básicas das taxas DI-PRE (coluna '252')
        taxa_media = df_di_pre['252'].mean()
        taxa_min = df_di_pre['252'].min()
        taxa_max = df_di_pre['252'].max()
        
        return {
            'taxa_media_percentual': taxa_media,
            'taxa_min_percentual': taxa_min,
            'taxa_max_percentual': taxa_max,
            'total_registros_di_pre': len(df_di_pre),
            'meses_disponiveis': sorted(df_di_pre['meses_futuros'].unique().tolist()),
            'formula_exponencial': 'An = (1 + taxa_di_pre)^(prazo_recebimento/12)',
            'descricao_prazo': 'prazo_recebimento em meses'
        }

def show():
    """Página de Correção Monetária e Valor Justo"""
    st.header("💰 CORREÇÃO MONETÁRIA e VALOR JUSTO")
    
    # Inicializar flags de controle
    if 'calculo_solicitado' not in st.session_state:
        st.session_state.calculo_solicitado = False
    if 'taxa_recuperacao_carregada' not in st.session_state:
        st.session_state.taxa_recuperacao_carregada = False
    if 'cdi_carregado' not in st.session_state:
        st.session_state.cdi_carregado = False
    if 'indices_carregados' not in st.session_state:
        st.session_state.indices_carregados = False
    
    # Verificar se temos dados padronizados
    if 'df_padronizado' not in st.session_state or st.session_state.df_padronizado.empty:
        st.warning("⚠️ Realize o mapeamento de campos antes de calcular a correção monetária.")
        st.info("💡 Vá para a página de **Mapeamento** e complete o processo de mapeamento primeiro.")
        return
    
    # Verificar se os parâmetros estão inicializados
    if 'params' not in st.session_state:
        from utils.parametros_correcao import ParametrosCorrecao
        st.session_state.params = ParametrosCorrecao()
    
    df_padronizado = st.session_state.df_padronizado
    calc_aging = CalculadorAging(st.session_state.params)
    calc_correcao = CalculadorCorrecao(st.session_state.params)
    
    # ETAPA 0: CARREGAMENTO DOS ÍNDICES IGP-M/IPCA (OBRIGATÓRIO)
    st.subheader("📊 0️⃣ Carregar Índices IGP-M/IPCA")
    
    # Verificar se temos dados de índices carregados
    tem_indices = 'df_indices_economicos' in st.session_state and not st.session_state.df_indices_economicos.empty
    
    if not tem_indices:
        st.warning("⚠️ **PASSO 0:** Faça o upload do arquivo de índices IGP-M/IPCA para continuar.")
        
        with st.expander("📤 Upload dos Índices IGP-M/IPCA", expanded=True):
            st.info("""
            **📋 Instruções:** 
            
            Faça o upload do arquivo Excel com os índices econômicos. O arquivo deve conter:
            - **Coluna A**: Data no formato AAAA.MM (ex: 2022.01)
            - **Coluna F**: Valores dos índices IGP-M ou IPCA
            - Histórico completo dos índices para correção monetária
            
            **Exemplo de estrutura esperada:**
            ```
            2021.12    543.21
            2022.01    548.65  
            2022.02    552.34
            ```
            """)
            
            # Upload do arquivo
            uploaded_file_indices = st.file_uploader(
                "📤 Selecione o arquivo de Índices IGP-M/IPCA",
                type=['xlsx', 'xls'],
                help="Arquivo Excel com índices econômicos (colunas A e F)",
                key="upload_indices_modulo4"
            )
            
            if uploaded_file_indices is not None:
                try:
                    with st.spinner("🔄 Processando arquivo de índices..."):
                        # Criar instância do calculador
                        calc_valor_justo = CalculadorValorJusto()
                        
                        # Carregar dados do Excel
                        df_indices = calc_valor_justo.carregar_dados_indices(uploaded_file_indices)
                        
                        if df_indices is not None and not df_indices.empty:
                            st.session_state.df_indices_economicos = df_indices
                            st.session_state.calculador_valor_justo = calc_valor_justo
                            st.session_state.indices_carregados = True
                            
                            st.success(f"✅ **{len(df_indices)} registros de índices carregados com sucesso!**")
                            
                            # Mostrar estatísticas dos dados carregados
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📊 Total de Registros", f"{len(df_indices):,}")
                            with col2:
                                periodo_min = df_indices['data'].min().strftime('%Y-%m')
                                periodo_max = df_indices['data'].max().strftime('%Y-%m')
                                st.metric("📅 Período", f"{periodo_min} a {periodo_max}")
                            with col3:
                                indice_atual = df_indices['indice'].iloc[-1]
                                st.metric("📈 Último Índice", f"{indice_atual:.2f}")
                            
                            # Mostrar preview dos dados (fora do expander)
                            st.write("**📋 Preview dos Índices Carregados:**")
                            st.dataframe(df_indices.head(10), use_container_width=True)
                            
                            st.rerun()
                        else:
                            st.error("❌ Não foi possível processar o arquivo. Verifique a estrutura (colunas A e F).")
                            
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {str(e)}")
                    st.error("Verifique se o arquivo possui as colunas A (data) e F (índice) com dados válidos.")

        # Se não tem índices, parar aqui
        return
    else:
        st.success("✅ **Índices IGP-M/IPCA carregados**")
        registros_indices = len(st.session_state.df_indices_economicos)
        periodo_min = st.session_state.df_indices_economicos['data'].min().strftime('%Y-%m')
        periodo_max = st.session_state.df_indices_economicos['data'].max().strftime('%Y-%m')
        st.info(f"📊 {registros_indices} registro(s) de índices disponível(eis) ({periodo_min} a {periodo_max})")
        
        if st.button("🔄 Recarregar Índices"):
            st.session_state.indices_carregados = False
            st.session_state.taxa_recuperacao_carregada = False
            st.session_state.cdi_carregado = False
            st.session_state.calculo_solicitado = False
            if 'df_indices_economicos' in st.session_state:
                del st.session_state.df_indices_economicos
            if 'calculador_valor_justo' in st.session_state:
                del st.session_state.calculador_valor_justo
            st.rerun()

        # Mostrar o head dos dados num expander
        with st.expander("📊 Preview dos Índices Carregados", expanded=False):
            if 'df_indices_economicos' in st.session_state:
                st.dataframe(st.session_state.df_indices_economicos.head(10), use_container_width=True)

    st.markdown("---")
    
    # ETAPA 1: CARREGAMENTO DA TAXA DE RECUPERAÇÃO (OBRIGATÓRIO)
    st.subheader("📈 1️⃣ Configurar Taxa de Recuperação")
    
    # Verificar se temos dados de taxa de recuperação
    tem_taxa_recuperacao = 'df_taxa_recuperacao' in st.session_state and not st.session_state.df_taxa_recuperacao.empty
    
    if not tem_taxa_recuperacao:
        st.warning("⚠️ **PASSO 1:** Faça o upload do arquivo de taxa de recuperação para continuar.")
        
        with st.expander("📤 Upload da Taxa de Recuperação", expanded=True):
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
                        # [Código de processamento mantido igual]
                        df_taxa_upload = pd.read_excel(uploaded_file_taxa, sheet_name="Input", header=None)
                        
                        tipos = ["Privado", "Público", "Hospital"]
                        aging_labels = ["A vencer", "Primeiro ano", "Segundo ano", "Terceiro ano", "Quarto ano", "Quinto ano", "Demais anos"]

                        empresa = None
                        dados_taxa = []
                        
                        for i in range(len(df_taxa_upload)):
                            row = df_taxa_upload.iloc[i]

                            for j in range(len(row) - 1):
                                if str(row[j]).strip().lower() == "x":
                                    empresa = str(row[j + 1]).strip()

                            if not empresa:
                                continue

                            for offset, tipo in zip([1, 5, 9], tipos):
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
                        
                        if dados_taxa:
                            df_taxa_recuperacao_nova = pd.DataFrame(dados_taxa)
                            st.session_state.df_taxa_recuperacao = df_taxa_recuperacao_nova
                            st.session_state.taxa_recuperacao_carregada = True
                            
                            # Resetar flags subsequentes
                            st.session_state.cdi_carregado = False
                            st.session_state.calculo_solicitado = False
                            if 'df_final' in st.session_state:
                                del st.session_state.df_final
                            if 'df_com_aging' in st.session_state:
                                del st.session_state.df_com_aging
                            
                            st.rerun()
                        else:
                            st.error("❌ Nenhum dado válido encontrado no arquivo. Verifique a estrutura do arquivo.")
                            
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {str(e)}")
                    st.error("Verifique se o arquivo possui uma aba 'Input' e se a estrutura está correta.")

        # Se não tem taxa, parar aqui
        return
    else:
        st.success("✅ **Taxa de recuperação carregada**")
        empresas = st.session_state.df_taxa_recuperacao['Empresa'].nunique()
        registros = len(st.session_state.df_taxa_recuperacao)
        st.info(f"🏢 {empresas} empresa(s) configurada(s) com {registros} registro(s) de taxa")
        
        if st.button("🔄 Recarregar Taxa de Recuperação"):
            st.session_state.taxa_recuperacao_carregada = False
            st.session_state.cdi_carregado = False
            st.session_state.calculo_solicitado = False
            if 'df_taxa_recuperacao' in st.session_state:
                del st.session_state.df_taxa_recuperacao
            st.rerun()

        # Mostrar o head dos dados num expander
        with st.expander("📊 Preview dos Dados de Taxa de Recuperação", expanded=False):
            if 'df_taxa_recuperacao' in st.session_state:
                st.dataframe(st.session_state.df_taxa_recuperacao.head(10), use_container_width=True)

    st.markdown("---")
    
    # ETAPA 2: CARREGAMENTO DO ARQUIVO CDI (OBRIGATÓRIO)
    st.subheader("📈 2️⃣ Carregar Dados CDI/DI-PRE")
    
    # Verificar se temos dados CDI carregados
    tem_cdi = 'df_di_pre' in st.session_state and not st.session_state.df_di_pre.empty
    
    if not tem_cdi:
        st.warning("⚠️ **PASSO 2:** Faça o upload do arquivo CDI/DI-PRE para continuar.")
        
        with st.expander("📤 Upload do Arquivo CDI/DI-PRE", expanded=True):
            st.info("""
            **📋 Instruções:** 
            
            Faça o upload do arquivo Excel (.xls ou .xlsx) com os dados de CDI/DI-PRE da BMF.
            Este arquivo contém as taxas de juros utilizadas para correção monetária.
            
            **Formato esperado:** Arquivo HTML/Excel da BMF com dados de DI x pré
            """)
            st.markdown(
                "🔗 Fonte oficial DI-PRE (B3): https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/txref1.asp"
            )
            
            # Upload do arquivo CDI
            uploaded_file_cdi = st.file_uploader(
                "📤 Selecione o arquivo CDI/DI-PRE",
                type=['xlsx', 'xls'],
                help="Arquivo Excel com dados de CDI/DI-PRE da BMF",
                key="upload_cdi_modulo4"
            )
            
            if uploaded_file_cdi is not None:
                try:
                    with st.spinner("🔄 Processando arquivo CDI/DI-PRE..."):
                        # Importar e usar o processador CDI
                        from utils.processador_di_pre import ProcessadorDIPre
                        
                        processador = ProcessadorDIPre()
                        df_cdi_processado = processador.processar_arquivo_bmf(uploaded_file_cdi)
                        
                        if df_cdi_processado is not None and not df_cdi_processado.empty:
                            st.session_state.df_di_pre = df_cdi_processado
                            st.session_state.cdi_carregado = True
                            
                            # Resetar flag de cálculo
                            st.session_state.calculo_solicitado = False
                            if 'df_final' in st.session_state:
                                del st.session_state.df_final
                            if 'df_com_aging' in st.session_state:
                                del st.session_state.df_com_aging

                            # Tratar dados df_di_pre - transformar dias em meses, usando float
                            # pegar o ano da data_arquivo
                            st.session_state.df_di_pre['meses_futuros'] = (st.session_state.df_di_pre['dias_corridos'] / 30.44)
                            
                            #Filtrar dados para mês sendo o mais próximo do numero inteiro seguindo a sequência 1,2,3,4,5,6...

                            # Lista para armazenar os índices das linhas que serão selecionadas.
                            indices_para_manter = []

                            # Determina o valor máximo de meses para saber até onde iterar.
                            # O `+ 2` garante que o loop inclua o último mês.
                            limite_mes = int(st.session_state.df_di_pre['meses_futuros'].max()) + 2

                            # Itera de 1 até o limite de meses.
                            for i in range(1, limite_mes):
                                # Encontra o índice da linha que tem o valor 'mes' mais próximo do inteiro 'i'.
                                indice_mais_proximo = (st.session_state.df_di_pre['meses_futuros'] - i).abs().idxmin()
                                indices_para_manter.append(indice_mais_proximo)

                            # Filtra o DataFrame original usando os índices encontrados e remove duplicatas.
                            df_filtrado = st.session_state.df_di_pre.loc[indices_para_manter].drop_duplicates()

                            # Ou salvar em uma nova variável de estado para usar depois:
                            st.session_state.df_di_pre = df_filtrado

                            # arredonda o mes
                            st.session_state.df_di_pre['meses_futuros'] = st.session_state.df_di_pre['meses_futuros'].round().astype(int)

                            # 1. Garanta que a coluna de data esteja no formato datetime do pandas.
                            st.session_state.df_di_pre['data_arquivo'] = pd.to_datetime(st.session_state.df_di_pre['data_arquivo'], format='%Y-%m-%d')

                            # 2. Calcule a data futura somando os dias corridos.
                            #    A função pd.to_timedelta converte o número de dias para um formato que pode ser somado a datas.
                            data_futura = st.session_state.df_di_pre['data_arquivo'] + pd.to_timedelta(st.session_state.df_di_pre['dias_corridos'], unit='d')

                            # 3. Crie as novas colunas 'ano_atual' e 'mes_atual' a partir da data futura.
                            st.session_state.df_di_pre['ano_atual'] = data_futura.dt.year
                            st.session_state.df_di_pre['mes_atual'] = data_futura.dt.month

                            st.rerun()  # Recarregar a página para atualizar o estado
                        else:
                            st.error("❌ Não foi possível processar o arquivo CDI. Verifique o formato do arquivo.")
                            
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo CDI: {str(e)}")
                    st.error("Verifique se o arquivo está no formato correto da BMF.")

        # Se não tem CDI, parar aqui
        return
    else:
        st.success("✅ **Dados CDI/DI-PRE carregados**")
        registros_cdi = len(st.session_state.df_di_pre)
        st.info(f"� {registros_cdi} registro(s) de CDI/DI-PRE disponível(eis)")
        
        # Mostrar botão para recarregar se necessário
        if st.button("🔄 Recarregar Dados CDI"):
            st.session_state.cdi_carregado = False
            st.session_state.calculo_solicitado = False
            if 'df_di_pre' in st.session_state:
                del st.session_state.df_di_pre
            st.rerun()  # Recarregar a página para atualizar o estado

        # Mostrar o head dos dados num expander
        if 'df_di_pre' in st.session_state:
            with st.expander("📊 Preview dos Dados CDI/DI-PRE", expanded=False):
                st.dataframe(st.session_state.df_di_pre.head(10), use_container_width=True)

    st.markdown("---")
    
    # ETAPA 3: INFORMAÇÕES E CÁLCULO
    st.subheader("📊 3️⃣ Executar Cálculo")
    
    # Seção de informações antes do cálculo
    st.write("**Informações do Processamento:**")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("📊 Registros a Processar", f"{len(df_padronizado):,}")
    
    with col2:
        empresas_dados = df_padronizado['empresa'].nunique() if 'empresa' in df_padronizado.columns else 0
        st.metric("🏢 Empresas nos Dados", empresas_dados)
    
    with col3:
        registros_indices = len(st.session_state.df_indices_economicos)
        st.metric("📈 Registros Índices", registros_indices)
    
    with col4:
        empresas_taxa = st.session_state.df_taxa_recuperacao['Empresa'].nunique()
        st.metric("🏢 Empresas com Taxa", empresas_taxa)
    
    with col5:
        registros_taxa = len(st.session_state.df_taxa_recuperacao)
        st.metric("📈 Registros de Taxa", registros_taxa)
    
    with col6:
        registros_cdi = len(st.session_state.df_di_pre)
        st.metric("📊 Registros CDI", registros_cdi)
    
    # Verificar se todos os arquivos necessários estão carregados
    tem_todos_arquivos = (
        tem_indices and 
        tem_taxa_recuperacao and 
        tem_cdi
    )
    
    # Botão para calcular correção (SÓ APARECE SE TIVER TODOS OS ARQUIVOS)
    st.markdown("---")
    if tem_todos_arquivos:
        st.write("**✅ Todos os arquivos carregados! Agora você pode executar o cálculo:**")
        calculo_executado = st.button("💰 Calcular Correção Monetária Completa", type="primary", use_container_width=True)
    else:
        arquivos_faltantes = []
        if not tem_indices:
            arquivos_faltantes.append("📊 Índices IGP-M/IPCA")
        if not tem_taxa_recuperacao:
            arquivos_faltantes.append("📈 Taxa de Recuperação")
        if not tem_cdi:
            arquivos_faltantes.append("📊 Dados CDI/DI-PRE")
        
        st.warning(f"⚠️ **Arquivos pendentes:** {', '.join(arquivos_faltantes)}")
        st.info("💡 Complete o carregamento de todos os arquivos acima para executar o cálculo.")
        calculo_executado = False
    
    if calculo_executado:
        # Marcar que o cálculo foi solicitado pelo usuário
        st.session_state.calculo_solicitado = True
        
        try:
            with st.spinner("⚙️ Processando aging e calculando correção monetária..."):
                # Primeiro, calcular aging automaticamente
                df_com_aging = calc_aging.processar_aging_completo(df_padronizado.copy())
                
                if df_com_aging.empty:
                    st.error("❌ Erro ao calcular aging. Verifique os dados de entrada.")
                    return
                
                # ========== USAR MÉTODO CORRETO DO CALCULADOR DE CORREÇÃO ==========
                st.info("📊 Calculando correção monetária completa...")
                
                # Usar o método correto que automaticamente calcula valor_liquido
                df_final_temp = calc_correcao.processar_correcao_completa_com_recuperacao(
                    df_com_aging.copy(), 
                    "Distribuidora", 
                    st.session_state.df_taxa_recuperacao
                )
                
                if 'calculador_valor_justo' in st.session_state and 'df_indices_economicos' in st.session_state:
                    st.info("📊 Aplicando índices customizados do Excel usando cálculo diário com merge...")

                    # Preparar DataFrame de índices
                    df_indices = st.session_state.df_indices_economicos.copy()
                    df_indices['data'] = pd.to_datetime(df_indices['data'])
                    df_indices = df_indices.sort_values('data')
                    
                    # Criar índices com mês anterior para cálculo da taxa mensal
                    df_indices['data_mes_anterior'] = df_indices['data'].shift(1)
                    df_indices['indice_mes_anterior'] = df_indices['indice'].shift(1)
                    
                    # Calcular taxa mensal = indice_atual - indice_anterior (diferença simples)
                    df_indices['taxa_mensal'] = 1 - df_indices['indice_mes_anterior'] / df_indices['indice']
                    df_indices['taxa_diaria'] = (df_indices['taxa_mensal'] + 1) ** (1/30) - 1

                    # Preparar DataFrame principal
                    df_final_temp = df_final_temp.copy()
                    df_final_temp['data_vencimento_limpa'] = pd.to_datetime(df_final_temp['data_vencimento_limpa'], errors='coerce')
                    df_final_temp['data_base'] = pd.to_datetime(df_final_temp['data_base'], errors='coerce')

                    # ==== MERGE 1: DATA BASE ====
                    # Criar coluna auxiliar para merge (ano-mês)
                    df_indices['ano_mes'] = df_indices['data'].dt.to_period('M')
                    df_final_temp['ano_mes_base'] = df_final_temp['data_base'].dt.to_period('M')
                    df_final_temp['ano_mes_venc'] = df_final_temp['data_vencimento_limpa'].dt.to_period('M')
                    
                    # Merge com data base
                    df_merged_base = df_final_temp.merge(
                        df_indices[['ano_mes', 'indice', 'indice_mes_anterior', 'taxa_mensal','taxa_diaria']].rename(columns={
                            'ano_mes': 'ano_mes_base',
                            'indice': 'indice_mes_base',
                            'indice_mes_anterior': 'indice_mes_anterior_base',
                            'taxa_mensal': 'taxa_mensal_base',
                            'taxa_diaria': 'taxa_diaria_base'
                        }),
                        on='ano_mes_base',
                        how='left'
                    )
                    
                    # ==== MERGE 2: DATA VENCIMENTO ====
                    df_merged_completo = df_merged_base.merge(
                        df_indices[['ano_mes', 'indice', 'indice_mes_anterior', 'taxa_mensal','taxa_diaria']].rename(columns={
                            'ano_mes': 'ano_mes_venc',
                            'indice': 'indice_mes_venc',
                            'indice_mes_anterior': 'indice_mes_anterior_venc',
                            'taxa_mensal': 'taxa_mensal_venc',
                            'taxa_diaria': 'taxa_diaria_venc'
                        }),
                        on='ano_mes_venc',
                        how='left'
                    )
                    
                    # ==== CÁLCULO DOS ÍNDICES DIÁRIOS ====
                    # Função para calcular índice na data específica
                    def calcular_indice_diario(row, tipo='base'):
                        if tipo == 'base':
                            data = row['data_base']
                            indice_mes = row['indice_mes_base']
                            indice_mes_anterior = row['indice_mes_anterior_base']
                            taxa_mensal = row['taxa_mensal_base']
                            taxa_diaria = row['taxa_diaria_base']
                            data_fechamento = row['data_base']
                        else:  # vencimento
                            data = row['data_vencimento_limpa']
                            indice_mes = row['indice_mes_venc']
                            indice_mes_anterior = row['indice_mes_anterior_venc']
                            taxa_mensal = row['taxa_mensal_venc']
                            taxa_diaria = row['taxa_diaria_venc']
                            data_fechamento = row['data_vencimento_limpa']
                        
                        if pd.isna(data) or pd.isna(indice_mes) or pd.isna(taxa_mensal):
                            return indice_mes if not pd.isna(indice_mes) else np.nan
                        
                        # Se a data é o último dia do mês de data_fechamento, usar índice direto
                        ultimo_dia_mes = (data_fechamento + pd.offsets.MonthEnd(0)).day
                        if data.day == ultimo_dia_mes:
                            return indice_mes
                        
                        # Calcular dias do período
                        dias_periodo = data.day
                        
                        # Taxa do período
                        taxa_periodo = ((1 + taxa_diaria) ** (dias_periodo) - 1)

                        # Índice na data
                        indice_na_data = (indice_mes_anterior * taxa_periodo) + indice_mes_anterior 

                        return indice_na_data
                    
                    # Aplicar cálculo vetorizado
                    st.info("📊 Calculando índices diários para data base...")
                    df_merged_completo['indice_base_diario'] = df_merged_completo.apply(
                        lambda row: calcular_indice_diario(row, 'base'), axis=1
                    )
                    
                    st.info("📊 Calculando índices diários para data vencimento...")
                    df_merged_completo['indice_venc_diario'] = df_merged_completo.apply(
                        lambda row: calcular_indice_diario(row, 'vencimento'), axis=1
                    )
                    
                    # ==== CÁLCULO DO FATOR DE CORREÇÃO ====
                    # Mask para registros válidos
                    mask_validos = (
                        df_merged_completo['indice_base_diario'].notna()
                        & df_merged_completo['indice_venc_diario'].notna()
                        & (df_merged_completo['indice_base_diario'] > 0)
                        & (df_merged_completo['indice_venc_diario'] > 0)
                    )
                    
                    # Fator de correção = indice_vencimento / indice_base
                    df_merged_completo['fator_correcao'] = 1.0  # Default
                    df_merged_completo.loc[mask_validos, 'fator_correcao'] = (
                        df_merged_completo.loc[mask_validos, 'indice_base_diario'] /
                        df_merged_completo.loc[mask_validos, 'indice_venc_diario']
                    )
                    
                    # ==== APLICAR CORREÇÃO MONETÁRIA ====
                    df_merged_completo['correcao_monetaria'] = np.maximum(
                        df_merged_completo['valor_liquido'] *
                        (df_merged_completo['fator_correcao'] - 1),
                        0
                    )

                    df_merged_completo['valor_corrigido'] = (
                        df_merged_completo['valor_liquido'] +
                        df_merged_completo['multa'] +
                        df_merged_completo['juros_moratorios'] +
                        df_merged_completo['correcao_monetaria']
                    )

                    if 'taxa_recuperacao' in df_merged_completo.columns:
                        df_merged_completo['valor_recuperavel_ate_data_base'] = (
                            df_merged_completo['valor_corrigido'] *
                            df_merged_completo['taxa_recuperacao']
                        )

                    # Atualizar colunas finais
                    df_merged_completo.loc[mask_validos, 'indice_vencimento'] = df_merged_completo.loc[mask_validos, 'indice_venc_diario']
                    df_merged_completo.loc[mask_validos, 'indice_base'] = df_merged_completo.loc[mask_validos, 'indice_base_diario']

                    registros_customizados = mask_validos.sum()
                    total_registros = len(df_merged_completo)
                    percentual = (registros_customizados / total_registros) * 100

                    st.success(f"✅ Correção diária aplicada com merge: {registros_customizados:,}/{total_registros:,} registros ({percentual:.1f}%)")

                    # Limpar colunas auxiliares
                    colunas_temp = [
                        'ano_mes_base', 'ano_mes_venc', 'indice_mes_base', 'indice_mes_venc',
                        'taxa_mensal_base', 'taxa_mensal_venc', 'data_fechamento_base', 'data_fechamento_venc',
                        'indice_base_diario', 'indice_venc_diario', 'indice_mes_anterior_base', 'taxa_diaria_base', 'indice_mes_anterior_venc', 'taxa_diaria_venc'
                    ]
                    df_final_temp = df_merged_completo.drop(columns=[col for col in colunas_temp if col in df_merged_completo.columns])
                    
                else:
                    st.info("ℹ️ Usando correção padrão do sistema (IGPM/IPCA automático)")

                
                if df_final_temp.empty:
                    st.error("❌ Erro ao processar correção monetária.")
                    return

                # ==== APLICAR CORREÇÃO MONETÁRIA ====
                df_final_temp['correcao_monetaria'] = np.maximum(
                    df_final_temp['valor_liquido'] *
                    (df_final_temp['fator_correcao'] - 1),
                    0
                )

                df_final_temp['valor_corrigido'] = (
                    df_final_temp['valor_liquido'] +
                    df_final_temp['multa'] +
                    df_final_temp['juros_moratorios'] +
                    df_final_temp['correcao_monetaria']
                )


                df_final_temp['valor_recuperavel_ate_data_base'] = (
                        df_final_temp['valor_corrigido'] *
                        df_final_temp['taxa_recuperacao']
                    )

                # Renomear fator_correcao para fator_correcao_ate_data_base
                df_final_temp.rename(columns={'fator_correcao': 'fator_correcao_ate_data_base'}, inplace=True)

                # ==================== CÁLCULO DO VALOR JUSTO COM DI-PRE & IPCA ====================
                st.info("📊 Calculando valor justo com taxas DI-PRE & IPCA...")

                try:
                    # Verificar se temos dados DI-PRE disponíveis
                    if st.session_state.df_di_pre.empty:
                        st.warning("⚠️ Dados DI-PRE não disponíveis. Usando taxa padrão.")
                        taxa_di_pre_6m = 0.10  # 10% ao ano como fallback
                    else:
                        # Buscar taxa DI-PRE para 6 meses (prazo padrão de recebimento)
                        linha_6m = st.session_state.df_di_pre[st.session_state.df_di_pre['meses_futuros'] == 6]
                        if not linha_6m.empty:
                            taxa_di_pre_6m = linha_6m.iloc[0]['252'] / 100  # Converter de % para decimal
                        else:
                            st.warning("⚠️ Taxa DI-PRE para 6 meses não encontrada. Usando valor médio.")
                            taxa_di_pre_6m = st.session_state.df_di_pre['252'].mean() / 100
                    
                    # ============= ETAPA 1: PREPARAR DADOS BASE =============
                    # Garantir que data_base seja datetime
                    if 'data_base' not in df_final_temp.columns:
                        df_final_temp['data_base'] = datetime.now()
                    df_final_temp['data_base'] = pd.to_datetime(df_final_temp['data_base'], errors='coerce')
                    
                    # ============= ETAPA 2: CÁLCULO DA TAXA DI-PRE ANUALIZADA =============
                    df_final_temp['di_pre_taxa_anual'] = taxa_di_pre_6m
                    
                    # Aplicar spread de risco de 2.5% sobre a taxa DI-PRE
                    spread_risco = 2.5  # 2.5%
                    df_final_temp['taxa_di_pre_total_anual'] = (1 + df_final_temp['di_pre_taxa_anual']) * (1 + spread_risco / 100) - 1

                    # Converter taxa anual para mensal: (1 + taxa_anual)^(1/12) - 1
                    df_final_temp['taxa_desconto_mensal'] = (1 + df_final_temp['taxa_di_pre_total_anual']) ** (1/12) - 1

                    # ============= ETAPA 3: CÁLCULO DO PERÍODO ATÉ RECEBIMENTO =============
                    # Data estimada de recebimento (data_base + prazo_recebimento em meses)
                    def calcular_data_recebimento(row):
                        try:
                            data_base = row.get('data_base', datetime.now())
                            # Usar prazo_recebimento se disponível, senão usar 30 como fallback
                            prazo = row.get('prazo_recebimento', 30) if 'prazo_recebimento' in df_final_temp.columns else 30
                            return pd.to_datetime(data_base) + pd.DateOffset(months=int(prazo))
                        except:
                            return datetime.now() + pd.DateOffset(months=6)
                    
                    df_final_temp['data_recebimento_estimada'] = df_final_temp.apply(calcular_data_recebimento, axis=1)
                    
                    # Calcular meses até o recebimento - usar prazo_recebimento se disponível
                    if 'prazo_recebimento' in df_final_temp.columns:
                        df_final_temp['meses_ate_recebimento'] = df_final_temp['prazo_recebimento']
                    else:
                        df_final_temp['meses_ate_recebimento'] = 30

                    # ============= ETAPA 3.1: CÁLCULO DO IPCA MENSAL REAL DOS DADOS DO EXCEL =============
                    st.info("📊 Calculando IPCA mensal real baseado nos índices carregados...")
                    
                    # Buscar data atual e data de 12 meses atrás nos dados carregados
                    data_hoje = datetime.now()
                    data_12m_atras = data_hoje - pd.DateOffset(months=12)
                    
                    # Formatar datas para busca (YYYY.MM)
                    data_hoje_formatada = data_hoje.strftime('%Y.%m')
                    data_12m_formatada = data_12m_atras.strftime('%Y.%m')
                    
                    # Buscar índices correspondentes no DataFrame de índices
                    df_indices = st.session_state.df_indices_economicos.copy()
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
                        � IPCA Mensal: {ipca_mensal_calculado*100:.4f}%
                        """)
                        
                    else:
                        # Fallback se não conseguir calcular
                        df_final_temp['ipca_mensal'] = 0.0037  # 4.5% ao ano
                        st.warning("⚠️ Não foi possível calcular IPCA dos dados. Usando taxa padrão de 4.5% a.a.")
                    
                    
                    # Calcular o fator de correção com IPCA
                    df_final_temp['fator_correcao_ate_recebimento'] = (1 + df_final_temp['ipca_mensal']) ** df_final_temp['meses_ate_recebimento']

                    # ============= ETAPA 4: APLICAR TAXA DE DESCONTO =============
                    # Fator de capitalização composta: (1 + taxa_mensal)^meses
                    df_final_temp['fator_de_desconto'] = (1 + df_final_temp['taxa_desconto_mensal'] ) ** df_final_temp['meses_ate_recebimento']
                    
                    # ============= ETAPA 5: CÁLCULO DE MORA BASEADA NO PRAZO =============
                    # Data atual para cálculo de atraso (mantido para referência)
                    data_atual = datetime.now()
                    
                    # Calcular dias de atraso em relação à data de recebimento estimada (mantido para referência)
                    df_final_temp['dias_atraso'] = (data_atual - df_final_temp['data_recebimento_estimada']).dt.days.clip(lower=0)
                    
                    # CORREÇÃO: Mora calculada como 1% * prazo_recebimento em meses
                    # Como temos meses_ate_recebimento = 30, a mora será 1% * 30 = 30%
                    taxa_mora_mensal = 0.01  # 1% ao mês
                    df_final_temp['mora'] = df_final_temp['meses_ate_recebimento'] * taxa_mora_mensal

                    df_final_temp['mora_final'] = df_final_temp['mora']
                    
                    # ========== DEBUG: VERIFICAR SE MORA FOI CALCULADA ==========
                    st.info(f"""
                    🔍 **DEBUG MORA CALCULADA:**
                    - Total de registros: {len(df_final_temp):,}
                    - Mora média: {df_final_temp['mora'].mean():.4f}
                    - Mora máxima: {df_final_temp['mora'].max():.4f}
                    - Mora mínima: {df_final_temp['mora'].min():.4f}
                    - Registros com mora > 0: {(df_final_temp['mora'] > 0).sum():,}
                    - Meses até recebimento (amostra): {df_final_temp['meses_ate_recebimento'].head(3).tolist()}
                    """)
                    
                    # Mostrar amostra dos cálculos
                    colunas_debug = ['meses_ate_recebimento', 'mora', 'mora_final']
                    amostra_debug = df_final_temp[colunas_debug].head(5)
                    st.dataframe(amostra_debug, use_container_width=True)
                    
                    # ============= ETAPA 6: CÁLCULO FINAL DO VALOR JUSTO =============
                    # Verificar se temos taxa_recuperacao
                    if 'taxa_recuperacao' in df_final_temp.columns:
                        # Fórmula completa: valor_corrigido × taxa_recuperacao × (fator_capitalização + multa)
                        df_final_temp['valor_justo'] = (
                            df_final_temp['valor_corrigido'] * 
                            df_final_temp['taxa_recuperacao'] * 
                            (df_final_temp['fator_correcao_ate_recebimento'] + df_final_temp['mora_final']) /
                            df_final_temp['fator_de_desconto']
                        )
                    else:
                        # Fallback sem taxa de recuperação
                        df_final_temp['valor_justo'] = (
                            df_final_temp['valor_corrigido'] * 
                            (df_final_temp['fator_correcao_ate_recebimento'] + df_final_temp['mora_final']) /
                            df_final_temp['fator_de_desconto']
                        )

                    # Calcular valor_recuperavel_ate_recebimento
                    df_final_temp['valor_recuperavel_ate_recebimento'] = (
                        df_final_temp['valor_recuperavel_ate_data_base'] * (df_final_temp['fator_correcao_ate_recebimento'] + df_final_temp['mora_final'])
                    )

                    # Remove a coluna 'valor_recuperavel' se existir
                    if 'valor_recuperavel' in df_final_temp.columns:
                        df_final_temp = df_final_temp.drop(columns=['valor_recuperavel'])

                    # ============= ETAPA 7: CALCULAR VALOR JUSTO PÓS REMUNERAÇÃO VARIÁVEL =============
                    # Aplicar descontos por aging sobre o valor justo
                    df_final_temp = calc_correcao.calcular_valor_justo_reajustado(df_final_temp)
                    
                    # ========== DEBUG: VERIFICAR SE MORA FOI PRESERVADA APÓS REMUNERAÇÃO VARIÁVEL ==========
                    st.info(f"""
                    🔍 **DEBUG MORA APÓS REMUNERAÇÃO VARIÁVEL:**
                    - Total de registros: {len(df_final_temp):,}
                    - Mora média: {df_final_temp['mora'].mean():.4f}
                    - Mora máxima: {df_final_temp['mora'].max():.4f}
                    - Mora mínima: {df_final_temp['mora'].min():.4f}
                    - Registros com mora > 0: {(df_final_temp['mora'] > 0).sum():,}
                    - Colunas disponíveis que contêm 'mora': {[col for col in df_final_temp.columns if 'mora' in col.lower()]}
                    """)
                    
                    # Mostrar amostra dos cálculos APÓS remuneração variável
                    colunas_debug_pos = [col for col in ['mora', 'mora_final', 'meses_ate_recebimento'] if col in df_final_temp.columns]
                    if colunas_debug_pos:
                        amostra_debug_pos = df_final_temp[colunas_debug_pos].head(5)
                        st.dataframe(amostra_debug_pos, use_container_width=True)

                    # ============= ETAPA 8: ADICIONAR COLUNAS INFORMATIVAS =============
                    
                    # Salvar resultado no session_state
                    st.session_state.df_final = df_final_temp
                    
                    # Calcular estatísticas do DI-PRE para exibição
                    calc_valor_justo = CalculadorValorJusto()
                    stats_di_pre = calc_valor_justo.obter_estatisticas_di_pre(st.session_state.df_di_pre)
                    st.session_state.stats_di_pre_valor_justo = stats_di_pre
                    
                    st.success("✅ Correção monetária e valor justo calculados com sucesso!")
                    
                except Exception as e:
                    st.error(f"❌ Erro no cálculo do valor justo: {str(e)}")
                    st.warning("⚠️ Continuando com dados básicos (sem valor justo)")
                    # Salvar dados básicos mesmo com erro no valor justo
                    st.session_state.df_final = df_final_temp
                    st.exception(e)  # Debug detalhado
                    
        except Exception as e:
            st.error(f"❌ Erro ao processar correção: {str(e)}")
            st.exception(e)  # Debug

    # Mostrar resultados APENAS se o cálculo foi solicitado pelo usuário E temos dados calculados
    calculo_foi_solicitado = st.session_state.get('calculo_solicitado', False)
    tem_dados_calculados = 'df_final' in st.session_state and not st.session_state.df_final.empty
    
    # Adicionar informação quando tudo está pronto mas o cálculo não foi executado
    if not calculo_foi_solicitado and tem_taxa_recuperacao:
        st.info("💡 **Tudo pronto!** Clique no botão 'Calcular Correção Monetária' acima para executar os cálculos.")
    
    if calculo_foi_solicitado and tem_dados_calculados:
        
        st.markdown("---")
        
        # Resultados da Correção Monetária
        st.subheader("💰 Resultados da Correção Monetária e Valor Justo")
        
        # Verificar se temos as novas colunas calculadas
        colunas_valor_justo_novo = ['fator_correcao_ate_recebimento', 'taxa_di_pre_mensal_efetiva', 'taxa_di_pre_aplicada', 'spread_risco_aplicado']
        tem_calculos_novos = all(col in st.session_state.df_final.columns for col in colunas_valor_justo_novo)
        
        # Verificar se temos colunas de taxa de recuperação e valor justo
        colunas_taxa = ['aging_taxa', 'taxa_recuperacao', 'prazo_recebimento', 'valor_recuperavel_ate_recebimento']
        tem_colunas_recuperacao = all(col in st.session_state.df_final.columns for col in colunas_taxa)
        
        colunas_valor_justo = ['valor_justo_pre_rv']
        tem_colunas_valor_justo = all(col in st.session_state.df_final.columns for col in colunas_valor_justo)
        
        # Verificar se temos valor justo pós remuneração variável
        colunas_valor_justo_pos_rv = ['valor_justo_pos_rv', 'percentual_rv', 'valor_desconto_rv']
        tem_colunas_valor_justo_pos_rv = all(col in st.session_state.df_final.columns for col in colunas_valor_justo_pos_rv)
        
        if tem_colunas_recuperacao and tem_colunas_valor_justo and tem_colunas_valor_justo_pos_rv:
            if tem_calculos_novos:
                st.success("✅ **Resultados completos aprimorados:** Taxa de recuperação + Valor justo com DI-PRE + Valor justo pós remuneração variável + Metodologia melhorada")
            else:
                st.success("✅ **Resultados completos:** Taxa de recuperação + Valor justo + Valor justo pós remuneração variável")
        elif tem_colunas_recuperacao and tem_colunas_valor_justo:
            if tem_calculos_novos:
                st.success("✅ **Resultados completos aprimorados:** Taxa de recuperação + Valor justo com DI-PRE + Metodologia melhorada")
            else:
                st.success("✅ **Resultados completos:** Taxa de recuperação + Valor justo com DI-PRE")
        elif tem_colunas_recuperacao:
            st.warning("⚠️ **Resultados parciais:** Apenas taxa de recuperação (sem valor justo)")
        elif tem_colunas_valor_justo:
            st.warning("⚠️ **Resultados parciais:** Apenas valor justo (sem taxa de recuperação)")
        else:
            st.warning("⚠️ **Resultados básicos:** Sem taxa de recuperação nem valor justo")
        
        # Mostrar detalhes dos novos cálculos se disponíveis
        if tem_calculos_novos:
            with st.expander("🔍 Detalhes dos Cálculos Aprimorados", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    taxa_media_aplicada = st.session_state.df_final['taxa_di_pre_aplicada'].mean()
                    st.metric(
                        "📊 Taxa DI-PRE Média",
                        f"{taxa_media_aplicada:.2f}%",
                        help="Taxa DI-PRE média aplicada aos cálculos"
                    )
                
                with col2:
                    spread_medio = st.session_state.df_final['spread_risco_aplicado'].mean()
                    st.metric(
                        "⚡ Spread Médio",
                        f"{spread_medio:.1f}%",
                        help="Spread de risco médio aplicado"
                    )
                
                with col3:
                    taxa_total_media = st.session_state.df_final['taxa_total_aplicada'].mean()
                    st.metric(
                        "🎯 Taxa Total Média",
                        f"{taxa_total_media:.2f}%",
                        help="Taxa total média (DI-PRE + spread)"
                    )
                
                with col4:
                    fator_medio = st.session_state.df_final['fator_correcao_ate_recebimento'].mean()
                    st.metric(
                        "📈 Fator Médio",
                        f"{fator_medio:.4f}",
                        help="Fator de capitalização médio aplicado"
                    )
                
                # Mostrar amostra dos cálculos detalhados
                st.subheader("🔬 Amostra dos Cálculos Detalhados")
                colunas_detalhe = [
                    'empresa', 'valor_corrigido', 'taxa_recuperacao', 
                    'taxa_di_pre_aplicada', 'spread_risco_aplicado', 'taxa_total_aplicada',
                    'fator_correcao_ate_recebimento', 'mora_final', 'valor_justo_pre_rv'
                ]
                
                # Filtrar apenas colunas que existem
                colunas_existentes = [col for col in colunas_detalhe if col in st.session_state.df_final.columns]
                
                # Mostrar amostra de 10 registros
                amostra_detalhe = st.session_state.df_final[colunas_existentes].head(10)
                st.dataframe(amostra_detalhe, use_container_width=True, hide_index=True)
        
        # Definir ordem de aging para organizar tabelas
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

        # Visão Detalhada por Empresa, Tipo e Classificação
        st.subheader("📊 Agrupamento Detalhado - Por Empresa, Tipo, Classe, Status e Situação")
        
        # Definir colunas de agregação baseado no que está disponível
        colunas_agg_1 = {
            'valor_principal': 'sum',
            'valor_liquido': 'sum', 
            'valor_corrigido': 'sum'
        }
        
        if tem_colunas_recuperacao:
            colunas_agg_1.update({
                'taxa_recuperacao': 'mean',
                'valor_recuperavel_ate_recebimento': 'sum'
            })
        
        if tem_colunas_valor_justo:
            colunas_agg_1.update({
                'valor_justo_pre_rv': 'sum'
            })
        
        if tem_colunas_valor_justo_pos_rv:
            colunas_agg_1.update({
                'valor_justo_pos_rv': 'sum',
                'valor_desconto_rv': 'sum'
            })
        
        # Adicionar colunas do novo cálculo se disponíveis
        if tem_calculos_novos:
            colunas_agg_1.update({
                'taxa_di_pre_aplicada': 'mean',
                'spread_risco_aplicado': 'mean',
                'taxa_total_aplicada': 'mean',
                'fator_correcao_ate_recebimento': 'mean',
                'mora_final': 'mean'
            })
        
        # Verificar se as colunas existem no DataFrame antes de agrupar
        colunas_groupby = ['empresa', 'aging','aging_taxa']
        
        # Adicionar colunas opcionais se existirem
        colunas_opcionais = ['tipo', 'classe', 'status', 'situacao']
        for col in colunas_opcionais:
            if col in st.session_state.df_final.columns:
                colunas_groupby.insert(-2, col)  # Inserir antes de aging
        
        df_agg1 = (
            st.session_state.df_final
            .groupby(colunas_groupby, dropna=False)
            .agg(colunas_agg_1)
            .reset_index()
        )

        df_agg1['aging'] = pd.Categorical(df_agg1['aging'], categories=ordem_aging, ordered=True)
        df_agg1 = df_agg1.sort_values(['empresa'] + [col for col in colunas_opcionais if col in df_agg1.columns] + ['aging'])

        st.dataframe(df_agg1, use_container_width=True, hide_index=True)

        # Visão Consolidada por Empresa e Aging
        st.subheader("🎯 Agrupamento Consolidado - Por Empresa e Aging")
        st.caption("Valores consolidados por empresa e faixa de aging, incluindo valor principal, líquido, corrigido, recuperável e valor justo")
        
        # Definir colunas de agregação baseado no que está disponível
        colunas_agg_2 = {
            'valor_principal': 'sum',
            'valor_liquido': 'sum',
            'valor_corrigido': 'sum'
        }
        
        if tem_colunas_recuperacao:
            colunas_agg_2.update({
                'valor_recuperavel_ate_recebimento': 'sum',
                'taxa_recuperacao': 'mean'
            })
        
        if tem_colunas_valor_justo:
            colunas_agg_2['valor_justo_pre_rv'] = 'sum'
        
        if tem_colunas_valor_justo_pos_rv:
            colunas_agg_2.update({
                'valor_justo_pos_rv': 'sum',
                'valor_desconto_rv': 'sum'
            })
        
        # Adicionar métricas do novo cálculo se disponíveis
        if tem_calculos_novos:
            colunas_agg_2.update({
                'taxa_di_pre_aplicada': 'mean',
                'fator_correcao_ate_recebimento': 'mean'
            })
        
        df_agg2 = (
            st.session_state.df_final
            .groupby(['empresa', 'aging', 'aging_taxa'], dropna=False)
            .agg(colunas_agg_2)
            .reset_index()
        )

        df_agg2['aging'] = pd.Categorical(df_agg2['aging'], categories=ordem_aging, ordered=True)
        df_agg2 = df_agg2.sort_values(['empresa'])

        st.dataframe(df_agg2, use_container_width=True, hide_index=True)

        # Visão Geral por Aging
        st.subheader("📈 Agrupamento Geral - Por Aging e Taxa de Recuperação")
        st.caption("Visão consolidada geral agrupada apenas por faixa de aging, mostrando totais gerais incluindo valor justo")
        
        # Definir colunas de agregação baseado no que está disponível
        colunas_agg_3 = {
            'valor_principal': 'sum',
            'valor_liquido': 'sum',
            'valor_corrigido': 'sum'
        }
        
        if tem_colunas_recuperacao:
            colunas_agg_3.update({
                'valor_recuperavel_ate_recebimento': 'sum',
                'taxa_recuperacao': 'mean'
            })
        
        if tem_colunas_valor_justo:
            colunas_agg_3['valor_justo_pre_rv'] = 'sum'
        
        if tem_colunas_valor_justo_pos_rv:
            colunas_agg_3.update({
                'valor_justo_pos_rv': 'sum',
                'valor_desconto_rv': 'sum'
            })
        
        # Adicionar estatísticas do novo cálculo se disponíveis
        if tem_calculos_novos:
            colunas_agg_3.update({
                'taxa_di_pre_aplicada': 'mean',
                'taxa_total_aplicada': 'mean',
                'fator_correcao_ate_recebimento': 'mean'
            })
        
        df_agg3 = (
            st.session_state.df_final
            .groupby(['aging_taxa'], dropna=False)
            .agg(colunas_agg_3)
            .reset_index()
        )

        # df_agg3['aging'] = pd.Categorical(df_agg3['aging'], categories=ordem_aging, ordered=True)
        # df_agg3 = df_agg3.sort_values(['aging'])

        st.dataframe(df_agg3, use_container_width=True, hide_index=True)

        # Resumo Total Consolidado por Empresa
        st.markdown("---")
        st.subheader("💰 Resumo Total Consolidado por Empresa")
        
        # Calcular totais por empresa
        colunas_resumo_empresa = {
            'valor_principal': 'sum',
            'valor_liquido': 'sum',
            'valor_corrigido': 'sum'
        }
        
        if tem_colunas_recuperacao:
            colunas_resumo_empresa['valor_recuperavel_ate_recebimento'] = 'sum'
        
        if tem_colunas_valor_justo:
            colunas_resumo_empresa['valor_justo_pre_rv'] = 'sum'
        
        if tem_colunas_valor_justo_pos_rv:
            colunas_resumo_empresa['valor_justo_pos_rv'] = 'sum'
        
        df_resumo_empresa = (
            st.session_state.df_final
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
        if tem_colunas_recuperacao:
            colunas_valor.append('valor_recuperavel_ate_recebimento')
        if tem_colunas_valor_justo:
            colunas_valor.append('valor_justo_pre_rv')
        if tem_colunas_valor_justo_pos_rv:
            colunas_valor.append('valor_justo_pos_rv')
        
        for col in colunas_valor:
            if col in df_resumo_display.columns:
                df_resumo_display[col] = df_resumo_display[col].apply(
                    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )
        
        # Renomear colunas para exibição
        nomes_colunas = {
            'empresa': '🏢 Empresa',
            'valor_principal': '📊 Valor Principal',
            'valor_liquido': '💧 Valor Líquido',
            'valor_corrigido': '⚡ Valor Corrigido'
        }
        
        if tem_colunas_recuperacao:
            nomes_colunas['valor_recuperavel_ate_recebimento'] = '🎯 Valor Recuperável'
        
        if tem_colunas_valor_justo:
            nomes_colunas['valor_justo_pre_rv'] = '💎 Valor Justo Pré-RV'
        
        if tem_colunas_valor_justo_pos_rv:
            nomes_colunas['valor_justo_pos_rv'] = '✨ Valor Justo Pós-RV'
        
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
        if tem_colunas_recuperacao:
            total_recuperavel = df_resumo_empresa['valor_recuperavel_ate_recebimento'].sum()
        else:
            total_recuperavel = 0
        
        if tem_colunas_valor_justo:
            total_valor_justo_pre_rv = df_resumo_empresa['valor_justo_pre_rv'].sum()
        else:
            total_valor_justo_pre_rv = 0
        
        if tem_colunas_valor_justo_pos_rv:
            total_valor_justo_pos_rv = df_resumo_empresa['valor_justo_pos_rv'].sum()
        else:
            total_valor_justo_pos_rv = 0
        
        # Criar colunas para as métricas (adaptar quantidade baseado no que temos)
        if tem_colunas_valor_justo_pos_rv:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
        elif tem_colunas_valor_justo:
            col1, col2, col3, col4, col5 = st.columns(5)
        else:
            col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 Valor Principal Total",
                f"R$ {total_principal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                help="Soma total dos valores principais de todas as empresas"
            )
        
        with col2:
            st.metric(
                "💧 Valor Líquido Total",
                f"R$ {total_liquido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                help="Soma total dos valores líquidos de todas as empresas"
            )
        
        with col3:
            st.metric(
                "⚡ Valor Corrigido Total",
                f"R$ {total_corrigido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                help="Soma total dos valores corrigidos monetariamente"
            )
        
        with col4:
            if tem_colunas_recuperacao:
                st.metric(
                    "🎯 Valor Recuperável Total",
                    f"R$ {total_recuperavel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    help="Soma total dos valores esperados de recuperação"
                )
            else:
                st.metric(
                    "⚠️ Valor Recuperável",
                    "N/D",
                    help="Taxa de recuperação não configurada"
                )
        
        # Quinta coluna só aparece se tivermos valor justo
        if tem_colunas_valor_justo:
            with col5:
                st.metric(
                    "💎 Valor Justo Pré-RV",
                    f"R$ {total_valor_justo_pre_rv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    help="Soma total dos valores justos antes da aplicação da remuneração variável"
                )
        
        # Sexta coluna só aparece se tivermos valor justo pós remuneração variável
        if tem_colunas_valor_justo_pos_rv:
            with col6:
                st.metric(
                    "✨ Valor Justo Pós Remuneração Variável",
                    f"R$ {total_valor_justo_pos_rv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    help="Soma total dos valores justos com descontos por aging aplicados"
                )
        
        # Exportação Manual dos Dados Brutos
        st.markdown("---")
        st.subheader("💾 Exportação dos Dados Finais")
        
        st.info(f"""
        **📋 Dados prontos para exportação:**
        - **Total de registros:** {len(st.session_state.df_final):,}
        - **Total de colunas:** {len(st.session_state.df_final.columns)}
        - **Conteúdo:** Todos os registros processados com aging, correção monetária, taxa de recuperação e valor justo com DI-PRE
        
        **💡 Sistema de divisão automática:**
        - **Limite por arquivo:** 700.000 linhas
        - **Arquivos necessários:** {math.ceil(len(st.session_state.df_final) / 700000)} arquivo(s)
        - **Divisão automática:** Se os dados excederem 700k linhas, serão divididos automaticamente em múltiplos arquivos
        
        **📁 Formato de exportação:**
        - **Separador:** `;` (ponto e vírgula)
        - **Decimal:** `,` (vírgula brasileira)
        - **Encoding:** UTF-8 com BOM (compatível com Excel)
        """)
        
        # Mostrar aviso se for necessário dividir
        total_registros = len(st.session_state.df_final)
        if total_registros > 700000:
            num_arquivos = math.ceil(total_registros / 700000)
            st.warning(f"""
            ⚠️ **Atenção - Divisão automática ativada!**
            
            Seus dados ({total_registros:,} registros) serão automaticamente divididos em **{num_arquivos} arquivos** 
            para otimizar o desempenho e compatibilidade com o Excel.
            
            **Arquivos que serão gerados:**
            - FIDC_Dados_Finais_[timestamp]_parte_1.csv
            - FIDC_Dados_Finais_[timestamp]_parte_2.csv
            {'- ...' if num_arquivos > 2 else ''}
            {f'- FIDC_Dados_Finais_[timestamp]_parte_{num_arquivos}.csv' if num_arquivos > 2 else ''}
            """)
        
        # Criar duas colunas para os botões
        col_export1, col_export2 = st.columns(2)

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
            'fator_de_desconto', 'mora', 'mora_final', 'fator_correcao_ate_recebimento',
             'valor_recuperavel_ate_data_base', 'valor_recuperavel_ate_recebimento','valor_justo', 'valor_justo_pos_rv', 'percentual_rv', 'valor_desconto_rv'
        ]

        preview_df = st.session_state.df_final.head(10).copy()

        # Identificar colunas que existem na ordem especificada
        colunas_existentes = [col for col in colunas_ordem_usuario if col in preview_df.columns]
        colunas_restantes = [col for col in preview_df.columns if col not in colunas_ordem_usuario]
        
        # Reordenar DataFrame conforme especificação do usuário
        preview_df = preview_df[colunas_existentes + colunas_restantes]

        st.dataframe(preview_df)
        
        # Botão para exportar dados completos
        if st.button("💾 Salvar Dados Completos na Pasta 'data'", type="primary", use_container_width=True):
            try:
                with st.spinner("💾 Salvando dados finais..."):
                    # Criar diretório data se não existir
                    data_dir = os.path.join(os.getcwd(), 'data')
                    os.makedirs(data_dir, exist_ok=True)
                    
                    # Nome do arquivo com timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_base_arquivo = "FIDC_Dados_Finais"
                    
                    # =========== PREPARAÇÃO DOS DADOS PARA EXPORTAÇÃO CSV ===========
                    csv_export = st.session_state.df_final.copy(deep=True)
                    
                    # 1. PREPARAR DADOS PARA FORMATAÇÃO CSV (CONVERSÕES DE TIPO)
                    st.info("📊 Preparando dados para exportação CSV...")
                    
                    # A. Converter todas as colunas de data para string formatada
                    colunas_data = ['data_vencimento_limpa', 'data_base', 'data_recebimento_estimada']
                    for col in colunas_data:
                        if col in csv_export.columns:
                            csv_export[col] = pd.to_datetime(csv_export[col], errors='coerce').dt.strftime('%Y-%m-%d')
                    
                    # B. Garantir que colunas numéricas não tenham problemas de formato
                    colunas_numericas = [
                        'valor_principal', 'valor_liquido', 'valor_corrigido', 'valor_recuperavel_ate_recebimento','valor_recuperavel_ate_data_base', 'valor_justo_pre_rv', 'valor_justo_pos_rv', 'valor_desconto_rv',
                        'multa', 'juros_moratorios', 'correcao_monetaria', 'percentual_rv',
                        'taxa_recuperacao', 'fator_correcao_ate_data_base', 'ipca_mensal',
                        'di_pre_taxa_anual', 'taxa_di_pre_total_anual', 'taxa_desconto_mensal',
                        'meses_ate_recebimento'
                    ]
                    
                    for col in colunas_numericas:
                        if col in csv_export.columns:
                            csv_export[col] = pd.to_numeric(csv_export[col], errors='coerce').fillna(0)
                    
                    # C. Garantir que colunas de texto não tenham problemas
                    colunas_texto = ['empresa', 'aging', 'aging_taxa', 'tipo', 'classe', 'status', 'situacao']
                    for col in colunas_texto:
                        if col in csv_export.columns:
                            csv_export[col] = csv_export[col].astype(str).fillna('')
                    
                    # D. Converter dados de aging para inteiros se possível
                    if 'meses_ate_recebimento' in csv_export.columns:
                        csv_export['meses_ate_recebimento'] = csv_export['meses_ate_recebimento'].astype(int)
                    
                    # G. Remover colunas temporárias/desnecessárias se existirem
                    colunas_remover = [
                        'vencimento_formatado', 'base_formatada', 'indice_vencimento_custom', 
                        'indice_base_custom', 'fator_correcao_ate_data_base', 'diferenca_12m'
                    ]
                    csv_export = csv_export.drop(columns=[col for col in colunas_remover if col in csv_export.columns])
                    
                    # G.1. Renomear colunas conforme especificado pelo usuário
                    st.info("📝 Renomeando colunas para exportação final...")
                    
                    colunas_renomear = {
                        'valor_justo': 'valor_justo_pre_rv',
                        'valor_justo_reajusto': 'valor_justo_pos_rv'
                    }
                    
                    # Aplicar renomeação apenas para colunas que existem
                    colunas_para_renomear = {k: v for k, v in colunas_renomear.items() if k in csv_export.columns}
                    if colunas_para_renomear:
                        csv_export = csv_export.rename(columns=colunas_para_renomear)
                        st.success(f"✅ Colunas renomeadas: {list(colunas_para_renomear.keys())} → {list(colunas_para_renomear.values())}")
                    
                    # Debug: Mostrar colunas de valor justo disponíveis
                    colunas_valor_justo_debug = [col for col in csv_export.columns if 'valor_justo' in col.lower()]
                    if colunas_valor_justo_debug:
                        st.info(f"📊 Colunas de valor justo no export: {colunas_valor_justo_debug}")
                    else:
                        st.warning("⚠️ Nenhuma coluna de valor justo encontrada no DataFrame final")
                    
                    # H. Reordenar colunas para exportação na sequência especificada pelo usuário
                    # Identificar colunas que existem na ordem especificada
                    colunas_existentes = [col for col in colunas_ordem_usuario if col in csv_export.columns]
                    colunas_restantes = [col for col in csv_export.columns if col not in colunas_ordem_usuario]
                    
                    # Reordenar DataFrame conforme especificação do usuário
                    csv_export = csv_export[colunas_existentes + colunas_restantes]
                    
                    # 2. VERIFICAR SE PRECISA DIVIDIR OS DADOS EM MÚLTIPLOS ARQUIVOS
                    total_linhas = len(csv_export)
                    limite_linhas = 700000  # 700 mil linhas por arquivo
                    
                    numero_arquivos = calcular_numero_arquivos(total_linhas, limite_linhas)
                    
                    if numero_arquivos == 1:
                        # Caso simples: apenas um arquivo
                        st.info("💾 Salvando arquivo único...")
                        
                        # Preparar DataFrame para exportação brasileira
                        csv_export_br = csv_export.copy()
                        
                        # Formatação de números para padrão brasileiro
                        colunas_numericas_final = csv_export_br.select_dtypes(include=[np.number]).columns
                        
                        for col in colunas_numericas_final:
                            if csv_export_br[col].dtype in ['float64', 'float32']:
                                # Todos os números com 6 casas decimais conforme solicitado
                                csv_export_br[col] = csv_export_br[col].apply(
                                    lambda x: f"{x:.6f}".replace('.', ',') if pd.notna(x) else ''
                                )
                            elif csv_export_br[col].dtype in ['int64', 'int32']:
                                # Manter inteiros como estão (sem vírgula)
                                csv_export_br[col] = csv_export_br[col].astype(str)
                        
                        # Nome e caminho do arquivo
                        nome_arquivo_csv = f"{nome_base_arquivo}_{timestamp}.csv"
                        caminho_csv = os.path.join(data_dir, nome_arquivo_csv)
                        
                        # Salvar com separador brasileiro (ponto e vírgula) e decimal brasileiro (vírgula)
                        csv_export_br.to_csv(caminho_csv, index=False, encoding='utf-8-sig', sep=';')
                        
                        st.success(f"✅ **Arquivo único salvo com sucesso!**")
                        st.info(f"""
                        **📁 Arquivo salvo no formato brasileiro:**
                        - **Nome:** `{nome_arquivo_csv}`
                        - **Localização:** `{data_dir}`
                        - **Registros:** {total_linhas:,}
                        - **Separador de campo:** `;` (ponto e vírgula)
                        - **Separador decimal:** `,` (vírgula - padrão brasileiro)
                        - **Encoding:** UTF-8 com BOM (compatível com Excel brasileiro)
                        
                        ✅ **Formato otimizado para Excel brasileiro!**
                        """)
                        
                    else:
                        # Caso complexo: múltiplos arquivos
                        st.info(f"📊 Dividindo dados em {numero_arquivos} arquivos (máximo {limite_linhas:,} linhas por arquivo)...")
                        
                        # Dividir o DataFrame em chunks
                        chunks = dividir_dataframe_em_chunks(csv_export, limite_linhas)
                        
                        # Gerar nomes dos arquivos
                        nomes_arquivos = gerar_nomes_arquivos_csv(nome_base_arquivo, numero_arquivos, timestamp)
                        
                        arquivos_salvos = []
                        
                        # Salvar cada chunk como um arquivo CSV
                        for i, (chunk, nome_arquivo) in enumerate(zip(chunks, nomes_arquivos), 1):
                            st.info(f"💾 Salvando parte {i}/{numero_arquivos}: {len(chunk):,} registros...")
                            
                            # Preparar DataFrame para exportação brasileira
                            csv_export_br = chunk.copy()
                            
                            # Formatação de números para padrão brasileiro
                            colunas_numericas_final = csv_export_br.select_dtypes(include=[np.number]).columns
                            
                            for col in colunas_numericas_final:
                                if csv_export_br[col].dtype in ['float64', 'float32']:
                                    # Todos os números com 6 casas decimais conforme solicitado
                                    csv_export_br[col] = csv_export_br[col].apply(
                                        lambda x: f"{x:.6f}".replace('.', ',') if pd.notna(x) else ''
                                    )
                                elif csv_export_br[col].dtype in ['int64', 'int32']:
                                    # Manter inteiros como estão (sem vírgula)
                                    csv_export_br[col] = csv_export_br[col].astype(str)
                            
                            # Caminho completo do arquivo
                            caminho_csv = os.path.join(data_dir, nome_arquivo)
                            
                            # Salvar com separador brasileiro (ponto e vírgula) e decimal brasileiro (vírgula)
                            csv_export_br.to_csv(caminho_csv, index=False, encoding='utf-8-sig', sep=';')
                            
                            arquivos_salvos.append({
                                'nome': nome_arquivo,
                                'caminho': caminho_csv,
                                'registros': len(chunk)
                            })
                        
                        st.success(f"✅ **Todos os {numero_arquivos} arquivos salvos com sucesso!**")
                        
                        # Mostrar detalhes de todos os arquivos
                        st.info("📁 **Arquivos gerados:**")
                        for i, arquivo in enumerate(arquivos_salvos, 1):
                            st.write(f"**Parte {i}:** `{arquivo['nome']}` - {arquivo['registros']:,} registros")
                        
                        st.info(f"""
                        **📋 Resumo da exportação:**
                        - **Total de arquivos:** {numero_arquivos}
                        - **Total de registros:** {total_linhas:,}
                        - **Máximo por arquivo:** {limite_linhas:,} linhas
                        - **Localização:** `{data_dir}`
                        - **Separador de campo:** `;` (ponto e vírgula)
                        - **Separador decimal:** `,` (vírgula - padrão brasileiro)
                        - **Encoding:** UTF-8 com BOM (compatível com Excel brasileiro)
                        
                        ✅ **Todos os arquivos otimizados para Excel brasileiro!**
                        """)
                    
            except Exception as e:
                st.error(f"❌ Erro ao salvar dados: {str(e)}")
                st.warning("⚠️ Verifique as permissões de escrita na pasta do projeto.")

    # Status da correção - só exibir se o cálculo foi solicitado
    if calculo_foi_solicitado and tem_dados_calculados:
        st.success(f"✅ **Processamento concluído:** {len(st.session_state.df_final):,} registros processados")
    
    # Informações sobre o processo
    st.markdown("---")
    st.subheader("ℹ️ Informações sobre o Processo")
    
    with st.expander("⚙️ Etapas do Processo de Correção", expanded=False):
        st.info("""
        **0. Carregamento de Índices Econômicos**
        - Importação dos índices IGP-M/IPCA do arquivo Excel
        - Estrutura: Coluna A (Data) e Coluna F (Índice)
        - Histórico completo para cálculos de correção monetária
        
        **1. Cálculo de Aging**
        - Determinação do tempo decorrido desde o vencimento
        - Classificação em faixas de aging padrão
        - Aplicação de regras específicas para cada faixa
        
        **2. Correção Monetária com Índices do Excel**
        - Busca do índice de vencimento (data do vencimento)
        - Busca do índice base (data atual/base)
        - Cálculo do fator: índice_base / índice_vencimento
        - Aplicação da correção: valor_liquido × (fator - 1)
        
        **3. Aplicação de Taxa de Recuperação**
        - Cruzamento por Empresa, Tipo e Aging
        - Cálculo do valor recuperável: valor_corrigido × taxa
        
        **4. Cálculo do Valor Justo**
        - Desconto pelo prazo de recebimento
        - Aplicação de taxa de desconto (DI-PRE + spread)
        - Resultado: valor presente líquido esperado
        """)
    
    with st.expander("💡 Fórmulas Utilizadas", expanded=False):
        st.info("""
        **Correção Monetária (Nova Metodologia):**
        `fator_correcao_ate_data_base = indice_base / indice_vencimento`
        `valor_corrigido = valor_liquido × fator_correcao_ate_data_base`
        
        **Busca de Índices:**
        - `indice_vencimento`: Índice para o mês/ano da data de vencimento
        - `indice_base`: Índice para o mês/ano da data base (atual)
        - Fonte: Arquivo Excel carregado (colunas A e F)
        
        **Valor Recuperável:**
        `valor_recuperavel_ate_data_base = valor_corrigido × taxa_recuperacao`
        `valor_recuperavel_ate_recebimento = valor_corrigido × taxa_recuperacao × fator_correcao_ate_recebimento`

        **Valor Justo com DI-PRE:**
        `valor_justo = valor_corrigido * taxa_recuperacao * (fator_exponencial_di_pre + multa)`
        
        **Fator Exponencial DI-PRE:**
        `fator_exponencial_di_pre = (1 + taxa_di_pre)^(prazo_recebimento/12)`
        
        **Onde:**
        - `fator_correcao`: Baseado no índice IGP-M
        - `taxa_multa`: Taxa de multa configurada
        - `juros_acumulados`: Juros moratórios compostos
        - `taxa_recuperacao`: Taxa específica por empresa/tipo/aging
        - `taxa_di_pre`: Taxa DI-PRE específica para cada prazo (em meses)
        - `prazo_recebimento`: Prazo esperado em meses
        - `multa`: Multa adicional por atraso no recebimento
        
        **Processo de Matching DI-PRE:**
        - Para cada registro, busca no arquivo DI-PRE a taxa correspondente
        - Critério: `meses_futuros` == `prazo_recebimento`
        - Se não encontrar correspondência, usa taxa padrão de 0.5% ao mês
        """)

    # Adicionar botão na tela do Streamlit para limpar o cache
    if st.button("Limpar Cache"):
        st.cache_data.clear()
        st.success("Cache limpo com sucesso!")

if __name__ == "__main__":
    show()
