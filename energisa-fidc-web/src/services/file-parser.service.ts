/**
 * Service: Excel File Parser
 * Handles reading and parsing uploaded Excel files using SheetJS.
 */
import * as XLSX from "xlsx";
import type { RawRecord, UploadedFile } from "@/types";

/**
 * Return true for cells that appear to be inline metadata rather than
 * real column names.
 *
 * Observed pattern in EMS LIQ files: the header row contains the real 27
 * column labels AND two trailing cells — "Data base:" (a label ending with
 * ':') and the reference date value (ISO date string).  Both should be
 * excluded from the column list that we display and pass downstream.
 */
function isMetadataColumn(name: string): boolean {
  if (!name || !name.trim()) return true;
  // Labels that are just metadata keys, e.g. "Data base:"
  if (name.trim().endsWith(":")) return true;
  // Cells whose value IS a date string (ISO format or "DD/MM/YYYY")
  if (/^\d{4}-\d{2}-\d{2}(T|\s|$)/.test(name.trim())) return true;
  if (/^\d{2}[/\-.]\d{2}[/\-.]\d{4}$/.test(name.trim())) return true;
  return false;
}

/**
 * Scan the first `limit` rows and return the index of the row that looks
 * most like a header: most non-empty cells that are text (not numbers /
 * pure dates). Falls back to 0 if nothing is found.
 */
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
      // skip pure numbers and date-like strings
      if (!isNaN(Number(s)) && s.length < 15) continue;
      if (/^\d{1,4}[\/\-.\s]\d{1,2}[\/\-.\s]\d{2,4}$/.test(s)) continue;
      textCount++;
    }
    if (nonEmpty === 0) continue;
    const score = nonEmpty + textCount * 2; // favour rows dense with text labels
    if (score > bestScore) {
      bestScore = score;
      bestIdx = i;
    }
  }
  return bestIdx;
}

export async function parseExcelFile(file: File): Promise<UploadedFile> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: "array", cellDates: false, raw: false });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];

        // --- Step 1: get raw rows to find the real header row ---
        const rawRows = XLSX.utils.sheet_to_json(worksheet, {
          header: 1,
          raw: false,
          defval: "",
          blankrows: false,
        }) as unknown[][];

        if (rawRows.length === 0) {
          return resolve({
            id: crypto.randomUUID(),
            name: file.name,
            data: [],
            columns: [],
            rowCount: 0,
            isVoltz: false,
          });
        }

        const headerRowIdx = findHeaderRowIndex(rawRows);
        const headerRow = rawRows[headerRowIdx] as unknown[];

        // Build column names from that row — strip inline metadata cells
        // (e.g. "Data base:" label + date value that EMS LIQ files embed in
        //  the header row alongside the real column names).
        const columns: string[] = headerRow
          .map((c) => String(c ?? "").trim())
          .filter((c) => c.length > 0 && !isMetadataColumn(c));

        // --- Step 2: parse keyed JSON using the correct header row ---
        // sheet_to_json with range starting at headerRowIdx uses that row as keys
        const ref = worksheet["!ref"];
        if (!ref) {
          return resolve({
            id: crypto.randomUUID(),
            name: file.name,
            data: [],
            columns,
            rowCount: 0,
            isVoltz: false,
          });
        }

        // restrict parse range to start from headerRowIdx (0-based → 1-based for XLSX range)
        const range = XLSX.utils.decode_range(ref);
        range.s.r = headerRowIdx; // start from the header row
        const jsonData: RawRecord[] = XLSX.utils.sheet_to_json(worksheet, {
          raw: false,
          defval: "",
          range,
        });

        const isVoltz =
          file.name.toLowerCase().includes("voltz") ||
          file.name.toLowerCase().includes("volt");

        // Detect date from filename (YYYYMMDD or DD.MM pattern)
        let detectedDate: string | undefined;
        const m1 = file.name.match(/(\d{4})(\d{2})(\d{2})/);
        const m2 = file.name.match(/(\d{2})\.(\d{2})(?:\.(\d{4}))?/);
        if (m1) {
          detectedDate = `${m1[1]}-${m1[2]}-${m1[3]}`;
        } else if (m2) {
          const year = m2[3] ?? new Date().getFullYear().toString();
          detectedDate = `${year}-${m2[2]}-${m2[1]}`;
        }

        console.info(
          `[parseExcelFile] ${file.name}: headerRow=${headerRowIdx}, cols=${columns.length}, rows=${jsonData.length}`
        );

        resolve({
          id: crypto.randomUUID(),
          name: file.name,
          data: jsonData,
          // Prefer keys from first data row; strip residual metadata columns
          columns:
            jsonData.length > 0
              ? Object.keys(jsonData[0]).filter((k) => !isMetadataColumn(k))
              : columns,
          rowCount: jsonData.length,
          detectedDate,
          isVoltz,
        });
      } catch (err) {
        reject(new Error(`Erro ao processar ${file.name}: ${err}`));
      }
    };

    reader.onerror = () => reject(new Error(`Erro ao ler ${file.name}`));
    reader.readAsArrayBuffer(file);
  });
}

/**
 * Parse IGP-M/IPCA indices from Excel.
 * Expected: Column C=Year, D=Month, F=Index value
 */
export async function parseIndicesExcel(
  file: File
): Promise<Array<{ date: string; value: number }>> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const wb = XLSX.read(data, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const rows: unknown[][] = XLSX.utils.sheet_to_json(ws, { header: 1 });

        const indices: Array<{ date: string; value: number }> = [];
        for (const row of rows) {
          const year = Number(row[2]);
          const month = Number(row[3]);
          const value = Number(row[5]);
          if (year && month && !isNaN(value)) {
            const m = String(month).padStart(2, "0");
            indices.push({ date: `${year}-${m}-01`, value });
          }
        }
        resolve(indices);
      } catch (err) {
        reject(new Error(`Erro ao processar índices: ${err}`));
      }
    };
    reader.onerror = () => reject(new Error("Erro ao ler arquivo de índices"));
    reader.readAsArrayBuffer(file);
  });
}

/**
 * Parse recovery rates from Excel "Input" sheet.
 */
export async function parseRecoveryRatesExcel(
  file: File
): Promise<
  Array<{
    empresa: string;
    tipo: string;
    aging: string;
    taxa_recuperacao: number;
    prazo_recebimento: number;
  }>
> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const wb = XLSX.read(data, { type: "array" });
        const sheetName =
          wb.SheetNames.find((s) => s.toLowerCase() === "input") ??
          wb.SheetNames[0];
        const ws = wb.Sheets[sheetName];
        const rows: unknown[][] = XLSX.utils.sheet_to_json(ws, { header: 1 });

        const rates: Array<{
          empresa: string;
          tipo: string;
          aging: string;
          taxa_recuperacao: number;
          prazo_recebimento: number;
        }> = [];

        let currentEmpresa = "";
        const tipos = ["Privado", "Público", "Hospital"];
        const blockOffsets = [1, 5, 9]; // Column offsets per tipo block (aging, taxa, prazo)
        const agings = [
          "A vencer",
          "Primeiro ano",
          "Segundo ano",
          "Terceiro ano",
          "Quarto ano",
          "Quinto ano",
          "Demais anos",
        ];

        for (const row of rows) {
          // Row with "x" marker in any column = company header
          let foundEmpresa = false;
          for (let j = 0; j < (row as unknown[]).length - 1; j++) {
            if (String((row as unknown[])[j]).trim().toLowerCase() === "x") {
              currentEmpresa = String((row as unknown[])[j + 1]).trim();
              foundEmpresa = true;
              break;
            }
          }
          if (foundEmpresa || !currentEmpresa) continue;

          // Each block: [aging, taxa, prazo] at offsets [1,5,9]
          for (let t = 0; t < tipos.length; t++) {
            const offset = blockOffsets[t];
            try {
              const aging = String(row[offset] || "").trim();
              const taxa = Number(String(row[offset + 1] || "0").replace(",", ".")) || 0;
              const prazo = Number(row[offset + 2]) || 6;

              if (agings.includes(aging) && taxa > 0) {
                rates.push({
                  empresa: currentEmpresa,
                  tipo: tipos[t],
                  aging,
                  taxa_recuperacao: taxa,
                  prazo_recebimento: prazo,
                });
              }
            } catch {
              // skip invalid block
            }
          }
        }

        resolve(rates);
      } catch (err) {
        reject(new Error(`Erro ao processar taxas: ${err}`));
      }
    };
    reader.onerror = () =>
      reject(new Error("Erro ao ler arquivo de taxas de recuperação"));
    reader.readAsArrayBuffer(file);
  });
}

/**
 * Parse DI-PRE rates from BMF HTML/Excel file.
 */
export async function parseDIPreFile(
  file: File
): Promise<
  Array<{
    dias_corridos: number;
    taxa_252: number;
    taxa_360: number;
    meses_futuros: number;
  }>
> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const wb = XLSX.read(data, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const rows: unknown[][] = XLSX.utils.sheet_to_json(ws, { header: 1 });

        const allRates: Array<{
          dias_corridos: number;
          taxa_252: number;
          taxa_360: number;
          meses_futuros_raw: number;
        }> = [];

        for (let i = 1; i < rows.length; i++) {
          const row = rows[i];
          const dias = Number(row[0]);
          const t252 = Number(String(row[1]).replace(",", ".")) || 0;
          const t360 = Number(String(row[2]).replace(",", ".")) || 0;
          if (dias > 0) {
            allRates.push({
              dias_corridos: dias,
              taxa_252: t252,
              taxa_360: t360,
              meses_futuros_raw: dias / 30.44,
            });
          }
        }

        // Filter: keep only the closest row per integer month (match Python logic)
        const rates: Array<{
          dias_corridos: number;
          taxa_252: number;
          taxa_360: number;
          meses_futuros: number;
        }> = [];

        if (allRates.length > 0) {
          const maxMonth = Math.ceil(
            allRates[allRates.length - 1].meses_futuros_raw
          );
          const seenIndices = new Set<number>();
          for (let m = 1; m <= maxMonth + 1; m++) {
            let bestIdx = -1;
            let bestDiff = Infinity;
            for (let j = 0; j < allRates.length; j++) {
              const diff = Math.abs(allRates[j].meses_futuros_raw - m);
              if (diff < bestDiff) {
                bestDiff = diff;
                bestIdx = j;
              }
            }
            if (bestIdx >= 0 && !seenIndices.has(bestIdx)) {
              seenIndices.add(bestIdx);
              rates.push({
                dias_corridos: allRates[bestIdx].dias_corridos,
                taxa_252: allRates[bestIdx].taxa_252,
                taxa_360: allRates[bestIdx].taxa_360,
                meses_futuros: m,
              });
            }
          }
        }

        resolve(rates);
      } catch (err) {
        reject(new Error(`Erro ao processar DI-PRE: ${err}`));
      }
    };
    reader.onerror = () =>
      reject(new Error("Erro ao ler arquivo DI-PRE"));
    reader.readAsArrayBuffer(file);
  });
}

/**
 * Export data to CSV with Brazilian formatting.
 */
export function exportToCSV(
  data: Record<string, unknown>[],
  filename: string
): void {
  if (data.length === 0) return;

  const headers = Object.keys(data[0]);
  const csvRows = [headers.join(";")];

  for (const row of data) {
    const values = headers.map((h) => {
      const val = row[h];
      if (typeof val === "number") {
        return val.toFixed(6).replace(".", ",");
      }
      return String(val ?? "");
    });
    csvRows.push(values.join(";"));
  }

  const bom = "\uFEFF";
  const blob = new Blob([bom + csvRows.join("\n")], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
