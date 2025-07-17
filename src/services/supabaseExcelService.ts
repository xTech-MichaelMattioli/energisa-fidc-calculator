// Serviço para integração com Edge Function do Supabase
export interface ProcessExcelResult {
  success: boolean;
  fileName: string;
  fileSize: number;
  totalRecords: number;
  columns: string[];
  preview: any[];
  validation: {
    camposEncontrados: { [key: string]: string | null };
    camposFaltantes: string[];
    score: number;
    valido: boolean;
  };
  metadata: {
    sheets: string[];
    processedSheet: string;
    encoding: string;
    processingTime: number;
  };
  error?: string;
}

export class SupabaseExcelService {
  private readonly edgeFunctionUrl: string;

  constructor() {
    // URL da Edge Function do Supabase
    this.edgeFunctionUrl = 'https://lzfhvodyvqdtdefuuwtg.supabase.co/functions/v1/process-excel-file';
  }

  /**
   * Processa um arquivo Excel usando a Edge Function do Supabase
   */
  async processExcelFile(file: File): Promise<ProcessExcelResult> {
    try {
      console.log('🚀 Enviando arquivo para Edge Function:', file.name);
      
      // Criar FormData para envio do arquivo
      const formData = new FormData();
      formData.append('file', file);

      // Fazer requisição para a Edge Function
      const response = await fetch(this.edgeFunctionUrl, {
        method: 'POST',
        body: formData,
        headers: {
          // Adicionar autorização Supabase
          'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6Zmh2b2R5dnFkdGRlZnV1d3RnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA5MzYwNzYsImV4cCI6MjA2NjUxMjA3Nn0.p6rIYlznTOmedGNhUFToRdFsdZmvtNuwWoupBTGbyvk'
          // Não definir Content-Type para FormData - o browser define automaticamente
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result: ProcessExcelResult = await response.json();
      
      if (!result.success) {
        throw new Error(result.error || 'Erro desconhecido no processamento');
      }

      console.log('✅ Arquivo processado com sucesso:', {
        arquivo: result.fileName,
        registros: result.totalRecords,
        colunas: result.columns.length,
        score: result.validation.score,
        tempo: result.metadata.processingTime + 'ms'
      });

      return result;

    } catch (error) {
      console.error('❌ Erro ao processar arquivo Excel:', error);
      
      // Retornar resultado de erro estruturado
      return {
        success: false,
        fileName: file.name,
        fileSize: file.size,
        totalRecords: 0,
        columns: [],
        preview: [],
        validation: {
          camposEncontrados: {},
          camposFaltantes: [],
          score: 0,
          valido: false
        },
        metadata: {
          sheets: [],
          processedSheet: '',
          encoding: '',
          processingTime: 0
        },
        error: error instanceof Error ? error.message : 'Erro desconhecido'
      };
    }
  }

  /**
   * Valida se o arquivo é um Excel válido
   */
  validateExcelFile(file: File): { valid: boolean; error?: string } {
    // Verificar tipo de arquivo
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      return {
        valid: false,
        error: 'Tipo de arquivo inválido. Apenas arquivos Excel (.xlsx, .xls) são aceitos.'
      };
    }

    // Verificar tamanho (máximo 100MB)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `Arquivo muito grande. Tamanho máximo: ${maxSize / 1024 / 1024}MB`
      };
    }

    return { valid: true };
  }

  /**
   * Formatar tamanho de arquivo em formato legível
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Gerar relatório de validação FIDC
   */
  generateValidationReport(validation: ProcessExcelResult['validation']): string {
    const { score, valido, camposFaltantes, camposEncontrados } = validation;
    
    let report = `📊 Score de Compatibilidade FIDC: ${score}%\n\n`;
    
    if (valido) {
      report += '✅ Estrutura VÁLIDA - Todos os campos obrigatórios encontrados!\n\n';
    } else {
      report += '⚠️ Estrutura INCOMPLETA - Campos faltantes detectados!\n\n';
    }
    
    report += '📋 Campos Encontrados:\n';
    Object.entries(camposEncontrados).forEach(([campo, coluna]) => {
      if (coluna) {
        report += `  ✅ ${campo}: "${coluna}"\n`;
      } else {
        report += `  ❌ ${campo}: Não encontrado\n`;
      }
    });
    
    if (camposFaltantes.length > 0) {
      report += '\n🚨 Ação Necessária:\n';
      camposFaltantes.forEach(campo => {
        report += `  • Verificar campo: ${campo}\n`;
      });
    }
    
    return report;
  }
}

// Instância única do serviço
export const supabaseExcelService = new SupabaseExcelService();
