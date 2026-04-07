/**
 * Service: Database Processing Pipeline
 *
 * Orchestrates the FIDC pipeline via Supabase:
 *   1. Create session & upload reference data (indices, recovery rates, DI-PRE)
 *   2. Ingest CSV files into fidc_session_data (via edge function)
 *   3. Results are computed on-the-fly via vw_fidc_results view
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
  | "complete"
  | "error";

export interface ProcessingDbProgress {
  step: ProcessingDbStep;
  progress: number; // 0-100
  message: string;
  details?: string;
  /** Emitted once after session is created so callers can store it even if pipeline fails later */
  sessionId?: string;
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
  by_aging: Record<
    string,
    {
      count: number;
      valor_principal: number;
      valor_corrigido: number;
      valor_justo: number;
    }
  >;
  by_empresa: Record<
    string,
    {
      count: number;
      valor_principal: number;
      valor_corrigido: number;
      valor_justo: number;
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
  // Aging (computed by view)
  dias_atraso: number;
  aging: string;
  aging_taxa: string | null;
  // Correção monetária (computed by view)
  valor_liquido: number;
  multa: number;
  juros_moratorios: number;
  fator_correcao: number | null;
  correcao_monetaria: number;
  valor_corrigido: number;
  juros_remuneratorios: number | null;
  saldo_devedor_vencimento: number | null;
  // Valor justo (computed by view)
  taxa_recuperacao: number;
  prazo_recebimento: number | null;
  valor_recuperavel: number | null;
  valor_justo: number;
}

/**
 * Informações de um arquivo que o worker precisa para baixar e parsear do Storage.
 * Armazenado em fidc_sessions.metadata.files[].
 */
export interface SessionFileMeta {
  /** Nome original do arquivo */
  name: string;
  /** Se pertence à empresa VOLTZ */
  is_voltz: boolean;
  /** Mapeamento de campos: { campo_interno: coluna_csv } */
  field_mapping: FieldMapping;
  /** Paths no Storage onde os chunks (ou arquivo único) estão */
  paths: string[];
}

// ─── Helpers ──────────────────────────────────────────────────────

function requireSupabase() {
  if (!isSupabaseConfigured() || !supabase) {
    throw new Error("Supabase não está configurado");
  }
  return supabase;
}

// ─── Step 0: Session + Reference Data ─────────────────────────────

export async function createSession(
  dataBase: string,
  spreadPercent: number = 0.025,
  prazoHorizonte: number = 6,
  files: SessionFileMeta[] = []
): Promise<string> {
  const sb = requireSupabase();
  const sessionId = getCurrentSessionId();

  const { error } = await sb.from("fidc_sessions").upsert({
    id: sessionId,
    data_base: dataBase,
    status: "active",
    updated_at: new Date().toISOString(),
    metadata: {
      spread_percent:  spreadPercent,
      prazo_horizonte: prazoHorizonte,
      data_base:       dataBase,
      files,           // worker lê daqui para baixar os CSVs do Storage
    },
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

  await Promise.all([
    sb.from("fidc_indices").delete().eq("session_id", sessionId),
    sb.from("fidc_recovery_rates").delete().eq("session_id", sessionId),
    sb.from("fidc_di_pre_rates").delete().eq("session_id", sessionId),
  ]);

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
  dataBase: string,
  onChunkProgress?: (chunksCompleted: number, chunksTotal: number) => void
): Promise<number> {
  const sb = requireSupabase();

  const paths: string[] = file.chunkPaths?.length
    ? file.chunkPaths
    : (() => {
        const p = file.csvPath || file.storagePath;
        if (!p) throw new Error(`Nenhum caminho de armazenamento para ${file.name}`);
        return [p];
      })();

  const { error: delError } = await sb.rpc("fidc_delete_file_rows", {
    p_session_id: sessionId,
    p_file_name: file.name,
  });

  if (delError) throw new Error(`Limpeza de dados anterior falhou: ${delError.message}`);

  const CONCURRENCY = 5;
  const ROW_OFFSET_STRIDE = 100_000;
  let totalInserted = 0;

  for (let i = 0; i < paths.length; i += CONCURRENCY) {
    const slice = paths.slice(i, i + CONCURRENCY);

    const results = await Promise.all(
      slice.map((filePath, sliceIdx) =>
        sb.functions.invoke("ingest-csv", {
          body: {
            session_id: sessionId,
            file_path: filePath,
            file_name: file.name,
            field_mapping: fieldMapping,
            is_voltz: file.isVoltz,
            data_base: dataBase,
            row_number_offset: (i + sliceIdx) * ROW_OFFSET_STRIDE,
          },
        })
      )
    );

    for (let j = 0; j < results.length; j++) {
      const { data, error } = results[j];
      const chunkIdx = i + j + 1;
      if (error) throw new Error(`Ingestão falhou (chunk ${chunkIdx}/${paths.length}): ${error.message}`);
      if (data?.error) throw new Error(`Ingestão falhou (chunk ${chunkIdx}/${paths.length}): ${data.error}`);
      totalInserted += data?.inserted ?? 0;
    }

    const chunksCompleted = Math.min(i + CONCURRENCY, paths.length);
    onChunkProgress?.(chunksCompleted, paths.length);
  }

  return totalInserted;
}

// ─── Summary & Results (via view) ─────────────────────────────────

export async function getSummary(sessionId: string): Promise<FidcSummary> {
  const sb = requireSupabase();

  const { data, error } = await sb.rpc("fidc_get_summary", {
    p_session_id: sessionId,
  });

  if (error) throw new Error(`Erro ao obter resumo: ${error.message}`);
  return data as FidcSummary;
}

const VIEW_COLUMNS =
  "id,file_name,row_number," +
  "empresa,tipo,status_conta,situacao,nome_cliente,documento,classe,contrato," +
  "valor_principal,valor_nao_cedido,valor_terceiro,valor_cip," +
  "data_vencimento,data_base,base_origem,is_voltz," +
  "dias_atraso,aging,aging_taxa," +
  "valor_liquido,multa,juros_moratorios,fator_correcao,correcao_monetaria," +
  "valor_corrigido,juros_remuneratorios,saldo_devedor_vencimento," +
  "taxa_recuperacao,prazo_recebimento,valor_recuperavel," +
  "valor_justo";

export async function getResults(
  sessionId: string,
  page: number = 0,
  pageSize: number = 50
): Promise<{ data: SessionDataRow[]; count: number }> {
  const sb = requireSupabase();

  // RPC materializa apenas a página antes dos cálculos → ~6ms vs ~30s da view completa
  const [pageResult, countResult] = await Promise.all([
    sb.rpc("fidc_get_results_page", {
      p_session_id: sessionId,
      p_page: page,
      p_page_size: pageSize,
    }),
    sb
      .from("fidc_session_data")
      .select("*", { count: "exact", head: true })
      .eq("session_id", sessionId),
  ]);

  if (pageResult.error)
    throw new Error(`Erro ao buscar resultados: ${pageResult.error.message}`);
  if (countResult.error)
    throw new Error(`Erro ao contar resultados: ${countResult.error.message}`);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rows: SessionDataRow[] = (pageResult.data as any) ?? [];
  return { data: rows, count: countResult.count ?? 0 };
}

/**
 * Fetch ALL rows for CSV export (no pagination).
 * Usa o RPC em batches para evitar computar 541k rows de uma vez.
 */
export async function getAllResultsForExport(
  sessionId: string
): Promise<SessionDataRow[]> {
  const sb = requireSupabase();
  const BATCH = 2000;
  const all: SessionDataRow[] = [];
  let page = 0;

  while (true) {
    const { data, error } = await sb.rpc("fidc_get_results_page", {
      p_session_id: sessionId,
      p_page: page,
      p_page_size: BATCH,
    });

    if (error)
      throw new Error(`Erro ao exportar resultados: ${error.message}`);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const rows: SessionDataRow[] = (data as any) ?? [];
    all.push(...rows);
    page++;
    if (rows.length < BATCH) break;
  }

  return all;
}

// ─── Raw rows for client-side computation ─────────────────────────

/** Raw columns as inserted by ingest-csv (no computed fields) */
export interface RawDataRow {
  id: number;
  file_name: string;
  row_number: number;
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
}

const RAW_COLUMNS_SELECT =
  "id,file_name,row_number,empresa,tipo,status_conta,situacao," +
  "nome_cliente,documento,classe,contrato," +
  "valor_principal,valor_nao_cedido,valor_terceiro,valor_cip," +
  "data_vencimento,data_base,base_origem,is_voltz";

export async function getRawRowsBatch(
  sessionId: string,
  page: number,
  batchSize: number
): Promise<RawDataRow[]> {
  const sb = requireSupabase();
  const { data, error } = await sb
    .from("fidc_session_data")
    .select(RAW_COLUMNS_SELECT)
    .eq("session_id", sessionId)
    .order("row_number")
    .range(page * batchSize, (page + 1) * batchSize - 1);
  if (error) throw new Error(`Erro ao buscar dados brutos: ${error.message}`);
  return (data ?? []) as RawDataRow[];
}

// ─── Full Pipeline Orchestrator ───────────────────────────────────

/**
 * Pipeline simplificado — sem ingest no Supabase.
 *
 * Apenas:
 *   1. Cria sessão com paths dos arquivos no metadata (worker lê daqui)
 *   2. Faz upload das tabelas de referência (índices, taxas, DI-PRE)
 *   3. Marca sessão como "completed" (worker fica responsável pelo cálculo)
 *
 * O worker Railway lê os CSVs do Storage diretamente usando os paths
 * armazenados em fidc_sessions.metadata.files[].
 */
export async function runFullDbPipeline(
  files: UploadedFile[],
  fieldMappings: Record<string, FieldMapping>,
  indices: EconomicIndex[],
  recoveryRates: RecoveryRate[],
  diPreRates: DIPRERate[],
  dataBase: string,
  onProgress: ProcessingDbCallback,
  spreadPercent: number = 0.025,
  prazoHorizonte: number = 6
): Promise<string> {
  // ── Monta lista de arquivos para o worker ─────────────────────────
  const validFiles = files.filter(
    (f) =>
      f.validationStatus === "valid" &&
      (f.chunkPaths?.length || f.csvPath || f.storagePath)
  );

  const sessionFiles: SessionFileMeta[] = validFiles
    .map((f) => ({
      name:          f.name,
      is_voltz:      f.isVoltz,
      field_mapping: fieldMappings[f.id] ?? {},
      paths:         f.chunkPaths?.length
        ? f.chunkPaths
        : [f.csvPath ?? f.storagePath ?? ""].filter(Boolean),
    }))
    .filter((f) => f.paths.length > 0);

  // ── Step 0: Cria sessão com file info no metadata ─────────────────
  onProgress({
    step: "setup",
    progress: 5,
    message: "Criando sessão e registrando arquivos...",
  });
  const sessionId = await createSession(dataBase, spreadPercent, prazoHorizonte, sessionFiles);

  onProgress({
    step: "setup",
    progress: 10,
    message: "Sessão criada.",
    sessionId,
    details: `${sessionFiles.length} arquivo(s) registrado(s) para processamento`,
  });

  // ── Step 1: Upload das tabelas de referência ──────────────────────
  onProgress({
    step: "setup",
    progress: 30,
    message: "Enviando índices e taxas de referência...",
    details: `${indices.length} índices  •  ${recoveryRates.length} taxas recuperação  •  ${diPreRates.length} pontos DI-PRE`,
  });
  await uploadReferenceData(sessionId, indices, recoveryRates, diPreRates);

  // ── Marca sessão como pronta ──────────────────────────────────────
  const sb = requireSupabase();
  await sb
    .from("fidc_sessions")
    .update({ status: "completed", updated_at: new Date().toISOString() })
    .eq("id", sessionId);

  onProgress({
    step: "complete",
    progress: 100,
    message: "Preparação concluída! Worker Railway iniciando cálculo...",
    details: `${validFiles.reduce((a, f) => a + f.rowCount, 0).toLocaleString("pt-BR")} registros estimados`,
  });

  return sessionId;
}
