import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Calculator, TrendingUp, AlertCircle, CheckCircle, DollarSign, Calendar, AlertTriangle } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "@/hooks/use-toast";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import DataService from "@/services/dataService";

export function ModuloCorrecao() {
  const navigate = useNavigate();
  const [isCalculating, setIsCalculating] = useState(false);
  const [calculationProgress, setCalculationProgress] = useState(0);
  const [calculatedData, setCalculatedData] = useState<any[]>([]);
  const [correctionMethod, setCorrectionMethod] = useState("ipca");
  const [selectedRecord, setSelectedRecord] = useState<any>(null);
  const [jurosMora, setJurosMora] = useState(1.0); // Padrão 1%
  const [multa, setMulta] = useState(2.0); // Padrão 2%
  const [showResponsibilityDialog, setShowResponsibilityDialog] = useState(false);
  const [tempJuros, setTempJuros] = useState(1.0);
  const [tempMulta, setTempMulta] = useState(2.0);
  const [isNonStandard, setIsNonStandard] = useState(false);

  // Simulated correction data
  const mockCorrectionData = [
    { 
      id: 1, 
      valorOriginal: 1000.00, 
      valorCorrigido: 1245.30, 
      juros: 245.30, 
      percentualCorrecao: 24.53,
      dataVencimento: "2023-01-15",
      diasAtraso: 365
    },
    { 
      id: 2, 
      valorOriginal: 2500.00, 
      valorCorrigido: 3113.25, 
      juros: 613.25, 
      percentualCorrecao: 24.53,
      dataVencimento: "2023-02-20",
      diasAtraso: 340
    },
    { 
      id: 3, 
      valorOriginal: 750.00, 
      valorCorrigido: 933.98, 
      juros: 183.98, 
      percentualCorrecao: 24.53,
      dataVencimento: "2023-03-10",
      diasAtraso: 320
    }
  ];

  const handleCalculateCorrection = async () => {
    setIsCalculating(true);
    setCalculationProgress(0);

    // Simulate calculation progress
    const interval = setInterval(() => {
      setCalculationProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsCalculating(false);
          setCalculatedData(mockCorrectionData);
          toast({
            title: "Correção Calculada",
            description: "Os valores foram corrigidos com sucesso!",
          });
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const handleNextModule = () => {
    // Save correction data to localStorage
    localStorage.setItem('correctionData', JSON.stringify(calculatedData));
    navigate('/analise');
  };

  const totalOriginal = calculatedData.reduce((sum, item) => sum + item.valorOriginal, 0);
  const totalCorrigido = calculatedData.reduce((sum, item) => sum + item.valorCorrigido, 0);
  const totalJuros = totalCorrigido - totalOriginal;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-lg">
          <Calculator className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Módulo 1: Correção</h1>
          <p className="text-slate-600">Aplicação de correção monetária e cálculo de juros</p>
        </div>
      </div>

      <Tabs defaultValue="configuracao" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="configuracao">Configuração</TabsTrigger>
          <TabsTrigger value="calculo">Cálculo</TabsTrigger>
          <TabsTrigger value="resultados">Resultados</TabsTrigger>
        </TabsList>

        <TabsContent value="configuracao" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-emerald-600" />
                  Método de Correção
                </CardTitle>
                <CardDescription>
                  Índice de correção alimentado por API
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <Label className="text-sm font-medium">Índice de Correção</Label>
                  <select 
                    className="w-full p-2 border rounded-md bg-slate-50"
                    value={correctionMethod}
                    onChange={(e) => setCorrectionMethod(e.target.value)}
                    disabled
                  >
                    <option value="ipca">IPCA (Automático via API)</option>
                    <option value="igpm">IGP-M (Automático via API)</option>
                    <option value="selic">SELIC (Automático via API)</option>
                    <option value="cdi">CDI (Automático via API)</option>
                  </select>
                </div>
                
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Os índices são atualizados automaticamente via API do Banco Central. Não é necessária intervenção manual.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-emerald-600" />
                  Parâmetros de Juros
                  {isNonStandard && (
                    <Badge variant="destructive" className="ml-2">
                      Não Padrão
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  Configuração dos juros de mora e multa
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm">Juros de Mora (%)</Label>
                    <Input 
                      type="number" 
                      value={jurosMora} 
                      onChange={(e) => {
                        const value = parseFloat(e.target.value) || 0;
                        if (value !== 1.0) {
                          setTempJuros(value);
                          setShowResponsibilityDialog(true);
                        } else {
                          setJurosMora(value);
                          setIsNonStandard(false);
                        }
                      }}
                      step="0.01" 
                      className={isNonStandard ? "border-orange-500" : ""}
                    />
                  </div>
                  <div>
                    <Label className="text-sm">Multa (%)</Label>
                    <Input 
                      type="number" 
                      value={multa} 
                      onChange={(e) => {
                        const value = parseFloat(e.target.value) || 0;
                        if (value !== 2.0) {
                          setTempMulta(value);
                          setShowResponsibilityDialog(true);
                        } else {
                          setMulta(value);
                          setIsNonStandard(false);
                        }
                      }}
                      step="0.01" 
                      className={isNonStandard ? "border-orange-500" : ""}
                    />
                  </div>
                </div>
                
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Valores padrão: 1% juros de mora e 2% multa. Alterações devem ser aprovadas.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </div>

          <Dialog open={showResponsibilityDialog} onOpenChange={setShowResponsibilityDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  Alteração de Parâmetros Padrão
                </DialogTitle>
                <DialogDescription>
                  Você está alterando os valores padrão de juros e multa. Esta alteração pode impactar significativamente os cálculos.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Valores Padrão:</strong> 1% juros de mora e 2% multa<br/>
                    <strong>Novos Valores:</strong> {tempJuros}% juros de mora e {tempMulta}% multa
                  </AlertDescription>
                </Alert>
                <p className="text-sm text-slate-600">
                  Ao confirmar, você assume total responsabilidade pelos cálculos realizados com estes parâmetros personalizados.
                </p>
              </div>
              <DialogFooter>
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowResponsibilityDialog(false);
                    setTempJuros(1.0);
                    setTempMulta(2.0);
                  }}
                >
                  Cancelar
                </Button>
                <Button 
                  onClick={() => {
                    setJurosMora(tempJuros);
                    setMulta(tempMulta);
                    setIsNonStandard(tempJuros !== 1.0 || tempMulta !== 2.0);
                    setShowResponsibilityDialog(false);
                    toast({
                      title: "Parâmetros Alterados",
                      description: "Os novos valores foram aplicados com sucesso.",
                      variant: "default"
                    });
                  }}
                  className="bg-orange-600 hover:bg-orange-700"
                >
                  Confirmar Alteração
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>

        <TabsContent value="calculo" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Processamento da Correção</CardTitle>
              <CardDescription>
                Aplique a correção monetária aos valores em aberto
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {!isCalculating && calculatedData.length === 0 && (
                <div className="text-center py-8">
                  <Calculator className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                  <p className="text-slate-600 mb-4">Pronto para calcular a correção dos valores</p>
                  <Button onClick={handleCalculateCorrection} className="bg-emerald-600 hover:bg-emerald-700">
                    Iniciar Cálculo de Correção
                  </Button>
                </div>
              )}

              {isCalculating && (
                <div className="space-y-4">
                  <div className="text-center">
                    <div className="inline-flex items-center gap-2 mb-4">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-600"></div>
                      <span className="text-emerald-600 font-medium">Calculando correção...</span>
                    </div>
                  </div>
                  <Progress value={calculationProgress} className="w-full" />
                  <p className="text-center text-sm text-slate-600">
                    {calculationProgress}% - Aplicando índices de correção
                  </p>
                </div>
              )}

              {calculatedData.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-emerald-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="font-medium">Correção calculada com sucesso!</span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-sm text-slate-600">Valor Original</p>
                          <p className="text-2xl font-bold text-slate-800">
                            R$ {totalOriginal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-sm text-slate-600">Valor Corrigido</p>
                          <p className="text-2xl font-bold text-emerald-600">
                            R$ {totalCorrigido.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-sm text-slate-600">Total de Juros</p>
                          <p className="text-2xl font-bold text-orange-600">
                            R$ {totalJuros.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resultados" className="space-y-6">
          {calculatedData.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Detalhamento da Correção</CardTitle>
                    <CardDescription>
                      Clique em um registro para ver detalhes interativos
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
                            <TableHead>Juros</TableHead>
                            <TableHead>% Correção</TableHead>
                            <TableHead>Vencimento</TableHead>
                            <TableHead>Dias Atraso</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {calculatedData.map((item) => (
                            <TableRow 
                              key={item.id} 
                              className={`cursor-pointer hover:bg-slate-50 transition-colors ${
                                selectedRecord?.id === item.id ? 'bg-emerald-50 border-l-4 border-emerald-500' : ''
                              }`}
                              onClick={() => setSelectedRecord(item)}
                            >
                              <TableCell>{item.id}</TableCell>
                              <TableCell>
                                R$ {item.valorOriginal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                              </TableCell>
                              <TableCell className="font-medium text-emerald-600">
                                R$ {item.valorCorrigido.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                              </TableCell>
                              <TableCell className="text-orange-600">
                                R$ {item.juros.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline">{item.percentualCorrecao}%</Badge>
                              </TableCell>
                              <TableCell>{item.dataVencimento}</TableCell>
                              <TableCell>{item.diasAtraso} dias</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="lg:col-span-1">
                {selectedRecord ? (
                  <Card className="sticky top-6">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Calculator className="h-5 w-5 text-emerald-600" />
                        Detalhes do Registro #{selectedRecord.id}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-3">
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-sm font-medium text-slate-600">Valor Original</p>
                          <p className="text-lg font-bold text-slate-800">
                            R$ {selectedRecord.valorOriginal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </p>
                        </div>

                        <div className="p-3 bg-emerald-50 rounded-lg">
                          <p className="text-sm font-medium text-emerald-700">Valor Corrigido</p>
                          <p className="text-lg font-bold text-emerald-600">
                            R$ {selectedRecord.valorCorrigido.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </p>
                        </div>

                        <div className="p-3 bg-orange-50 rounded-lg">
                          <p className="text-sm font-medium text-orange-700">Juros Aplicados</p>
                          <p className="text-lg font-bold text-orange-600">
                            R$ {selectedRecord.juros.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </p>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div className="p-3 bg-blue-50 rounded-lg">
                            <p className="text-sm font-medium text-blue-700">% Correção</p>
                            <p className="text-lg font-bold text-blue-600">{selectedRecord.percentualCorrecao}%</p>
                          </div>
                          <div className="p-3 bg-purple-50 rounded-lg">
                            <p className="text-sm font-medium text-purple-700">Dias Atraso</p>
                            <p className="text-lg font-bold text-purple-600">{selectedRecord.diasAtraso}</p>
                          </div>
                        </div>

                        <div className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-sm font-medium text-slate-600">Vencimento</p>
                          <p className="text-md font-semibold text-slate-800">{selectedRecord.dataVencimento}</p>
                        </div>
                      </div>

                      <div className="pt-4 border-t">
                        <h4 className="font-medium text-sm text-slate-600 mb-2">Parâmetros Aplicados</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span>Índice:</span>
                            <span className="font-medium">{correctionMethod.toUpperCase()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Juros Mora:</span>
                            <span className="font-medium">{jurosMora}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Multa:</span>
                            <span className="font-medium">{multa}%</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ) : (
                  <Card className="h-64">
                    <CardContent className="p-8 text-center flex items-center justify-center h-full">
                      <div>
                        <Calculator className="h-8 w-8 text-slate-400 mx-auto mb-3" />
                        <p className="text-slate-600 text-sm">Selecione um registro para ver os detalhes</p>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Calculator className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-600">Execute o cálculo de correção para ver os resultados</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {calculatedData.length > 0 && (
        <div className="flex justify-between items-center pt-6 border-t">
          <Button variant="outline" onClick={() => navigate('/')}>
            Voltar ao Aging
          </Button>
          <Button onClick={handleNextModule} className="bg-emerald-600 hover:bg-emerald-700">
            Continuar para Análise
          </Button>
        </div>
      )}
    </div>
  );
}