# Modelagem Matemática do Sistema FIDC Calculator

## Introdução

O Sistema FIDC Calculator implementa uma metodologia matemática rigorosa para o cálculo de valor justo de carteiras de recebíveis de distribuidoras de energia elétrica. A modelagem baseia-se em princípios financeiros consolidados, incorporando correção monetária, juros moratórios, multas contratuais e taxas de recuperação específicas do setor elétrico brasileiro.

## Fundamentos Teóricos

### Conceito de Valor Justo

O valor justo representa o montante pelo qual um ativo pode ser negociado entre partes conhecedoras e dispostas a negociar em uma transação sem favorecimentos. No contexto de recebíveis em atraso, o valor justo incorpora não apenas o valor principal da dívida, mas também os encargos financeiros decorrentes da inadimplência e a probabilidade de recuperação efetiva dos valores.

### Metodologia de Correção Monetária

A correção monetária adotada segue a metodologia híbrida estabelecida para o setor elétrico brasileiro:

- **Período até maio/2021**: Utilização do Índice Geral de Preços do Mercado (IGP-M) da Fundação Getúlio Vargas
- **Período a partir de junho/2021**: Utilização do Índice Nacional de Preços ao Consumidor Amplo (IPCA) do Instituto Brasileiro de Geografia e Estatística

Esta transição reflete mudanças regulatórias no setor elétrico e busca maior aderência à inflação oficial do país.

## Modelagem Matemática Detalhada

### 1. Cálculo do Valor Líquido

O valor líquido representa a base de cálculo para todos os encargos financeiros e é definido como:

```
VL = VP - VNC - VT - VCIP
```

Onde:
- **VL**: Valor Líquido
- **VP**: Valor Principal (valor original da fatura)
- **VNC**: Valor Não Cedido (parcelas excluídas da cessão)
- **VT**: Valor de Terceiros (valores devidos a terceiros)
- **VCIP**: Valor CIP (Contribuição para Iluminação Pública)

Esta formulação garante que apenas os valores efetivamente cedidos ao FIDC sejam considerados na base de cálculo dos encargos.

### 2. Cálculo do Aging (Tempo de Inadimplência)

O aging representa o tempo decorrido entre o vencimento original e a data base de cálculo:

```
DA = DB - DV
```

Onde:
- **DA**: Dias de Atraso
- **DB**: Data Base de Cálculo
- **DV**: Data de Vencimento Original

A classificação do aging segue faixas específicas do setor:

| Faixa | Classificação | Critério |
|-------|---------------|----------|
| DA ≤ 0 | A vencer | Ainda não vencido |
| 0 < DA ≤ 30 | Menor que 30 dias | Inadimplência recente |
| 30 < DA ≤ 59 | De 31 a 59 dias | Inadimplência inicial |
| 59 < DA ≤ 89 | De 60 a 89 dias | Inadimplência estabelecida |
| 89 < DA ≤ 119 | De 90 a 119 dias | Inadimplência consolidada |
| 119 < DA ≤ 359 | De 120 a 359 dias | Inadimplência prolongada |
| 359 < DA ≤ 719 | De 360 a 719 dias | Inadimplência de segundo ano |
| 719 < DA ≤ 1080 | De 720 a 1080 dias | Inadimplência de terceiro ano |
| DA > 1080 | Maior que 1080 dias | Inadimplência de longo prazo |

### 3. Cálculo da Multa Contratual

A multa contratual é aplicada sobre o valor líquido para débitos em atraso:

```
M = VL × TM × I(DA > 0)
```

Onde:
- **M**: Multa
- **TM**: Taxa de Multa (2% = 0,02)
- **I(DA > 0)**: Função indicadora (1 se DA > 0, 0 caso contrário)

A função indicadora garante que a multa seja aplicada apenas para valores efetivamente em atraso.

### 4. Cálculo dos Juros Moratórios

Os juros moratórios são calculados proporcionalmente ao tempo de atraso:

```
JM = VL × TJ × (DA / 30) × I(DA > 0)
```

Onde:
- **JM**: Juros Moratórios
- **TJ**: Taxa de Juros Mensal (1% = 0,01)
- **DA / 30**: Conversão de dias para meses (proporcional)

Esta formulação permite cálculo proporcional para períodos fracionários de meses.

### 5. Cálculo da Correção Monetária

A correção monetária utiliza índices oficiais para recompor o poder de compra:

```
CM = VL × (IDB / IDV - 1) × I(DA > 0)
```

Onde:
- **CM**: Correção Monetária
- **IDB**: Índice na Data Base
- **IDV**: Índice na Data de Vencimento

A seleção do índice segue a regra temporal:

```
Índice = {
    IGP-M,  se data ≤ 2021.05
    IPCA,   se data > 2021.05
}
```

### 6. Cálculo do Valor Corrigido Total

O valor corrigido total representa a soma de todos os componentes:

```
VC = VL + M + JM + CM
```

Onde:
- **VC**: Valor Corrigido Total

### 7. Cálculo do Valor Recuperável

O valor recuperável incorpora a probabilidade de efetiva recuperação baseada em dados históricos específicos do setor elétrico:

```
VR = VC × TR(E, T, A)
```

Onde:
- **VR**: Valor Recuperável
- **VC**: Valor Corrigido Total
- **TR(E, T, A)**: Taxa de Recuperação função da Empresa (E), Tipo de cliente (T) e Aging (A)

O mapeamento do aging detalhado para categorias de recuperação segue:

| Aging Detalhado | Categoria de Recuperação |
|-----------------|-------------------------|
| A vencer | A vencer |
| Menor que 30 dias até De 120 a 359 dias | Primeiro ano |
| De 360 a 719 dias | Segundo ano |
| De 720 a 1080 dias | Terceiro ano |
| Maior que 1080 dias | Demais anos |

As taxas de recuperação são específicas para cada combinação de empresa, tipo de cliente (Privado, Público, Hospital) e faixa de aging, refletindo padrões históricos de recuperação observados no setor elétrico brasileiro.

### 8. Cálculo do Valor Justo (Valor Presente)

O valor justo representa o valor presente do fluxo de caixa esperado, descontado pela taxa de desconto apropriada e pelo prazo esperado de recebimento:

```
VJ = VR ÷ (1 + TD)^(PR/365)
```

Onde:
- **VJ**: Valor Justo (Valor Presente)
- **VR**: Valor Recuperável
- **TD**: Taxa de Desconto (taxa de atratividade do investidor)
- **PR**: Prazo de Recebimento em dias (específico por empresa, tipo e aging)

Esta formulação considera:

**Prazo de Recebimento (PR):** Obtido da tabela de taxas de recuperação, representa o tempo médio esperado para efetiva recuperação do valor, baseado em dados históricos específicos para cada combinação de empresa, tipo de cliente e aging.

**Taxa de Desconto (TD):** Taxa de atratividade definida pelo investidor, que reflete o custo de oportunidade do capital e o risco específico da operação. Tipicamente varia entre 8% a 15% ao ano para operações de FIDC no setor elétrico.

**Conversão Temporal:** O prazo é convertido de dias para anos através da divisão por 365, permitindo aplicação correta da taxa de desconto anual.

### 9. Fórmula Consolidada do Sistema

A sequência completa de cálculos pode ser expressa através da fórmula consolidada:

```
VJ = [(VL + VL×0,02×I(DA>0) + VL×0,01×(DA/30)×I(DA>0) + VL×(IDB/IDV-1)×I(DA>0)) × TR(E,T,A)] ÷ (1+TD)^(PR/365)
```

Esta fórmula integra todos os componentes do sistema:
1. **Base de Cálculo**: Valor Líquido (VL)
2. **Encargos Financeiros**: Multa + Juros + Correção Monetária
3. **Probabilidade de Recuperação**: Taxa específica por perfil
4. **Valor Temporal**: Desconto pelo prazo de recebimento

O resultado final representa o valor justo da carteira de recebíveis, considerando todos os fatores relevantes para a tomada de decisão de investimento.

## Implementação Computacional

### Tratamento de Dados Ausentes

O sistema implementa estratégias robustas para tratamento de dados ausentes:

- **Valores numéricos ausentes**: Substituição por zero
- **Datas inválidas**: Utilização de data base padrão
- **Índices não encontrados**: Utilização de valores de fallback

### Validações de Integridade

- **Valores negativos**: Garantia de que VL ≥ 0
- **Datas futuras**: Validação de consistência temporal
- **Índices de correção**: Verificação de disponibilidade

### Otimizações de Performance

- **Cálculos vetorizados**: Utilização de operações pandas para processamento em lote
- **Cache de índices**: Armazenamento local de índices econômicos
- **Processamento incremental**: Cálculo apenas de registros modificados

## Verificação de Consistência

- **Soma de componentes**: VC = VL + M + JM + CM
- **Aplicação condicional**: Encargos apenas para DA > 0
- **Limites de sanidade**: Verificação de valores extremos


## Conclusões da Modelagem

A modelagem matemática implementada no Sistema FIDC Calculator representa uma abordagem robusta e auditável para o cálculo de valor justo de carteiras de recebíveis. A metodologia combina rigor técnico com praticidade operacional, permitindo processamento eficiente de grandes volumes de dados mantendo a precisão necessária para decisões de investimento.

A estrutura modular do sistema facilita futuras adaptações regulatórias e metodológicas, enquanto a documentação detalhada garante transparência e auditabilidade dos resultados. A integração de múltiplas fontes de dados e a aplicação de validações rigorosas conferem confiabilidade aos cálculos realizados.

A implementação de taxas de recuperação específicas por empresa, tipo de cliente e aging adiciona uma camada de sofisticação que aproxima os resultados da realidade operacional do setor elétrico brasileiro, contribuindo para uma avaliação mais precisa do valor justo das carteiras analisadas.

