// Serviço para integração com Supabase Storage
import { createClient } from '@supabase/supabase-js'

export interface ValidacaoFIDC {
  camposEncontrados: { [key: string]: string | null };
  camposFaltantes: string[];
  score: number;
  valido: boolean;
}

export interface UploadResult {
  success: boolean;
  fileName: string;
  filePath: string;
  fileUrl: string;
  uploadTime: number;
  fileSize: number;
  error?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export class SupabaseExcelService {
  private readonly supabase;
  private readonly supabaseUrl = 'https://jlvkyasuvvgjdamhnwlb.supabase.co';
  private readonly supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impsdmt5YXN1dnZnamRhbWhud2xiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI3MzMyOTAsImV4cCI6MjA2ODMwOTI5MH0.CVhdtnlSphfZTJD1qibN_jQnpu6hog1E27f-RrLI8us';
  private readonly storageBucket = 'excel-uploads';

  constructor() {
    // Inicializar cliente Supabase
    this.supabase = createClient(this.supabaseUrl, this.supabaseKey);
  }

  /**
   * Faz upload do arquivo para o Supabase Storage com progress tracking
   */
  async uploadFile(file: File, userId?: string, onProgress?: (progress: UploadProgress) => void): Promise<UploadResult> {
    try {
      const startTime = Date.now();
      console.log('📤 Iniciando upload para Supabase Storage:', {
        nome: file.name,
        tamanho: this.formatFileSize(file.size),
        tipo: file.type
      });
      
      // Validar arquivo antes do upload
      const validation = this.validateExcelFile(file);
      if (!validation.valid) {
        throw new Error(validation.error);
      }
      
      // Gerar nome único para o arquivo
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const fileName = `${timestamp}_${file.name}`;
      
      // Incluir user_id no path se fornecido
      const userPath = userId ? `${userId}/` : '';
      const filePath = `energisa-uploads/${userPath}${fileName}`;
      
      // Configurar opções de upload otimizadas para arquivos grandes
      const uploadOptions = {
        cacheControl: '3600',
        upsert: false,
        contentType: file.type || 'application/octet-stream'
      };
      
      // Callback de progresso se fornecido
      if (onProgress) {
        onProgress({
          loaded: 0,
          total: file.size,
          percentage: 0
        });
      }
      
      // Fazer upload para o bucket
      const { data, error } = await this.supabase.storage
        .from(this.storageBucket)
        .upload(filePath, file, uploadOptions);
      
      if (error) {
        console.error('❌ Erro detalhado do upload:', error);
        throw new Error(`Erro no upload: ${error.message}`);
      }
      
      // Callback de progresso completo
      if (onProgress) {
        onProgress({
          loaded: file.size,
          total: file.size,
          percentage: 100
        });
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
        tempo: uploadTime + 'ms',
        tamanho: this.formatFileSize(file.size),
        usuario: userId || 'anônimo'
      });
      
      return {
        success: true,
        fileName: fileName,
        filePath: filePath,
        fileUrl: publicUrlData.publicUrl,
        uploadTime: uploadTime,
        fileSize: file.size
      };
      
    } catch (error) {
      console.error('❌ Erro no upload:', error);
      
      return {
        success: false,
        fileName: file.name,
        filePath: '',
        fileUrl: '',
        uploadTime: 0,
        fileSize: file.size,
        error: error instanceof Error ? error.message : 'Erro desconhecido no upload'
      };
    }
  }

  /**
   * Upload inteligente que escolhe a melhor estratégia baseada no tamanho
   */
  async smartUpload(file: File, userId?: string, onProgress?: (progress: UploadProgress) => void): Promise<UploadResult> {
    try {
      // Validar arquivo primeiro
      const validation = this.validateExcelFile(file);
      if (!validation.valid) {
        throw new Error(validation.error);
      }
      
      const fileSizeMB = file.size / (1024 * 1024);
      
      console.log('📊 Analisando estratégia de upload:', {
        arquivo: file.name,
        tamanho: this.formatFileSize(file.size),
        tamanhoMB: Math.round(fileSizeMB * 100) / 100,
        estrategia: fileSizeMB > 50 ? 'Upload para arquivo grande' : 'Upload normal'
      });
      
      // Para arquivos maiores que 50MB, usar upload especializado
      if (fileSizeMB > 50) {
        return this.uploadLargeFile(file, userId, onProgress);
      }
      
      // Para arquivos menores, usar upload normal
      return this.uploadFile(file, userId, onProgress);
      
    } catch (error) {
      console.error('❌ Erro no upload inteligente:', error);
      throw error;
    }
  }

  /**
   * Upload com chunking para arquivos muito grandes (>50MB)
   */
  async uploadLargeFile(file: File, userId?: string, onProgress?: (progress: UploadProgress) => void): Promise<UploadResult> {
    const CHUNK_SIZE = 50 * 1024 * 1024; // 50MB por chunk
    
    try {
      console.log('📤 Iniciando upload de arquivo grande:', {
        nome: file.name,
        tamanho: this.formatFileSize(file.size),
        chunks: Math.ceil(file.size / CHUNK_SIZE)
      });

      // Se o arquivo é menor que 50MB, usar upload normal
      if (file.size <= CHUNK_SIZE) {
        return this.uploadFile(file, userId, onProgress);
      }

      // TODO: Implementar upload com chunking
      // Por enquanto, usar upload normal e monitorar performance
      console.warn('⚠️ Arquivo grande detectado, usando upload normal. Considere implementar chunking se houver problemas.');
      
      return this.uploadFile(file, userId, onProgress);
      
    } catch (error) {
      console.error('❌ Erro no upload de arquivo grande:', error);
      throw error;
    }
  }

  /**
   * Processa um arquivo CSV e faz upload para o storage
   */
  async processCSVFile(file: File, userId?: string): Promise<UploadResult> {
    try {
      console.log('📄 Processando arquivo CSV:', file.name);
      
      // Fazer upload do arquivo CSV para o storage
      const uploadResult = await this.uploadFile(file, userId);
      
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
        fileSize: file.size,
        error: error instanceof Error ? error.message : 'Erro desconhecido'
      };
    }
  }

  /**
   * Lista arquivos do storage para um usuário específico
   */
  async listFiles(userId?: string): Promise<{ success: boolean; files: any[]; error?: string }> {
    try {
      const userPath = userId ? `energisa-uploads/${userId}` : 'energisa-uploads';
      
      const { data, error } = await this.supabase.storage
        .from(this.storageBucket)
        .list(userPath, {
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
    // Verificar tipo de arquivo por extensão
    if (!file.name.match(/\.(xlsx|xls)$/i)) {
      return {
        valid: false,
        error: 'Tipo de arquivo inválido. Apenas arquivos Excel (.xlsx, .xls) são aceitos.'
      };
    }

    // Verificar MIME type
    const allowedMimeTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'application/octet-stream'
    ];
    
    if (file.type && !allowedMimeTypes.includes(file.type)) {
      console.warn('⚠️ MIME type não reconhecido:', file.type, 'para arquivo:', file.name);
      // Não bloquear por MIME type, pois alguns browsers podem não definir corretamente
    }

    // Verificar tamanho (máximo 100MB)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `Arquivo muito grande. Tamanho máximo: ${this.formatFileSize(maxSize)}. Tamanho atual: ${this.formatFileSize(file.size)}`
      };
    }

    // Verificar se o arquivo não está vazio
    if (file.size === 0) {
      return {
        valid: false,
        error: 'Arquivo está vazio.'
      };
    }

    // Verificar tamanho mínimo (1KB)
    const minSize = 1024; // 1KB
    if (file.size < minSize) {
      return {
        valid: false,
        error: `Arquivo muito pequeno. Tamanho mínimo: ${this.formatFileSize(minSize)}`
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
  generateValidationReport(validation: ValidacaoFIDC): string {
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
