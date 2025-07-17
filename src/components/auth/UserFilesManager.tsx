import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { supabaseExcelService } from '../../services/supabaseExcelService';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { FileText, Download, Trash2, RefreshCw, Calendar, User } from 'lucide-react';

interface FileInfo {
  id: string;
  name: string;
  size: number;
  created_at: string;
  last_accessed_at: string;
  metadata: any;
}

export const UserFilesManager: React.FC = () => {
  const { user } = useAuth();
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cache key para arquivos do usuário
  const filesStorageKey = `user_files_${user?.id || 'anonymous'}`;

  const loadFiles = async () => {
    if (!user) return;
    
    setLoading(true);
    setError(null);

    try {
      // Tentar carregar do cache primeiro
      const cachedFiles = localStorage.getItem(filesStorageKey);
      if (cachedFiles) {
        try {
          const parsedFiles = JSON.parse(cachedFiles) as FileInfo[];
          setFiles(parsedFiles);
          setLoading(false); // Mostrar cache enquanto carrega dados atualizados
        } catch (e) {
          localStorage.removeItem(filesStorageKey);
        }
      }

      // Carregar dados atualizados do Supabase
      const result = await supabaseExcelService.listFiles(user.id);
      
      if (result.success) {
        setFiles(result.files);
        // Salvar no cache
        localStorage.setItem(filesStorageKey, JSON.stringify(result.files));
      } else {
        setError(result.error || 'Erro ao carregar arquivos');
      }
    } catch (err) {
      setError('Erro inesperado ao carregar arquivos');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFile = async (filePath: string) => {
    if (!confirm('Tem certeza que deseja excluir este arquivo?')) {
      return;
    }

    try {
      const result = await supabaseExcelService.deleteFile(filePath);
      
      if (result.success) {
        await loadFiles(); // Recarregar lista
      } else {
        setError(result.error || 'Erro ao excluir arquivo');
      }
    } catch (err) {
      setError('Erro inesperado ao excluir arquivo');
    }
  };

  const formatFileSize = (bytes: number) => {
    return supabaseExcelService.formatFileSize(bytes);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    return <FileText className="h-4 w-4" />;
  };

  useEffect(() => {
    loadFiles();

    // Escutar eventos de novos uploads
    const handleNewUpload = () => {
      // Atualizar lista após um pequeno delay para garantir que o upload foi processado
      setTimeout(() => {
        loadFiles();
      }, 1000);
    };

    // Escutar mudanças no localStorage de uploads
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key?.includes('arquivos_carregados_') && e.newValue) {
        handleNewUpload();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    // Custom event para atualizações internas
    window.addEventListener('newFileUploaded', handleNewUpload);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('newFileUploaded', handleNewUpload);
    };
  }, [user]);

  if (!user) {
    return null;
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Meus Arquivos
            </CardTitle>
            <CardDescription>
              Arquivos enviados para processamento FIDC
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadFiles}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            Carregando arquivos...
          </div>
        ) : files.length === 0 ? (
          <div className="text-center p-8 text-gray-500">
            <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg mb-2">Nenhum arquivo encontrado</p>
            <p className="text-sm">Envie arquivos através do módulo de carregamento</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Badge variant="secondary">
                {files.length} arquivo{files.length !== 1 ? 's' : ''}
              </Badge>
              <span className="text-sm text-gray-500">
                Total: {formatFileSize(files.reduce((acc, file) => acc + file.size, 0))}
              </span>
            </div>
            
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Arquivo</TableHead>
                  <TableHead>Tamanho</TableHead>
                  <TableHead>Criado em</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {files.map((file) => (
                  <TableRow key={file.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {getFileIcon(file.name)}
                        <span className="truncate max-w-xs">{file.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {formatFileSize(file.size)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Calendar className="h-3 w-3" />
                        {formatDate(file.created_at)}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center gap-2 justify-end">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteFile(`energisa-uploads/${user.id}/${file.name}`)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
