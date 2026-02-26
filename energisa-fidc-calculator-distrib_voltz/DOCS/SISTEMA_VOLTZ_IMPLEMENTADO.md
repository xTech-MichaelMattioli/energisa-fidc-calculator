# Sistema de Cálculo Diferenciado para VOLTZ

## ⚡ Nova Funcionalidade Implementada

Foi criado um sistema de cálculo diferenciado que automaticamente detecta arquivos da **VOLTZ** e aplica regras específicas para esta fintech, mantendo os cálculos padrão para outras distribuidoras.

## 🔍 Como Funciona a Detecção

O sistema identifica arquivos da VOLTZ através do **nome do arquivo**:
- Arquivos contendo "voltz" ou "volt" no nome (case-insensitive)
- Exemplo: `VOLTZ_dados_2025.xlsx`, `voltz-contratos.xlsx`, `base_volt.xlsx`

## 📋 Regras Específicas da VOLTZ

### 🏢 Contexto
- **Subsidiária:** Fintech focada em redução de inadimplência
- **Tipo de Contratos:** CCBs (Cédulas de Crédito Bancário)
- **Objetivo:** Transferência de carteira entre FIDCs

### 💰 Cálculos Diferenciados

#### ✅ **ANTES DO VENCIMENTO** (Contratos não vencidos)
1. **Correção Monetária:** IGP-M sobre saldo devedor
2. **Juros Remuneratórios:** 4,65% a.m. até o vencimento

#### ✅ **APÓS O VENCIMENTO** (Contratos inadimplentes)
1. **Correção Monetária:** IGP-M sobre saldo devedor
2. **Juros Remuneratórios:** 4,65% a.m. (aplicados até o vencimento)
3. **Multa:** 2% sobre saldo devedor no vencimento (uma vez)
4. **Juros Moratórios:** 1,0% a.m. sobre valor no vencimento

### 🔑 Diferenças vs. Distribuidoras Padrão

| Aspecto | VOLTZ | Distribuidoras Padrão |
|---------|--------|----------------------|
| **Índice de Correção** | **Sempre IGP-M** | IPCA (conforme período) |
| **Juros Remuneratórios** | **4,65% a.m.** | Variável |
| **Multa** | **2% no vencimento** | Conforme contrato |
| **Juros Moratórios** | **1,0% a.m.** | Conforme contrato |
| **Base de Cálculo** | **Saldo devedor c/ juros** | Valor líquido |

## 🚀 Como Usar

### 1. **Upload do Arquivo**
- Faça upload de um arquivo Excel com nome contendo "voltz" ou "volt"
- O sistema detectará automaticamente

### 2. **Processamento Automático**
- Va para a página de **Mapeamento** e realize o mapeamento normalmente
- Va para a página de **Correção** e execute o cálculo
- O sistema mostrará: ⚡ **VOLTZ detectada!** Aplicando regras específicas

### 3. **Resultados Diferenciados**
- Resumo específico da VOLTZ com métricas detalhadas
- Cálculos seguindo as regras CCBs da fintech
- Comparação transparente com regras padrão

## 📊 Exemplo de Processamento

```
⚡ VOLTZ detectada! Aplicando regras específicas para Fintech/CCBs

🔄 Aplicando cálculos VOLTZ...
✅ Regras Aplicadas - VOLTZ (Fintech):
- ✅ Juros Remuneratórios: 4,65% a.m. até vencimento
- ✅ Correção Monetária: IGP-M (sempre, nunca IPCA)
- ✅ Multa: 2% sobre saldo devedor no vencimento (apenas vencidos)
- ✅ Juros Moratórios: 1,0% a.m. sobre valor no vencimento (apenas vencidos)
- ✅ Taxa de Recuperação: Específica para contratos CCBs
```

## 🔧 Arquivos Modificados/Criados

### Novos Arquivos
- `utils/calculador_voltz.py` - Calculador específico da VOLTZ

### Arquivos Modificados
- `utils/calculador_correcao.py` - Integração do sistema de detecção
- `pages/4_Correcao.py` - Uso do novo método integrado

## 💡 Benefícios

1. **Automático:** Detecção sem intervenção manual
2. **Transparente:** Clara identificação das regras aplicadas
3. **Flexível:** Mantém cálculos padrão para outras distribuidoras
4. **Preciso:** Regras específicas para contratos CCBs da VOLTZ
5. **Auditável:** Logs claros do tipo de cálculo aplicado

## 🧪 Teste Recomendado

1. Faça upload de um arquivo com nome contendo "voltz"
2. Complete o mapeamento normalmente
3. Execute o cálculo e verifique:
   - Mensagem de detecção da VOLTZ
   - Resumo específico com regras aplicadas
   - Valores calculados conforme as regras CCBs

---
*Sistema desenvolvido para atender às especificidades da VOLTZ como subsidiária fintech com contratos CCBs diferenciados.*
