# DOCUMENTAÇÃO OFICIAL: MECÂNICA DE CÁLCULOS FIDC ENERGISA

**Preparado para:** Energisa S.A.  
**Preparado por:** BIP Brasil
**Data:** 27 de junho de 2025  
**Versão:** 1.0  
**Classificação:** Documento Técnico Oficial  

---

## SUMÁRIO EXECUTIVO

Este documento constitui a documentação técnica oficial da mecânica de cálculos aplicada na avaliação de carteiras inadimplentes para estruturação de Fundos de Investimento em Direitos Creditórios (FIDC) da Energisa. A metodologia aqui descrita baseia-se na análise detalhada do arquivo Excel "Parte10.xlsx", que contém a base de cálculo de referência com 51 campos de dados e fórmulas específicas para determinação do valor justo de carteiras inadimplentes.

O modelo Excel analisado processa dados de 6 registros de exemplo da Energisa, demonstrando a aplicação prática da metodologia em contratos reais de distribuição de energia elétrica. Cada registro representa um contrato inadimplente com informações completas desde dados cadastrais até cálculos de valor presente líquido, permitindo a transformação de ativos de baixa liquidez em valores monetários precisos para negociação com FIDCs.

---

## 1. CONTEXTO E OBJETIVO

### 1.1 Contexto Estratégico da Energisa

A Energisa, como maior grupo privado do setor elétrico brasileiro, possui carteiras significativas de créditos inadimplentes distribuídas entre suas 9 distribuidoras. Estes ativos, embora representem direitos creditórios legítimos, apresentam baixa liquidez e custos elevados de recuperação através dos processos internos tradicionais.

A estruturação de operações FIDC permite à Energisa:
- **Liquidez Imediata**: Conversão de ativos ilíquidos em recursos financeiros disponíveis
- **Transferência de Risco**: Especialização da recuperação para gestores especializados
- **Otimização de Capital**: Liberação de recursos para investimentos em infraestrutura
- **Redução de Custos**: Eliminação de custos internos de cobrança e recuperação

### 1.2 Objetivo da Metodologia de Cálculo

A metodologia de cálculo desenvolvida tem como objetivo determinar o **valor justo** de carteiras inadimplentes, considerando:

1. **Probabilidade de Recuperação**: Baseada em dados históricos e benchmarks setoriais
2. **Prazo de Recebimento**: Tempo esperado para recuperação efetiva dos valores
3. **Valor Presente Líquido**: Desconto temporal considerando custo de oportunidade
4. **Correção Monetária**: Atualização dos valores conforme índices oficiais (IGPM/IPCA)
5. **Segmentação por Risco**: Diferentes tratamentos conforme perfil do devedor

### 1.3 Base Legal e Regulatória

A metodologia está fundamentada em:
- **Instrução CVM 356/2001**: Regulamentação de FIDCs
- **Resolução ANEEL 414/2010**: Condições gerais de fornecimento de energia
- **Lei 10.848/2004**: Marco regulatório do setor elétrico
- **Melhores Práticas de Mercado**: Benchmarks de recuperação de créditos inadimplentes

---

## 2. ESTRUTURA DO MODELO DE CÁLCULO

### 2.1 Arquitetura do Excel Parte10

O arquivo Excel "Parte10.xlsx" está estruturado em 4 abas principais, cada uma com função específica na metodologia:

#### **Aba "Parte 10" - Base de Dados e Cálculos**
- **Função**: Contém os dados individuais de cada contrato e todas as fórmulas de cálculo
- **Conteúdo**: Dados cadastrais, valores originais, correções, aging e valor justo final

#### **Aba "Indice" - Referências Macroeconômicas**
- **Função**: Tabela de índices IGPM e IPCA para correção monetária
- **Conteúdo**: Índices mensais para cálculo de correção monetária

#### **Aba "Pivot" - Consolidações e Agrupamentos**
- **Função**: Análises consolidadas por critérios específicos (aging, tipo de cliente, etc.)
- **Conteúdo**: Totalizações e percentuais por categoria

### 2.2 Fluxo de Processamento

O processamento segue sequência lógica determinística:

```
Dados Brutos → Classificação → Correção → Aging → Taxas → Valor Presente → Resultado Final
```

1. **Entrada de Dados**: Informações cadastrais e financeiras do contrato
2. **Classificação**: Determinação do tipo de cliente e situação contratual
3. **Correção Monetária**: Atualização do valor pela inflação acumulada
4. **Aging**: Classificação temporal da inadimplência
5. **Aplicação de Taxas**: Probabilidade de recuperação por categoria
6. **Valor Presente**: Desconto temporal do valor recuperável
7. **Resultado Final**: Valor justo para negociação FIDC

---

## 3. DICIONÁRIO DE DADOS

### 3.1 Campos de Identificação e Cadastro

| Campo | Descrição | Tipo | Exemplo Energisa |
|-------|-----------|------|------------------|
| **Id** | Identificador único do registro | Numérico | 9000000 |
| **Parceiro de Negócio** | Código SAP do cliente | Numérico | 33054356 |
| **Nome** | Razão social ou nome do cliente | Texto | "ENERGISA DISTRIBUIDORA DE ENERGIA S.A." |
| **Número CPF/CNPJ** | Documento de identificação | Numérico | 33.054.356/0001-00 |
| **Tipo de Identificação** | CPF ou CNPJ | Texto | "CNPJ" |
| **Conta Contrato** | Número da conta contratual | Numérico | 200000123456 |
| **Nº Contrato** | Número do contrato de fornecimento | Numérico | 123456789 |
| **Nº Instalação** | Código da unidade consumidora | Numérico | 987654321 |

### 3.2 Campos de Classificação Comercial

| Campo | Descrição | Tipo | Exemplo Energisa |
|-------|-----------|------|------------------|
| **Gestão Comercial** | Área responsável pela gestão | Texto | "DE" |
| **Procedimento Advertência** | Código do procedimento de cobrança | Texto | "UB" |
| **Nível de Tensão** | Classificação técnica da ligação | Numérico | 1 |
| **Classe** | Categoria tarifária do cliente | Numérico | 1001 |
| **Situação do Contrato** | Status atual do contrato | Texto | A (Ativo) |
| **Status da Instalação** | Situação física da ligação | Texto | D (Desligado/Ligado) |

### 3.3 Campos Financeiros Básicos

| Campo | Descrição | Tipo | Exemplo Energisa |
|-------|-----------|------|------------------|
| **Partida em Aberto (R$ Valor)** | Valor original da dívida | Monetário | R$ 1.234,56 |
| **COSIP** | Contribuição para Iluminação Pública | Monetário | R$ 12,34 |
| **Outros_Valores_Terceiros** | Encargos de terceiros | Monetário | R$ 56,78 |
| **Juros/Multa** | Encargos financeiros aplicados | Monetário | R$ 123,45 |
| **Data Vencimento Líquido** | Data original de vencimento | Data | 15/03/2022 |
| **Data Vecto Ajustado** | Data ajustada para cálculos | Data | 15/03/2022 |

### 3.4 Campos de Aging e Temporalidade

| Campo | Descrição | Tipo | Exemplo Energisa |
|-------|-----------|------|------------------|
| **Idade do Saldo** | Dias desde o vencimento original | Numérico | 456 |
| **Dias atraso** | Dias de inadimplência calculados | Numérico | 456 |
| **Aging** | Classificação temporal da dívida | Texto | "De 360 a 719 dias" |
| **Data base** | Data de referência para cálculos | Data | 31/01/2022 |

### 3.5 Campos de Correção Monetária

| Campo | Descrição | Tipo | Exemplo Energisa |
|-------|-----------|------|------------------|
| **Base calculo** | Valor base para correção (calculado) | Monetário | R$ 1.234,56 |
| **Multa** | Multa por inadimplência (2%) | Monetário | R$ 24,69 |
| **Corr Monet** | Correção monetária acumulada | Monetário | R$ 234,56 |
| **Juros Mor** | Juros moratórios (1% ao mês) | Monetário | R$ 56,78 |
| **Valor Corrig** | Valor total corrigido | Monetário | R$ 1.550,59 |

### 3.6 Campos de Indexação

| Campo | Descrição | Tipo | Exemplo Energisa |
|-------|-----------|------|------------------|
| **Ano Ant** | Ano de referência anterior | Numérico | 2021 |
| **Mes Ant** | Mês de referência anterior | Numérico | 12 |
| **Ref Ant** | Referência anterior (AAAAMM) | Numérico | 202112 |
| **Indice Ant** | Índice do período anterior | Numérico | 543,21 |
| **Ano Atu** | Ano atual de referência | Numérico | 2022 |
| **Mes Atu** | Mês atual de referência | Numérico | 1 |
| **Ref Atu** | Referência atual (AAAAMM) | Numérico | 202201 |
| **Indice Atu** | Índice do período atual | Numérico | 548,65 |
| **Indice VENC** | Índice na data de vencimento | Numérico | 520,45 |
| **Indice BASE** | Índice na data base | Numérico | 548,65 |

---

## 4. MECÂNICA DE CÁLCULOS DETALHADA

### 4.1 Cálculo de Aging (Classificação Temporal)

**Objetivo**: Classificar cada dívida conforme tempo de inadimplência para aplicação de taxas diferenciadas.

**Fórmula Excel**:
```excel
=SE([@[Dias atraso]]<=0;"A vencer";
  SE([@[Dias atraso]]<=30;"Menor que 30 dias";
    SE([@[Dias atraso]]<=60;"De 31 a 59 dias";
      SE([@[Dias atraso]]<=90;"De 60 a 89 dias";
        SE([@[Dias atraso]]<=120;"De 90 a 119 dias";
          SE([@[Dias atraso]]<=360;"De 120 a 359 dias";
            SE([@[Dias atraso]]<=720;"De 360 a 719 dias";
              SE([@[Dias atraso]]<=1080;"De 720 a 1080 dias";
                "Maior que 1080 dias"))))))))
```

**Exemplo Prático Energisa**:
- Contrato com vencimento em 15/03/2022
- Data base: 31/01/2023
- Dias de atraso: 322 dias
- **Resultado**: "De 120 a 359 dias"

**Justificativa**: Esta classificação permite aplicação de taxas de recuperação específicas, pois carteiras com diferentes tempos de inadimplência apresentam comportamentos distintos de pagamento.

### 4.2 Cálculo da Base de Cálculo

**Objetivo**: Determinar o valor líquido da dívida de energia elétrica, excluindo encargos de terceiros e taxas que não fazem parte do valor principal.

**Fórmula da Base calculo**:
```excel
=[@[Partida em Aberto (R$ Valor)]] - [@[COSIP]] - [@[Outros_Valores_Terceiros]]
```

**Exemplo Prático Energisa**:
```
Base calculo = R$ 1.500,00 - R$ 15,50 - R$ 249,94
Base calculo = R$ 1.234,56
```

**Justificativa**: A base de cálculo representa apenas o valor da dívida de energia elétrica propriamente dita, excluindo encargos de terceiros (como COSIP e outros valores) que possuem tratamento diferenciado na recuperação.

### 4.3 Cálculo de Correção Monetária

**Objetivo**: Atualizar o valor da dívida pela inflação acumulada desde o vencimento.

**Fórmula Excel**:
```excel
=[@[Base calculo]] * ([@[Indice BASE]] / [@[Indice VENC]])
```

**Componentes**:
- **Base calculo**: Valor original da dívida (R$ 1.234,56)
- **Indice VENC**: IGPM na data de vencimento (520,45)
- **Indice BASE**: IGPM na data base (548,65)

**Exemplo Prático Energisa**:
```
Correção = R$ 1.234,56 × (548,65 ÷ 520,45)
Correção = R$ 1.234,56 × 1,0542
Correção = R$ 1.301,45
```

**Justificativa**: A correção monetária preserva o poder de compra do crédito, sendo fundamental para determinar o valor real da dívida na data de análise.

### 4.4 Cálculo de Multa e Juros

**Objetivo**: Aplicar encargos contratuais e legais sobre a dívida inadimplente.

**Fórmula da Multa (2%)**:
```excel
=SE([@[Juros/Multa]]>0;0;[@[Base calculo]] * 0,02)
```

**Fórmula dos Juros Moratórios (1% ao mês)**:
```excel
=[@[Base calculo]] * 0,01 * ([@[Dias atraso]] / 30)
```

**Exemplo Prático Energisa**:
```
Multa = R$ 1.234,56 × 2% = R$ 24,69
Juros = R$ 1.234,56 × 1% × (322 ÷ 30) = R$ 132,51
```

**Justificativa**: Encargos previstos na regulamentação setorial e contratos de fornecimento, representando o custo financeiro da inadimplência.

### 4.5 Cálculo do Valor Corrigido Total

**Objetivo**: Consolidar todos os componentes da dívida atualizada.

**Fórmula Excel**:
```excel
=[@[Base calculo]] + [@[Multa]] + [@[Corr Monet]] + [@[Juros Mor]]
```

**Exemplo Prático Energisa**:
```
Valor Corrigido = R$ 1.234,56 + R$ 24,69 + R$ 66,89 + R$ 132,51
Valor Corrigido = R$ 1.458,65
```

**Justificativa**: Este é o valor total que o devedor deve à Energisa na data base, considerando todos os encargos e correções aplicáveis.

### 4.6 Aplicação de Taxa de Recuperação

**Objetivo**: Estimar o valor efetivamente recuperável baseado no aging da dívida.

**Tabela de Taxas por Aging**:
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

**Fórmula Excel**:
```excel
=PROCV([@Aging];TabelaTaxas;2;FALSO) * [@[Valor Corrig]]
```

**Exemplo Prático Energisa**:
```
Aging: "De 120 a 359 dias" → Taxa: 47%
Valor Recuperável = R$ 1.458,65 × 47% = R$ 685,57
```

**Justificativa**: Taxas baseadas em dados históricos de recuperação do setor elétrico e benchmarks de FIDCs similares.

### 4.7 Cálculo do Valor Presente (Valor Justo)

**Objetivo**: Determinar o valor presente líquido considerando prazo de recebimento e custo de capital.

**Parâmetros**:
- **Taxa de Desconto**: 12% ao ano (Selic + spread de risco)
- **Prazo de Recebimento**: Varia conforme aging (6 a 36 meses)

**Fórmula Excel**:
```excel
=[@[Valor Recuperável]] / (1 + 0,12) ^ ([@[Prazo Meses]] / 12)
```

**Tabela de Prazos por Aging**:
| Aging | Prazo (meses) |
|-------|---------------|
| A vencer | 6 |
| Menor que 30 dias | 6 |
| De 31 a 59 dias | 6 |
| De 60 a 89 dias | 6 |
| De 90 a 119 dias | 6 |
| De 120 a 359 dias | 6 |
| De 360 a 719 dias | 18 |
| De 720 a 1080 dias | 30 |
| Maior que 1080 dias | 36 |

**Exemplo Prático Energisa**:
```
Aging: "De 120 a 359 dias" → Prazo: 6 meses
Valor Justo = R$ 685,57 ÷ (1,12)^(6/12)
Valor Justo = R$ 685,57 ÷ 1,0583
Valor Justo = R$ 647,85
```

**Justificativa**: O desconto temporal reflete o custo de oportunidade do capital e o risco inerente à recuperação de créditos inadimplentes.

---

## 5. INTEGRAÇÃO COM ÍNDICES MACROECONÔMICOS

### 5.1 Aba "Indice" - Estrutura e Função

A aba "Indice" contém série histórica de 392 meses (1989-2025) dos índices IGPM e IPCA, fundamentais para correção monetária dos valores.

**Estrutura da Tabela**:
- **Coluna A**: Data no formato AAAA.MM (ex: 2022.01)
- **Coluna F**: Índice IGPM (base agosto/1994 = 100)
- **Colunas adicionais**: IPCA e outros índices de referência

**Exemplo de Dados**:
```
2021.12 → IGPM: 543,21
2022.01 → IGPM: 548,65
2022.02 → IGPM: 552,34
```

### 5.2 Fórmulas de Busca de Índices

**Busca do Índice na Data de Vencimento**:
```excel
=PROCV(ANO([@[Data Vecto Ajustado]])+MÊS([@[Data Vecto Ajustado]])/100;
       Indice!A:F;6;FALSO)
```

**Busca do Índice na Data Base**:
```excel
=PROCV([@[Ref Atu]]/100;Indice!A:F;6;FALSO)
```

**Justificativa**: A utilização de índices oficiais (IGPM/IPCA) garante transparência e aderência às práticas de mercado para correção monetária de créditos.

---

## 6. CONSOLIDAÇÕES E ANÁLISES (ABA PIVOT)

### 6.1 Agrupamentos por Aging

A aba Pivot consolida os resultados por categoria de aging, permitindo análise da distribuição de valor e risco da carteira.

**Métricas Consolidadas**:
- Quantidade de contratos por aging
- Valor corrigido total por categoria
- Valor justo total por categoria
- Percentual de recuperação médio
- Concentração de risco por faixa temporal

### 6.2 Análises por Tipo de Cliente

Segmentação adicional considerando:
- **Clientes Residenciais**: Maior volume, menor valor individual
- **Clientes Comerciais**: Volume médio, valor médio
- **Clientes Industriais**: Menor volume, maior valor individual
- **Poder Público**: Características específicas de recuperação

### 6.3 Indicadores de Performance

**Taxa de Recuperação Geral**:
```
Taxa Geral = Σ(Valor Justo) ÷ Σ(Valor Corrigido) × 100
```

**Concentração por Aging**:
```
Concentração = Valor Justo por Aging ÷ Valor Justo Total × 100
```

**Prazo Médio Ponderado**:
```
PMP = Σ(Valor Justo × Prazo) ÷ Σ(Valor Justo)
```

---

## 7. CONTROLES DE QUALIDADE E VALIDAÇÃO

### 7.1 Validações Automáticas

O modelo incorpora controles automáticos para garantir consistência:

**Validação de Datas**:
```excel
=SE([@[Data Vecto Ajustado]]>[@[Data base]];"ERRO: Data inconsistente";"OK")
```

**Validação de Índices**:
```excel
=SE(ÉERRO([@[Indice VENC]]);"ERRO: Índice não encontrado";"OK")
```

**Validação de Aging**:
```excel
=SE([@[Dias atraso]]<>[@[Data base]]-[@[Data Vecto Ajustado]];"ERRO: Aging inconsistente";"OK")
```

### 7.2 Testes de Sensibilidade

**Variação da Taxa de Desconto (±2%)**:
- Cenário Conservador: 14% ao ano
- Cenário Base: 12% ao ano
- Cenário Otimista: 10% ao ano

**Variação das Taxas de Recuperação (±20%)**:
- Cenário Pessimista: Taxas × 0,8
- Cenário Base: Taxas originais
- Cenário Otimista: Taxas × 1,2

### 7.3 Benchmarking com Mercado

Comparação dos resultados com:
- FIDCs similares do setor elétrico
- Carteiras de outros setores regulados
- Índices de recuperação publicados (SERASA, SPC)

---

## 8. RESULTADOS ESPERADOS E INTERPRETAÇÃO

### 8.1 Faixas de Valores Típicos

Com base na metodologia aplicada, os resultados esperados situam-se em:

**Por Aging**:
- Primeiro ano (até 359 dias): 25% a 50% de recuperação
- Segundo ano (360-719 dias): 1% a 3% de recuperação
- Terceiro ano (720-1080 dias): 0,5% a 1,5% de recuperação
- Acima de 3 anos: 0,3% a 0,8% de recuperação

**Consolidado Geral**:
- Carteiras balanceadas: 3% a 5% do valor corrigido
- Carteiras antigas: 1% a 2% do valor corrigido
- Carteiras recentes: 5% a 8% do valor corrigido

### 8.2 Fatores de Influência

**Composição da Carteira**:
- Concentração em aging de 120-359 dias maximiza valor
- Carteiras muito antigas reduzem significativamente o valor justo
- Mix equilibrado otimiza relação risco-retorno

**Condições Macroeconômicas**:
- Taxa Selic elevada reduz valor presente
- Inflação alta aumenta valor corrigido
- Estabilidade econômica melhora taxas de recuperação

**Características Setoriais**:
- Essencialidade do serviço favorece recuperação
- Regulamentação específica influencia prazos
- Sazonalidade de consumo afeta inadimplência

---

## 9. IMPLEMENTAÇÃO PRÁTICA

### 9.1 Preparação dos Dados

**Requisitos Mínimos**:
- Dados cadastrais completos dos devedores
- Histórico de vencimentos e pagamentos
- Classificação por tipo de cliente
- Situação atual dos contratos

**Qualidade dos Dados**:
- CPF/CNPJ válidos e atualizados
- Datas consistentes e verificadas
- Valores conferidos e validados
- Classificações padronizadas

### 9.2 Parametrização do Modelo

**Calibração de Taxas**:
- Análise histórica de recuperação da Energisa
- Benchmarking com mercado
- Ajustes por características regionais
- Validação por especialistas

**Definição de Prazos**:
- Experiência interna de cobrança
- Padrões regulatórios setoriais
- Práticas de mercado de FIDCs
- Capacidade operacional de gestores

---

## 10. CONSIDERAÇÕES FINAIS

### 10.1 Robustez da Metodologia

A metodologia apresentada baseia-se em:
- **Fundamentos Técnicos Sólidos**: Fórmulas matematicamente consistentes
- **Dados Históricos Confiáveis**: Benchmarks setoriais validados
- **Práticas de Mercado**: Alinhamento com padrões de FIDCs
- **Flexibilidade Paramétrica**: Adaptação a diferentes cenários

---

**DOCUMENTO CONFIDENCIAL - ENERGISA S.A.**  
*Este documento contém informações proprietárias e confidenciais. Sua reprodução ou distribuição sem autorização expressa é proibida.*

