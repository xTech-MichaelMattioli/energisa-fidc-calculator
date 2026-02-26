/**
 * Page 1: Upload (Carregamento)
 *
 * Progressive pipeline per file:
 *  1. Parse locally with SheetJS  → file appears in list immediately
 *  2. Upload to Supabase Storage   → Storage badge updates
 *  3. Edge Function `read-columns` → validates header + extracts column metadata
 *     - If invalid: file marked as rejected (can still be removed)
 *     - If valid:   columns / rowCount / columnInfo updated from server
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
  CheckCircle2,
} from "lucide-react";
import { formatNumber } from "@/lib/utils";
import type { UploadedFile } from "@/types";

export function UploadPage() {
  const { uploadedFiles, setUploadedFiles, setCurrentStep } = useApp();
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const supabaseReady = isSupabaseConfigured();

  const handleFiles = useCallback(
    async (fileList: FileList | File[]) => {
      setIsProcessing(true);
      setError(null);

      const files = Array.from(fileList).filter(
        (f) => f.name.endsWith(".xlsx") || f.name.endsWith(".xls")
      );

      if (files.length === 0) {
        setError("Nenhum arquivo Excel válido (.xlsx, .xls) selecionado.");
        setIsProcessing(false);
        return;
      }

      // ── Step 1: Parse locally → show immediately ─────────────────
      let parsed: UploadedFile[];
      try {
        parsed = await Promise.all(files.map(parseExcelFile));
      } catch (err) {
        setError(String(err));
        setIsProcessing(false);
        return;
      }

      // Add all parsed files to state right away so the user sees data
      const withInit: UploadedFile[] = parsed.map((p) => ({
        ...p,
        uploadStatus: supabaseReady ? "pending" : undefined,
        validationStatus: supabaseReady ? "pending" : undefined,
      }));

      setUploadedFiles((prev) => [...prev, ...withInit]);
      setIsProcessing(false); // local parse done — spinner off

      if (!supabaseReady) return; // no Supabase → stop here

      // ── Step 2 + 3: Upload → edge function (per file, parallel) ──
      for (const [i, parsed_item] of withInit.entries()) {
        const file = files[i];
        const id = parsed_item.id;

        // Run the async pipeline without blocking the loop
        (async () => {
          // 2a. Upload to Storage
          setUploadedFiles((prev) =>
            prev.map((f) =>
              f.id === id ? { ...f, uploadStatus: "uploading" } : f
            )
          );

          let storagePath: string;
          try {
            const storageResult = await uploadFileToStorage(file, "bases");
            storagePath = storageResult.path;
            setUploadedFiles((prev) =>
              prev.map((f) =>
                f.id === id
                  ? { ...f, storagePath, uploadStatus: "uploaded" }
                  : f
              )
            );
          } catch (uploadErr) {
            console.error("[upload] failed:", uploadErr);
            setUploadedFiles((prev) =>
              prev.map((f) =>
                f.id === id ? { ...f, uploadStatus: "error" } : f
              )
            );
            return; // skip edge function if upload failed
          }

          // 2b. Edge function: validate + extract columns
          setUploadedFiles((prev) =>
            prev.map((f) =>
              f.id === id ? { ...f, validationStatus: "validating" } : f
            )
          );

          try {
            const r = await callReadColumns(storagePath, file.name);

            if (!r.valid) {
              console.warn("[read-columns] invalid:", r.error);
              // Remove from Storage (best-effort)
              deleteFileFromStorage(storagePath).catch(() => {});
              setUploadedFiles((prev) =>
                prev.map((f) =>
                  f.id === id
                    ? {
                        ...f,
                        validationStatus: "invalid",
                        validationError:
                          r.error ??
                          "Cabeçalho inválido — a primeira linha não contém nomes de colunas.",
                        uploadStatus: "error",
                      }
                    : f
                )
              );
              return;
            }

            // Valid → update with server-side data (authoritative)
            console.info(
              `[read-columns] ok: ${r.columns?.length} cols, ${r.rowCount} rows`
            );
            setUploadedFiles((prev) =>
              prev.map((f) =>
                f.id === id
                  ? {
                      ...f,
                      validationStatus: "valid",
                      columns: r.columns ?? f.columns,
                      columnInfo: r.columnInfo,
                      rowCount: r.rowCount ?? f.rowCount,
                      sheetName: r.sheetName,
                      isVoltz: r.isVoltz || f.isVoltz,
                    }
                  : f
              )
            );
          } catch (efErr) {
            console.warn("[read-columns] edge function unreachable:", efErr);
            // Keep local data, mark validation as error (not invalid)
            setUploadedFiles((prev) =>
              prev.map((f) =>
                f.id === id ? { ...f, validationStatus: "error" } : f
              )
            );
          }
        })();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [supabaseReady]
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
    setUploadedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const proceed = () => {
    if (uploadedFiles.length > 0) setCurrentStep(1);
  };

  // Allow proceeding if all files are valid (or Supabase not configured, or validation errored but not rejected)
  const allReady = uploadedFiles.every(
    (f) =>
      !supabaseReady ||
      f.validationStatus === "valid" ||
      f.validationStatus === "error" // edge fn down → allow with local data
  );
  const anyPending = uploadedFiles.some(
    (f) =>
      supabaseReady &&
      (f.uploadStatus === "uploading" ||
        f.validationStatus === "validating" ||
        f.validationStatus === "pending")
  );

  const canProceed =
    uploadedFiles.length > 0 &&
    allReady &&
    !anyPending &&
    uploadedFiles.some((f) => f.validationStatus !== "invalid");

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
          Faça upload dos arquivos Excel das distribuidoras para iniciar o processamento.
        </p>
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

          {isProcessing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm rounded-xl"
            >
              <div className="flex flex-col items-center gap-3">
                <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-sm font-medium text-primary">Lendo arquivo…</span>
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
            transition={{ delay: idx * 0.04 }}
          >
            <Card className={file.validationStatus === "invalid" ? "border-red-200 bg-red-50/30" : ""}>
              <CardContent className="flex items-center gap-4 p-4">
                <div className={`flex items-center justify-center w-11 h-11 rounded-xl
                  ${file.validationStatus === "invalid"
                    ? "bg-red-100 text-red-500"
                    : "bg-emerald-50 text-emerald-600"}`}
                >
                  <FileSpreadsheet className="w-5 h-5" />
                </div>

                <div className="flex-1 min-w-0">
                  {/* Badges */}
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <p className="text-sm font-medium truncate">{file.name}</p>

                    {file.isVoltz && (
                      <Badge variant="warning" className="gap-1">
                        <Zap className="w-3 h-3" />VOLTZ
                      </Badge>
                    )}

                    {/* Local parse done (no Supabase) */}
                    {!supabaseReady && (
                      <Badge variant="default" className="gap-1 bg-slate-100 text-slate-600 border-slate-200">
                        <CheckCircle2 className="w-3 h-3" />Local
                      </Badge>
                    )}

                    {/* Storage badges */}
                    {file.uploadStatus === "uploading" && (
                      <Badge variant="default" className="gap-1 bg-amber-50 text-amber-600 border-amber-200">
                        <Loader2 className="w-3 h-3 animate-spin" />Enviando…
                      </Badge>
                    )}
                    {file.uploadStatus === "uploaded" && (
                      <Badge variant="default" className="gap-1 bg-sky-100 text-sky-700 border-sky-200">
                        <Cloud className="w-3 h-3" />Storage
                      </Badge>
                    )}
                    {file.uploadStatus === "error" && file.validationStatus !== "invalid" && (
                      <Badge variant="destructive" className="gap-1">
                        <CloudOff className="w-3 h-3" />Erro upload
                      </Badge>
                    )}

                    {/* Validation badges */}
                    {file.validationStatus === "pending" && file.uploadStatus === "uploaded" && (
                      <Badge variant="default" className="gap-1 bg-slate-100 text-slate-500 border-slate-200">
                        <Loader2 className="w-3 h-3 animate-spin" />Aguardando…
                      </Badge>
                    )}
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
                        <AlertCircle className="w-3 h-3" />Sem validação
                      </Badge>
                    )}

                    {/* Column info badge */}
                    {file.columnInfo && file.columnInfo.length > 0 && (
                      <Badge variant="default" className="gap-1 bg-violet-50 text-violet-700 border-violet-200">
                        <Columns3 className="w-3 h-3" />{file.columnInfo.length} colunas
                      </Badge>
                    )}
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className={file.rowCount === 0 ? "text-orange-500 font-medium" : ""}>
                      {formatNumber(file.rowCount, 0)} registros
                    </span>
                    <span>{file.columns.length} colunas</span>
                    {file.sheetName && <span>Aba: {file.sheetName}</span>}
                    {file.detectedDate && <span>Data: {file.detectedDate}</span>}
                  </div>

                  {/* Validation error */}
                  {file.validationError && (
                    <p className="mt-1 text-xs text-red-600">{file.validationError}</p>
                  )}
                </div>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeFile(file.id)}
                  className="text-slate-400 hover:text-red-500 shrink-0"
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
          <div className="flex items-center gap-4 text-xs flex-wrap">
            <span className="text-sm text-muted-foreground">
              {uploadedFiles.length} arquivo(s) —{" "}
              {formatNumber(uploadedFiles.reduce((a, f) => a + f.rowCount, 0), 0)} registros
            </span>
            {supabaseReady && (
              <span className="flex items-center gap-1 text-sky-600">
                <Cloud className="w-3.5 h-3.5" />
                {uploadedFiles.filter((f) => f.uploadStatus === "uploaded").length}/{uploadedFiles.length} no Storage
              </span>
            )}
            {supabaseReady && (
              <span className="flex items-center gap-1 text-emerald-600">
                <ShieldCheck className="w-3.5 h-3.5" />
                {uploadedFiles.filter((f) => f.validationStatus === "valid").length}/{uploadedFiles.length} validados
              </span>
            )}
            {anyPending && (
              <span className="flex items-center gap-1 text-amber-600">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />processando…
              </span>
            )}
          </div>

          <Button onClick={proceed} className="gap-2" disabled={!canProceed}>
            {anyPending ? (
              <><Loader2 className="w-4 h-4 animate-spin" />Aguardar…</>
            ) : (
              <>Próximo: Mapeamento<ArrowRight className="w-4 h-4" /></>
            )}
          </Button>
        </motion.div>
      )}
    </motion.div>
  );
}