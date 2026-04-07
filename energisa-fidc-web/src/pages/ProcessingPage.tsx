/**
 * Page 4: Processing
 * FIDC pipeline with DB persistence.
 *
 * Steps:
 *   1. Ingestão de Dados – CSV → fidc_session_data (via edge function)
 *   Results computed on-the-fly via vw_fidc_results view.
 *
 * After completion, shows summary cards + paginated results table.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useApp } from "@/context/AppContext";
import {
  runFullDbPipeline,
  runPipeline,
  triggerComputeJob,
  waitForJob,
  isWorkerConfigured,
} from "@/services";
import type {
  FidcSummary,
  ProcessingDbStep,
  ProcessingDbProgress,
  WorkerJobStatus,
} from "@/services";
import { isSupabaseConfigured } from "@/lib/supabase";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Play,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Database,
  Sparkles,
  Table2,
  Zap,
  BarChart3,
  Download,
} from "lucide-react";

// ─── Constants ────────────────────────────────────────────────────

const FIELD_LABELS: Record<string, string> = {
  empresa: "Empresa",
  tipo: "Tipo",
  status: "Status",
  situacao: "Situação",
  nome_cliente: "Nome Cliente",
  documento: "CPF/CNPJ",
  classe: "Classe",
  contrato: "Contrato/UC",
  valor_principal: "Valor Principal",
  valor_nao_cedido: "Valor Não Cedido",
  valor_terceiro: "Valor Terceiros",
  valor_cip: "Valor CIP",
  data_vencimento: "Data Vencimento",
};

interface PipelineStepDef {
  key: ProcessingDbStep;
  label: string;
  icon: React.ReactNode;
}

const PIPELINE_STEPS_UI: PipelineStepDef[] = [
  { key: "ingest", label: "Preparação", icon: <Database className="w-4 h-4" /> },
  { key: "complete", label: "Worker Railway", icon: <Sparkles className="w-4 h-4" /> },
];

function formatBRL(v: number | null | undefined): string {
  if (v == null) return "R$ 0,00";
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatNumber(v: number | null | undefined, decimals = 0): string {
  if (v == null) return "0";
  return v.toLocaleString("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

// ─── Component ────────────────────────────────────────────────────

export function ProcessingPage() {
  const {
    uploadedFiles,
    fieldMappings,
    mappedRecords,
    indices,
    recoveryRates,
    diPreRates,
    dataBase,
    isProcessing,
    setIsProcessing,
    setProcessingProgress,
    setResults,
    setCurrentStep,
    setDbSessionId,
    setProcessedAt,
    workerCsvUrl,
    setWorkerCsvUrl,
    workerSummary,
    setWorkerSummary,
  } = useApp();

  const [progress, setProgress] = useState<ProcessingDbProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [computePhase, setComputePhase] = useState<"idle" | "computing" | "done">("idle");
  const [computeProgress, setComputeProgress] = useState<{ done: number; total: number } | null>(null);

  const stepLogRef = useRef<ProcessingDbProgress[]>([]);
  const computeStartedRef = useRef<string | null>(null); // sessionId for which compute was started

  const useDbPipeline = isSupabaseConfigured();
  const isDone = progress?.step === "complete";

  // Derive column mapping table for display
  const columnMappings = useMemo(() => {
    const rows: { targetField: string; label: string; sourceCol: string; fileName: string; isVoltz: boolean }[] = [];
    const validFiles = uploadedFiles.filter((f) => f.validationStatus === "valid");

    for (const file of validFiles) {
      const mapping = fieldMappings[file.id];
      if (!mapping) continue;
      for (const [target, source] of Object.entries(mapping)) {
        if (source) {
          rows.push({
            targetField: target,
            label: FIELD_LABELS[target] || target,
            sourceCol: source,
            fileName: file.name,
            isVoltz: file.isVoltz,
          });
        }
      }
    }
    return rows;
  }, [uploadedFiles, fieldMappings]);

  const validFiles = useMemo(
    () => uploadedFiles.filter((f) => f.validationStatus === "valid"),
    [uploadedFiles]
  );

  // Current step index for the stepper ("setup" maps to ingest step)
  const currentStepIdx = useMemo(() => {
    if (!progress) return -1;
    const step = progress.step === "setup" ? "ingest" : progress.step;
    return PIPELINE_STEPS_UI.findIndex((s) => s.key === step);
  }, [progress]);

  // ── Worker compute phase ──
  const runComputePhase = useCallback(
    async (sid: string) => {
      if (!isWorkerConfigured()) return;
      setComputePhase("computing");
      setComputeProgress(null);
      try {
        const jobId = await triggerComputeJob(sid);

        await waitForJob(jobId, (status: WorkerJobStatus) => {
          if (status.rows_total != null) {
            setComputeProgress({
              done:  status.rows_done  ?? 0,
              total: status.rows_total ?? 0,
            });
          }
          if (status.status === "done") {
            if (status.csv_url)  setWorkerCsvUrl(status.csv_url);
            if (status.summary)  setWorkerSummary(status.summary as FidcSummary);
            setComputePhase("done");
          }
        });
      } catch (err) {
        console.error("Worker error:", err);
        setComputePhase("idle");
      }
    },
    [setWorkerCsvUrl, setWorkerSummary]
  );

  useEffect(() => {
    if (isDone && sessionId) {
      if (computeStartedRef.current !== sessionId) {
        computeStartedRef.current = sessionId;
        runComputePhase(sessionId);
      }
    }
  }, [isDone, sessionId, runComputePhase]);

  // ── Run pipeline ──
  const handleRun = useCallback(async () => {
    setError(null);
    setIsProcessing(true);
    stepLogRef.current = [];
    computeStartedRef.current = null;
    setProgress(null);
    setComputePhase("idle");
    setComputeProgress(null);
    setWorkerCsvUrl(null);
    setWorkerSummary(null);

    const onProgress = (p: ProcessingDbProgress) => {
      stepLogRef.current = [
        ...stepLogRef.current.filter((l) => l.step !== p.step),
        p,
      ];
      // Capture sessionId as soon as it arrives (before pipeline may fail)
      if (p.sessionId) {
        setSessionId(p.sessionId);
        setDbSessionId(p.sessionId);
      }
      setProgress({ ...p });
    };

    try {
      if (useDbPipeline) {
        // ── DB Pipeline ──
        const sid = await runFullDbPipeline(
          validFiles,
          fieldMappings,
          indices,
          recoveryRates,
          diPreRates,
          dataBase,
          onProgress
        );
        setSessionId(sid);
        setDbSessionId(sid);
        setProcessedAt(new Date().toISOString());
      } else {
        // ── Local Pipeline (fallback) ──
        const result = await runPipeline(
          { records: mappedRecords, indices, recoveryRates, diPreRates, dataBase },
          (p) => {
            onProgress({
              step: p.step as ProcessingDbStep,
              progress: p.progress,
              message: p.message,
              details: p.details,
            });
          }
        );
        setResults(result);
        onProgress({ step: "complete", progress: 100, message: "Pipeline finalizado com sucesso!" });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      onProgress({ step: "error", progress: 0, message: msg });
    } finally {
      setIsProcessing(false);
    }
  }, [
    validFiles,
    fieldMappings,
    mappedRecords,
    indices,
    recoveryRates,
    diPreRates,
    dataBase,
    useDbPipeline,
    setIsProcessing,
    setProcessingProgress,
    setResults,
    setDbSessionId,
    setProcessedAt,
  ]);

  // ─── RENDER ─────────────────────────────────────────────────────

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* ── Header ── */}
      <div>
        <h2 className="text-2xl font-bold text-foreground">Processamento</h2>
        <p className="text-muted-foreground mt-1">
          Os arquivos ficam no Storage. O worker Railway lê, calcula aging / correção / valor justo e devolve o CSV pronto para download.
        </p>
        {useDbPipeline && (
          <Badge variant="outline" className="mt-2 gap-1 bg-emerald-50 text-emerald-700 border-emerald-200">
            <Database className="w-3 h-3" />
            Processamento no banco de dados (Supabase)
          </Badge>
        )}
      </div>

      {/* ── Column Mapping Summary ── */}
      {!isProcessing && !isDone && columnMappings.length > 0 && (
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2 mb-3">
              <Table2 className="w-4 h-4 text-primary" />
              <p className="text-sm font-semibold text-foreground">
                Mapeamento de Colunas ({validFiles.length} arquivo{validFiles.length !== 1 ? "s" : ""})
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-1.5 px-2 font-semibold text-muted-foreground">Campo FIDC</th>
                    <th className="text-left py-1.5 px-2 font-semibold text-muted-foreground">Coluna Original</th>
                    <th className="text-left py-1.5 px-2 font-semibold text-muted-foreground">Arquivo</th>
                  </tr>
                </thead>
                <tbody>
                  {columnMappings.map((m, i) => (
                    <tr key={`${m.targetField}-${m.fileName}-${i}`} className="border-b border-dashed last:border-0">
                      <td className="py-1.5 px-2 font-medium text-foreground">{m.label}</td>
                      <td className="py-1.5 px-2">
                        <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">{m.sourceCol}</code>
                      </td>
                      <td className="py-1.5 px-2 text-muted-foreground flex items-center gap-1">
                        {m.isVoltz && <Zap className="w-3 h-3 text-amber-500" />}
                        {m.fileName}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── File Summary ── */}
      {!isProcessing && !isDone && (
        <Card>
          <CardContent className="p-5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-primary">{validFiles.length}</p>
                <p className="text-xs text-muted-foreground">Arquivos</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-primary">
                  {formatNumber(validFiles.reduce((a, f) => a + f.rowCount, 0))}
                </p>
                <p className="text-xs text-muted-foreground">Registros (est.)</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-primary">{indices.length}</p>
                <p className="text-xs text-muted-foreground">Índices</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-primary">{recoveryRates.length}</p>
                <p className="text-xs text-muted-foreground">Taxas Recuperação</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Start Button ── */}
      {!isProcessing && !isDone && !error && (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
          <Card className="border-dashed">
            <CardContent className="p-8 flex flex-col items-center text-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
                <Play className="w-7 h-7 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">Pronto para processar</p>
                <p className="text-xs text-muted-foreground">
                  {useDbPipeline
                    ? "Os arquivos serão enviados ao Railway worker que calculará tudo diretamente do Storage."
                    : "O cálculo será realizado localmente no navegador."}
                </p>
              </div>
              <Button
                size="lg"
                onClick={handleRun}
                className="gap-2"
                disabled={validFiles.length === 0}
              >
                <Play className="w-4 h-4" />
                Iniciar Processamento
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Pipeline Stepper + Progress ── */}
      {(isProcessing || isDone) && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
          {/* Stepper */}
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-4">
                {PIPELINE_STEPS_UI.map((step, i) => {
                  const isActive = currentStepIdx === i;
                  const isCompleted = currentStepIdx > i || isDone;

                  return (
                    <div key={step.key} className="flex-1 flex items-center">
                      <div className="flex flex-col items-center flex-1">
                        <div
                          className={`
                            w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300
                            ${
                              isCompleted
                                ? "bg-emerald-100 text-emerald-600"
                                : isActive
                                ? "bg-primary/10 text-primary ring-2 ring-primary/30"
                                : "bg-slate-100 text-slate-400"
                            }
                          `}
                        >
                          {isCompleted ? (
                            <CheckCircle2 className="w-5 h-5" />
                          ) : isActive ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            step.icon
                          )}
                        </div>
                        <p
                          className={`text-[10px] mt-1.5 font-medium text-center leading-tight ${
                            isCompleted
                              ? "text-emerald-700"
                              : isActive
                              ? "text-primary"
                              : "text-muted-foreground"
                          }`}
                        >
                          {step.label}
                        </p>
                      </div>
                      {i < PIPELINE_STEPS_UI.length - 1 && (
                        <div
                          className={`h-0.5 flex-1 mx-1 mt-[-16px] rounded transition-colors duration-300 ${
                            currentStepIdx > i || isDone
                              ? "bg-emerald-300"
                              : "bg-slate-200"
                          }`}
                        />
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Progress bar */}
              <Progress value={progress?.progress ?? 0} className="h-2" />

              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-2">
                  {isProcessing ? (
                    <Loader2 className="w-4 h-4 text-primary animate-spin" />
                  ) : isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  ) : null}
                  <span className="text-sm font-medium">
                    {progress?.message ?? "Preparando..."}
                  </span>
                </div>
                <Badge variant="outline">
                  {Math.round(progress?.progress ?? 0)}%
                </Badge>
              </div>

              {progress?.details && (
                <p className="text-xs text-muted-foreground mt-1 whitespace-pre-line">
                  {progress.details}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Step Log */}
          <Card>
            <CardContent className="p-4">
              <p className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
                Log de Processamento
              </p>
              <div className="space-y-2">
                <AnimatePresence>
                  {stepLogRef.current.map((entry, i) => (
                    <motion.div
                      key={entry.step}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-start gap-2 text-xs"
                    >
                      <div
                        className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 ${
                          entry.step === "complete"
                            ? "bg-emerald-100 text-emerald-600"
                            : entry.step === "error"
                            ? "bg-red-100 text-red-600"
                            : "bg-blue-100 text-blue-600"
                        }`}
                      >
                        {entry.step === "complete" ? (
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        ) : entry.step === "error" ? (
                          <AlertCircle className="w-3.5 h-3.5" />
                        ) : entry.step === "ingest" ? (
                          <Database className="w-3.5 h-3.5" />
                        ) : (
                          <Sparkles className="w-3.5 h-3.5" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="font-medium text-foreground">{entry.message}</span>
                        {entry.details && (
                          <p className="text-muted-foreground mt-0.5 whitespace-pre-line break-all">
                            {entry.details}
                          </p>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Worker Compute Phase ── */}
      {isDone && computePhase !== "idle" && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card className={computePhase === "done" ? "border-emerald-200 bg-emerald-50/20" : ""}>
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                {computePhase === "computing" ? (
                  <Loader2 className="w-4 h-4 text-primary animate-spin" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                )}
                <p className="text-sm font-semibold text-foreground">
                  {computePhase === "computing"
                    ? "Calculando valores via worker (Railway)..."
                    : "CSV pronto para download"}
                </p>
                {computeProgress && (
                  <span className="text-xs text-muted-foreground ml-auto">
                    {formatNumber(computeProgress.done)} / {formatNumber(computeProgress.total)} linhas
                  </span>
                )}
              </div>
              {computePhase === "computing" && computeProgress && (
                <Progress
                  value={
                    computeProgress.total > 0
                      ? (computeProgress.done / computeProgress.total) * 100
                      : 0
                  }
                  className="h-2"
                />
              )}
              {computePhase === "done" && workerCsvUrl && (
                <Button
                  size="sm"
                  className="gap-2 mt-1"
                  onClick={() => {
                    const a = document.createElement("a");
                    a.href = workerCsvUrl;
                    a.download = `fidc_resultados_${sessionId ?? "export"}.csv`;
                    a.click();
                  }}
                >
                  <Download className="w-4 h-4" />
                  Download CSV ({formatNumber(computeProgress?.total)} linhas)
                </Button>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Summary Cards (após worker terminar) ── */}
      <AnimatePresence>
        {computePhase === "done" && workerSummary && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            <Card className="border-emerald-200 bg-emerald-50/20">
              <CardContent className="p-5">
                <p className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-600" />
                  Resumo dos Cálculos
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                  <SummaryCard label="Registros" value={formatNumber(workerSummary.total_rows)} />
                  <SummaryCard label="VP Total" value={formatBRL(workerSummary.total_valor_principal)} accent />
                  <SummaryCard label="VL Total" value={formatBRL(workerSummary.total_valor_liquido)} />
                  <SummaryCard label="Correção" value={formatBRL(workerSummary.total_correcao_monetaria)} />
                  <SummaryCard label="VC Total" value={formatBRL(workerSummary.total_valor_corrigido)} accent />
                  <SummaryCard label="Multa" value={formatBRL(workerSummary.total_multa)} />
                  <SummaryCard label="Juros Moratórios" value={formatBRL(workerSummary.total_juros_moratorios)} />
                  <SummaryCard label="Valor Justo" value={formatBRL(workerSummary.total_valor_justo)} accent />
                  <SummaryCard label="Recuperável" value={formatBRL(workerSummary.total_valor_recuperavel)} />
                </div>
              </CardContent>
            </Card>

            {/* By Aging */}
            {workerSummary.by_aging && Object.keys(workerSummary.by_aging).length > 0 && (
              <Card>
                <CardContent className="p-5">
                  <p className="text-sm font-semibold text-foreground mb-3">Breakdown por Aging</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-1.5 px-2 font-semibold text-muted-foreground">Aging</th>
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">Qtd</th>
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">VP</th>
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">VC</th>
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">VJ</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(workerSummary.by_aging).map(([aging, data]) => (
                          <tr key={aging} className="border-b border-dashed last:border-0 hover:bg-slate-50">
                            <td className="py-1.5 px-2 font-medium">{aging}</td>
                            <td className="py-1.5 px-2 text-right">{formatNumber(data.count)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_principal)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_corrigido)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_justo)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* By Empresa */}
            {workerSummary.by_empresa && Object.keys(workerSummary.by_empresa).length > 0 && (
              <Card>
                <CardContent className="p-5">
                  <p className="text-sm font-semibold text-foreground mb-3">Breakdown por Empresa</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-1.5 px-2 font-semibold text-muted-foreground">Empresa</th>
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">Qtd</th>
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">VP</th>
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">VC</th>
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">VJ</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(workerSummary.by_empresa).map(([empresa, data]) => (
                          <tr key={empresa} className="border-b border-dashed last:border-0 hover:bg-slate-50">
                            <td className="py-1.5 px-2 font-medium flex items-center gap-1">
                              {empresa === "VOLTZ" && <Zap className="w-3 h-3 text-amber-500" />}
                              {empresa}
                            </td>
                            <td className="py-1.5 px-2 text-right">{formatNumber(data.count)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_principal)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_corrigido)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_justo)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Error ── */}
      <AnimatePresence>
        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Card className="border-red-200 bg-red-50/50">
              <CardContent className="p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800">Erro no processamento</p>
                  <p className="text-xs text-red-600 mt-1 whitespace-pre-wrap">{error}</p>
                  <div className="flex items-center gap-2 mt-3 flex-wrap">
                    <Button
                      variant="destructive"
                      size="sm"
                      className="gap-2"
                      onClick={handleRun}
                    >
                      <Play className="w-3.5 h-3.5" />
                      Tentar Novamente
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Actions ── */}
      <div className="flex items-center justify-between pt-4">
        <Button
          variant="outline"
          onClick={() => setCurrentStep(2)}
          disabled={isProcessing}
          className="gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </Button>
        <Button
          onClick={() => setCurrentStep(4)}
          disabled={!isDone}
          className="gap-2"
        >
          Ver Resultados
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </motion.div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────

function SummaryCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="text-center">
      <p
        className={`text-base font-bold truncate ${
          accent ? "text-primary" : "text-foreground"
        }`}
      >
        {value}
      </p>
      <p className="text-[10px] text-muted-foreground mt-0.5">{label}</p>
    </div>
  );
}
