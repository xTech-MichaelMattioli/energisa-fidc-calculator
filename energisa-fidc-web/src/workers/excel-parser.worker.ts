/**
 * Web Worker: Excel Parser & CSV Converter
 *
 * Runs XLSX parsing off the main thread so the UI never freezes,
 * even for very large files. Vite loads this with the `?worker` suffix.
 *
 * Message protocol
 * ─────────────────
 * IN  → { type?: "parse"|"convert"; id; buffer; name; size }
 *
 * OUT (parse — default / legacy)
 *   → { id; result: ParsedResult }
 *   | { id; error: string }
 *
 * OUT (convert — new "Excel → CSV" mode)
 *   → { id; convert: ConvertResult }   (csvBuffer is Transferable)
 *   | { id; error: string }
 */
import * as XLSX from "xlsx";

// ─── Protocol types ───────────────────────────────────────────────

type WorkerInput = {
  type?: "parse" | "convert";
  id: string;
  buffer: ArrayBuffer;
  name: string;
  size: number;
};

/** Legacy parse result (keeps full data[] in memory) */
export type ParsedResult = {
  id: string;
  name: string;
  data: Record<string, string>[];
  columns: string[];
  rowCount: number;
  detectedDate?: string;
  isVoltz: boolean;
  size: number;
};

/** Column metadata — mirrors edge-function ColumnInfo */
export type WorkerColumnInfo = {
  name: string;
  index: number;
  detectedType: "string" | "number" | "date" | "empty" | "mixed";
  sampleValues: string[];
  nonEmptyCount: number;
  uniqueCount: number;
};

/** New convert result: metadata + raw CSV bytes (Transferable) */
export type ConvertResult = {
  valid: boolean;
  error?: string;
  /** Raw CSV encoded as UTF-8 ArrayBuffer — transferred, not copied */
  csvBuffer: ArrayBuffer;
  columns: string[];
  columnInfo: WorkerColumnInfo[];
  rowCount: number;
  sheetName: string;
  isVoltz: boolean;
  detectedDate?: string;
  /** Original Excel size for reference */
  originalSize: number;
  /** CSV byte length */
  csvSize: number;
};

type WorkerOutput =
  | { id: string; result: ParsedResult }
  | { id: string; convert: ConvertResult }
  | { id: string; error: string };

// ── Helpers ───────────────────────────────────────────────────────

function isMetadataColumn(name: string): boolean {
  if (!name || !name.trim()) return true;
  if (name.trim().endsWith(":")) return true;
  if (/^\d{4}-\d{2}-\d{2}(T|\s|$)/.test(name.trim())) return true;
  if (/^\d{2}[/\-.]\d{2}[/\-.]\d{4}$/.test(name.trim())) return true;
  return false;
}

function findHeaderRowIndex(rawRows: unknown[][], limit = 10): number {
  let bestIdx = 0;
  let bestScore = -1;

  for (let i = 0; i < Math.min(rawRows.length, limit); i++) {
    const row = rawRows[i] as unknown[];
    let textCount = 0;
    let nonEmpty = 0;
    for (const cell of row) {
      const s = String(cell ?? "").trim();
      if (!s) continue;
      nonEmpty++;
      if (!isNaN(Number(s)) && s.length < 15) continue;
      if (/^\d{1,4}[/\-.\s]\d{1,2}[/\-.\s]\d{2,4}$/.test(s)) continue;
      textCount++;
    }
    if (nonEmpty === 0) continue;
    const score = nonEmpty + textCount * 2;
    if (score > bestScore) {
      bestScore = score;
      bestIdx = i;
    }
  }
  return bestIdx;
}

function isHeaderRow(row: unknown[]): boolean {
  if (!row || row.length === 0) return false;
  let textCount = 0;
  let nonEmpty = 0;
  for (const cell of row) {
    const s = String(cell ?? "").trim();
    if (!s) continue;
    nonEmpty++;
    if (!isNaN(Number(s)) && s.length < 15) continue;
    if (/^\d{1,4}[/\-.\s]\d{1,2}[/\-.\s]\d{2,4}$/.test(s)) continue;
    textCount++;
  }
  return nonEmpty > 0 && textCount / nonEmpty >= 0.6;
}

function detectColumnType(
  values: unknown[],
): "string" | "number" | "date" | "empty" | "mixed" {
  let numCount = 0,
    dateCount = 0,
    strCount = 0,
    total = 0;
  for (const v of values) {
    const s = String(v ?? "").trim();
    if (!s) continue;
    total++;
    if (
      /^\d{1,4}[/\-.\s]\d{1,2}[/\-.\s]\d{2,4}$/.test(s) ||
      /^\d{2}\/\d{2}\/\d{4}$/.test(s)
    ) {
      dateCount++;
      continue;
    }
    const cleaned = s.replace(/\./g, "").replace(",", ".");
    if (!isNaN(Number(cleaned)) && cleaned !== "") {
      numCount++;
      continue;
    }
    strCount++;
  }
  if (total === 0) return "empty";
  const th = total * 0.7;
  if (numCount >= th) return "number";
  if (dateCount >= th) return "date";
  if (strCount >= th) return "string";
  return "mixed";
}

function detectDate(name: string): string | undefined {
  const m1 = name.match(/(\d{4})(\d{2})(\d{2})/);
  const m2 = name.match(/(\d{2})\.(\d{2})(?:\.(\d{4}))?/);
  if (m1) return `${m1[1]}-${m1[2]}-${m1[3]}`;
  if (m2) {
    const year = m2[3] ?? new Date().getFullYear().toString();
    return `${year}-${m2[2]}-${m2[1]}`;
  }
  return undefined;
}

// ── Core: parse workbook + find header ────────────────────────────

/**
 * Load a workbook and detect the header row.
 * Only reads the first HEADER_SCAN_ROWS rows from the sheet to minimise
 * memory usage — critical for files with hundreds of thousands of rows.
 */
const HEADER_SCAN_ROWS = 15;

function parseWorkbook(buffer: ArrayBuffer) {
  const uint8 = new Uint8Array(buffer);
  const workbook = XLSX.read(uint8, {
    type: "array",
    cellDates: false,
    raw: false,
  });
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];

  // Build a limited range covering only the first HEADER_SCAN_ROWS rows.
  // This avoids allocating a JS array for every row in the sheet just to
  // find the header — a 1 M-row file would create ~1 M arrays otherwise.
  const fullRef = worksheet["!ref"];
  const scanRange = fullRef
    ? (() => {
        const r = XLSX.utils.decode_range(fullRef);
        return {
          s: r.s,
          e: { r: Math.min(r.e.r, HEADER_SCAN_ROWS - 1), c: r.e.c },
        };
      })()
    : undefined;

  const rawRows = XLSX.utils.sheet_to_json(worksheet, {
    header: 1,
    raw: false,
    defval: "",
    blankrows: false,
    range: scanRange,
  }) as unknown[][];

  const headerRowIdx = findHeaderRowIndex(rawRows);
  const headerRow = (rawRows[headerRowIdx] ?? []) as unknown[];

  return { workbook, sheetName, worksheet, rawRows, headerRowIdx, headerRow };
}

// ── Mode: "parse" (legacy) ────────────────────────────────────────

function handleParse(id: string, buffer: ArrayBuffer, name: string, size: number) {
  const { sheetName: _sn, worksheet, rawRows, headerRowIdx, headerRow } =
    parseWorkbook(buffer);

  if (rawRows.length === 0) {
    const out: WorkerOutput = {
      id,
      result: { id, name, data: [], columns: [], rowCount: 0, isVoltz: false, size },
    };
    self.postMessage(out);
    return;
  }

  const columns: string[] = headerRow
    .map((c) => String(c ?? "").trim())
    .filter((c) => c.length > 0 && !isMetadataColumn(c));

  const ref = worksheet["!ref"];
  if (!ref) {
    const out: WorkerOutput = {
      id,
      result: { id, name, data: [], columns, rowCount: 0, isVoltz: false, size },
    };
    self.postMessage(out);
    return;
  }

  const range = XLSX.utils.decode_range(ref);
  range.s.r = headerRowIdx;
  const jsonData = XLSX.utils.sheet_to_json(worksheet, {
    raw: false,
    defval: "",
    range,
  }) as Record<string, string>[];

  const isVoltz =
    name.toLowerCase().includes("voltz") ||
    name.toLowerCase().includes("volt");

  const finalColumns =
    jsonData.length > 0
      ? Object.keys(jsonData[0]).filter((k) => !isMetadataColumn(k))
      : columns;

  const out: WorkerOutput = {
    id,
    result: {
      id,
      name,
      data: jsonData,
      columns: finalColumns,
      rowCount: jsonData.length,
      detectedDate: detectDate(name),
      isVoltz,
      size,
    },
  };
  self.postMessage(out);
}

// ── Mode: "convert" (Excel → CSV + metadata) ─────────────────────

function handleConvert(id: string, buffer: ArrayBuffer, name: string, size: number) {
  const { sheetName, worksheet, rawRows, headerRowIdx, headerRow } =
    parseWorkbook(buffer);

  // ── Validate header ──
  if (rawRows.length < 2 || !isHeaderRow(headerRow)) {
    const out: WorkerOutput = {
      id,
      convert: {
        valid: false,
        error:
          rawRows.length < 2
            ? "Arquivo precisa ter pelo menos 2 linhas (cabeçalho + dados)."
            : "Cabeçalho não reconhecido — a primeira linha não contém nomes de colunas.",
        csvBuffer: new ArrayBuffer(0),
        columns: [],
        columnInfo: [],
        rowCount: 0,
        sheetName,
        isVoltz: false,
        originalSize: size,
        csvSize: 0,
      },
    };
    self.postMessage(out);
    return;
  }

  // ── Columns (filter metadata cells) ──
  const columns: string[] = headerRow
    .map((c) => String(c ?? "").trim())
    .filter((c) => c.length > 0 && !isMetadataColumn(c));

  if (columns.length === 0) {
    const out: WorkerOutput = {
      id,
      convert: {
        valid: false,
        error: "Nenhuma coluna válida encontrada no cabeçalho.",
        csvBuffer: new ArrayBuffer(0),
        columns: [],
        columnInfo: [],
        rowCount: 0,
        sheetName,
        isVoltz: false,
        originalSize: size,
        csvSize: 0,
      },
    };
    self.postMessage(out);
    return;
  }

  // ── Parse keyed data from header row onward ──
  const ref = worksheet["!ref"];
  if (!ref) {
    const out: WorkerOutput = {
      id,
      convert: {
        valid: false,
        error: "Worksheet sem dados (ref ausente).",
        csvBuffer: new ArrayBuffer(0),
        columns,
        columnInfo: [],
        rowCount: 0,
        sheetName,
        isVoltz: false,
        originalSize: size,
        csvSize: 0,
      },
    };
    self.postMessage(out);
    return;
  }

  const range = XLSX.utils.decode_range(ref);
  range.s.r = headerRowIdx;

  // Trim sheet to start from headerRowIdx before CSV generation
  worksheet["!ref"] = XLSX.utils.encode_range(range);

  // ── Generate CSV directly from the worksheet (fast, native XLSX) ──
  const csvString = XLSX.utils.sheet_to_csv(worksheet, {
    FS: ",",
    RS: "\n",
    strip: false,
    blankrows: false,
    skipHidden: true,
  });

  const csvBytes = new TextEncoder().encode(csvString);
  const csvBuffer = csvBytes.buffer;

  // ── Row count from worksheet range (header is at range.s.r, data below) ──
  // Avoids loading all rows into JS objects just to count them.
  const rowCount = Math.max(0, range.e.r - range.s.r);

  // ── Keyed data for column metadata — SAMPLE ONLY ──
  // For a 1M-row file, sheet_to_json over all rows would create 1M JS objects.
  // We only need a small sample (150 rows) to infer column types, so we cap
  // the range here.  rowCount is already derived from the worksheet ref above.
  const SAMPLE_SIZE = 150;
  const sampleRange = {
    s: range.s,
    e: { r: Math.min(range.e.r, range.s.r + SAMPLE_SIZE), c: range.e.c },
  };
  const sampleRows = XLSX.utils.sheet_to_json(worksheet, {
    raw: false,
    defval: "",
    range: sampleRange,
  }) as Record<string, unknown>[];

  // Refine columns from sample data
  const finalColumns =
    sampleRows.length > 0
      ? Object.keys(sampleRows[0]).filter((k) => !isMetadataColumn(k))
      : columns;

  // ── Column metadata ──
  const columnInfo: WorkerColumnInfo[] = finalColumns.map((colName, index) => {
    const vals = sampleRows.map((r) => r[colName]);
    const nonEmpty = vals.filter((v) => String(v ?? "").trim() !== "");
    const unique = new Set(nonEmpty.map((v) => String(v).trim()));
    return {
      name: colName,
      index,
      detectedType: detectColumnType(vals),
      sampleValues: [...unique].slice(0, 5).map(String),
      nonEmptyCount: nonEmpty.length,
      uniqueCount: unique.size,
    };
  });

  const isVoltz =
    name.toLowerCase().includes("voltz") ||
    name.toLowerCase().includes("volt");

  const out: WorkerOutput = {
    id,
    convert: {
      valid: true,
      csvBuffer,
      columns: finalColumns,
      columnInfo,
      rowCount,
      sheetName,
      isVoltz,
      detectedDate: detectDate(name),
      originalSize: size,
      csvSize: csvBytes.byteLength,
    },
  };

  // Transfer csvBuffer (zero-copy)
  (self as unknown as Worker).postMessage(out, [csvBuffer]);
}

// ── Worker message handler ────────────────────────────────────────

self.onmessage = (e: MessageEvent<WorkerInput>) => {
  const { type = "parse", id, buffer, name, size } = e.data;

  try {
    if (type === "convert") {
      handleConvert(id, buffer, name, size);
    } else {
      handleParse(id, buffer, name, size);
    }
  } catch (err) {
    const out: WorkerOutput = { id, error: String(err) };
    self.postMessage(out);
  }
};
