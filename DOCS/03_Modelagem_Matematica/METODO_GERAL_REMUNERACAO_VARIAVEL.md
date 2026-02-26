# Método Geral de Remuneração Variável

## Visão Geral

O módulo `calculador_remuneracao_variavel.py` fornece um sistema genérico e flexível para cálculo de remuneração variável baseado em aging de valores. Este sistema foi desenvolvido para ser usado por qualquer distribuidora (Voltz, ETO, outras) no contexto do FIDC Energisa.

## Características Principais

### 🎯 **Flexibilidade**
- Configurações personalizáveis por distribuidora
- Faixas de aging e percentuais ajustáveis
- Suporte a diferentes modelos de negócio

### 🔧 **Facilidade de Uso**
- Funções de conveniência para casos comuns
- Validação automática de dados
- Logs detalhados para auditoria

### 📊 **Relatórios Integrados**
- Resumos estatísticos automáticos
- Integração com Streamlit
- Detalhamento por faixa de aging

## Configurações Pré-definidas

### Configuração Padrão FIDC
```python
FAIXAS_AGING_PADRAO = {
    'A vencer': 0.065,                    # 6,5%
    'Menor que 30 dias': 0.065,          # 6,5%
    'De 31 a 59 dias': 0.065,            # 6,5%
    'De 60 a 89 dias': 0.065,            # 6,5%
    'De 90 a 119 dias': 0.080,           # 8,0%
    'De 120 a 359 dias': 0.150,          # 15,0%
    'De 360 a 719 dias': 0.220,          # 22,0%
    'De 720 a 1080 dias': 0.360,         # 36,0%
    'Maior que 1080 dias': 0.500         # 50,0%
}
```

### Configuração Voltz (Mais Agressiva)
```python
FAIXAS_AGING_VOLTZ = {
    'A vencer': 0.050,                    # 5,0%
    'Menor que 30 dias': 0.050,          # 5,0%
    'De 31 a 59 dias': 0.070,            # 7,0%
    'De 60 a 89 dias': 0.090,            # 9,0%
    'De 90 a 119 dias': 0.120,           # 12,0%
    'De 120 a 359 dias': 0.180,          # 18,0%
    'De 360 a 719 dias': 0.280,          # 28,0%
    'De 720 a 1080 dias': 0.420,         # 42,0%
    'Maior que 1080 dias': 0.600         # 60,0%
}
```

## Exemplos de Uso

### 1. Uso Básico - Configuração Padrão
```python
from utils.calculador_remuneracao_variavel import CalculadorRemuneracaoVariavel

# Inicializar calculador padrão
calculador = CalculadorRemuneracaoVariavel()

# Calcular remuneração variável
df_resultado = calculador.calcular_remuneracao_variavel(df)

# Gerar resumo
resumo = calculador.gerar_resumo_remuneracao(df_resultado)
```

### 2. Uso com Configuração Voltz
```python
# Inicializar calculador para Voltz
calculador_voltz = CalculadorRemuneracaoVariavel(distribuidora="VOLTZ")

# Calcular com configuração Voltz
df_resultado = calculador_voltz.calcular_remuneracao_variavel(df)
```

### 3. Configuração Personalizada
```python
# Definir faixas personalizadas
faixas_personalizadas = {
    'A vencer': 0.040,                    # 4,0%
    'Menor que 30 dias': 0.040,          # 4,0%
    'De 31 a 59 dias': 0.060,            # 6,0%
    'De 60 a 89 dias': 0.080,            # 8,0%
    'De 90 a 119 dias': 0.100,           # 10,0%
    'De 120 a 359 dias': 0.200,          # 20,0%
    'De 360 a 719 dias': 0.300,          # 30,0%
    'De 720 a 1080 dias': 0.450,         # 45,0%
    'Maior que 1080 dias': 0.700         # 70,0%
}

# Criar calculador personalizado
calculador_custom = CalculadorRemuneracaoVariavel(
    faixas_aging=faixas_personalizadas,
    distribuidora="DISTRIBUIDORA_CUSTOM"
)
```

### 4. Funções de Conveniência
```python
from utils.calculador_remuneracao_variavel import (
    calcular_remuneracao_variavel_padrao,
    calcular_remuneracao_variavel_voltz
)

# Uso rápido - configuração padrão
df_resultado = calcular_remuneracao_variavel_padrao(df)

# Uso rápido - configuração Voltz
df_resultado_voltz = calcular_remuneracao_variavel_voltz(df)
```

## Colunas Geradas

O sistema adiciona as seguintes colunas ao DataFrame:

- **`remuneracao_variavel_perc`**: Percentual de desconto aplicado
- **`remuneracao_variavel_valor`**: Valor absoluto do desconto
- **`remuneracao_variavel_valor_final`**: Valor final após desconto

## Validações Implementadas

### ✅ **Validação de Dados**
- Verificação de DataFrame vazio
- Validação de colunas obrigatórias
- Verificação de valores nulos

### ✅ **Proteções**
- Valores finais não podem ser negativos
- Tratamento de faixas de aging não mapeadas
- Logs de erro e warnings detalhados

## Integração com Sistema Atual

### Substituição no `calculador_correcao.py`

Para integrar o novo sistema, substitua o método `calcular_valor_justo_reajustado` por:

```python
from .calculador_remuneracao_variavel import CalculadorRemuneracaoVariavel

def calcular_valor_justo_reajustado(self, df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula valor justo reajustado usando o novo sistema de remuneração variável.
    """
    if df.empty:
        return df
    
    # Verificar se temos valor_justo
    if 'valor_justo_ate_recebimento' not in df.columns:
        st.warning("⚠️ Coluna 'valor_justo_ate_recebimento' não encontrada.")
        df['valor_justo_ate_recebimento'] = df.get('valor_corrigido', 0)
    
    # Usar calculador de remuneração variável
    calculador_rv = CalculadorRemuneracaoVariavel(distribuidora="PADRAO")
    df_resultado = calculador_rv.calcular_remuneracao_variavel(df)
    
    # Compatibilidade com código existente
    df_resultado['valor_justo_pos_rv'] = df_resultado['remuneracao_variavel_valor_final']
    
    # Gerar resumo
    calculador_rv.gerar_resumo_remuneracao(df_resultado)
    
    return df_resultado
```

## Benefícios do Novo Sistema

### 🚀 **Escalabilidade**
- Fácil adição de novas distribuidoras
- Configurações independentes por empresa
- Manutenção centralizada

### 🔍 **Transparência**
- Logs detalhados para auditoria
- Relatórios automáticos
- Rastreabilidade completa

### 🛠️ **Manutenibilidade**
- Código limpo e documentado
- Testes unitários incluídos
- Separação de responsabilidades

### 🎯 **Flexibilidade**
- Configurações dinâmicas
- Suporte a regras específicas
- Fácil personalização

## Roadmap Futuro

- [ ] Interface web para configuração de faixas
- [ ] Importação/exportação de configurações
- [ ] Histórico de mudanças nas configurações
- [ ] Análise comparativa entre configurações
- [ ] Simulação de cenários

## Considerações Técnicas

### Performance
- Operações vetorizadas com Pandas
- Processamento eficiente de grandes volumes
- Uso mínimo de memória

### Segurança
- Validação rigorosa de entrada
- Proteção contra overflow
- Logs de auditoria

### Compatibilidade
- Mantém compatibilidade com código existente
- Migração gradual possível
- Interfaces estáveis