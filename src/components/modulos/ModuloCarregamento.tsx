import { useState, useRef, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Upload, 
  FileText, 
  ArrowRight, 
  CheckCircle, 
  AlertTriangle,
  Database,
  Info,
  Target,
  X
} from "lucide-react";

interface ArquivoCarregado {
  nome: string;
  tamanho: number;
  tipo: string;
  status: 'carregado' | 'processando' | 'mapeado' | 'erro';
  registros?: number;
  colunas?: string[];
  preview?: any[];
  erro?: string;
  progresso?: number;
}

export function ModuloCarregamento() {
  const [arquivos, setArquivos] = useState<ArquivoCarregado[]>([]);
  const [processandoArquivo, setProcessandoArquivo] = useState<string | null>(null);
  const [abaAtiva, setAbaAtiva] = useState("upload");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    files.forEach(file => {
      const novoArquivo: ArquivoCarregado = {
        nome: file.name,
        tamanho: file.size,
        tipo: file.type,
        status: 'carregado',
        progresso: 0
      };

      setArquivos(prev => [...prev, novoArquivo]);
      
      // Simular processamento
      setTimeout(() => processarArquivo(file.name), 500);
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const processarArquivo = async (nomeArquivo: string) => {
    setProcessandoArquivo(nomeArquivo);
    
    // Atualizar status para processando
    setArquivos(prev => prev.map(arq => 
      arq.nome === nomeArquivo 
        ? { ...arq, status: 'processando', progresso: 0 }
        : arq
    ));

    // Simular processamento com progresso
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 200));
      
      setArquivos(prev => prev.map(arq => 
        arq.nome === nomeArquivo 
          ? { ...arq, progresso: i }
          : arq
      ));
    }

    // Simular análise do arquivo
    const registrosSimulados = Math.floor(Math.random() * 50000) + 10000;
    const colunasSimuladas = [
      'ID_CONTRATO', 'NOME_CLIENTE', 'CPF_CNPJ', 'VALOR_ORIGINAL', 
      'DATA_VENCIMENTO', 'DATA_OPERACAO', 'STATUS', 'PRODUTO', 
      'AGENCIA', 'CONTA'
    ];
    
    const previewSimulado = Array.from({ length: 5 }, (_, i) => ({
      ID_CONTRATO: `CNT${String(i + 1).padStart(6, '0')}`,
      NOME_CLIENTE: `Cliente ${i + 1}`,
      CPF_CNPJ: `${Math.random().toString().substr(2, 11)}`,
      VALOR_ORIGINAL: (Math.random() * 10000 + 1000).toFixed(2),
      DATA_VENCIMENTO: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      DATA_OPERACAO: new Date(Date.now() - Math.random() * 730 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      STATUS: Math.random() > 0.5 ? 'ATIVO' : 'VENCIDO',
      PRODUTO: Math.random() > 0.5 ? 'CRÉDITO PESSOAL' : 'CARTÃO',
      AGENCIA: `00${Math.floor(Math.random() * 9) + 1}`,
      CONTA: `${Math.random().toString().substr(2, 8)}`
    }));

    // Finalizar processamento
    setArquivos(prev => prev.map(arq => 
      arq.nome === nomeArquivo 
        ? { 
            ...arq, 
            status: 'mapeado',
            progresso: 100,
            registros: registrosSimulados,
            colunas: colunasSimuladas,
            preview: previewSimulado
          }
        : arq
    ));

    setProcessandoArquivo(null);
  };

  const removerArquivo = (nomeArquivo: string) => {
    setArquivos(prev => prev.filter(arq => arq.nome !== nomeArquivo));
  };

  const formatarTamanho = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const todosArquivosMapeados = arquivos.length > 0 && arquivos.every(arq => arq.status === 'mapeado');

  const passarProximoModulo = () => {
    const dadosCarregamento = {
      arquivos: arquivos.map(arq => ({
        nome: arq.nome,
        registros: arq.registros,
        colunas: arq.colunas,
        preview: arq.preview
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
          Upload e análise das bases de dados ESS e Voltz
        </p>
      </div>

      <Tabs value={abaAtiva} onValueChange={setAbaAtiva} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="upload">Upload de Arquivos</TabsTrigger>
          <TabsTrigger value="preview">Preview dos Dados</TabsTrigger>
        </TabsList>
        
        {/* Aba de Upload */}
        <TabsContent value="upload" className="space-y-6">
          {/* Área de Upload */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload de Arquivos
              </CardTitle>
              <CardDescription>
                Faça upload dos arquivos CSV ou Excel das bases ESS e Voltz
              </CardDescription>
            </CardHeader>
            <CardContent>
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
                  </div>
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-gradient-to-r from-cyan-500 to-blue-500"
                  >
                    Selecionar Arquivos
                  </Button>
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
                            arquivo.status === 'mapeado' ? 'default' :
                            arquivo.status === 'processando' ? 'secondary' :
                            arquivo.status === 'erro' ? 'destructive' : 'outline'
                          }>
                            {arquivo.status === 'mapeado' && <CheckCircle className="h-3 w-3 mr-1" />}
                            {arquivo.status === 'erro' && <AlertTriangle className="h-3 w-3 mr-1" />}
                            {arquivo.status}
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

                      {arquivo.status === 'processando' && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Processando arquivo...</span>
                            <span>{arquivo.progresso}%</span>
                          </div>
                          <Progress value={arquivo.progresso} className="h-2" />
                        </div>
                      )}

                      {arquivo.status === 'mapeado' && (
                        <div className="text-sm text-slate-600 space-y-1">
                          <p>• {arquivo.registros?.toLocaleString('pt-BR')} registros encontrados</p>
                          <p>• {arquivo.colunas?.length} colunas identificadas</p>
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
        </TabsContent>

        {/* Aba de Preview */}
        <TabsContent value="preview" className="space-y-6">
          {arquivos.filter(arq => arq.status === 'mapeado').length > 0 ? (
            <div className="space-y-6">
              {arquivos.filter(arq => arq.status === 'mapeado').map((arquivo) => (
                <Card key={arquivo.nome}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      {arquivo.nome}
                    </CardTitle>
                    <CardDescription>
                      {arquivo.registros?.toLocaleString('pt-BR')} registros • {arquivo.colunas?.length} colunas
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            {arquivo.colunas?.slice(0, 6).map((coluna) => (
                              <th key={coluna} className="text-left p-2 font-medium">
                                {coluna}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {arquivo.preview?.map((linha, index) => (
                            <tr key={index} className="border-b">
                              {arquivo.colunas?.slice(0, 6).map((coluna) => (
                                <td key={coluna} className="p-2">
                                  {String(linha[coluna] || '')}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Info className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-500">
                  Nenhum arquivo processado ainda. Faça upload na aba anterior.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Botão de Próximo Módulo */}
      <Card className={todosArquivosMapeados ? "border-green-200 bg-green-50" : "border-slate-200"}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold flex items-center gap-2">
                <Info className="h-5 w-5" />
                Status do Carregamento
              </h3>
              <p className="text-sm text-slate-600">
                {arquivos.filter(arq => arq.status === 'mapeado').length} de {arquivos.length} arquivo(s) processado(s)
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