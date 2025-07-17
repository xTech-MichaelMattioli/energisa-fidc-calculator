/**
 * Utilitário para gerenciar cache de arquivos no localStorage
 * Mantém sincronização entre diferentes componentes e abas
 */

export interface CachedFile {
  nome: string;
  tamanho: number;
  tipo: string;
  status: 'carregado' | 'processando' | 'erro';
  erro?: string;
  progresso?: number;
  uploadedAt?: string;
  fileUrl?: string;
}

export class FileCache {
  private static instance: FileCache;
  
  static getInstance(): FileCache {
    if (!FileCache.instance) {
      FileCache.instance = new FileCache();
    }
    return FileCache.instance;
  }

  private getStorageKey(userId: string): string {
    return `arquivos_carregados_${userId}`;
  }

  /**
   * Salva arquivos no cache local
   */
  saveFiles(userId: string, files: CachedFile[]): void {
    try {
      const validFiles = files.filter(file => file.status === 'carregado');
      const key = this.getStorageKey(userId);
      localStorage.setItem(key, JSON.stringify(validFiles));
      
      // Disparar evento para sincronização
      window.dispatchEvent(new CustomEvent('fileCacheUpdated', {
        detail: { userId, files: validFiles }
      }));
    } catch (error) {
      console.error('Erro ao salvar arquivos no cache:', error);
    }
  }

  /**
   * Carrega arquivos do cache local
   */
  loadFiles(userId: string): CachedFile[] {
    try {
      const key = this.getStorageKey(userId);
      const cached = localStorage.getItem(key);
      return cached ? JSON.parse(cached) : [];
    } catch (error) {
      console.error('Erro ao carregar arquivos do cache:', error);
      return [];
    }
  }

  /**
   * Adiciona um novo arquivo ao cache
   */
  addFile(userId: string, file: CachedFile): void {
    const existingFiles = this.loadFiles(userId);
    const filteredFiles = existingFiles.filter(f => f.nome !== file.nome);
    const updatedFiles = [...filteredFiles, { ...file, uploadedAt: new Date().toISOString() }];
    this.saveFiles(userId, updatedFiles);
  }

  /**
   * Remove um arquivo do cache
   */
  removeFile(userId: string, fileName: string): void {
    const existingFiles = this.loadFiles(userId);
    const filteredFiles = existingFiles.filter(f => f.nome !== fileName);
    this.saveFiles(userId, filteredFiles);
  }

  /**
   * Limpa todo o cache do usuário
   */
  clearCache(userId: string): void {
    const key = this.getStorageKey(userId);
    localStorage.removeItem(key);
    
    // Disparar evento para sincronização
    window.dispatchEvent(new CustomEvent('fileCacheCleared', {
      detail: { userId }
    }));
  }

  /**
   * Verifica se um arquivo já existe no cache
   */
  fileExists(userId: string, fileName: string): boolean {
    const files = this.loadFiles(userId);
    return files.some(f => f.nome === fileName);
  }

  /**
   * Obtém estatísticas do cache
   */
  getCacheStats(userId: string): { count: number; totalSize: number } {
    const files = this.loadFiles(userId);
    return {
      count: files.length,
      totalSize: files.reduce((total, file) => total + file.tamanho, 0)
    };
  }
}

export const fileCache = FileCache.getInstance();
