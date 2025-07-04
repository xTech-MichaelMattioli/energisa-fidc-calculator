import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Calculator, TrendingUp, AlertCircle, CheckCircle, DollarSign, Calendar } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "@/hooks/use-toast";

export function ModuloCorrecao() {
  const navigate = useNavigate();
  const [isCalculating, setIsCalculating] = useState(false);
  const [calculationProgress, setCalculationProgress] = useState(0);
  const [calculatedData, setCalculatedData] = useState<any[]>([]);
  const [correctionMethod, setCorrectionMethod] = useState("ipca");

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
          <h1 className="text-2xl font-bold text-slate-800">Módulo 6: Correção</h1>
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
                  Selecione o índice para correção monetária
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <Label className="text-sm font-medium">Índice de Correção</Label>
                  <select 
                    className="w-full p-2 border rounded-md"
                    value={correctionMethod}
                    onChange={(e) => setCorrectionMethod(e.target.value)}
                  >
                    <option value="ipca">IPCA</option>
                    <option value="igpm">IGP-M</option>
                    <option value="selic">SELIC</option>
                    <option value="cdi">CDI</option>
                  </select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm">Taxa Mensal (%)</Label>
                    <Input type="number" placeholder="0.5" step="0.01" />
                  </div>
                  <div>
                    <Label className="text-sm">Taxa Anual (%)</Label>
                    <Input type="number" placeholder="6.5" step="0.01" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-emerald-600" />
                  Parâmetros de Juros
                </CardTitle>
                <CardDescription>
                  Configuração dos juros de mora
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm">Juros de Mora (%)</Label>
                    <Input type="number" placeholder="1.0" step="0.01" />
                  </div>
                  <div>
                    <Label className="text-sm">Multa (%)</Label>
                    <Input type="number" placeholder="2.0" step="0.01" />
                  </div>
                </div>
                
                <div>
                  <Label className="text-sm">Data de Referência</Label>
                  <Input type="date" />
                </div>
              </CardContent>
            </Card>
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Os parâmetros de correção serão aplicados a todos os registros com base no aging calculado no módulo anterior.
            </AlertDescription>
          </Alert>
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
            <Card>
              <CardHeader>
                <CardTitle>Detalhamento da Correção</CardTitle>
                <CardDescription>
                  Valores corrigidos por registro
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
                        <TableRow key={item.id}>
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
          <Button variant="outline" onClick={() => navigate('/aging')}>
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