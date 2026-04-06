/**
 * Service: Database Processing Pipeline
 *
 * Orchestrates the full FIDC calculation pipeline via Supabase:
 *   1. Create session & upload reference data (indices, recovery rates, DI-PRE)
 *   2. Ingest CSV files into fidc_session_data (via edge function)
 *   3. Run aging calculation (SQL function)
 *   4. Run monetary correction (SQL function)
 *   5. Run fair value + variable remuneration (SQL function)
 *   6. Fetch summary & paginated results
 */
import { supabase, isSupabaseConfigured } from "@/lib/supabase";
import { getCurrentSessionId } from "./storage.service";
import type {
  UploadedFile,
  FieldMapping,
  EconomicIndex,
  RecoveryRate,
  DIPRERate,
} from "@/types";

// ─── Types ────────────────────────────────────────────────────────

export type ProcessingDbStep =
  | "setup"
  | "ingest"
  | "aging"
  | "correction"
  | "fair_value"
  | "complete"
  | "error";

export interface ProcessingDbProgress {
  step: ProcessingDbStep;
  progress: number; // 0-100
  message: string;
  details?: string;
}

export type ProcessingDbCallback = (p: ProcessingDbProgress) => void;

export interface FidcSummary {
  total_rows: number;
  total_valor_principal: number;
  total_valor_liquido: number;
  total_multa: number;
  total_juros_moratorios: number;
  total_correcao_monetaria: number;
  total_valor_corrigido: number;
  total_valor_recuperavel: number;
  total_valor_justo: number;
  total_valor_justo_reajustado: number;
  by_aging: Record<
    string,
    {
      count: number;
      valor_principal: number;
      valor_corrigido: number;
      valor_justo: number;
      valor_justo_reajustado: number;
    }
  >;
  by_empresa: Record<
    string,
    {
      count: number;
      valor_principal: number;
      valor_corrigido: number;
      valor_justo: number;
      valor_justo_reajustado: number;
    }
  >;
}

export interface SessionDataRow {
  id: number;
  file_name: string;
  row_number: number;
  // Campos originais
  empresa: string;
  tipo: string;
  status_conta: string | null;
  situacao: string | null;
  nome_cliente: string | null;
  documento: string | null;
  classe: string | null;
  contrato: string;
  valor_principal: number;
  valor_nao_cedido: number | null;
  valor_terceiro: number | null;
  valor_cip: number | null;
  data_vencimento: string | null;
  data_base: string | null;
  base_origem: string | null;
  is_voltz: boolean;
  // Aging
  dias_atraso: number;
  aging: string;
  aging_taxa: string | null;
  // Correção monetária
  valor_liquido: number;
  multa: number;
  juros_moratorios: number;
  fator_correcao: number | null;
  correcao_monetaria: number;
  valor_corrigido: number;
  juros_remuneratorios: number | null;
  saldo_devedor_vencimento: number | null;
  // Valor justo
  taxa_recuperacao: number;
  prazo_recebimento: number | null;
  valor_recuperavel: number | null;
  valor_justo: number;
  desconto_aging: number;
  valor_justo_reajustado: number;
}

// ─── Helpers ──────────────────────────────────────────────────────

function requireSupabase() {
  if (!isSupabaseConfigured() || !supabase) {
    throw new Error("Supabase não está configurado");
  }
  return supabase;
}

// ─── Step 0: Session + Reference Data ─────────────────────────────

export async function createSession(dataBase: string): Promise<string> {
  const sb = requireSupabase();
  const sessionId = getCurrentSessionId();

  // Upsert session
  const { error } = await sb.from("fidc_sessions").upsert({
    id: sessionId,
    data_base: dataBase,
    status: "active",
    updated_at: new Date().toISOString(),
  });

  if (error) throw new Error(`Erro ao criar sessão: ${error.message}`);
  return sessionId;
}

export async function uploadReferenceData(
  sessionId: string,
  indices: EconomicIndex[],
  recoveryRates: RecoveryRate[],
  diPreRates: DIPRERate[]
): Promise<void> {
  const sb = requireSupabase();

  // Clear existing reference data for this session
  await Promise.all([
    sb.from("fidc_indices").delete().eq("session_id", sessionId),
    sb.from("fidc_recovery_rates").delete().eq("session_id", sessionId),
    sb.from("fidc_di_pre_rates").delete().eq("session_id", sessionId),
  ]);

  // Insert indices in batches
  if (indices.length > 0) {
    const rows = indices.map((i) => ({
      session_id: sessionId,
      date: i.date,
      value: i.value,
    }));
    for (let i = 0; i < rows.length; i += 500) {
      const { error } = await sb
        .from("fidc_indices")
        .insert(rows.slice(i, i + 500));
      if (error)
        throw new Error(`Erro ao inserir índices: ${error.message}`);
    }
  }

  // Insert recovery rates
  if (recoveryRates.length > 0) {
    const rows = recoveryRates.map((r) => ({
      session_id: sessionId,
      empresa: r.empresa,
      tipo: r.tipo,
      aging: r.aging,
      taxa_recuperacao: r.taxa_recuperacao,
      prazo_recebimento: r.prazo_recebimento,
    }));
    const { error } = await sb.from("fidc_recovery_rates").insert(rows);
    if (error)
      throw new Error(`Erro ao inserir taxas de recuperação: ${error.message}`);
  }

  // Insert DI-PRE rates
  if (diPreRates.length > 0) {
    const rows = diPreRates.map((r) => ({
      session_id: sessionId,
      dias_corridos: r.dias_corridos,
      taxa_252: r.taxa_252,
      taxa_360: r.taxa_360,
      meses_futuros: r.meses_futuros,
    }));
    const { error } = await sb.from("fidc_di_pre_rates").insert(rows);
    if (error)
      throw new Error(`Erro ao inserir taxas DI-PRE: ${error.message}`);
  }
}

// ─── Step 1: Ingest CSV via Edge Function ─────────────────────────

export async function ingestFile(
  sessionId: string,
  file: UploadedFile,
  fieldMapping: FieldMapping,
  dataBase: string
): Promise<number> {
  const sb = requireSupabase();

  const filePath = file.csvPath || file.storagePath;
  if (!filePath) {
    throw new Error(`Nenhum caminho de armazenamento para ${file.name}`);
  }

  const { data, error } = await sb.functions.invoke("ingest-csv", {
    body: {
      session_id: sessionId,
      file_path: filePath,
      file_name: file.name,
      field_mapping: fieldMapping,
      is_voltz: file.isVoltz,
      data_base: dataBase,
    },
  });

  if (error) throw new Error(`Ingestão falhou: ${error.message}`);
  if (data?.error) throw new Error(`Ingestão falhou: ${data.error}`);

  return data?.inserted ?? 0;
}

// ─── Step 2: Aging (SQL RPC) ──────────────────────────────────────

export async function runAging(
  sessionId: string
): Promise<{ affected: number; summary: Record<string, number> }> {
  const sb = requireSupabase();

  const { data, error } = await sb.rpc("fidc_calculate_aging", {
    p_session_id: sessionId,
  });

  if (error)
    throw new Error(`Cálculo de aging falhou: ${error.message}`);
  return data as { affected: number; summary: Record<string, number> };
}

// ─── Step 3: Correction (SQL RPC) ─────────────────────────────────

export async function runCorrection(
  sessionId: string
): Promise<{ standard: number; voltz: number; total: number }> {
  const sb = requireSupabase();

  const { data, error } = await sb.rpc("fidc_calculate_correction", {
    p_session_id: sessionId,
  });

  if (error)
    throw new Error(`Cálculo de correção falhou: ${error.message}`);
  return data as { standard: number; voltz: number; total: number };
}

// ─── Step 4: Fair Value (SQL RPC) ─────────────────────────────────

export async function runFairValue(
  sessionId: string,
  spreadPercent: number = 0.025,
  prazoHorizonte: number = 6
): Promise<{
  affected: number;
  total_valor_justo: number;
  total_valor_reajustado: number;
}> {
  const sb = requireSupabase();

  const { data, error } = await sb.rpc("fidc_calculate_fair_value", {
    p_session_id: sessionId,
    p_spread_percent: spreadPercent,
    p_prazo_horizonte: prazoHorizonte,
  });

  if (error)
    throw new Error(`Cálculo de valor justo falhou: ${error.message}`);
  return data as {
    affected: number;
    total_valor_justo: number;
    total_valor_reajustado: number;
  };
}

// ─── Summary & Results ────────────────────────────────────────────

export async function getSummary(sessionId: string): Promise<FidcSummary> {
  const sb = requireSupabase();

  const { data, error } = await sb.rpc("fidc_get_summary", {
    p_session_id: sessionId,
  });

  if (error) throw new Error(`Erro ao obter resumo: ${error.message}`);
  return data as FidcSummary;
}

const ALL_COLUMNS =
  "id,file_name,row_number," +
  "empresa,tipo,status_conta,situacao,nome_cliente,documento,classe,contrato," +
  "valor_principal,valor_nao_cedido,valor_terceiro,valor_cip," +
  "data_vencimento,data_base,base_origem,is_voltz," +
  "dias_atraso,aging,aging_taxa," +
  "valor_liquido,multa,juros_moratorios,fator_correcao,correcao_monetaria," +
  "valor_corrigido,juros_remuneratorios,saldo_devedor_vencimento," +
  "taxa_recuperacao,prazo_recebimento,valor_recuperavel," +
  "valor_justo,desconto_aging,valor_justo_reajustado";

export async function getResults(
  sessionId: string,
  page: number = 0,
  pageSize: number = 50
): Promise<{ data: SessionDataRow[]; count: number }> {
  const sb = requireSupabase();

  const { data, error, count } = await sb
    .from("fidc_session_data")
    .select(ALL_COLUMNS, { count: "exact" })
    .eq("session_id", sessionId)
    .range(page * pageSize, (page + 1) * pageSize - 1)
    .order("row_number", { ascending: true });

  if (error)
    throw new Error(`Erro ao buscar resultados: ${error.message}`);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rows: SessionDataRow[] = (data as any) ?? [];
  return { data: rows, count: count ?? 0 };
}

/**
 * Fetch ALL rows for CSV export (no pagination).
 * Supabase default limit is 1 000 rows, so we paginate internally.
 */
export async function getAllResultsForExport(
  sessionId: string
): Promise<SessionDataRow[]> {
  const sb = requireSupabase();
  const BATCH = 1000;
  const all: SessionDataRow[] = [];
  let offset = 0;
  let keepGoing = true;

  while (keepGoing) {
    const { data, error } = await sb
      .from("fidc_session_data")
      .select(ALL_COLUMNS)
      .eq("session_id", sessionId)
      .range(offset, offset + BATCH - 1)
      .order("row_number", { ascending: true });

    if (error)
      throw new Error(`Erro ao exportar resultados: ${error.message}`);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const rows: SessionDataRow[] = (data as any) ?? [];
    all.push(...rows);
    offset += BATCH;
    if (rows.length < BATCH) keepGoing = false;
  }

  return all;
}

// ─── Full Pipeline Orchestrator ───────────────────────────────────

export async function runFullDbPipeline(
  files: UploadedFile[],
  fieldMappings: Record<string, FieldMapping>,
  indices: EconomicIndex[],
  recoveryRates: RecoveryRate[],
  diPreRates: DIPRERate[],
  dataBase: string,
  onProgress: ProcessingDbCallback
): Promise<string> {
  // Step 0: Session + reference data
  onProgress({
    step: "setup",
    progress: 2,
    message: "Criando sessão no banco de dados...",
  });
  const sessionId = await createSession(dataBase);

  onProgress({
    step: "setup",
    progress: 8,
    message: "Enviando índices e taxas de referência...",
    details: `${indices.length} índices, ${recoveryRates.length} taxas recuperação, ${diPreRates.length} pontos DI-PRE`,
  });
  await uploadReferenceData(sessionId, indices, recoveryRates, diPreRates);

  // Step 1: Ingest files
  let totalInserted = 0;
  const validFiles = files.filter(
    (f) => f.validationStatus === "valid" && (f.csvPath || f.storagePath)
  );

  for (let i = 0; i < validFiles.length; i++) {
    const file = validFiles[i];
    const mapping = fieldMappings[file.id] ?? {};

    onProgress({
      step: "ingest",
      progress: 10 + (i / validFiles.length) * 25,
      message: `Ingestão: ${file.name}`,
      details: `Arquivo ${i + 1} de ${validFiles.length}`,
    });

    const inserted = await ingestFile(sessionId, file, mapping, dataBase);
    totalInserted += inserted;
  }

  onProgress({
    step: "ingest",
    progress: 38,
    message: `${totalInserted.toLocaleString("pt-BR")} registros carregados no banco`,
  });

  // Step 2: Aging
  onProgress({
    step: "aging",
    progress: 42,
    message: "Calculando aging (dias de atraso)...",
  });
  const agingResult = await runAging(sessionId);
  onProgress({
    step: "aging",
    progress: 55,
    message: `Aging calculado para ${agingResult.affected.toLocaleString("pt-BR")} registros`,
    details: Object.entries(agingResult.summary ?? {})
      .map(([k, v]) => `${k}: ${v}`)
      .join(" │ "),
  });

  // Step 3: Correction
  onProgress({
    step: "correction",
    progress: 58,
    message: "Calculando correção monetária...",
  });
  const corrResult = await runCorrection(sessionId);
  onProgress({
    step: "correction",
    progress: 75,
    message: `Correção aplicada: ${corrResult.total.toLocaleString("pt-BR")} registros`,
    details: `Padrão: ${corrResult.standard.toLocaleString("pt-BR")} │ VOLTZ: ${corrResult.voltz.toLocaleString("pt-BR")}`,
  });

  // Step 4: Fair Value + Variable Remuneration
  onProgress({
    step: "fair_value",
    progress: 78,
    message: "Calculando valor justo e remuneração variável...",
  });
  const fvResult = await runFairValue(sessionId);
  onProgress({
    step: "fair_value",
    progress: 95,
    message: `Valor justo calculado para ${fvResult.affected.toLocaleString("pt-BR")} registros`,
  });

  // Update session status
  const sb = requireSupabase();
  await sb
    .from("fidc_sessions")
    .update({ status: "completed", updated_at: new Date().toISOString() })
    .eq("id", sessionId);

  // Done
  onProgress({
    step: "complete",
    progress: 100,
    message: "Pipeline concluído com sucesso!",
    details: `${totalInserted.toLocaleString("pt-BR")} registros processados`,
  });

  return sessionId;
}
