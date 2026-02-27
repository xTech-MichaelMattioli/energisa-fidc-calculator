"""
Exportador de resultados para Excel
Baseado no notebook original
"""

import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
from io import BytesIO


class ExportadorResultados:
    """
    Exporta os resultados finais para Excel com resumos por aging e formatação aprimorada.
    """
    
    def __init__(self, params):
        self.params = params
    
    def gerar_resumo_por_aging(self, df, nome_base):
        """
        Gera resumo consolidado por aging para uma base específica.
        """
        if df is None or df.empty or 'aging' not in df.columns:
            return pd.DataFrame()
        
        # Colunas necessárias para o resumo
        colunas_valores = ['valor_liquido', 'valor_corrigido', 'multa', 'juros_moratorios', 'correcao_monetaria']
        colunas_disponiveis = [col for col in colunas_valores if col in df.columns]
        
        if not colunas_disponiveis:
            return pd.DataFrame()
        
        # Agrupar por aging
        resumo = df.groupby('aging').agg({
            'id_padronizado': 'count',  # Quantidade de registros
            **{col: 'sum' for col in colunas_disponiveis}  # Somas dos valores
        }).round(2)
        
        # Renomear colunas
        resumo.columns = ['Qtd_Registros'] + [col.replace('_', ' ').title() for col in colunas_disponiveis]
        
        # Calcular percentuais de participação
        if 'valor_corrigido' in df.columns:
            total_valor_corrigido = df['valor_corrigido'].sum()
            if total_valor_corrigido > 0:
                resumo['Participacao_Perc'] = (resumo['Valor Corrigido'] / total_valor_corrigido * 100).round(2)
        
        # Calcular percentual médio de correção por aging
        if 'valor_liquido' in df.columns and 'valor_corrigido' in df.columns:
            mask = resumo['Valor Liquido'] > 0
            resumo.loc[mask, 'Perc_Correcao_Medio'] = ((resumo.loc[mask, 'Valor Corrigido'] / resumo.loc[mask, 'Valor Liquido'] - 1) * 100).round(2)
        
        # Resetar índice para incluir aging como coluna
        resumo = resumo.reset_index()
        resumo.insert(0, 'Base', nome_base)
        
        return resumo
    
    def criar_dicionario_dados(self) -> pd.DataFrame:
        """
        Cria dicionário de dados com descrição de todas as colunas da base.
        """
        dicionario = {
            'Campo': [
                'id_padronizado',
                'empresa',
                'tipo',
                'classe', 
                'status',
                'situacao',
                'nome_cliente',
                'documento',
                'contrato',
                'data_vencimento',
                'valor_principal',
                'valor_nao_cedido',
                'valor_terceiro',
                'valor_cip',
                'valor_principal_limpo',
                'valor_liquido',
                'aging',
                'aging_taxa',
                'dias_atraso',
                'taxa_multa_aplicada',
                'taxa_juros_aplicada',
                'multa',
                'juros_moratorios',
                'correcao_monetaria',
                'valor_corrigido',
                'valor_justo',
                'valor_recuperavel'
            ],
            'Descricao': [
                'Identificador único criado a partir do nome do cliente e data de vencimento',
                'Nome da empresa/distribuidora (ESS, EMR, etc.)',
                'Tipo de cliente ou débito',
                'Classe do cliente (Residencial, Comercial, Industrial, etc.)',
                'Status atual do débito',
                'Situação específica do débito',
                'Nome completo do cliente devedor',
                'CPF ou CNPJ do cliente',
                'Número do contrato ou unidade consumidora',
                'Data de vencimento original da fatura',
                'Valor principal da fatura original',
                'Valor que não foi cedido ao FIDC',
                'Valor relacionado a terceiros',
                'Valor relacionado ao CIP (Conta de Irregularidades de Pagamento)',
                'Valor principal após aplicação das regras de limpeza',
                'Valor líquido = Principal Limpo - Não Cedido - Terceiro - CIP',
                'Classificação de aging conforme metodologia FIDC',
                'Taxa de recuperação associada ao aging',
                'Número de dias em atraso desde o vencimento',
                'Taxa de multa aplicada (configurável)',
                'Taxa de juros moratórios aplicada (configurável)',
                'Valor da multa calculada',
                'Valor dos juros moratórios calculados',
                'Valor da correção monetária (IGP-M até 2021.05, IPCA após)',
                'Valor total corrigido = Valor Líquido + Multa + Juros + Correção',
                'Valor justo = Valor Corrigido × Taxa de Recuperação do Aging',
                'Valor recuperável final esperado conforme taxas de recuperação'
            ],
            'Tipo': [
                'Texto',
                'Texto',
                'Texto',
                'Texto',
                'Texto',
                'Texto',
                'Texto',
                'Texto',
                'Texto',
                'Data',
                'Monetário',
                'Monetário',
                'Monetário',
                'Monetário',
                'Monetário',
                'Monetário',
                'Texto',
                'Percentual',
                'Numérico',
                'Percentual',
                'Percentual',
                'Monetário',
                'Monetário',
                'Monetário',
                'Monetário',
                'Monetário',
                'Monetário'
            ],
            'Obrigatorio': [
                'Sim',
                'Sim',
                'Não',
                'Não',
                'Não',
                'Não',
                'Sim',
                'Não',
                'Não',
                'Sim',
                'Sim',
                'Não',
                'Não',
                'Não',
                'Sim',
                'Sim',
                'Sim',
                'Sim',
                'Sim',
                'Sim',
                'Sim',
                'Sim',
                'Sim',
                'Sim',
                'Sim',
                'Sim',
                'Sim'
            ]
        }
        
        return pd.DataFrame(dicionario)
    
    def gerar_agrupamento_detalhado(self, df_consolidado):
        """
        Gera agrupamento detalhado por empresa, tipo, classe, status e situação.
        """
        if df_consolidado is None or df_consolidado.empty:
            return pd.DataFrame()
        
        # Colunas para agrupamento
        colunas_agrupamento = ['empresa', 'tipo', 'classe', 'status', 'situacao', 'aging', 'aging_taxa']
        colunas_existentes = [col for col in colunas_agrupamento if col in df_consolidado.columns]
        
        if not colunas_existentes:
            return pd.DataFrame()
        
        # Colunas para soma
        colunas_valores = ['valor_liquido', 'valor_corrigido', 'multa', 'juros_moratorios', 'correcao_monetaria', 'valor_justo', 'valor_recuperavel']
        colunas_valores_existentes = [col for col in colunas_valores if col in df_consolidado.columns]
        
        agrupado = (df_consolidado
                   .groupby(colunas_existentes, dropna=False)
                   .agg({
                       'id_padronizado': 'count',
                       **{col: 'sum' for col in colunas_valores_existentes}
                   })
                   .reset_index()
                   .round(2))
        
        agrupado.rename(columns={'id_padronizado': 'qtd_registros'}, inplace=True)
        
        return agrupado
    
    def gerar_agrupamento_consolidado(self, df_consolidado):
        """
        Gera agrupamento consolidado por empresa e aging.
        """
        if df_consolidado is None or df_consolidado.empty:
            return pd.DataFrame()
        
        colunas_agrupamento = ['empresa', 'aging', 'aging_taxa']
        colunas_existentes = [col for col in colunas_agrupamento if col in df_consolidado.columns]
        
        if not colunas_existentes:
            return pd.DataFrame()
        
        colunas_valores = ['valor_liquido', 'valor_corrigido', 'multa', 'juros_moratorios', 'correcao_monetaria', 'valor_justo', 'valor_recuperavel']
        colunas_valores_existentes = [col for col in colunas_valores if col in df_consolidado.columns]
        
        agrupado = (df_consolidado
                   .groupby(colunas_existentes, dropna=False)
                   .agg({
                       'id_padronizado': 'count',
                       **{col: 'sum' for col in colunas_valores_existentes}
                   })
                   .reset_index()
                   .round(2))
        
        agrupado.rename(columns={'id_padronizado': 'qtd_registros'}, inplace=True)
        
        return agrupado
    
    def gerar_agrupamento_geral(self, df_consolidado):
        """
        Gera agrupamento geral por aging e taxa de recuperação.
        """
        if df_consolidado is None or df_consolidado.empty:
            return pd.DataFrame()
        
        colunas_agrupamento = ['aging', 'aging_taxa']
        colunas_existentes = [col for col in colunas_agrupamento if col in df_consolidado.columns]
        
        if not colunas_existentes:
            return pd.DataFrame()
        
        colunas_valores = ['valor_liquido', 'valor_corrigido', 'multa', 'juros_moratorios', 'correcao_monetaria', 'valor_justo', 'valor_recuperavel']
        colunas_valores_existentes = [col for col in colunas_valores if col in df_consolidado.columns]
        
        agrupado = (df_consolidado
                   .groupby(colunas_existentes, dropna=False)
                   .agg({
                       'id_padronizado': 'count',
                       **{col: 'sum' for col in colunas_valores_existentes}
                   })
                   .reset_index()
                   .round(2))
        
        agrupado.rename(columns={'id_padronizado': 'qtd_registros'}, inplace=True)
        
        # Calcular percentuais de participação
        if 'valor_corrigido' in agrupado.columns:
            total_valor_corrigido = agrupado['valor_corrigido'].sum()
            if total_valor_corrigido > 0:
                agrupado['participacao_perc'] = (agrupado['valor_corrigido'] / total_valor_corrigido * 100).round(2)
        
        return agrupado
    
    def criar_arquivo_excel_consolidado(self, df_consolidado) -> BytesIO:
        """
        Cria arquivo Excel com as 5 abas solicitadas:
        1. Dicionário de Dados
        2. Dados Consolidados (sem agregação)
        3. Agrupamento Detalhado
        4. Agrupamento Consolidado  
        5. Agrupamento Geral
        """
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            
            # Aba 1: Dicionário de Dados
            df_dicionario = self.criar_dicionario_dados()
            df_dicionario.to_excel(writer, sheet_name='1_Dicionario_Dados', index=False)
            st.success(f"✅ Aba 1: Dicionário de Dados - {len(df_dicionario)} campos")
            
            # Aba 2: Dados Consolidados (sem agregação)
            if df_consolidado is not None and not df_consolidado.empty:
                df_consolidado.to_excel(writer, sheet_name='2_Dados_Consolidados', index=False)
                st.success(f"✅ Aba 2: Dados Consolidados - {len(df_consolidado):,} registros")
                
                # Aba 3: Agrupamento Detalhado
                agrupamento_detalhado = self.gerar_agrupamento_detalhado(df_consolidado)
                if not agrupamento_detalhado.empty:
                    agrupamento_detalhado.to_excel(writer, sheet_name='3_Agrupamento_Detalhado', index=False)
                    st.success(f"✅ Aba 3: Agrupamento Detalhado - {len(agrupamento_detalhado):,} grupos")
                
                # Aba 4: Agrupamento Consolidado
                agrupamento_consolidado = self.gerar_agrupamento_consolidado(df_consolidado)
                if not agrupamento_consolidado.empty:
                    agrupamento_consolidado.to_excel(writer, sheet_name='4_Agrupamento_Consolidado', index=False)
                    st.success(f"✅ Aba 4: Agrupamento Consolidado - {len(agrupamento_consolidado):,} grupos")
                
                # Aba 5: Agrupamento Geral
                agrupamento_geral = self.gerar_agrupamento_geral(df_consolidado)
                if not agrupamento_geral.empty:
                    agrupamento_geral.to_excel(writer, sheet_name='5_Agrupamento_Geral', index=False)
                    st.success(f"✅ Aba 5: Agrupamento Geral - {len(agrupamento_geral):,} grupos")
            
            # Aba adicional: Parâmetros utilizados
            params_data = {
                'Parametro': [
                    'Taxa de Multa',
                    'Taxa de Juros Moratórios',
                    'Data de Processamento',
                    'Metodologia IGP-M',
                    'Metodologia IPCA',
                    'Fonte dos Dados IGPM',
                    'Aging - Critério'
                ],
                'Valor': [
                    f"{self.params.taxa_multa:.2%}",
                    f"{self.params.taxa_juros_mensal:.2%} ao mês",
                    datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'Até 2021.05',
                    'A partir de 2021.06',
                    'SIDRA/IBGE',
                    'Baseado em dias de atraso'
                ]
            }
            df_params = pd.DataFrame(params_data)
            df_params.to_excel(writer, sheet_name='Parametros', index=False)
            st.success("✅ Aba Parâmetros")
        
        output.seek(0)
        return output

    def criar_arquivo_excel(self, df_ess=None, df_voltz=None) -> BytesIO:
        """
        Cria arquivo Excel em memória com múltiplas abas.
        """
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            
            # Aba ESS - Dados detalhados
            if df_ess is not None and not df_ess.empty:
                df_ess.to_excel(writer, sheet_name='ESS_Detalhado', index=False)
                st.success(f"✅ Aba ESS Detalhada: {len(df_ess):,} registros")
            
            # Aba Voltz - Dados detalhados
            if df_voltz is not None and not df_voltz.empty:
                df_voltz.to_excel(writer, sheet_name='Voltz_Detalhado', index=False)
                st.success(f"✅ Aba Voltz Detalhada: {len(df_voltz):,} registros")
            
            # Resumo por Aging - ESS
            if df_ess is not None and not df_ess.empty:
                resumo_ess_aging = self.gerar_resumo_por_aging(df_ess, 'ESS')
                if not resumo_ess_aging.empty:
                    resumo_ess_aging.to_excel(writer, sheet_name='ESS_Resumo_Aging', index=False)
                    st.success(f"✅ Aba ESS Resumo por Aging: {len(resumo_ess_aging)} categorias")
            
            # Resumo por Aging - Voltz
            if df_voltz is not None and not df_voltz.empty:
                resumo_voltz_aging = self.gerar_resumo_por_aging(df_voltz, 'Voltz')
                if not resumo_voltz_aging.empty:
                    resumo_voltz_aging.to_excel(writer, sheet_name='Voltz_Resumo_Aging', index=False)
                    st.success(f"✅ Aba Voltz Resumo por Aging: {len(resumo_voltz_aging)} categorias")
            
            # Resumo Consolidado por Aging (Ambas as bases)
            resumos_aging = []
            if df_ess is not None and not df_ess.empty:
                resumo_ess = self.gerar_resumo_por_aging(df_ess, 'ESS')
                if not resumo_ess.empty:
                    resumos_aging.append(resumo_ess)
            
            if df_voltz is not None and not df_voltz.empty:
                resumo_voltz = self.gerar_resumo_por_aging(df_voltz, 'Voltz')
                if not resumo_voltz.empty:
                    resumos_aging.append(resumo_voltz)
            
            if resumos_aging:
                df_aging_consolidado = pd.concat(resumos_aging, ignore_index=True)
                df_aging_consolidado.to_excel(writer, sheet_name='Resumo_Aging_Consolidado', index=False)
                st.success("✅ Aba Resumo Aging Consolidado")
            
            # Aba de resumo geral
            resumo_data = []
            
            if df_ess is not None and not df_ess.empty:
                ess_liquido = df_ess['valor_liquido'].sum() if 'valor_liquido' in df_ess.columns else 0
                ess_corrigido = df_ess['valor_corrigido'].sum() if 'valor_corrigido' in df_ess.columns else 0
                resumo_data.append({
                    'Base': 'ESS',
                    'Registros': len(df_ess),
                    'Valor_Liquido': ess_liquido,
                    'Valor_Corrigido': ess_corrigido,
                    'Percentual_Correcao': ((ess_corrigido / ess_liquido - 1) * 100) if ess_liquido > 0 else 0
                })
            
            if df_voltz is not None and not df_voltz.empty:
                voltz_liquido = df_voltz['valor_liquido'].sum() if 'valor_liquido' in df_voltz.columns else 0
                voltz_corrigido = df_voltz['valor_corrigido'].sum() if 'valor_corrigido' in df_voltz.columns else 0
                resumo_data.append({
                    'Base': 'Voltz',
                    'Registros': len(df_voltz),
                    'Valor_Liquido': voltz_liquido,
                    'Valor_Corrigido': voltz_corrigido,
                    'Percentual_Correcao': ((voltz_corrigido / voltz_liquido - 1) * 100) if voltz_liquido > 0 else 0
                })
            
            if resumo_data:
                df_resumo = pd.DataFrame(resumo_data)
                df_resumo.to_excel(writer, sheet_name='Resumo_Geral', index=False)
                st.success("✅ Aba Resumo Geral")
            
            # Aba de parâmetros utilizados
            params_data = {
                'Parametro': [
                    'Taxa de Multa',
                    'Taxa de Juros Moratórios',
                    'Data Base ESS',
                    'Data Base Voltz',
                    'Data de Processamento',
                    'Metodologia IGP-M',
                    'Metodologia IPCA'
                ],
                'Valor': [
                    f"{self.params.taxa_multa:.2%}",
                    f"{self.params.taxa_juros_mensal:.2%} ao mês",
                    self.params.data_base_ess.strftime('%d/%m/%Y'),
                    self.params.data_base_voltz.strftime('%d/%m/%Y'),
                    datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    'Até 2021.05',
                    'A partir de 2021.06'
                ]
            }
            df_params = pd.DataFrame(params_data)
            df_params.to_excel(writer, sheet_name='Parametros', index=False)
            st.success("✅ Aba Parâmetros")
        
        output.seek(0)
        return output
    
    def gerar_relatorio_texto(self, df_ess=None, df_voltz=None) -> str:
        """
        Gera relatório em texto dos resultados.
        """
        relatorio = f"""
# RELATÓRIO DE VALOR CORRIGIDO - BASES ESS E VOLTZ
## Data de Processamento: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

### PARÂMETROS UTILIZADOS:
- **Taxa de multa**: {self.params.taxa_multa:.1%}
- **Taxa de juros moratórios**: {self.params.taxa_juros_mensal:.1%} ao mês
- **Data base ESS**: {self.params.data_base_ess.strftime('%d/%m/%Y')}
- **Data base Voltz**: {self.params.data_base_voltz.strftime('%d/%m/%Y')}

### METODOLOGIA:
- **Correção monetária**: IGP-M até 2021.05, IPCA a partir de 2021.06
- **Aging**: Conforme classificação oficial FIDC Energisa
- **Valor líquido**: Principal - Não Cedido - Terceiro - CIP

---

### RESULTADOS:
"""
        
        if df_ess is not None and not df_ess.empty:
            ess_original = df_ess['valor_principal_limpo'].sum() if 'valor_principal_limpo' in df_ess.columns else 0
            ess_liquido = df_ess['valor_liquido'].sum() if 'valor_liquido' in df_ess.columns else 0
            ess_corrigido = df_ess['valor_corrigido'].sum() if 'valor_corrigido' in df_ess.columns else 0
            ess_correcao = ((ess_corrigido / ess_liquido) - 1) * 100 if ess_liquido > 0 else 0
            
            relatorio += f"""
#### BASE ESS:
- **Registros processados**: {len(df_ess):,}
- **Valor principal**: R$ {ess_original:,.2f}
- **Valor líquido**: R$ {ess_liquido:,.2f}
- **Valor corrigido**: R$ {ess_corrigido:,.2f}
- **Correção aplicada**: {ess_correcao:.2f}%
"""
        
        if df_voltz is not None and not df_voltz.empty:
            voltz_original = df_voltz['valor_principal_limpo'].sum() if 'valor_principal_limpo' in df_voltz.columns else 0
            voltz_liquido = df_voltz['valor_liquido'].sum() if 'valor_liquido' in df_voltz.columns else 0
            voltz_corrigido = df_voltz['valor_corrigido'].sum() if 'valor_corrigido' in df_voltz.columns else 0
            voltz_correcao = ((voltz_corrigido / voltz_liquido) - 1) * 100 if voltz_liquido > 0 else 0
            
            relatorio += f"""
#### BASE VOLTZ:
- **Registros processados**: {len(df_voltz):,}
- **Valor principal**: R$ {voltz_original:,.2f}
- **Valor líquido**: R$ {voltz_liquido:,.2f}
- **Valor corrigido**: R$ {voltz_corrigido:,.2f}
- **Correção aplicada**: R$ {voltz_correcao:.2f}%
"""
        
        relatorio += """
---

### PRÓXIMOS PASSOS:
1. Validar resultados com equipe técnica
2. Aplicar taxas de recuperação FIDC
3. Calcular valor presente líquido
4. Gerar análises de sensibilidade

### OBSERVAÇÕES:
- Valores corrigidos incluem: principal + multa + juros + correção monetária
- Aging calculado conforme metodologia oficial
- Dados prontos para próxima fase do processo FIDC

---
*Relatório gerado automaticamente pelo Sistema FIDC Energisa*
"""
        
        return relatorio
    
    def gerar_relatorio_texto_generico(self, bases_finais):
        """
        Gera relatório texto para múltiplas distribuidoras.
        """
        if not bases_finais:
            return "Nenhuma base de dados processada."
        
        relatorio = f"""# RELATÓRIO FIDC - ANÁLISE DE CARTEIRAS
**Data de Geração:** {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

## RESUMO EXECUTIVO

"""
        
        # Consolidado geral
        total_registros = 0
        total_valor_liquido = 0
        total_valor_corrigido = 0
        
        for distribuidora, df in bases_finais.items():
            if not df.empty:
                total_registros += len(df)
                if 'valor_liquido' in df.columns:
                    total_valor_liquido += df['valor_liquido'].sum()
                if 'valor_corrigido' in df.columns:
                    total_valor_corrigido += df['valor_corrigido'].sum()
        
        relatorio += f"""
**CONSOLIDADO GERAL:**
- Total de Registros: {total_registros:,}
- Valor Líquido Total: R$ {total_valor_liquido:,.2f}
- Valor Corrigido Total: R$ {total_valor_corrigido:,.2f}
- Percentual de Correção: {((total_valor_corrigido/total_valor_liquido - 1) * 100):.2f}%

## DETALHAMENTO POR DISTRIBUIDORA

"""
        
        # Detalhes por distribuidora
        for distribuidora, df in bases_finais.items():
            if df.empty:
                continue
                
            relatorio += f"""
### {distribuidora}

**Indicadores Principais:**
- Registros: {len(df):,}
"""
            
            if 'valor_liquido' in df.columns:
                valor_liquido = df['valor_liquido'].sum()
                relatorio += f"- Valor Líquido: R$ {valor_liquido:,.2f}\n"
            
            if 'valor_corrigido' in df.columns:
                valor_corrigido = df['valor_corrigido'].sum()
                relatorio += f"- Valor Corrigido: R$ {valor_corrigido:,.2f}\n"
                
                if 'valor_liquido' in df.columns and valor_liquido > 0:
                    perc_correcao = ((valor_corrigido/valor_liquido - 1) * 100)
                    relatorio += f"- Percentual de Correção: {perc_correcao:.2f}%\n"
            
            # Distribuição por aging se disponível
            if 'aging' in df.columns:
                aging_dist = df.groupby('aging')['valor_corrigido'].sum() if 'valor_corrigido' in df.columns else df.groupby('aging').size()
                relatorio += f"\n**Distribuição por Aging:**\n"
                for aging, valor in aging_dist.items():
                    if 'valor_corrigido' in df.columns:
                        relatorio += f"- {aging}: R$ {valor:,.2f}\n"
                    else:
                        relatorio += f"- {aging}: {valor:,} registros\n"
        
        relatorio += f"""

### OBSERVAÇÕES:
- Valores corrigidos incluem: principal + multa + juros + correção monetária
- Aging calculado conforme metodologia oficial
- Dados prontos para próxima fase do processo FIDC

---
*Relatório gerado automaticamente pelo Sistema FIDC Energisa*
"""
        
        return relatorio
    
    def criar_arquivo_excel_generico(self, bases_finais):
        """
        Cria arquivo Excel consolidado para múltiplas distribuidoras.
        """
        if not bases_finais:
            return BytesIO()
        
        # Criar buffer para o arquivo Excel
        excel_buffer = BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Aba de resumo consolidado
            dados_resumo = []
            for distribuidora, df in bases_finais.items():
                if df.empty:
                    continue
                    
                dados_resumo.append({
                    'Distribuidora': distribuidora,
                    'Registros': len(df),
                    'Valor_Liquido': df['valor_liquido'].sum() if 'valor_liquido' in df.columns else 0,
                    'Valor_Corrigido': df['valor_corrigido'].sum() if 'valor_corrigido' in df.columns else 0,
                    'Multa_Total': df['multa'].sum() if 'multa' in df.columns else 0,
                    'Juros_Total': df['juros_moratorios'].sum() if 'juros_moratorios' in df.columns else 0,
                    'Correcao_Total': df['correcao_monetaria'].sum() if 'correcao_monetaria' in df.columns else 0
                })
            
            if dados_resumo:
                df_resumo = pd.DataFrame(dados_resumo)
                df_resumo['Perc_Correcao'] = ((df_resumo['Valor_Corrigido'] / df_resumo['Valor_Liquido'] - 1) * 100).round(2)
                df_resumo.to_excel(writer, sheet_name='Resumo_Consolidado', index=False)
            
            # Aba para cada distribuidora
            for distribuidora, df in bases_finais.items():
                if df.empty:
                    continue
                    
                # Nome da aba (limitado a 31 caracteres)
                nome_aba = distribuidora[:31] if len(distribuidora) > 31 else distribuidora
                df.to_excel(writer, sheet_name=nome_aba, index=False)
                
                # Resumo por aging para esta distribuidora
                if 'aging' in df.columns:
                    resumo_aging = self.gerar_resumo_por_aging(df, distribuidora)
                    if not resumo_aging.empty:
                        nome_aba_aging = f"{distribuidora[:25]}_Aging"
                        resumo_aging.to_excel(writer, sheet_name=nome_aba_aging, index=True)
        
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
