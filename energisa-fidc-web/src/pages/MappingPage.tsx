/**
 * Page 2: Mapping (Mapeamento)
 * Auto-map & manually adjust field mappings.
 */
import { useEffect, useMemo, useState } from "react";
import { useApp } from "@/context/AppContext";
import {
  autoMapFields,
  applyMapping,
  getMissingRequiredFields,
  getMappingConfidence,
  TARGET_FIELDS,
} from "@/services";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { motion } from "framer-motion";
import {
  ArrowRight,
  ArrowLeft,
  GitBranch,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ChevronDown,
} from "lucide-react";

const FIELD_LABELS: Record<string, string> = {
  empresa: "Empresa / Distribuidora",
  tipo: "Tipo do Consumidor",
  status: "Status da Conta",
  situacao: "Situação Específica",
  nome_cliente: "Nome do Cliente",
  documento: "CPF/CNPJ",
  classe: "Classe de Consumo",
  contrato: "Contrato / UC",
  valor_principal: "Valor Principal (R$)",
  valor_nao_cedido: "Valor Não Cedido",
  valor_terceiro: "Valor de Terceiros",
  valor_cip: "Valor CIP/COSIP",
  data_vencimento: "Data de Vencimento",
};

const REQUIRED_FIELDS = ["empresa", "tipo", "valor_principal", "data_vencimento"];

export function MappingPage() {
  const {
    uploadedFiles,
    fieldMappings,
    setFieldMappings,
    setMappedRecords,
    setCurrentStep,
    dataBase,
    setDataBase,
  } = useApp();

  const [activeFileIdx, setActiveFileIdx] = useState(0);
  const activeFile = uploadedFiles[activeFileIdx];

  // Auto-map on mount for each file
  useEffect(() => {
    const newMappings: Record<string, Record<string, string>> = {};
    for (const file of uploadedFiles) {
      if (!fieldMappings[file.id]) {
        newMappings[file.id] = autoMapFields(file.columns);
      }
    }
    if (Object.keys(newMappings).length > 0) {
      setFieldMappings({ ...fieldMappings, ...newMappings });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uploadedFiles]);

  const currentMapping = fieldMappings[activeFile?.id] ?? {};

  const confidence = useMemo(
    () => getMappingConfidence(currentMapping),
    [currentMapping]
  );

  const missingFields = useMemo(
    () => getMissingRequiredFields(currentMapping),
    [currentMapping]
  );

  const updateMapping = (target: string, source: string) => {
    setFieldMappings({
      ...fieldMappings,
      [activeFile.id]: {
        ...currentMapping,
        [target]: source || undefined!,
      },
    });
  };

  const proceed = () => {
    // Apply mapping to all files and combine
    const allMapped: import("@/types").MappedRecord[] = [];
    for (const file of uploadedFiles) {
      const mapping = fieldMappings[file.id] ?? {};
      const mapped = applyMapping(file.data, mapping, {
        dataBase,
        baseOrigem: file.name,
        isVoltz: file.isVoltz,
      });
      allMapped.push(...mapped);
    }
    setMappedRecords(allMapped);
    setCurrentStep(2);
  };

  const allFilesReady = uploadedFiles.every((f) => {
    const m = fieldMappings[f.id] ?? {};
    return getMissingRequiredFields(m).length === 0;
  });

  if (!activeFile) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Mapeamento de Campos</h2>
          <p className="text-muted-foreground mt-1">
            Configure o mapeamento dos campos de cada arquivo para o esquema padrão.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-500" />
          <span className="text-sm text-muted-foreground">
            Mapeamento automático aplicado
          </span>
        </div>
      </div>

      {/* ── File Tabs ── */}
      {uploadedFiles.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {uploadedFiles.map((file, idx) => {
            const m = fieldMappings[file.id] ?? {};
            const missing = getMissingRequiredFields(m);
            return (
              <button
                key={file.id}
                onClick={() => setActiveFileIdx(idx)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap
                  ${idx === activeFileIdx
                    ? "bg-white shadow-sm border border-blue-100 text-foreground"
                    : "text-muted-foreground hover:bg-white/60"
                  }
                `}
              >
                {file.name}
                {missing.length === 0 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                ) : (
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* ── Confidence & Data Base ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Confiança do Mapeamento</span>
              <Badge variant={confidence >= 80 ? "success" : confidence >= 50 ? "warning" : "destructive"}>
                {confidence}%
              </Badge>
            </div>
            <Progress value={confidence} />
            {missingFields.length > 0 && (
              <p className="text-xs text-amber-600 mt-2">
                Campos obrigatórios faltando: {missingFields.map((f) => FIELD_LABELS[f] || f).join(", ")}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <label className="text-sm font-medium mb-2 block">Data Base de Cálculo</label>
            <input
              type="date"
              value={dataBase}
              onChange={(e) => setDataBase(e.target.value)}
              className="w-full h-10 px-3 rounded-lg border border-border bg-white text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </CardContent>
        </Card>
      </div>

      {/* ── Mapping Table ── */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <GitBranch className="w-4 h-4 text-primary" />
            {activeFile.name}
            {activeFile.isVoltz && (
              <Badge variant="warning" className="ml-2 text-[10px]">VOLTZ</Badge>
            )}
          </CardTitle>
          <CardDescription>
            {activeFile.rowCount} registros • {activeFile.columns.length} colunas detectadas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {TARGET_FIELDS.map((field) => {
              const isRequired = REQUIRED_FIELDS.includes(field);
              const mapped = currentMapping[field];
              const isDisabled =
                activeFile.isVoltz &&
                ["valor_nao_cedido", "valor_terceiro", "valor_cip"].includes(field);

              return (
                <div
                  key={field}
                  className="flex items-center gap-4 py-2 px-3 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  <div className="w-1/3 flex items-center gap-2">
                    <span className="text-sm font-medium">
                      {FIELD_LABELS[field] || field}
                    </span>
                    {isRequired && (
                      <span className="text-[10px] text-red-500 font-bold">*</span>
                    )}
                  </div>

                  <div className="w-8 flex justify-center">
                    <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
                  </div>

                  <div className="flex-1 relative">
                    {isDisabled ? (
                      <div className="h-9 px-3 flex items-center rounded-lg bg-slate-50 text-sm text-muted-foreground">
                        Fixado em 0 (VOLTZ)
                      </div>
                    ) : (
                      <div className="relative">
                        <select
                          value={mapped || ""}
                          onChange={(e) => updateMapping(field, e.target.value)}
                          className="w-full h-9 px-3 pr-8 rounded-lg border border-border bg-white text-sm appearance-none focus:outline-none focus:ring-2 focus:ring-ring"
                        >
                          <option value="">— Selecione —</option>
                          {activeFile.columns.map((col) => (
                            <option key={col} value={col}>
                              {col}
                            </option>
                          ))}
                        </select>
                        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
                      </div>
                    )}
                  </div>

                  <div className="w-8">
                    {mapped && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* ── Actions ── */}
      <div className="flex items-center justify-between pt-4">
        <Button variant="outline" onClick={() => setCurrentStep(0)} className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          Voltar
        </Button>
        <Button
          onClick={proceed}
          disabled={!allFilesReady}
          className="gap-2"
        >
          Próximo: Índices
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </motion.div>
  );
}
