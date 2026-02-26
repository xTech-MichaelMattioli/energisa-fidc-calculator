"""
Calculador de correção monetária e valor corrigido final
Baseado no notebook original
"""

import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
from .calculador_voltz import CalculadorVoltz
from .calculador_remuneracao_variavel import CalculadorRemuneracaoVariavel


class CalculadorCorrecao:
    """
    Calcula correção monetária e valor corrigido final.
    """
    
    def __init__(self, params):
        self.params = params
        # Inicializar calculador específico da Voltz
        self.calculador_voltz = CalculadorVoltz(params)
    
    def identificar_distribuidora(self, nome_arquivo: str) -> str:
        """
        Identifica o tipo de distribuidora baseado no nome do arquivo.
        """
        if self.calculador_voltz.identificar_voltz(nome_arquivo):
            return "VOLTZ"
        else:
            return "PADRAO"
    
    def processar_com_regras_especificas(self, df: pd.DataFrame, nome_base: str, df_taxa_recuperacao: pd.DataFrame = None) -> pd.DataFrame:
        """
        Processa correção com regras específicas baseado no tipo de distribuidora.
        """
        tipo_distribuidora = self.identificar_distribuidora(nome_base)
        
        if tipo_distribuidora == "VOLTZ":
            st.success("⚡ **VOLTZ detectada!** Aplicando regras específicas para Fintech/CCBs")
            return self.calculador_voltz.processar_correcao_voltz_completa(df, nome_base, df_taxa_recuperacao)
        else:
            st.info("🏢 **Distribuidora padrão** - Aplicando regras convencionais")
            return self.processar_correcao_completa_com_recuperacao(df, nome_base, df_taxa_recuperacao)
    
    def limpar_e_converter_valor(self, serie_valor: pd.Series) -> pd.Series:
        """
        Limpa e converte série de valores para numérico, tratando diversos formatos.
        
        Formatos suportados:
        - "1.234,56" (formato brasileiro)
        - "1,234.56" (formato americano)
        - "R$ 1.234,56" (com símbolo de moeda)
        - "1 234,56" (separador de milhares com espaço)
        - "(1.234,56)" (valores negativos entre parênteses)
        - "-1.234,56" (valores negativos com sinal)
        - "1234,56" (sem separador de milhares)
        - "1234.56" (decimal com ponto)
        - Valores já numéricos (int, float)
        - Strings vazias, None, NaN
        """
        import re
        
        def limpar_valor_individual(valor):
            """Limpa um valor individual"""
            # Se já é numérico, retorna como está
            if pd.isna(valor) or valor is None:
                return 0.0
                
            if isinstance(valor, (int, float)):
                return float(valor)
            
            # Converter para string se não for
            if not isinstance(valor, str):
                valor = str(valor)
            
            # Remover espaços extras
            valor = valor.strip()
            
            # Se string vazia, retorna 0
            if valor == '' or valor.lower() in ['null', 'none', 'n/a', '#n/a', 'nan']:
                return 0.0
            
            # Detectar se valor está entre parênteses (valor negativo)
            eh_negativo = False
            if valor.startswith('(') and valor.endswith(')'):
                eh_negativo = True
                valor = valor[1:-1]  # Remove parênteses
            elif valor.startswith('-'):
                eh_negativo = True
                valor = valor[1:]  # Remove sinal negativo
            
            # Remover símbolos de moeda comuns
            simbolos_moeda = ['R$', 'USD', 'EUR', '$', '€', '£', 'US$']
            for simbolo in simbolos_moeda:
                valor = valor.replace(simbolo, '')
            
            # Remover espaços novamente após remoção dos símbolos
            valor = valor.strip()
            
            # Remover caracteres não numéricos exceto vírgula, ponto e sinal de menos
            # Manter apenas números, vírgulas, pontos
            valor_limpo = re.sub(r'[^\d.,\-]', '', valor)
            
            if not valor_limpo:
                return 0.0
            
            # Detectar formato do número
            # Contar vírgulas e pontos
            num_virgulas = valor_limpo.count(',')
            num_pontos = valor_limpo.count('.')
            
            try:
                if num_virgulas == 0 and num_pontos == 0:
                    # Apenas números: "1234"
                    resultado = float(valor_limpo)
                    
                elif num_virgulas == 1 and num_pontos == 0:
                    # Formato brasileiro com vírgula decimal: "1234,56"
                    resultado = float(valor_limpo.replace(',', '.'))
                    
                elif num_virgulas == 0 and num_pontos == 1:
                    # Pode ser formato americano "1234.56" ou separador de milhares "1.234"
                    partes = valor_limpo.split('.')
                    if len(partes[-1]) <= 2:  # Última parte tem 1-2 dígitos = decimal
                        # Formato americano: "1234.56"
                        resultado = float(valor_limpo)
                    else:
                        # Separador de milhares: "1.234" -> "1234"
                        resultado = float(valor_limpo.replace('.', ''))
                        
                elif num_virgulas == 1 and num_pontos >= 1:
                    # Formato brasileiro completo: "1.234.567,89"
                    # ou formato misto: "1.234,56"
                    partes_virgula = valor_limpo.split(',')
                    if len(partes_virgula) == 2 and len(partes_virgula[1]) <= 2:
                        # Vírgula é separador decimal
                        parte_inteira = partes_virgula[0].replace('.', '')  # Remove pontos da parte inteira
                        parte_decimal = partes_virgula[1]
                        resultado = float(f"{parte_inteira}.{parte_decimal}")
                    else:
                        # Formato confuso, tentar conversão direta
                        resultado = float(valor_limpo.replace('.', '').replace(',', '.'))
                        
                elif num_virgulas >= 2 or num_pontos >= 2:
                    # Formato americano completo: "1,234,567.89"
                    if '.' in valor_limpo and valor_limpo.rindex('.') > valor_limpo.rindex(','):
                        # Ponto é decimal: "1,234,567.89"
                        partes_ponto = valor_limpo.rsplit('.', 1)
                        parte_inteira = partes_ponto[0].replace(',', '')  # Remove vírgulas da parte inteira
                        parte_decimal = partes_ponto[1]
                        resultado = float(f"{parte_inteira}.{parte_decimal}")
                    else:
                        # Vírgula é decimal: "1.234.567,89"
                        partes_virgula = valor_limpo.rsplit(',', 1)
                        parte_inteira = partes_virgula[0].replace('.', '')  # Remove pontos da parte inteira
                        parte_decimal = partes_virgula[1] if len(partes_virgula) > 1 else '0'
                        resultado = float(f"{parte_inteira}.{parte_decimal}")
                else:
                    # Caso não identificado, tentar conversão direta
                    resultado = float(valor_limpo.replace(',', '.'))
                    
                # Aplicar sinal negativo se detectado
                if eh_negativo:
                    resultado = -resultado
                    
                return resultado
                
            except (ValueError, IndexError) as e:
                # Se falhou, tentar métodos alternativos
                try:
                    # Remover tudo exceto números e usar como inteiro
                    apenas_numeros = re.sub(r'[^\d]', '', valor_limpo)
                    if apenas_numeros:
                        resultado = float(apenas_numeros)
                        # Se tinha vírgula ou ponto, assumir que são casas decimais
                        if ',' in valor_limpo or '.' in valor_limpo:
                            resultado = resultado / 100  # Assumir 2 casas decimais
                        if eh_negativo:
                            resultado = -resultado
                        return resultado
                    else:
                        return 0.0
                except:
                    return 0.0
        
        # Aplicar a limpeza em toda a série
        valores_convertidos = serie_valor.apply(limpar_valor_individual)
        
        # Garantir que é float64
        valores_convertidos = valores_convertidos.astype('float64')
        
        # Substituir infinitos por 0
        valores_convertidos = valores_convertidos.replace([np.inf, -np.inf], 0)
        
        return valores_convertidos
    
    def calcular_valor_liquido(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula valor líquido = valor_principal - valor_nao_cedido - valor_terceiro - valor_cip
        """
        # Limpar valor principal
        if 'valor_principal' not in df.columns:
            df['valor_liquido'] = 0
            return df
        
        df['valor_principal_limpo'] = self.limpar_e_converter_valor(df['valor_principal'])
        
        # Limpar valores de dedução
        # Valor não cedido
        if 'valor_nao_cedido' in df.columns:
            df['valor_nao_cedido_limpo'] = self.limpar_e_converter_valor(df['valor_nao_cedido'].fillna(0))
        
        # Valor terceiro
        if 'valor_terceiro' in df.columns:
            df['valor_terceiro_limpo'] = self.limpar_e_converter_valor(df['valor_terceiro'].fillna(0))
        
        # Valor CIP
        if 'valor_cip' in df.columns:
            df['valor_cip_limpo'] = self.limpar_e_converter_valor(df['valor_cip'].fillna(0))
        
        # Calcular valor líquido
        df['valor_liquido'] = (
            df['valor_principal_limpo'] - 
            df['valor_nao_cedido_limpo'] - 
            df['valor_terceiro_limpo'] - 
            df['valor_cip_limpo']
        )
        
        # Garantir que valor líquido não seja negativo
        df['valor_liquido'] = np.maximum(df['valor_liquido'], 0)
        
        return df
    
    def calcular_multa(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula multa de 2% sobre valor líquido.
        """
        df = df.copy()
        
        # Calcular valor líquido se não foi calculado
        if 'valor_liquido' not in df.columns:
            df = self.calcular_valor_liquido(df)
        
        # Calcular multa apenas para valores em atraso
        df['multa'] = np.where(
            df['dias_atraso'] > 0,
            df['valor_liquido'] * self.params.taxa_multa,
            0
        )
        
        return df
    
    def calcular_juros_moratorios(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula juros moratórios de 1% ao mês proporcional sobre valor líquido.
        """
        df = df.copy()
        
        # Calcular meses de atraso
        df['meses_atraso'] = df['dias_atraso'] / 30
        
        # Calcular juros proporcionais apenas para valores em atraso
        df['juros_moratorios'] = np.where(
            df['dias_atraso'] > 0,
            df['valor_liquido'] * self.params.taxa_juros_mensal * df['meses_atraso'],
            0
        )
        
        return df
    
    def calcular_correcao_monetaria(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula correção monetária baseada em IGPM/IPCA sobre valor líquido.
        """
        df = df.copy()
        
        # Buscar índices
        df['indice_vencimento'] = df['data_vencimento_limpa'].apply(
            lambda x: self.params.buscar_indice_correcao(x) if pd.notna(x) else 624.40
        )
        
        df['indice_base'] = df['data_base'].apply(self.params.buscar_indice_correcao)
        
        # Calcular fator de correção
        df['fator_correcao'] = df['indice_base'] / df['indice_vencimento']
        
        # Aplicar correção monetária apenas para valores em atraso
        df['correcao_monetaria'] = np.where(
            df['dias_atraso'] > 0,
            df['valor_liquido'] * (df['fator_correcao'] - 1),
            0
        )
        
        # Garantir que correção não seja negativa
        df['correcao_monetaria'] = np.maximum(df['correcao_monetaria'], 0)
        
        return df
    
    def calcular_valor_corrigido_final(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula valor corrigido final somando todos os componentes.
        """
        df = df.copy()
        
        # Somar todos os componentes
        df['valor_corrigido'] = (
            df['valor_liquido'] +
            df['multa'] +
            df['juros_moratorios'] +
            df['correcao_monetaria']
        )
        
        return df
    
    def gerar_resumo_correcao(self, df: pd.DataFrame, nome_base: str):
        """
        Gera resumo da correção monetária.
        """
        st.subheader(f"📊 Resumo da Correção - {nome_base.upper()}")
        
        valor_principal = df['valor_principal_limpo'].sum()
        valor_deducoes = (df['valor_nao_cedido_limpo'].sum() + 
                         df['valor_terceiro_limpo'].sum() + 
                         df['valor_cip_limpo'].sum())
        valor_liquido = df['valor_liquido'].sum()
        multa_total = df['multa'].sum()
        juros_total = df['juros_moratorios'].sum()
        correcao_total = df['correcao_monetaria'].sum()
        valor_corrigido = df['valor_corrigido'].sum()
        
        percentual_total = ((valor_corrigido / valor_liquido) - 1) * 100 if valor_liquido > 0 else 0
        
        # Exibir em formato de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💵 Valor Principal", f"R$ {valor_principal:,.2f}")
            st.metric("⚖️ Multa (2%)", f"R$ {multa_total:,.2f}")
        
        with col2:
            st.metric("➖ Deduções Totais", f"R$ {valor_deducoes:,.2f}")
            st.metric("📈 Juros Moratórios", f"R$ {juros_total:,.2f}")
        
        with col3:
            st.metric("💎 Valor Líquido", f"R$ {valor_liquido:,.2f}")
            st.metric("💹 Correção Monetária", f"R$ {correcao_total:,.2f}")
        
        with col4:
            st.metric("🎯 Valor Corrigido", f"R$ {valor_corrigido:,.2f}")
            st.metric("📊 Correção Total", f"{percentual_total:.2f}%")
    
    def processar_correcao_completa(self, df: pd.DataFrame, nome_base: str) -> pd.DataFrame:
        """
        Executa todo o processo de correção monetária.
        """
        if df.empty:
            return df
        
        # Calcular valor líquido
        df = self.calcular_valor_liquido(df)
        
        # Calcular multa
        df = self.calcular_multa(df)
        
        # Calcular juros moratórios
        df = self.calcular_juros_moratorios(df)
        
        # Calcular correção monetária
        df = self.calcular_correcao_monetaria(df)
        
        # Calcular valor corrigido final
        df = self.calcular_valor_corrigido_final(df)
        
        return df
    
    def mapear_aging_para_taxa(self, aging: str) -> str:
        """
        Mapeia aging detalhado para categorias de taxa de recuperação.
        """
        # Dicionário de mapeamento aging -> categoria taxa
        mapeamento = {
            'A vencer': 'A vencer',
            'Menor que 30 dias': 'Primeiro ano',
            'De 31 a 59 dias': 'Primeiro ano',
            'De 60 a 89 dias': 'Primeiro ano',
            'De 90 a 119 dias': 'Primeiro ano',
            'De 120 a 359 dias': 'Primeiro ano',
            'De 360 a 719 dias': 'Segundo ano',
            'De 720 a 1080 dias': 'Terceiro ano',
            'Maior que 1080 dias': 'Demais anos'
        }
        
        return mapeamento.get(aging, 'Não identificado')
    
    def adicionar_taxa_recuperacao(self, df: pd.DataFrame, df_taxa_recuperacao: pd.DataFrame) -> pd.DataFrame:
        """
        Adiciona taxa de recuperação e prazo de recebimento cruzando Empresa, Tipo e Aging.
        """
        if df.empty or df_taxa_recuperacao.empty:
            st.warning("⚠️ Dados insuficientes para calcular taxa de recuperação")
            df['aging_taxa'] = 'Não identificado'
            df['taxa_recuperacao'] = 0.0
            df['prazo_recebimento'] = 0
            df['valor_recuperavel'] = 0.0
            return df
        
        with st.spinner("🔄 Aplicando taxas de recuperação..."):
            df = df.copy()
            
            # Remover registros onde empresa é None ou vazia
            registros_antes = len(df)
            df = df.dropna(subset=['empresa'])  # Remove linhas onde empresa é NaN/None
            df = df[df['empresa'].str.strip() != '']  # Remove linhas onde empresa é string vazia
            registros_depois = len(df)
            
            if registros_antes != registros_depois:
                registros_removidos = registros_antes - registros_depois
                st.warning(f"⚠️ Removidos {registros_removidos:,} registros sem empresa válida")
            
            if df.empty:
                st.error("❌ Nenhum registro válido após remoção de empresas vazias")
                return df
            
            # Mapear aging detalhado para categorias de taxa
            df['aging_taxa'] = df['aging'].apply(self.mapear_aging_para_taxa)
            
            # Fazer merge com dados de taxa de recuperação
            # Chaves: Empresa, Tipo, Aging (mapeado)
            df_merged = df.merge(
                df_taxa_recuperacao,
                left_on=['empresa', 'tipo', 'aging_taxa'],
                right_on=['Empresa', 'Tipo', 'Aging'],
                how='left'
            )
            
            # Preencher valores não encontrados
            df_merged['Taxa de recuperação'] = df_merged['Taxa de recuperação'].fillna(0.0)
            df_merged['Prazo de recebimento'] = df_merged['Prazo de recebimento'].fillna(0)
            
            # Renomear colunas para padrão
            df_merged = df_merged.rename(columns={
                'Taxa de recuperação': 'taxa_recuperacao',
                'Prazo de recebimento': 'prazo_recebimento'
            })
            
            # Calcular valor recuperável (valor corrigido * taxa de recuperação)
            df_merged['valor_recuperavel'] = df_merged['valor_corrigido'] * (df_merged['taxa_recuperacao'])
            
            # Remover colunas duplicadas do merge
            colunas_para_remover = ['Empresa', 'Tipo', 'Aging']
            for col in colunas_para_remover:
                if col in df_merged.columns:
                    df_merged = df_merged.drop(columns=[col])
            
            # Estatísticas de match
            total_registros = len(df)
            registros_com_taxa = (df_merged['taxa_recuperacao'] > 0).sum()
            percentual_match = (registros_com_taxa / total_registros) * 100
            
            st.success(f"✅ Taxa de recuperação aplicada: {registros_com_taxa:,}/{total_registros:,} registros ({percentual_match:.1f}%)")
            
            # Mostrar estatísticas por categoria
            if registros_com_taxa > 0:
                stats_taxa = df_merged[df_merged['taxa_recuperacao'] > 0].groupby('aging_taxa').agg({
                    'taxa_recuperacao': ['count', 'mean'],
                    'valor_recuperavel': 'sum'
                }).round(2)
        
        return df_merged
    
    def gerar_resumo_recuperacao(self, df: pd.DataFrame, nome_base: str):
        """
        Gera resumo da recuperação.
        """
        if 'valor_recuperavel' not in df.columns:
            return
        
        # st.subheader(f"🎯 Resumo da Recuperação - {nome_base.upper()}")
        
        valor_corrigido = df['valor_corrigido'].sum()
        valor_recuperavel = df['valor_recuperavel'].sum()
        percentual_recuperacao = (valor_recuperavel / valor_corrigido) * 100 if valor_corrigido > 0 else 0
        
        # Breakdown por aging
        if 'aging_taxa' in df.columns:
            # st.subheader("📈 Recuperação por Aging")
            
            recovery_breakdown = df.groupby('aging_taxa').agg({
                'valor_corrigido': 'sum',
                'valor_recuperavel': 'sum',
                'taxa_recuperacao': 'mean'
            }).round(2)
            
            recovery_breakdown['percentual_recuperacao'] = (
                recovery_breakdown['valor_recuperavel'] / 
                recovery_breakdown['valor_corrigido'] * 100
            ).round(1)
            
            recovery_breakdown.columns = [
                'Valor Corrigido', 
                'Valor Recuperável', 
                'Taxa Média (%)', 
                'Recuperação (%)'
            ]
            
            # st.dataframe(recovery_breakdown, use_container_width=True)
    
    def processar_correcao_completa_com_recuperacao(self, df: pd.DataFrame, nome_base: str, df_taxa_recuperacao: pd.DataFrame = None) -> pd.DataFrame:
        """
        Executa todo o processo de correção monetária incluindo taxa de recuperação.
        """
        if df.empty:
            return df
        
        # Processamento padrão de correção
        df = self.processar_correcao_completa(df, nome_base)
        
        # Adicionar taxa de recuperação se disponível
        if df_taxa_recuperacao is not None and not df_taxa_recuperacao.empty:
            df = self.adicionar_taxa_recuperacao(df, df_taxa_recuperacao)
            
            # Gerar resumo com recuperação
            self.gerar_resumo_recuperacao(df, nome_base)
        else:
            # Gerar resumo padrão
            self.gerar_resumo_correcao(df, nome_base)
        
        return df
    
    def calcular_valor_justo_reajustado(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula valor justo reajustado aplicando descontos por faixa de aging.
        
        Agora utiliza o novo sistema modular de remuneração variável que permite
        diferentes configurações por distribuidora.
        
        Descontos por aging (configuração padrão):
        - A vencer: 6,5%
        - Menor que 30 dias: 6,5%
        - De 31 a 59 dias: 6,5%
        - De 60 a 89 dias: 6,5%
        - De 90 a 119 dias: 8,0%
        - De 120 a 359 dias: 15,0%
        - De 360 a 719 dias: 22,0%
        - De 720 a 1080 dias: 36,0%
        - Maior que 1080 dias: 50,0%
        """
        if df.empty:
            return df
        
        # Verificar se temos valor_justo
        if 'valor_justo_ate_recebimento' not in df.columns:
            st.warning("⚠️ Coluna 'valor_justo_ate_recebimento' não encontrada. Calculando valor justo reajustado apenas com valor corrigido.")
            df['valor_justo_ate_recebimento'] = df.get('valor_corrigido', 0)
        
        # Usar o novo calculador de remuneração variável
        calculador_rv = CalculadorRemuneracaoVariavel(distribuidora="PADRAO")
        df_resultado = calculador_rv.calcular_remuneracao_variavel(df)
        
        # Manter compatibilidade com o código existente
        df_resultado['valor_justo_pos_rv'] = df_resultado['remuneracao_variavel_valor_final']
        
        # Gerar resumo usando o novo sistema
        with st.spinner("💎 Calculando valor justo reajustado..."):
            resumo = calculador_rv.gerar_resumo_remuneracao(df_resultado)

        return df_resultado
