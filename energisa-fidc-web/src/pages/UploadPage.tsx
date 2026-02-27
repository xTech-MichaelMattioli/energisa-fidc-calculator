/**
 * Page 1: Upload (Carregamento)
 *
 * NEW "upload-first, validate-later" flow:
 *
 *  1. User drops files → each is uploaded DIRECTLY to Storage
 *     (`para_validacao/<session>/file.xlsx`) with real-time progress.
 *  2. Once all uploads finish, files are listed from Storage.
 *  3. User clicks "Validar" → edge function validates each file.
 *     - Invalid → file deleted + reason shown.
 *     - Valid   → moved to `validados/`, columns extracted.
 *  4. User clicks "Próximo" to proceed to Mapping.
 */
import { useCallback, useState, useEffect } from "react";
import { useApp } from "@/context/AppContext";
import {
  uploadFileForValidation,
  listSessionStageFiles,
  deleteFileFromStorage,
} from "@/services/storage.service";
import { validateFile } from "@/services/validation-processor.service";
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
  PlayCircle,
  FolderOpen,
  RefreshCw,
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
  const [isValidating, setIsValidating] = useState(false);
  const [validationProgress, setValidationProgress] = useState<{
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

    // Merge stored files into state (don't duplicate)
    setUploadedFiles((prev) => {
      const existingPaths = new Set(prev.map((f) => f.storagePath));
      const newFromStorage: UploadedFile[] = [];

      for (const sf of [...stored, ...validados]) {
        if (existingPaths.has(sf.path)) continue;
        newFromStorage.push({
          id: crypto.randomUUID(),
          name: sf.name,
          size: sf.size,
          storagePath: sf.path,
          uploadStatus: "uploaded",
          uploadProgress: 100,
          validationStatus: sf.path.startsWith("validados/") ? "valid" : "pending",
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
  const handleFiles = useCallback(
    async (fileList: FileList | File[]) => {
      setError(null);

      const files = Array.from(fileList).filter(
        (f) => f.name.endsWith(".xlsx") || f.name.endsWith(".xls")
      );

      if (files.length === 0) {
        setError("Nenhum arquivo Excel válido (.xlsx, .xls) selecionado.");
        return;
      }

      if (!supabaseReady) {
        setError("Supabase não configurado. Configure as variáveis de ambiente.");
        return;
      }

      // Create placeholder entries immediately (uploading state)
      const placeholders: UploadedFile[] = files.map((f) => ({
        id: crypto.randomUUID(),
        name: f.name,
        size: f.size,
        uploadStatus: "uploading" as const,
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

      // Upload each file in parallel with progress
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const id = placeholders[i].id;

        // Fire-and-forget per file (parallel uploads)
        (async () => {
          try {
            const result = await uploadFileForValidation(file, (_loaded, _total, percent) => {
              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === id
                    ? { ...f, uploadProgress: Math.round(percent) }
                    : f
                )
              );
            });

            setUploadedFiles((prev) =>
              prev.map((f) =>
                f.id === id
                  ? {
                      ...f,
                      storagePath: result.path,
                      uploadStatus: "uploaded" as const,
                      uploadProgress: 100,
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
    },
    [supabaseReady, setUploadedFiles]
  );

  // ── Validate all pending files ─────────────────────────────────
  const validateAllFiles = useCallback(async () => {
    const pendingFiles = uploadedFiles.filter(
      (f) =>
        f.uploadStatus === "uploaded" &&
        f.validationStatus === "pending" &&
        f.storagePath
    );

    if (pendingFiles.length === 0) return;

    setIsValidating(true);

    for (let i = 0; i < pendingFiles.length; i++) {
      const file = pendingFiles[i];
      const id = file.id;

      setValidationProgress({
        current: i + 1,
        total: pendingFiles.length,
        fileName: file.name,
        step: "Iniciando validação…",
      });

      // Mark as validating
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.id === id ? { ...f, validationStatus: "validating" as const } : f
        )
      );

      const outcome = await validateFile(
        file.storagePath!,
        file.name,
        (step, detail) => {
          setValidationProgress((prev) =>
            prev ? { ...prev, step: detail ?? step } : null
          );
        }
      );

      if (outcome.status === "valid") {
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === id
              ? {
                  ...f,
                  validationStatus: "valid" as const,
                  storagePath: outcome.validadosPath,
                  columns: outcome.columns,
                  columnInfo: outcome.columnInfo,
                  rowCount: outcome.rowCount,
                  sheetName: outcome.sheetName,
                  isVoltz: outcome.isVoltz || f.isVoltz,
                }
              : f
          )
        );
      } else if (outcome.status === "invalid") {
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === id
              ? {
                  ...f,
                  validationStatus: "invalid" as const,
                  validationError: outcome.error,
                  uploadStatus: "error" as const,
                }
              : f
          )
        );
      } else {
        // error contacting edge function — keep file, mark error
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.id === id
              ? {
                  ...f,
                  validationStatus: "error" as const,
                  validationError: outcome.error,
                }
              : f
          )
        );
      }
    }

    setIsValidating(false);
    setValidationProgress(null);
  }, [uploadedFiles, setUploadedFiles]);

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
  const anyUploading = uploadedFiles.some((f) => f.uploadStatus === "uploading");
  const pendingValidation = uploadedFiles.filter(
    (f) => f.uploadStatus === "uploaded" && f.validationStatus === "pending"
  );
  const validFiles = uploadedFiles.filter((f) => f.validationStatus === "valid");
  const canProceed =
    validFiles.length > 0 && !anyUploading && !isValidating;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* ── Validation Overlay ── */}
      <AnimatePresence>
        {validationProgress && (
          <motion.div
            key="validation-overlay"
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
                <ShieldCheck className="w-7 h-7 text-primary" />
              </div>

              <div className="text-center space-y-1">
                <p className="text-base font-semibold text-foreground">
                  Validando arquivo{validationProgress.total > 1 ? "s" : ""}…
                </p>
                <p className="text-sm text-muted-foreground">
                  {validationProgress.total > 1
                    ? `Arquivo ${validationProgress.current} de ${validationProgress.total}`
                    : validationProgress.step}
                </p>
                <p className="text-xs font-medium text-primary truncate max-w-[220px]">
                  {validationProgress.fileName}
                </p>
              </div>

              {validationProgress.total > 1 && (
                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <motion.div
                    className="h-full bg-primary rounded-full"
                    initial={{ width: 0 }}
                    animate={{
                      width: `${(validationProgress.current / validationProgress.total) * 100}%`,
                    }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              )}

              <p className="text-xs text-muted-foreground">
                {validationProgress.step}
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

      {/* ── Validate Button (when there are pending files) ── */}
      {pendingValidation.length > 0 && !isValidating && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-amber-200 bg-amber-50/30">
            <CardContent className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-amber-100 text-amber-600">
                  <FolderOpen className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {pendingValidation.length} arquivo(s) aguardando validação
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Clique para validar os cabeçalhos e extrair colunas via servidor
                  </p>
                </div>
              </div>
              <Button
                onClick={validateAllFiles}
                className="gap-2"
                disabled={anyUploading}
              >
                <PlayCircle className="w-4 h-4" />
                Validar Arquivos
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

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

                    {/* Upload status */}
                    {file.uploadStatus === "uploading" && (
                      <Badge variant="default" className="gap-1 bg-amber-50 text-amber-600 border-amber-200">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        {file.uploadProgress !== undefined
                          ? `${file.uploadProgress}% • ${formatBytes(file.size)}`
                          : "Enviando…"}
                      </Badge>
                    )}
                    {file.uploadStatus === "uploaded" && file.validationStatus === "pending" && (
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
                  {file.uploadStatus === "uploading" && file.uploadProgress !== undefined && (
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
            {(anyUploading || isValidating) && (
              <span className="flex items-center gap-1 text-amber-600">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />processando…
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {pendingValidation.length > 0 && !isValidating && (
              <Button
                variant="outline"
                onClick={validateAllFiles}
                className="gap-2"
                disabled={anyUploading}
              >
                <PlayCircle className="w-4 h-4" />
                Validar ({pendingValidation.length})
              </Button>
            )}
            <Button onClick={proceed} className="gap-2" disabled={!canProceed}>
              {isValidating || anyUploading ? (
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