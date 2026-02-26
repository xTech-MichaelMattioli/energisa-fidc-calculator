// ─── Types: Core Data Model ───────────────────────────────────────
// Maps the complete FIDC calculation pipeline

/** Raw record from uploaded Excel */
export interface RawRecord {
  [key: string]: unknown;
}

/** Standardized record after field mapping */
export interface MappedRecord {
  empresa: string;
  tipo: string;
  status: string;
  situacao: string;
  nome_cliente: string;
  documento: string;
  classe: string;
  contrato: string;
  valor_principal: number;
  valor_nao_cedido: number;
  valor_terceiro: number;
  valor_cip: number;
  data_vencimento: string; // ISO date
  data_base: string;       // ISO date
  base_origem: string;
}

/** Record with aging classification */
export interface AgingRecord extends MappedRecord {
  dias_atraso: number;
  aging: AgingBucket;
  aging_taxa: AgingTaxa;
}

/** Record after monetary correction */
export interface CorrectedRecord extends AgingRecord {
  valor_liquido: number;
  multa: number;
  juros_moratorios: number;
  fator_correcao: number;
  correcao_monetaria: number;
  valor_corrigido: number;
  // Voltz-specific
  juros_remuneratorios?: number;
  saldo_devedor_vencimento?: number;
}

/** Record after fair value calculation */
export interface FinalRecord extends CorrectedRecord {
  taxa_recuperacao: number;
  prazo_recebimento: number;
  valor_recuperavel: number;
  valor_justo: number;
  desconto_aging?: number;
  valor_justo_reajustado?: number;
  is_voltz?: boolean;
}

// ─── Enums ────────────────────────────────────────────────────────

export type AgingBucket =
  | "A vencer"
  | "Menor que 30 dias"
  | "De 31 a 59 dias"
  | "De 60 a 89 dias"
  | "De 90 a 119 dias"
  | "De 120 a 359 dias"
  | "De 360 a 719 dias"
  | "De 720 a 1080 dias"
  | "Maior que 1080 dias";

export type AgingTaxa =
  | "A vencer"
  | "Primeiro ano"
  | "Segundo ano"
  | "Terceiro ano"
  | "Quarto ano"
  | "Quinto ano"
  | "Demais anos";

// ─── Configuration Types ──────────────────────────────────────────

export interface RecoveryRate {
  empresa: string;
  tipo: string;
  aging: AgingTaxa;
  taxa_recuperacao: number;
  prazo_recebimento: number;
}

export interface EconomicIndex {
  date: string;  // ISO date
  value: number;
}

export interface DIPRERate {
  dias_corridos: number;
  taxa_252: number;
  taxa_360: number;
  meses_futuros: number;
}

// ─── Upload State ─────────────────────────────────────────────────

export interface UploadedFile {
  id: string;
  name: string;
  data: RawRecord[];
  columns: string[];
  rowCount: number;
  detectedDate?: string;
  isVoltz: boolean;
  /** Remote path in Supabase Storage (temp bucket) */
  storagePath?: string;
  /** Upload status */
  uploadStatus?: "pending" | "uploading" | "uploaded" | "error";
}

export interface FieldMapping {
  [targetField: string]: string; // target → source column
}

// ─── Processing State ─────────────────────────────────────────────

export type ProcessingStep =
  | "idle"
  | "validating"
  | "aging"
  | "correction"
  | "recovery"
  | "fair-value"
  | "remuneration"
  | "exporting"
  | "complete"
  | "error";

export interface ProcessingProgress {
  step: ProcessingStep;
  progress: number;      // 0-100
  message: string;
  details?: string;
}

// ─── Pipeline Step Definition (for stepper UI) ────────────────────

export interface PipelineStep {
  id: number;
  key: string;
  title: string;
  description: string;
  icon: string;
}

export const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: 1,
    key: "upload",
    title: "Carregamento",
    description: "Upload dos arquivos Excel das distribuidoras",
    icon: "Upload",
  },
  {
    id: 2,
    key: "mapping",
    title: "Mapeamento",
    description: "Mapeamento automático dos campos",
    icon: "GitBranch",
  },
  {
    id: 3,
    key: "indices",
    title: "Índices",
    description: "Configuração de IGP-M, IPCA e DI-PRE",
    icon: "TrendingUp",
  },
  {
    id: 4,
    key: "processing",
    title: "Processamento",
    description: "Cálculo de aging, correção e valor justo",
    icon: "Calculator",
  },
  {
    id: 5,
    key: "results",
    title: "Resultados",
    description: "Visualização e exportação dos resultados",
    icon: "BarChart3",
  },
];
