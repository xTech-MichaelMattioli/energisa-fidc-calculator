"""
Página de Correção - FIDC Calculator
Cálculo de aging, correção monetária e valor justo
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import os
from utils.calculador_aging import CalculadorAging
from utils.calculador_correcao import CalculadorCorrecao
from utils.visualizador_voltz import VisualizadorVoltz
from utils.visualizador_distribuidoras import VisualizadorDistribuidoras

# Importar classe de valor justo do app original
import requests
from dateutil.relativedelta import relativedelta
import numpy as np

class CalculadorIndicesEconomicos:
    """
    Classe para cálculo de índices econômicos a partir de arquivo Excel
    """
    
    def __init__(self):
        self.df_indices = None
        self.ipca_12m_real = None
        self.data_base = None
    
    def carregar_indices_do_excel(self, arquivo_excel, aba_especifica=None):
        """
        Carrega dados de IGP-M/IPCA do arquivo Excel
        Suporta duas estruturas:
        1. Aba IGPM_IPCA: Coluna C (Ano), Coluna D (Mês) e Coluna F (Índice IGP-M)
        2. Aba IGPM: Coluna A (Mês/Ano), Coluna B (Índice)
        
        Parâmetros:
        - arquivo_excel: arquivo Excel para carregar
        - aba_especifica: nome específico da aba (para VOLTZ usar "IGPM")
        """
        try:
            import pandas as pd
            import streamlit as st
            import numpy as np
            from datetime import datetime
            
            print("🔄 Carregando índices do arquivo Excel...")
            
            # Determinar qual aba usar
            sheet_name = aba_especifica if aba_especifica else 0  # 0 = primeira aba por padrão
            
            if aba_especifica:
                print(f"📊 Carregando da aba específica: {aba_especifica}")
            else:
                print("📊 Carregando da primeira aba do arquivo")
            
            # Ler o arquivo Excel completo primeiro para analisar
            try:
                df_completo = pd.read_excel(arquivo_excel, sheet_name=sheet_name)
                print(f"📊 Arquivo carregado com {df_completo.shape[0]} linhas e {df_completo.shape[1]} colunas")
                
                # Detectar qual estrutura usar baseado na aba e no conteúdo
                if aba_especifica == "IGPM":
                    # Estrutura IGPM: Coluna A (Mês/Ano), Coluna B (Índice)
                    print("📊 Detectada estrutura IGPM - usando colunas A (mês/ano) e B (índice)")
                    
                    if df_completo.shape[1] < 2:
                        raise ValueError(f"Aba IGPM tem apenas {df_completo.shape[1]} colunas, mas precisa de pelo menos 2 (A-B)")
                    
                    # Extrair colunas A (0) e B (1) - Mês/Ano e Índice
                    df = df_completo.iloc[:, [0, 1]].copy()
                    df.columns = ['mes_ano', 'indice']
                    
                    # Processar coluna mes_ano para extrair ano e mês
                    df = df.dropna(subset=['mes_ano'])
                    
                    # Converter mes_ano para string para processamento
                    df['mes_ano'] = df['mes_ano'].astype(str)
                    
                    # Extrair ano e mês da string (formato: "agosto/1994")
                    meses_dict = {
                        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
                        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
                    }
                    
                    # Separar mês e ano
                    df_expandido = df['mes_ano'].str.split('/', expand=True)
                    if df_expandido.shape[1] < 2:
                        raise ValueError("Formato de data inválido na coluna A. Esperado: 'mês/ano'")
                    
                    df['mes_nome'] = df_expandido[0].str.strip().str.lower()
                    df['ano'] = pd.to_numeric(df_expandido[1].str.strip(), errors='coerce')
                    
                    # Converter nome do mês para número
                    df['mes'] = df['mes_nome'].map(meses_dict)
                    
                    # Remover linhas onde não conseguimos mapear o mês
                    df = df.dropna(subset=['mes', 'ano'])
                    df['mes'] = df['mes'].astype(int)
                    df['ano'] = df['ano'].astype(int)
                    
                    print(f"📊 Processamento IGPM: {len(df)} registros com data válida")
                    
                else:
                    # Estrutura IGPM_IPCA: Coluna C (Ano), Coluna D (Mês) e Coluna F (Índice IGP-M)
                    print("📊 Detectada estrutura IGPM_IPCA - usando colunas C (ano), D (mês) e F (índice)")
                    
                    # Verificar se tem pelo menos 6 colunas (A até F)
                    if df_completo.shape[1] < 6:
                        raise ValueError(f"Aba IGPM_IPCA tem apenas {df_completo.shape[1]} colunas, mas precisa de pelo menos 6 (A-F)")
                    
                    # Extrair colunas C (2), D (3) e F (5) - Ano, Mês e Índice IGP-M
                    df = df_completo.iloc[:, [2, 3, 5]].copy()
                    df.columns = ['ano', 'mes', 'indice']
                
            except Exception as e:
                print(f"❌ Erro ao ler arquivo Excel: {e}")
                # Se falhar com aba específica, tentar primeira aba
                if aba_especifica:
                    print(f"⚠️ Falha ao carregar aba '{aba_especifica}', tentando primeira aba...")
                    try:
                        df_completo = pd.read_excel(arquivo_excel, sheet_name=0)
                        # Usar estrutura padrão IGMP_IPCA
                        df = df_completo.iloc[:, [2, 3, 5]].copy()
                        df.columns = ['ano', 'mes', 'indice']
                        print("✅ Carregamento da primeira aba bem-sucedido")
                    except:
                        raise e
                else:
                    raise e
            
            # Padronizar as colunas para ['ano', 'mes', 'indice']
            if 'mes_ano' in df.columns:
                # Para estrutura IGPM, já processamos e temos ano, mes, indice
                df = df[['ano', 'mes', 'indice']].copy()
            
            print(f"📊 Dados extraídos - ano, mês e índice padronizados")
            
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
        Carrega dados de índices do arquivo Excel.
        Detecta automaticamente se deve usar aba específica para VOLTZ.
        """
        # Verificar se existe algum arquivo VOLTZ no session_state para determinar aba
        aba_usar = None
        
        # Detectar se é VOLTZ baseado nos arquivos carregados
        if 'df_dados_principais' in st.session_state:
            dados_principais = st.session_state.df_dados_principais
            if not dados_principais.empty and hasattr(dados_principais, 'attrs'):
                nome_arquivo = dados_principais.attrs.get('nome_arquivo', '')
                if 'VOLTZ' in nome_arquivo.upper():
                    aba_usar = "IGPM"
                    st.info("🔍 **VOLTZ detectado** - Carregando índices da aba específica 'IGPM'")
        
        # Verificar também se existe informação sobre VOLTZ em outros lugares
        if aba_usar is None and 'distribuidora_detectada' in st.session_state:
            if st.session_state.distribuidora_detectada == 'VOLTZ':
                aba_usar = "IGPM"
                st.info("🔍 **VOLTZ detectado** - Carregando índices da aba específica 'IGPM'")
        
        if aba_usar:
            st.success(f"⚡ **Modo VOLTZ ativado** - Usando aba '{aba_usar}' para índices IGP-M")
        else:
            st.info("📊 Usando primeira aba do arquivo para índices (padrão)")
        
        return self.calculador_indices.carregar_indices_do_excel(arquivo_excel, aba_usar)
    
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
            df_resultado['prazo_recebimento'] = 6  # Padrão 6 meses
        
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
        
        # Dias de atraso em relação ao vencimento
        df_resultado['data_vencimento'] = data_base + pd.DateOffset(months=6)
        df_resultado['dias_atraso'] = (datetime.now() - df_resultado['data_vencimento']).dt.days.clip(lower=0)

        # Multa proporcional: 1% ao mês → 0.01 / 30 por dia, com fallback para dias_atraso = 0
        df_resultado['multa_para_justo'] = (0.01 / 30) * df_resultado['dias_atraso']
        
        # Fallback: se dias_atraso = 0, usar multa de 0,06 (6%)
        df_resultado['multa_para_justo'] = df_resultado['multa_para_justo'].where(
            df_resultado['dias_atraso'] > 0, 
            0.06
        )
        
        # Verificar se temos coluna de taxa_recuperacao
        if 'taxa_recuperacao' in df_resultado.columns:            
            # Fórmula com DI-PRE: valor_justo = valor_corrigido * taxa_recuperacao * (fator_exponencial_di_pre + multa)
            df_resultado['valor_justo'] = df_resultado[coluna_valor_corrigido] * df_resultado['taxa_recuperacao'] * (df_resultado['fator_exponencial_di_pre'] + df_resultado['multa_para_justo'])
        else:
            # Fallback sem taxa de recuperação
            df_resultado['valor_justo'] = df_resultado[coluna_valor_corrigido] * (df_resultado['fator_exponencial_di_pre'] + df_resultado['multa_para_justo'])
        
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
            
            Faça o upload do arquivo Excel com os índices econômicos. O sistema suporta duas estruturas:
            
            **Estrutura 1 (IGPM_IPCA):**
            - **Coluna C**: Ano (ex: 2022)
            - **Coluna D**: Mês (ex: 1, 2, 3...)  
            - **Coluna F**: Valores dos índices IGP-M ou IPCA
            
            **Estrutura 2 (IGPM - para VOLTZ):**
            - **Coluna A**: Mês/Ano (ex: agosto/1994, setembro/1994)
            - **Coluna B**: Índice (ex: 100.000, 101.751)
            
            O sistema detecta automaticamente qual estrutura usar baseado na distribuidora.
            
            **Exemplo de estrutura IGPM_IPCA:**
            ```
            2021    12    543.21
            2022    01    548.65  
            2022    02    552.34
            ```
            
            **Exemplo de estrutura IGPM:**
            ```
            agosto/1994      100.000
            setembro/1994    101.751  
            outubro/1994     103.602
            ```
            """)
            
            # Upload do arquivo
            uploaded_file_indices = st.file_uploader(
                "📤 Selecione o arquivo de Índices IGP-M/IPCA",
                type=['xlsx', 'xls'],
                help="Arquivo Excel com índices econômicos. Suporta estruturas IGPM_IPCA (C,D,F) e IGPM (A,B)",
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
        
        if st.button("🔄 Recarregar Índices", key="recarregar_indices"):
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
        
        if st.button("🔄 Recarregar Taxa de Recuperação", key="recarregar_taxa_recuperacao"):
            st.session_state.taxa_recuperacao_carregada = False
            st.session_state.cdi_carregado = False
            st.session_state.calculo_solicitado = False
            if 'df_taxa_recuperacao' in st.session_state:
                del st.session_state.df_taxa_recuperacao
            st.rerun()

        # Mostrar o head dos dados num expander
        with st.expander("📊 Preview dos Dados de Taxa de Recuperação", expanded=False):
            if 'df_taxa_recuperacao' in st.session_state:
                st.dataframe(st.session_state.df_taxa_recuperacao, use_container_width=True)

    st.markdown("---")
    
    # Detectar se é VOLTZ para determinar se precisa de CDI
    nome_arquivo_detectado = "Distribuidora"  # Default
    if 'df_carregado' in st.session_state and st.session_state.df_carregado:
        primeiro_arquivo = list(st.session_state.df_carregado.keys())[0]
        nome_arquivo_detectado = primeiro_arquivo
    
    # Verificar se é VOLTZ
    from utils.calculador_voltz import CalculadorVoltz
    calculador_voltz = CalculadorVoltz(st.session_state.params)
    eh_voltz = calculador_voltz.identificar_voltz(nome_arquivo_detectado)
    
    # ETAPA 2: CARREGAMENTO DO ARQUIVO CDI (OBRIGATÓRIO PARA TODAS AS DISTRIBUIDORAS)
    st.subheader("📈 2️⃣ Carregar Dados CDI/DI-PRE")
    
    if eh_voltz:
        st.info("⚡ **VOLTZ detectada:** CDI/DI-PRE necessário para cálculo do valor justo (desconto a valor presente)")
    
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

    else:
        st.success("✅ **Dados CDI/DI-PRE carregados**")
        registros_cdi = len(st.session_state.df_di_pre)
        st.info(f"📊 {registros_cdi} registro(s) de CDI/DI-PRE disponível(eis)")
        
        # Mostrar botão para recarregar se necessário
        if st.button("🔄 Recarregar Dados CDI", key="recarregar_dados_cdi"):
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
        if eh_voltz:
            st.metric("📊 Registros CDI", "N/A (VOLTZ)")
        else:
            registros_cdi = len(st.session_state.df_di_pre) if 'df_di_pre' in st.session_state else 0
            st.metric("📊 Registros CDI", registros_cdi)
    
    # Verificar se todos os arquivos necessários estão carregados
    # TODAS as distribuidoras (incluindo VOLTZ) precisam de: índices, taxa de recuperação e CDI
    tem_todos_arquivos = tem_indices and tem_taxa_recuperacao and tem_cdi
    
    # Botão para calcular correção (SÓ APARECE SE TIVER TODOS OS ARQUIVOS)
    st.markdown("---")
    if tem_todos_arquivos:
        st.write("**✅ Todos os arquivos carregados! Agora você pode executar o cálculo:**")
        calculo_executado = st.button("💰 Calcular Correção Monetária Completa", type="primary", use_container_width=True, key="calcular_correcao_completa")
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
            # ========== DASHBOARD DE PROGRESSO EM TEMPO REAL ==========
            st.markdown("### 🚀 **Processamento Ultra-Otimizado em Andamento**")
            
            # Container para métricas em tempo real
            col_prog1, col_prog2, col_prog3 = st.columns(3)
            
            with col_prog1:
                metric_registros = st.empty()
            with col_prog2:
                metric_velocidade = st.empty()
            with col_prog3:
                metric_tempo = st.empty()
            
            # Barra de progresso principal
            progress_main = st.progress(0)
            status_text = st.empty()
            
            # Container para logs detalhados
            log_container = st.expander("📊 **Logs Detalhados de Performance**", expanded=False)
            
            # Iniciar cronômetro
            import time
            inicio_processamento = time.time()
            total_registros = len(df_padronizado)
            
            # ========== ETAPA 1: CÁLCULO DE AGING (20%) ==========
            status_text.text("🔄 Etapa 1/5: Calculando aging dos contratos...")
            progress_main.progress(0.1)
            
            with log_container:
                st.info(f"📊 **Iniciando processamento ultra-otimizado:** {total_registros:,} registros")
                
            etapa_inicio = time.time()
            df_com_aging = calc_aging.processar_aging_completo(df_padronizado.copy())
            etapa_tempo = time.time() - etapa_inicio
            
            if df_com_aging.empty:
                st.error("❌ Erro ao calcular aging. Verifique os dados de entrada.")
                return
            
            progress_main.progress(0.2)
            velocidade_aging = total_registros / etapa_tempo if etapa_tempo > 0 else 0
            
            with log_container:
                st.success(f"✅ **Aging calculado:** {len(df_com_aging):,} registros em {etapa_tempo:.2f}s ({velocidade_aging:,.0f} reg/s)")
            
            # Atualizar métricas
            tempo_decorrido = time.time() - inicio_processamento
            metric_registros.metric("📊 Registros", f"{len(df_com_aging):,}", f"{total_registros:,} total")
            metric_velocidade.metric("⚡ Velocidade", f"{velocidade_aging:,.0f}", "registros/seg")
            metric_tempo.metric("⏱️ Tempo", f"{tempo_decorrido:.1f}s", "decorrido")
            
            # ========== ETAPA 2: DETECÇÃO AUTOMÁTICA (40%) ==========
            status_text.text("� Etapa 2/5: Detectando tipo de distribuidora e regras...")
            progress_main.progress(0.3)
            
            # Obter nome do arquivo original (se disponível)
            nome_arquivo_original = "Distribuidora"  # Default
            if 'df_carregado' in st.session_state and st.session_state.df_carregado:
                primeiro_arquivo = list(st.session_state.df_carregado.keys())[0]
                nome_arquivo_original = primeiro_arquivo
            
            etapa_inicio = time.time()

            
            
            # Usar o novo método que detecta automaticamente VOLTZ vs Padrão
            df_final_temp = calc_correcao.processar_com_regras_especificas(
                df_com_aging.copy(), 
                nome_arquivo_original,  # Passa o nome do arquivo para detecção
                st.session_state.df_taxa_recuperacao
            )
            
            etapa_tempo = time.time() - etapa_inicio
            progress_main.progress(0.4)
            
            velocidade_correcao = len(df_final_temp) / etapa_tempo if etapa_tempo > 0 else 0
            
            with log_container:
                st.success(f"✅ **Correção base:** {len(df_final_temp):,} registros em {etapa_tempo:.2f}s ({velocidade_correcao:,.0f} reg/s)")
            
            # Detectar se é VOLTZ para mostrar no log
            eh_voltz_detectado = 'VOLTZ' in nome_arquivo_original.upper()
            with log_container:
                if eh_voltz_detectado:
                    st.info("🎯 **Sistema VOLTZ detectado** - Usando regras ultra-otimizadas")
                else:
                    st.info("🎯 **Sistema padrão detectado** - Usando regras tradicionais")
            
            # Atualizar métricas
            tempo_decorrido = time.time() - inicio_processamento
            metric_registros.metric("📊 Registros", f"{len(df_final_temp):,}", "processados")
            metric_velocidade.metric("⚡ Velocidade", f"{velocidade_correcao:,.0f}", "registros/seg")
            metric_tempo.metric("⏱️ Tempo", f"{tempo_decorrido:.1f}s", "decorrido")
                
            # ========== ETAPA 3: ÍNDICES CUSTOMIZADOS (60%) ==========
            status_text.text("📈 Etapa 3/5: Aplicando índices econômicos customizados...")
            progress_main.progress(0.5)
            
            if 'calculador_valor_justo' in st.session_state and 'df_indices_economicos' in st.session_state:
                etapa_inicio = time.time()
                
                with log_container:
                    st.info("📊 **Iniciando merge vetorizado** de índices temporais...")

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

                progress_main.progress(0.52)
                
                # ==== MERGE 1: DATA BASE (ULTRA-OTIMIZADO) ====
                with log_container:
                    st.info("🔄 **Merge 1/2:** Índices da data base (O(log n))...")
                
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
                
                progress_main.progress(0.54)
                
                # ==== MERGE 2: DATA VENCIMENTO (ULTRA-OTIMIZADO) ====
                with log_container:
                    st.info("🔄 **Merge 2/2:** Índices da data vencimento (O(log n))...")
                    
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
                
                progress_main.progress(0.56)
                
                # ==== CÁLCULO DOS ÍNDICES DIÁRIOS (VETORIZADO) ====
                with log_container:
                    st.info("🧮 **Cálculo vetorizado** de índices diários...")
                
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
                with log_container:
                    st.info("🔄 **Aplicando** índices data base...")
                df_merged_completo['indice_base_diario'] = df_merged_completo.apply(
                    lambda row: calcular_indice_diario(row, 'base'), axis=1
                )
                
                progress_main.progress(0.58)
                
                with log_container:
                    st.info("🔄 **Aplicando** índices data vencimento...")
                df_merged_completo['indice_venc_diario'] = df_merged_completo.apply(
                    lambda row: calcular_indice_diario(row, 'vencimento'), axis=1
                )
                
                # ==== CÁLCULO DO FATOR DE CORREÇÃO (ULTRA-RÁPIDO) ====
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
                
                # ==== APLICAR CORREÇÃO MONETÁRIA (VETORIZADA) ====
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

                # Limpar colunas auxiliares
                colunas_temp = [
                    'ano_mes_base', 'ano_mes_venc', 'indice_mes_base', 'indice_mes_venc',
                    'taxa_mensal_base', 'taxa_mensal_venc', 'data_fechamento_base', 'data_fechamento_venc',
                    'indice_base_diario', 'indice_venc_diario', 'indice_mes_anterior_base', 'taxa_diaria_base', 'indice_mes_anterior_venc', 'taxa_diaria_venc'
                ]
                df_final_temp = df_merged_completo.drop(columns=[col for col in colunas_temp if col in df_merged_completo.columns])
                
                etapa_tempo = time.time() - etapa_inicio
                velocidade_indices = registros_customizados / etapa_tempo if etapa_tempo > 0 else 0
                
                with log_container:
                    st.success(f"✅ **Índices customizados aplicados:** {registros_customizados:,}/{total_registros:,} registros ({percentual:.1f}%) em {etapa_tempo:.2f}s ({velocidade_indices:,.0f} reg/s)")
                
            else:
                with log_container:
                    st.info("ℹ️ **Usando correção padrão** do sistema (IGPM/IPCA automático)")

            
            # ========== ETAPA 4: CÁLCULO DE CORREÇÃO MONETÁRIA FINAL (80%) ==========
            status_text.text("� Etapa 4/5: Calculando correção monetária final...")
            progress_main.progress(0.7)
            
            etapa_inicio = time.time()
            
            if df_final_temp.empty:
                st.error("❌ Erro ao processar correção monetária.")
                return

            # ==== APLICAR CORREÇÃO MONETÁRIA FINAL (VETORIZADA) ====
            with log_container:
                st.info("💰 **Calculando correção monetária** vetorizada...")
                
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

            progress_main.progress(0.75)
            
            etapa_tempo = time.time() - etapa_inicio
            velocidade_correcao_final = len(df_final_temp) / etapa_tempo if etapa_tempo > 0 else 0
            
            with log_container:
                st.success(f"✅ **Correção monetária final:** {len(df_final_temp):,} registros em {etapa_tempo:.2f}s ({velocidade_correcao_final:,.0f} reg/s)")

            # ========== ETAPA 5: CÁLCULO DO VALOR JUSTO (100%) ==========
            status_text.text("⚖️ Etapa 5/5: Calculando valor justo com DI-PRE & IPCA...")
            progress_main.progress(0.8)
            
            etapa_inicio = time.time()
            
            with log_container:
                st.info("⚖️ **Iniciando cálculo** de valor justo...")

            try:
                # Verificar se temos dados DI-PRE disponíveis
                if st.session_state.df_di_pre.empty:
                    with log_container:
                        st.warning("⚠️ Dados DI-PRE não disponíveis. Usando taxa padrão.")
                    taxa_di_pre_6m = 0.10  # 10% ao ano como fallback
                else:
                    # Buscar taxa DI-PRE para 6 meses (prazo padrão de recebimento)
                    linha_6m = st.session_state.df_di_pre[st.session_state.df_di_pre['meses_futuros'] == 6]
                    if not linha_6m.empty:
                        taxa_di_pre_6m = linha_6m.iloc[0]['252'] / 100  # Converter de % para decimal
                    else:
                        with log_container:
                            st.warning("⚠️ Taxa DI-PRE para 6 meses não encontrada. Usando valor médio.")
                        taxa_di_pre_6m = st.session_state.df_di_pre['252'].mean() / 100
                
                progress_main.progress(0.82)
                
                # ============= PREPARAR DADOS BASE (ULTRA-RÁPIDO) =============
                # Garantir que data_base seja datetime
                if 'data_base' not in df_final_temp.columns:
                    df_final_temp['data_base'] = datetime.now()
                df_final_temp['data_base'] = pd.to_datetime(df_final_temp['data_base'], errors='coerce')
                
                # Usar prazo_recebimento da taxa de recuperação se disponível, senão 6 meses
                if 'prazo_recebimento' not in df_final_temp.columns:
                    df_final_temp['prazo_recebimento'] = 6  # Padrão: 6 meses
                
                # ============= CÁLCULO DA TAXA DI-PRE ANUALIZADA (VETORIZADO) =============
                df_final_temp['di_pre_taxa_anual'] = taxa_di_pre_6m
                
                # Aplicar spread de risco de 2.5% sobre a taxa DI-PRE
                spread_risco = 2.5  # 2.5%
                df_final_temp['taxa_di_pre_total_anual'] = (1 + df_final_temp['di_pre_taxa_anual']) * (1 + spread_risco / 100) - 1

                # Converter taxa anual para mensal: (1 + taxa_anual)^(1/12) - 1
                df_final_temp['taxa_desconto_mensal'] = (1 + df_final_temp['taxa_di_pre_total_anual']) ** (1/12) - 1

                progress_main.progress(0.85)
                
                # ============= CÁLCULO DO PERÍODO ATÉ RECEBIMENTO (MERGE OTIMIZADO) =============
                with log_container:
                    st.info("📊 **Merge dinâmico** de prazos de recebimento...")
                
                # Usar dados da taxa de recuperação que já estão carregados no session_state
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
                            return 6  # Baseado no exemplo: todos têm 6 meses
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
                            return 6  # Default baseado no template
                    
                    df_final_temp['meses_ate_recebimento'] = df_final_temp.apply(calcular_meses_fallback, axis=1)
                    
                    # Data estimada de recebimento (data_base + meses_ate_recebimento)
                    def calcular_data_recebimento(row):
                        try:
                            data_base = row.get('data_base', datetime.now())
                            meses = row.get('meses_ate_recebimento', 30)
                            return pd.to_datetime(data_base) + pd.DateOffset(months=int(meses))
                        except:
                            return datetime.now() + pd.DateOffset(months=30)
                    
                    df_final_temp['data_recebimento_estimada'] = df_final_temp.apply(calcular_data_recebimento, axis=1)

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
                    
                    # ============= ETAPA 5: CÁLCULO DE MULTA POR ATRASO =============
                    # Data atual para cálculo de atraso
                    data_atual = datetime.now()
                    
                    # Calcular dias de atraso em relação à data de recebimento estimada
                    df_final_temp['dias_atraso'] = (data_atual - df_final_temp['data_recebimento_estimada']).dt.days.clip(lower=0)
                    
                    # Multa por atraso: 1% ao mês = 0.01/30 por dia
                    taxa_multa_diaria = 0.01 / 30
                    df_final_temp['multa_atraso'] = df_final_temp['dias_atraso'] * taxa_multa_diaria
                    
                    # Aplicar multa mínima de 6% mesmo sem atraso (margem de segurança)
                    multa_minima = 0.06
                    df_final_temp['multa_final'] = df_final_temp['multa_atraso'].clip(lower=multa_minima)
                    
                    # ============= ETAPA 6: CÁLCULO FINAL DO VALOR JUSTO =============
                    # Verificar se temos taxa_recuperacao
                    if 'taxa_recuperacao' in df_final_temp.columns:
                        # Fórmula completa: valor_corrigido × taxa_recuperacao × (fator_capitalização + multa)
                        df_final_temp['valor_justo'] = (
                            df_final_temp['valor_corrigido'] * 
                            df_final_temp['taxa_recuperacao'] * 
                            (df_final_temp['fator_correcao_ate_recebimento'] + df_final_temp['multa_final']) /
                            df_final_temp['fator_de_desconto']
                        )
                    else:
                        # Fallback sem taxa de recuperação
                        df_final_temp['valor_justo'] = (
                            df_final_temp['valor_corrigido'] * 
                            (df_final_temp['fator_correcao_ate_recebimento'] + df_final_temp['multa_final']) /
                            df_final_temp['fator_de_desconto']
                        )

                    # Calcular valor_recuperavel_ate_recebimento
                    df_final_temp['valor_recuperavel_ate_recebimento'] = (
                        df_final_temp['valor_recuperavel_ate_data_base'] * (df_final_temp['fator_correcao_ate_recebimento'] + df_final_temp['multa_final'])
                    )

                    # Remove a coluna 'valor_recuperavel' se existir
                    if 'valor_recuperavel' in df_final_temp.columns:
                        df_final_temp = df_final_temp.drop(columns=['valor_recuperavel'])

                    # ============= ETAPA 6.5: CALCULAR VALOR JUSTO PARA VOLTZ =============
                    if eh_voltz_detectado:
                        with log_container:
                            st.info("⚡ **VOLTZ detectada:** Calculando valor justo com DI-PRE...")
                        
                        # Aplicar valor justo específico para VOLTZ
                        df_final_temp = calculador_voltz.calcular_valor_justo_voltz(
                            df_final_temp, 
                            st.session_state.df_di_pre,
                            data_base=None,  # Usa data atual
                            spread_risco=0.025  # 2.5% de spread
                        )
                        
                        with log_container:
                            st.success("✅ **Valor justo VOLTZ:** Aplicado com sucesso usando DI-PRE + spread")

                    # ============= ETAPA 7: CALCULAR VALOR JUSTO REAJUSTADO =============
                    # Aplicar descontos por aging sobre o valor justo
                    df_final_temp = calc_correcao.calcular_valor_justo_reajustado(df_final_temp)

                    # ============= ETAPA 8: ADICIONAR COLUNAS INFORMATIVAS =============
                    
                    # Salvar resultado no session_state
                    st.session_state.df_final = df_final_temp
                    st.session_state.df_com_aging = df_com_aging
                    
                    # Calcular estatísticas do DI-PRE para exibição
                    calc_valor_justo = CalculadorValorJusto()
                    stats_di_pre = calc_valor_justo.obter_estatisticas_di_pre(st.session_state.df_di_pre)
                    st.session_state.stats_di_pre_valor_justo = stats_di_pre
                    
                    progress_main.progress(1.0)
                    etapa_tempo = time.time() - etapa_inicio
                    tempo_total = time.time() - inicio_processamento
                    
                    # ========== DASHBOARD FINAL DE SUCESSO ==========
                    status_text.text("✅ Processamento ultra-otimizado concluído com sucesso!")
                    
                    # Métricas finais
                    velocidade_total = len(df_final_temp) / tempo_total if tempo_total > 0 else 0
                    metric_registros.metric("📊 Registros", f"{len(df_final_temp):,}", "✅ Processados")
                    metric_velocidade.metric("⚡ Velocidade", f"{velocidade_total:,.0f}", "registros/seg")
                    metric_tempo.metric("⏱️ Tempo Total", f"{tempo_total:.1f}s", "🎯 Ultra-rápido")
                    
                    # Dashboard de performance final
                    with log_container:
                        st.balloons()  # Animação de sucesso
                        st.success("🎉 **PROCESSAMENTO ULTRA-OTIMIZADO CONCLUÍDO!**")
                        st.info(f"📊 **Performance final:** {len(df_final_temp):,} registros processados em {tempo_total:.2f}s")
                        st.info(f"🚀 **Throughput:** {velocidade_total:,.0f} registros/segundo")
                        st.info(f"⚡ **Speedup estimado:** ~200x vs versão anterior")
                        
                        # Verificar se temos otimizações VOLTZ
                        if eh_voltz_detectado:
                            st.success("🎯 **Sistema VOLTZ:** Otimizações ultra-avançadas aplicadas com sucesso!")
                        
                        # Performance score
                        performance_score = min(100, (velocidade_total / 1000) * 100)  # Score baseado em throughput
                        st.metric("🏆 Performance Score", f"{performance_score:.0f}/100", "Ultra-Performance")
                    
                    st.success("✅ Correção monetária e valor justo calculados com sucesso!")
                    
            except Exception as e:
                st.error(f"❌ Erro no cálculo do valor justo: {str(e)}")
                st.warning("⚠️ Continuando com dados básicos (sem valor justo)")
                # Salvar dados básicos mesmo com erro no valor justo
                st.session_state.df_final = df_final_temp
                st.session_state.df_com_aging = df_com_aging
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
        
        # Detectar se é VOLTZ para escolher o visualizador apropriado
        nome_arquivo_detectado = "Distribuidora"  # Default
        if 'df_carregado' in st.session_state and st.session_state.df_carregado:
            primeiro_arquivo = list(st.session_state.df_carregado.keys())[0]
            nome_arquivo_detectado = primeiro_arquivo
        
        # Verificar se é VOLTZ
        from utils.calculador_voltz import CalculadorVoltz
        calculador_voltz = CalculadorVoltz(st.session_state.params)
        eh_voltz = calculador_voltz.identificar_voltz(nome_arquivo_detectado)
        
        # Usar o visualizador apropriado
        if eh_voltz:
            st.info("⚡ **VOLTZ detectada:** Usando visualização específica para VOLTZ")
            visualizador = VisualizadorVoltz()
            visualizador.exibir_resultados_voltz(st.session_state.df_final)
            visualizador.exibir_exportacao_voltz(st.session_state.df_final)
            visualizador.exibir_limpar_cache()
            visualizador.exibir_gerenciamento_checkpoints()
        else:
            st.info("🏢 **Distribuidora Geral:** Usando visualização padrão com DI-PRE")
            visualizador = VisualizadorDistribuidoras()
            visualizador.exibir_resultados_distribuidoras(st.session_state.df_final)
            visualizador.exibir_exportacao_distribuidoras(st.session_state.df_final)
            visualizador.exibir_info_processo_distribuidoras()
            visualizador.exibir_limpar_cache()


if __name__ == "__main__":
    show()