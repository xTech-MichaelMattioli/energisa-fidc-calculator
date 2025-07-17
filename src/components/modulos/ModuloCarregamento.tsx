import { useState, useRef, useCallback, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Upload, 
  FileText, 
  ArrowRight, 
  CheckCircle, 
  AlertTriangle,
  Database,
  Info,
  X
} from "lucide-react";
import DataService, { ArquivoBase } from "@/services/dataService";
import { supabaseExcelService } from "@/services/supabaseExcelService";
import { useAuth } from "@/contexts/AuthContext";
import { fileCache, CachedFile } from "@/utils/fileCache";

interface ArquivoCarregado extends CachedFile {}

export function ModuloCarregamento() {
  const { user } = useAuth();
  const [arquivos, setArquivos] = useState<ArquivoCarregado[]>([]);
  const [processandoArquivo, setProcessandoArquivo] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dataService = DataService.getInstance();

  // Carregar arquivos do cache ao inicializar
  useEffect(() => {
    if (user?.id) {
      const cachedFiles = fileCache.loadFiles(user.id);
      setArquivos(cachedFiles);
    }
  }, [user?.id]);

  // Escutar mudanças no cache de outras abas/componentes
  useEffect(() => {
    const handleCacheUpdate = (event: CustomEvent) => {
      if (event.detail.userId === user?.id) {
        setArquivos(event.detail.files);
      }
    };

    const handleCacheCleared = (event: CustomEvent) => {
      if (event.detail.userId === user?.id) {
        setArquivos([]);
      }
    };

    window.addEventListener('fileCacheUpdated', handleCacheUpdate as EventListener);
    window.addEventListener('fileCacheCleared', handleCacheCleared as EventListener);

    return () => {
      window.removeEventListener('fileCacheUpdated', handleCacheUpdate as EventListener);
      window.removeEventListener('fileCacheCleared', handleCacheCleared as EventListener);
    };
  }, [user?.id]);

  const handleFileUpload = useCallback((event: any) => {
    const files = Array.from(event.target.files || []) as File[];
    
    files.forEach(file => {
      // Verificar se já existe um arquivo com o mesmo nome usando o cache
      if (user?.id && fileCache.fileExists(user.id, file.name)) {
        alert(`O arquivo "${file.name}" já foi carregado anteriormente.`);
        return;
      }

      // Verificar tipo de arquivo
      if (!file.name.match(/\.(xlsx|xls|csv)$/i)) {
        const arquivoErro: ArquivoCarregado = {
          nome: file.name,
          tamanho: file.size,
          tipo: file.type,
          status: 'erro',
          erro: 'Formato não suportado. Use Excel (.xlsx, .xls) ou CSV (.csv)'
        };
        setArquivos(prev => [...prev, arquivoErro]);
        return;
      }

      const novoArquivo: ArquivoCarregado = {
        nome: file.name,
        tamanho: file.size,
        tipo: file.type,
        status: 'carregado',
        progresso: 0
      };

      setArquivos(prev => [...prev, novoArquivo]);
      
      // Processar arquivo real
      setTimeout(() => processarArquivoReal(file), 500);
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [user?.id]);

  const processarArquivoReal = async (file: File) => {
    setProcessandoArquivo(file.name);
    
    // Atualizar status para processando
    setArquivos(prev => prev.map(arq => 
      arq.nome === file.name 
        ? { ...arq, status: 'processando', progresso: 0 }
        : arq
    ));

    try {
      // Fazer upload do arquivo para o Supabase Storage
      console.log('📤 Fazendo upload para Supabase Storage:', {
        nome: file.name,
        tamanho: supabaseExcelService.formatFileSize(file.size),
        tipo: file.type
      });
      
      const uploadResult = await supabaseExcelService.smartUpload(
        file, 
        user?.id,
        (progress) => {
          setArquivos(prev => prev.map(arq => 
            arq.nome === file.name 
              ? { ...arq, progresso: Math.round(progress.percentage) }
              : arq
          ));
        }
      );
      
      if (!uploadResult.success) {
        throw new Error(`Erro no upload: ${uploadResult.error}`);
      }
      
      console.log('✅ Upload concluído:', {
        url: uploadResult.fileUrl,
        tamanho: supabaseExcelService.formatFileSize(uploadResult.fileSize),
        tempo: uploadResult.uploadTime + 'ms'
      });
      
      // Arquivo carregado com sucesso
      const arquivoCarregado: ArquivoCarregado = { 
        nome: file.name,
        tamanho: file.size,
        tipo: file.type,
        status: 'carregado',
        progresso: 100,
        fileUrl: uploadResult.fileUrl
      };

      setArquivos(prev => prev.map(arq => 
        arq.nome === file.name ? arquivoCarregado : arq
      ));

      // Salvar no cache
      if (user?.id) {
        fileCache.addFile(user.id, arquivoCarregado);
      }

      // Disparar evento para outros componentes saberem do novo upload
      window.dispatchEvent(new CustomEvent('newFileUploaded', { 
        detail: { fileName: file.name, fileUrl: uploadResult.fileUrl } 
      }));

    } catch (error) {
      console.error('Erro ao fazer upload:', error);
      
      setArquivos(prev => prev.map(arq => 
        arq.nome === file.name 
          ? { 
              ...arq, 
              status: 'erro',
              progresso: 100,
              erro: `Erro no upload: ${error instanceof Error ? error.message : 'Erro desconhecido'}`
            }
          : arq
      ));
    }

    setProcessandoArquivo(null);
  };

  const removerArquivo = (nomeArquivo: string) => {
    setArquivos(prev => prev.filter(arq => arq.nome !== nomeArquivo));
    
    // Remover do cache
    if (user?.id) {
      fileCache.removeFile(user.id, nomeArquivo);
    }
  };

  const limparCache = () => {
    if (user?.id) {
      fileCache.clearCache(user.id);
    }
  };

  const formatarTamanho = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const todosArquivosMapeados = arquivos.length > 0 && arquivos.every(arq => arq.status === 'carregado');

  const passarProximoModulo = () => {
    const dadosCarregamento = {
      arquivos: arquivos.map(arq => ({
        nome: arq.nome
      })),
      dataProcessamento: new Date().toISOString()
    };
    
    localStorage.setItem('dadosCarregamento', JSON.stringify(dadosCarregamento));
    window.location.href = '/mapeamento';
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header do Módulo */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-slate-800 flex items-center justify-center gap-3">
          <Database className="h-8 w-8 text-cyan-600" />
          Módulo 1: Carregamento de Dados
        </h1>
        <p className="text-lg text-slate-600">
          Upload das bases de dados com memória persistente
        </p>
      </div>

      {/* Informações discretas sobre estrutura FIDC */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload de Arquivos
          </CardTitle>
          <CardDescription>
            Faça upload dos arquivos CSV ou Excel das bases das distribuidoras.
            Os arquivos são sincronizados automaticamente com o Storage.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">

            {/* Formatos suportados - versão compacta */}
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-700">
                  <strong>Formatos:</strong> Excel (.xlsx, .xls) • <strong>Tamanho máximo:</strong> 100MB
                </p>
                {arquivos.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {arquivos.filter(arq => arq.status === 'carregado').length} arquivo(s) na memória
                    </Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={limparCache}
                      className="text-xs h-6 px-2"
                    >
                      Limpar
                    </Button>
                  </div>
                )}
              </div>
            </div>
            
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-cyan-400 transition-colors">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                multiple
                onChange={handleFileUpload}
                className="hidden"
              />
              <div className="space-y-4">
                <div className="mx-auto w-12 h-12 bg-cyan-100 rounded-full flex items-center justify-center">
                  <Upload className="h-6 w-6 text-cyan-600" />
                </div>
                <div>
                  <p className="text-lg font-medium text-slate-900">
                    Clique para fazer upload ou arraste arquivos aqui
                  </p>
                  <p className="text-sm text-slate-500">
                    Suporte para CSV, Excel (.xlsx, .xls) - Máximo 100MB por arquivo
                  </p>
                  {arquivos.length > 0 && (
                    <p className="text-xs text-green-600 mt-1">
                      💾 Arquivos carregados são mantidos na memória entre mudanças de tela
                    </p>
                  )}
                </div>
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-gradient-to-r from-cyan-500 to-blue-500"
                >
                  Selecionar Arquivos
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Arquivos Carregados */}
      {arquivos.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Arquivos Carregados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {arquivos.map((arquivo) => (
                <div key={arquivo.nome} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-slate-500" />
                      <div>
                        <p className="font-medium">{arquivo.nome}</p>
                        <p className="text-sm text-slate-500">
                          {formatarTamanho(arquivo.tamanho)} • {arquivo.tipo}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={
                        arquivo.status === 'carregado' ? 'default' :
                        arquivo.status === 'processando' ? 'secondary' :
                        arquivo.status === 'erro' ? 'destructive' : 'outline'
                      }>
                        {arquivo.status === 'carregado' && <CheckCircle className="h-3 w-3 mr-1" />}
                        {arquivo.status === 'erro' && <AlertTriangle className="h-3 w-3 mr-1" />}
                        {arquivo.status === 'carregado' ? 'Carregado' : arquivo.status}
                      </Badge>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => removerArquivo(arquivo.nome)}
                        disabled={arquivo.status === 'processando'}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {(arquivo.status === 'processando') && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Enviando para Supabase Storage...</span>
                        <span>{arquivo.progresso}%</span>
                      </div>
                      <Progress value={arquivo.progresso} className="h-2" />
                    </div>
                  )}

                  {arquivo.status === 'carregado' && (
                    <div className="text-sm text-green-600">
                      <p>✅ Arquivo salvo no Storage e mantido na memória local</p>
                    </div>
                  )}

                  {arquivo.status === 'erro' && (
                    <div className="text-sm text-red-600">
                      <p>Erro: {arquivo.erro}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Botão de Próximo Módulo */}
      <Card className={todosArquivosMapeados ? "border-green-200 bg-green-50" : "border-slate-200"}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold flex items-center gap-2">
                <Info className="h-5 w-5" />
                Status do Upload
              </h3>
              <p className="text-sm text-slate-600">
                {arquivos.filter(arq => arq.status === 'carregado').length} de {arquivos.length} arquivo(s) carregado(s)
              </p>
            </div>
            
            <Button
              onClick={passarProximoModulo}
              disabled={!todosArquivosMapeados}
              size="lg"
              className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
            >
              Prosseguir para Mapeamento
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}