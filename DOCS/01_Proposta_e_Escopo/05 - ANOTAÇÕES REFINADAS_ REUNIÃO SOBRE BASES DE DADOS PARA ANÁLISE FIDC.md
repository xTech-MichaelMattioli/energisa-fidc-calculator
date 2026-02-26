# ANOTAÇÕES REFINADAS: REUNIÃO SOBRE BASES DE DADOS PARA ANÁLISE FIDC

**Preparado por:** Manus AI  
**Data:** 25 de junho de 2025  
**Objetivo:** Refinamento das anotações da reunião sobre as bases ESS_BRUTA_30.04 e Voltz_Base_FIDC_20022025

---

## SUMÁRIO EXECUTIVO

Esta reunião abordou especificamente a estrutura e características das duas bases de dados fundamentais para o projeto de análise de carteiras FIDC da Energisa: a base ESS_BRUTA_30.04 (extraída do contas a receber) e a base Voltz_Base_FIDC_20022025. As discussões focaram nos critérios de seleção de clientes, tratamento de dados, deduções necessárias e metodologia para preparação das carteiras que serão submetidas à análise de recuperação via FIDC.

A estratégia central baseia-se na premissa de que a curva de recuperação de inadimplência apresenta efetividade máxima até 12 meses, justificando a contratação de especialistas como FIDCs (exemplo: Pascoalotto) para otimizar a recuperação de dívidas em carteiras com perfil específico de aging superior a 12 meses.

---

## 1. CONTEXTO ESTRATÉGICO E FUNDAMENTAÇÃO

### 1.1 Premissa de Recuperação Temporal

A base ESS_BRUTA_30.04 representa a extração consolidada do sistema de contas a receber da Energisa, especificamente das empresas da região Sul-Sudeste. O fundamento estratégico para utilização de FIDCs baseia-se na análise empírica de que a capacidade interna de recuperação de créditos inadimplentes mantém efetividade ótima durante os primeiros 12 meses após o vencimento. Transcorrido esse período, a curva de recuperação apresenta declínio significativo, justificando economicamente a transferência dessas carteiras para especialistas externos.

A estratégia de terceirização para FIDCs como a Pascoalotto fundamenta-se na expertise diferenciada que essas organizações possuem em recuperação de créditos. Por trabalharem com múltiplas empresas e diversos perfis de inadimplência, desenvolveram metodologias e estratégias otimizadas que superam significativamente a capacidade de recuperação interna da Energisa para carteiras com aging superior a 12 meses.

### 1.2 Critérios de Elegibilidade para FIDC

O critério fundamental estabelecido para inclusão de clientes na análise FIDC é a existência de pelo menos uma fatura com vencimento superior a 12 meses. Este parâmetro temporal não apenas alinha-se com a premissa de efetividade de recuperação interna, mas também assegura que apenas carteiras com perfil adequado para terceirização sejam consideradas na análise.

A base contempla clientes de todas as classes de consumo, incluindo residencial, comercial, industrial e rural. Entretanto, observa-se predominância de clientes em situação de desligamento, ou seja, unidades consumidoras que não estão sendo faturadas no período atual. Esta característica é relevante pois indica que a inadimplência resultou em interrupção do fornecimento, sinalizando maior complexidade para recuperação através de canais convencionais.

---

## 2. ESTRUTURA E CARACTERÍSTICAS DA BASE ESS_BRUTA_30.04

### 2.1 Identificação e Dados Cadastrais

A estrutura de identificação única de cada registro na base ESS_BRUTA_30.04 é composta pela combinação de três elementos fundamentais: UC (Unidade Consumidora), Nome do Cliente e Empresa. Esta tríade garante individualização precisa mesmo em casos de homonímia ou múltiplas unidades consumidoras associadas ao mesmo titular.

O campo "Empresa" identifica a distribuidora específica dentro do grupo Energisa, permitindo segregação e análise individualizada por empresa. O campo "UC Vinculado" representa o código único da unidade consumidora no sistema da concessionária, enquanto "Nome do Cliente" contém a denominação completa do titular da conta.

A documentação de identificação está consolidada no campo "CNPJ / CPF", sendo que registros com valores zerados devem ser obrigatoriamente excluídos da base de análise, pois impossibilitam identificação adequada para procedimentos de cobrança e recuperação.

### 2.2 Classificação Temporal e Status de Cobrança

O sistema de classificação temporal da inadimplência segue estrutura hierárquica baseada em três status principais. O "Status Pendente" abrange o período de 6 meses a 1 ano após o vencimento, representando a fase de cobrança ativa interna. Transcorrido este período, os registros migram para "Status Incobrável", que compreende o intervalo de 1 a 5 anos, período no qual a recuperação interna apresenta efetividade reduzida. Finalmente, após 5 anos, os registros assumem "Status Prescritas", quando legalmente não é mais possível realizar cobrança.

Os campos "Mês Ref" e "Ano Ref" identificam especificamente o período de competência da fatura, permitindo cálculos precisos de aging e classificação temporal. Esta informação é fundamental para aplicação correta das taxas de recuperação diferenciadas por período de inadimplência.

### 2.3 Análise de Comportamento e Exclusões

O campo "Número de religações" representa indicador crítico para qualidade da carteira. Registros com alto número de religações devem ser excluídos da base de análise, pois indicam padrão comportamental de inadimplência recorrente seguida de regularização, sugerindo capacidade de pagamento mas resistência ao cumprimento regular das obrigações. Este perfil apresenta complexidade adicional para recuperação via FIDC e pode distorcer as análises de viabilidade.

A classificação por "Classe" (residencial, industrial, comercial, rural, etc.) permite segmentação analítica fundamental, pois diferentes classes apresentam padrões distintos de recuperação. Particularmente relevante é a identificação de serviços essenciais, como hospitais e órgãos públicos, que possuem restrições legais para desligamento e, consequentemente, permanecem conectados por períodos significativamente superiores aos demais perfis.

---

## 3. ESTRUTURA FINANCEIRA E CÁLCULOS DE VALOR

### 3.1 Composição do Valor da Fatura

A estrutura financeira da base contempla múltiplas camadas de valor, iniciando pelo "Valor Líquido", que representa o valor da fatura deduzido de impostos e outros componentes não operacionais. Entretanto, para fins de análise FIDC, o campo prioritário é "Total Faturas", que consolida o valor integral apresentado ao cliente na data de vencimento.

O campo "Data Venc" estabelece a referência temporal para todos os cálculos de aging e atualização monetária. A partir desta data, calcula-se o "Dias de atraso" através da fórmula: Data Base (30.04) menos Data de Vencimento. Valores negativos neste campo indicam situações especiais onde clientes possuem acordos de parcelamento que resultam em vencimentos futuros, classificados como "a vencer" no campo "Período de atraso".

### 3.2 Deduções e Ajustes para Valor FIDC

A determinação do valor efetivo para análise FIDC requer aplicação de múltiplas deduções sobre o "Total Faturas". O "Valor não cedido" representa recursos destinados a ONGs e programas de assistência energética, onde terceiros assumem o pagamento da conta de energia como forma de apoio social. Estes valores não podem ser incluídos na base FIDC pois não representam crédito direto da Energisa contra o consumidor.

O "Valor Terceiro" contempla encargos setoriais e taxas de responsabilidade do sistema elétrico nacional, incluindo custos de termelétricas e outros componentes regulatórios que são repassados através da fatura mas pertencem ao Tesouro Nacional. Por não constituírem receita própria da Energisa, devem ser deduzidos do valor base para análise FIDC.

O "Valor CIP" (Contribuição para Iluminação Pública) representa taxa municipal recolhida através da fatura de energia elétrica. Como este valor pertence ao município e não à concessionária, deve ser obrigatoriamente deduzido para determinação do valor líquido de responsabilidade da Energisa.

### 3.3 Valor Líquido Final e Tratamento de Anomalias

O "Total Líquido" representa o valor final de responsabilidade da Energisa após todas as deduções mencionadas. Este campo pode apresentar valores negativos em situações onde créditos tributários ou ajustes regulatórios superam o valor da fatura base. Registros com "Total Líquido" negativo devem ser obrigatoriamente excluídos da análise FIDC, pois representam situações onde a Energisa possui obrigação financeira com o cliente, não o contrário.

A atualização monetária constitui processo fundamental para determinação do valor presente dos créditos. O sistema deve reproduzir os cálculos de atualização utilizando indicadores oficiais de inflação, observando que historicamente houve transição do GPM (Gerenciador de Preços Médios) para o IPCA (Índice de Preços ao Consumidor Amplo) como referência para correção monetária.

---

## 4. ESTRUTURA E CARACTERÍSTICAS DA BASE VOLTZ

### 4.1 Diferenciações Estruturais em Relação à Base ESS

A base Voltz_Base_FIDC_20022025 apresenta estrutura similar à ESS_BRUTA_30.04, mantendo os campos fundamentais de identificação e classificação, mas incorporando elementos específicos relacionados a contratos e parcelamentos. A principal diferenciação reside na necessidade de adicionar o "Número do Contrato" como elemento de individualização, conforme orientação específica registrada durante a reunião.

Leonardo destacou que existe minoria de casos onde um único cliente possui múltiplas faturas, situação que requer tratamento diferenciado para evitar duplicações ou inconsistências na análise. O "Número do Contrato" permite segregação adequada destes casos, assegurando que cada obrigação seja tratada individualmente no processo de análise FIDC.

### 4.2 Campos Específicos de Contratos e Parcelamentos

A base Voltz incorpora campos específicos para gestão de contratos parcelados: "VALOR_ORIGINAL_CONTRATO" e "VALOR_ATUALIZADO_CONTRATO" representam, respectivamente, o valor inicial acordado e o valor corrigido monetariamente na data base da análise. Estes campos são fundamentais para cálculos de recuperação em situações de parcelamento, onde o valor individual da parcela pode não refletir adequadamente o potencial de recuperação total.

Os campos "NUMERO_PARCELA" e "STATUS_PARCELA" permitem identificação precisa da situação de cada parcela dentro do contrato global. Esta granularidade é essencial para análises de recuperação, pois parcelas em diferentes estágios de inadimplência apresentam potenciais de recuperação distintos.

### 4.3 Integração e Consistência entre Bases

A manutenção de consistência entre as bases ESS e Voltz requer atenção especial aos campos comuns, assegurando que critérios de classificação, cálculos de aging e aplicação de deduções sigam metodologia idêntica. Particularmente importante é a uniformização dos campos "Empresa", "Status", "UC Vinculado", "CNPJ / CPF" e demais elementos de identificação.

A capacidade de filtração dinâmica mencionada na reunião é fundamental para tratamento de casos futuros. A implementação deve permitir exclusão seletiva de registros baseada em critérios como "UC Vinculado", possibilitando refinamento da base conforme necessidades específicas de cada análise ou cenário regulatório.

---

## 5. CRITÉRIOS DE TRATAMENTO E EXCLUSÕES

### 5.1 Filtros de Qualidade de Dados

A implementação de filtros de qualidade constitui etapa fundamental para assegurar confiabilidade da análise FIDC. O filtro primário baseia-se na classificação "Incobrável", que identifica registros com perfil adequado para terceirização. Este filtro deve ser aplicado em conjunto com o critério temporal de pelo menos uma fatura superior a 12 meses.

A exclusão de registros com "CNPJ / CPF" zerado é obrigatória, pois impossibilita identificação adequada para procedimentos de cobrança. Similarmente, registros com alto "Número de religações" devem ser excluídos por indicarem padrão comportamental inadequado para análise FIDC padrão.

### 5.2 Tratamento de Serviços Essenciais

Serviços essenciais, particularmente hospitais e órgãos públicos, requerem tratamento diferenciado devido às restrições legais para desligamento. Hospitais, embora classificados como "Comercial", devem ser identificados através de análise combinada da classificação e verificação de permanência de ligação por períodos superiores ao padrão.

A distinção entre serviços essenciais e demais consumidores comerciais requer utilização de duas variáveis: a "Classe" e a verificação do status de ligação por período estendido. Esta metodologia permite identificação precisa de unidades que permanecem conectadas por imposição legal, apresentando perfil de recuperação diferenciado.

### 5.3 Critérios de Inclusão Temporal

O critério fundamental para inclusão na análise FIDC é a existência de clientes com mais de 12 meses de inadimplência. Este parâmetro temporal alinha-se com a estratégia de transferência de carteiras após esgotamento da capacidade ótima de recuperação interna.

A aplicação deste critério deve considerar que clientes podem possuir múltiplas faturas em diferentes estágios de inadimplência. A regra estabelecida determina que a presença de pelo menos uma fatura superior a 12 meses qualifica o cliente para inclusão, independentemente da existência de faturas mais recentes.

---

## 6. METODOLOGIA DE ATUALIZAÇÃO MONETÁRIA

### 6.1 Evolução dos Índices de Correção

A atualização monetária dos valores constitui processo crítico para determinação do valor presente dos créditos inadimplentes. Historicamente, o sistema utilizava o GPM (Gerenciador de Preços Médios) como referência para correção monetária, posteriormente substituído pelo IPCA (Índice de Preços ao Consumidor Amplo), seguindo determinações regulatórias.

A transição entre índices requer atenção especial para assegurar continuidade metodológica e comparabilidade temporal dos resultados. O sistema deve reproduzir adequadamente os cálculos de atualização, aplicando o índice apropriado conforme o período de competência de cada fatura.

### 6.2 Implementação de Cálculos de Atualização

A implementação dos cálculos de atualização monetária deve considerar a data base de referência (30.04 para a base ESS) e aplicar os índices de correção apropriados para cada período. Esta metodologia assegura que todos os valores sejam expressos em moeda de poder aquisitivo equivalente, permitindo análises comparativas adequadas.

A reprodução destes cálculos em planilhas específicas permite validação e auditoria dos resultados, assegurando transparência metodológica e confiabilidade dos valores utilizados na análise FIDC. A manutenção de histórico de índices utilizados é fundamental para replicabilidade e auditoria posterior.

---

## 7. FLEXIBILIDADE E CAPACIDADE DE FILTRAÇÃO

### 7.1 Implementação de Filtros Dinâmicos

A capacidade de filtração dinâmica representa requisito fundamental para adaptabilidade do sistema a cenários futuros e necessidades específicas de análise. A implementação deve permitir aplicação de múltiplos critérios simultaneamente, incluindo "UC Vinculado", "Classe", "Tipo", "Status" e demais campos relevantes.

Esta flexibilidade é particularmente importante considerando que regulamentações setoriais e estratégias comerciais podem evoluir, requerendo ajustes nos critérios de seleção de carteiras para análise FIDC. A capacidade de reconfiguração sem alterações estruturais no sistema assegura sustentabilidade da solução.

### 7.2 Gestão de Casos Especiais

A gestão de casos especiais, como clientes com múltiplos contratos ou situações regulatórias específicas, requer flexibilidade adicional na aplicação de filtros. A possibilidade de exclusão seletiva baseada em listas de "UC Vinculado" ou outros critérios específicos permite tratamento adequado de situações excepcionais.

A documentação adequada dos critérios aplicados em cada análise é fundamental para auditoria e replicabilidade dos resultados. O sistema deve manter registro dos filtros utilizados, permitindo reconstrução exata das condições de cada análise realizada.

---

## CONCLUSÕES E RECOMENDAÇÕES

As bases ESS_BRUTA_30.04 e Voltz_Base_FIDC_20022025 constituem fundamento sólido para análise de viabilidade de carteiras FIDC da Energisa. A estrutura de dados apresenta granularidade adequada para aplicação de metodologias sofisticadas de análise de recuperação, permitindo segmentação por múltiplos critérios e aplicação de taxas diferenciadas conforme perfil de inadimplência.

A implementação bem-sucedida da análise FIDC requer atenção especial aos processos de limpeza de dados, aplicação de filtros de qualidade e cálculos de atualização monetária. A flexibilidade para tratamento de casos especiais e adaptação a cenários futuros constitui elemento fundamental para sustentabilidade da solução.

A metodologia de identificação única através da combinação UC + Nome + Empresa, associada aos critérios temporais estabelecidos, assegura precisão na seleção de carteiras adequadas para terceirização via FIDC. A estrutura de deduções implementada garante que apenas valores efetivamente de responsabilidade da Energisa sejam considerados na análise, assegurando precisão nos cálculos de viabilidade econômica.

---

*Este documento preserva integralmente todas as observações e nuances registradas durante a reunião, apresentando-as de forma estruturada e tecnicamente refinada para suporte às análises subsequentes do projeto FIDC.*

