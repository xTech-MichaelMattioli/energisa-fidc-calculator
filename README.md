# ENERGISA FIDC Calculator

Sistema de cálculo de valor corrigido para análise de carteiras FIDC das distribuidoras de energia elétrica Energisa.

## 🎯 Objetivo

Interface web moderna para processamento e análise das bases de dados ESS e Voltz, permitindo:
- Carregamento automatizado das bases de dados
- Mapeamento inteligente de campos
- Cálculo de aging por faixas de vencimento
- Correção monetária por diferentes índices
- Análise detalhada dos resultados
- Exportação dos dados processados

## 🏗️ Arquitetura

### Frontend (React + TypeScript)
- **Framework**: Vite + React 18
- **UI Components**: Shadcn/UI + Tailwind CSS
- **Roteamento**: React Router
- **Estado**: Context API + Hooks

### Backend (Python)
- **Script de processamento**: `scripts/processar_bases.py`
- **Bibliotecas**: pandas, numpy, openpyxl
- **Baseado no notebook**: `FIDC_Calculo_Valor_Corrigido_CORRIGIDO.ipynb`

## 📊 Módulos do Sistema

### 1. Módulo Carregamento
- Upload manual de arquivos CSV/Excel
- **Carregamento automático das bases Energisa**
- Validação de estrutura dos dados
- Preview dos dados carregados

### 2. Módulo Mapeamento
- Mapeamento automático de campos
- Configuração manual de correspondências
- Validação de campos obrigatórios

### 3. Módulo Aging
- Cálculo de dias em atraso
- Distribuição por faixas etárias
- Análise de inadimplência

### 4. Módulo Correção
- Correção monetária (IPCA, Selic, CDI, INPC)
- Cálculo de juros e multa
- Valor corrigido final

### 5. Módulo Análise
- Dashboards interativos
- Gráficos de distribuição
- Métricas consolidadas

### 6. Módulo Exportação
- Exportação para Excel
- Relatórios personalizados
- Histórico de processamentos

## 🗂️ Bases de Dados

### Base ESS (Energisa Sergipe)
- **Arquivo**: `BASE DADOS/1 - Distribuidoras/1. ESS_BRUTA_30.04.xlsx`
- **Registros**: ~45.320
- **Campos principais**: CD_CLIENTE, VL_FATURA_ORIGINAL, DT_VENCIMENTO

### Base Voltz
- **Arquivo**: `BASE DADOS/0- Voltz/Voltz_Base_FIDC_20022025.xlsx`
- **Registros**: ~38.745  
- **Campos principais**: CODIGO_CLIENTE, VALOR_DEBITO, DATA_VENCIMENTO

## 🚀 Como Executar

### Método 1: Script Automático
```bash
# Execute o arquivo start.bat
./start.bat
```

### Método 2: Manual
```bash
# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev
```

## 📈 Fluxo de Trabalho

1. **Carregar Bases** → Módulo 1 (Carregamento)
2. **Mapear Campos** → Módulo 2 (Mapeamento)  
3. **Calcular Aging** → Módulo 3 (Aging)
4. **Aplicar Correção** → Módulo 4 (Correção)
5. **Analisar Resultados** → Módulo 5 (Análise)
6. **Exportar Dados** → Módulo 6 (Exportação)

## 🔧 Tecnologias

- **React 18** + TypeScript
- **Vite** (build tool)
- **Tailwind CSS** (estilização)
- **Shadcn/UI** (componentes)
- **Lucide React** (ícones)
- **React Router** (navegação)
- **Python 3.x** (processamento)
- **Pandas** (manipulação de dados)

## 📝 Integração com Notebook

O sistema web implementa a mesma lógica do notebook `FIDC_Calculo_Valor_Corrigido_CORRIGIDO.ipynb` com dados reais das bases ESS e Voltz.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/8d2a900c-2737-4027-9da0-656c68928dd3) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)
