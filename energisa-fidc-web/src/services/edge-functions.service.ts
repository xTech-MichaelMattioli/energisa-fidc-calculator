/**
 * Service: Edge Function Client
 * Wraps calls to Supabase Edge Functions.
 *
 * Primary function:
 *   read-columns  →  download + validate header + extract column metadata (single shot)
 *
 * Legacy functions kept for reference:
 *   validate-excel, extract-columns (now superseded by read-columns)
 */
import { supabase, isSupabaseConfigured } from "@/lib/supabase";

// ─── Response Types ───────────────────────────────────────────────

export type DetectedColumnType = "string" | "number" | "date" | "empty" | "mixed";

export interface ColumnInfo {
  name: string;
  index: number;
  detectedType: DetectedColumnType;
  sampleValues: string[];
  nonEmptyCount: number;
  uniqueCount: number;
}

/**
 * Unified result from the `read-columns` edge function.
 * Covers both header validation and column extraction in one call.
 */
export interface ReadColumnsResult {
  valid: boolean;
  error?: string;
  // populated when valid = true
  columns?: string[];
  columnInfo?: ColumnInfo[];
  rowCount?: number;
  sheetName?: string;
  isVoltz?: boolean;
  sampleData?: Record<string, unknown>[];
}

// ── Legacy types kept for backward compatibility ──────────────────
export interface ValidateExcelResult {
  valid: boolean;
  columns: string[];
  rowCount: number;
  sheetName: string;
  sampleData: Record<string, unknown>[];
  isVoltz: boolean;
  error?: string;
}

export interface ExtractColumnsResult {
  success: boolean;
  columns: ColumnInfo[];
  totalRows: number;
  sheetName: string;
  isVoltz: boolean;
  error?: string;
}

// ─── Primary Function ─────────────────────────────────────────────

/**
 * Call the `read-columns` Edge Function.
 *
 * Single HTTP round-trip:
 *   download file → validate header → extract column metadata → return all
 *
 * On error the returned object has `valid: false` and an `error` message
 * instead of throwing, so callers can inspect the reason.
 */
export async function callReadColumns(
  storagePath: string,
  fileName: string
): Promise<ReadColumnsResult> {
  if (!isSupabaseConfigured() || !supabase) {
    return { valid: false, error: "Supabase não configurado" };
  }

  // invoke() resolves even for non-2xx — error is set by the JS client only
  // for network/fetch failures, not for application-level errors returned by
  // the function. So we read data regardless.
  const { data, error } = await supabase.functions.invoke("read-columns", {
    body: { storagePath, fileName },
  });

  if (error) {
    // Network or invocation-level failure
    return { valid: false, error: `Falha ao chamar edge function: ${error.message}` };
  }

  // data is the JSON body returned by the function (could be valid:false)
  return (data ?? { valid: false, error: "Resposta vazia da edge function" }) as ReadColumnsResult;
}

// ─── Legacy Functions (kept for backward compatibility) ───────────

/** @deprecated Use callReadColumns instead */
export async function callValidateExcel(
  storagePath: string,
  fileName: string
): Promise<ValidateExcelResult> {
  const r = await callReadColumns(storagePath, fileName);
  return {
    valid: r.valid,
    columns: r.columns ?? [],
    rowCount: r.rowCount ?? 0,
    sheetName: r.sheetName ?? "",
    sampleData: r.sampleData ?? [],
    isVoltz: r.isVoltz ?? false,
    error: r.error,
  };
}

/** @deprecated Use callReadColumns instead */
export async function callExtractColumns(
  storagePath: string,
  fileName: string
): Promise<ExtractColumnsResult> {
  const r = await callReadColumns(storagePath, fileName);
  return {
    success: r.valid,
    columns: r.columnInfo ?? [],
    totalRows: r.rowCount ?? 0,
    sheetName: r.sheetName ?? "",
    isVoltz: r.isVoltz ?? false,
    error: r.error,
  };
}

/** @deprecated Use callReadColumns instead */
export async function validateAndExtractColumns(
  storagePath: string,
  fileName: string
): Promise<{
  validation: ValidateExcelResult;
  extraction: ExtractColumnsResult | null;
}> {
  const r = await callReadColumns(storagePath, fileName);
  const validation: ValidateExcelResult = {
    valid: r.valid,
    columns: r.columns ?? [],
    rowCount: r.rowCount ?? 0,
    sheetName: r.sheetName ?? "",
    sampleData: r.sampleData ?? [],
    isVoltz: r.isVoltz ?? false,
    error: r.error,
  };
  if (!r.valid) return { validation, extraction: null };
  return {
    validation,
    extraction: {
      success: true,
      columns: r.columnInfo ?? [],
      totalRows: r.rowCount ?? 0,
      sheetName: r.sheetName ?? "",
      isVoltz: r.isVoltz ?? false,
    },
  };
}

