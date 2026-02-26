/**
 * Service: Edge Function Client
 * Wraps calls to Supabase Edge Functions (validate-excel, extract-columns).
 */
import { supabase, isSupabaseConfigured } from "@/lib/supabase";

// ─── Response Types ───────────────────────────────────────────────

export interface ValidateExcelResult {
  valid: boolean;
  columns: string[];
  rowCount: number;
  sheetName: string;
  sampleData: Record<string, unknown>[];
  isVoltz: boolean;
  error?: string;
}

export type DetectedColumnType = "string" | "number" | "date" | "empty" | "mixed";

export interface ColumnInfo {
  name: string;
  index: number;
  detectedType: DetectedColumnType;
  sampleValues: string[];
  nonEmptyCount: number;
  uniqueCount: number;
}

export interface ExtractColumnsResult {
  success: boolean;
  columns: ColumnInfo[];
  totalRows: number;
  sheetName: string;
  isVoltz: boolean;
  error?: string;
}

// ─── Edge Function Calls ──────────────────────────────────────────

/**
 * Call the `validate-excel` Edge Function.
 * Validates that the first row of the uploaded Excel is a proper header.
 * Returns column names, row count, sample data, and VOLTZ detection.
 */
export async function callValidateExcel(
  storagePath: string,
  fileName: string
): Promise<ValidateExcelResult> {
  if (!isSupabaseConfigured() || !supabase) {
    throw new Error("Supabase não configurado");
  }

  const { data, error } = await supabase.functions.invoke("validate-excel", {
    body: { storagePath, fileName },
  });

  if (error) {
    throw new Error(`Erro na validação: ${error.message}`);
  }

  return data as ValidateExcelResult;
}

/**
 * Call the `extract-columns` Edge Function.
 * Performs deeper column analysis: type detection, sample values, stats.
 * This feeds into the field-mapper service for smarter auto-mapping.
 */
export async function callExtractColumns(
  storagePath: string,
  fileName: string
): Promise<ExtractColumnsResult> {
  if (!isSupabaseConfigured() || !supabase) {
    throw new Error("Supabase não configurado");
  }

  const { data, error } = await supabase.functions.invoke("extract-columns", {
    body: { storagePath, fileName },
  });

  if (error) {
    throw new Error(`Erro na extração de colunas: ${error.message}`);
  }

  return data as ExtractColumnsResult;
}

/**
 * Full validation + extraction pipeline.
 * 1. Upload completed → validate header
 * 2. If valid → extract detailed column info
 * Returns both results.
 */
export async function validateAndExtractColumns(
  storagePath: string,
  fileName: string
): Promise<{
  validation: ValidateExcelResult;
  extraction: ExtractColumnsResult | null;
}> {
  // Step 1: Validate
  const validation = await callValidateExcel(storagePath, fileName);

  if (!validation.valid) {
    return { validation, extraction: null };
  }

  // Step 2: Extract detailed column info
  const extraction = await callExtractColumns(storagePath, fileName);

  return { validation, extraction };
}
