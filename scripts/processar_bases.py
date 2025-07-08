#!/usr/bin/env python3
"""
Script para processamento das bases ESS e Voltz
Baseado no notebook FIDC_Calculo_Valor_Corrigido_CORRIGIDO.ipynb
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import os
from pathlib import Path

class ProcessadorFIDC:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.df_ess = None
        self.df_voltz = None
        self.data_base = datetime(2025, 7, 7)  # Data atual para cálculos
        
    def carregar_base_ess(self):
        """Carrega base ESS"""
        try:
            arquivo_ess = self.base_path / "BASE DADOS" / "1 - Distribuidoras" / "1. ESS_BRUTA_30.04.xlsx"
            
            if not arquivo_ess.exists():
                # Fallback para arquivo de cópia
                arquivo_ess = self.base_path / "BASE DADOS" / "1 - Distribuidoras" / "1. ESS_BRUTA_30.04 - Copia.xlsx"
            
            if arquivo_ess.exists():
                self.df_ess = pd.read_excel(arquivo_ess)
                return {
                    'status': 'sucesso',
                    'registros': len(self.df_ess),
                    'colunas': list(self.df_ess.columns),
                    'preview': self.df_ess.head(5).to_dict('records')
                }
            else:
                return {'status': 'erro', 'mensagem': 'Arquivo ESS não encontrado'}
                
        except Exception as e:
            return {'status': 'erro', 'mensagem': f'Erro ao carregar ESS: {str(e)}'}
    
    def carregar_base_voltz(self):
        """Carrega base Voltz"""
        try:
            arquivo_voltz = self.base_path / "BASE DADOS" / "0- Voltz" / "Voltz_Base_FIDC_20022025 (26.02).xlsx"
            
            if not arquivo_voltz.exists():
                # Fallback para arquivo de cópia
                arquivo_voltz = self.base_path / "BASE DADOS" / "0- Voltz" / "Voltz_Base_FIDC_20022025 (26.02) - Copia.xlsx"
            
            if arquivo_voltz.exists():
                self.df_voltz = pd.read_excel(arquivo_voltz)
                return {
                    'status': 'sucesso',
                    'registros': len(self.df_voltz),
                    'colunas': list(self.df_voltz.columns),
                    'preview': self.df_voltz.head(5).to_dict('records')
                }
            else:
                return {'status': 'erro', 'mensagem': 'Arquivo Voltz não encontrado'}
                
        except Exception as e:
            return {'status': 'erro', 'mensagem': f'Erro ao carregar Voltz: {str(e)}'}
    
    def identificar_campos_chave(self, df, nome_base):
        """Identifica campos chave automaticamente"""
        campos_encontrados = {}
        
        # Dicionário de termos para busca
        mapeamentos = {
            'id_cliente': ['client', 'codigo', 'cd_client'],
            'nome_cliente': ['nome', 'cliente', 'no_client'],
            'documento': ['cpf', 'cnpj', 'documento', 'nu_documento'],
            'contrato': ['contrato', 'conta', 'cd_contrato'],
            'valor': ['valor', 'debito', 'saldo', 'vl_fatura'],
            'vencimento': ['vencimento', 'venc', 'dt_vencimento'],
            'emissao': ['emissao', 'dt_emissao'],
            'classe': ['classe', 'categoria', 'cd_classe']
        }
        
        for campo, termos in mapeamentos.items():
            for coluna in df.columns:
                coluna_lower = str(coluna).lower()
                for termo in termos:
                    if termo in coluna_lower:
                        campos_encontrados[campo] = coluna
                        break
                if campo in campos_encontrados:
                    break
        
        return campos_encontrados
    
    def calcular_aging(self, df, campo_vencimento, campo_valor):
        """Calcula aging das bases"""
        try:
            # Converter data de vencimento
            df[campo_vencimento] = pd.to_datetime(df[campo_vencimento], errors='coerce')
            
            # Calcular dias em atraso
            df['dias_atraso'] = (self.data_base - df[campo_vencimento]).dt.days
            
            # Definir faixas de aging
            faixas = {
                'a_vencer': (df['dias_atraso'] <= 0).sum(),
                'ate_30': ((df['dias_atraso'] > 0) & (df['dias_atraso'] <= 30)).sum(),
                'ate_60': ((df['dias_atraso'] > 30) & (df['dias_atraso'] <= 60)).sum(),
                'ate_90': ((df['dias_atraso'] > 60) & (df['dias_atraso'] <= 90)).sum(),
                'ate_120': ((df['dias_atraso'] > 90) & (df['dias_atraso'] <= 120)).sum(),
                'acima_120': (df['dias_atraso'] > 120).sum()
            }
            
            # Calcular valores por faixa
            valores = {
                'a_vencer': df[df['dias_atraso'] <= 0][campo_valor].sum(),
                'ate_30': df[(df['dias_atraso'] > 0) & (df['dias_atraso'] <= 30)][campo_valor].sum(),
                'ate_60': df[(df['dias_atraso'] > 30) & (df['dias_atraso'] <= 60)][campo_valor].sum(),
                'ate_90': df[(df['dias_atraso'] > 60) & (df['dias_atraso'] <= 90)][campo_valor].sum(),
                'ate_120': df[(df['dias_atraso'] > 90) & (df['dias_atraso'] <= 120)][campo_valor].sum(),
                'acima_120': df[df['dias_atraso'] > 120][campo_valor].sum()
            }
            
            return {
                'status': 'sucesso',
                'faixas_quantidade': faixas,
                'faixas_valor': valores,
                'total_registros': len(df),
                'valor_total': df[campo_valor].sum()
            }
            
        except Exception as e:
            return {'status': 'erro', 'mensagem': f'Erro no cálculo de aging: {str(e)}'}
    
    def calcular_correcao_monetaria(self, df, campo_valor, campo_vencimento, indice='IPCA'):
        """Calcula correção monetária baseada no notebook"""
        try:
            # Simular índices de correção (normalmente viriam de fonte externa)
            indices_correcao = {
                'IPCA': 0.064,  # 6.4% ao ano
                'SELIC': 0.0523,  # 5.23% ao ano
                'CDI': 0.0501   # 5.01% ao ano
            }
            
            fator_correcao = 1 + indices_correcao.get(indice, 0.064)
            
            # Converter datas
            df[campo_vencimento] = pd.to_datetime(df[campo_vencimento], errors='coerce')
            df['dias_atraso'] = (self.data_base - df[campo_vencimento]).dt.days
            
            # Calcular correção proporcional aos dias
            df['fator_dias'] = np.where(df['dias_atraso'] > 0, 
                                      np.power(fator_correcao, df['dias_atraso'] / 365),
                                      1.0)
            
            df['valor_corrigido'] = df[campo_valor] * df['fator_dias']
            df['valor_correcao'] = df['valor_corrigido'] - df[campo_valor]
            
            resultado = {
                'status': 'sucesso',
                'indice_utilizado': indice,
                'fator_anual': fator_correcao,
                'valor_original_total': df[campo_valor].sum(),
                'valor_corrigido_total': df['valor_corrigido'].sum(),
                'valor_correcao_total': df['valor_correcao'].sum(),
                'registros_processados': len(df)
            }
            
            return resultado
            
        except Exception as e:
            return {'status': 'erro', 'mensagem': f'Erro na correção monetária: {str(e)}'}

def main():
    if len(sys.argv) < 3:
        print(json.dumps({'status': 'erro', 'mensagem': 'Argumentos insuficientes'}))
        return
    
    operacao = sys.argv[1]
    base_path = sys.argv[2]
    
    processador = ProcessadorFIDC(base_path)
    
    if operacao == 'carregar_ess':
        resultado = processador.carregar_base_ess()
    elif operacao == 'carregar_voltz':
        resultado = processador.carregar_base_voltz()
    elif operacao == 'processar_completo':
        # Carregar ambas as bases e processar
        ess = processador.carregar_base_ess()
        voltz = processador.carregar_base_voltz()
        
        if ess['status'] == 'sucesso' and voltz['status'] == 'sucesso':
            # Identificar campos automaticamente
            campos_ess = processador.identificar_campos_chave(processador.df_ess, 'ESS')
            campos_voltz = processador.identificar_campos_chave(processador.df_voltz, 'Voltz')
            
            # Calcular aging se campos necessários estão presentes
            aging_ess = None
            aging_voltz = None
            
            if 'vencimento' in campos_ess and 'valor' in campos_ess:
                aging_ess = processador.calcular_aging(
                    processador.df_ess, 
                    campos_ess['vencimento'], 
                    campos_ess['valor']
                )
            
            if 'vencimento' in campos_voltz and 'valor' in campos_voltz:
                aging_voltz = processador.calcular_aging(
                    processador.df_voltz, 
                    campos_voltz['vencimento'], 
                    campos_voltz['valor']
                )
            
            resultado = {
                'status': 'sucesso',
                'bases': {
                    'ess': ess,
                    'voltz': voltz
                },
                'campos_identificados': {
                    'ess': campos_ess,
                    'voltz': campos_voltz
                },
                'aging': {
                    'ess': aging_ess,
                    'voltz': aging_voltz
                }
            }
        else:
            resultado = {
                'status': 'erro',
                'mensagem': 'Erro ao carregar uma ou ambas as bases',
                'detalhes': {'ess': ess, 'voltz': voltz}
            }
    else:
        resultado = {'status': 'erro', 'mensagem': 'Operação não reconhecida'}
    
    print(json.dumps(resultado, ensure_ascii=False, default=str))

if __name__ == '__main__':
    main()
