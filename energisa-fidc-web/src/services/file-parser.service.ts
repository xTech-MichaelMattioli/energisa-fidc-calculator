/**
 * Service: Excel File Parser
 * Handles reading and parsing uploaded Excel files using SheetJS.
 */
import * as XLSX from "xlsx";
import type { RawRecord, UploadedFile } from "@/types";

export async function parseExcelFile(file: File): Promise<UploadedFile> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: "array", cellDates: true });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData: RawRecord[] = XLSX.utils.sheet_to_json(worksheet, {
          raw: false,
          defval: "",
        });

        const columns =
          jsonData.length > 0 ? Object.keys(jsonData[0]) : [];
        const isVoltz =
          file.name.toLowerCase().includes("voltz") ||
          file.name.toLowerCase().includes("volt");

        // Try to detect date from filename or first row
        let detectedDate: string | undefined;
        const dateMatch = file.name.match(/(\d{4})(\d{2})(\d{2})/);
        if (dateMatch) {
          detectedDate = `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]}`;
        }

        resolve({
          id: crypto.randomUUID(),
          name: file.name,
          data: jsonData,
          columns,
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
