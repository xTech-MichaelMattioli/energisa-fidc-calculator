import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Download, FileText, Database, Mail, Settings, CheckCircle, AlertCircle, Clock } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/hooks/use-toast";

export function ModuloExportacao() {
  const navigate = useNavigate();
  const [exportData, setExportData] = useState<any>({});
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['excel']);
  const [exportProgress, setExportProgress] = useState(0);
  const [isExporting, setIsExporting] = useState(false);
  const [exportComplete, setExportComplete] = useState(false);

  useEffect(() => {
    // Load all processed data
    const correctionData = JSON.parse(localStorage.getItem('correctionData') || '[]');
    const analysisResults = JSON.parse(localStorage.getItem('analysisResults') || '{}');
    const agingData = JSON.parse(localStorage.getItem('agingData') || '[]');
    
    setExportData({
      correctionData,
      analysisResults,
      agingData,
      totalRecords: correctionData.length,
      totalValue: correctionData.reduce((sum: number, item: any) => sum + item.valorCorrigido, 0)
    });
  }, []);

  const exportFormats = [
    {
      id: 'excel',
      name: 'Excel (.xlsx)',
      description: 'Planilha com dados detalhados',
      icon: FileText,
      size: '2.3 MB'
    },
    {
      id: 'csv',
      name: 'CSV (.csv)',
      description: 'Dados separados por vírgula',
      icon: Database,
      size: '1.1 MB'
    },
    {
      id: 'pdf',
      name: 'PDF (.pdf)',
      description: 'Relatório formatado',
      icon: FileText,
      size: '4.7 MB'
    },
    {
      id: 'json',
      name: 'JSON (.json)',
      description: 'Dados estruturados',
      icon: Database,
      size: '890 KB'
    }
  ];

  const handleFormatToggle = (formatId: string) => {
    setSelectedFormats(prev => 
      prev.includes(formatId) 
        ? prev.filter(id => id !== formatId)
        : [...prev, formatId]
    );
  };

  const handleExport = async () => {
    if (selectedFormats.length === 0) {
      toast({
        title: "Erro",
        description: "Selecione pelo menos um formato para exportação.",
        variant: "destructive"
      });
      return;
    }

    setIsExporting(true);
    setExportProgress(0);

    // Simulate export progress
    const interval = setInterval(() => {
      setExportProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsExporting(false);
          setExportComplete(true);
          toast({
            title: "Exportação Concluída",
            description: "Todos os arquivos foram gerados com sucesso!",
          });
          return 100;
        }
        return prev + 10;
      });
    }, 300);
  };

  const handleFinish = () => {
    toast({
      title: "Processo Finalizado",
      description: "Todos os módulos foram concluídos com sucesso!",
    });
    navigate('/');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg">
          <Download className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Módulo 4: Exportação</h1>
          <p className="text-slate-600">Exportação dos resultados processados</p>
        </div>
      </div>

      <Tabs defaultValue="resumo" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="setup">Setup</TabsTrigger>
          <TabsTrigger value="resumo">Resumo</TabsTrigger>
          <TabsTrigger value="formatos">Formatos</TabsTrigger>
          <TabsTrigger value="configuracao">Configuração</TabsTrigger>
          <TabsTrigger value="exportar">Exportar</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-indigo-600" />
                Configurações do Sistema
              </CardTitle>
              <CardDescription>
                Parâmetros transferidos dos módulos anteriores
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-sm font-medium">Nome do Projeto</Label>
                <Input defaultValue="FIDC - Energisa Data Refactor" className="mt-1" />
              </div>
              
              <div>
                <Label className="text-sm font-medium">Período de Referência</Label>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <Input type="date" />
                  <Input type="date" />
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Responsável</Label>
                <Input placeholder="Nome do responsável" className="mt-1" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resumo" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <FileText className="h-5 w-5 text-indigo-600" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-600">Total de Registros</p>
                    <p className="text-2xl font-bold text-indigo-600">{exportData.totalRecords || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Database className="h-5 w-5 text-emerald-600" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-600">Valor Total</p>
                    <p className="text-2xl font-bold text-emerald-600">
                      R$ {(exportData.totalValue || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-600">Status</p>
                    <p className="text-2xl font-bold text-green-600">Pronto</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Dados Processados</CardTitle>
              <CardDescription>
                Resumo dos dados disponíveis para exportação
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">Dados de Correção</h3>
                    <Badge className="bg-emerald-100 text-emerald-800">Processado</Badge>
                  </div>
                  <p className="text-sm text-slate-600">
                    {exportData.correctionData?.length || 0} registros com valores corrigidos
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">Dados de Aging</h3>
                    <Badge className="bg-blue-100 text-blue-800">Processado</Badge>
                  </div>
                  <p className="text-sm text-slate-600">
                    {exportData.agingData?.length || 0} registros com cálculo de aging
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">Análise de Resultados</h3>
                    <Badge className="bg-purple-100 text-purple-800">Processado</Badge>
                  </div>
                  <p className="text-sm text-slate-600">
                    Indicadores e métricas de performance
                  </p>
                </div>

                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">Relatórios</h3>
                    <Badge className="bg-orange-100 text-orange-800">Disponível</Badge>
                  </div>
                  <p className="text-sm text-slate-600">
                    Relatórios executivos e detalhados
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="formatos" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Formatos de Exportação</CardTitle>
              <CardDescription>
                Selecione os formatos desejados para exportação
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {exportFormats.map((format) => (
                  <div key={format.id} className="flex items-center space-x-3 p-4 border rounded-lg">
                    <Checkbox
                      id={format.id}
                      checked={selectedFormats.includes(format.id)}
                      onCheckedChange={() => handleFormatToggle(format.id)}
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <format.icon className="h-4 w-4 text-slate-600" />
                        <Label htmlFor={format.id} className="font-medium cursor-pointer">
                          {format.name}
                        </Label>
                      </div>
                      <p className="text-sm text-slate-600 mt-1">{format.description}</p>
                      <p className="text-xs text-slate-500 mt-1">Tamanho estimado: {format.size}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="configuracao" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5 text-indigo-600" />
                  Configurações de Exportação
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm font-medium">Nome do Arquivo</Label>
                  <Input placeholder="relatorio_fidc_2024" className="mt-1" />
                </div>

                <div>
                  <Label className="text-sm font-medium">Prefixo do Arquivo</Label>
                  <Input placeholder="FIDC_" className="mt-1" />
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Opções Adicionais</Label>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox id="includeHeaders" defaultChecked />
                      <Label htmlFor="includeHeaders" className="text-sm">Incluir cabeçalhos</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox id="includeFormulas" />
                      <Label htmlFor="includeFormulas" className="text-sm">Incluir fórmulas (Excel)</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox id="compressFiles" defaultChecked />
                      <Label htmlFor="compressFiles" className="text-sm">Compactar arquivos</Label>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5 text-indigo-600" />
                  Notificações
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm font-medium">Email para Notificação</Label>
                  <Input type="email" placeholder="usuario@empresa.com" className="mt-1" />
                </div>

                <div>
                  <Label className="text-sm font-medium">Mensagem Personalizada</Label>
                  <Textarea 
                    placeholder="Adicione uma mensagem personalizada para o relatório..."
                    className="mt-1"
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox id="emailOnComplete" defaultChecked />
                    <Label htmlFor="emailOnComplete" className="text-sm">
                      Enviar email ao concluir
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox id="includeLinks" />
                    <Label htmlFor="includeLinks" className="text-sm">
                      Incluir links para download
                    </Label>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="exportar" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Exportação de Dados</CardTitle>
              <CardDescription>
                Execute a exportação dos dados processados
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {!isExporting && !exportComplete && (
                <div>
                  <Alert className="mb-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Verifique as configurações antes de iniciar a exportação. 
                      Formatos selecionados: {selectedFormats.join(', ')}
                    </AlertDescription>
                  </Alert>

                  <div className="text-center">
                    <Button onClick={handleExport} className="bg-indigo-600 hover:bg-indigo-700">
                      <Download className="h-4 w-4 mr-2" />
                      Iniciar Exportação
                    </Button>
                  </div>
                </div>
              )}

              {isExporting && (
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="inline-flex items-center gap-2 mb-4">
                      <Clock className="h-5 w-5 text-indigo-600 animate-spin" />
                      <span className="text-indigo-600 font-medium">Exportando dados...</span>
                    </div>
                  </div>
                  <Progress value={exportProgress} className="w-full" />
                  <p className="text-center text-sm text-slate-600">
                    {exportProgress}% - Gerando arquivos nos formatos selecionados
                  </p>
                </div>
              )}

              {exportComplete && (
                <div className="space-y-6">
                  <div className="text-center">
                    <div className="inline-flex items-center gap-2 mb-4">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                      <span className="text-green-600 font-medium text-lg">Exportação Concluída!</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedFormats.map((formatId) => {
                      const format = exportFormats.find(f => f.id === formatId);
                      return format ? (
                        <div key={formatId} className="p-4 border rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <format.icon className="h-4 w-4 text-slate-600" />
                              <span className="font-medium">{format.name}</span>
                            </div>
                            <Badge className="bg-green-100 text-green-800">Pronto</Badge>
                          </div>
                          <p className="text-sm text-slate-600 mb-3">{format.size}</p>
                          <Button size="sm" variant="outline" className="w-full">
                            <Download className="h-4 w-4 mr-2" />
                            Baixar Arquivo
                          </Button>
                        </div>
                      ) : null;
                    })}
                  </div>

                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      Todos os arquivos foram gerados com sucesso e estão prontos para download. 
                      Os dados incluem correção monetária, aging e análises completas.
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-between items-center pt-6 border-t">
        <Button variant="outline" onClick={() => navigate('/analise')}>
          Voltar à Análise
        </Button>
        {exportComplete && (
          <Button onClick={handleFinish} className="bg-green-600 hover:bg-green-700">
            Finalizar Processo
          </Button>
        )}
      </div>
    </div>
  );
}