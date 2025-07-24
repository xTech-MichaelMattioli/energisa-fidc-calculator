# 🔋 ENERGISA Data Refactor Wizard - Sistema de Análise FIDC

> **Sistema especializado para cálculo de valor justo de carteiras inadimplentes para Fundos de Investimento em Direitos Creditórios (FIDC) das distribuidoras Energisa**

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Contexto do Projeto](#-contexto-do-projeto)
- [Base de Cálculo](#-base-de-cálculo)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Como Utilizar](#-como-utilizar)
- [Metodologia de Cálculo](#-metodologia-de-cálculo)
- [Estrutura dos Dados](#-estrutura-dos-dados)
- [Exemplos Práticos](#-exemplos-práticos)
- [Documentação Técnica](#-documentação-técnica)
- [Suporte e Contribuição](#-suporte-e-contribuição)

---

## 🎯 Visão Geral

O **Energisa Data Refactor Wizard** é uma aplicação Streamlit desenvolvida para automatizar e padronizar o processo de avaliação de carteiras inadimplentes das distribuidoras do Grupo Energisa, transformando ativos de baixa liquidez em valores precisos para negociação com Fundos de Investimento em Direitos Creditórios (FIDC).

### ✨ Principais Funcionalidades

- **📊 Análise Automatizada**: Processamento de milhões de registros de inadimplência
- **💰 Cálculo de Valor Justo**: Determinação precisa do valor de mercado das carteiras
- **📈 Aging Inteligente**: Classificação temporal automática da inadimplência
- **🔄 Correção Monetária**: Atualização por IGPM/IPCA
- **📋 Relatórios Executivos**: Dashboards interativos e exportações Excel

---

## 🏢 Contexto do Projeto

### Sobre a Energisa

A **Energisa** é o maior grupo privado do setor elétrico brasileiro, com:
- **120 anos** de história (fundada em 1905)
- **9 distribuidoras** + 13 concessões de transmissão
- Presença em múltiplos estados brasileiros
- Sede em Cataguases, MG

### O Desafio FIDC

As distribuidoras da Energisa possuem carteiras significativas de créditos inadimplentes que precisam ser convertidas em recursos financeiros disponíveis através de operações FIDC, permitindo:

- ✅ **Liquidez Imediata** das carteiras inadimplentes
- ✅ **Transferência de Risco** para especialistas em recuperação
- ✅ **Redução de Custos** de cobrança interna
- ✅ **Liberação de Capital** para investimentos em infraestrutura
- ✅ **Melhoria de Indicadores** financeiros

---

## 🧮 Base de Cálculo

### Metodologia de Avaliação

O sistema implementa uma metodologia complexa baseada em **análise de valor presente líquido** que considera:

### Fundamentos Teóricos

**Conceito de Valor Justo:** O valor justo representa o montante pelo qual um ativo pode ser negociado entre partes conhecedoras e dispostas a negociar em uma transação sem favorecimentos. No contexto de recebíveis em atraso, incorpora não apenas o valor principal da dívida, mas também os encargos financeiros decorrentes da inadimplência e a probabilidade de recuperação efetiva dos valores.

**Metodologia de Correção Monetária:** A correção segue a metodologia híbrida estabelecida para o setor elétrico brasileiro, utilizando IGP-M até maio/2021 e IPCA a partir de junho/2021, refletindo mudanças regulatórias e maior aderência à inflação oficial.

#### 1. **Classificação por Aging**
```
A vencer → Menor que 30 dias → 31-59 dias → 60-89 dias → 90-119 dias → 
120-359 dias → 360-719 dias → 720-1080 dias → Maior que 1080 dias
```

**Critérios de Classificação Detalhados:**

| Faixa de Dias | Classificação | Critério de Negócio |
|---------------|---------------|-------------------|
| DA ≤ 0 | A vencer | Ainda não vencido |
| 0 < DA ≤ 30 | Menor que 30 dias | Inadimplência recente |
| 30 < DA ≤ 59 | De 31 a 59 dias | Inadimplência inicial |
| 59 < DA ≤ 89 | De 60 a 89 dias | Inadimplência estabelecida |
| 89 < DA ≤ 119 | De 90 a 119 dias | Inadimplência consolidada |
| 119 < DA ≤ 359 | De 120 a 359 dias | Inadimplência prolongada |
| 359 < DA ≤ 719 | De 360 a 719 dias | Inadimplência de segundo ano |
| 719 < DA ≤ 1080 | De 720 a 1080 dias | Inadimplência de terceiro ano |
| DA > 1080 | Maior que 1080 dias | Inadimplência de longo prazo |

#### 2. **Taxas de Recuperação por Categoria**
| Aging | Taxa de Recuperação |
|-------|-------------------|
| A vencer | 0,89% |
| Menor que 30 dias | 47,00% |
| De 31 a 59 dias | 39,00% |
| De 60 a 89 dias | 52,00% |
| De 90 a 119 dias | 57,00% |
| De 120 a 359 dias | 47,00% |
| De 360 a 719 dias | 2,00% |
| De 720 a 1080 dias | 1,00% |
| Maior que 1080 dias | 0,70% |

**Metodologia de Correção Monetária Híbrida:**
```
Índice = {
    IGP-M,  se data ≤ maio/2021
    IPCA,   se data > maio/2021
}
```

**Mapeamento de Aging para Categorias de Recuperação:**

| Aging Detalhado | Categoria de Recuperação |
|-----------------|-------------------------|
| A vencer | A vencer |
| Menor que 30 dias até De 120 a 359 dias | Primeiro ano |
| De 360 a 719 dias | Segundo ano |
| De 720 a 1080 dias | Terceiro ano |
| Maior que 1080 dias | Demais anos |

#### 3. **Modelagem Matemática Detalhada**

**Cálculo do Valor Líquido:**
```
VL = VP - VNC - VT - VCIP
```
Onde:
- **VL**: Valor Líquido (base para cálculos)
- **VP**: Valor Principal (valor original da fatura)
- **VNC**: Valor Não Cedido (parcelas excluídas da cessão)
- **VT**: Valor de Terceiros (encargos de terceiros)
- **VCIP**: Valor CIP (Contribuição para Iluminação Pública)

**Cálculo do Aging (Tempo de Inadimplência):**
```
DA = DB - DV
```
Onde:
- **DA**: Dias de Atraso
- **DB**: Data Base de Cálculo
- **DV**: Data de Vencimento Original

**Cálculo da Multa Contratual:**
```
M = VL × 0,02 × I(DA > 0)
```
Onde:
- **M**: Multa (2% sobre valor líquido)
- **I(DA > 0)**: Função indicadora (1 se em atraso, 0 se não)

**Cálculo dos Juros Moratórios:**
```
JM = VL × 0,01 × (DA / 30) × I(DA > 0)
```
Onde:
- **JM**: Juros Moratórios (1% ao mês proporcional)
- **DA / 30**: Conversão de dias para meses

**Cálculo da Correção Monetária:**
```
CM = VL × (IDB / IDV - 1) × I(DA > 0)
```
Onde:
- **CM**: Correção Monetária
- **IDB**: Índice na Data Base (IGPM até mai/2021, IPCA após)
- **IDV**: Índice na Data de Vencimento

**Valor Corrigido Total:**
```
VC = VL + M + JM + CM
```

**Valor Recuperável:**
```
VR = VC × TR(E, T, A)
```
Onde:
- **TR(E, T, A)**: Taxa de Recuperação função da Empresa, Tipo e Aging

**Valor Justo (Presente):**
```
VJ = VR ÷ (1 + TD)^(PR/365)
```
Onde:
- **TD**: Taxa de Desconto (8% a 15% a.a.)
- **PR**: Prazo de Recebimento em dias (específico por perfil)

**Fórmula Consolidada do Sistema:**
```
VJ = [(VL + VL×0,02×I(DA>0) + VL×0,01×(DA/30)×I(DA>0) + VL×(IDB/IDV-1)×I(DA>0)) × TR(E,T,A)] ÷ (1+TD)^(PR/365)
```

#### 4. **Validações e Tratamento de Dados**

**Tratamento de Dados Ausentes:**
- Valores numéricos ausentes: Substituição por zero
- Datas inválidas: Utilização de data base padrão
- Índices não encontrados: Utilização de valores de fallback

**Validações de Integridade:**
- Garantia de que VL ≥ 0 (valores líquidos não negativos)
- Validação de consistência temporal (datas futuras)
- Verificação de disponibilidade de índices de correção
- Aplicação condicional de encargos apenas para DA > 0

**Verificações de Consistência:**
- VC = VL + M + JM + CM (soma de componentes)
- Encargos aplicados apenas para valores em atraso
- Limites de sanidade para valores extremos

### Resultados Esperados

**Por Aging:**
- **Primeiro ano** (até 359 dias): 25% a 50% de recuperação
- **Segundo ano** (360-719 dias): 1% a 3% de recuperação  
- **Terceiro ano** (720-1080 dias): 0,5% a 1,5% de recuperação
- **Acima de 3 anos**: 0,3% a 0,8% de recuperação

**Consolidado Geral:**
- Carteiras balanceadas: **3% a 5%** do valor corrigido
- Carteiras antigas: **1% a 2%** do valor corrigido
- Carteiras recentes: **5% a 8%** do valor corrigido

---

## 🏗️ Arquitetura do Sistema

### Estrutura de Módulos

```
📁 energisa-data-refactor-wizard/
├── 📄 app.py                    # Aplicação principal Streamlit
├── 📄 requirements.txt          # Dependências do projeto
├── 📁 utils/                    # Módulos utilitários
│   ├── parametros_correcao.py   # Parâmetros e índices de correção
│   ├── analisador_bases.py      # Análise e validação de dados
│   ├── mapeador_campos.py       # Mapeamento de campos
│   ├── calculador_aging.py      # Cálculos de aging
│   ├── calculador_correcao.py   # Correção monetária
│   └── exportador_resultados.py # Geração de relatórios
├── 📁 BASE_DADOS/               # Bases de dados das distribuidoras
├── 📁 DOCS/                     # Documentação técnica
└── 📁 data/                     # Dados auxiliares (índices, etc.)
```

### Fluxo de Processamento

```
Dados Brutos → Mapeamento Campos → Cálculo Aging → Correção Monetária → 
Taxa Recuperação → Valor Presente → Relatórios
```

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

### 1. Clone do Repositório

```bash
git clone https://github.com/xTech-MichaelMattioli/energisa-data-refactor-wizard.git
cd energisa-data-refactor-wizard
```

### 2. Instalação de Dependências

```bash
pip install -r requirements.txt
```

### 3. Execução da Aplicação

```bash
streamlit run app.py
```

A aplicação estará disponível em: `http://localhost:8501`

---

## 📖 Como Utilizar

### Passo 1: Upload de Dados

1. Acesse a aplicação no navegador
2. Na barra lateral, faça upload dos arquivos Excel das distribuidoras
3. Formatos suportados: `.xlsx`, `.xls`

### Passo 2: Configuração de Parâmetros

1. **Data Base**: Define a data de referência para cálculos (padrão: 30/04/2025)
2. **Índice de Correção**: Escolha entre IGPM ou IPCA
3. **Taxa de Desconto**: Configure a taxa para valor presente (padrão: 12% a.a.)

### Passo 3: Mapeamento de Campos

O sistema oferece mapeamento automático, mas você pode ajustar manualmente:

- **Campos Obrigatórios**: Valor Principal, Data Vencimento, Empresa, Tipo
- **Campos Opcionais**: COSIP, Valores de Terceiros, Status, Classe

### Passo 4: Processamento

1. Clique em "Processar Dados"
2. Acompanhe o progresso nas barras de status
3. Visualize os resultados em tempo real

### Passo 5: Análise e Exportação

1. Explore os dashboards interativos
2. Analise métricas por aging, distribuidora e tipo
3. Exporte relatórios em Excel
4. Baixe análises consolidadas

---

## 🔬 Metodologia de Cálculo

### Sequência de Processamento

#### 1. **Limpeza e Padronização**
- Conversão de tipos de dados
- Tratamento de valores nulos
- Padronização de formatos de data

#### 2. **Cálculo de Aging**
```python
def classificar_aging(dias_atraso):
    if dias <= 0: return 'A vencer'
    elif dias <= 30: return 'Menor que 30 dias'
    elif dias <= 59: return 'De 31 a 59 dias'
    # ... demais classificações
```

#### 3. **Correção Monetária**
```python
fator_correcao = indice_base / indice_vencimento
correcao_monetaria = valor_liquido * (fator_correcao - 1)
```

#### 4. **Valor Corrigido Total**
```python
valor_corrigido = (valor_liquido + 
                  multa + 
                  correcao_monetaria + 
                  juros_moratorios)
```

#### 5. **Aplicação de Taxa de Recuperação**
```python
valor_recuperavel = valor_corrigido * taxa_recuperacao_por_aging
```

#### 6. **Cálculo do Valor Presente**
```python
valor_justo = valor_recuperavel / (1 + taxa_desconto) ** (prazo_anos)
```

---

## 📊 Estrutura dos Dados

### Campos de Entrada Esperados

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| **Valor Principal** | Monetário | ✅ | Valor original da dívida |
| **Data Vencimento** | Data | ✅ | Data de vencimento original |
| **Empresa** | Texto | ✅ | Código/nome da distribuidora |
| **Tipo** | Texto | ✅ | Classificação do cliente |
| **COSIP** | Monetário | ❌ | Contribuição Iluminação Pública |
| **Valores Terceiros** | Monetário | ❌ | Encargos de terceiros |
| **Juros/Multa** | Monetário | ❌ | Encargos já aplicados |
| **Status** | Texto | ❌ | Situação do contrato |
| **Classe** | Numérico | ❌ | Categoria tarifária |

### Campos de Saída Gerados

| Campo | Descrição |
|-------|-----------|
| **dias_atraso** | Dias entre vencimento e data base |
| **aging** | Classificação temporal da inadimplência |
| **valor_liquido** | Valor após deduções |
| **correcao_monetaria** | Correção por IGPM/IPCA |
| **valor_corrigido** | Valor total atualizado |
| **taxa_recuperacao** | Taxa aplicada por aging |
| **valor_recuperavel** | Valor estimado de recuperação |
| **valor_justo** | Valor presente líquido final |

---

## 💡 Exemplos Práticos

### Exemplo 1: Cliente Residencial

**Dados de Entrada:**
- Valor Principal (VP): R$ 1.500,00
- Valor Não Cedido (VNC): R$ 0,00
- Valor Terceiros (VT): R$ 0,00
- Valor CIP (VCIP): R$ 0,00
- Data Vencimento: 15/01/2024
- Data Base: 30/04/2025
- Dias de Atraso: 470 dias
- Aging: "De 360 a 719 dias"

**Processamento Matemático:**

1. **Valor Líquido**: VL = 1.500 - 0 - 0 - 0 = R$ 1.500,00

2. **Multa**: M = 1.500 × 0,02 × 1 = R$ 30,00

3. **Juros Moratórios**: JM = 1.500 × 0,01 × (470/30) × 1 = R$ 235,00

4. **Correção Monetária**: CM = 1.500 × (1,12 - 1) × 1 = R$ 180,00

5. **Valor Corrigido**: VC = 1.500 + 30 + 235 + 180 = R$ 1.945,00

6. **Taxa Recuperação**: 2% (segundo ano)

7. **Valor Recuperável**: VR = 1.945 × 0,02 = R$ 38,90

8. **Valor Justo**: VJ = 38,90 ÷ (1,12)^(548/365) = R$ 32,50

**Resultado Final: R$ 32,50 (1,67% do valor corrigido)**

### Exemplo 2: Cliente Comercial

**Dados de Entrada:**
- Valor Principal (VP): R$ 10.000,00
- Valor Não Cedido (VNC): R$ 500,00
- Valor Terceiros (VT): R$ 200,00
- Valor CIP (VCIP): R$ 300,00
- Data Vencimento: 20/12/2024
- Data Base: 30/04/2025
- Dias de Atraso: 130 dias
- Aging: "De 120 a 359 dias"

**Processamento Matemático:**

1. **Valor Líquido**: VL = 10.000 - 500 - 200 - 300 = R$ 9.000,00

2. **Multa**: M = 9.000 × 0,02 × 1 = R$ 180,00

3. **Juros Moratórios**: JM = 9.000 × 0,01 × (130/30) × 1 = R$ 390,00

4. **Correção Monetária**: CM = 9.000 × (1,05 - 1) × 1 = R$ 450,00

5. **Valor Corrigido**: VC = 9.000 + 180 + 390 + 450 = R$ 10.020,00

6. **Taxa Recuperação**: 47% (primeiro ano)

7. **Valor Recuperável**: VR = 10.020 × 0,47 = R$ 4.709,40

8. **Valor Justo**: VJ = 4.709,40 ÷ (1,12)^(180/365) = R$ 4.447,15

**Resultado Final: R$ 4.447,15 (44,4% do valor corrigido)**

---

## 📚 Documentação Técnica

### Documentos Disponíveis

- **01 - Resumo Executivo**: Visão geral do projeto FIDC
- **02 - Análise Especializada**: Detalhamento técnico da proposta
- **03 - Documentação Oficial**: Mecânica completa de cálculos
- **04 - Sumário Executivo**: Entendimento integrado dos cálculos
- **05 - Anotações Reunião**: Insights sobre bases de dados

### Arquivos de Referência

- **FIDC_Calculo_Valor_Corrigido.ipynb**: Notebook original de desenvolvimento
- **Parte10.xlsx**: Modelo Excel de referência com fórmulas
- **Dicionários de Dados**: Mapeamento detalhado de campos

---

## 🔧 Configurações Avançadas

### Parâmetros de Correção Monetária

```python
# Em utils/parametros_correcao.py
class ParametrosCorrecao:
    def __init__(self):
        self.taxa_multa = 0.02           # 2% de multa
        self.taxa_juros_mensal = 0.01    # 1% ao mês
        self.data_base_padrao = datetime(2025, 4, 30)
```

### Personalização de Taxas de Recuperação

O sistema permite carregar tabelas customizadas de taxa de recuperação através do upload de arquivos Excel com a estrutura:

| Empresa | Tipo | Aging | Taxa de recuperação | Prazo de recebimento |
|---------|------|-------|-------------------|-------------------|
| ESS | Privado | Primeiro ano | 0.45 | 6 |
| EMR | Público | Segundo ano | 0.02 | 18 |

---

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Erro de Formato de Data
**Problema**: "Erro na conversão de datas"
**Solução**: Verifique se as datas estão no formato DD/MM/AAAA ou AAAA-MM-DD

#### 2. Campos Não Reconhecidos
**Problema**: Mapeamento automático falha
**Solução**: Use o mapeamento manual na interface

#### 3. Valores Zerados
**Problema**: Todos os valores justos são zero
**Solução**: Verifique se os dados de taxa de recuperação foram carregados

#### 4. Performance Lenta
**Problema**: Processamento demorado
**Solução**: Processe arquivos menores (máximo 100k registros por vez)

### Logs de Debug

Para habilitar logs detalhados, adicione ao início do arquivo:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🤝 Suporte e Contribuição

### Reportar Issues

Para reportar bugs ou sugerir melhorias:

1. Acesse: [GitHub Issues](https://github.com/xTech-MichaelMattioli/energisa-data-refactor-wizard/issues)
2. Descreva o problema detalhadamente
3. Inclua arquivos de exemplo (sem dados sensíveis)
4. Especifique versão do sistema e Python

### Contribuir com Código

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m "Adiciona nova funcionalidade"`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

### Contato da Equipe

- **Desenvolvedor Principal**: Michael Mattioli
- **Organização**: Business Integration Partners LTDA
- **Email**: michael.mattioli@bip-group.com

---

## 📄 Licença

Este projeto está licenciado sob os termos definidos pela Business Integration Partners. Todos os direitos reservados.

**Confidencialidade**: Este sistema contém metodologias proprietárias e deve ser usado exclusivamente para os fins autorizados pela Energisa S.A.

---

## 🏆 Reconhecimentos

Desenvolvido por **Business Integration Partners (BIP)** para o Grupo **Energisa**, este sistema representa o estado da arte em avaliação de carteiras FIDC para o setor elétrico brasileiro.

**Tecnologias Utilizadas:**
- Streamlit para interface web
- Pandas para manipulação de dados
- Plotly para visualizações
- SidraPI para índices econômicos

---

*© 2025 Business Integration Partners  | Desenvolvido para Energisa S.A.*
