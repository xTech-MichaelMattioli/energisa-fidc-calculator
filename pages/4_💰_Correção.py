"""
Página de Correção - FIDC Calculator
Cálculo de aging, correção monetária e valor justo
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
from utils.calculador_aging import CalculadorAging
from utils.calculador_correcao import CalculadorCorrecao

# Importar classe de valor justo do app original
import requests
from dateutil.relativedelta import relativedelta
import numpy as np

class CalculadorValorJusto:
    """
    Classe para cálculo do valor justo integrando IPCA do Banco Central
    """
    
    def __init__(self):
        self.df_ipca = None
        self.ipca_12m_real = None
        self.data_base = None
    
    def get_ipca_mensal(self):
        """
        Obtém dados mensais do IPCA via API do Banco Central
        """
        try:
            print("🔄 Buscando dados do IPCA via API Banco Central...")
            url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.16121/dados?formato=json"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            df = pd.DataFrame(response.json())
            df['data'] = pd.to_datetime(df['data'], dayfirst=True)
            df['valor'] = df['valor'].astype(float) / 100  # Converter para escala 0-1
            
            self.df_ipca = df.sort_values('data')
            print(f"✅ {len(df)} registros de IPCA carregados")
            return self.df_ipca
            
        except Exception as e:
            print(f"❌ Erro ao carregar IPCA: {e}")
            # Dados fallback (últimos valores conhecidos)
            dados_fallback = [
                {'data': '01/08/2024', 'valor': 0.0038},
                {'data': '01/09/2024', 'valor': 0.0044},
                {'data': '01/10/2024', 'valor': 0.0056},
                {'data': '01/11/2024', 'valor': 0.0039},
                {'data': '01/12/2024', 'valor': 0.0052},
                {'data': '01/01/2025', 'valor': 0.0016},
                {'data': '01/02/2025', 'valor': 0.0131},
                {'data': '01/03/2025', 'valor': 0.0056},
                {'data': '01/04/2025', 'valor': 0.0043},
                {'data': '01/05/2025', 'valor': 0.0026},
                {'data': '01/06/2025', 'valor': 0.0024},
                {'data': '01/07/2025', 'valor': 0.0031}
            ]
            
            df = pd.DataFrame(dados_fallback)
            df['data'] = pd.to_datetime(df['data'], dayfirst=True)
            df['valor'] = df['valor'].astype(float)
            
            self.df_ipca = df.sort_values('data')
            print(f"⚠️ Usando dados fallback: {len(df)} registros")
            return self.df_ipca
    
    def calcular_12m_mensal(self, base_date):
        """
        Calcula IPCA acumulado nos últimos 12 meses
        """
        if self.df_ipca is None:
            self.get_ipca_mensal()
        
        base_period = pd.Period(base_date, freq='M')
        df_temp = self.df_ipca.copy()
        df_temp['periodo'] = df_temp['data'].dt.to_period('M')
        
        # Filtrar dados até a data base
        df_base = df_temp[df_temp['periodo'] <= base_period]
        
        if df_base.empty or len(df_base) < 12:
            print(f"⚠️ Dados insuficientes. Usando últimos {len(df_base)} meses disponíveis")
            ultimos_dados = df_base.tail(min(12, len(df_base)))
        else:
            # Pegar últimos 12 meses
            base_idx = df_base.index[-1]
            idx_inicio = max(0, base_idx - 11)  # 12 meses = posições i-11 até i
            ultimos_dados = df_base.iloc[idx_inicio:base_idx + 1]
        
        # Calcular fator composto
        valores = ultimos_dados['valor']
        fator = (1 + valores).prod()
        ipca_12m = fator - 1
        
        self.ipca_12m_real = ipca_12m
        self.data_base = base_date
        
        print(f"📊 IPCA 12 meses até {base_date.strftime('%m/%Y')}: {ipca_12m * 100:.2f}%")
        print(f"📅 Período analisado: {ultimos_dados['data'].min().strftime('%m/%Y')} a {ultimos_dados['data'].max().strftime('%m/%Y')}")
        
        return ipca_12m
    
    def calcular_valor_justo(self, df_corrigido, coluna_valor_corrigido='valor_corrigido', data_base=None):
        """
        Calcula valor justo aplicando IPCA com progressão exponencial sobre valor corrigido
        """
        if data_base is None:
            data_base = datetime.now()
        
        # Calcular IPCA 12 meses
        ipca_12m = self.calcular_12m_mensal(data_base)
        
        # Aplicar IPCA sobre valor corrigido com taxa de recuperação e progressão exponencial
        df_resultado = df_corrigido.copy()
        df_resultado['ipca_12m_real'] = ipca_12m
        df_resultado['ipca_mensal'] = (1 + ipca_12m) ** (1/12) - 1
        df_resultado['mês_recebimento'] = 6
        df_resultado['fator_exponencial'] = (1 + df_resultado['ipca_mensal']) ** df_resultado['mês_recebimento']
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
        
        # Verificar se temos coluna de taxa_recuperacao e prazo_recebimento
        if 'taxa_recuperacao' in df_resultado.columns:            
            # Fórmula com progressão exponencial: valor_justo = valor_corrigido * An * taxa_recuperacao
            df_resultado['valor_justo'] = df_resultado[coluna_valor_corrigido] * df_resultado['taxa_recuperacao'] * (df_resultado['fator_exponencial'] + df_resultado['multa_para_justo'])
        else:
            # Fallback sem taxa de recuperação: valor_justo = valor_corrigido * (1 + df_resultado['ipca_mensal'])
            df_resultado['valor_justo'] = df_resultado[coluna_valor_corrigido] * (df_resultado['fator_exponencial'] + df_resultado['multa_para_justo'])
        
        return df_resultado
    
    def obter_estatisticas_ipca(self):
        """
        Retorna estatísticas do IPCA calculado incluindo informações sobre progressão exponencial
        """
        if self.ipca_12m_real is None:
            return None
        
        return {
            'ipca_12m_percentual': self.ipca_12m_real * 100,
            'data_base': self.data_base,
            'fator_multiplicador': 1 + self.ipca_12m_real,
            'total_registros_ipca': len(self.df_ipca) if self.df_ipca is not None else 0,
            'formula_exponencial': 'An = (1 + ipca_12m)^n',
            'descricao_n': 'n = prazo_recebimento (em anos)'
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
                        aging_labels = ["A vencer", "Primeiro ano", "Segundo ano", "Terceiro ano", "Demais anos"]
                        
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
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Registros a Processar", f"{len(df_padronizado):,}")
    
    with col2:
        empresas_dados = df_padronizado['empresa'].nunique() if 'empresa' in df_padronizado.columns else 0
        st.metric("🏢 Empresas nos Dados", empresas_dados)
    
    with col3:
        empresas_taxa = st.session_state.df_taxa_recuperacao['Empresa'].nunique()
        st.metric("🏢 Empresas com Taxa", empresas_taxa)
    
    with col4:
        registros_taxa = len(st.session_state.df_taxa_recuperacao)
        st.metric("📈 Registros de Taxa", registros_taxa)
    
    with col5:
        registros_cdi = len(st.session_state.df_di_pre)
        st.metric("📊 Registros CDI", registros_cdi)
    
    # Botão para calcular correção (SÓ APARECE SE TIVER TAXA E CDI)
    st.markdown("---")
    st.write("**Todos os arquivos carregados! Agora você pode executar o cálculo:**")
    calculo_executado = st.button("💰 Calcular Correção Monetária Completa", type="primary", use_container_width=True)
    
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
                
                # Sempre usar método com taxa de recuperação (já que é obrigatória)
                df_final_temp = calc_correcao.processar_correcao_completa_com_recuperacao(
                    df_com_aging.copy(), 
                    "Distribuidora", 
                    st.session_state.df_taxa_recuperacao
                )
                
                if df_final_temp.empty:
                    st.error("❌ Erro ao processar correção monetária.")
                    return
                
                # Calcular valor justo usando IPCA
                with st.spinner("💎 Calculando valor justo com IPCA..."):
                    calculadora_valor_justo = CalculadorValorJusto()
                    
                    # Usar data atual como base
                    data_base = datetime.now()
                    
                    # Calcular valor justo
                    df_final = calculadora_valor_justo.calcular_valor_justo(
                        df_final_temp, 
                        coluna_valor_corrigido='valor_corrigido',
                        data_base=data_base
                    )
                    
                    # Armazenar informações do IPCA para exibição
                    stats_ipca = calculadora_valor_justo.obter_estatisticas_ipca()
                    st.session_state.stats_ipca_valor_justo = stats_ipca
                
                # Salvar resultado final
                st.session_state.df_com_aging = df_com_aging
                df_final = df_final.dropna(subset=['empresa'])
                st.session_state.df_final = df_final
                
                st.success("✅ Correção monetária e valor justo calculados com sucesso!")
                # Remover st.rerun() para evitar execução automática
                    
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
        
        # Exibir informações do IPCA usado no cálculo
        if 'stats_ipca_valor_justo' in st.session_state and st.session_state.stats_ipca_valor_justo:
            stats = st.session_state.stats_ipca_valor_justo
            
            with st.expander("📊 Informações do IPCA para Valor Justo", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "📅 Data Base IPCA",
                        stats['data_base'].strftime('%d/%m/%Y'),
                        help="Data de referência para cálculo do IPCA 12 meses"
                    )
                
                with col2:
                    st.metric(
                        "📊 IPCA 12 Meses",
                        f"{stats['ipca_12m_percentual']:.2f}%",
                        help="Taxa IPCA acumulada nos últimos 12 meses"
                    )
                
                with col3:
                    st.metric(
                        "🔢 Fator Base IPCA",
                        f"{stats['fator_multiplicador']:.4f}",
                        help="Fator base para progressão exponencial: (1 + ipca_12m)"
                    )
                
                with col4:
                    st.metric(
                        "📈 Total Registros IPCA",
                        stats['total_registros_ipca'],
                        help="Quantidade de períodos de IPCA utilizados no cálculo"
                    )
                
                st.info(f"""
                **💡 Fórmula do Valor Justo com Progressão Exponencial:**  
                `valor_justo = valor_corrigido × An × taxa_recuperacao`  
                
                **🧮 Onde:**  
                - `An = (1 + ipca_12m_real)^n` (Progressão exponencial)  
                - `n = prazo_recebimento` (em anos)  
                - `ipca_12m_real`: {stats['ipca_12m_percentual']:.2f}% (já na escala 0-1 = {stats['ipca_12m_percentual']/100:.4f})  
                - `fator_base`: {stats['fator_multiplicador']:.4f}  
                - `taxa_recuperacao`: Taxa de recuperação específica por aging e tipo  
                
                **📊 Exemplos de cálculo:**  
                - Se n=1 ano: An = {stats['fator_multiplicador']:.4f}^1 = {stats['fator_multiplicador']:.4f}  
                - Se n=2 anos: An = {stats['fator_multiplicador']:.4f}^2 = {stats['fator_multiplicador']**2:.4f}  
                - Se n=3 anos: An = {stats['fator_multiplicador']:.4f}^3 = {stats['fator_multiplicador']**3:.4f}  
                
                **🎯 Para valor_corrigido = R$ 1.000,00, n=2 anos, taxa_recuperacao = 85%:**  
                valor_justo = R$ 1.000,00 × {stats['fator_multiplicador']**2:.4f} × 0,85 = R$ {1000 * (stats['fator_multiplicador']**2) * 0.85:,.2f}
                """)
        
        # Verificar se temos colunas de taxa de recuperação e valor justo
        colunas_taxa = ['aging_taxa', 'taxa_recuperacao', 'prazo_recebimento', 'valor_recuperavel']
        tem_colunas_recuperacao = all(col in st.session_state.df_final.columns for col in colunas_taxa)
        
        colunas_valor_justo = ['ipca_12m_real', 'fator_exponencial', 'valor_justo']
        tem_colunas_valor_justo = all(col in st.session_state.df_final.columns for col in colunas_valor_justo)
        
        if tem_colunas_recuperacao and tem_colunas_valor_justo:
            st.success("✅ **Resultados completos:** Taxa de recuperação + Valor justo com IPCA")
        elif tem_colunas_recuperacao:
            st.warning("⚠️ **Resultados parciais:** Apenas taxa de recuperação (sem valor justo)")
        elif tem_colunas_valor_justo:
            st.warning("⚠️ **Resultados parciais:** Apenas valor justo (sem taxa de recuperação)")
        else:
            st.warning("⚠️ **Resultados básicos:** Sem taxa de recuperação nem valor justo")
        
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
        colunas_agg_1 = {'valor_corrigido': 'sum'}
        
        if tem_colunas_recuperacao:
            colunas_agg_1.update({
                'taxa_recuperacao': 'mean',
                'valor_recuperavel': 'sum'
            })
        
        if tem_colunas_valor_justo:
            colunas_agg_1.update({
                'valor_justo': 'sum',
                'ipca_12m_real': 'mean'
            })
        
        df_agg1 = (
            st.session_state.df_final
            .groupby(['empresa', 'tipo', 'classe', 'status', 'situacao', 'aging', 'aging_taxa'], dropna=False)
            .agg(colunas_agg_1)
            .reset_index()
        )

        df_agg1['aging'] = pd.Categorical(df_agg1['aging'], categories=ordem_aging, ordered=True)
        df_agg1 = df_agg1.sort_values(['empresa', 'tipo', 'classe', 'status', 'situacao', 'aging'])

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
            colunas_agg_2['valor_recuperavel'] = 'sum'
        
        if tem_colunas_valor_justo:
            colunas_agg_2['valor_justo'] = 'sum'
        
        df_agg2 = (
            st.session_state.df_final
            .groupby(['empresa', 'aging', 'aging_taxa'], dropna=False)
            .agg(colunas_agg_2)
            .reset_index()
        )

        df_agg2['aging'] = pd.Categorical(df_agg2['aging'], categories=ordem_aging, ordered=True)
        df_agg2 = df_agg2.sort_values(['empresa', 'aging'])

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
            colunas_agg_3['valor_recuperavel'] = 'sum'
        
        if tem_colunas_valor_justo:
            colunas_agg_3['valor_justo'] = 'sum'
        
        df_agg3 = (
            st.session_state.df_final
            .groupby(['aging', 'aging_taxa'], dropna=False)
            .agg(colunas_agg_3)
            .reset_index()
        )

        df_agg3['aging'] = pd.Categorical(df_agg3['aging'], categories=ordem_aging, ordered=True)
        df_agg3 = df_agg3.sort_values(['aging'])

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
            colunas_resumo_empresa['valor_recuperavel'] = 'sum'
        
        if tem_colunas_valor_justo:
            colunas_resumo_empresa['valor_justo'] = 'sum'
        
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
            colunas_valor.append('valor_recuperavel')
        if tem_colunas_valor_justo:
            colunas_valor.append('valor_justo')
        
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
            nomes_colunas['valor_recuperavel'] = '🎯 Valor Recuperável'
        
        if tem_colunas_valor_justo:
            nomes_colunas['valor_justo'] = '💎 Valor Justo'
        
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
            total_recuperavel = df_resumo_empresa['valor_recuperavel'].sum()
        else:
            total_recuperavel = 0
        
        if tem_colunas_valor_justo:
            total_valor_justo = df_resumo_empresa['valor_justo'].sum()
        else:
            total_valor_justo = 0
        
        # Criar colunas para as métricas (adaptar quantidade baseado no que temos)
        if tem_colunas_valor_justo:
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
                    "💎 Valor Justo Total",
                    f"R$ {total_valor_justo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    help="Soma total dos valores justos (corrigido + IPCA + taxa recuperação)"
                )
        
        # Exportação Automática dos Dados Brutos
        st.markdown("---")
        st.subheader("💾 Exportação Automática dos Dados Brutos")
        
        try:
            # Criar diretório data se não existir
            data_dir = os.path.join(os.getcwd(), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo_csv = f"FIDC_Dados_Brutos_{timestamp}.csv"
            
            # Caminhos completos
            caminho_csv = os.path.join(data_dir, nome_arquivo_csv)
            
            # Exportar CSV
            csv_export = st.session_state.df_final.copy(deep=True)
            csv_export['data_vencimento'] = pd.to_datetime(csv_export['data_vencimento'], errors='coerce')  # Converter para datetime
            csv_export.to_csv(caminho_csv, index=False, encoding='utf-8-sig')
            
            # Feedback para o usuário
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                st.success(f"✅ **CSV exportado:**\n`{nome_arquivo_csv}`")
                st.info(f"📊 **{len(st.session_state.df_final):,} registros** exportados")
            
            with col_export2:
                st.info(f"""
                **📋 Localização:**
                `{data_dir}`
                
                **📄 Conteúdo:**
                - Todos os registros processados
                - Aging calculado
                - Correção monetária aplicada
                - Taxa de recuperação aplicada
                - Valor justo com IPCA
                """)
            
            # Informações adicionais sobre os arquivos exportados
            st.markdown("---")
            st.info(f"""
            **📋 Dados exportados automaticamente:**
            - **Formato:** CSV
            - **Localização:** `{data_dir}`
            - **Conteúdo:** Todos os registros do df_final (dados brutos linha a linha)
            - **Encoding:** UTF-8 com BOM (compatível com Excel brasileiro)
            - **Total de registros:** {len(st.session_state.df_final):,}
            - **Total de colunas:** {len(st.session_state.df_final.columns)}
            """)
            
        except Exception as e:
            st.error(f"❌ Erro na exportação automática: {str(e)}")
            st.warning("⚠️ Verifique as permissões de escrita na pasta do projeto.")
    
    # Status da correção - só exibir se o cálculo foi solicitado
    if calculo_foi_solicitado and tem_dados_calculados:
        st.success(f"✅ **Processamento concluído:** {len(st.session_state.df_final):,} registros processados")
    
    # Informações sobre o processo
    st.markdown("---")
    st.subheader("ℹ️ Informações sobre o Processo")
    
    with st.expander("⚙️ Etapas do Processo de Correção", expanded=False):
        st.info("""
        **1. Cálculo de Aging**
        - Determinação do tempo decorrido desde o vencimento
        - Classificação em faixas de aging padrão
        - Aplicação de regras específicas para cada faixa
        
        **2. Correção Monetária**
        - Aplicação de índices de correção (IGP-M)
        - Cálculo de juros moratórios
        - Aplicação de multas por inadimplência
        
        **3. Taxa de Recuperação**
        - Aplicação de taxas específicas por empresa e tipo
        - Consideração do prazo de recebimento esperado
        - Ajuste por faixa de aging
        
        **4. Valor Justo com IPCA**
        - Aplicação do IPCA acumulado 12 meses
        - Progressão exponencial baseada no prazo
        - Cálculo final considerando todos os fatores
        """)
    
    with st.expander("💡 Fórmulas Utilizadas", expanded=False):
        st.info("""
        **Valor Corrigido:**
        `valor_corrigido = valor_liquido × fator_correcao × (1 + taxa_multa) × (1 + juros_acumulados)`
        
        **Valor Recuperável:**
        `valor_recuperavel = valor_corrigido × taxa_recuperacao`
        
        **Valor Justo:**
        `valor_justo = valor_corrigido × taxa_recuperacao × fator_exponencial_ipca`
        
        **Fator Exponencial IPCA:**
        `fator_exponencial = (1 + ipca_12m)^(prazo_recebimento/12)`
        
        **Onde:**
        - `fator_correcao`: Baseado no índice IGP-M
        - `taxa_multa`: Taxa de multa configurada
        - `juros_acumulados`: Juros moratórios compostos
        - `taxa_recuperacao`: Taxa específica por empresa/tipo/aging
        - `ipca_12m`: IPCA acumulado 12 meses
        - `prazo_recebimento`: Prazo esperado em meses
        """)

if __name__ == "__main__":
    show()
