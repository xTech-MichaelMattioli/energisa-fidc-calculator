/**
 * Page 5: Results
 * Display summary metrics, data table, and export controls.
 */
import { useMemo, useState } from "react";
import { useApp } from "@/context/AppContext";
import { exportToCSV } from "@/services";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
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
} from "lucide-react";
import { formatBRL, formatNumber } from "@/lib/utils";
import type { FinalRecord } from "@/types";

const PAGE_SIZE = 25;

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

export function ResultsPage() {
  const { results, setCurrentStep } = useApp();
  const [page, setPage] = useState(0);
  const [sortCol, setSortCol] = useState<keyof FinalRecord | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  // ── Aggregated metrics ──
  const metrics = useMemo(() => {
    if (!results.length) return null;

    const totalPrincipal = results.reduce((s, r) => s + (r.valor_principal || 0), 0);
    const totalCorrigido = results.reduce((s, r) => s + (r.valor_corrigido || 0), 0);
    const totalJusto = results.reduce((s, r) => s + (r.valor_justo || 0), 0);
    const totalReajustado = results.reduce(
      (s, r) => s + (r.valor_justo_reajustado ?? r.valor_justo ?? 0),
      0
    );

    const empresas = new Set(results.map((r) => r.empresa)).size;
    const voltzCount = results.filter((r) => r.empresa?.toUpperCase() === "VOLTZ").length;

    return {
      total: results.length,
      totalPrincipal,
      totalCorrigido,
      totalJusto,
      totalReajustado,
      empresas,
      voltzCount,
    };
  }, [results]);

  // ── Aging distribution ──
  const agingDist = useMemo(() => {
    const map: Record<string, { count: number; valor: number }> = {};
    for (const r of results) {
      const key = r.aging || "N/A";
      if (!map[key]) map[key] = { count: 0, valor: 0 };
      map[key].count++;
      map[key].valor += r.valor_corrigido || 0;
    }
    return Object.entries(map).sort((a, b) => b[1].valor - a[1].valor);
  }, [results]);

  // ── Sorted & paginated data ──
  const sorted = useMemo(() => {
    if (!sortCol) return results;
    return [...results].sort((a, b) => {
      const va = a[sortCol] ?? "";
      const vb = b[sortCol] ?? "";
      if (typeof va === "number" && typeof vb === "number") return sortAsc ? va - vb : vb - va;
      return sortAsc
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va));
    });
  }, [results, sortCol, sortAsc]);

  const totalPages = Math.ceil(sorted.length / PAGE_SIZE);
  const pageData = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleSort = (col: keyof FinalRecord) => {
    if (sortCol === col) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(col);
      setSortAsc(true);
    }
    setPage(0);
  };

  const handleExport = () => {
    exportToCSV(results as unknown as Record<string, unknown>[], `fidc_resultados_${new Date().toISOString().slice(0, 10)}.csv`);
  };

  // ── Column config ──
  const columns: { key: keyof FinalRecord; label: string; fmt?: (v: unknown) => string }[] = [
    { key: "empresa", label: "Empresa" },
    { key: "tipo", label: "Tipo" },
    { key: "aging", label: "Aging" },
    {
      key: "valor_principal",
      label: "VP (R$)",
      fmt: (v) => formatBRL(v as number),
    },
    {
      key: "valor_corrigido",
      label: "VC (R$)",
      fmt: (v) => formatBRL(v as number),
    },
    {
      key: "valor_justo",
      label: "VJ (R$)",
      fmt: (v) => formatBRL(v as number),
    },
    {
      key: "valor_justo_reajustado",
      label: "VJ Reaj. (R$)",
      fmt: (v) => formatBRL(v as number),
    },
    {
      key: "taxa_recuperacao",
      label: "Taxa Rec.",
      fmt: (v) => `${((v as number) * 100).toFixed(1)}%`,
    },
  ];

  if (!results.length) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center py-20 gap-4 text-center"
      >
        <FileSpreadsheet className="w-12 h-12 text-muted-foreground/50" />
        <p className="text-muted-foreground">Nenhum resultado disponível. Execute o processamento primeiro.</p>
        <Button variant="outline" onClick={() => setCurrentStep(3)} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          Ir para Processamento
        </Button>
      </motion.div>
    );
  }

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
            Resumo dos cálculos e exportação de dados.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setCurrentStep(3)} className="gap-2">
            <RefreshCw className="w-4 h-4" />
            Reprocessar
          </Button>
          <Button onClick={handleExport} className="gap-2">
            <Download className="w-4 h-4" />
            Exportar CSV
          </Button>
        </div>
      </div>

      {/* ── Metric cards ── */}
      {metrics && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            label="Total Registros"
            value={formatNumber(metrics.total, 0)}
            icon={<FileSpreadsheet className="w-5 h-5" />}
            color="bg-blue-100 text-blue-600"
            delay={0}
          />
          <MetricCard
            label="Valor Principal"
            value={formatBRL(metrics.totalPrincipal)}
            icon={<DollarSign className="w-5 h-5" />}
            color="bg-emerald-100 text-emerald-600"
            delay={0.05}
          />
          <MetricCard
            label="Valor Corrigido"
            value={formatBRL(metrics.totalCorrigido)}
            icon={<TrendingUp className="w-5 h-5" />}
            color="bg-amber-100 text-amber-600"
            delay={0.1}
          />
          <MetricCard
            label="Valor Justo Reaj."
            value={formatBRL(metrics.totalReajustado)}
            icon={<BarChart3 className="w-5 h-5" />}
            color="bg-purple-100 text-purple-600"
            delay={0.15}
          />
        </div>
      )}

      {/* ── Aging distribution ── */}
      {agingDist.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Distribuição por Aging</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="space-y-2">
                {agingDist.map(([aging, { count, valor }]) => {
                  const pct = metrics ? (valor / metrics.totalCorrigido) * 100 : 0;
                  return (
                    <div key={aging} className="flex items-center gap-3 text-sm">
                      <span className="w-40 truncate font-medium">{aging}</span>
                      <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${Math.max(pct, 1)}%` }}
                        />
                      </div>
                      <span className="w-14 text-right text-muted-foreground text-xs">
                        {count}
                      </span>
                      <span className="w-28 text-right text-xs font-medium">
                        {formatBRL(valor)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Data table ── */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
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
                          <span className="text-xs">{sortAsc ? "▲" : "▼"}</span>
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
                      <td key={col.key} className="px-3 py-2 whitespace-nowrap">
                        {col.key === "empresa" && row.empresa?.toUpperCase() === "VOLTZ" ? (
                          <Badge variant="warning" className="text-[10px]">
                            {String(row[col.key] ?? "")}
                          </Badge>
                        ) : col.fmt ? (
                          col.fmt(row[col.key])
                        ) : (
                          String(row[col.key] ?? "")
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        {/* ── Pagination ── */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-3">
            <p className="text-xs text-muted-foreground">
              Mostrando {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, sorted.length)} de{" "}
              {sorted.length}
            </p>
            <div className="flex gap-1">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </motion.div>

      {/* ── Back ── */}
      <div className="flex items-center justify-start pt-4">
        <Button variant="outline" onClick={() => setCurrentStep(3)} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </Button>
      </div>
    </motion.div>
  );
}
