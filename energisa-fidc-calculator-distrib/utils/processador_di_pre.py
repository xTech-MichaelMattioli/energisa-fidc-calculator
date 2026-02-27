# utils/processador_di_pre.py - Processador específico para arquivos DI x pré da BMF
import pandas as pd
import re
from bs4 import BeautifulSoup
from datetime import datetime
import numpy as np

class ProcessadorDIPre:
    """
    Classe para processar arquivos Excel de DI x pré da BMF
    """
    
    def __init__(self):
        self.df_di_pre = None
        self.data_arquivo = None
        self.total_registros = 0
        
    def processar_arquivo_bmf(self, uploaded_file):
        """
        Processa arquivo Excel/HTML da BMF com dados de DI x pré
        """
        try:
            # Ler o conteúdo do arquivo
            if hasattr(uploaded_file, 'read'):
                conteudo = uploaded_file.read()
                if isinstance(conteudo, bytes):
                    conteudo = conteudo.decode('utf-8', errors='ignore')
            else:
                with open(uploaded_file, 'r', encoding='utf-8', errors='ignore') as f:
                    conteudo = f.read()
            
            # Extrair data do nome do arquivo se possível
            nome_arquivo = uploaded_file.name if hasattr(uploaded_file, 'name') else str(uploaded_file)
            self.data_arquivo = self._extrair_data_arquivo(nome_arquivo)
            
            # Processar HTML
            soup = BeautifulSoup(conteudo, 'html.parser')
            
            # Buscar dados da tabela
            dados_extraidos = self._extrair_dados_tabela(soup)
            
            if dados_extraidos:
                # Criar DataFrame
                self.df_di_pre = pd.DataFrame(dados_extraidos)
                self.total_registros = len(self.df_di_pre)
                
                # Validar e limpar dados
                self.df_di_pre = self._validar_e_limpar_dados(self.df_di_pre)
                
                return self.df_di_pre
            else:
                raise ValueError("Nenhum dado válido encontrado no arquivo")
                
        except Exception as e:
            raise Exception(f"Erro ao processar arquivo BMF: {str(e)}")
    
    def _extrair_data_arquivo(self, nome_arquivo):
        """
        Extrai data do nome do arquivo (ex: PRE20250801.xls)
        """
        try:
            # Procurar padrão de data no nome
            padrao_data = re.search(r'(\d{8})', nome_arquivo)
            if padrao_data:
                data_str = padrao_data.group(1)
                return datetime.strptime(data_str, '%Y%m%d').date()
            
            # Se não encontrar, usar data atual
            return datetime.now().date()
            
        except:
            return datetime.now().date()
    
    def _extrair_dados_tabela(self, soup):
        """
        Extrai dados da tabela HTML BMF
        """
        dados_extraidos = []
        
        try:
            # Buscar todas as linhas da tabela
            linhas = soup.find_all('tr')
            
            for linha in linhas:
                cells = linha.find_all('td')
                
                if len(cells) >= 3:
                    # Primeira célula: dias corridos
                    dias_texto = cells[0].get_text(strip=True)
                    
                    # Verificar se é um número (dias corridos)
                    if dias_texto.isdigit():
                        dias_corridos = int(dias_texto)
                        
                        # Verificar se está no range válido
                        if 1 <= dias_corridos <= 12799:
                            # Segunda célula: taxa para 252 dias úteis
                            taxa_252_texto = cells[1].get_text(strip=True)
                            taxa_252 = self._extrair_numero_brasileiro(taxa_252_texto)
                            
                            # Terceira célula: taxa para 360 dias corridos
                            taxa_360_texto = cells[2].get_text(strip=True)
                            taxa_360 = self._extrair_numero_brasileiro(taxa_360_texto)
                            
                            # Adicionar registro se pelo menos uma taxa for válida
                            if taxa_252 is not None or taxa_360 is not None:
                                dados_extraidos.append({
                                    'dias_corridos': dias_corridos,
                                    '252': taxa_252 if taxa_252 is not None else 0.0,
                                    '360': taxa_360 if taxa_360 is not None else 0.0,
                                    'taxa_252_original': taxa_252_texto,
                                    'taxa_360_original': taxa_360_texto,
                                    'data_arquivo': self.data_arquivo
                                })
            
            return dados_extraidos
            
        except Exception as e:
            raise Exception(f"Erro ao extrair dados da tabela: {str(e)}")
    
    def _extrair_numero_brasileiro(self, texto):
        """
        Extrai número do formato brasileiro (14,90)
        """
        if not texto or texto in ['', '-', 'N/A', 'n/a']:
            return None
            
        # Limpar o texto
        texto_limpo = re.sub(r'[^\d,\.\-\+]', '', texto.strip())
        
        if not texto_limpo:
            return None
        
        try:
            # Padrões para números brasileiros
            padroes = [
                r'(\-?\d{1,3}(?:\.\d{3})*,\d{1,4})',  # 12.345,67
                r'(\-?\d+,\d{1,4})',                   # 123,45
                r'(\-?\d+\.\d{1,4})',                  # 123.45 (formato americano)
                r'(\-?\d+)',                           # 123 (inteiros)
            ]
            
            for padrao in padroes:
                match = re.search(padrao, texto_limpo)
                if match:
                    numero_str = match.group(1)
                    
                    # Converter formato brasileiro para float
                    if ',' in numero_str and '.' in numero_str:
                        # Formato: 12.345,67
                        numero_str = numero_str.replace('.', '').replace(',', '.')
                    elif ',' in numero_str and numero_str.count(',') == 1:
                        # Formato: 123,45
                        numero_str = numero_str.replace(',', '.')
                    
                    valor = float(numero_str)
                    
                    # Filtrar valores muito extremos
                    if -1000 <= valor <= 1000:
                        return valor
            
            return None
            
        except:
            return None
    
    def _validar_e_limpar_dados(self, df):
        """
        Valida e limpa os dados extraídos
        """
        try:
            # Remover registros com dias corridos duplicados (manter o primeiro)
            df = df.drop_duplicates(subset=['dias_corridos'], keep='first')
            
            # Ordenar por dias corridos
            df = df.sort_values('dias_corridos').reset_index(drop=True)
            
            # Validar ranges das taxas
            df.loc[df['252'] < 0, '252'] = 0.0
            df.loc[df['252'] > 100, '252'] = 100.0
            df.loc[df['360'] < 0, '360'] = 0.0
            df.loc[df['360'] > 100, '360'] = 100.0
            
            return df
            
        except Exception as e:
            raise Exception(f"Erro na validação dos dados: {str(e)}")
    
    def obter_estatisticas(self):
        """
        Retorna estatísticas dos dados carregados
        """
        if self.df_di_pre is None or self.df_di_pre.empty:
            return None
        
        # Calcular algumas taxas anualizadas de referência
        taxa_anual_30d_252 = self.calcular_taxa_anualizada(30, '252')
        taxa_anual_30d_360 = self.calcular_taxa_anualizada(30, '360')
        taxa_anual_180d_252 = self.calcular_taxa_anualizada(180, '252')
        taxa_anual_180d_360 = self.calcular_taxa_anualizada(180, '360')
        taxa_anual_360d_252 = self.calcular_taxa_anualizada(360, '252')
        taxa_anual_360d_360 = self.calcular_taxa_anualizada(360, '360')
        
        stats = {
            'total_registros': len(self.df_di_pre),
            'dias_min': self.df_di_pre['dias_corridos'].min(),
            'dias_max': self.df_di_pre['dias_corridos'].max(),
            'taxa_252_min': self.df_di_pre['252'].min(),
            'taxa_252_max': self.df_di_pre['252'].max(),
            'taxa_252_media': self.df_di_pre['252'].mean(),
            'taxa_360_min': self.df_di_pre['360'].min(),
            'taxa_360_max': self.df_di_pre['360'].max(),
            'taxa_360_media': self.df_di_pre['360'].mean(),
            'data_arquivo': self.data_arquivo,
            # Taxas anualizadas de referência
            'taxa_anual_30d_252': taxa_anual_30d_252,
            'taxa_anual_30d_360': taxa_anual_30d_360,
            'taxa_anual_180d_252': taxa_anual_180d_252,
            'taxa_anual_180d_360': taxa_anual_180d_360,
            'taxa_anual_360d_252': taxa_anual_360d_252,
            'taxa_anual_360d_360': taxa_anual_360d_360
        }
        
        return stats
    
    def obter_taxa_por_dias(self, dias_corridos, base_calculo='252'):
        """
        Obtém taxa específica para um número de dias corridos
        """
        if self.df_di_pre is None or self.df_di_pre.empty:
            return None
        
        # Buscar exato
        linha_exata = self.df_di_pre[self.df_di_pre['dias_corridos'] == dias_corridos]
        
        if not linha_exata.empty:
            return linha_exata.iloc[0][base_calculo]
        
        # Se não encontrar exato, fazer interpolação
        return self._interpolar_taxa(dias_corridos, base_calculo)
    
    def calcular_taxa_anualizada(self, dias_corridos, base_calculo='252'):
        """
        Calcula a taxa anualizada com base nos dias corridos e base de cálculo
        
        Fórmula: Taxa_Anualizada = ((1 + taxa_periodo)^(base_anual/dias_corridos) - 1) * 100
        
        Args:
            dias_corridos: Número de dias corridos
            base_calculo: '252' (dias úteis) ou '360' (dias corridos)
            
        Returns:
            float: Taxa anualizada em percentual
        """
        try:
            # Obter a taxa do período
            taxa_periodo = self.obter_taxa_por_dias(dias_corridos, base_calculo)
            
            if taxa_periodo is None:
                return None
            
            # Converter percentual para decimal
            taxa_decimal = taxa_periodo / 100
            
            # Definir base anual
            if base_calculo == '252':
                base_anual = 252  # Dias úteis no ano
            else:  # base_calculo == '360'
                base_anual = 360  # Dias corridos no ano
            
            # Calcular taxa anualizada
            # Taxa_Anualizada = ((1 + taxa_periodo)^(base_anual/dias_corridos) - 1)
            fator_capitalizacao = (1 + taxa_decimal) ** (base_anual / dias_corridos)
            taxa_anualizada = (fator_capitalizacao - 1) * 100
            
            return taxa_anualizada
            
        except Exception as e:
            print(f"Erro ao calcular taxa anualizada: {e}")
            return None
    
    def calcular_fator_acumulado(self, dias_corridos, base_calculo='252'):
        """
        Calcula o fator de acumulação para o período
        
        Fórmula: Fator = (1 + taxa_periodo/100)
        
        Args:
            dias_corridos: Número de dias corridos
            base_calculo: '252' (dias úteis) ou '360' (dias corridos)
            
        Returns:
            float: Fator de acumulação
        """
        try:
            taxa_periodo = self.obter_taxa_por_dias(dias_corridos, base_calculo)
            
            if taxa_periodo is None:
                return None
            
            fator = 1 + (taxa_periodo / 100)
            return fator
            
        except Exception as e:
            print(f"Erro ao calcular fator acumulado: {e}")
            return None
    
    def calcular_valor_corrigido(self, valor_inicial, dias_corridos, base_calculo='252'):
        """
        Calcula o valor corrigido pela taxa DI x pré
        
        Args:
            valor_inicial: Valor inicial a ser corrigido
            dias_corridos: Número de dias corridos
            base_calculo: '252' (dias úteis) ou '360' (dias corridos)
            
        Returns:
            float: Valor corrigido
        """
        try:
            fator = self.calcular_fator_acumulado(dias_corridos, base_calculo)
            
            if fator is None:
                return None
            
            valor_corrigido = valor_inicial * fator
            return valor_corrigido
            
        except Exception as e:
            print(f"Erro ao calcular valor corrigido: {e}")
            return None
    
    def obter_equivalencia_bases(self, dias_corridos):
        """
        Compara as taxas das duas bases (252 vs 360) para o mesmo período
        
        Returns:
            dict: Comparação das bases com taxas anualizadas
        """
        try:
            taxa_252 = self.obter_taxa_por_dias(dias_corridos, '252')
            taxa_360 = self.obter_taxa_por_dias(dias_corridos, '360')
            
            taxa_anual_252 = self.calcular_taxa_anualizada(dias_corridos, '252')
            taxa_anual_360 = self.calcular_taxa_anualizada(dias_corridos, '360')
            
            resultado = {
                'dias_corridos': dias_corridos,
                'taxa_252_periodo': taxa_252,
                'taxa_360_periodo': taxa_360,
                'taxa_252_anualizada': taxa_anual_252,
                'taxa_360_anualizada': taxa_anual_360,
                'diferenca_periodo': taxa_252 - taxa_360 if (taxa_252 and taxa_360) else None,
                'diferenca_anualizada': taxa_anual_252 - taxa_anual_360 if (taxa_anual_252 and taxa_anual_360) else None
            }
            
            return resultado
            
        except Exception as e:
            print(f"Erro ao calcular equivalência: {e}")
            return None
    
    def _interpolar_taxa(self, dias_corridos, base_calculo):
        """
        Interpola taxa para dias corridos não disponíveis
        """
        try:
            # Encontrar o ponto anterior e posterior
            anterior = self.df_di_pre[self.df_di_pre['dias_corridos'] < dias_corridos]
            posterior = self.df_di_pre[self.df_di_pre['dias_corridos'] > dias_corridos]
            
            if anterior.empty:
                # Usar o primeiro valor disponível
                return self.df_di_pre.iloc[0][base_calculo]
            
            if posterior.empty:
                # Usar o último valor disponível
                return self.df_di_pre.iloc[-1][base_calculo]
            
            # Interpolação linear
            x1 = anterior.iloc[-1]['dias_corridos']
            y1 = anterior.iloc[-1][base_calculo]
            x2 = posterior.iloc[0]['dias_corridos']
            y2 = posterior.iloc[0][base_calculo]
            
            # Fórmula da interpolação linear
            taxa_interpolada = y1 + (y2 - y1) * (dias_corridos - x1) / (x2 - x1)
            
            return taxa_interpolada
            
        except:
            # Em caso de erro, retornar média geral
            return self.df_di_pre[base_calculo].mean()
    
    def exportar_csv(self, nome_arquivo=None):
        """
        Exporta dados para CSV
        """
        if self.df_di_pre is None or self.df_di_pre.empty:
            raise ValueError("Nenhum dado para exportar")
        
        if nome_arquivo is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f"di_pre_bmf_{timestamp}.csv"
        
        # Preparar DataFrame para exportação
        df_export = self.df_di_pre[['dias_corridos', '252', '360']].copy()
        df_export.columns = ['Dias_Corridos', 'Taxa_252_Dias_Uteis', 'Taxa_360_Dias_Corridos']
        
        df_export.to_csv(nome_arquivo, index=False, decimal=',', sep=';')
        
        return nome_arquivo
    
    def exportar_excel(self, nome_arquivo=None):
        """
        Exporta dados para Excel
        """
        if self.df_di_pre is None or self.df_di_pre.empty:
            raise ValueError("Nenhum dado para exportar")
        
        if nome_arquivo is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f"di_pre_bmf_{timestamp}.xlsx"
        
        with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
            # Aba principal
            df_export = self.df_di_pre[['dias_corridos', '252', '360']].copy()
            df_export.columns = ['Dias_Corridos', 'Taxa_252_Dias_Uteis', 'Taxa_360_Dias_Corridos']
            df_export.to_excel(writer, sheet_name='DI_Pre_BMF', index=False)
            
            # Aba com estatísticas
            stats = self.obter_estatisticas()
            if stats:
                df_stats = pd.DataFrame([stats]).T
                df_stats.columns = ['Valor']
                df_stats.to_excel(writer, sheet_name='Estatisticas')
        
        return nome_arquivo
 