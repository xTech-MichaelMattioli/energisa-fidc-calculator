/**
 * Page 5: Results
 * Full calculation results with every intermediate column exposed for manual
 * verification. Export to CSV with all columns, processing date, and
 * "processado" filename suffix.
 *
 * Column groups (mirroring the calculation pipeline):
 *   1. Dados Originais     – empresa, tipo, classe, contrato, VP, etc.
 *   2. Aging               – dias_atraso, aging, aging_taxa
 *   3. Correção Monetária  – VL, multa, juros_moratórios, fator_correção,
 *                            correção_monetária, VC, juros_remuneratórios, SDV
 *   4. Valor Justo         – taxa_recuperação, prazo, V.recuperável, Valor Justo
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useApp } from "@/context/AppContext";
import {
  exportToCSV,
  getResults,
  getAllResultsForExport,
  getCurrentSessionId,
  getLatestSessionJob,
  isWorkerConfigured,
} from "@/services";
import type { FidcSummary, SessionDataRow } from "@/services";
import { isSupabaseConfigured } from "@/lib/supabase";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Download,
  DollarSign,
  FileSpreadsheet,
  TrendingUp,
  BarChart3,
  Users,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Zap,
  Calendar,
  Table2,
  CheckCircle2,
} from "lucide-react";
import { formatBRL, formatNumber } from "@/lib/utils";
import type { FinalRecord } from "@/types";

// ─── Column definitions for the full-detail table ─────────────────

interface ColDef {
  key: keyof SessionDataRow;
  label: string;
  group: "original" | "aging" | "correcao" | "vj";
  align?: "left" | "right";
  fmt?: (v: unknown) => string;
}

const fmtBRL = (v: unknown) =>
  v != null && typeof v === "number"
    ? v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
    : "R$ 0,00";

const fmtPct = (v: unknown) =>
  v != null && typeof v === "number" ? `${(v * 100).toFixed(2)}%` : "-";

const fmtNum = (v: unknown) =>
  v != null && typeof v === "number"
    ? v.toLocaleString("pt-BR", { maximumFractionDigits: 6 })
    : "-";

const DB_COLUMNS: ColDef[] = [
  // ── Dados Originais ──
  { key: "row_number", label: "#", group: "original", align: "right" },
  { key: "file_name", label: "Arquivo", group: "original" },
  { key: "empresa", label: "Empresa", group: "original" },
  { key: "tipo", label: "Tipo", group: "original" },
  { key: "status_conta", label: "Status", group: "original" },
  { key: "situacao", label: "Situação", group: "original" },
  { key: "nome_cliente", label: "Cliente", group: "original" },
  { key: "documento", label: "Documento", group: "original" },
  { key: "classe", label: "Classe", group: "original" },
  { key: "contrato", label: "Contrato", group: "original" },
  { key: "valor_principal", label: "VP (R$)", group: "original", align: "right", fmt: fmtBRL },
  { key: "valor_nao_cedido", label: "V.Não Cedido", group: "original", align: "right", fmt: fmtBRL },
  { key: "valor_terceiro", label: "V.Terceiros", group: "original", align: "right", fmt: fmtBRL },
  { key: "valor_cip", label: "V.CIP", group: "original", align: "right", fmt: fmtBRL },
  { key: "data_vencimento", label: "Vencimento", group: "original" },
  { key: "data_base", label: "Data Base", group: "original" },
  { key: "base_origem", label: "Origem", group: "original" },
  { key: "is_voltz", label: "VOLTZ?", group: "original", fmt: (v) => (v ? "Sim" : "Não") },
  // ── Aging ──
  { key: "dias_atraso", label: "Dias Atraso", group: "aging", align: "right", fmt: fmtNum },
  { key: "aging", label: "Aging", group: "aging" },
  { key: "aging_taxa", label: "Aging Taxa", group: "aging" },
  // ── Correção Monetária ──
  { key: "valor_liquido", label: "VL (R$)", group: "correcao", align: "right", fmt: fmtBRL },
  { key: "multa", label: "Multa (R$)", group: "correcao", align: "right", fmt: fmtBRL },
  { key: "juros_moratorios", label: "Juros Mora (R$)", group: "correcao", align: "right", fmt: fmtBRL },
  { key: "fator_correcao", label: "Fator Correção", group: "correcao", align: "right", fmt: fmtNum },
  { key: "correcao_monetaria", label: "Correção (R$)", group: "correcao", align: "right", fmt: fmtBRL },
  { key: "valor_corrigido", label: "VC (R$)", group: "correcao", align: "right", fmt: fmtBRL },
  { key: "juros_remuneratorios", label: "Juros Remun. (R$)", group: "correcao", align: "right", fmt: fmtBRL },
  { key: "saldo_devedor_vencimento", label: "SDV (R$)", group: "correcao", align: "right", fmt: fmtBRL },
  // ── Valor Justo ──
  { key: "taxa_recuperacao", label: "Taxa Recup.", group: "vj", align: "right", fmt: fmtPct },
  { key: "prazo_recebimento", label: "Prazo (meses)", group: "vj", align: "right", fmt: fmtNum },
  { key: "valor_recuperavel", label: "V.Recuperável (R$)", group: "vj", align: "right", fmt: fmtBRL },
  { key: "valor_justo", label: "Valor Justo (R$)", group: "vj", align: "right", fmt: fmtBRL },
];

const GROUP_COLORS: Record<string, string> = {
  original: "bg-slate-50",
  aging: "bg-violet-50",
  correcao: "bg-amber-50",
  vj: "bg-emerald-50",
};

const GROUP_LABELS: Record<string, string> = {
  original: "Dados Originais",
  aging: "Aging",
  correcao: "Correção Monetária",
  vj: "Valor Justo",
};

// ─── CSV export column ordering (human-readable headers, PT-BR) ──

const CSV_HEADERS: Record<string, string> = {
  row_number: "Nº Linha",
  file_name: "Arquivo Origem",
  empresa: "Empresa",
  tipo: "Tipo",
  status_conta: "Status Conta",
  situacao: "Situação",
  nome_cliente: "Nome Cliente",
  documento: "CPF/CNPJ",
  classe: "Classe",
  contrato: "Contrato/UC",
  valor_principal: "Valor Principal (R$)",
  valor_nao_cedido: "Valor Não Cedido (R$)",
  valor_terceiro: "Valor Terceiros (R$)",
  valor_cip: "Valor CIP (R$)",
  data_vencimento: "Data Vencimento",
  data_base: "Data Base",
  base_origem: "Base Origem",
  is_voltz: "É VOLTZ",
  dias_atraso: "Dias de Atraso",
  aging: "Faixa Aging",
  aging_taxa: "Aging (Taxa Lookup)",
  valor_liquido: "Valor Líquido (R$)",
  multa: "Multa 2% (R$)",
  juros_moratorios: "Juros Moratórios (R$)",
  fator_correcao: "Fator de Correção",
  correcao_monetaria: "Correção Monetária (R$)",
  valor_corrigido: "Valor Corrigido (R$)",
  juros_remuneratorios: "Juros Remuneratórios (R$)",
  saldo_devedor_vencimento: "Saldo Devedor Vencimento (R$)",
  taxa_recuperacao: "Taxa de Recuperação",
  prazo_recebimento: "Prazo Recebimento (meses)",
  valor_recuperavel: "Valor Recuperável (R$)",
  valor_justo: "Valor Justo (R$)",
};

const CSV_KEY_ORDER = DB_COLUMNS.map((c) => c.key);

const PAGE_SIZE = 50;

// ─── Helpers ──────────────────────────────────────────────────────

function buildExportFilename(
  originalFiles: string[],
  processedAt: string | null
): string {
  const date = processedAt
    ? new Date(processedAt)
    : new Date();
  const ts = date
    .toISOString()
    .replace(/[-:T]/g, "")
    .slice(0, 14); // YYYYMMDDHHmmss

  const baseName =
    originalFiles.length === 1
      ? originalFiles[0].replace(/\.[^.]+$/, "")
      : "FIDC_Dados";

  return `${baseName}_processado_${ts}.csv`;
}

function formatDateBR(iso: string | null | undefined): string {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ─── Metric Card ──────────────────────────────────────────────────

interface MetricCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  color: string;
  delay?: number;
}

function MetricCard({ label, value, icon, color, delay = 0 }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
    >
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4 flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${color}`}
          >
            {icon}
          </div>
          <div className="min-w-0">
            <p className="text-xs text-muted-foreground truncate">{label}</p>
            <p className="text-lg font-bold text-foreground truncate">{value}</p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ─── Export logic (builds CSV manually for full control) ──────────

function exportSessionDataToCsv(
  rows: SessionDataRow[],
  filename: string,
  processedAt: string | null
): void {
  if (rows.length === 0) return;

  const sep = ";";
  const headerRow = CSV_KEY_ORDER.map((k) => CSV_HEADERS[k] ?? k).join(sep);

  // Add a metadata row with processing timestamp
  const metaRow = `# Processado em: ${formatDateBR(processedAt)} | Total registros: ${rows.length}`;

  const dataRows = rows.map((row) =>
    CSV_KEY_ORDER.map((key) => {
      const val = row[key];
      if (val == null) return "";
      if (typeof val === "number") return val.toFixed(6).replace(".", ",");
      if (typeof val === "boolean") return val ? "Sim" : "Não";
      // Escape strings with semicolons or quotes
      const s = String(val);
      if (s.includes(sep) || s.includes('"') || s.includes("\n")) {
        return `"${s.replace(/"/g, '""')}"`;
      }
      return s;
    }).join(sep)
  );

  const bom = "\uFEFF";
  const csv = [metaRow, headerRow, ...dataRows].join("\n");
  const blob = new Blob([bom + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ═══════════════════════════════════════════════════════════════════
//  COMPONENT
// ═══════════════════════════════════════════════════════════════════

export function ResultsPage() {
  const {
    results,
    uploadedFiles,
    setCurrentStep,
    dbSessionId,
    processedAt,
    workerCsvUrl,
    setWorkerCsvUrl,
    workerSummary,
    setWorkerSummary,
  } = useApp();

  const useDb = isSupabaseConfigured() && !!dbSessionId;

  // ── DB state ──
  const [dbRows, setDbRows] = useState<SessionDataRow[]>([]);
  const [dbCount, setDbCount] = useState(0);
  const [dbPage, setDbPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);

  // ── Load page of DB results ──
  const loadPage = useCallback(
    async (page: number) => {
      if (!dbSessionId) return;
      setLoading(true);
      try {
        const { data, count } = await getResults(dbSessionId, page, PAGE_SIZE);
        setDbRows(data);
        setDbCount(count);
        setDbPage(page);
      } catch {
        // silent
      } finally {
        setLoading(false);
      }
    },
    [dbSessionId]
  );

  // ── Initial load (só carrega tabela paginada se houver dados no DB) ──
  useEffect(() => {
    if (useDb && dbSessionId) {
      loadPage(0);
    }
  }, [useDb, dbSessionId, loadPage]);

  // ── Recupera csv_url + summary do worker se perdidos na navegação ──
  useEffect(() => {
    const missing = !workerCsvUrl || !workerSummary;
    if (missing && dbSessionId && isWorkerConfigured()) {
      getLatestSessionJob(dbSessionId).then((job) => {
        if (job?.status === "done") {
          if (job.csv_url  && !workerCsvUrl)  setWorkerCsvUrl(job.csv_url);
          if (job.summary  && !workerSummary) setWorkerSummary(job.summary as FidcSummary);
        }
      }).catch(() => {});
    }
  }, [dbSessionId, workerCsvUrl, workerSummary, setWorkerCsvUrl, setWorkerSummary]);

  // ── Local-mode metrics ──
  const localMetrics = useMemo(() => {
    if (useDb || !results.length) return null;
    return {
      total: results.length,
      totalPrincipal: results.reduce((s, r) => s + (r.valor_principal || 0), 0),
      totalCorrigido: results.reduce((s, r) => s + (r.valor_corrigido || 0), 0),
      totalJusto: results.reduce((s, r) => s + (r.valor_justo || 0), 0),
    };
  }, [useDb, results]);

  // ── File names ──
  const fileNames = useMemo(
    () =>
      uploadedFiles
        .filter((f) => f.validationStatus === "valid")
        .map((f) => f.name),
    [uploadedFiles]
  );

  // ── Export handler (DB mode) ──
  const handleExportDb = useCallback(async () => {
    if (!dbSessionId) return;
    setExporting(true);
    setExportProgress(10);
    try {
      const all = await getAllResultsForExport(dbSessionId);
      setExportProgress(80);
      const filename = buildExportFilename(fileNames, processedAt);
      exportSessionDataToCsv(all, filename, processedAt);
      setExportProgress(100);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setTimeout(() => {
        setExporting(false);
        setExportProgress(0);
      }, 1200);
    }
  }, [dbSessionId, fileNames, processedAt]);

  // ── Export handler (local mode) ──
  const handleExportLocal = useCallback(() => {
    const filename = buildExportFilename(fileNames, processedAt);
    exportToCSV(
      results as unknown as Record<string, unknown>[],
      filename
    );
  }, [results, fileNames, processedAt]);

  const totalPages = useDb
    ? Math.ceil(dbCount / PAGE_SIZE)
    : Math.ceil(results.length / PAGE_SIZE);

  // ── Empty state — só mostra se não há NADA (sem DB, sem resultado local, sem worker) ──
  if (!useDb && !results.length && !workerCsvUrl && !workerSummary) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center py-20 gap-4 text-center"
      >
        <FileSpreadsheet className="w-12 h-12 text-muted-foreground/50" />
        <p className="text-muted-foreground">
          Nenhum resultado disponível. Execute o processamento primeiro.
        </p>
        <Button
          variant="outline"
          onClick={() => setCurrentStep(3)}
          className="gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Ir para Processamento
        </Button>
      </motion.div>
    );
  }

  // ═════════════════════════════════════════════════════════════════
  //  RENDER
  // ═════════════════════════════════════════════════════════════════
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* ── Header ── */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Resultados</h2>
          <p className="text-muted-foreground mt-1">
            Dados completos com todas as etapas de cálculo para validação.
          </p>
          {processedAt && (
            <div className="flex items-center gap-1.5 mt-2 text-xs text-muted-foreground">
              <Calendar className="w-3.5 h-3.5" />
              Processado em {formatDateBR(processedAt)}
            </div>
          )}
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(3)}
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Reprocessar
          </Button>

          {/* Botão primário: CSV gerado pelo worker no Storage (direto, sem espera) */}
          {workerCsvUrl ? (
            <Button
              asChild
              className="gap-2 bg-emerald-600 hover:bg-emerald-700"
            >
              <a href={workerCsvUrl} download>
                <Download className="w-4 h-4" />
                Download CSV (Storage)
              </a>
            </Button>
          ) : (
            /* Fallback: gera CSV client-side buscando tudo do banco */
            <Button
              onClick={useDb ? handleExportDb : handleExportLocal}
              disabled={exporting}
              className="gap-2"
            >
              {exporting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              {exporting ? "Exportando..." : "Exportar CSV Completo"}
            </Button>
          )}
        </div>
      </div>

      {/* ── Export progress ── */}
      <AnimatePresence>
        {exporting && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <Card>
              <CardContent className="p-4 flex items-center gap-4">
                <Loader2 className="w-5 h-5 text-primary animate-spin shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium">
                    {exportProgress < 80
                      ? "Buscando todos os registros do banco..."
                      : exportProgress < 100
                      ? "Gerando arquivo CSV..."
                      : "Download iniciado!"}
                  </p>
                  <Progress value={exportProgress} className="h-1.5 mt-2" />
                </div>
                {exportProgress >= 100 && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Metric cards ── */}
      {/* Prioridade: workerSummary (Railway) > localMetrics (browser) */}
      {workerSummary ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            label="Total Registros"
            value={formatNumber(workerSummary.total_rows, 0)}
            icon={<FileSpreadsheet className="w-5 h-5" />}
            color="bg-blue-100 text-blue-600"
            delay={0}
          />
          <MetricCard
            label="Valor Principal"
            value={formatBRL(workerSummary.total_valor_principal)}
            icon={<DollarSign className="w-5 h-5" />}
            color="bg-emerald-100 text-emerald-600"
            delay={0.05}
          />
          <MetricCard
            label="Valor Corrigido"
            value={formatBRL(workerSummary.total_valor_corrigido)}
            icon={<TrendingUp className="w-5 h-5" />}
            color="bg-amber-100 text-amber-600"
            delay={0.1}
          />
          <MetricCard
            label="Valor Justo"
            value={formatBRL(workerSummary.total_valor_justo)}
            icon={<BarChart3 className="w-5 h-5" />}
            color="bg-purple-100 text-purple-600"
            delay={0.15}
          />
        </div>
      ) : localMetrics ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            label="Total Registros"
            value={formatNumber(localMetrics.total, 0)}
            icon={<FileSpreadsheet className="w-5 h-5" />}
            color="bg-blue-100 text-blue-600"
            delay={0}
          />
          <MetricCard
            label="Valor Principal"
            value={formatBRL(localMetrics.totalPrincipal)}
            icon={<DollarSign className="w-5 h-5" />}
            color="bg-emerald-100 text-emerald-600"
            delay={0.05}
          />
          <MetricCard
            label="Valor Corrigido"
            value={formatBRL(localMetrics.totalCorrigido)}
            icon={<TrendingUp className="w-5 h-5" />}
            color="bg-amber-100 text-amber-600"
            delay={0.1}
          />
          <MetricCard
            label="Valor Justo"
            value={formatBRL(localMetrics.totalJusto)}
            icon={<BarChart3 className="w-5 h-5" />}
            color="bg-purple-100 text-purple-600"
            delay={0.15}
          />
        </div>
      ) : null}

      {/* ── Column legend ── */}
      {useDb && (
        <Card>
          <CardContent className="p-3 flex flex-wrap items-center gap-3">
            <span className="text-xs font-semibold text-muted-foreground mr-1">
              Grupos de colunas:
            </span>
            {Object.entries(GROUP_LABELS).map(([key, label]) => (
              <Badge
                key={key}
                variant="outline"
                className={`text-[10px] ${GROUP_COLORS[key]}`}
              >
                {label}
              </Badge>
            ))}
          </CardContent>
        </Card>
      )}

      {/* ── Full-detail DB table ── */}
      {useDb && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Table2 className="w-4 h-4 text-primary" />
                  Dados Calculados — Todas as Etapas
                </CardTitle>
                <span className="text-xs text-muted-foreground">
                  {dbCount > 0
                    ? `${dbPage * PAGE_SIZE + 1}–${Math.min(
                        (dbPage + 1) * PAGE_SIZE,
                        dbCount
                      )} de ${dbCount.toLocaleString("pt-BR")}`
                    : "Carregando..."}
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-0 overflow-x-auto">
              <div className="max-h-[500px] overflow-y-auto">
                <table className="w-full text-[11px] whitespace-nowrap">
                  {/* column group header */}
                  <thead className="sticky top-0 z-20">
                    <tr>
                      {DB_COLUMNS.map((col) => (
                        <th
                          key={col.key}
                          className={`px-2 py-1 text-[9px] font-semibold uppercase tracking-wider border-b ${GROUP_COLORS[col.group]} text-muted-foreground`}
                        >
                          {GROUP_LABELS[col.group]}
                        </th>
                      ))}
                    </tr>
                    <tr className="bg-white">
                      {DB_COLUMNS.map((col) => (
                        <th
                          key={col.key}
                          className={`px-2 py-1.5 font-semibold border-b text-muted-foreground ${
                            col.align === "right" ? "text-right" : "text-left"
                          }`}
                        >
                          {col.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td
                          colSpan={DB_COLUMNS.length}
                          className="text-center py-12"
                        >
                          <Loader2 className="w-5 h-5 animate-spin mx-auto text-muted-foreground" />
                        </td>
                      </tr>
                    ) : dbRows.length === 0 ? (
                      <tr>
                        <td
                          colSpan={DB_COLUMNS.length}
                          className="text-center py-12 text-muted-foreground"
                        >
                          Nenhum resultado
                        </td>
                      </tr>
                    ) : (
                      dbRows.map((row) => (
                        <tr
                          key={row.id}
                          className="border-b border-dashed last:border-0 hover:bg-slate-50/50"
                        >
                          {DB_COLUMNS.map((col) => {
                            const raw = row[col.key];
                            const display = col.fmt
                              ? col.fmt(raw)
                              : raw != null
                              ? String(raw)
                              : "";
                            const isVjr =
                              col.key === "valor_justo";
                            return (
                              <td
                                key={col.key}
                                className={`px-2 py-1 ${
                                  col.align === "right"
                                    ? "text-right"
                                    : "text-left"
                                } ${isVjr ? "font-medium text-emerald-700" : ""}`}
                              >
                                {col.key === "empresa" &&
                                row.is_voltz ? (
                                  <span className="flex items-center gap-0.5">
                                    <Zap className="w-3 h-3 text-amber-500 inline" />
                                    {display}
                                  </span>
                                ) : (
                                  display
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadPage(dbPage - 1)}
                    disabled={dbPage === 0 || loading}
                    className="gap-1"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                    Anterior
                  </Button>
                  <span className="text-xs text-muted-foreground">
                    Página {dbPage + 1} de {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => loadPage(dbPage + 1)}
                    disabled={
                      (dbPage + 1) * PAGE_SIZE >= dbCount || loading
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

      {/* ── Local-mode table (fallback, simpler) ── */}
      {!useDb && results.length > 0 && (
        <LocalResultsTable
          results={results}
          page={dbPage}
          setPage={setDbPage}
          pageSize={PAGE_SIZE}
        />
      )}

      {/* ── Back ── */}
      <div className="flex items-center justify-start pt-4">
        <Button
          variant="outline"
          onClick={() => setCurrentStep(3)}
          className="gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </Button>
      </div>
    </motion.div>
  );
}

// ─── Local fallback table (preserved from original) ───────────────

function LocalResultsTable({
  results,
  page,
  setPage,
  pageSize,
}: {
  results: FinalRecord[];
  page: number;
  setPage: (p: number) => void;
  pageSize: number;
}) {
  const [sortCol, setSortCol] = useState<keyof FinalRecord | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  const columns: {
    key: keyof FinalRecord;
    label: string;
    fmt?: (v: unknown) => string;
  }[] = [
    { key: "empresa", label: "Empresa" },
    { key: "tipo", label: "Tipo" },
    { key: "aging", label: "Aging" },
    { key: "valor_principal", label: "VP (R$)", fmt: (v) => formatBRL(v as number) },
    { key: "valor_liquido", label: "VL (R$)", fmt: (v) => formatBRL(v as number) },
    { key: "multa", label: "Multa (R$)", fmt: (v) => formatBRL(v as number) },
    { key: "juros_moratorios", label: "Juros (R$)", fmt: (v) => formatBRL(v as number) },
    { key: "correcao_monetaria", label: "Correção (R$)", fmt: (v) => formatBRL(v as number) },
    { key: "valor_corrigido", label: "VC (R$)", fmt: (v) => formatBRL(v as number) },
    { key: "taxa_recuperacao", label: "Taxa Rec.", fmt: (v) => `${((v as number) * 100).toFixed(1)}%` },
    { key: "valor_justo", label: "Valor Justo (R$)", fmt: (v) => formatBRL(v as number) },
  ];

  const sorted = useMemo(() => {
    if (!sortCol) return results;
    return [...results].sort((a, b) => {
      const va = a[sortCol] ?? "";
      const vb = b[sortCol] ?? "";
      if (typeof va === "number" && typeof vb === "number")
        return sortAsc ? va - vb : vb - va;
      return sortAsc
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });
  }, [results, sortCol, sortAsc]);

  const totalPages = Math.ceil(sorted.length / pageSize);
  const pageData = sorted.slice(page * pageSize, (page + 1) * pageSize);

  const handleSort = (col: keyof FinalRecord) => {
    if (sortCol === col) setSortAsc(!sortAsc);
    else {
      setSortCol(col);
      setSortAsc(true);
    }
    setPage(0);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
    >
      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="data-table w-full text-sm">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className="px-3 py-2 text-left cursor-pointer hover:bg-slate-100 select-none transition-colors whitespace-nowrap"
                    onClick={() => handleSort(col.key)}
                  >
                    <span className="flex items-center gap-1">
                      {col.label}
                      {sortCol === col.key && (
                        <span className="text-xs">
                          {sortAsc ? "▲" : "▼"}
                        </span>
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageData.map((row, i) => (
                <tr
                  key={i}
                  className="border-t border-slate-100 hover:bg-slate-50/50 transition-colors"
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className="px-3 py-2 whitespace-nowrap"
                    >
                      {col.fmt
                        ? col.fmt(row[col.key])
                        : String(row[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-3">
          <p className="text-xs text-muted-foreground">
            Mostrando {page * pageSize + 1}–
            {Math.min((page + 1) * pageSize, sorted.length)} de{" "}
            {sorted.length}
          </p>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages - 1}
              onClick={() => setPage(page + 1)}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
