"""
Calculador de Remuneração Variável - Módulo Geral
=================================================

Este módulo fornece métodos genéricos para cálculo de remuneração variável
que podem ser utilizados por qualquer distribuidora (Voltz, ETO, etc.).

A remuneração variável é aplicada como desconto baseado no aging dos valores,
permitindo diferentes configurações de faixas e percentuais conforme a necessidade
de cada distribuidora.

Autor: Sistema FIDC Energisa
Data: 2025-09-04
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Union
import streamlit as st
from datetime import datetime
import logging

# Configurar logger
logger = logging.getLogger(__name__)


class CalculadorRemuneracaoVariavel:
    """
    Calculador genérico de remuneração variável baseado em aging.
    
    Este calculador permite diferentes configurações de faixas de aging
    e percentuais de desconto, tornando-o flexível para uso em diferentes
    distribuidoras.
    """
    
    # Configuração padrão FIDC Energisa
    FAIXAS_AGING_PADRAO = {
        'A vencer': 0.065,                    # 6,5%
        'Menor que 30 dias': 0.065,          # 6,5%
        'De 31 a 59 dias': 0.065,            # 6,5%
        'De 60 a 89 dias': 0.065,            # 6,5%
        'De 90 a 119 dias': 0.080,           # 8,0%
        'De 120 a 359 dias': 0.150,          # 15,0%
        'De 360 a 719 dias': 0.220,          # 22,0%
        'De 720 a 1080 dias': 0.360,         # 36,0%
        'Maior que 1080 dias': 0.500         # 50,0%
    }
    
    # Configuração específica para Voltz (mais agressiva)
    FAIXAS_AGING_VOLTZ = {
        'A vencer': 0.065,                    # 6,5%
        'Menor que 30 dias': 0.065,          # 6,5%
        'De 31 a 59 dias': 0.065,            # 6,5%
        'De 60 a 89 dias': 0.065,            # 6,5%
        'De 90 a 119 dias': 0.080,           # 8,0%
        'De 120 a 359 dias': 0.150,          # 15,0%
        'De 360 a 719 dias': 0.220,          # 22,0%
        'De 720 a 1080 dias': 0.360,         # 36,0%
        'Maior que 1080 dias': 0.500         # 50,0%
    }
    
    def __init__(self, faixas_aging: Optional[Dict[str, float]] = None, distribuidora: str = "PADRAO"):
        """
        Inicializa o calculador de remuneração variável.
        
        Args:
            faixas_aging: Dicionário com faixas de aging e percentuais de desconto
            distribuidora: Nome da distribuidora para logs e configurações específicas
        """
        self.distribuidora = distribuidora
        
        if faixas_aging is None:
            if distribuidora.upper() == "VOLTZ":
                self.faixas_aging = self.FAIXAS_AGING_VOLTZ.copy()
            else:
                self.faixas_aging = self.FAIXAS_AGING_PADRAO.copy()
        else:
            self.faixas_aging = faixas_aging.copy()
        
        logger.info(f"Calculador de remuneração variável iniciado para {distribuidora}")
    
    def validar_dados_entrada(self, df: pd.DataFrame, coluna_valor: str, coluna_aging: str) -> bool:
        """
        Valida se os dados de entrada estão corretos.
        
        Args:
            df: DataFrame com os dados
            coluna_valor: Nome da coluna com valores
            coluna_aging: Nome da coluna com aging
            
        Returns:
            bool: True se dados válidos, False caso contrário
        """
        if df.empty:
            logger.warning("DataFrame vazio fornecido")
            return False
        
        if coluna_valor not in df.columns:
            logger.error(f"Coluna '{coluna_valor}' não encontrada no DataFrame")
            return False
        
        if coluna_aging not in df.columns:
            logger.error(f"Coluna '{coluna_aging}' não encontrada no DataFrame")
            return False
        
        # Verificar se há valores não nulos
        if df[coluna_valor].isnull().all():
            logger.warning(f"Todos os valores na coluna '{coluna_valor}' são nulos")
            return False
        
        return True
    
    def calcular_remuneracao_variavel(self, 
                                     df: pd.DataFrame, 
                                     coluna_valor: str = 'valor_justo_ate_recebimento',
                                     coluna_aging: str = 'aging',
                                     prefixo_colunas: str = 'remuneracao_variavel') -> pd.DataFrame:
        """
        Calcula a remuneração variável baseada no aging dos valores.
        
        Args:
            df: DataFrame com os dados
            coluna_valor: Nome da coluna com os valores base para cálculo
            coluna_aging: Nome da coluna com as faixas de aging
            prefixo_colunas: Prefixo para as novas colunas criadas
            
        Returns:
            pd.DataFrame: DataFrame com colunas de remuneração variável adicionadas
        """
        if not self.validar_dados_entrada(df, coluna_valor, coluna_aging):
            logger.error("Validação de dados falhou")
            return df
        
        # Criar cópia para não modificar original
        df_resultado = df.copy()
        
        # Mapear percentuais de desconto baseado no aging
        coluna_percentual = f'{prefixo_colunas}_perc'
        df_resultado[coluna_percentual] = df_resultado[coluna_aging].map(self.faixas_aging).fillna(0.0)
        
        # Calcular valor do desconto
        coluna_valor_desconto = f'{prefixo_colunas}_valor'
        df_resultado[coluna_valor_desconto] = (
            df_resultado[coluna_valor] * df_resultado[coluna_percentual]
        )
        
        # Calcular valor final (valor original - desconto)
        coluna_valor_final = f'{prefixo_colunas}_valor_final'
        df_resultado[coluna_valor_final] = (
            df_resultado[coluna_valor] - df_resultado[coluna_valor_desconto]
        )
        
        # Garantir que não seja negativo
        df_resultado[coluna_valor_final] = np.maximum(df_resultado[coluna_valor_final], 0)
        
        logger.info(f"Remuneração variável calculada para {len(df_resultado)} registros")
        
        return df_resultado
    
    def gerar_resumo_remuneracao(self, 
                                df: pd.DataFrame, 
                                coluna_valor: str = 'valor_justo_ate_recebimento',
                                prefixo_colunas: str = 'remuneracao_variavel',
                                exibir_streamlit: bool = True) -> Dict[str, Union[float, int]]:
        """
        Gera resumo estatístico da aplicação da remuneração variável.
        
        Args:
            df: DataFrame com dados calculados
            coluna_valor: Nome da coluna com valores originais
            prefixo_colunas: Prefixo das colunas de remuneração variável
            exibir_streamlit: Se deve exibir no Streamlit
            
        Returns:
            Dict: Dicionário com estatísticas do cálculo
        """
        if df.empty:
            return {}
        
        coluna_valor_desconto = f'{prefixo_colunas}_valor'
        coluna_valor_final = f'{prefixo_colunas}_valor_final'
        
        # Verificar se as colunas existem
        colunas_necessarias = [coluna_valor, coluna_valor_desconto, coluna_valor_final]
        if not all(col in df.columns for col in colunas_necessarias):
            logger.error("Colunas de remuneração variável não encontradas. Execute o cálculo primeiro.")
            return {}
        
        # Calcular estatísticas
        total_valor_original = df[coluna_valor].sum()
        total_desconto = df[coluna_valor_desconto].sum()
        total_valor_final = df[coluna_valor_final].sum()
        
        percentual_desconto = (total_desconto / total_valor_original * 100) if total_valor_original > 0 else 0
        
        # Estatísticas por faixa de aging
        resumo_por_aging = df.groupby('aging').agg({
            coluna_valor: ['sum', 'count'],
            coluna_valor_desconto: 'sum',
            coluna_valor_final: 'sum'
        }).round(2)
        
        resumo = {
            'total_valor_original': total_valor_original,
            'total_desconto': total_desconto,
            'total_valor_final': total_valor_final,
            'percentual_desconto': percentual_desconto,
            'quantidade_registros': len(df),
            'distribuidora': self.distribuidora
        }
        
        if exibir_streamlit and st:
            self._exibir_resumo_streamlit(resumo, resumo_por_aging)
        
        return resumo
    
    def _exibir_resumo_streamlit(self, resumo: Dict, resumo_por_aging: pd.DataFrame):
        """Exibe resumo no Streamlit"""
        st.success(f"✅ Remuneração variável calculada para {self.distribuidora}!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Valor Original", 
                f"R$ {resumo['total_valor_original']:,.2f}",
                help="Valor total antes da aplicação da remuneração variável"
            )
        
        with col2:
            st.metric(
                "Total Desconto", 
                f"R$ {resumo['total_desconto']:,.2f}",
                f"-{resumo['percentual_desconto']:.2f}%",
                help="Total de desconto aplicado como remuneração variável"
            )
        
        with col3:
            st.metric(
                "Valor Final", 
                f"R$ {resumo['total_valor_final']:,.2f}",
                help="Valor final após aplicação da remuneração variável"
            )
        
        # Exibir resumo por aging se disponível
        if not resumo_por_aging.empty:
            with st.expander("📊 Detalhamento por Faixa de Aging"):
                st.dataframe(
                    resumo_por_aging,
                    use_container_width=True
                )
    
    def obter_configuracao_atual(self) -> Dict[str, float]:
        """
        Retorna a configuração atual de faixas de aging.
        
        Returns:
            Dict: Dicionário com faixas de aging e percentuais
        """
        return self.faixas_aging.copy()
    
    def atualizar_faixa_aging(self, faixa: str, percentual: float):
        """
        Atualiza o percentual de uma faixa específica de aging.
        
        Args:
            faixa: Nome da faixa de aging
            percentual: Novo percentual (como decimal, ex: 0.065 para 6.5%)
        """
        if faixa in self.faixas_aging:
            self.faixas_aging[faixa] = percentual
            logger.info(f"Faixa '{faixa}' atualizada para {percentual:.3f} ({percentual*100:.1f}%)")
        else:
            logger.warning(f"Faixa '{faixa}' não encontrada nas configurações atuais")
    
    def criar_configuracao_personalizada(self, faixas_aging: Dict[str, float]) -> 'CalculadorRemuneracaoVariavel':
        """
        Cria uma nova instância com configuração personalizada.
        
        Args:
            faixas_aging: Dicionário com faixas de aging personalizadas
            
        Returns:
            CalculadorRemuneracaoVariavel: Nova instância com configuração personalizada
        """
        return CalculadorRemuneracaoVariavel(
            faixas_aging=faixas_aging,
            distribuidora=f"{self.distribuidora}_PERSONALIZADA"
        )


# Funções utilitárias para facilitar o uso

def calcular_remuneracao_variavel_padrao(df: pd.DataFrame, 
                                        coluna_valor: str = 'valor_justo_ate_recebimento',
                                        coluna_aging: str = 'aging') -> pd.DataFrame:
    """
    Função de conveniência para calcular remuneração variável com configuração padrão.
    
    Args:
        df: DataFrame com os dados
        coluna_valor: Nome da coluna com valores
        coluna_aging: Nome da coluna com aging
        
    Returns:
        pd.DataFrame: DataFrame com remuneração variável calculada
    """
    calculador = CalculadorRemuneracaoVariavel()
    return calculador.calcular_remuneracao_variavel(df, coluna_valor, coluna_aging)


def calcular_remuneracao_variavel_voltz(df: pd.DataFrame, 
                                       coluna_valor: str = 'valor_justo_ate_recebimento',
                                       coluna_aging: str = 'aging') -> pd.DataFrame:
    """
    Função de conveniência para calcular remuneração variável com configuração Voltz.
    
    Args:
        df: DataFrame com os dados
        coluna_valor: Nome da coluna com valores
        coluna_aging: Nome da coluna com aging
        
    Returns:
        pd.DataFrame: DataFrame com remuneração variável calculada
    """
    calculador = CalculadorRemuneracaoVariavel(distribuidora="VOLTZ")
    return calculador.calcular_remuneracao_variavel(df, coluna_valor, coluna_aging)


def obter_faixas_aging_padrao() -> Dict[str, float]:
    """Retorna as faixas de aging padrão"""
    return CalculadorRemuneracaoVariavel.FAIXAS_AGING_PADRAO.copy()


def obter_faixas_aging_voltz() -> Dict[str, float]:
    """Retorna as faixas de aging da Voltz"""
    return CalculadorRemuneracaoVariavel.FAIXAS_AGING_VOLTZ.copy()


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de dados
    dados_exemplo = {
        'aging': ['A vencer', 'De 31 a 59 dias', 'De 120 a 359 dias', 'Maior que 1080 dias'],
        'valor_justo_ate_recebimento': [1000.0, 2000.0, 3000.0, 4000.0]
    }
    
    df_exemplo = pd.DataFrame(dados_exemplo)
    
    # Calculador padrão
    print("=== Calculador Padrão ===")
    calculador_padrao = CalculadorRemuneracaoVariavel()
    df_resultado = calculador_padrao.calcular_remuneracao_variavel(df_exemplo)
    print(df_resultado[['aging', 'valor_justo_ate_recebimento', 'remuneracao_variavel_perc', 'remuneracao_variavel_valor_final']])
    
    # Calculador Voltz
    print("\n=== Calculador Voltz ===")
    calculador_voltz = CalculadorRemuneracaoVariavel(distribuidora="VOLTZ")
    df_resultado_voltz = calculador_voltz.calcular_remuneracao_variavel(df_exemplo)
    print(df_resultado_voltz[['aging', 'valor_justo_ate_recebimento', 'remuneracao_variavel_perc', 'remuneracao_variavel_valor_final']])
