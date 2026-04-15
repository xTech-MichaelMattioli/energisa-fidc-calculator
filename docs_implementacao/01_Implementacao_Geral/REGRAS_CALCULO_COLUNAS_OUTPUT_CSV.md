# REGRAS DE CALCULO DAS COLUNAS DE OUTPUT

## Objetivo
Este documento descreve, **na sequencia exata em que o codigo executa**, cada coluna calculada no output final do sistema. Para cada coluna: a formula implementada e a referencia ao arquivo/metodo Python onde acontece.

## Convencoes
- `valor_corrigido` no DataFrame interno equivale a `valor_corrigido_ate_data_base` no arquivo exportado (rename feito em `auto_export_resultado.py`).
- `documento` e removida no momento da exportacao final.
- Truncamento numerico: valores fora de (-1, 1) com 4 casas; dentro de (-1, 1) ate 8 casas; `ipca_mensal` e colunas `fator_*` sem truncamento.

---

## 1) Fluxo Distribuidoras Padrao

O processamento acontece nas seguintes etapas, nessa ordem:

### Etapa 1 — Mapeamento e identificacao
**Arquivo:** `pages/4_Correcao.py`

| Coluna | Regra | Ref. codigo |
|---|---|---|
| nome_cliente | Copia do campo mapeado de origem. | mapeamento geral |
| contrato | Copia do campo mapeado de origem. | mapeamento geral |
| classe | Copia do campo mapeado de origem. | mapeamento geral |
| situacao | Copia do campo mapeado de origem. | mapeamento geral |
| valor_principal | Copia do campo mapeado de origem. | mapeamento geral |
| valor_nao_cedido | Copia do campo mapeado de origem. | mapeamento geral |
| valor_terceiro | Copia do campo mapeado de origem. | mapeamento geral |
| valor_cip | Copia do campo mapeado de origem. | mapeamento geral |
| data_vencimento | Copia do campo mapeado de origem. | mapeamento geral |
| empresa | Copia do campo mapeado de origem. | mapeamento geral |
| tipo | Copia do campo mapeado de origem. | mapeamento geral |
| status | Copia do campo mapeado de origem. | mapeamento geral |
| id_padronizado | `{base}_{nome_limpo}_{data_vencimento}` com sufixo incremental se duplicar. | mapeamento geral |
| base_origem | Nome do arquivo base carregado. | mapeamento geral |
| data_base | Data base padrao dos parametros. | `params.data_base_padrao` |

### Etapa 2 — Saneamento, aging e correcao ate data base
**Arquivo:** `utils/correcao_otimizada.py` (pipeline vetorizado)

| Coluna | Regra | Ref. codigo |
|---|---|---|
| data_vencimento_limpa | `pd.to_datetime(data_vencimento)`. | `correcao_otimizada.py` |
| dias_atraso | `(data_base - data_vencimento_limpa).days`. | `correcao_otimizada.py` |
| aging | Faixas: `A vencer`, `< 30d`, `31-59d`, `60-89d`, `90-119d`, `120-359d`, `360-719d`, `720-1080d`, `> 1080d`. | `correcao_otimizada.py` |
| valor_principal_limpo | Conversao numerica robusta (formatos BR/EN, invalidos → 0). | `calculador_correcao.py` |
| valor_nao_cedido_limpo | Idem. | `calculador_correcao.py` |
| valor_terceiro_limpo | Idem. | `calculador_correcao.py` |
| valor_cip_limpo | Idem. | `calculador_correcao.py` |
| valor_liquido | `max(principal_limpo - nao_cedido_limpo - terceiro_limpo - cip_limpo, 0)`. | `correcao_otimizada.py` |
| multa | `if dias_atraso > 0: valor_liquido × 0.02 else 0`. | `correcao_otimizada.py` |
| meses_atraso | `dias_atraso / 30`. | `correcao_otimizada.py` |
| juros_moratorios | `if dias_atraso > 0: valor_liquido × 0.01 × meses_atraso else 0`. | `correcao_otimizada.py` |
| indice_vencimento | Indice diario na data de vencimento via merge temporal; fallback para ultimo indice disponivel. | `correcao_otimizada.py` |
| indice_base | Indice diario na data base; fallback para ultimo indice disponivel. | `correcao_otimizada.py` |
| fator_correcao_ate_data_base | `indice_base / indice_vencimento` (validos), senao `1.0`. Rename de `fator_correcao`. | `correcao_otimizada.py` |
| correcao_monetaria | `max(valor_liquido × (fator_correcao_ate_data_base - 1), 0)`. | `correcao_otimizada.py` |
| valor_corrigido | `valor_liquido + multa + juros_moratorios + correcao_monetaria`. Exportado como `valor_corrigido_ate_data_base`. | `correcao_otimizada.py` |

### Etapa 3 — Recuperacao e prazo
**Arquivo:** `utils/calculador_correcao.py` (merge de taxas)

| Coluna | Regra | Ref. codigo |
|---|---|---|
| aging_taxa | Mapeamento de aging para categoria de taxa (`A vencer`, `Primeiro ano`, `Segundo ano`, `Terceiro ano`, `Demais anos`). | `calculador_correcao.py` |
| taxa_recuperacao | Merge por `(empresa, tipo, aging_taxa)` → `Taxa de recuperacao` da tabela de taxas. | `calculador_correcao.py` |
| prazo_recebimento | Merge por `(empresa, tipo, aging_taxa)` → `Prazo de recebimento`. | `calculador_correcao.py` |
| valor_recuperavel_ate_data_base | `valor_corrigido × taxa_recuperacao`. | `correcao_otimizada.py` |

### Etapa 4 — DI-PRE, IPCA, projecao ate recebimento
**Arquivo:** `utils/calculador_valor_justo_distribuidoras.py` → metodos `_calcular_meses_recebimento`, `_aplicar_taxas_di_pre`, `_calcular_taxas_anualizadas`, `_calcular_ipca_mensal`
**Fonte DI-PRE (B3):** [https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/txref1.asp](https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/txref1.asp)

| Coluna | Regra | Ref. codigo |
|---|---|---|
| meses_ate_recebimento | Merge por `(empresa, tipo, aging_taxa)` com `Prazo de recebimento`; fallback `6`. | `_calcular_meses_recebimento` |
| taxa_di_pre_percentual | Merge com curva DI-PRE por `meses_ate_recebimento`; sem match exato usa prazo mais proximo. | `_aplicar_taxas_di_pre` |
| taxa_di_pre_decimal | `taxa_di_pre_percentual / 100`. | `_calcular_taxas_anualizadas` |
| taxa_di_pre_total_anual | `((1 + taxa_di_pre_decimal) × (1 + 0.025)) - 1`. | `_calcular_taxas_anualizadas` |
| taxa_desconto_mensal | `(1 + taxa_di_pre_total_anual)^(1/12) - 1`. | `_calcular_taxas_anualizadas` |
| data_recebimento_estimada | `data_base + meses_ate_recebimento` (calendario real, dia do mes preservado). | `_calcular_meses_recebimento` |
| ipca_anual | `PROD(1 + r_t, t=1..12) - 1`, media sazonal 3 anos por mes. | `_calcular_ipca_mensal` |
| ipca_mensal | Taxa projetada m+1 pela media dos ultimos 3 anos do mesmo mes; fallback `0.0037`. | `_calcular_ipca_mensal` |
| fator_correcao_ate_recebimento | `(1 + ipca_mensal) ^ meses_ate_recebimento`. | `_calcular_ipca_mensal` |
| mora_ate_recebimento | `valor_corrigido × 0.01 × meses_ate_recebimento` (mora simples 1% a.m.). | `_calcular_ipca_mensal` |
| valor_corrigido_ate_recebimento | `valor_corrigido × fator_correcao_ate_recebimento + mora_ate_recebimento`. | `_calcular_ipca_mensal` |
| fator_de_desconto | `(1 + taxa_desconto_mensal) ^ meses_ate_recebimento`. | `_calcular_ipca_mensal` |

### Etapa 5 — Valor recuperavel ate recebimento e fator de desconto VP
**Arquivo:** `utils/calculador_valor_justo_distribuidoras.py` → metodo `_calcular_valor_justo_final`

| Coluna | Regra | Ref. codigo |
|---|---|---|
| valor_recuperavel_ate_recebimento | `max(valor_corrigido_ate_recebimento × taxa_recuperacao, 0)`. | `_calcular_valor_justo_final` |
| cdi_taxa_prazo | Copia de `taxa_di_pre_decimal`. | `_calcular_valor_justo_final` |
| taxa_desconto_total | `((1 + cdi_taxa_prazo) × (1 + 0.025)) - 1`. | `_calcular_valor_justo_final` |
| anos_ate_recebimento | `meses_ate_recebimento / 12`. | `_calcular_valor_justo_final` |
| fator_de_desconto_vp | `(1 + taxa_desconto_total) ^ anos_ate_recebimento`. | `_calcular_valor_justo_final` |
| data_calculo | `datetime.now()` formatado `%Y-%m-%d %H:%M:%S`. | `_calcular_valor_justo_final` |

### Etapa 6 — Remuneracao variavel e valor justo final
**Arquivo:** `utils/calculador_correcao.py` → metodo `calcular_valor_justo_reajustado`, que internamente usa `utils/calculador_remuneracao_variavel.py`

| Coluna | Regra | Ref. codigo |
|---|---|---|
| remuneracao_variavel_perc | Percentual por faixa de aging: `A vencer 6.5%`, `< 30d 6.5%`, `31-59d 6.5%`, `60-89d 6.5%`, `90-119d 8%`, `120-359d 15%`, `360-719d 22%`, `720-1080d 36%`, `> 1080d 50%`. | `CalculadorRemuneracaoVariavel.calcular_remuneracao_variavel` |
| remuneracao_variavel_valor | `valor_recuperavel_ate_recebimento × remuneracao_variavel_perc`. | `CalculadorRemuneracaoVariavel.calcular_remuneracao_variavel` |
| remuneracao_variavel_valor_final | `max(valor_recuperavel_ate_recebimento - remuneracao_variavel_valor, 0)`. | `CalculadorRemuneracaoVariavel.calcular_remuneracao_variavel` |
| valor_justo | `max(remuneracao_variavel_valor_final / fator_de_desconto_vp, 0)`. Coluna final do output. | `calcular_valor_justo_reajustado` |

---

## 2) Fluxo VOLTZ

### Etapas VOLTZ (sequencia)

#### Etapa 1 — Mapeamento, aging e correcao ate data base
**Arquivo:** `utils/calculador_voltz.py`

| Coluna | Regra | Ref. codigo |
|---|---|---|
| empresa | `VOLTZ`. | mapeamento |
| dias_atraso | `max((data_base - data_vencimento_limpa).days, 0)`. | `calculador_voltz.py` |
| meses_atraso | `dias_atraso / 30`. | `calculador_voltz.py` |
| esta_vencido | `dias_atraso > 0`. | `calculador_voltz.py` |
| valor_liquido | `max(valor_principal_limpo, 0)` (sem deducoes). | `calculador_voltz.py` |
| indice_vencimento | Indice proporcional IGP-M na data de vencimento. | `calculador_voltz.py` |
| indice_base | Indice proporcional IGP-M na data base (media movel se data base > ultimo indice). | `calculador_voltz.py` |
| juros_remuneratorios_ate_data_base | `valor_liquido × ((1.0465)^(max((data_base-data_vencimento)/30, 0)) - 1)`. | `calculador_voltz.py` |
| correcao_monetaria_igpm | `max(valor_liquido × (fator_igpm_ate_data_base - 1), 0)`. | `calculador_voltz.py` |
| multa | `if esta_vencido: valor_liquido × 0.02 else 0`. | `calculador_voltz.py` |
| juros_moratorios_ate_data_base | `valor_liquido × 0.01 × meses_atraso` (vencidos); `0` (nao vencidos). | `calculador_voltz.py` |
| valor_corrigido_ate_data_base | `max(valor_liquido + juros_remuneratorios + multa + juros_moratorios + correcao_igpm, 0)`. | `calculador_voltz.py` |

#### Etapa 2 — Recuperacao e prazo VOLTZ
**Arquivo:** `utils/calculador_voltz.py`

| Coluna | Regra | Ref. codigo |
|---|---|---|
| aging_taxa | Mapeamento VOLTZ de aging para categoria de taxa. | `calculador_voltz.py` |
| taxa_recuperacao | Merge por `(empresa, aging_taxa)`; fallback `0.10`. | `calculador_voltz.py` |
| meses_ate_recebimento | `Prazo de recebimento` da tabela de taxas; fallback `12`. | `calculador_voltz.py` |
| data_recebimento | Soma de meses por calendario real a partir de `data_base`. | `calculador_voltz.py` |

#### Etapa 3 — Projecao ate recebimento VOLTZ
**Arquivo:** `utils/calculador_voltz.py`

| Coluna | Regra | Ref. codigo |
|---|---|---|
| indice_recebimento | Indice proporcional na data de recebimento; extrapolacao se excede serie historica. | `calculador_voltz.py` |
| juros_remuneratorios_recebimento | `valor_corrigido_ate_data_base × ((1.0465)^(meses_ate_recebimento) - 1)`, piso 0. | `calculador_voltz.py` |
| correcao_igpm_recebimento | `valor_corrigido_ate_data_base × (fator_igpm_recebimento - 1)`. | `calculador_voltz.py` |
| juros_moratorios_recebimento | `if esta_vencido: valor_corrigido_ate_data_base × 0.01 × meses_ate_recebimento else 0`. | `calculador_voltz.py` |
| valor_corrigido_ate_recebimento | `max(valor_corrigido_ate_data_base + juros_remuneratorios_recebimento + correcao_igpm_recebimento + juros_moratorios_recebimento, 0)`. | `calculador_voltz.py` |
| valor_recuperavel_ate_recebimento | `max(valor_corrigido_ate_recebimento × taxa_recuperacao, 0)`. | `calculador_voltz.py` |

#### Etapa 4 — RV e valor justo VOLTZ
**Arquivo:** `utils/calculador_correcao.py` → `calcular_valor_justo_reajustado`

| Coluna | Regra | Ref. codigo |
|---|---|---|
| remuneracao_variavel_voltz_perc | Percentual RV por faixa aging (configuracao VOLTZ). | `calculador_remuneracao_variavel.py` |
| remuneracao_variavel_voltz_valor | `valor_recuperavel_ate_recebimento × remuneracao_variavel_voltz_perc`. | `calculador_remuneracao_variavel.py` |
| valor_recuperavel_pos_remuneracao_variavel | `max(valor_recuperavel_ate_recebimento - remuneracao_variavel_voltz_valor, 0)`. | `calculador_remuneracao_variavel.py` |
| fator_de_desconto | `(1 + taxa_desconto_mensal) ^ meses_ate_recebimento`. | `calculador_voltz.py` |
| valor_justo | `max(valor_recuperavel_pos_remuneracao_variavel / fator_de_desconto, 0)`. | `calcular_valor_justo_reajustado` |

### Colunas excluidas no fluxo VOLTZ antes do export
`status`, `valor_nao_cedido`, `valor_terceiro`, `valor_cip`, `base_origem`, `fator_igpm_ate_data_base`, `fator_juros_moratorios_ate_data_base`, `tipo`, `valor_recuperavel_ate_data_base`, `indice_base_proporcional`, `fator_igpm_recebimento`.

---

## 3) Cadeia resumida de formulas-chave

### Padrao (sequencia de execucao)
```
valor_liquido = principal - nao_cedido - terceiro - cip
valor_corrigido = valor_liquido + multa + juros_moratorios + correcao_monetaria
fator_correcao_ate_recebimento = (1 + ipca_mensal) ^ meses_ate_recebimento
mora_ate_recebimento = valor_corrigido × 0.01 × meses_ate_recebimento
valor_corrigido_ate_recebimento = valor_corrigido × fator_correcao_ate_recebimento + mora_ate_recebimento
valor_recuperavel_ate_recebimento = valor_corrigido_ate_recebimento × taxa_recuperacao
remuneracao_variavel_valor = valor_recuperavel_ate_recebimento × remuneracao_variavel_perc
remuneracao_variavel_valor_final = valor_recuperavel_ate_recebimento - remuneracao_variavel_valor
fator_de_desconto_vp = (1 + taxa_desconto_total) ^ (meses_ate_recebimento / 12)
valor_justo = remuneracao_variavel_valor_final / fator_de_desconto_vp
```

### VOLTZ (sequencia de execucao)
```
valor_corrigido_ate_data_base = valor_liquido + juros_remuneratorios + multa + juros_moratorios + correcao_igpm
valor_corrigido_ate_recebimento = valor_corrigido_ate_data_base + juros_remuneratorios_recebimento + correcao_igpm_recebimento + juros_moratorios_recebimento
valor_recuperavel_ate_recebimento = valor_corrigido_ate_recebimento × taxa_recuperacao
remuneracao_variavel_voltz_valor = valor_recuperavel_ate_recebimento × remuneracao_variavel_voltz_perc
valor_recuperavel_pos_rv = valor_recuperavel_ate_recebimento - remuneracao_variavel_voltz_valor
valor_justo = valor_recuperavel_pos_rv / fator_de_desconto
```

---

## 4) Nota de governanca
Este documento descreve a regra **implementada no codigo atual**. Se houver alteracao de formula no codigo, atualizar este arquivo junto com a mudanca.
