import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PieChart, BarChart3, TrendingUp, FileText, Download, Eye } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

export function ModuloAnalise() {
  const navigate = useNavigate();
  const [analysisData, setAnalysisData] = useState<any>({});
  
  useEffect(() => {
    // Load data from previous modules
    const correctionData = JSON.parse(localStorage.getItem('correctionData') || '[]');
    const agingData = JSON.parse(localStorage.getItem('agingData') || '[]');
    
    // Calculate analysis metrics
    const totalOriginal = correctionData.reduce((sum: number, item: any) => sum + item.valorOriginal, 0);
    const totalCorrigido = correctionData.reduce((sum: number, item: any) => sum + item.valorCorrigido, 0);
    const totalJuros = totalCorrigido - totalOriginal;
    
    // Age distribution
    const ageDistribution = {
      '0-30': correctionData.filter((item: any) => item.diasAtraso <= 30).length,
      '31-60': correctionData.filter((item: any) => item.diasAtraso > 30 && item.diasAtraso <= 60).length,
      '61-90': correctionData.filter((item: any) => item.diasAtraso > 60 && item.diasAtraso <= 90).length,
      '90+': correctionData.filter((item: any) => item.diasAtraso > 90).length,
    };
    
    setAnalysisData({
      correctionData,
      agingData,
      totals: { totalOriginal, totalCorrigido, totalJuros },
      ageDistribution,
      recoveryRate: 65.4,
      provisionsNeeded: totalCorrigido * 0.15
    });
  }, []);

  const handleNextModule = () => {
    // Save analysis results
    localStorage.setItem('analysisResults', JSON.stringify(analysisData));
    navigate('/exportacao');
  };

  const summaryData = [
    {
      title: "Registros Analisados",
      value: analysisData.correctionData?.length || 0,
      icon: FileText,
      color: "text-blue-600"
    },
    {
      title: "Valor Original Total",
      value: `R$ ${(analysisData.totals?.totalOriginal || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
      icon: TrendingUp,
      color: "text-slate-600"
    },
    {
      title: "Valor Corrigido Total",
      value: `R$ ${(analysisData.totals?.totalCorrigido || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
      icon: TrendingUp,
      color: "text-emerald-600"
    },
    {
      title: "Total de Juros",
      value: `R$ ${(analysisData.totals?.totalJuros || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
      icon: TrendingUp,
      color: "text-orange-600"
    }
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-lg">
          <PieChart className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Módulo 7: Análise</h1>
          <p className="text-slate-600">Análise detalhada dos resultados da correção</p>
        </div>
      </div>

      <Tabs defaultValue="resumo" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="resumo">Resumo</TabsTrigger>
          <TabsTrigger value="distribuicao">Distribuição</TabsTrigger>
          <TabsTrigger value="detalhamento">Detalhamento</TabsTrigger>
          <TabsTrigger value="relatorios">Relatórios</TabsTrigger>
        </TabsList>

        <TabsContent value="resumo" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {summaryData.map((item) => (
              <Card key={item.title}>
                <CardContent className="p-6">
                  <div className="flex items-center space-x-2">
                    <item.icon className={`h-5 w-5 ${item.color}`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-600">{item.title}</p>
                      <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-purple-600" />
                  Indicadores de Performance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Taxa de Recuperação</span>
                    <span className="text-sm font-medium">{analysisData.recoveryRate}%</span>
                  </div>
                  <Progress value={analysisData.recoveryRate} className="h-2" />
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Eficiência da Cobrança</span>
                    <span className="text-sm font-medium">78.2%</span>
                  </div>
                  <Progress value={78.2} className="h-2" />
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Provisão Necessária</span>
                    <span className="text-sm font-medium">
                      R$ {(analysisData.provisionsNeeded || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Impacto Financeiro</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between py-2 border-b">
                  <span className="text-sm text-slate-600">Valor Original</span>
                  <span className="font-medium">
                    R$ {(analysisData.totals?.totalOriginal || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-sm text-slate-600">Correção Monetária</span>
                  <span className="font-medium text-emerald-600">
                    R$ {(analysisData.totals?.totalJuros || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-sm text-slate-600">Valor Total</span>
                  <span className="font-bold text-lg">
                    R$ {(analysisData.totals?.totalCorrigido || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-sm text-slate-600">Incremento (%)</span>
                  <span className="font-medium text-orange-600">
                    {analysisData.totals?.totalOriginal ? 
                      ((analysisData.totals.totalJuros / analysisData.totals.totalOriginal) * 100).toFixed(2) : 0}%
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="distribuicao" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Distribuição por Faixa de Atraso</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(analysisData.ageDistribution || {}).map(([range, count]) => (
                    <div key={range} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-4 h-4 bg-gradient-to-r from-purple-500 to-indigo-500 rounded"></div>
                        <span className="text-sm">{range} dias</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium">{count as number} registros</span>
                        <Badge variant="outline">
                          {analysisData.correctionData?.length ? 
                            ((count as number / analysisData.correctionData.length) * 100).toFixed(1) : 0}%
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Análise de Risco</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Risco Baixo (0-30 dias)</span>
                    <Badge className="bg-green-100 text-green-800">
                      {analysisData.ageDistribution?.['0-30'] || 0} registros
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Risco Médio (31-60 dias)</span>
                    <Badge className="bg-yellow-100 text-yellow-800">
                      {analysisData.ageDistribution?.['31-60'] || 0} registros
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Risco Alto (61-90 dias)</span>
                    <Badge className="bg-orange-100 text-orange-800">
                      {analysisData.ageDistribution?.['61-90'] || 0} registros
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Risco Crítico (90+ dias)</span>
                    <Badge className="bg-red-100 text-red-800">
                      {analysisData.ageDistribution?.['90+'] || 0} registros
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="detalhamento" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Detalhamento por Registro</CardTitle>
              <CardDescription>
                Análise individual dos valores corrigidos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Valor Original</TableHead>
                      <TableHead>Valor Corrigido</TableHead>
                      <TableHead>Incremento</TableHead>
                      <TableHead>Dias Atraso</TableHead>
                      <TableHead>Classificação</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(analysisData.correctionData || []).map((item: any) => {
                      const incremento = ((item.juros / item.valorOriginal) * 100).toFixed(2);
                      const classificacao = item.diasAtraso <= 30 ? 'Baixo' : 
                                          item.diasAtraso <= 60 ? 'Médio' :
                                          item.diasAtraso <= 90 ? 'Alto' : 'Crítico';
                      const statusColor = classificacao === 'Baixo' ? 'bg-green-100 text-green-800' :
                                        classificacao === 'Médio' ? 'bg-yellow-100 text-yellow-800' :
                                        classificacao === 'Alto' ? 'bg-orange-100 text-orange-800' :
                                        'bg-red-100 text-red-800';
                      
                      return (
                        <TableRow key={item.id}>
                          <TableCell>{item.id}</TableCell>
                          <TableCell>
                            R$ {item.valorOriginal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </TableCell>
                          <TableCell className="font-medium text-emerald-600">
                            R$ {item.valorCorrigido.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </TableCell>
                          <TableCell className="text-orange-600">+{incremento}%</TableCell>
                          <TableCell>{item.diasAtraso} dias</TableCell>
                          <TableCell>
                            <Badge className={statusColor}>
                              {classificacao}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">Processado</Badge>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="relatorios" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-purple-600" />
                Relatórios Disponíveis
              </CardTitle>
              <CardDescription>
                Gere relatórios detalhados da análise
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">Relatório Executivo</h3>
                    <Eye className="h-4 w-4 text-slate-400" />
                  </div>
                  <p className="text-sm text-slate-600 mb-3">
                    Resumo executivo com indicadores principais
                  </p>
                  <Button size="sm" variant="outline" className="w-full">
                    <Download className="h-4 w-4 mr-2" />
                    Baixar PDF
                  </Button>
                </div>

                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">Relatório Detalhado</h3>
                    <Eye className="h-4 w-4 text-slate-400" />
                  </div>
                  <p className="text-sm text-slate-600 mb-3">
                    Análise completa com todos os registros
                  </p>
                  <Button size="sm" variant="outline" className="w-full">
                    <Download className="h-4 w-4 mr-2" />
                    Baixar Excel
                  </Button>
                </div>

                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">Dashboard Interativo</h3>
                    <Eye className="h-4 w-4 text-slate-400" />
                  </div>
                  <p className="text-sm text-slate-600 mb-3">
                    Visualizações interativas dos dados
                  </p>
                  <Button size="sm" variant="outline" className="w-full">
                    <Eye className="h-4 w-4 mr-2" />
                    Visualizar
                  </Button>
                </div>

                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">Análise Comparativa</h3>
                    <Eye className="h-4 w-4 text-slate-400" />
                  </div>
                  <p className="text-sm text-slate-600 mb-3">
                    Comparação com períodos anteriores
                  </p>
                  <Button size="sm" variant="outline" className="w-full">
                    <Download className="h-4 w-4 mr-2" />
                    Baixar Relatório
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="flex justify-between items-center pt-6 border-t">
        <Button variant="outline" onClick={() => navigate('/correcao')}>
          Voltar à Correção
        </Button>
        <Button onClick={handleNextModule} className="bg-purple-600 hover:bg-purple-700">
          Continuar para Exportação
        </Button>
      </div>
    </div>
  );
}