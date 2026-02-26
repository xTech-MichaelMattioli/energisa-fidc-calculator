# 📚 DOCUMENTAÇÃO OFICIAL - ÍNDICE E GUIA DE NAVEGAÇÃO

> **Data de Organização:** 26/02/2026  
> **Versão:** 1.0 - Estrutura Consolidada

---

## 📋 VISÃO GERAL DA DOCUMENTAÇÃO

Esta pasta contém toda a **documentação técnica oficial** do Projeto FIDC Energisa. Os documentos estão organizados em **5 categorias principais** para facilitar navegação e referência cruzada.

### 📊 Estatísticas Gerais

- **Total de Documentos:** 22+ arquivos
- **Formatos:** Markdown (.md), Jupyter Notebooks (.ipynb), Excel (.xlsx), PDF
- **Escopo:** Desde proposta até implementação técnica completa
- **Públicos:** Executivos, Analistas de Dados, Desenvolvedores, Auditores

---

## 🗂️ ESTRUTURA DE PASTAS

```
DOCS/
├── 01_Proposta_e_Escopo/          ← Entendimento estratégico
├── 02_Documentacao_Oficial/        ← Especificações técnicas oficiais
├── 03_Modelagem_Matematica/        ← Fórmulas e metodologia matemática
├── 04_Dicionarios_e_Referencia/    ← Dados, schemas, dicionários
├── 05_Notebooks_e_Desenvolvimento/ ← Exemplos práticos e simulações
└── INDEX.md                         ← Este arquivo
```

---

## 📚 DESCRIÇÃO DETALHADA DE CADA CATEGORIA

### 1️⃣ **01_Proposta_e_Escopo/** 
**Entendimento Estratégico e Contexto do Projeto**

Estes documentos estabelecem o **contexto estratégico** do projeto FIDC Energisa:

| Documento | Descrição | Público |
|-----------|-----------|---------|
| **01 - RESUMO EXECUTIVO...** | Visão geral da proposta, objetivo do FIDC, escopo de 9 distribuidoras, duração de 8 semanas em 3 ondas. Apresenta contexto da Energisa (120 anos, maior grupo privado, 9 distribuidoras) e metodologia BIP em 4 etapas | Executivos, Gestores |
| **02 - ANÁLISE ESPECIALIZADA...** | Análise profunda das carteiras FIDC, características de inadimplência, segmentação por tipo de cliente (Privado, Público, Hospital) e perfis de risco | Analistas Senior |
| **04 - SUMÁRIO EXECUTIVO...** | Consolidação do entendimento completo dos cálculos FIDC no contexto Energisa, síntese das metodologias aplicadas | Coordenadores, Gestores |
| **05 - ANOTAÇÕES REFINADAS...** | Anotações técnicas de reuniões, insights sobre base de dados, decisões documentadas sobre structure FIDC | Analistas Técnicos |

📌 **Use esta pasta quando:** Precisa entender o PORQUÊ do projeto, escopo, contexto estratégico, ou apresentar para stakeholders.

---

### 2️⃣ **02_Documentacao_Oficial/**
**Especificação Técnica Oficial das Mecânicas de Cálculo**

Contém a **especificação técnica oficial** que governa todos os cálculos do sistema:

| Documento | Descrição | Escopo |
|-----------|-----------|--------|
| **03 - DOCUMENTAÇÃO OFICIAL...** | Documento técnico oficial COMPLETO. Define valor justo, probabilidade recuperação, prazo recebimento, VPL, correção monetária, segmentação risco. Base legal e regulatória. **REFERÊNCIA PRINCIPAL PARA DESENVOLVIMENTO** | Todos os cálculos |
| **documentação mecanica de calculos.md** | Detalhe prático da mecânica de cálculos, formatação dos dados, sequência de processamento | Implementadores |
| **SISTEMA_VOLTZ_IMPLEMENTADO.md** | Especificação do sistema diferenciado para Voltz, detecção automática, regras específicas (IGP-M, 4.65% juros, 2% multa, 1% mora), diferenças vs padrão | Voltz |
| **DOCUMENTAÇÃO OFICIAL_ MECÂNICA...** | Versão alternativa/complementar da especificação oficial | Referência cruzada |

📌 **Use esta pasta quando:** Implementa um cálculo novo, valida lógica de negócio, ou precisa da especificação oficial.

---

### 3️⃣ **03_Modelagem_Matematica/**
**Fórmulas, Metodologia Matemática e Equações**

Contém a **modelagem matemática rigorosa** do sistema:

| Documento | Descrição | Conteúdo |
|-----------|-----------|---------|
| **Modelagem Matemática.md** | Fundamentos teóricos completos. Conceito de valor justo, metodologia correção monetária (IGP-M até mai/2021, IPCA após), fórmula VL = VP - VNC - VT - VCIP, cálculo de encargos, VPL, taxa desconto | Equações principais |
| **Regras_Calculo_Correcao_Melhorado.md** | Regras refinadas especificamente para cálculo de correção monetária, periodicidades, tratamento de períodos incompletos | Correção monetária |
| **METODO_GERAL_REMUNERACAO_VARIAVEL.md** | Método genérico de remuneração variável por aging, faixas padrão FIDC (6.5%, 8%, 15%, 22%, 36%, 50%), suporte multi-distribuidora, validações, logs | Remuneração variável |

💡 **Principais Conceitos:**
- **Valor Líquido:** VL = VP - VNC - VT - VCIP
- **Correção Monetária:** IGP-M (até mai/2021) → IPCA (após)
- **Taxa de Desconto:** Baseada em DI-PRE + spread risco
- **Faixas de Aging:** 9 categorias com remuneração progressiva

📌 **Use esta pasta quando:** Precisa derivar nova fórmula, validar cálculo manual, ou entender equações subjacentes.

---

### 4️⃣ **04_Dicionarios_e_Referencia/**
**Schema de Dados, Dicionários e Estrutura**

Contém **definições de estrutura de dados** e referências:

| Documento | Descrição | Detalhes |
|-----------|-----------|---------|
| **DICIONARIO_DADOS_DF_FINAL.md** | Dicionário COMPLETO de 42 colunas do DataFrame final. 6 grupos funcionais: (1) Dados básicos cliente, (2) Metadados, (3) Aging, (4) Valores limpos/líquidos, (5) Correção monetária, (6) Taxa recuperação & Valor justo. Tipos, formatos, exemplos para cada coluna. | 42 colunas |
| **CONEXÃO ENTRE BASES...** | Documentação de integração entre bases de dados Energisa e FIDC Calculator, mapeamento de campos, transformações necessárias | Integração |
| **DICIONARIO DE DADOS/** | Subpasta com dicionários adicionais, estruturas detalhadas, schemas alternativos | Referência |
| **Arquivos Excel (.xlsx)** | Dicionários técnicos em formato Excel, estruturas de dados, templates | Desenvolvimento |

📊 **Exemplo de Coluna (DICIONARIO_DADOS_DF_FINAL.md):**
```
| # | Campo | Tipo | Descrição | Exemplo | Obs |
|----|-------|------|-----------|---------|-----|
| 1 | nome_cliente | str | Nome do cliente | "Cliente ABC" | PK |
```

📌 **Use esta pasta quando:** Desenvolve código Python/SQL, integra nova base de dados, ou precisa mapear campos.

---

### 5️⃣ **05_Notebooks_e_Desenvolvimento/**
**Exemplos Práticos, Simulações e Protótipos**

Contém **exemplos executáveis** e ferramentas de desenvolvimento:

| Arquivo | Tipo | Descrição | Uso |
|---------|------|-----------|-----|
| **FIDC_Calculo_Valor_Corrigido_CORRIGIDO.ipynb** | Jupyter | Notebook com exemplo completo de cálculo, simulações com dados reais Energisa (6 registros), demonstra aplicação prática das fórmulas | Validação, aprendizado |
| **PDFs Técnicos** | PDF | Documentos suplementares em PDF (entendimento base cálculo, mecânica modelos FIDC) | Complementar |
| **Arquivos Suporte** | Diversos | Arquivos de suporte e referência para desenvolvimento | Debug, teste |

💻 **Como usar os notebooks:**
1. Abra o Jupyter Notebook
2. Execute célula por célula para acompanhar o fluxo
3. Modifique dados de entrada para simular cenários
4. Valide resultados contra especificação técnica

📌 **Use esta pasta quando:** Quer aprender na prática, fazer prototipagem, ou validar implementação.

---

## 🔍 GUIA DE NAVEGAÇÃO POR CENÁRIO

### 🎯 Cenário 1: "Sou novo no projeto, quero entender tudo"
1. Comece em **01_Proposta_e_Escopo/** → Para entender contexto
2. Vá para **02_Documentacao_Oficial/03** → Para especificação
3. Explore **05_Notebooks_e_Desenvolvimento/FIDC_Calculo...** → Para exemplo prático
4. Consulte **04_Dicionarios_e_Referencia/DICIONARIO_DADOS_DF_FINAL.md** → Para detalhes de dados

### 💻 Cenário 2: "Vou implementar um novo cálculo"
1. Leia **02_Documentacao_Oficial/** → Especificação
2. Consulte **03_Modelagem_Matematica/** → Fórmulas exatas
3. Valide contra **04_Dicionarios_e_Referencia/DICIONARIO_DADOS_DF_FINAL.md** → Tipos dados
4. Teste com **05_Notebooks_e_Desenvolvimento/FIDC_Calculo...** → Validação

### 📊 Cenário 3: "Estou debugando um cálculo"
1. Verifique **02_Documentacao_Oficial/03** → O que DEVE acontecer
2. Consulte **03_Modelagem_Matematica/Modelagem...** → Fórmula exata
3. Valide dados contra **04_Dicionarios_e_Referencia/** → Tipos, formatos, ranges
4. Simule em **05_Notebooks_e_Desenvolvimento/** → Teste isolado

### 🔧 Cenário 4: "Preciso ajustar para Voltz"
1. Leia **02_Documentacao_Oficial/SISTEMA_VOLTZ_IMPLEMENTADO.md** → O sistema Voltz
2. Consulte **03_Modelagem_Matematica/METODO_GERAL_REMUNERACAO_VARIAVEL.md** → Remuneração
3. Verifique diferenças em **02_Documentacao_Oficial/SISTEMA_VOLTZ...** → Regras específicas
4. Valide em **05_Notebooks_e_Desenvolvimento/** → Com dados Voltz

---

## 📖 DOCUMENTOS RELACIONADOS

**Veja também:**
- [`docs_implementacao/`](../docs_implementacao/INDEX.md) - Implementação técnica e detalhes de código
- [`requirements.txt`](../../requirements.txt) - Dependências Python
- [`README.md`](../../README.md) - Overview geral do projeto

---

## ❓ FAQ - Perguntas Frequentes

**P: Qual é o documento "oficial"?**  
R: [`02_Documentacao_Oficial/03 - DOCUMENTAÇÃO OFICIAL_ MECÂNICA DE CÁLCULOS FIDC ENERGISA.md`](02_Documentacao_Oficial/03%20-%20DOCUMENTAÇÃO%20OFICIAL_%20MECÂNICA%20DE%20CÁLCULOS%20FIDC%20ENERGISA.md) é a fonte de verdade técnica.

**P: Aonde vejo um exemplo prático?**  
R: Em [`05_Notebooks_e_Desenvolvimento/FIDC_Calculo_Valor_Corrigido_CORRIGIDO.ipynb`](05_Notebooks_e_Desenvolvimento/FIDC_Calculo_Valor_Corrigido_CORRIGIDO.ipynb)

**P: Como funciona para Voltz especificamente?**  
R: Leia [`02_Documentacao_Oficial/SISTEMA_VOLTZ_IMPLEMENTADO.md`](02_Documentacao_Oficial/SISTEMA_VOLTZ_IMPLEMENTADO.md) para as regras únicas da Voltz.

**P: Lista completa de campos na saída?**  
R: Veja [`04_Dicionarios_e_Referencia/DICIONARIO_DADOS_DF_FINAL.md`](04_Dicionarios_e_Referencia/DICIONARIO_DADOS_DF_FINAL.md) - descreve 42 colunas em detalhes.

---

## 🔄 HISTÓRICO DE VERSÕES

| Versão | Data | Mudanças |
|--------|------|----------|
| 1.0 | 26/02/2026 | Reorganização completa em 5 categorias, criação de INDEX.md |

---

## 📞 SUPORTE E DÚVIDAS

Para dúvidas sobre conteúdo:
1. Consulte o INDEX desta pasta (este arquivo)
2. Procure no documento específico mencionado
3. Valide em `05_Notebooks_e_Desenvolvimento/` com exemplo
4. Contacte a equipe de projeto

---

**Last Updated:** 26/02/2026  
**Maintainer:** BIP Brasil | Project FIDC Energisa  
**Status:** ✅ Documentação Completa e Organizada
