/**
 * Page 1: Upload (Carregamento)
 *
 * Flow per file:
 *  1. User drops / selects Excel files
 *  2. File is parsed locally (SheetJS) for instant preview
 *  3. File is uploaded to Supabase Storage  temp/bases/<sessionId>/<file>
 *  4. Edge Function `validate-excel` checks if row 1 is a header
 *     → If invalid: file is rejected with an error message
 *  5. Edge Function `extract-columns` returns detailed column metadata
 *     (type detection, sample values, uniqueness)
 *  6. Results feed into field-mapper on the next step
 */
import { useCallback, useState } from "react";
import { useApp } from "@/context/AppContext";
import {
  parseExcelFile,
  uploadFileToStorage,
  callReadColumns,
  deleteFileFromStorage,
} from "@/services";
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
  CloudOff,
  Loader2,
  ShieldCheck,
  ShieldX,
  Columns3,
} from "lucide-react";
import { formatNumber } from "@/lib/utils";
import type { UploadedFile } from "@/types";

export function UploadPage() {
  const { uploadedFiles, setUploadedFiles, setCurrentStep } = useApp();
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabaseReady = isSupabaseConfigured();

  /**
   * Full pipeline per file:
   *  upload → validate-excel → extract-columns → update state
   */
  const processFile = async (
    file: File,
    parsed: UploadedFile
  ): Promise<UploadedFile> => {
    let result: UploadedFile = {
      ...parsed,
      uploadStatus: "pending",
      validationStatus: "pending",
    };

    if (!supabaseReady) return result;

    // ── Step 1: Upload to Storage ──
    try {
      result = { ...result, uploadStatus: "uploading" };
      const storageResult = await uploadFileToStorage(file, "bases");
      result = {
        ...result,
        storagePath: storageResult.path,
        uploadStatus: "uploaded",
      };
    } catch {
      return { ...result, uploadStatus: "error" };
    }

    // ── Step 2: Read columns (single edge function: validate + extract) ──
    try {
      result = { ...result, validationStatus: "validating" };
      const r = await callReadColumns(result.storagePath!, file.name);

      if (!r.valid) {
        // Invalid header or parse error → reject, remove from Storage
        await deleteFileFromStorage(result.storagePath!).catch(() => {});
        return {
          ...result,
          validationStatus: "invalid",
          validationError:
            r.error ?? "Cabeçalho inválido — a primeira linha não contém nomes de colunas válidos.",
          uploadStatus: "error",
        };
      }

      // Success — use server-side data (authoritative)
      result = {
        ...result,
        validationStatus: "valid",
        columns: r.columns ?? result.columns,
        columnInfo: r.columnInfo,
        rowCount: r.rowCount ?? result.rowCount,
        sheetName: r.sheetName,
        isVoltz: r.isVoltz || result.isVoltz,
      };
    } catch (e) {
      // Edge function unreachable → keep local parse data, allow proceeding
      console.warn("read-columns edge function failed:", e);
      result = { ...result, validationStatus: "error" };
    }

    return result;
  };

  const handleFiles = useCallback(
    async (fileList: FileList | File[]) => {
      setIsLoading(true);
      setError(null);
      const files = Array.from(fileList).filter(
        (f) => f.name.endsWith(".xlsx") || f.name.endsWith(".xls")
      );

      if (files.length === 0) {
        setError("Nenhum arquivo Excel válido (.xlsx, .xls) selecionado.");
        setIsLoading(false);
        return;
      }

      try {
        // Parse locally first (instant feedback)
        const parsed = await Promise.all(files.map(parseExcelFile));

        // Run full pipeline in parallel per file
        const processed = await Promise.all(
          parsed.map((p, i) => processFile(files[i], p))
        );

        // Separate valid and rejected
        const valid = processed.filter(
          (f) => f.validationStatus !== "invalid"
        );
        const rejected = processed.filter(
          (f) => f.validationStatus === "invalid"
        );

        if (rejected.length > 0) {
          const msgs = rejected
            .map((f) => `• ${f.name}: ${f.validationError}`)
            .join("\n");
          setError(
            `${rejected.length} arquivo(s) rejeitado(s):\n${msgs}`
          );
        }

        if (valid.length > 0) {
          setUploadedFiles([...uploadedFiles, ...valid]);
        }
      } catch (err) {
        setError(String(err));
      } finally {
        setIsLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [uploadedFiles, setUploadedFiles, supabaseReady]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const removeFile = async (id: string) => {
    const file = uploadedFiles.find((f) => f.id === id);
    if (file?.storagePath) {
      deleteFileFromStorage(file.storagePath).catch(() => {});
    }
    setUploadedFiles(uploadedFiles.filter((f) => f.id !== id));
  };

  const proceed = () => {
    if (uploadedFiles.length > 0) setCurrentStep(1);
  };

  // Only allow proceeding when all files passed validation (or Supabase isn't configured)
  const allValidated = uploadedFiles.every(
    (f) => f.validationStatus === "valid" || !supabaseReady
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* ── Header ── */}
      <div>
        <h2 className="text-2xl font-bold text-foreground">
          Carregamento de Dados
        </h2>
        <p className="text-muted-foreground mt-1">
          Faça upload dos arquivos Excel das distribuidoras para iniciar o
          processamento.
        </p>
      </div>

      {/* ── Drop Zone ── */}
      <Card className="overflow-hidden">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`
            relative flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-xl
            transition-all duration-300 cursor-pointer
            ${
              isDragging
                ? "border-primary bg-blue-50/50 scale-[1.01]"
                : "border-slate-200 hover:border-blue-300 hover:bg-slate-50/50"
            }
          `}
        >
          <div
            className={`
              flex items-center justify-center w-16 h-16 rounded-2xl mb-4 transition-all duration-300
              ${
                isDragging
                  ? "bg-primary text-white scale-110"
                  : "bg-slate-100 text-slate-400"
              }
            `}
          >
            <Upload className="w-7 h-7" />
          </div>

          <p className="text-base font-medium text-foreground mb-1">
            {isDragging
              ? "Solte os arquivos aqui"
              : "Arraste e solte seus arquivos Excel"}
          </p>
          <p className="text-sm text-muted-foreground mb-4">
            Formatos aceitos: .xlsx, .xls
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

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm rounded-xl"
            >
              <div className="flex flex-col items-center gap-3">
                <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-sm font-medium text-primary">
                  Enviando e validando…
                </span>
              </div>
            </motion.div>
          )}
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
            transition={{ delay: idx * 0.05 }}
          >
            <Card>
              <CardContent className="flex items-center gap-4 p-4">
                <div className="flex items-center justify-center w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>

                <div className="flex-1 min-w-0">
                  {/* ── Badges Row ── */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-medium truncate">
                      {file.name}
                    </p>

                    {file.isVoltz && (
                      <Badge variant="warning" className="gap-1">
                        <Zap className="w-3 h-3" />
                        VOLTZ
                      </Badge>
                    )}

                    {/* Storage badge */}
                    {file.uploadStatus === "uploaded" && (
                      <Badge
                        variant="default"
                        className="gap-1 bg-sky-100 text-sky-700 border-sky-200"
                      >
                        <Cloud className="w-3 h-3" />
                        Storage
                      </Badge>
                    )}
                    {file.uploadStatus === "uploading" && (
                      <Badge
                        variant="default"
                        className="gap-1 bg-amber-50 text-amber-600 border-amber-200"
                      >
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Enviando…
                      </Badge>
                    )}
                    {file.uploadStatus === "error" &&
                      file.validationStatus !== "invalid" && (
                        <Badge variant="destructive" className="gap-1">
                          <CloudOff className="w-3 h-3" />
                          Erro Storage
                        </Badge>
                      )}

                    {/* Validation badge */}
                    {file.validationStatus === "valid" && (
                      <Badge
                        variant="default"
                        className="gap-1 bg-emerald-50 text-emerald-700 border-emerald-200"
                      >
                        <ShieldCheck className="w-3 h-3" />
                        Validado
                      </Badge>
                    )}
                    {file.validationStatus === "validating" && (
                      <Badge
                        variant="default"
                        className="gap-1 bg-amber-50 text-amber-600 border-amber-200"
                      >
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Validando…
                      </Badge>
                    )}
                    {file.validationStatus === "invalid" && (
                      <Badge variant="destructive" className="gap-1">
                        <ShieldX className="w-3 h-3" />
                        Rejeitado
                      </Badge>
                    )}

                    {/* Column extraction badge */}
                    {file.columnInfo && file.columnInfo.length > 0 && (
                      <Badge
                        variant="default"
                        className="gap-1 bg-violet-50 text-violet-700 border-violet-200"
                      >
                        <Columns3 className="w-3 h-3" />
                        {file.columnInfo.length} colunas analisadas
                      </Badge>
                    )}
                  </div>

                  {/* ── Stats Row ── */}
                  <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                    <span>{formatNumber(file.rowCount, 0)} registros</span>
                    <span>{file.columns.length} colunas</span>
                    {file.sheetName && <span>Aba: {file.sheetName}</span>}
                    {file.detectedDate && (
                      <span>Data: {file.detectedDate}</span>
                    )}
                  </div>

                  {/* ── Validation Error ── */}
                  {file.validationError && (
                    <p className="mt-1 text-xs text-red-600">
                      {file.validationError}
                    </p>
                  )}
                </div>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeFile(file.id)}
                  className="text-slate-400 hover:text-red-500"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* ── Actions ── */}
      {uploadedFiles.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-between pt-4"
        >
          <div className="flex items-center gap-4">
            <p className="text-sm text-muted-foreground">
              {uploadedFiles.length} arquivo(s) carregado(s) —{" "}
              {formatNumber(
                uploadedFiles.reduce((acc, f) => acc + f.rowCount, 0),
                0
              )}{" "}
              registros totais
            </p>
            {supabaseReady && (
              <div className="flex items-center gap-1.5 text-xs text-sky-600">
                <Cloud className="w-3.5 h-3.5" />
                {
                  uploadedFiles.filter((f) => f.uploadStatus === "uploaded")
                    .length
                }
                /{uploadedFiles.length} no Storage
              </div>
            )}
            {supabaseReady && (
              <div className="flex items-center gap-1.5 text-xs text-emerald-600">
                <ShieldCheck className="w-3.5 h-3.5" />
                {
                  uploadedFiles.filter(
                    (f) => f.validationStatus === "valid"
                  ).length
                }
                /{uploadedFiles.length} validados
              </div>
            )}
          </div>
          <Button
            onClick={proceed}
            className="gap-2"
            disabled={!allValidated}
          >
            Próximo: Mapeamento
            <ArrowRight className="w-4 h-4" />
          </Button>
        </motion.div>
      )}
    </motion.div>
  );
}
