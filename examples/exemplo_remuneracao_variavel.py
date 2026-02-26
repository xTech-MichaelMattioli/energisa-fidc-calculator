"""
Exemplo de Uso do Sistema de Remuneração Variável
================================================

Este arquivo demonstra como usar o novo sistema modular de remuneração variável
em diferentes cenários reais do FIDC Energisa.

Cenários demonstrados:
1. Uso padrão para distribuidoras convencionais
2. Uso específico para Voltz (fintech)
3. Configuração personalizada para nova distribuidora
4. Migração do código existente
"""

import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

# Importar o novo sistema
from utils.calculador_remuneracao_variavel import (
    CalculadorRemuneracaoVariavel,
    calcular_remuneracao_variavel_padrao,
    calcular_remuneracao_variavel_voltz
)


def exemplo_uso_padrao():
    """Exemplo de uso para distribuidoras padrão"""
    st.subheader("📋 Exemplo: Distribuidora Padrão")
    
    # Dados de exemplo
    dados_exemplo = {
        'numero_contrato': ['CNT-001', 'CNT-002', 'CNT-003', 'CNT-004'],
        'aging': ['A vencer', 'De 31 a 59 dias', 'De 120 a 359 dias', 'Maior que 1080 dias'],
        'valor_justo_ate_recebimento': [50000.0, 75000.0, 100000.0, 125000.0],
        'empresa': ['ETO', 'ETO', 'ETO', 'ETO']
    }
    
    df = pd.DataFrame(dados_exemplo)
    
    st.write("**Dados de entrada:**")
    st.dataframe(df)
    
    # Calcular remuneração variável usando função de conveniência
    df_resultado = calcular_remuneracao_variavel_padrao(df)
    
    st.write("**Resultado com remuneração variável:**")
    colunas_resultado = [
        'numero_contrato', 'aging', 'valor_justo_ate_recebimento',
        'remuneracao_variavel_perc', 'remuneracao_variavel_valor',
        'remuneracao_variavel_valor_final'
    ]
    st.dataframe(df_resultado[colunas_resultado])
    
    # Resumo
    total_original = df['valor_justo_ate_recebimento'].sum()
    total_final = df_resultado['remuneracao_variavel_valor_final'].sum()
    total_desconto = df_resultado['remuneracao_variavel_valor'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Valor Original", f"R$ {total_original:,.2f}")
    with col2:
        st.metric("Desconto Total", f"R$ {total_desconto:,.2f}")
    with col3:
        st.metric("Valor Final", f"R$ {total_final:,.2f}")
    
    return df_resultado


def exemplo_uso_voltz():
    """Exemplo de uso específico para Voltz"""
    st.subheader("⚡ Exemplo: Voltz (Fintech)")
    
    # Dados de exemplo específicos da Voltz
    dados_voltz = {
        'numero_contrato': ['VOLTZ-001', 'VOLTZ-002', 'VOLTZ-003', 'VOLTZ-004'],
        'aging': ['Menor que 30 dias', 'De 60 a 89 dias', 'De 360 a 719 dias', 'Maior que 1080 dias'],
        'valor_justo_ate_recebimento': [30000.0, 45000.0, 80000.0, 150000.0],
        'empresa': ['VOLTZ', 'VOLTZ', 'VOLTZ', 'VOLTZ'],
        'tipo_contrato': ['CCB', 'CCB', 'CCB', 'CCB']
    }
    
    df = pd.DataFrame(dados_voltz)
    
    st.write("**Dados de entrada (Voltz):**")
    st.dataframe(df)
    
    # Calcular usando configuração específica da Voltz
    df_resultado = calcular_remuneracao_variavel_voltz(df)
    
    st.write("**Resultado com configuração Voltz (mais agressiva):**")
    colunas_resultado = [
        'numero_contrato', 'aging', 'valor_justo_ate_recebimento',
        'remuneracao_variavel_perc', 'remuneracao_variavel_valor',
        'remuneracao_variavel_valor_final'
    ]
    st.dataframe(df_resultado[colunas_resultado])
    
    # Comparar com configuração padrão
    df_padrao = calcular_remuneracao_variavel_padrao(df)
    
    desconto_voltz = df_resultado['remuneracao_variavel_valor'].sum()
    desconto_padrao = df_padrao['remuneracao_variavel_valor'].sum()
    diferenca = desconto_voltz - desconto_padrao
    
    st.info(f"💡 **Diferença Voltz vs Padrão:** R$ {diferenca:,.2f} a mais de desconto")
    
    return df_resultado


def exemplo_configuracao_personalizada():
    """Exemplo de configuração personalizada para nova distribuidora"""
    st.subheader("🎨 Exemplo: Configuração Personalizada")
    
    # Definir configuração personalizada para uma nova distribuidora
    faixas_personalizadas = {
        'A vencer': 0.040,                    # 4,0% (mais conservador)
        'Menor que 30 dias': 0.040,          # 4,0%
        'De 31 a 59 dias': 0.055,            # 5,5%
        'De 60 a 89 dias': 0.070,            # 7,0%
        'De 90 a 119 dias': 0.090,           # 9,0%
        'De 120 a 359 dias': 0.130,          # 13,0%
        'De 360 a 719 dias': 0.200,          # 20,0%
        'De 720 a 1080 dias': 0.320,         # 32,0%
        'Maior que 1080 dias': 0.450         # 45,0%
    }
    
    st.write("**Configuração personalizada:**")
    config_df = pd.DataFrame([
        {'Faixa de Aging': faixa, 'Percentual': f"{perc*100:.1f}%"}
        for faixa, perc in faixas_personalizadas.items()
    ])
    st.dataframe(config_df)
    
    # Dados de exemplo
    dados_exemplo = {
        'numero_contrato': ['NOVA-001', 'NOVA-002', 'NOVA-003'],
        'aging': ['De 31 a 59 dias', 'De 360 a 719 dias', 'Maior que 1080 dias'],
        'valor_justo_ate_recebimento': [60000.0, 90000.0, 120000.0],
        'empresa': ['NOVA_DISTRIBUIDORA', 'NOVA_DISTRIBUIDORA', 'NOVA_DISTRIBUIDORA']
    }
    
    df = pd.DataFrame(dados_exemplo)
    
    # Criar calculador personalizado
    calculador_personalizado = CalculadorRemuneracaoVariavel(
        faixas_aging=faixas_personalizadas,
        distribuidora="NOVA_DISTRIBUIDORA"
    )
    
    df_resultado = calculador_personalizado.calcular_remuneracao_variavel(df)
    
    st.write("**Resultado com configuração personalizada:**")
    colunas_resultado = [
        'numero_contrato', 'aging', 'valor_justo_ate_recebimento',
        'remuneracao_variavel_perc', 'remuneracao_variavel_valor',
        'remuneracao_variavel_valor_final'
    ]
    st.dataframe(df_resultado[colunas_resultado])
    
    # Gerar resumo
    resumo = calculador_personalizado.gerar_resumo_remuneracao(
        df_resultado, 
        exibir_streamlit=False
    )
    
    st.success(f"✅ Configuração personalizada aplicada com {resumo['percentual_desconto']:.2f}% de desconto total")
    
    return df_resultado


def exemplo_migracao_codigo_existente():
    """Exemplo de como migrar código existente"""
    st.subheader("🔄 Migração do Código Existente")
    
    st.code("""
# ANTES - Código antigo no calculador_correcao.py
def calcular_valor_justo_reajustado(self, df: pd.DataFrame) -> pd.DataFrame:
    # Dicionário de descontos por aging (hardcoded)
    descontos_aging = {
        'A vencer': 0.065,
        'Menor que 30 dias': 0.065,
        # ... mais definições hardcoded
    }
    
    # Mapeamento manual
    df['remuneracao_variavel_perc'] = df['aging'].map(descontos_aging).fillna(0.0)
    df['remuneracao_variavel_valor'] = df['valor_justo_ate_recebimento'] * df['remuneracao_variavel_perc']
    df['valor_justo_pos_rv'] = df['valor_justo_ate_recebimento'] - df['remuneracao_variavel_valor']
    
    return df
""", language="python")
    
    st.code("""
# DEPOIS - Novo código modular
from .calculador_remuneracao_variavel import CalculadorRemuneracaoVariavel

def calcular_valor_justo_reajustado(self, df: pd.DataFrame) -> pd.DataFrame:
    # Usar sistema modular
    calculador_rv = CalculadorRemuneracaoVariavel(distribuidora="PADRAO")
    df_resultado = calculador_rv.calcular_remuneracao_variavel(df)
    
    # Manter compatibilidade com código existente
    df_resultado['valor_justo_pos_rv'] = df_resultado['remuneracao_variavel_valor_final']
    
    # Gerar resumo automático
    calculador_rv.gerar_resumo_remuneracao(df_resultado)
    
    return df_resultado
""", language="python")
    
    st.success("✅ Migração concluída - Código mais limpo, flexível e reutilizável!")


def demonstrar_beneficios():
    """Demonstra os benefícios do novo sistema"""
    st.subheader("🎯 Benefícios do Novo Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🔴 Sistema Antigo:**")
        st.write("❌ Código duplicado em várias classes")
        st.write("❌ Configurações hardcoded")
        st.write("❌ Difícil manutenção")
        st.write("❌ Sem reutilização")
        st.write("❌ Relatórios manuais")
    
    with col2:
        st.write("**🟢 Sistema Novo:**")
        st.write("✅ Código centralizado e modular")
        st.write("✅ Configurações flexíveis")
        st.write("✅ Fácil manutenção")
        st.write("✅ Máxima reutilização")
        st.write("✅ Relatórios automáticos")
    
    st.info("""
    **💡 Principais Vantagens:**
    - **Escalabilidade**: Fácil adição de novas distribuidoras
    - **Flexibilidade**: Configurações específicas por empresa
    - **Manutenibilidade**: Código limpo e documentado
    - **Auditabilidade**: Logs e resumos automáticos
    - **Performance**: Operações vetorizadas com Pandas/NumPy
    """)


def main():
    """Função principal da demonstração"""
    st.title("🎯 Sistema de Remuneração Variável - Exemplos de Uso")
    st.markdown("---")
    
    st.markdown("""
    Este sistema modular permite calcular remuneração variável para qualquer distribuidora
    do FIDC Energisa de forma consistente e flexível.
    """)
    
    # Executar exemplos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Padrão", "Voltz", "Personalizada", "Migração", "Benefícios"
    ])
    
    with tab1:
        exemplo_uso_padrao()
    
    with tab2:
        exemplo_uso_voltz()
    
    with tab3:
        exemplo_configuracao_personalizada()
    
    with tab4:
        exemplo_migracao_codigo_existente()
    
    with tab5:
        demonstrar_beneficios()
    
    st.markdown("---")
    st.success("🎉 **Sistema pronto para uso em produção!**")


if __name__ == "__main__":
    main()
