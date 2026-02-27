/**
 * Service: Excel Worker
 *
 * Wraps the excel-parser.worker Web Worker so callers get a clean
 * Promise-based API.  A single shared worker instance is reused for
 * all requests (multiplexed by a random `id`).
 *
 * Two modes:
 *   parseExcelFileAsync(file)    → legacy full parse (data[] in memory)
 *   convertExcelToCsvAsync(file) → Excel → CSV + metadata (no data[] in memory)
 */
import type { UploadedFile } from "@/types";
import type { ParsedResult, ConvertResult } from "@/workers/excel-parser.worker";

// Vite resolves `?worker` to a Worker constructor automatically
import ExcelParserWorker from "@/workers/excel-parser.worker?worker";

type PendingEntry = {
  resolve: (r: unknown) => void;
  reject: (e: Error) => void;
  mode: "parse" | "convert";
};

let _worker: Worker | null = null;
const pending = new Map<string, PendingEntry>();

function getWorker(): Worker {
  if (_worker) return _worker;

  _worker = new ExcelParserWorker();

  _worker.onmessage = (
    e: MessageEvent<
      | { id: string; result: ParsedResult }
      | { id: string; convert: ConvertResult }
      | { id: string; error: string }
    >
  ) => {
    const { id } = e.data;
    const entry = pending.get(id);
    if (!entry) return;
    pending.delete(id);

    if ("error" in e.data) {
      entry.reject(new Error(e.data.error));
      return;
    }

    if (entry.mode === "convert" && "convert" in e.data) {
      entry.resolve(e.data.convert);
    } else if ("result" in e.data) {
      const r = e.data.result;
      entry.resolve({
        id: r.id,
        name: r.name,
        data: r.data,
        columns: r.columns,
        rowCount: r.rowCount,
        detectedDate: r.detectedDate,
        isVoltz: r.isVoltz,
        size: r.size,
      } as UploadedFile);
    }
  };

  _worker.onerror = (e) => {
    const err = new Error(e.message ?? "Excel worker crashed");
    for (const entry of pending.values()) entry.reject(err);
    pending.clear();
    _worker = null; // allow recreation on next call
  };

  return _worker;
}

/**
 * Parse an Excel file using a background Web Worker (legacy mode).
 * Returns the full data[] in memory — use for small files or backward compat.
 */
export function parseExcelFileAsync(file: File): Promise<UploadedFile> {
  return new Promise((resolve, reject) => {
    const id = crypto.randomUUID();
    const reader = new FileReader();

    reader.onload = (evt) => {
      const buffer = evt.target?.result as ArrayBuffer;
      pending.set(id, { resolve: resolve as (r: unknown) => void, reject, mode: "parse" });
      getWorker().postMessage({ type: "parse", id, buffer, name: file.name, size: file.size }, [buffer]);
    };

    reader.onerror = () =>
      reject(new Error(`Erro ao ler o arquivo: ${file.name}`));

    reader.readAsArrayBuffer(file);
  });
}

/**
 * Convert an Excel file to CSV + extract column metadata in a background Worker.
 *
 * Returns a ConvertResult with:
 *  - csvBuffer: ArrayBuffer with UTF-8 CSV (zero-copy transferred)
 *  - columns, columnInfo, rowCount, sheetName, isVoltz, etc.
 *  - valid: boolean (header validation done inside the Worker)
 *
 * This never sends the entire data[] over — only the CSV bytes + metadata.
 */
export function convertExcelToCsvAsync(file: File): Promise<ConvertResult> {
  return new Promise((resolve, reject) => {
    const id = crypto.randomUUID();
    const reader = new FileReader();

    reader.onload = (evt) => {
      const buffer = evt.target?.result as ArrayBuffer;
      pending.set(id, { resolve: resolve as (r: unknown) => void, reject, mode: "convert" });
      getWorker().postMessage(
        { type: "convert", id, buffer, name: file.name, size: file.size },
        [buffer],
      );
    };

    reader.onerror = () =>
      reject(new Error(`Erro ao ler o arquivo: ${file.name}`));

    reader.readAsArrayBuffer(file);
  });
}
