/**
 * Service: Aging Calculator
 * Classifies records by days overdue into aging buckets.
 */
import type { AgingBucket, AgingTaxa, MappedRecord, AgingRecord } from "@/types";

/** Classify days overdue into an aging bucket */
export function classifyAging(diasAtraso: number): AgingBucket {
  if (diasAtraso <= 0) return "A vencer";
  if (diasAtraso <= 30) return "Menor que 30 dias";
  if (diasAtraso <= 59) return "De 31 a 59 dias";
  if (diasAtraso <= 89) return "De 60 a 89 dias";
  if (diasAtraso <= 119) return "De 90 a 119 dias";
  if (diasAtraso <= 359) return "De 120 a 359 dias";
  if (diasAtraso <= 719) return "De 360 a 719 dias";
  if (diasAtraso <= 1080) return "De 720 a 1080 dias";
  return "Maior que 1080 dias";
}

/** Map aging bucket to taxa category */
export function agingToTaxaCategory(aging: AgingBucket): AgingTaxa {
  switch (aging) {
    case "A vencer":
      return "A vencer";
    case "Menor que 30 dias":
    case "De 31 a 59 dias":
    case "De 60 a 89 dias":
    case "De 90 a 119 dias":
    case "De 120 a 359 dias":
      return "Primeiro ano";
    case "De 360 a 719 dias":
      return "Segundo ano";
    case "De 720 a 1080 dias":
      return "Terceiro ano";
    case "Maior que 1080 dias":
      return "Demais anos";
  }
}

/** Calculate days overdue */
function calcDiasAtraso(dataVencimento: string, dataBase: string): number {
  const venc = new Date(dataVencimento);
  const base = new Date(dataBase);
  if (isNaN(venc.getTime()) || isNaN(base.getTime())) return 0;
  const diffMs = base.getTime() - venc.getTime();
  return Math.floor(diffMs / (1000 * 60 * 60 * 24));
}

/**
 * Process aging for all records.
 * @param records - Standardized records
 * @returns Records with aging classification
 */
export function processAging(records: MappedRecord[]): AgingRecord[] {
  return records.map((r) => {
    const dias = calcDiasAtraso(r.data_vencimento, r.data_base);
    const aging = classifyAging(dias);
    return {
      ...r,
      dias_atraso: dias,
      aging,
      aging_taxa: agingToTaxaCategory(aging),
    };
  });
}

/** Aging bucket display order */
export const AGING_ORDER: AgingBucket[] = [
  "A vencer",
  "Menor que 30 dias",
  "De 31 a 59 dias",
  "De 60 a 89 dias",
  "De 90 a 119 dias",
  "De 120 a 359 dias",
  "De 360 a 719 dias",
  "De 720 a 1080 dias",
  "Maior que 1080 dias",
];
