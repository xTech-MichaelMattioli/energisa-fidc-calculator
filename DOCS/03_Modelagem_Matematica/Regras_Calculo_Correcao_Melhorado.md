# Regras de Calculo de Correcao (Implementacao Atual)

## Escopo

Este documento descreve o fluxo implementado na pasta `energisa-fidc-calculator-distrib` para distribuidoras padrao.

Nao cobre a pasta `energisa-fidc-calculator-distrib_voltz`.

## Objetivo

Documentar, em nivel tecnico e matematico:

1. Encadeamento e sequencia dos calculos.
2. Informacoes minimas necessarias para executar o pipeline.
3. Arquivos obrigatorios de entrada e formato esperado.
4. Formulas usadas em cada etapa do processamento.

## Arquivos De Entrada Obrigatorios

### 1. Base(s) da distribuidora

- Formato: `.xlsx` ou `.xls`.
- Conteudo: carteira com cliente, contrato, valores e vencimento.
- Origem no fluxo: pagina `2_Carregamento.py`.

### 2. Arquivo de indices economicos

- Formato: `.xlsx` ou `.xls`.
- Leitura no fluxo:
	- Aba `IGPM` (suporte a estrutura A/B).
	- Primeira aba (estrutura C/D/F, chamada no texto de `IGPM_IPCA`).
- Uso principal na rota padrao: base de indices economicos para correcao monetaria e IPCA mensal.
- Origem no fluxo: pagina `4_Correcao.py`.

### 3. Arquivo de taxa de recuperacao

- Formato: `.xlsx` ou `.xls`.
- Aba obrigatoria: `Input`.
- Estrutura esperada no parser:
	- Empresa marcada por `x`.
	- Blocos por tipo: `Privado`, `Publico`, `Hospital`.
	- Aging: `A vencer`, `Primeiro ano`, `Segundo ano`, `Terceiro ano`, `Quarto ano`, `Quinto ano`, `Demais anos`.
	- Campos extraidos: `Taxa de recuperacao` e `Prazo de recebimento`.

### 4. Arquivo CDI/DI-PRE (BMF)

- Formato aceito no parser atual: conteudo HTML em arquivo `.xls`/`.xlsx` exportado da BMF.
- Estrutura usada:
	- Coluna 1: dias corridos.
	- Coluna 2: taxa base `252`.
	- Coluna 3: taxa base `360`.
- Origem no fluxo: `utils/processador_di_pre.py`.

## Informacoes Minimas (Campos)

Durante o mapeamento de campos para distribuidoras padrao, a aplicacao espera identificar:

- `empresa`
- `tipo`
- `status`
- `situacao`
- `nome_cliente`
- `classe`
- `contrato`
- `valor_principal`
- `valor_nao_cedido`
- `valor_terceiro`
- `valor_cip`
- `data_vencimento`

Campos recomendados adicionais:

- `documento` (CPF/CNPJ)

Campos criados automaticamente no pipeline:

- `id_padronizado`
- `base_origem`
- `data_base`

## Sequencia Operacional (Encadeamento)

### Etapa A - Carregamento

1. Upload de um ou mais arquivos de carteira.
2. Deteccao de data base (cabecalho com data ou coluna de vencimento).
3. Armazenamento por arquivo no `session_state`.

### Etapa B - Mapeamento

1. Mapeamento automatico por palavras-chave.
2. Ajuste manual de campos.
3. Aplicacao do mapeamento para DataFrame padronizado.
4. Consolidacao de multiplos arquivos.
5. Remocao de duplicatas (rota padrao): chave por nome limpo + valor principal + data vencimento limpa.

### Etapa C - Correcao e Valor Justo

Pre-condicao para executar calculo: todos os 3 insumos auxiliares carregados

- Indices economicos.
- Taxa de recuperacao.
- CDI/DI-PRE.

## Modelo Matematico Das Etapas

### 1) Aging (tempo de atraso)

$$
dias\_atraso = data\_base - data\_vencimento
$$

Classificacao aplicada:

- `A vencer` se $dias\_atraso \le 0$
- `Menor que 30 dias` se $1 \le dias\_atraso \le 30$
- `De 31 a 59 dias`
- `De 60 a 89 dias`
- `De 90 a 119 dias`
- `De 120 a 359 dias`
- `De 360 a 719 dias`
- `De 720 a 1080 dias`
- `Maior que 1080 dias`

### 2) Valor liquido

$$
VL = \max(VP - VNC - VT - VCIP, 0)
$$

Onde:

- $VP$: `valor_principal`
- $VNC$: `valor_nao_cedido`
- $VT$: `valor_terceiro`
- $VCIP$: `valor_cip`

### 3) Encargos moratorios

Multa:

$$
M = \begin{cases}
VL \cdot 0.02, & dias\_atraso > 0 \\
0, & caso\ contrario
\end{cases}
$$

Juros moratorios:

$$
JM = \begin{cases}
VL \cdot 0.01 \cdot \frac{dias\_atraso}{30}, & dias\_atraso > 0 \\
0, & caso\ contrario
\end{cases}
$$

### 4) Correcao monetaria ate data base

No fluxo padrao, a pagina aplica merge de indices por ano/mes e calcula indice diario aproximado.

Taxa mensal no indice:

$$
taxa\_mensal = 1 - \frac{I_{m-1}}{I_m}
$$

Taxa diaria equivalente:

$$
taxa\_diaria = (1 + taxa\_mensal)^{1/30} - 1
$$

Indice na data (quando nao e fechamento do mes):

$$
I_{data} = I_{m-1} \cdot \left[(1+taxa\_diaria)^{d} - 1\right] + I_{m-1}
$$

Fator de correcao ate data base:

$$
F_{corr} = \frac{I_{base}}{I_{venc}}
$$

Correcao monetaria:

$$
CM = \max\left(VL \cdot (F_{corr} - 1), 0\right)
$$

### 5) Valor corrigido ate data base

$$
VC = VL + M + JM + CM
$$

Valor recuperavel na data base:

$$
VR_{base} = VC \cdot taxa\_recuperacao
$$

### 6) Mapeamento de aging para taxa de recuperacao

Mapeamento usado para cruzar com tabela de taxa:

- `A vencer` -> `A vencer`
- `Menor que 30 dias` ate `De 120 a 359 dias` -> `Primeiro ano`
- `De 360 a 719 dias` -> `Segundo ano`
- `De 720 a 1080 dias` -> `Terceiro ano`
- `Maior que 1080 dias` -> `Demais anos`

### 7) Curva CDI/DI-PRE por prazo

Do arquivo BMF:

$$
meses\_futuros \approx round\left(\frac{dias\_corridos}{30.44}\right)
$$

A taxa usada no valuation e a coluna `252`:

$$
taxa\_{DI} = \frac{taxa\_{252}}{100}
$$

Com spread de risco de 2.5% a.a.:

$$
taxa\_{desconto\_total} = taxa\_{DI} + 0.025
$$

Fator de desconto (metodo implementado):

$$
F_{desc} = (1 + taxa\_{desconto\_total})^{meses\_ate\_recebimento/12}
$$

### 8) Correcao ate recebimento e multa de recebimento

IPCA mensal derivado dos indices carregados:

$$
ipca\_{anual} = \frac{Indice\_{hoje}}{Indice\_{12m}} - 1
$$

$$
ipca\_{mensal} = (1 + ipca\_{anual})^{1/12} - 1
$$

Fator de correcao ate recebimento:

$$
F_{corr\_rec} = (1 + ipca\_{mensal})^{meses\_ate\_recebimento}
$$

Multa de recebimento:

$$
multa\_{atraso} = dias\_atraso\_{recebimento} \cdot \frac{0.01}{30}
$$

$$
multa\_{final} = \max(multa\_{atraso}, 0.06)
$$

### 9) Valor justo ate recebimento

No fluxo implementado para distribuidoras padrao:

$$
VJ = \frac{VR}{F_{desc}}
$$

Onde $VR$ e inicialmente derivado de `valor_corrigido * taxa_recuperacao` (ou fallback).

### 10) Remuneracao variavel (haircut pos-valor justo)

Percentuais por aging:

- 6.5%: `A vencer`, `Menor que 30 dias`, `De 31 a 59 dias`, `De 60 a 89 dias`
- 8.0%: `De 90 a 119 dias`
- 15.0%: `De 120 a 359 dias`
- 22.0%: `De 360 a 719 dias`
- 36.0%: `De 720 a 1080 dias`
- 50.0%: `Maior que 1080 dias`

Calculo:

$$
RV\_{valor} = VJ \cdot perc\_{RV}(aging)
$$

$$
VJ\_{pos\_RV} = \max(VJ - RV\_{valor}, 0)
$$

## Saidas Principais Esperadas

Colunas relevantes no resultado final:

- `valor_liquido`
- `multa`
- `juros_moratorios`
- `correcao_monetaria`
- `valor_corrigido`
- `taxa_recuperacao`
- `valor_recuperavel_ate_data_base`
- `taxa_di_pre_percentual`
- `taxa_desconto_total`
- `valor_justo_ate_recebimento`
- `remuneracao_variavel_perc`
- `remuneracao_variavel_valor`
- `remuneracao_variavel_valor_final`
- `valor_justo_pos_rv`

## Observacoes Tecnicas Importantes

1. A execucao exige todos os insumos auxiliares antes do botao de calculo final.
2. O pipeline possui fallbacks (ex.: taxa DI padrao e IPCA mensal padrao) quando algum dado nao encontra correspondencia.
3. O processamento da rota padrao de distribuidoras ocorre na pasta `energisa-fidc-calculator-distrib`, sem depender da pasta `energisa-fidc-calculator-distrib_voltz`.

## Referencias De Implementacao

- `energisa-fidc-calculator-distrib/pages/2_Carregamento.py`
- `energisa-fidc-calculator-distrib/pages/3_Mapeamento.py`
- `energisa-fidc-calculator-distrib/pages/4_Correcao.py`
- `energisa-fidc-calculator-distrib/utils/calculador_aging.py`
- `energisa-fidc-calculator-distrib/utils/calculador_correcao.py`
- `energisa-fidc-calculator-distrib/utils/calculador_valor_justo_distribuidoras.py`
- `energisa-fidc-calculator-distrib/utils/calculador_remuneracao_variavel.py`
- `energisa-fidc-calculator-distrib/utils/processador_di_pre.py`
