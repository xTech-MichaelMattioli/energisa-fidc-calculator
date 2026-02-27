/**
 * Service: Validation Processor
 *
 * After files are uploaded to `para_validacao/<session>/`, this service
 * orchestrates the server-side pipeline per file:
 *
 *  1. Call `read-columns` edge function (validates header + extracts columns)
 *  2. If INVALID  → delete file from Storage, return rejection reason
 *  3. If VALID    → move file to `validados/`, call `excel-to-csv` to produce
 *                   a CSV that can later be inserted into a temp Supabase table
 *
 * Each step emits progress via a callback so the UI can update badges/bars.
 */
import {
  callReadColumns,
  type ReadColumnsResult,
} from "./edge-functions.service";
import {
  deleteFileFromStorage,
  moveToValidados,
} from "./storage.service";

// ─── Types ────────────────────────────────────────────────────────

export type ValidationOutcome =
  | {
      status: "valid";
      columns: string[];
      columnInfo: ReadColumnsResult["columnInfo"];
      rowCount: number;
      sheetName?: string;
      isVoltz: boolean;
      validadosPath: string;          // new path after move
    }
  | {
      status: "invalid";
      error: string;
    }
  | {
      status: "error";
      error: string;
    };

export type ValidationStepCallback = (step: string, detail?: string) => void;

// ─── Main pipeline ────────────────────────────────────────────────

/**
 * Validate a single file that's already in Storage.
 *
 * @param storagePath  e.g. "para_validacao/<session>/file.xlsx"
 * @param fileName     original file name (for logging / edge function)
 * @param onStep       optional callback to track progress
 */
export async function validateFile(
  storagePath: string,
  fileName: string,
  onStep?: ValidationStepCallback,
): Promise<ValidationOutcome> {
  // ── Step 1: Edge function validates + extracts columns ──────────
  onStep?.("validating", "Validando cabeçalho e colunas…");

  let result: ReadColumnsResult;
  try {
    result = await callReadColumns(storagePath, fileName);
  } catch (err) {
    // Network error → we can't validate, but don't delete the file
    return { status: "error", error: String(err) };
  }

  // ── Step 2: Check result ────────────────────────────────────────
  if (!result.valid) {
    onStep?.("rejected", result.error ?? "Cabeçalho inválido");

    // Delete the rejected file from storage (best-effort)
    try {
      await deleteFileFromStorage(storagePath);
    } catch { /* ignore */ }

    return {
      status: "invalid",
      error:
        result.error ??
        "Cabeçalho inválido — a primeira linha não contém nomes de colunas reconhecidos.",
    };
  }

  // ── Step 3: Move to validados ───────────────────────────────────
  onStep?.("moving", "Movendo para pasta de validados…");

  let validadosPath: string;
  try {
    validadosPath = await moveToValidados(storagePath);
  } catch (err) {
    // Move failed — file stays in para_validacao, still usable
    console.warn("[validateFile] moveToValidados failed, keeping original:", err);
    validadosPath = storagePath;
  }

  onStep?.("done", "Validação concluída");

  return {
    status: "valid",
    columns: result.columns ?? [],
    columnInfo: result.columnInfo,
    rowCount: result.rowCount ?? 0,
    sheetName: result.sheetName,
    isVoltz: result.isVoltz ?? false,
    validadosPath,
  };
}

/**
 * Validate all files in batch.
 * Returns an array of outcomes in the same order as the input paths.
 */
export async function validateFiles(
  files: Array<{ storagePath: string; fileName: string }>,
  onFileStep?: (fileIndex: number, step: string, detail?: string) => void,
): Promise<ValidationOutcome[]> {
  // Process sequentially to avoid overwhelming the edge function
  const outcomes: ValidationOutcome[] = [];
  for (let i = 0; i < files.length; i++) {
    const { storagePath, fileName } = files[i];
    const outcome = await validateFile(storagePath, fileName, (step, detail) => {
      onFileStep?.(i, step, detail);
    });
    outcomes.push(outcome);
  }
  return outcomes;
}
