import type {
  UploadedFile,
  FieldMapping,
  MappedRecord,
  FinalRecord,
  EconomicIndex,
  RecoveryRate,
  DIPRERate,
  ProcessingProgress,
} from "@/types";
import { createContext, useContext, useState, type ReactNode } from "react";

interface AppState {
  // Step tracking
  currentStep: number;
  setCurrentStep: (step: number) => void;

  // Step 1: Upload
  uploadedFiles: UploadedFile[];
  setUploadedFiles: (files: UploadedFile[]) => void;

  // Step 2: Mapping
  fieldMappings: Record<string, FieldMapping>;
  setFieldMappings: (m: Record<string, FieldMapping>) => void;
  mappedRecords: MappedRecord[];
  setMappedRecords: (r: MappedRecord[]) => void;

  // Step 3: Indices
  indices: EconomicIndex[];
  setIndices: (i: EconomicIndex[]) => void;
  recoveryRates: RecoveryRate[];
  setRecoveryRates: (r: RecoveryRate[]) => void;
  diPreRates: DIPRERate[];
  setDiPreRates: (r: DIPRERate[]) => void;
  dataBase: string;
  setDataBase: (d: string) => void;

  // Step 4: Processing
  processingProgress: ProcessingProgress | null;
  setProcessingProgress: (p: ProcessingProgress | null) => void;
  isProcessing: boolean;
  setIsProcessing: (v: boolean) => void;

  // Step 5: Results
  results: FinalRecord[];
  setResults: (r: FinalRecord[]) => void;
}

const AppContext = createContext<AppState | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [fieldMappings, setFieldMappings] = useState<Record<string, FieldMapping>>({});
  const [mappedRecords, setMappedRecords] = useState<MappedRecord[]>([]);
  const [indices, setIndices] = useState<EconomicIndex[]>([]);
  const [recoveryRates, setRecoveryRates] = useState<RecoveryRate[]>([]);
  const [diPreRates, setDiPreRates] = useState<DIPRERate[]>([]);
  const [dataBase, setDataBase] = useState("2025-04-30");
  const [processingProgress, setProcessingProgress] = useState<ProcessingProgress | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<FinalRecord[]>([]);

  return (
    <AppContext.Provider
      value={{
        currentStep, setCurrentStep,
        uploadedFiles, setUploadedFiles,
        fieldMappings, setFieldMappings,
        mappedRecords, setMappedRecords,
        indices, setIndices,
        recoveryRates, setRecoveryRates,
        diPreRates, setDiPreRates,
        dataBase, setDataBase,
        processingProgress, setProcessingProgress,
        isProcessing, setIsProcessing,
        results, setResults,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
