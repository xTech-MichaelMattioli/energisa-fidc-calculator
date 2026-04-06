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
  listSessionStageFiles,
  deleteFileFromStorage,
} from "@/services/storage.service";
import { isSupabaseConfigured } from "@/lib/supabase";
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
          storagePath: sf.path,
          uploadStatus: "uploaded",
          uploadProgress: 100,
          validationStatus: isCsv ? "valid" : "pending",
          columns: [],
          rowCount: 0,
          isVoltz:
            sf.name.toLowerCase().includes("voltz") ||
            sf.name.toLowerCase().includes("volt"),
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
        (f) => f.name.endsWith(".xlsx") || f.name.endsWith(".xls")
      );

      if (files.length === 0) {
        setError("Nenhum arquivo Excel válido (.xlsx, .xls) selecionado.");
        return;
      }

      // Warn about very large files — the Worker needs to parse the entire
      // Excel binary in memory; files over 100 MB may be slow or crash.
      const LARGE_FILE_BYTES = 100 * 1024 * 1024; // 100 MB
      const largeFiles = files.filter((f) => f.size > LARGE_FILE_BYTES);
      if (largeFiles.length > 0) {
        setError(
          `Atenção: ${largeFiles.map((f) => f.name).join(", ")} ${largeFiles.length > 1 ? "são arquivos grandes" : "é um arquivo grande"} (>${Math.round(largeFiles[0].size / 1024 / 1024)} MB). ` +
          `O processamento pode demorar vários minutos e consumir bastante memória do navegador. Se travar, divida o arquivo em partes menores.`
        );
        // Do NOT return — let the user proceed anyway
      }

      if (!supabaseReady) {
        setError("Supabase não configurado. Configure as variáveis de ambiente.");
        return;
      }

      // Create placeholder entries immediately
      const placeholders: UploadedFile[] = files.map((f) => ({
        id: crypto.randomUUID(),
        name: f.name,
        size: f.size,
        uploadStatus: "converting" as const,
        uploadProgress: 0,
        validationStatus: "pending" as const,
        columns: [],
        rowCount: 0,
        isVoltz:
          f.name.toLowerCase().includes("voltz") ||
          f.name.toLowerCase().includes("volt"),
        data: [],
      }));

      setUploadedFiles((prev) => [...prev, ...placeholders]);

      // Process each file: convert → validate → upload CSV
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const id = placeholders[i].id;

        setProcessingOverlay({
          current: i + 1,
          total: files.length,
          fileName: file.name,
          step: "Convertendo Excel → CSV…",
        });

        // Fire-and-forget per file
        (async () => {
          try {
            // ── Step 1: Worker converts Excel → CSV + validates header ──
            setUploadedFiles((prev) =>
              prev.map((f) =>
                f.id === id ? { ...f, uploadStatus: "converting" as const } : f
              )
            );

            const result = await convertExcelToCsvAsync(file);

            // ── Step 2: Check validation ──
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

            // ── Step 3: Upload CSV to Storage with progress ──
            setUploadedFiles((prev) =>
              prev.map((f) =>
                f.id === id
                  ? {
                      ...f,
                      uploadStatus: "uploading_csv" as const,
                      uploadProgress: 0,
                      // Populate metadata from worker immediately
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
                    f.id === id
                      ? { ...f, uploadProgress: Math.round(percent) }
                      : f
                  )
                );
              }
            );

            // ── Done! ──
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
    if (file?.storagePath) {
      deleteFileFromStorage(file.storagePath).catch(() => {});
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
      {/* ── Processing Overlay ── */}
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
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl shadow-2xl p-10 flex flex-col items-center gap-5 max-w-sm w-full mx-4"
            >
              <div className="relative flex items-center justify-center w-20 h-20">
                <div className="absolute inset-0 rounded-full border-4 border-primary/20" />
                <div className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent animate-spin" />
                <FileType2 className="w-7 h-7 text-primary" />
              </div>

              <div className="text-center space-y-1">
                <p className="text-base font-semibold text-foreground">
                  Processando arquivo{processingOverlay.total > 1 ? "s" : ""}…
                </p>
                <p className="text-sm text-muted-foreground">
                  {processingOverlay.total > 1
                    ? `Arquivo ${processingOverlay.current} de ${processingOverlay.total}`
                    : processingOverlay.step}
                </p>
                <p className="text-xs font-medium text-primary truncate max-w-[220px]">
                  {processingOverlay.fileName}
                </p>
              </div>

              {processingOverlay.total > 1 && (
                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <motion.div
                    className="h-full bg-primary rounded-full"
                    initial={{ width: 0 }}
                    animate={{
                      width: `${(processingOverlay.current / processingOverlay.total) * 100}%`,
                    }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              )}

              <p className="text-xs text-muted-foreground">
                {processingOverlay.step}
              </p>
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
            {isDragging ? "Solte os arquivos aqui" : "Arraste e solte seus arquivos Excel"}
          </p>
          <p className="text-sm text-muted-foreground mb-1">
            Formatos aceitos: .xlsx, .xls • Upload direto ao servidor
          </p>
          <p className="text-xs text-muted-foreground/60 mb-4">
            Nenhum processamento local — arquivos vão direto para a nuvem
          </p>

          <label className="cursor-pointer">
            <input
              type="file"
              accept=".xlsx,.xls"
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

                  {/* Upload progress bar */}
                  {(file.uploadStatus === "uploading" || file.uploadStatus === "uploading_csv") && file.uploadProgress !== undefined && (
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