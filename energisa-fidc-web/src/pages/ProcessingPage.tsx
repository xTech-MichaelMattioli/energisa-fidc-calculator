/**
 * Page 4: Processing
 * Multi-step FIDC calculation pipeline with DB persistence.
 *
 * Steps:
 *   1. Ingestão de Dados   – CSV → DB table (via edge function)
 *   2. Cálculo de Aging    – dias_atraso + classificação (SQL)
 *   3. Correção Monetária  – multa, juros, correção, valor_corrigido (SQL)
 *   4. Valor Justo & RV    – taxa recuperação, VJ, desconto, VJR (SQL)
 *
 * After completion, shows summary cards + paginated results table.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useApp } from "@/context/AppContext";
import {
  runFullDbPipeline,
  getSummary,
  getResults,
  runPipeline,
} from "@/services";
import type {
  FidcSummary,
  SessionDataRow,
  ProcessingDbStep,
  ProcessingDbProgress,
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
  Calculator,
  BarChart3,
  Sparkles,
  Table2,
  ChevronLeft,
  ChevronRight,
  Zap,
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
  { key: "ingest", label: "Ingestão de Dados", icon: <Database className="w-4 h-4" /> },
  { key: "aging", label: "Cálculo de Aging", icon: <BarChart3 className="w-4 h-4" /> },
  { key: "correction", label: "Correção Monetária", icon: <Calculator className="w-4 h-4" /> },
  { key: "fair_value", label: "Valor Justo & RV", icon: <Sparkles className="w-4 h-4" /> },
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
  } = useApp();

  const [progress, setProgress] = useState<ProcessingDbProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [summary, setSummary] = useState<FidcSummary | null>(null);
  const [rowResults, setRowResults] = useState<SessionDataRow[]>([]);
  const [resultsPage, setResultsPage] = useState(0);
  const [resultsCount, setResultsCount] = useState(0);
  const [loadingResults, setLoadingResults] = useState(false);

  const stepLogRef = useRef<ProcessingDbProgress[]>([]);
  const PAGE_SIZE = 50;

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

  // Current step index for the stepper
  const currentStepIdx = useMemo(() => {
    if (!progress) return -1;
    return PIPELINE_STEPS_UI.findIndex((s) => s.key === progress.step);
  }, [progress]);

  // ── Load results after completion ──
  const loadResults = useCallback(
    async (page: number) => {
      if (!sessionId) return;
      setLoadingResults(true);
      try {
        const { data, count } = await getResults(sessionId, page, PAGE_SIZE);
        setRowResults(data);
        setResultsCount(count);
        setResultsPage(page);
      } catch {
        // silent
      } finally {
        setLoadingResults(false);
      }
    },
    [sessionId]
  );

  useEffect(() => {
    if (isDone && sessionId) {
      getSummary(sessionId).then(setSummary).catch(() => {});
      loadResults(0);
    }
  }, [isDone, sessionId, loadResults]);

  // ── Run pipeline ──
  const handleRun = useCallback(async () => {
    setError(null);
    setIsProcessing(true);
    stepLogRef.current = [];
    setProgress(null);
    setSummary(null);
    setRowResults([]);

    const onProgress = (p: ProcessingDbProgress) => {
      stepLogRef.current = [
        ...stepLogRef.current.filter((l) => l.step !== p.step),
        p,
      ];
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
          Execute o pipeline de cálculos FIDC no banco de dados: ingestão, aging, correção monetária, valor justo e remuneração variável.
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
                    ? "Os dados serão enviados ao banco e processados via SQL."
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
                        ) : entry.step === "aging" ? (
                          <BarChart3 className="w-3.5 h-3.5" />
                        ) : entry.step === "correction" ? (
                          <Calculator className="w-3.5 h-3.5" />
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

      {/* ── Summary Cards (after completion) ── */}
      <AnimatePresence>
        {isDone && summary && (
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
                  <SummaryCard label="Registros" value={formatNumber(summary.total_rows)} />
                  <SummaryCard label="VP Total" value={formatBRL(summary.total_valor_principal)} accent />
                  <SummaryCard label="VL Total" value={formatBRL(summary.total_valor_liquido)} />
                  <SummaryCard label="Correção" value={formatBRL(summary.total_correcao_monetaria)} />
                  <SummaryCard label="VC Total" value={formatBRL(summary.total_valor_corrigido)} accent />
                  <SummaryCard label="Multa" value={formatBRL(summary.total_multa)} />
                  <SummaryCard label="Juros Moratórios" value={formatBRL(summary.total_juros_moratorios)} />
                  <SummaryCard label="VJ Total" value={formatBRL(summary.total_valor_justo)} accent />
                  <SummaryCard label="Recuperável" value={formatBRL(summary.total_valor_recuperavel)} />
                  <SummaryCard label="VJ Reajustado" value={formatBRL(summary.total_valor_justo_reajustado)} accent />
                </div>
              </CardContent>
            </Card>

            {/* By Aging */}
            {summary.by_aging && Object.keys(summary.by_aging).length > 0 && (
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
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">VJR</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(summary.by_aging).map(([aging, data]) => (
                          <tr key={aging} className="border-b border-dashed last:border-0 hover:bg-slate-50">
                            <td className="py-1.5 px-2 font-medium">{aging}</td>
                            <td className="py-1.5 px-2 text-right">{formatNumber(data.count)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_principal)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_corrigido)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_justo)}</td>
                            <td className="py-1.5 px-2 text-right font-medium text-emerald-700">
                              {formatBRL(data.valor_justo_reajustado)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* By Empresa */}
            {summary.by_empresa && Object.keys(summary.by_empresa).length > 0 && (
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
                          <th className="text-right py-1.5 px-2 font-semibold text-muted-foreground">VJR</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(summary.by_empresa).map(([empresa, data]) => (
                          <tr key={empresa} className="border-b border-dashed last:border-0 hover:bg-slate-50">
                            <td className="py-1.5 px-2 font-medium flex items-center gap-1">
                              {empresa === "VOLTZ" && <Zap className="w-3 h-3 text-amber-500" />}
                              {empresa}
                            </td>
                            <td className="py-1.5 px-2 text-right">{formatNumber(data.count)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_principal)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_corrigido)}</td>
                            <td className="py-1.5 px-2 text-right">{formatBRL(data.valor_justo)}</td>
                            <td className="py-1.5 px-2 text-right font-medium text-emerald-700">
                              {formatBRL(data.valor_justo_reajustado)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ── Paginated Results Table ── */}
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-semibold text-foreground flex items-center gap-2">
                    <Table2 className="w-4 h-4 text-primary" />
                    Dados Calculados (linha a linha)
                  </p>
                  <span className="text-xs text-muted-foreground">
                    {resultsCount > 0
                      ? `${resultsPage * PAGE_SIZE + 1}–${Math.min((resultsPage + 1) * PAGE_SIZE, resultsCount)} de ${formatNumber(resultsCount)}`
                      : "Carregando..."}
                  </span>
                </div>

                <div className="overflow-x-auto max-h-[420px] overflow-y-auto">
                  <table className="w-full text-[11px] whitespace-nowrap">
                    <thead className="sticky top-0 bg-white z-10">
                      <tr className="border-b">
                        <th className="text-left py-1.5 px-1.5 font-semibold text-muted-foreground">#</th>
                        <th className="text-left py-1.5 px-1.5 font-semibold text-muted-foreground">Empresa</th>
                        <th className="text-left py-1.5 px-1.5 font-semibold text-muted-foreground">Tipo</th>
                        <th className="text-left py-1.5 px-1.5 font-semibold text-muted-foreground">Contrato</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">VP</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">VL</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">Dias</th>
                        <th className="text-left py-1.5 px-1.5 font-semibold text-muted-foreground">Aging</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">Multa</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">Juros</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">Correção</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">VC</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">TR%</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">VJ</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-muted-foreground">Desc%</th>
                        <th className="text-right py-1.5 px-1.5 font-semibold text-emerald-700">VJR</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loadingResults ? (
                        <tr>
                          <td colSpan={16} className="text-center py-8">
                            <Loader2 className="w-5 h-5 animate-spin mx-auto text-muted-foreground" />
                          </td>
                        </tr>
                      ) : rowResults.length === 0 ? (
                        <tr>
                          <td colSpan={16} className="text-center py-8 text-muted-foreground">
                            Nenhum resultado
                          </td>
                        </tr>
                      ) : (
                        rowResults.map((r) => (
                          <tr key={r.id} className="border-b border-dashed last:border-0 hover:bg-slate-50/50">
                            <td className="py-1 px-1.5 text-muted-foreground">{r.row_number}</td>
                            <td className="py-1 px-1.5 font-medium">
                              {r.is_voltz && <Zap className="w-3 h-3 text-amber-500 inline mr-0.5" />}
                              {r.empresa}
                            </td>
                            <td className="py-1 px-1.5">{r.tipo}</td>
                            <td className="py-1 px-1.5">{r.contrato}</td>
                            <td className="py-1 px-1.5 text-right">{formatBRL(r.valor_principal)}</td>
                            <td className="py-1 px-1.5 text-right">{formatBRL(r.valor_liquido)}</td>
                            <td className="py-1 px-1.5 text-right">{r.dias_atraso}</td>
                            <td className="py-1 px-1.5 text-[10px]">{r.aging}</td>
                            <td className="py-1 px-1.5 text-right">{formatBRL(r.multa)}</td>
                            <td className="py-1 px-1.5 text-right">{formatBRL(r.juros_moratorios)}</td>
                            <td className="py-1 px-1.5 text-right">{formatBRL(r.correcao_monetaria)}</td>
                            <td className="py-1 px-1.5 text-right font-medium">{formatBRL(r.valor_corrigido)}</td>
                            <td className="py-1 px-1.5 text-right">
                              {r.taxa_recuperacao != null ? `${(r.taxa_recuperacao * 100).toFixed(1)}%` : "-"}
                            </td>
                            <td className="py-1 px-1.5 text-right">{formatBRL(r.valor_justo)}</td>
                            <td className="py-1 px-1.5 text-right">
                              {r.desconto_aging != null ? `${(r.desconto_aging * 100).toFixed(1)}%` : "-"}
                            </td>
                            <td className="py-1 px-1.5 text-right font-medium text-emerald-700">
                              {formatBRL(r.valor_justo_reajustado)}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {resultsCount > PAGE_SIZE && (
                  <div className="flex items-center justify-between mt-3 pt-3 border-t">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadResults(resultsPage - 1)}
                      disabled={resultsPage === 0 || loadingResults}
                      className="gap-1"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                      Anterior
                    </Button>
                    <span className="text-xs text-muted-foreground">
                      Página {resultsPage + 1} de {Math.ceil(resultsCount / PAGE_SIZE)}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => loadResults(resultsPage + 1)}
                      disabled={
                        (resultsPage + 1) * PAGE_SIZE >= resultsCount || loadingResults
                      }
                      className="gap-1"
                    >
                      Próxima
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
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
                  <Button variant="destructive" size="sm" className="mt-3 gap-2" onClick={handleRun}>
                    <Play className="w-3.5 h-3.5" />
                    Tentar Novamente
                  </Button>
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
