/**
 * Page 4: Processing
 * Runs the full FIDC calculation pipeline with animated progress.
 */
import { useCallback, useRef, useState } from "react";
import { useApp } from "@/context/AppContext";
import { runPipeline } from "@/services";
import type { ProcessingProgress } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  Play,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Zap,
  Database,
  Calculator,
  BarChart3,
  Sparkles,
} from "lucide-react";

const STEP_ICONS: Record<string, React.ReactNode> = {
  validação: <Database className="w-4 h-4" />,
  aging: <BarChart3 className="w-4 h-4" />,
  "correção (distribuidoras)": <Calculator className="w-4 h-4" />,
  "correção (voltz)": <Zap className="w-4 h-4" />,
  "valor justo": <Sparkles className="w-4 h-4" />,
  "remuneração variável": <Sparkles className="w-4 h-4" />,
  finalização: <CheckCircle2 className="w-4 h-4" />,
};

function getStepIcon(step: string) {
  const key = step.toLowerCase();
  for (const [k, v] of Object.entries(STEP_ICONS)) {
    if (key.includes(k)) return v;
  }
  return <Calculator className="w-4 h-4" />;
}

export function ProcessingPage() {
  const {
    mappedRecords,
    indices,
    recoveryRates,
    diPreRates,
    dataBase,
    isProcessing,
    setIsProcessing,
    processingProgress,
    setProcessingProgress,
    setResults,
    setCurrentStep,
  } = useApp();

  const logRef = useRef<ProcessingProgress[]>([]);
  const hasResults = useRef(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = useCallback(async () => {
    setError(null);
    setIsProcessing(true);
    logRef.current = [];
    hasResults.current = false;

    try {
      const result = await runPipeline(
        {
          records: mappedRecords,
          indices,
          recoveryRates,
          diPreRates,
          dataBase,
        },
        (progress) => {
          logRef.current = [...logRef.current.filter((l) => l.step !== progress.step), progress];
          setProcessingProgress({ ...progress });
        }
      );

      setResults(result);
      hasResults.current = true;
      setProcessingProgress({ step: "complete", progress: 100, message: "Pipeline finalizado com sucesso!" });
    } catch (err) {
      setError(String(err));
      setProcessingProgress({ step: "error", progress: 0, message: String(err) });
    } finally {
      setIsProcessing(false);
    }
  }, [mappedRecords, indices, recoveryRates, diPreRates, dataBase, setIsProcessing, setProcessingProgress, setResults]);

  const isDone = processingProgress?.progress === 100 && processingProgress?.step === "complete";

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
          Execute o pipeline de cálculos FIDC: aging, correção monetária, valor justo e remuneração variável.
        </p>
      </div>

      {/* ── Summary before run ── */}
      <Card>
        <CardContent className="p-5">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-primary">{mappedRecords.length}</p>
              <p className="text-xs text-muted-foreground">Registros</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-primary">{indices.length}</p>
              <p className="text-xs text-muted-foreground">Índices</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-primary">{recoveryRates.length}</p>
              <p className="text-xs text-muted-foreground">Taxas Recuperação</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-primary">{diPreRates.length}</p>
              <p className="text-xs text-muted-foreground">Pontos DI-PRE</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Start / Progress ── */}
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
                  O cálculo será realizado localmente no navegador.
                </p>
              </div>
              <Button size="lg" onClick={handleRun} className="gap-2">
                <Play className="w-4 h-4" />
                Iniciar Processamento
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Progress Indicator ── */}
      {(isProcessing || isDone) && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
          <Card>
            <CardContent className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isProcessing ? (
                    <Loader2 className="w-4 h-4 text-primary animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  )}
                  <span className="text-sm font-medium">
                    {processingProgress?.step || "Iniciando..."}
                  </span>
                </div>
                <Badge variant={isDone ? "success" : "default"}>
                  {Math.round(processingProgress?.progress ?? 0)}%
                </Badge>
              </div>

              <Progress value={processingProgress?.progress ?? 0} />

              <p className="text-xs text-muted-foreground">
                {processingProgress?.message || "Preparando..."}
              </p>
            </CardContent>
          </Card>

          {/* ── Step Log ── */}
          <Card>
            <CardContent className="p-4">
              <p className="text-xs font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
                Log de Processamento
              </p>
              <div className="space-y-2">
                <AnimatePresence>
                  {logRef.current.map((entry, i) => (
                    <motion.div
                      key={entry.step}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="flex items-center gap-2 text-xs"
                    >
                      <div
                        className={`
                          w-6 h-6 rounded-lg flex items-center justify-center shrink-0
                          ${entry.progress >= 100 ? "bg-emerald-100 text-emerald-600" : "bg-blue-100 text-blue-600"}
                        `}
                      >
                        {getStepIcon(entry.step)}
                      </div>
                      <span className="font-medium text-foreground">{entry.step}</span>
                      <span className="text-muted-foreground truncate flex-1">{entry.message}</span>
                      {entry.progress >= 100 && (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Error ── */}
      <AnimatePresence>
        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Card className="border-red-200 bg-red-50/50">
              <CardContent className="p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-800">Erro no processamento</p>
                  <p className="text-xs text-red-600 mt-1">{error}</p>
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
        <Button variant="outline" onClick={() => setCurrentStep(2)} disabled={isProcessing} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </Button>
        <Button onClick={() => setCurrentStep(4)} disabled={!isDone} className="gap-2">
          Ver Resultados
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </motion.div>
  );
}
