// Serviço para integração com Edge Function do Supabase
import { createClient } from '@supabase/supabase-js'

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

export interface UploadResult {
  success: boolean;
  fileName: string;
  filePath: string;
  fileUrl: string;
  uploadTime: number;
  error?: string;
}

export class SupabaseExcelService {
  private readonly edgeFunctionUrl: string;
  private readonly supabase;
  private readonly supabaseUrl = 'https://tlxrdgamqsgeryzhioly.supabase.co';
  private readonly supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRseFJkZ2FtcXNnZXJ5emhpb2x5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzc3MjI5MjgsImV4cCI6MjA1MzI5ODkyOH0.vQJHNTZxPPQYIZlH5dKCYHv2_tHJ9uMRV4xLU_kJSTo';
  private readonly storageBucket = 'excel-uploads';

  constructor() {
    // URL da Edge Function do Supabase
    this.edgeFunctionUrl = 'https://tlxrdgamqsgeryzhioly.supabase.co/functions/v1/process-excel-file';
    
    // Inicializar cliente Supabase
    this.supabase = createClient(this.supabaseUrl, this.supabaseKey);
  }

  /**
   * Faz upload do arquivo para o Supabase Storage
   */
  async uploadFile(file: File): Promise<UploadResult> {
    try {
      const startTime = Date.now();
      console.log('📤 Iniciando upload para Supabase Storage:', file.name);
      
      // Gerar nome único para o arquivo
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const fileName = `${timestamp}_${file.name}`;
      const filePath = `energisa-uploads/${fileName}`;
      
      // Fazer upload para o bucket
      const { data, error } = await this.supabase.storage
        .from(this.storageBucket)
        .upload(filePath, file, {
          cacheControl: '3600',
          upsert: false
        });
      
      if (error) {
        throw error;
      }
      
      // Obter URL pública do arquivo
      const { data: publicUrlData } = this.supabase.storage
        .from(this.storageBucket)
        .getPublicUrl(filePath);
      
      const uploadTime = Date.now() - startTime;
      
      console.log('✅ Upload concluído:', {
        arquivo: fileName,
        path: filePath,
        url: publicUrlData.publicUrl,
        tempo: uploadTime + 'ms'
      });
      
      return {
        success: true,
        fileName: fileName,
        filePath: filePath,
        fileUrl: publicUrlData.publicUrl,
        uploadTime: uploadTime
      };
      
    } catch (error) {
      console.error('❌ Erro no upload:', error);
      
      return {
        success: false,
        fileName: file.name,
        filePath: '',
        fileUrl: '',
        uploadTime: 0,
        error: error instanceof Error ? error.message : 'Erro desconhecido no upload'
      };
    }
  }

  /**
   * Processa um arquivo Excel usando a Edge Function do Supabase
   */
  async processExcelFile(file: File): Promise<ProcessExcelResult> {
    try {
      console.log('🚀 Processando arquivo Excel:', file.name);
      
      // 1. Primeiro fazer upload do arquivo para o storage
      console.log('📤 Fazendo upload para Supabase Storage...');
      const uploadResult = await this.uploadFile(file);
      
      if (!uploadResult.success) {
        throw new Error(`Erro no upload: ${uploadResult.error}`);
      }
      
      console.log('✅ Upload concluído, processando via Edge Function...');
      
      // 2. Criar FormData para envio do arquivo para Edge Function
      const formData = new FormData();
      formData.append('file', file);

      // 3. Fazer requisição para a Edge Function
      const response = await fetch(this.edgeFunctionUrl, {
        method: 'POST',
        body: formData,
        headers: {
          // Adicionar autorização Supabase
          'Authorization': `Bearer ${this.supabaseKey}`
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
        tempo: result.metadata.processingTime + 'ms',
        uploadUrl: uploadResult.fileUrl
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
   * Processa um arquivo CSV e faz upload para o storage
   */
  async processCSVFile(file: File): Promise<UploadResult> {
    try {
      console.log('📄 Processando arquivo CSV:', file.name);
      
      // Fazer upload do arquivo CSV para o storage
      const uploadResult = await this.uploadFile(file);
      
      if (!uploadResult.success) {
        throw new Error(`Erro no upload: ${uploadResult.error}`);
      }
      
      console.log('✅ Arquivo CSV processado e enviado para storage');
      return uploadResult;
      
    } catch (error) {
      console.error('❌ Erro ao processar arquivo CSV:', error);
      
      return {
        success: false,
        fileName: file.name,
        filePath: '',
        fileUrl: '',
        uploadTime: 0,
        error: error instanceof Error ? error.message : 'Erro desconhecido'
      };
    }
  }

  /**
   * Lista arquivos do storage
   */
  async listFiles(): Promise<{ success: boolean; files: any[]; error?: string }> {
    try {
      const { data, error } = await this.supabase.storage
        .from(this.storageBucket)
        .list('energisa-uploads', {
          limit: 100,
          offset: 0,
          sortBy: { column: 'created_at', order: 'desc' }
        });
      
      if (error) {
        throw error;
      }
      
      return {
        success: true,
        files: data || []
      };
      
    } catch (error) {
      console.error('❌ Erro ao listar arquivos:', error);
      
      return {
        success: false,
        files: [],
        error: error instanceof Error ? error.message : 'Erro desconhecido'
      };
    }
  }

  /**
   * Remove arquivo do storage
   */
  async deleteFile(filePath: string): Promise<{ success: boolean; error?: string }> {
    try {
      const { error } = await this.supabase.storage
        .from(this.storageBucket)
        .remove([filePath]);
      
      if (error) {
        throw error;
      }
      
      return { success: true };
      
    } catch (error) {
      console.error('❌ Erro ao remover arquivo:', error);
      
      return {
        success: false,
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
