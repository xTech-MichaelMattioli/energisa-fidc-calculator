# 📊 DICIONÁRIO DE DADOS - DataFrame Final (df_final)

## Sumário Executivo

Este documento descreve todas as colunas do DataFrame final (`df_final`) exportado pelo sistema FIDC Calculator - Distribuidoras. O DataFrame contém **42 colunas** que representam todo o fluxo de processamento desde os dados brutos até o cálculo final do valor justo.

**Total de registros processados:** 239.539  
**Arquivo de referência:** `FIDC_Dados_Brutos_YYYYMMDD_HHMMSS.csv/xlsx`  
**Data de geração:** 06/08/2025

---

## 📋 ESTRUTURA GERAL DO DATASET

O DataFrame está organizado em **6 grupos funcionais** principais:

1. **🏢 Dados Básicos do Cliente** (Colunas 1-9)
2. **🗂️ Metadados e Controle** (Colunas 10-16)  
3. **⏰ Aging e Temporalidade** (Colunas 17-19)
4. **💰 Valores Limpos e Líquidos** (Colunas 20-24)
5. **📈 Correção Monetária** (Colunas 25-32)
6. **🎯 Taxa de Recuperação e Valor Justo** (Colunas 33-42)

---

## 📖 DICIONÁRIO DETALHADO DAS COLUNAS

### 🏢 GRUPO 1: DADOS BÁSICOS DO CLIENTE

| # | Campo | Tipo | Descrição | Exemplo | Observações |
|---|--------|------|-----------|---------|-------------|
| 1 | **nome_cliente** | `object` | Nome do cliente titular da conta | "PAULO ROBERTO FLORES" | Campo obrigatório para identificação |
| 2 | **documento** | `float64` | CPF/CNPJ do cliente | `NaN` | Frequentemente vazio (0 non-null) |
| 3 | **contrato** | `float64` | Número do contrato de energia | `19.0` | Identificador único do contrato |
| 4 | **classe** | `object` | Classificação do cliente | "Residencial" | Tipos: Residencial, Comercial, Industrial, etc. |
| 5 | **situacao** | `object` | Status atual do cliente | "Desligado" | Estados: Ativo, Desligado, Suspenso, etc. |
| 6 | **valor_principal** | `float64` | Valor original da dívida | `115.00` | Valor base antes de deduções |
| 7 | **valor_nao_cedido** | `float64` | Parcela não cedida ao FIDC | `0.0` | Valor retido pela distribuidora |
| 8 | **valor_terceiro** | `float64` | Valores de terceiros | `0.0` | Tributos, taxas de terceiros |
| 9 | **valor_cip** | `float64` | Valor CIP (Contribuição de Iluminação Pública) | `2.37` | Taxa municipal específica |

### 🗂️ GRUPO 2: METADADOS E CONTROLE

| # | Campo | Tipo | Descrição | Exemplo | Observações |
|---|--------|------|-----------|---------|-------------|
| 10 | **data_vencimento** | `object` | Data original de vencimento (string) | "2026-02-06 10:07:09.771992" | Formato timestamp original |
| 11 | **empresa** | `object` | Código da distribuidora | "ESS" | ESS, EMR, etc. |
| 12 | **tipo** | `object` | Classificação do negócio | "Privado" | Privado, Público, Hospital |
| 13 | **status** | `object` | Status da cobrança | "Incobrável" | Cobrável, Incobrável, Em análise |
| 14 | **id_padronizado** | `object` | Identificador único gerado | "1. ESS_BRUTA_30.04.xlsx_PAULO..." | Chave primária para rastreamento |
| 15 | **base_origem** | `object` | Arquivo de origem dos dados | "1. ESS_BRUTA_30.04.xlsx" | Rastreabilidade da fonte |
| 16 | **data_base** | `object` | Data de referência para cálculos | "2025-04-30" | Data fixa para todos os cálculos |

### ⏰ GRUPO 3: AGING E TEMPORALIDADE

| # | Campo | Tipo | Descrição | Exemplo | Observações |
|---|--------|------|-----------|---------|-------------|
| 17 | **data_vencimento_limpa** | `object` | Data de vencimento padronizada | "2013-08-27" | Formato YYYY-MM-DD limpo |
| 18 | **dias_atraso** | `int64` | Dias entre vencimento e data base | `0` | Cálculo: data_base - data_vencimento |
| 19 | **aging** | `object` | Classificação de aging | "Maior que 1080 dias" | 9 faixas: A vencer até >1080 dias |

### 💰 GRUPO 4: VALORES LIMPOS E LÍQUIDOS

| # | Campo | Tipo | Descrição | Exemplo | Observações |
|---|--------|------|-----------|---------|-------------|
| 20 | **valor_principal_limpo** | `float64` | Valor principal sem formatação | `115.00` | Numérico puro |
| 21 | **valor_nao_cedido_limpo** | `float64` | Valor não cedido limpo | `0.0` | Numérico puro |
| 22 | **valor_terceiro_limpo** | `float64` | Valor terceiros limpo | `0.0` | Numérico puro |
| 23 | **valor_cip_limpo** | `float64` | Valor CIP limpo | `2.37` | Numérico puro |
| 24 | **valor_liquido** | `float64` | Valor líquido final | `95.32` | **Fórmula:** principal - nao_cedido - terceiro - cip |

### 📈 GRUPO 5: CORREÇÃO MONETÁRIA

| # | Campo | Tipo | Descrição | Exemplo | Observações |
|---|--------|------|-----------|---------|-------------|
| 25 | **multa** | `float64` | Multa calculada | `1.9064` | **Fórmula:** valor_liquido × taxa_multa |
| 26 | **meses_atraso** | `float64` | Meses de atraso calculados | `141.366667` | dias_atraso ÷ 30 |
| 27 | **juros_moratorios** | `float64` | Juros moratórios | `1334.750707` | **Fórmula:** valor_liquido × taxa_juros × meses |
| 28 | **indice_vencimento** | `float64` | Índice IGP-M no vencimento | `529.09` | Obtido da tabela histórica |
| 29 | **indice_base** | `float64` | Índice IGP-M na data base | `1349.824` | Índice de referência (data_base) |
| 30 | **fator_correcao** | `float64` | Fator de correção monetária | `2.551218` | **Fórmula:** indice_base ÷ indice_vencimento |
| 31 | **correcao_monetaria** | `float64` | Correção monetária aplicada | `147.862112` | **Fórmula:** valor_liquido × (fator_correcao - 1) |
| 32 | **valor_corrigido** | `float64` | Valor final corrigido | `379.839219` | **Fórmula:** valor_liquido + multa + juros + correção |

### 🎯 GRUPO 6: TAXA DE RECUPERAÇÃO E VALOR JUSTO

| # | Campo | Tipo | Descrição | Exemplo | Observações |
|---|--------|------|-----------|---------|-------------|
| 33 | **aging_taxa** | `object` | Aging mapeado para taxa | "Demais anos" | Mapeamento: >1080 dias → Demais anos |
| 34 | **taxa_recuperacao** | `float64` | Taxa de recuperação esperada | `0.003954` | Taxa decimal (ex: 0.39%) |
| 35 | **prazo_recebimento** | `float64` | Prazo esperado de recebimento | `42.0` | Meses até recebimento esperado |
| 36 | **valor_recuperavel** | `float64` | Valor esperado de recuperação | `1.502052` | **Fórmula:** valor_corrigido × taxa_recuperacao |
| 37 | **ipca_12m_real** | `float64` | IPCA 12 meses (decimal) | `0.054035` | Taxa IPCA anual em decimal |
| 38 | **ipca_mensal** | `float64` | IPCA mensal equivalente | `0.004395` | Taxa IPCA mensal derivada |
| 39 | **mês_recebimento** | `int64` | Mês esperado de recebimento | `6` | Baseado no prazo_recebimento |
| 40 | **fator_exponencial** | `float64` | Fator exponencial IPCA | `1.026662` | **Fórmula:** (1 + ipca_12m)^(prazo/12) |
| 41 | **multa_para_justo** | `float64` | Multa ajustada para valor justo | `0.06` | Multa proporcional aplicada |
| 42 | **valor_justo** | `float64` | Valor justo final | `1.632223` | **Fórmula:** (valor_corrigido × fator_exponencial × taxa_recuperacao) |

---

## 🧮 PRINCIPAIS FÓRMULAS UTILIZADAS

### 💰 Cálculo do Valor Líquido
```
valor_liquido = valor_principal - valor_nao_cedido - valor_terceiro - valor_cip
```

### ⏰ Cálculo do Aging
```
dias_atraso = data_base - data_vencimento_limpa
aging = classificacao_por_faixas(dias_atraso)
```

### 📈 Correção Monetária Completa
```
fator_correcao = indice_base ÷ indice_vencimento
multa = valor_liquido × taxa_multa
meses_atraso = dias_atraso ÷ 30
juros_moratorios = valor_liquido × taxa_juros_mensal × meses_atraso
correcao_monetaria = valor_liquido × (fator_correcao - 1)
valor_corrigido = valor_liquido + multa + juros_moratorios + correcao_monetaria
```

### 🎯 Valor Justo com Progressão Exponencial
```
fator_exponencial = (1 + ipca_12m_real)^(prazo_recebimento ÷ 12)
valor_justo = valor_corrigido × fator_exponencial × taxa_recuperacao
```

---

## 📊 ESTATÍSTICAS GERAIS DO DATASET

| Métrica | Valor |
|---------|--------|
| **Total de Registros** | 239.539 |
| **Total de Colunas** | 42 |
| **Empresas Únicas** | ESS, EMR, etc. |
| **Tipos de Aging** | 9 classificações |
| **Memória Utilizada** | ~76.8 MB |
| **Campos Obrigatórios** | 41 de 42 (exceto documento) |

---

## 🔧 PARÂMETROS DE CONFIGURAÇÃO UTILIZADOS

| Parâmetro | Valor Padrão | Descrição |
|-----------|--------------|-----------|
| **taxa_multa** | 2% | Taxa de multa aplicada |
| **taxa_juros_mensal** | 1% | Taxa de juros moratórios mensal |
| **data_base** | 2025-04-30 | Data de referência para cálculos |
| **ipca_12m** | ~5.4% | IPCA acumulado 12 meses |

---

## ⚠️ OBSERVAÇÕES IMPORTANTES

### 🔴 Campos Críticos para Validação
- `nome_cliente`: Sempre preenchido (100% dos casos)
- `valor_liquido`: Base para todos os cálculos posteriores
- `data_vencimento_limpa`: Essencial para aging
- `aging`: Determina a taxa de recuperação

### 🟡 Campos com Dados Faltantes
- `documento`: 0% preenchido (pode estar em formato não reconhecido)
- `classe`: 99.9% preenchido (1 registro faltante)

### 🟢 Campos Calculados Automaticamente
- Todos os campos dos grupos 3, 4, 5 e 6 são calculados automaticamente
- Não devem ser editados manualmente
- Dependem dos parâmetros de configuração do sistema

---

## 📚 REFERÊNCIAS TÉCNICAS

- **Metodologia FIDC**: Baseada em regulamentação CVM
- **Índices de Correção**: IGP-M (FGV) e IPCA (IBGE)
- **Aging FIDC**: Padrão de mercado para fundos de direitos creditórios
- **Valor Justo**: Metodologia com progressão exponencial IPCA

---

*Documento gerado automaticamente pelo FIDC Calculator - Distribuidoras*  
*Versão: 1.0 | Data: 06/08/2025*
