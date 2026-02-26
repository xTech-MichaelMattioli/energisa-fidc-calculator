/**
 * Service: Monetary Correction Calculator
 * Implements the full correction pipeline for standard distribuidoras.
 *
 * Formula:
 *   VL = VP - VNC - VT - VCIP   (min 0)
 *   Multa = VL × 0.02           (if dias_atraso > 0)
 *   JM = VL × 0.01 × (DA/30)   (if dias_atraso > 0)
 *   CM = VL × (IDB/IDV - 1)     (if dias_atraso > 0, min 0)
 *   VC = VL + Multa + JM + CM
 */
import type {
  AgingRecord,
  CorrectedRecord,
  EconomicIndex,
} from "@/types";

export interface CorrectionParams {
  taxaMulta: number;          // default 0.02
  taxaJurosMensal: number;    // default 0.01
  indices: EconomicIndex[];   // loaded IGP-M/IPCA index series
  dataBase: string;           // ISO date
}

const DEFAULT_PARAMS: CorrectionParams = {
  taxaMulta: 0.02,
  taxaJurosMensal: 0.01,
  indices: [],
  dataBase: "2025-04-30",
};

/**
 * Find the closest index value for a given date.
 */
function findIndex(indices: EconomicIndex[], dateStr: string): number {
  if (indices.length === 0) return 1;
  const target = new Date(dateStr).getTime();

  let closest = indices[0];
  let minDiff = Math.abs(new Date(closest.date).getTime() - target);

  for (const idx of indices) {
    const diff = Math.abs(new Date(idx.date).getTime() - target);
    if (diff < minDiff) {
      minDiff = diff;
      closest = idx;
    }
  }
  return closest.value;
}

/**
 * Calculate monetary correction for standard distribuidoras.
 */
export function calculateCorrection(
  records: AgingRecord[],
  params: Partial<CorrectionParams> = {}
): CorrectedRecord[] {
  const p = { ...DEFAULT_PARAMS, ...params };

  return records.map((r) => {
    // Net value
    const valorLiquido = Math.max(
      r.valor_principal - r.valor_nao_cedido - r.valor_terceiro - r.valor_cip,
      0
    );

    const isOverdue = r.dias_atraso > 0;

    // Penalty (multa)
    const multa = isOverdue ? valorLiquido * p.taxaMulta : 0;

    // Late interest (juros moratórios)
    const mesesAtraso = r.dias_atraso / 30;
    const jurosMoratorios = isOverdue
      ? valorLiquido * p.taxaJurosMensal * mesesAtraso
      : 0;

    // Monetary correction via index
    let fatorCorrecao = 1;
    let correcaoMonetaria = 0;

    if (isOverdue && p.indices.length > 0) {
      const indiceBase = findIndex(p.indices, p.dataBase);
      const indiceVenc = findIndex(p.indices, r.data_vencimento);
      fatorCorrecao = indiceVenc > 0 ? indiceBase / indiceVenc : 1;
      correcaoMonetaria = Math.max(valorLiquido * (fatorCorrecao - 1), 0);
    }

    const valorCorrigido =
      valorLiquido + multa + jurosMoratorios + correcaoMonetaria;

    return {
      ...r,
      valor_liquido: valorLiquido,
      multa,
      juros_moratorios: jurosMoratorios,
      fator_correcao: fatorCorrecao,
      correcao_monetaria: correcaoMonetaria,
      valor_corrigido: valorCorrigido,
    };
  });
}

/**
 * Calculate monetary correction for VOLTZ (fintech-specific rules).
 *
 * Differences from standard:
 *  - valor_liquido = valor_principal (no deductions)
 *  - juros_remuneratorios = VL × 4.65%
 *  - Always uses IGP-M (never IPCA)
 *  - Different compounding for juros moratórios
 */
export function calculateCorrectionVoltz(
  records: AgingRecord[],
  params: Partial<CorrectionParams> & {
    taxaJurosRemuneratorios?: number;
  } = {}
): CorrectedRecord[] {
  const p = { ...DEFAULT_PARAMS, ...params };
  const taxaJR = params.taxaJurosRemuneratorios ?? 0.0465;

  return records.map((r) => {
    const valorLiquido = r.valor_principal; // No deductions for VOLTZ
    const jurosRemuneratorios = valorLiquido * taxaJR;
    const saldoDevedorVencimento = valorLiquido + jurosRemuneratorios;

    const isOverdue = r.dias_atraso > 0;

    // IGP-M correction on saldo devedor
    let fatorCorrecao = 1;
    let correcaoMonetaria = 0;

    if (isOverdue && p.indices.length > 0) {
      const idxBase = findIndex(p.indices, p.dataBase);
      const idxVenc = findIndex(p.indices, r.data_vencimento);
      fatorCorrecao = idxVenc > 0 ? idxBase / idxVenc : 1;
      correcaoMonetaria = Math.max(
        saldoDevedorVencimento * (fatorCorrecao - 1),
        0
      );
    }

    const saldoCorrigidoIgpm = saldoDevedorVencimento + correcaoMonetaria;

    // Multa (2% sobre saldo devedor no vencimento, NÃO sobre saldo corrigido)
    const multa = isOverdue ? saldoDevedorVencimento * p.taxaMulta : 0;

    // Juros moratórios (composto, sobre saldo devedor no vencimento)
    const meses = r.dias_atraso / 30.44;
    const jurosMoratorios = isOverdue
      ? saldoDevedorVencimento * (Math.pow(1 + p.taxaJurosMensal, meses) - 1)
      : 0;

    const valorCorrigido = saldoCorrigidoIgpm + multa + jurosMoratorios;

    return {
      ...r,
      valor_liquido: valorLiquido,
      juros_remuneratorios: jurosRemuneratorios,
      saldo_devedor_vencimento: saldoDevedorVencimento,
      multa,
      juros_moratorios: jurosMoratorios,
      fator_correcao: fatorCorrecao,
      correcao_monetaria: correcaoMonetaria,
      valor_corrigido: valorCorrigido,
    };
  });
}
