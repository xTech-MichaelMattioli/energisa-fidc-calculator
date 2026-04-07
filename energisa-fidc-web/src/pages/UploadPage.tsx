/**
 * Page 1: Upload (Carregamento)
 *
 * NEW flow — "convert locally, upload CSV, no edge function":
 *
 *  1. User drops Excel files.
 *  2. Web Worker converts each Excel → CSV + extracts column metadata.
 *     Validation happens inside the Worker (header detection).
 *  3. Valid CSVs are uploaded to Storage (`para_validacao/<session>/file.csv`).
 *  4. Invalid files are rejected immediately with a reason.
 *  5. No edge function needed — zero 422 errors on large files.
 *  6. User clicks "Próximo" to proceed to Mapping.
 */
import { useCallback, useState, useEffect } from "react";
import { useApp } from "@/context/AppContext";
import { convertExcelToCsvAsync } from "@/services/excel-worker.service";
import {
  uploadCsvBlob,
  uploadBlobToPath,
  uploadFileForValidation,
  listSessionStageFiles,
  deleteFileFromStorage,
  deleteRunFolder,
  getCurrentSessionId,
} from "@/services/storage.service";
import { callReadColumnsWithCsv } from "@/services/edge-functions.service";
import { isSupabaseConfigured } from "@/lib/supabase";

/** Files larger than this use server-side conversion via Edge Function */
const LARGE_FILE_THRESHOLD = 50 * 1024 * 1024; // 50 MB
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileSpreadsheet,
  Trash2,
  ArrowRight,
  AlertCircle,
  Zap,
  Cloud,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  ShieldX,
  Columns3,
  RefreshCw,
  FileType2,
} from "lucide-react";
import { formatNumber } from "@/lib/utils";
import type { UploadedFile } from "@/types";

// ─── Helper: format bytes ─────────────────────────────────────────
function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

// ─── CSV helpers ─────────────────────────────────────────────────

/** Max bytes per CSV chunk (smaller = lower memory per edge-function call). */
const CSV_CHUNK_SIZE = 1 * 1024 * 1024; // 1 MB

/** How many chunks to upload simultaneously. */
const PARALLEL_CHUNK_UPLOADS = 5;

/** Detect the most likely field delimiter from a CSV header line. */
function detectCsvDelimiter(line: string): string {
  const semi = (line.match(/;/g) || []).length;
  const comma = (line.match(/,/g) || []).length;
  const tab = (line.match(/\t/g) || []).length;
  if (tab > comma && tab > semi) return "\t";
  if (semi > comma) return ";";
  return ",";
}

/** Parse a single CSV line respecting RFC 4180 quoting. */
function parseCsvLine(line: string, delim: string): string[] {
  const cols: string[] = [];
  let inQuote = false;
  let cur = "";
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuote && line[i + 1] === '"') { cur += '"'; i++; }
      else { inQuote = !inQuote; }
    } else if (ch === delim && !inQuote) {
      cols.push(cur.trim());
      cur = "";
    } else {
      cur += ch;
    }
  }
  cols.push(cur.trim());
  return cols.filter((c) => c.length > 0);
}

interface ChunkProgressInfo {
  phase: "reading" | "splitting" | "uploading";
  chunkCurrent?: number;  // completed count
  chunkTotal?: number;
  parallelCount?: number; // how many are currently in-flight
}

/**
 * Split a large CSV into ≤5 MB chunks (each with the header row),
 * upload every chunk to Storage, and return the list of Storage paths.
 *
 * Runs entirely in the browser — memory is not a constraint here.
 */
async function chunkAndUploadCsv(
  file: File,
  onProgress: (info: ChunkProgressInfo) => void
): Promise<{ chunkPaths: string[]; columns: string[] }> {
  onProgress({ phase: "reading" });

  // Read full text (browser RAM is not the bottleneck)
  const raw = await file.text();

  // Strip BOM, isolate header + body
  const text = raw.startsWith("\uFEFF") ? raw.slice(1) : raw;
  const firstNl = text.indexOf("\n");
  const headerLine = firstNl >= 0 ? text.slice(0, firstNl + 1) : text; // includes \n
  const body = firstNl >= 0 ? text.slice(firstNl + 1) : "";

  // Detect columns from header
  const headerTrimmed = headerLine.replace(/\r?\n$/, "");
  const delim = detectCsvDelimiter(headerTrimmed);
  const columns = parseCsvLine(headerTrimmed, delim);

  // ── 1. Split into chunks ──────────────────────────────────────────
  const targetChars = Math.max(10_000, CSV_CHUNK_SIZE - headerLine.length);
  const encoder = new TextEncoder();

  interface Chunk { path: string; buffer: ArrayBuffer; size: number }
  const chunks: Chunk[] = [];

  // Each upload gets its own run_id folder so Storage groups them
  const runId = crypto.randomUUID();
  const sessionId = getCurrentSessionId();
  const runFolderPath = `para_validacao/${sessionId}/${runId}`;

  let offset = 0;
  while (offset < body.length) {
    let end = offset + targetChars;
    if (end < body.length) {
      const nl = body.indexOf("\n", end);
      end = nl >= 0 ? nl + 1 : body.length;
    } else {
      end = body.length;
    }
    const buf = encoder.encode(headerLine + body.slice(offset, end)).buffer;
    chunks.push({
      path: `${runFolderPath}/chunk_${String(chunks.length + 1).padStart(3, "0")}.csv`,
      buffer: buf,
      size: buf.byteLength,
    });
    offset = end;
  }

  onProgress({ phase: "splitting", chunkTotal: chunks.length });

  // ── 2. Upload in parallel (pool of PARALLEL_CHUNK_UPLOADS) ────────
  let completed = 0;
  let inFlight = 0;

  // Simple concurrency pool: launch up to PARALLEL_CHUNK_UPLOADS at once
  await new Promise<void>((resolve, reject) => {
    let nextIdx = 0;
    let settled = 0;

    const launchNext = () => {
      while (inFlight < PARALLEL_CHUNK_UPLOADS && nextIdx < chunks.length) {
        const chunk = chunks[nextIdx++];
        inFlight++;
        uploadBlobToPath(chunk.buffer, chunk.path, "text/csv")
          .then(() => {
            completed++;
            inFlight--;
            onProgress({
              phase: "uploading",
              chunkCurrent: completed,
              chunkTotal: chunks.length,
              parallelCount: inFlight,
            });
            settled++;
            if (settled === chunks.length) resolve();
            else launchNext();
          })
          .catch(reject);
      }
    };

    launchNext();
    if (chunks.length === 0) resolve();
  });

  // ── 3. Upload manifest ────────────────────────────────────────────
  const isVoltz =
    file.name.toLowerCase().includes("voltz") ||
    file.name.toLowerCase().includes("volt");
  const totalSize = chunks.reduce((s, c) => s + c.size, 0);
  const chunkPaths = chunks.map((c) => c.path);
  const meta = { originalName: file.name, columns, isVoltz, totalSize, totalChunks: chunks.length, chunkPaths };
  const metaBuf = encoder.encode(JSON.stringify(meta)).buffer;
  await uploadBlobToPath(metaBuf, `${runFolderPath}/_meta.json`, "application/octet-stream");

  return { chunkPaths, columns, runFolderPath };
}

export function UploadPage() {
  const { uploadedFiles, setUploadedFiles, setCurrentStep } = useApp();
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingOverlay, setProcessingOverlay] = useState<{
    current: number;
    total: number;
    fileName: string;
    step: string;
  } | null>(null);

  /** Inline chunk progress per file id — drives the card progress display */
  const [chunkProgressMap, setChunkProgressMap] = useState<
    Map<string, { current: number; total: number; step: string; parallelCount: number }>
  >(new Map());

  const updateChunkProgress = (
    id: string,
    current: number,
    total: number,
    step: string,
    parallelCount = 0
  ) =>
    setChunkProgressMap((prev) => {
      const next = new Map(prev);
      next.set(id, { current, total, step, parallelCount });
      return next;
    });

  const clearChunkProgress = (id: string) =>
    setChunkProgressMap((prev) => {
      const next = new Map(prev);
      next.delete(id);
      return next;
    });
  const supabaseReady = isSupabaseConfigured();

  // ── Refresh file list from Storage on mount ─────────────────────
  const refreshFileList = useCallback(async () => {
    if (!supabaseReady) return;
    const stored = await listSessionStageFiles("para_validacao");
    const validados = await listSessionStageFiles("validados");

    setUploadedFiles((prev) => {
      const existingPaths = new Set(prev.map((f) => f.storagePath));
      const newFromStorage: UploadedFile[] = [];

      for (const sf of [...stored, ...validados]) {
        if (existingPaths.has(sf.path)) continue;
        const isCsv = sf.name.endsWith(".csv");

        newFromStorage.push({
          id: crypto.randomUUID(),
          name: sf.name,
          size: sf.size,
          storagePath: sf.path,          // first chunk or single-file path
          chunkPaths: sf.chunkPaths,     // undefined for single files
          runFolderPath: sf.runFolderPath,
          uploadStatus: "uploaded",
          uploadProgress: 100,
          validationStatus: isCsv ? "valid" : "pending",
          columns: sf.columns ?? [],
          rowCount: 0,
          isVoltz:
            sf.isVoltz ??
            (sf.name.toLowerCase().includes("voltz") ||
            sf.name.toLowerCase().includes("volt")),
          data: [],
        });
      }

      return newFromStorage.length > 0 ? [...prev, ...newFromStorage] : prev;
    });
  }, [supabaseReady, setUploadedFiles]);

  useEffect(() => {
    refreshFileList();
  }, [refreshFileList]);

  // ── Handle file drop / selection ────────────────────────────────
  // New flow: Excel → Worker (convert to CSV + validate) → Upload CSV
  const handleFiles = useCallback(
    async (fileList: FileList | File[]) => {
      setError(null);

      const allFiles = Array.from(fileList);
      const files = allFiles.filter(
        (f) =>
          f.name.endsWith(".xlsx") ||
          f.name.endsWith(".xls") ||
          f.name.endsWith(".csv")
      );

      if (files.length === 0) {
        setError("Nenhum arquivo válido selecionado. Formatos aceitos: .xlsx, .xls, .csv");
        return;
      }

      if (!supabaseReady) {
        setError("Supabase não configurado. Configure as variáveis de ambiente.");
        return;
      }

      // Create placeholder entries immediately
      const placeholders: UploadedFile[] = files.map((f) => {
        const isCsv = f.name.endsWith(".csv");
        return {
          id: crypto.randomUUID(),
          name: f.name,
          size: f.size,
          uploadStatus: isCsv ? ("uploading" as const) : ("converting" as const),
          uploadProgress: 0,
          validationStatus: "pending" as const,
          columns: [],
          rowCount: 0,
          isVoltz:
            f.name.toLowerCase().includes("voltz") ||
            f.name.toLowerCase().includes("volt"),
          data: [],
        };
      });

      setUploadedFiles((prev) => [...prev, ...placeholders]);

      // Process each file: convert → validate → upload CSV
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const id = placeholders[i].id;
        const isCsvFile = file.name.endsWith(".csv");
        const isLarge = !isCsvFile && file.size >= LARGE_FILE_THRESHOLD;

        setProcessingOverlay({
          current: i + 1,
          total: files.length,
          fileName: file.name,
          step: isCsvFile
            ? `Enviando CSV (${formatBytes(file.size)})…`
            : isLarge
            ? "Arquivo grande — enviando para o servidor…"
            : "Convertendo Excel → CSV…",
        });

        // Fire-and-forget per file
        (async () => {
          try {
            if (isCsvFile) {
              // ── CSV path ──────────────────────────────────────────────
              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === id ? { ...f, uploadStatus: "uploading" as const, uploadProgress: 0 } : f
                )
              );

              const isLargeCsv = file.size > CSV_CHUNK_SIZE;

              if (isLargeCsv) {
                // Large CSV → split into ≤5 MB chunks, progress shown inline on the card
                updateChunkProgress(id, 0, 1, "Lendo e analisando arquivo…");

                const { chunkPaths, columns, runFolderPath } = await chunkAndUploadCsv(
                  file,
                  ({ phase, chunkCurrent, chunkTotal, parallelCount }) => {
                    const step =
                      phase === "reading"
                        ? "Lendo e analisando arquivo…"
                        : phase === "splitting"
                        ? `Dividindo em ${chunkTotal} partes de 1 MB…`
                        : `${chunkCurrent} de ${chunkTotal} partes enviadas`;
                    updateChunkProgress(
                      id,
                      chunkCurrent ?? 0,
                      chunkTotal ?? 1,
                      step,
                      parallelCount ?? 0
                    );
                    if (phase === "uploading" && chunkCurrent && chunkTotal) {
                      setUploadedFiles((prev) =>
                        prev.map((f) =>
                          f.id === id
                            ? { ...f, uploadProgress: Math.round((chunkCurrent / chunkTotal) * 100) }
                            : f
                        )
                      );
                    }
                  }
                );

                clearChunkProgress(id);

                setUploadedFiles((prev) =>
                  prev.map((f) =>
                    f.id === id
                      ? {
                          ...f,
                          storagePath: chunkPaths[0],
                          chunkPaths,
                          runFolderPath,
                          uploadStatus: "uploaded" as const,
                          uploadProgress: 100,
                          validationStatus: "valid" as const,
                          columns,
                          rowCount: 0,
                        }
                      : f
                  )
                );
              } else {
                // Small CSV → single upload (fast path)
                const headerSlice = file.slice(0, 8192);
                const headerText = await headerSlice.text();
                const cleanedHeader = headerText.replace(/^\uFEFF/, "");
                const firstLine = cleanedHeader.split(/\r?\n/)[0] ?? "";
                const delim = detectCsvDelimiter(firstLine);
                const columns = parseCsvLine(firstLine, delim);

                const buffer = await file.arrayBuffer();
                const uploadResult = await uploadCsvBlob(
                  buffer,
                  file.name,
                  (_loaded, _total, percent) => {
                    setUploadedFiles((prev) =>
                      prev.map((f) =>
                        f.id === id ? { ...f, uploadProgress: Math.round(percent) } : f
                      )
                    );
                  }
                );

                setUploadedFiles((prev) =>
                  prev.map((f) =>
                    f.id === id
                      ? {
                          ...f,
                          storagePath: uploadResult.path,
                          csvPath: uploadResult.path,
                          uploadStatus: "uploaded" as const,
                          uploadProgress: 100,
                          validationStatus: "valid" as const,
                          columns,
                          rowCount: 0,
                        }
                      : f
                  )
                );
              }
            } else if (isLarge) {
              // ── Large file path: upload raw Excel → server converts to CSV ──

              // Step 1: Upload raw Excel to Storage
              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === id ? { ...f, uploadStatus: "uploading" as const, uploadProgress: 0 } : f
                )
              );

              setProcessingOverlay((prev) =>
                prev ? { ...prev, step: `Enviando Excel (${formatBytes(file.size)})…` } : null
              );

              const rawUpload = await uploadFileForValidation(file, (_loaded, _total, percent) => {
                setUploadedFiles((prev) =>
                  prev.map((f) =>
                    f.id === id ? { ...f, uploadProgress: Math.round(percent * 0.6) } : f
                  )
                );
              });

              // Step 2: Ask Edge Function to convert + extract metadata
              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === id
                    ? { ...f, uploadStatus: "converting" as const, uploadProgress: 60 }
                    : f
                )
              );

              setProcessingOverlay((prev) =>
                prev ? { ...prev, step: "Servidor convertendo Excel → CSV…" } : null
              );

              const result = await callReadColumnsWithCsv(rawUpload.path, file.name);

              if (!result.valid || !result.csvPath) {
                setUploadedFiles((prev) =>
                  prev.map((f) =>
                    f.id === id
                      ? {
                          ...f,
                          uploadStatus: "error" as const,
                          validationStatus: "invalid" as const,
                          validationError: result.error ?? "Falha na conversão server-side.",
                        }
                      : f
                  )
                );
                return;
              }

              // Done — CSV is already in Storage
              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === id
                    ? {
                        ...f,
                        storagePath: result.csvPath,
                        csvPath: result.csvPath,
                        uploadStatus: "uploaded" as const,
                        uploadProgress: 100,
                        validationStatus: "valid" as const,
                        columns: result.columns ?? [],
                        columnInfo: result.columnInfo,
                        rowCount: result.rowCount ?? 0,
                        sheetName: result.sheetName,
                        isVoltz: result.isVoltz ?? f.isVoltz,
                      }
                    : f
                )
              );

            } else {
              // ── Small file path: Worker converts locally → upload CSV ──

              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === id ? { ...f, uploadStatus: "converting" as const } : f
                )
              );

              const result = await convertExcelToCsvAsync(file);

              if (!result.valid) {
                setUploadedFiles((prev) =>
                  prev.map((f) =>
                    f.id === id
                      ? {
                          ...f,
                          uploadStatus: "error" as const,
                          validationStatus: "invalid" as const,
                          validationError: result.error ?? "Cabeçalho inválido.",
                        }
                      : f
                  )
                );
                return;
              }

              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === id
                    ? {
                        ...f,
                        uploadStatus: "uploading_csv" as const,
                        uploadProgress: 0,
                        columns: result.columns,
                        columnInfo: result.columnInfo,
                        rowCount: result.rowCount,
                        sheetName: result.sheetName,
                        isVoltz: result.isVoltz || f.isVoltz,
                        detectedDate: result.detectedDate,
                      }
                    : f
                )
              );

              setProcessingOverlay((prev) =>
                prev ? { ...prev, step: `Enviando CSV (${formatBytes(result.csvSize)})…` } : null
              );

              const uploadResult = await uploadCsvBlob(
                result.csvBuffer,
                file.name,
                (_loaded, _total, percent) => {
                  setUploadedFiles((prev) =>
                    prev.map((f) =>
                      f.id === id ? { ...f, uploadProgress: Math.round(percent) } : f
                    )
                  );
                }
              );

              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === id
                    ? {
                        ...f,
                        storagePath: uploadResult.path,
                        csvPath: uploadResult.path,
                        uploadStatus: "uploaded" as const,
                        uploadProgress: 100,
                        validationStatus: "valid" as const,
                      }
                    : f
                )
              );
            }
          } catch (err) {
            console.error(`[upload] failed for ${file.name}:`, err);
            setUploadedFiles((prev) =>
              prev.map((f) =>
                f.id === id
                  ? {
                      ...f,
                      uploadStatus: "error" as const,
                      validationStatus: "error" as const,
                      validationError: String(err),
                    }
                  : f
              )
            );
          }
        })();
      }

      // Clear overlay once all fire-and-forget calls launched
      // (individual progress shows on each card)
      setTimeout(() => setProcessingOverlay(null), 800);
    },
    [supabaseReady, setUploadedFiles]
  );

  // ── Drop handler ────────────────────────────────────────────────
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  // ── Remove file ─────────────────────────────────────────────────
  const removeFile = async (id: string) => {
    const file = uploadedFiles.find((f) => f.id === id);
    if (file) {
      if (file.runFolderPath) {
        // Chunked upload — delete the entire run_id folder (chunks + _meta.json)
        deleteRunFolder(file.runFolderPath).catch(() => {});
      } else if (file.storagePath) {
        deleteFileFromStorage(file.storagePath).catch(() => {});
      }
    }
    setUploadedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  // ── Navigation ──────────────────────────────────────────────────
  const proceed = () => {
    if (uploadedFiles.length > 0) setCurrentStep(1);
  };

  // ── Derived state ───────────────────────────────────────────────
  const anyProcessing = uploadedFiles.some(
    (f) => f.uploadStatus === "converting" || f.uploadStatus === "uploading_csv" || f.uploadStatus === "uploading"
  );
  const validFiles = uploadedFiles.filter((f) => f.validationStatus === "valid");
  const canProceed = validFiles.length > 0 && !anyProcessing;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* ── Processing Overlay (Excel conversion only — quick operations) ── */}
      <AnimatePresence>
        {processingOverlay && (
          <motion.div
            key="processing-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.92, opacity: 0, y: 8 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.92, opacity: 0, y: 8 }}
              transition={{ type: "spring", stiffness: 300, damping: 28 }}
              className="bg-white rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-4 max-w-sm w-full mx-4"
            >
              <div className="relative flex items-center justify-center w-16 h-16">
                <div className="absolute inset-0 rounded-full border-4 border-primary/15" />
                <motion.div
                  className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                />
                <FileType2 className="w-6 h-6 text-primary" />
              </div>
              <div className="text-center space-y-1">
                <p className="text-sm font-semibold text-foreground">
                  {processingOverlay.total > 1
                    ? `Arquivo ${processingOverlay.current} de ${processingOverlay.total}`
                    : processingOverlay.step}
                </p>
                <p className="text-xs text-primary font-medium truncate max-w-[220px]">
                  {processingOverlay.fileName}
                </p>
              </div>
              {processingOverlay.total > 1 && (
                <>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                    <motion.div
                      className="h-full bg-primary rounded-full"
                      animate={{ width: `${((processingOverlay.current - 1) / processingOverlay.total) * 100}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">{processingOverlay.step}</p>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">
            Carregamento de Dados
          </h2>
          <p className="text-muted-foreground mt-1">
            Faça upload dos arquivos Excel → validação automática no servidor → processamento.
          </p>
        </div>
        {supabaseReady && (
          <Button
            variant="ghost"
            size="sm"
            onClick={refreshFileList}
            className="gap-1.5 text-muted-foreground"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Atualizar
          </Button>
        )}
      </div>

      {/* ── Drop Zone ── */}
      <Card className="overflow-hidden">
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`
            relative flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-xl
            transition-all duration-300 cursor-pointer
            ${isDragging
              ? "border-primary bg-blue-50/50 scale-[1.01]"
              : "border-slate-200 hover:border-blue-300 hover:bg-slate-50/50"}
          `}
        >
          <div
            className={`
              flex items-center justify-center w-16 h-16 rounded-2xl mb-4 transition-all duration-300
              ${isDragging ? "bg-primary text-white scale-110" : "bg-slate-100 text-slate-400"}
            `}
          >
            <Upload className="w-7 h-7" />
          </div>

          <p className="text-base font-medium text-foreground mb-1">
            {isDragging ? "Solte os arquivos aqui" : "Arraste e solte seus arquivos"}
          </p>
          <p className="text-sm text-muted-foreground mb-1">
            Formatos aceitos: .xlsx, .xls, .csv
          </p>
          <p className="text-xs text-muted-foreground/60 mb-4">
            CSV é enviado diretamente • Excel grande (&gt;50 MB) é convertido no servidor
          </p>

          <label className="cursor-pointer">
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              multiple
              className="hidden"
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
            />
            <Button variant="outline" size="sm" asChild>
              <span>Selecionar Arquivos</span>
            </Button>
          </label>
        </div>
      </Card>

      {/* ── Error ── */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm whitespace-pre-line"
          >
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── File List ── */}
      <AnimatePresence mode="popLayout">
        {uploadedFiles.map((file, idx) => (
          <motion.div
            key={file.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ delay: idx * 0.04 }}
          >
            <Card
              className={
                file.validationStatus === "invalid"
                  ? "border-red-200 bg-red-50/30"
                  : file.validationStatus === "valid"
                  ? "border-emerald-200 bg-emerald-50/10"
                  : ""
              }
            >
              <CardContent className="flex items-center gap-4 p-4">
                {/* Icon */}
                <div
                  className={`flex items-center justify-center w-11 h-11 rounded-xl
                  ${
                    file.validationStatus === "invalid"
                      ? "bg-red-100 text-red-500"
                      : file.validationStatus === "valid"
                      ? "bg-emerald-50 text-emerald-600"
                      : "bg-slate-100 text-slate-400"
                  }`}
                >
                  <FileSpreadsheet className="w-5 h-5" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {/* Name + Badges */}
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <p className="text-sm font-medium truncate">{file.name}</p>

                    {file.isVoltz && (
                      <Badge variant="warning" className="gap-1">
                        <Zap className="w-3 h-3" />VOLTZ
                      </Badge>
                    )}

                    {/* Upload / processing status */}
                    {file.uploadStatus === "converting" && (
                      <Badge variant="default" className="gap-1 bg-violet-50 text-violet-600 border-violet-200">
                        <Loader2 className="w-3 h-3 animate-spin" />Convertendo…
                      </Badge>
                    )}
                    {file.uploadStatus === "uploading_csv" && (
                      <Badge variant="default" className="gap-1 bg-amber-50 text-amber-600 border-amber-200">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        {file.uploadProgress !== undefined
                          ? `Enviando CSV ${file.uploadProgress}%`
                          : "Enviando CSV…"}
                      </Badge>
                    )}
                    {file.uploadStatus === "uploading" && (
                      <Badge variant="default" className="gap-1 bg-amber-50 text-amber-600 border-amber-200">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        {file.uploadProgress !== undefined
                          ? `${file.uploadProgress}%`
                          : "Enviando…"}
                      </Badge>
                    )}
                    {file.uploadStatus === "uploaded" && file.validationStatus === "valid" && (
                      <Badge variant="default" className="gap-1 bg-sky-100 text-sky-700 border-sky-200">
                        <Cloud className="w-3 h-3" />No Storage
                      </Badge>
                    )}
                    {/* Chunk indicator */}
                    {file.chunkPaths && file.chunkPaths.length > 1 && (
                      <Badge variant="default" className="gap-1 bg-violet-50 text-violet-700 border-violet-200">
                        {file.chunkPaths.length} partes
                      </Badge>
                    )}

                    {/* Validation status */}
                    {file.validationStatus === "validating" && (
                      <Badge variant="default" className="gap-1 bg-amber-50 text-amber-600 border-amber-200">
                        <Loader2 className="w-3 h-3 animate-spin" />Validando…
                      </Badge>
                    )}
                    {file.validationStatus === "valid" && (
                      <Badge variant="default" className="gap-1 bg-emerald-50 text-emerald-700 border-emerald-200">
                        <ShieldCheck className="w-3 h-3" />Validado
                      </Badge>
                    )}
                    {file.validationStatus === "invalid" && (
                      <Badge variant="destructive" className="gap-1">
                        <ShieldX className="w-3 h-3" />Rejeitado
                      </Badge>
                    )}
                    {file.validationStatus === "error" && (
                      <Badge variant="default" className="gap-1 bg-amber-50 text-amber-700 border-amber-200">
                        <AlertCircle className="w-3 h-3" />Erro validação
                      </Badge>
                    )}

                    {/* Column count */}
                    {file.validationStatus === "valid" && file.columns.length > 0 && (
                      <Badge variant="default" className="gap-1 bg-violet-50 text-violet-700 border-violet-200">
                        <Columns3 className="w-3 h-3" />{file.columns.length} colunas
                      </Badge>
                    )}
                  </div>

                  {/* Stats row */}
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{formatBytes(file.size)}</span>
                    {file.rowCount > 0 && (
                      <span>{formatNumber(file.rowCount, 0)} registros</span>
                    )}
                    {file.columns.length > 0 && (
                      <span>{file.columns.length} colunas</span>
                    )}
                    {file.sheetName && <span>Aba: {file.sheetName}</span>}
                  </div>

                  {/* ── Chunk upload progress (large CSV) ── */}
                  {(() => {
                    const cp = chunkProgressMap.get(file.id);
                    if (!cp) return null;
                    const pct = cp.total > 0 ? Math.round((cp.current / cp.total) * 100) : 0;
                    return (
                      <div className="mt-3 space-y-2">
                        {/* Step label + percentage */}
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">{cp.step}</span>
                          <span className="font-semibold tabular-nums text-primary">{pct}%</span>
                        </div>

                        {/* Main bar */}
                        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                          <motion.div
                            className="h-full bg-primary rounded-full"
                            animate={{ width: `${pct}%` }}
                            transition={{ duration: 0.35, ease: "easeOut" }}
                          />
                        </div>

                        {/* Chunk chips — max 60 shown to avoid overflow */}
                        {cp.total <= 60 && (
                          <div className="flex flex-wrap gap-1 pt-0.5">
                            {Array.from({ length: cp.total }, (_, i) => {
                              const done     = i < cp.current;
                              const inFlight = i >= cp.current && i < cp.current + (cp.parallelCount ?? 0);
                              return (
                                <div
                                  key={i}
                                  title={
                                    inFlight ? `Parte ${i + 1} — enviando…`
                                    : done   ? `Parte ${i + 1} — concluída`
                                    :          `Parte ${i + 1} — aguardando`
                                  }
                                  className={`w-5 h-5 rounded text-[9px] font-bold flex items-center justify-center transition-all duration-200
                                    ${inFlight ? "bg-primary text-white shadow-sm animate-pulse scale-110"
                                    : done     ? "bg-primary/30 text-primary"
                                    :            "bg-slate-100 text-slate-300"}`}
                                >
                                  {i + 1}
                                </div>
                              );
                            })}
                          </div>
                        )}

                        {/* For very many chunks just show counter */}
                        {cp.total > 60 && (
                          <p className="text-xs text-muted-foreground">
                            {cp.current} de {cp.total} partes concluídas
                            {(cp.parallelCount ?? 0) > 0 && ` • ${cp.parallelCount} em paralelo`}
                          </p>
                        )}
                      </div>
                    );
                  })()}

                  {/* ── Standard upload bar (small files) ── */}
                  {!chunkProgressMap.has(file.id) &&
                    (file.uploadStatus === "uploading" || file.uploadStatus === "uploading_csv") &&
                    file.uploadProgress !== undefined && (
                    <div className="mt-2">
                      <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <motion.div
                          className="h-full bg-amber-500 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${file.uploadProgress}%` }}
                          transition={{ duration: 0.2 }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Validation error */}
                  {file.validationError && (
                    <p className="mt-1 text-xs text-red-600">{file.validationError}</p>
                  )}
                </div>

                {/* Delete button */}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeFile(file.id)}
                  className="text-slate-400 hover:text-red-500 shrink-0"
                  disabled={file.validationStatus === "validating"}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* ── Footer / Actions ── */}
      {uploadedFiles.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-between pt-4"
        >
          <div className="flex items-center gap-4 text-xs flex-wrap">
            <span className="text-sm text-muted-foreground">
              {uploadedFiles.length} arquivo(s) •{" "}
              {formatBytes(uploadedFiles.reduce((a, f) => a + f.size, 0))} total
            </span>
            <span className="flex items-center gap-1 text-sky-600">
              <Cloud className="w-3.5 h-3.5" />
              {uploadedFiles.filter((f) => f.uploadStatus === "uploaded").length}/{uploadedFiles.length} enviados
            </span>
            <span className="flex items-center gap-1 text-emerald-600">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {validFiles.length}/{uploadedFiles.length} validados
            </span>
            {anyProcessing && (
              <span className="flex items-center gap-1 text-amber-600">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />processando…
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button onClick={proceed} className="gap-2" disabled={!canProceed}>
              {anyProcessing ? (
                <><Loader2 className="w-4 h-4 animate-spin" />Aguardar…</>
              ) : (
                <>Próximo: Mapeamento<ArrowRight className="w-4 h-4" /></>
              )}
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}