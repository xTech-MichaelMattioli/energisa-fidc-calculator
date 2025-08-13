# FIDC Calculator - Energisa 

⚡ Sistema de Cálculo de Valor Justo para Distribuidoras

## 🚀 Nova Estrutura Modular

### Como executar a nova versão:
```bash
streamlit run main.py
```

### Como executar a versão legada:
```bash
streamlit run app.py
```

## 📁 Estrutura do Projeto

```
energisa-data-refactor-wizard/
├── main.py                          # 🏠 Página principal (NOVA VERSÃO)
├── app.py                           # 📜 Aplicação legada (monolítica)
├── pages/                           # 📄 Páginas separadas
│   ├── 1_📋_Configurações.py       # Parâmetros e índices
│   ├── 2_📂_Carregamento.py        # Upload de arquivos Excel
│   ├── 3_🗺️_Mapeamento.py         # Mapeamento de campos
│   └── 4_💰_Correção.py            # Correção monetária e valor justo
├── utils/                           # 🛠️ Utilitários e classes
│   ├── parametros_correcao.py       # Parâmetros financeiros
│   ├── analisador_bases.py          # Análise de arquivos
│   ├── mapeador_campos.py           # Mapeamento automático
│   ├── calculador_aging.py          # Cálculo de aging
│   ├── calculador_correcao.py       # Correção monetária
│   └── exportador_resultados.py     # Exportação de dados
├── data/                            # 📊 Dados processados
├── BASE_DADOS/                      # 📂 Arquivos base
├── DOCS/                            # 📋 Documentação
└── requirements.txt                 # 📦 Dependências
```

## ✨ Benefícios da Nova Estrutura

### 🎯 Navegação Intuitiva
- **Páginas separadas** por funcionalidade
- **Fluxo linear** do processo
- **Status visual** do progresso
- **Navegação lateral** sempre visível

### 🔧 Arquitetura Modular
- **Código organizado** em páginas específicas
- **Reutilização** de componentes
- **Manutenção simplificada**
- **Facilidade de extensão**

### ⚡ Performance Melhorada
- **Carregamento otimizado** por página
- **Menos overhead** de interface
- **Cache inteligente** de dados
- **Responsividade aprimorada**

## 🧭 Fluxo do Processo

### 1. 📋 Configurações
- Definir parâmetros financeiros (multa, juros)
- Visualizar índices de correção (IGP-M, IPCA)
- Configurar data base padrão

### 2. 📂 Carregamento
- Upload de múltiplos arquivos Excel
- Detecção automática de estrutura
- Identificação de data base
- Validação de formato

### 3. 🗺️ Mapeamento
- Mapeamento automático de campos
- Ajuste manual quando necessário
- Validação de campos obrigatórios
- Preview dos dados padronizados

### 4. 💰 Correção
- **Upload obrigatório** da taxa de recuperação
- Cálculo automático de aging
- Correção monetária com IGP-M
- Aplicação de IPCA para valor justo
- Exportação automática dos resultados

## 📊 Funcionalidades Principais

### 🔍 Análise Automática
- **Detecção de estrutura** dos arquivos Excel
- **Identificação de campos** por correspondência semântica
- **Validação de tipos** de dados
- **Sugestões inteligentes** de mapeamento

### 💰 Cálculos Financeiros
- **Aging** baseado em data de vencimento
- **Correção monetária** com IGP-M
- **Juros moratórios** compostos
- **Multas** por inadimplência
- **Taxa de recuperação** por empresa/tipo/aging
- **Valor justo** com IPCA exponencial

### 📈 Relatórios e Visualizações
- **Agrupamentos** por empresa, tipo, aging
- **Totais consolidados** por categoria
- **Métricas em tempo real**
- **Gráficos interativos** de índices
- **Exportação automática** para CSV

## 🛠️ Instalação e Configuração

### Pré-requisitos
```bash
pip install -r requirements.txt
```

### Dependências principais:
- `streamlit >= 1.28.0`
- `pandas >= 1.5.0`
- `plotly >= 5.0.0`
- `requests >= 2.28.0`
- `sidrapy` (opcional, para IPCA)

### Executar aplicação:
```bash
# Nova versão (recomendada)
streamlit run main.py

# Versão legada
streamlit run app.py
```

## 📋 Arquivo de Taxa de Recuperação

### Estrutura obrigatória:
- **Aba:** "Input"
- **Formato:** Excel (.xlsx/.xls)
- **Marcação:** "x" para identificar empresas
- **Tipos:** Privado, Público, Hospital
- **Aging:** A vencer, Primeiro ano, Segundo ano, Terceiro ano, Demais anos

### Exemplo de estrutura:
```
| x | ESS | Privado |     | Público |     | Hospital |     |
|   |     | A vencer| 85% | A vencer| 80% | A vencer | 75% |
|   |     | 1º ano  | 70% | 1º ano  | 65% | 1º ano   | 60% |
```

## 🎯 Próximos Passos

### Migração Recomendada
1. ✅ **Teste a nova versão:** `streamlit run main.py`
2. ✅ **Valide os resultados** com dados conhecidos
3. ✅ **Migre seus processos** para a nova estrutura
4. ✅ **Archive a versão legada** quando confiante

### Melhorias Futuras
- 🔄 **API REST** para integração
- 📱 **Interface mobile-friendly**
- 🔐 **Autenticação** e controle de acesso
- 📊 **Dashboard executivo** com KPIs
- 🤖 **ML** para melhor mapeamento automático

## 📞 Suporte

Para dúvidas ou problemas:
1. 📋 Verifique a documentação em `/DOCS/`
2. 🔍 Analise os logs de erro
3. 🛠️ Use a versão legada como fallback
4. 📧 Entre em contato com a equipe técnica

---

**🏢 Business Integration Partners SPA**  
**⚡ Energisa - FIDC Calculator**  
**📅 Última atualização: Agosto 2025**
