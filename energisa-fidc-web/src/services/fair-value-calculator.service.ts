/**
 * Service: Fair Value (Valor Justo) Calculator
 * Applies recovery rates, discount factor, and variable remuneration.
 *
 * Fair Value Formula:
 *   VJ = VC × TR × (FC_recebimento + mora) / FD
 *
 * Where:
 *   VC  = Valor Corrigido
 *   TR  = Taxa de Recuperação (por empresa, tipo, aging)
 *   FC  = Fator Correção até recebimento = (1 + ipca_mensal)^meses
 *   mora = meses × 0.01
 *   FD  = Fator de Desconto = (1 + taxa_desconto_mensal)^meses
 */
import type {
  CorrectedRecord,
  FinalRecord,
  RecoveryRate,
  DIPRERate,
  EconomicIndex,
  AgingBucket,
} from "@/types";

/** Default VOLTZ recovery rates */
const VOLTZ_DEFAULT_RATES: Record<string, { taxa: number; prazo: number }> = {
  "A vencer": { taxa: 0.98, prazo: 6 },
  "Primeiro ano": { taxa: 0.90, prazo: 6 },
  "Segundo ano": { taxa: 0.75, prazo: 12 },
  "Terceiro ano": { taxa: 0.60, prazo: 18 },
  "Quarto ano": { taxa: 0.45, prazo: 24 },
  "Quinto ano": { taxa: 0.30, prazo: 30 },
  "Demais anos": { taxa: 0.15, prazo: 36 },
};

/** Variable remuneration discounts (by aging bucket) */
const REMUNERATION_DISCOUNTS: Record<AgingBucket, number> = {
  "A vencer": 0.065,
  "Menor que 30 dias": 0.065,
  "De 31 a 59 dias": 0.065,
  "De 60 a 89 dias": 0.065,
  "De 90 a 119 dias": 0.08,
  "De 120 a 359 dias": 0.15,
  "De 360 a 719 dias": 0.22,
  "De 720 a 1080 dias": 0.36,
  "Maior que 1080 dias": 0.50,
};

interface FairValueParams {
  recoveryRates: RecoveryRate[];
  diPreRates: DIPRERate[];
  indices: EconomicIndex[];
  spreadPercent: number;   // default 0.025 (2.5%)
  prazoHorizonte: number;  // default 6 months
}

/**
 * Find recovery rate for a specific record.
 */
function findRecoveryRate(
  rates: RecoveryRate[],
  empresa: string,
  tipo: string,
  aging: string,
  isVoltz: boolean
): { taxa: number; prazo: number } {
  if (isVoltz) {
    return VOLTZ_DEFAULT_RATES[aging] ?? { taxa: 0.15, prazo: 36 };
  }

  const match = rates.find(
    (r) =>
      r.empresa.toUpperCase() === empresa.toUpperCase() &&
      r.tipo.toLowerCase() === tipo.toLowerCase() &&
      r.aging === aging
  );

  if (match) {
    return {
      taxa: match.taxa_recuperacao,
      prazo: match.prazo_recebimento,
    };
  }

  // Fallback: try same empresa, any tipo
  const fallback = rates.find(
    (r) =>
      r.empresa.toUpperCase() === empresa.toUpperCase() && r.aging === aging
  );

  return fallback
    ? { taxa: fallback.taxa_recuperacao, prazo: fallback.prazo_recebimento }
    : { taxa: 0, prazo: 6 };
}

/**
 * Calculate DI-PRE-based discount rate.
 */
function getDIPreRate(
  rates: DIPRERate[],
  horizonte: number
): number {
  const match = rates.find((r) => r.meses_futuros === horizonte);
  if (match) return match.taxa_252 / 100;

  // Find closest
  if (rates.length === 0) return 0.12; // fallback 12%
  const sorted = [...rates].sort(
    (a, b) =>
      Math.abs(a.meses_futuros - horizonte) -
      Math.abs(b.meses_futuros - horizonte)
  );
  return sorted[0].taxa_252 / 100;
}

/**
 * Calculate monthly IPCA from index series (last 12 months).
 */
function getIPCAMonthly(indices: EconomicIndex[]): number {
  if (indices.length < 13) return 0.004; // fallback ~5% annual

  const sorted = [...indices].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );
  const current = sorted[sorted.length - 1].value;
  const prev12 = sorted[sorted.length - 13].value;

  if (prev12 <= 0) return 0.004;

  const ipcaAnual = current / prev12 - 1;
  return Math.pow(1 + ipcaAnual, 1 / 12) - 1;
}

/**
 * Calculate fair value for all records.
 */
export function calculateFairValue(
  records: CorrectedRecord[],
  params: FairValueParams
): FinalRecord[] {
  const {
    recoveryRates,
    diPreRates,
    indices,
    spreadPercent = 0.025,
    prazoHorizonte = 6,
  } = params;

  // DI-PRE annual rate
  const diPreAnual = getDIPreRate(diPreRates, prazoHorizonte);
  const taxaDiPreTotal = (1 + diPreAnual) * (1 + spreadPercent) - 1;
  const taxaDescontoMensal = Math.pow(1 + taxaDiPreTotal, 1 / 12) - 1;

  // IPCA monthly
  const ipcaMensal = getIPCAMonthly(indices);

  return records.map((r) => {
    const isVoltz = r.empresa.toUpperCase() === "VOLTZ";
    const { taxa, prazo } = findRecoveryRate(
      recoveryRates,
      r.empresa,
      r.tipo,
      r.aging_taxa,
      isVoltz
    );

    const mesesAteRecebimento = prazo;

    // Recovery value at base date
    const valorRecuperavel = r.valor_corrigido * taxa;

    // Correction factor to receipt date
    const fatorCorrecaoRecebimento = Math.pow(
      1 + ipcaMensal,
      mesesAteRecebimento
    );

    // Late payment charge
    const mora = mesesAteRecebimento * 0.01;

    // Discount factor
    const fatorDesconto = Math.pow(
      1 + taxaDescontoMensal,
      mesesAteRecebimento
    );

    // Fair value
    const valorJusto =
      fatorDesconto > 0
        ? (r.valor_corrigido *
            taxa *
            (fatorCorrecaoRecebimento + mora)) /
          fatorDesconto
        : 0;

    // Variable remuneration discount
    const descontoAging = REMUNERATION_DISCOUNTS[r.aging] ?? 0.5;
    const valorJustoReajustado = valorJusto * (1 - descontoAging);

    return {
      ...r,
      taxa_recuperacao: taxa,
      prazo_recebimento: prazo,
      valor_recuperavel: valorRecuperavel,
      valor_justo: valorJusto,
      desconto_aging: descontoAging,
      valor_justo_reajustado: valorJustoReajustado,
    };
  });
}
