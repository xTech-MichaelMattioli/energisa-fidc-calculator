/**
 * Service: Calculation Pipeline Orchestrator
 * Runs the full FIDC calculation pipeline with progress reporting.
 *
 * Pipeline:
 *   1. Validate Data  →  2. Aging  →  3. Correction  →  4. Recovery Rates
 *   →  5. Fair Value  →  6. Variable Remuneration  →  7. Export Ready
 *
 * Can run locally or delegate to Supabase Edge Functions.
 */
import type {
  MappedRecord,
  FinalRecord,
  ProcessingProgress,
  RecoveryRate,
  DIPRERate,
  EconomicIndex,
} from "@/types";
import { processAging } from "./aging-calculator.service";
import {
  calculateCorrection,
  calculateCorrectionVoltz,
} from "./correction-calculator.service";
import { calculateFairValue } from "./fair-value-calculator.service";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import { delay } from "@/lib/utils";

export interface PipelineInput {
  records: MappedRecord[];
  indices: EconomicIndex[];
  recoveryRates: RecoveryRate[];
  diPreRates: DIPRERate[];
  dataBase: string;
  spreadPercent?: number;
}

export type ProgressCallback = (progress: ProcessingProgress) => void;

/**
 * Run the full calculation pipeline.
 */
export async function runPipeline(
  input: PipelineInput,
  onProgress?: ProgressCallback
): Promise<FinalRecord[]> {
  const report = (step: ProcessingProgress["step"], progress: number, message: string, details?: string) => {
    onProgress?.({ step, progress, message, details });
  };

  // If Supabase is configured, delegate to edge function
  if (isSupabaseConfigured() && supabase) {
    return runPipelineRemote(input, onProgress);
  }

  // ── Step 1: Validate ───────────────────────────────────────────
  report("validating", 5, "Validando dados de entrada...", `${input.records.length} registros`);
  await delay(300);

  const validRecords = input.records.filter(
    (r) => r.valor_principal > 0 && r.data_vencimento
  );
  report("validating", 15, `${validRecords.length} registros válidos`, `${input.records.length - validRecords.length} removidos`);
  await delay(200);

  // ── Step 2: Aging ──────────────────────────────────────────────
  report("aging", 20, "Calculando aging (dias de atraso)...");
  await delay(200);

  const agingRecords = processAging(validRecords);
  report("aging", 30, "Aging calculado com sucesso", `Buckets classificados para ${agingRecords.length} registros`);
  await delay(200);

  // ── Step 3: Monetary Correction ────────────────────────────────
  report("correction", 35, "Aplicando correção monetária...");
  await delay(200);

  // Separate Voltz from standard
  const voltzRecords = agingRecords.filter(
    (r) => r.empresa.toUpperCase() === "VOLTZ"
  );
  const stdRecords = agingRecords.filter(
    (r) => r.empresa.toUpperCase() !== "VOLTZ"
  );

  const correctedStd = calculateCorrection(stdRecords, {
    indices: input.indices,
    dataBase: input.dataBase,
  });

  report("correction", 50, "Correção aplicada para distribuidoras padrão", `${correctedStd.length} registros`);
  await delay(200);

  const correctedVoltz = calculateCorrectionVoltz(voltzRecords, {
    indices: input.indices,
    dataBase: input.dataBase,
  });

  report("correction", 60, "Correção VOLTZ aplicada", `${correctedVoltz.length} registros`);
  await delay(200);

  const allCorrected = [...correctedStd, ...correctedVoltz];

  // ── Step 4: Fair Value ─────────────────────────────────────────
  report("fair-value", 65, "Calculando valor justo com DI-PRE...");
  await delay(300);

  const finalRecords = calculateFairValue(allCorrected, {
    recoveryRates: input.recoveryRates,
    diPreRates: input.diPreRates,
    indices: input.indices,
    spreadPercent: input.spreadPercent ?? 0.025,
    prazoHorizonte: 6,
  });

  report("fair-value", 80, "Valor justo calculado", `Taxa DI-PRE + spread 2.5%`);
  await delay(200);

  // ── Step 5: Variable Remuneration ──────────────────────────────
  report("remuneration", 85, "Aplicando remuneração variável...");
  await delay(200);

  // Already computed inside calculateFairValue
  report("remuneration", 95, "Remuneração variável aplicada");
  await delay(200);

  // ── Done ───────────────────────────────────────────────────────
  report("complete", 100, "Processamento concluído!", `${finalRecords.length} registros processados`);

  return finalRecords;
}

/**
 * Run pipeline via Supabase Edge Function (future implementation).
 */
async function runPipelineRemote(
  input: PipelineInput,
  onProgress?: ProgressCallback
): Promise<FinalRecord[]> {
  onProgress?.({
    step: "validating",
    progress: 10,
    message: "Enviando dados para processamento remoto...",
  });

  if (!supabase) throw new Error("Supabase não configurado");

  const { data, error } = await supabase.functions.invoke(
    "calculate-fidc",
    {
      body: {
        records: input.records,
        indices: input.indices,
        recoveryRates: input.recoveryRates,
        diPreRates: input.diPreRates,
        dataBase: input.dataBase,
        spreadPercent: input.spreadPercent,
      },
    }
  );

  if (error) throw new Error(`Erro no processamento remoto: ${error.message}`);

  onProgress?.({
    step: "complete",
    progress: 100,
    message: "Processamento remoto concluído!",
  });

  return data as FinalRecord[];
}
