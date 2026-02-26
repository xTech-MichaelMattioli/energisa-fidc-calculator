/**
 * Page 3: Indices Configuration
 * Upload IGP-M/IPCA, Recovery Rates, and DI-PRE files.
 */
import { useState } from "react";
import { useApp } from "@/context/AppContext";
import {
  parseIndicesExcel,
  parseRecoveryRatesExcel,
  parseDIPreFile,
} from "@/services";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  ArrowLeft,
  TrendingUp,
  Upload,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  Percent,
  FileText,
} from "lucide-react";
import type { RecoveryRate } from "@/types";
import { formatNumber } from "@/lib/utils";

interface UploadCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  accept?: string;
  isLoaded: boolean;
  loadedInfo?: string;
  onUpload: (file: File) => Promise<void>;
  error?: string | null;
}

function UploadCard({
  title,
  description,
  icon,
  accept = ".xlsx,.xls",
  isLoaded,
  loadedInfo,
  onUpload,
  error,
}: UploadCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleFile = async (files: FileList | null) => {
    if (!files?.[0]) return;
    setIsLoading(true);
    try {
      await onUpload(files[0]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className={`transition-all duration-300 ${isLoaded ? "border-emerald-200 bg-emerald-50/30" : ""}`}>
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div
            className={`
              flex items-center justify-center w-11 h-11 rounded-xl shrink-0 transition-colors
              ${isLoaded ? "bg-emerald-100 text-emerald-600" : "bg-slate-100 text-slate-400"}
            `}
          >
            {isLoaded ? <CheckCircle2 className="w-5 h-5" /> : icon}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-sm font-semibold">{title}</h3>
              {isLoaded && <Badge variant="success">Carregado</Badge>}
            </div>
            <p className="text-xs text-muted-foreground mb-3">{description}</p>

            {isLoaded && loadedInfo && (
              <p className="text-xs text-emerald-600 mb-2">{loadedInfo}</p>
            )}

            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="text-xs text-red-600 mb-2 flex items-center gap-1"
                >
                  <AlertCircle className="w-3 h-3" />
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <label className="cursor-pointer inline-block">
              <input
                type="file"
                accept={accept}
                className="hidden"
                onChange={(e) => handleFile(e.target.files)}
              />
              <Button
                variant={isLoaded ? "outline" : "default"}
                size="sm"
                asChild
                disabled={isLoading}
              >
                <span className="gap-2">
                  {isLoading ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      Processando...
                    </>
                  ) : (
                    <>
                      <Upload className="w-3.5 h-3.5" />
                      {isLoaded ? "Substituir Arquivo" : "Upload Arquivo"}
                    </>
                  )}
                </span>
              </Button>
            </label>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function IndicesPage() {
  const {
    indices,
    setIndices,
    recoveryRates,
    setRecoveryRates,
    diPreRates,
    setDiPreRates,
    setCurrentStep,
  } = useApp();

  const [errors, setErrors] = useState<Record<string, string | null>>({});

  const handleIndices = async (file: File) => {
    try {
      setErrors((e) => ({ ...e, indices: null }));
      const parsed = await parseIndicesExcel(file);
      setIndices(parsed);
    } catch (err) {
      setErrors((e) => ({ ...e, indices: String(err) }));
    }
  };

  const handleRecovery = async (file: File) => {
    try {
      setErrors((e) => ({ ...e, recovery: null }));
      const parsed = await parseRecoveryRatesExcel(file);
      setRecoveryRates(parsed as RecoveryRate[]);
    } catch (err) {
      setErrors((e) => ({ ...e, recovery: String(err) }));
    }
  };

  const handleDIPre = async (file: File) => {
    try {
      setErrors((e) => ({ ...e, dipre: null }));
      const parsed = await parseDIPreFile(file);
      setDiPreRates(parsed);
    } catch (err) {
      setErrors((e) => ({ ...e, dipre: String(err) }));
    }
  };

  const canProceed =
    indices.length > 0 && recoveryRates.length > 0 && diPreRates.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* ── Header ── */}
      <div>
        <h2 className="text-2xl font-bold text-foreground">Configuração de Índices</h2>
        <p className="text-muted-foreground mt-1">
          Carregue os arquivos de índices econômicos, taxas de recuperação e curva DI-PRE.
        </p>
      </div>

      {/* ── Upload Cards ── */}
      <div className="grid grid-cols-1 gap-4">
        <UploadCard
          title="Índices IGP-M / IPCA"
          description="Excel com colunas: Ano (C), Mês (D), Índice (F). Utilizado para correção monetária."
          icon={<TrendingUp className="w-5 h-5" />}
          isLoaded={indices.length > 0}
          loadedInfo={`${formatNumber(indices.length, 0)} índices carregados`}
          onUpload={handleIndices}
          error={errors.indices}
        />

        <UploadCard
          title="Taxas de Recuperação"
          description="Excel com aba 'Input' contendo taxas por empresa, tipo e aging."
          icon={<Percent className="w-5 h-5" />}
          isLoaded={recoveryRates.length > 0}
          loadedInfo={`${formatNumber(recoveryRates.length, 0)} taxas configuradas`}
          onUpload={handleRecovery}
          error={errors.recovery}
        />

        <UploadCard
          title="Curva DI × PRE (BMF)"
          description="Arquivo HTML/Excel da BMF com dias corridos, taxa 252 e taxa 360."
          icon={<BarChart3 className="w-5 h-5" />}
          accept=".xlsx,.xls,.html,.htm"
          isLoaded={diPreRates.length > 0}
          loadedInfo={`${formatNumber(diPreRates.length, 0)} pontos da curva`}
          onUpload={handleDIPre}
          error={errors.dipre}
        />
      </div>

      {/* ── Summary ── */}
      {canProceed && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Card className="border-emerald-200 bg-gradient-to-r from-emerald-50/50 to-green-50/50">
            <CardContent className="p-4 flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
              <div>
                <p className="text-sm font-medium text-emerald-800">
                  Todos os índices configurados
                </p>
                <p className="text-xs text-emerald-600">
                  {indices.length} índices • {recoveryRates.length} taxas • {diPreRates.length} pontos DI-PRE
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Actions ── */}
      <div className="flex items-center justify-between pt-4">
        <Button variant="outline" onClick={() => setCurrentStep(1)} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </Button>
        <Button onClick={() => setCurrentStep(3)} disabled={!canProceed} className="gap-2">
          Próximo: Processamento
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </motion.div>
  );
}
