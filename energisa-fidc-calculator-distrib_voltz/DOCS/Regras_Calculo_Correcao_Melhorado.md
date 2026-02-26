# REGRAS PARA CÁLCULO DE CORREÇÃO

Nas projeções financeiras fornecidas, o período de projeção adotado varia conforme as classes de crédito. Principais premissas:

- **Créditos comerciais**: Para a distribuidora, adotou-se a taxa de recuperação fornecida pela Energisa, no que diz respeito a aging, setor de atuação, localização, entre outros. Para a curva de recuperação, o prazo de recebimento varia conforme o aging específico de cada registro, sendo obtido da tabela de taxas de recuperação que contém prazos individualizados por empresa, tipo e aging. Para a faixa de aging a vencer, foi considerado uma estimativa de taxa de recuperação de 0,89% com base no risco de crédito apurado nos clientes que contém esses créditos (SINED).

Para a projeção até o recebimento, foi utilizada uma metodologia de desconto a valor presente utilizando taxa DI-PRE com capitalização exponencial, onde para cada registro busca-se no arquivo DI-PRE a taxa de desconto correspondente ao prazo esperado de recebimento específico. A correção monetária utiliza índices oficiais IPCA a partir de junho/2021 e IGP-M até maio/2021, com encargos moratórios de 1% a.m. sobre o principal em atraso. O valor presente líquido é determinado aplicando a probabilidade de recuperação sobre o valor atualizado monetariamente, descontado pela taxa DI-PRE capitalizada exponencialmente e ajustado por penalidades de atraso no recebimento.

- **Ajuste de Remuneração Variável (Haircut Pós-Valuation)**: Após a determinação do valor presente líquido, foi implementada uma estrutura de deságios escalonados denominada "remuneração variável", que representa um haircut aplicado sobre o valor justo previamente calculado. Esta estrutura de deságios varia conforme a maturidade do aging: 6,5% para créditos performados e inadimplência inicial até 90 dias, 8,0% para inadimplência de 90-119 dias, 15,0% para inadimplência intermediária de 120-359 dias, 22,0% para inadimplência avançada de 360-719 dias, 36,0% para inadimplência crítica de 720-1080 dias, e 50,0% para créditos em situação de perda (>1080 dias). O valor justo final ajustado reflete a subtração deste haircut sobre o valor presente inicialmente apurado.

## DETALHAMENTO TÉCNICO

### Taxas de Recuperação por Aging
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

### Estrutura de Remuneração Variável (Desconto Pós-Valor Justo)
| Aging | Percentual de Desconto |
|-------|----------------------|
| A vencer | 6,5% |
| Menor que 30 dias | 6,5% |
| De 31 a 59 dias | 6,5% |
| De 60 a 89 dias | 6,5% |
| De 90 a 119 dias | 8,0% |
| De 120 a 359 dias | 15,0% |
| De 360 a 719 dias | 22,0% |
| De 720 a 1080 dias | 36,0% |
| Maior que 1080 dias | 50,0% |

### Metodologias Aplicadas

**Correção Monetária:**
Aplicação de índices econômicos (IPCA/IGP-M) para atualização do valor líquido pela relação entre o índice da data base e o índice da data de vencimento.

**Fator Exponencial DI-PRE:**
Utilização de progressão exponencial baseada na taxa DI-PRE específica para o prazo de recebimento de cada registro, aplicando capitalização composta.

**Valor Justo:**
Cálculo resultante da aplicação da taxa de recuperação sobre o valor corrigido, multiplicado pelo fator exponencial DI-PRE acrescido da multa por atraso no recebimento.

**Remuneração Variável:**
Desconto aplicado sobre o valor justo já calculado, com percentuais específicos por faixa de aging, representando custos operacionais de recuperação.

### Observações
- **Metodologia DI-PRE**: Busca taxa específica para cada prazo de recebimento no arquivo DI-PRE
- **Taxa padrão**: 0,5% ao mês quando não há correspondência no DI-PRE
- **Prazo individualizado**: Cada registro possui prazo específico da tabela de taxas de recuperação
- **Concentração de valor**: ≈60% na faixa de 120-359 dias
- **Variação entre distribuidoras**: 2,00% a 6,48% de performance
