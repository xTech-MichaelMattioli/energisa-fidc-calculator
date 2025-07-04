import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { 
  Calculator, 
  ArrowRight, 
  CheckCircle, 
  AlertTriangle,
  Calendar,
  Target,
  BarChart3,
  Info,
  Play,
  Clock
} from "lucide-react";

interface FaixaAging {
  nome: string;
  diasInicio: number;
  diasFim: number;
  cor: string;
  quantidade: number;
  valorTotal: number;
  percentual: number;
}

interface BaseAging {
  nome: string;
  registros: number;
  dataBase: string;
  faixasAging: FaixaAging[];
  statusProcessamento: 'pendente' | 'processando' | 'concluido';
  progressoProcessamento: number;
  totalGeral: number;
  mediaIdade: number;
}

const faixasPadrao: Omit<FaixaAging, 'quantidade' | 'valorTotal' | 'percentual'>[] = [
  { nome: 'A Vencer', diasInicio: -999, diasFim: 0, cor: 'bg-green-500' },
  { nome: '1-30 dias', diasInicio: 1, diasFim: 30, cor: 'bg-yellow-500' },
  { nome: '31-60 dias', diasInicio: 31, diasFim: 60, cor: 'bg-orange-500' },
  { nome: '61-90 dias', diasInicio: 61, diasFim: 90, cor: 'bg-red-500' },
  { nome: '91-180 dias', diasInicio: 91, diasFim: 180, cor: 'bg-red-600' },
  { nome: '181-360 dias', diasInicio: 181, diasFim: 360, cor: 'bg-red-700' },
  { nome: 'Acima de 360 dias', diasInicio: 361, diasFim: 9999, cor: 'bg-red-900' }
];

export function ModuloAging() {
  const [basesProcessamento, setBasesProcessamento] = useState<BaseAging[]>([]);
  const [dataReferencia, setDataReferencia] = useState(new Date().toISOString().split('T')[0]);
  const [tipoCalculo, setTipoCalculo] = useState('vencimento');
  const [processamentoAtivo, setProcessamentoAtivo] = useState(false);
  const [baseAtual, setBaseAtual] = useState('');

  useEffect(() => {
    // Carregar dados do módulo anterior
    const dadosMapeamento = localStorage.getItem('dadosMapeamento');
    if (dadosMapeamento) {
      const dados = JSON.parse(dadosMapeamento);
      const basesAging: BaseAging[] = dados.basesMapeadas.map((base: any) => ({
        nome: base.nome,
        registros: Math.floor(Math.random() * 50000) + 10000,
        dataBase: dataReferencia,
        faixasAging: faixasPadrao.map(faixa => ({
          ...faixa,
          quantidade: 0,
          valorTotal: 0,
          percentual: 0
        })),
        statusProcessamento: 'pendente' as const,
        progressoProcessamento: 0,
        totalGeral: 0,
        mediaIdade: 0
      }));
      setBasesProcessamento(basesAging);
    }
  }, [dataReferencia]);

  const processarAging = async (baseNome: string) => {
    setProcessamentoAtivo(true);
    setBaseAtual(baseNome);
    
    const base = basesProcessamento.find(b => b.nome === baseNome);
    if (!base) return;

    // Atualizar status para processando
    setBasesProcessamento(prev => prev.map(b => 
      b.nome === baseNome 
        ? { ...b, statusProcessamento: 'processando', progressoProcessamento: 0 }
        : b
    ));

    // Simulação do processamento
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 300));
      
      setBasesProcessamento(prev => prev.map(b => 
        b.nome === baseNome 
          ? { ...b, progressoProcessamento: i }
          : b
      ));
    }

    // Simular resultados do aging
    const totalRegistros = base.registros;
    const valorMedio = 1500 + Math.random() * 3000;
    let totalGeral = 0;
    let somaIdades = 0;
    
    const faixasCalculadas = faixasPadrao.map((faixa, index) => {
      // Distribuição simulada baseada em padrões reais de aging
      let percentualFaixa;
      switch(index) {
        case 0: percentualFaixa = 0.35; break; // A Vencer
        case 1: percentualFaixa = 0.25; break; // 1-30
        case 2: percentualFaixa = 0.20; break; // 31-60
        case 3: percentualFaixa = 0.10; break; // 61-90
        case 4: percentualFaixa = 0.06; break; // 91-180
        case 5: percentualFaixa = 0.03; break; // 181-360
        case 6: percentualFaixa = 0.01; break; // 360+
        default: percentualFaixa = 0;
      }
      
      const quantidade = Math.floor(totalRegistros * percentualFaixa);
      const valorTotal = quantidade * (valorMedio + Math.random() * 500 - 250);
      totalGeral += valorTotal;
      
      const mediaFaixa = (faixa.diasInicio + faixa.diasFim) / 2;
      somaIdades += quantidade * Math.max(0, mediaFaixa);
      
      return {
        ...faixa,
        quantidade,
        valorTotal,
        percentual: Math.round(percentualFaixa * 100)
      };
    });

    const mediaIdade = Math.round(somaIdades / totalRegistros);

    // Finalizar processamento
    setBasesProcessamento(prev => prev.map(b => 
      b.nome === baseNome 
        ? { 
            ...b, 
            statusProcessamento: 'concluido',
            progressoProcessamento: 100,
            faixasAging: faixasCalculadas,
            totalGeral,
            mediaIdade
          }
        : b
    ));

    setProcessamentoAtivo(false);
  };

  const processarTodasBases = async () => {
    for (const base of basesProcessamento) {
      if (base.statusProcessamento !== 'concluido') {
        await processarAging(base.nome);
        await new Promise(resolve => setTimeout(resolve, 500)); // Pausa entre bases
      }
    }
  };

  const todasBasesProcessadas = basesProcessamento.every(b => b.statusProcessamento === 'concluido');

  const passarProximoModulo = () => {
    const dadosAging = {
      basesProcessadas: basesProcessamento.map(base => ({
        nome: base.nome,
        faixasAging: base.faixasAging,
        totalGeral: base.totalGeral,
        mediaIdade: base.mediaIdade,
        dataReferencia: dataReferencia
      })),
      dataProcessamento: new Date().toISOString()
    };
    
    localStorage.setItem('dadosAging', JSON.stringify(dadosAging));
    window.location.href = '/correcao';
  };

  const formatarMoeda = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor);
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header do Módulo */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-slate-800 flex items-center justify-center gap-3">
          <Calculator className="h-8 w-8 text-cyan-600" />
          Módulo 1: Cálculo de Aging
        </h1>
        <p className="text-lg text-slate-600">
          Análise de aging por faixas de vencimento das bases mapeadas
        </p>
      </div>

      {/* Configurações do Aging */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Configurações de Aging
          </CardTitle>
          <CardDescription>
            Configure os parâmetros para o cálculo do aging
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="data-referencia">Data de Referência</Label>
              <Input
                id="data-referencia"
                type="date"
                value={dataReferencia}
                onChange={(e) => setDataReferencia(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="tipo-calculo">Tipo de Cálculo</Label>
              <Select value={tipoCalculo} onValueChange={setTipoCalculo}>
                <SelectTrigger id="tipo-calculo">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="vencimento">Por Data de Vencimento</SelectItem>
                  <SelectItem value="contrato">Por Data do Contrato</SelectItem>
                  <SelectItem value="operacao">Por Data da Operação</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-end">
              <Button
                onClick={processarTodasBases}
                disabled={processamentoAtivo}
                className="w-full bg-gradient-to-r from-cyan-500 to-blue-500"
              >
                <Play className="h-4 w-4 mr-2" />
                Processar Todas as Bases
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Status das Bases */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Status do Processamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {basesProcessamento.map((base) => (
              <div key={base.nome} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{base.nome.replace('_', ' ')}</h3>
                  <Badge variant={
                    base.statusProcessamento === 'concluido' ? 'default' :
                    base.statusProcessamento === 'processando' ? 'secondary' : 'outline'
                  }>
                    {base.statusProcessamento === 'concluido' && <CheckCircle className="h-3 w-3 mr-1" />}
                    {base.statusProcessamento === 'processando' && <Clock className="h-3 w-3 mr-1" />}
                    {base.statusProcessamento}
                  </Badge>
                </div>
                
                <div className="space-y-2">
                  <p className="text-sm text-slate-600">
                    Registros: {base.registros.toLocaleString('pt-BR')}
                  </p>
                  {base.statusProcessamento === 'processando' && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>Progresso:</span>
                        <span>{base.progressoProcessamento}%</span>
                      </div>
                      <Progress value={base.progressoProcessamento} className="h-2" />
                    </div>
                  )}
                  {base.statusProcessamento === 'concluido' && (
                    <>
                      <p className="text-sm text-slate-600">
                        Valor Total: {formatarMoeda(base.totalGeral)}
                      </p>
                      <p className="text-sm text-slate-600">
                        Idade Média: {base.mediaIdade} dias
                      </p>
                    </>
                  )}
                </div>
                
                <Button
                  size="sm"
                  onClick={() => processarAging(base.nome)}
                  disabled={processamentoAtivo || base.statusProcessamento === 'concluido'}
                  className="w-full"
                >
                  <Calculator className="h-3 w-3 mr-1" />
                  {base.statusProcessamento === 'concluido' ? 'Processado' : 'Processar Aging'}
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Progresso do Processamento Atual */}
      {processamentoAtivo && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Calculator className="h-5 w-5 text-blue-600 animate-spin" />
                <span className="font-medium">Processando aging da base {baseAtual}...</span>
              </div>
              <p className="text-sm text-blue-600">
                Calculando faixas de vencimento e distribuição de valores...
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Resultados do Aging */}
      {basesProcessamento.some(b => b.statusProcessamento === 'concluido') && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Resultados do Aging
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue={basesProcessamento.find(b => b.statusProcessamento === 'concluido')?.nome} className="w-full">
              <TabsList className="grid w-full grid-cols-2 lg:grid-cols-3">
                {basesProcessamento.filter(b => b.statusProcessamento === 'concluido').slice(0, 6).map(base => (
                  <TabsTrigger key={base.nome} value={base.nome}>
                    {base.nome.replace('_', ' ')}
                  </TabsTrigger>
                ))}
              </TabsList>
              
              {basesProcessamento.filter(b => b.statusProcessamento === 'concluido').map(base => (
                <TabsContent key={base.nome} value={base.nome} className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="bg-slate-50 p-3 rounded">
                      <span className="text-slate-600">Total Geral:</span>
                      <div className="font-bold">{formatarMoeda(base.totalGeral)}</div>
                    </div>
                    <div className="bg-slate-50 p-3 rounded">
                      <span className="text-slate-600">Registros:</span>
                      <div className="font-bold">{base.registros.toLocaleString('pt-BR')}</div>
                    </div>
                    <div className="bg-slate-50 p-3 rounded">
                      <span className="text-slate-600">Idade Média:</span>
                      <div className="font-bold">{base.mediaIdade} dias</div>
                    </div>
                    <div className="bg-slate-50 p-3 rounded">
                      <span className="text-slate-600">Data Base:</span>
                      <div className="font-bold">{new Date(base.dataBase).toLocaleDateString('pt-BR')}</div>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    {base.faixasAging.map((faixa, index) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className={`w-4 h-4 rounded ${faixa.cor}`}></div>
                          <div>
                            <div className="font-medium">{faixa.nome}</div>
                            <div className="text-sm text-slate-600">
                              {faixa.quantidade.toLocaleString('pt-BR')} registros ({faixa.percentual}%)
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">{formatarMoeda(faixa.valorTotal)}</div>
                          <div className="text-sm text-slate-600">
                            {Math.round((faixa.valorTotal / base.totalGeral) * 100)}% do total
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Resumo e Passagem para Próximo Módulo */}
      <Card className={todasBasesProcessadas ? "border-green-200 bg-green-50" : "border-slate-200"}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold flex items-center gap-2">
                <Info className="h-5 w-5" />
                Resumo do Aging
              </h3>
              <p className="text-sm text-slate-600">
                {basesProcessamento.filter(b => b.statusProcessamento === 'concluido').length} de {basesProcessamento.length} base(s) processada(s)
              </p>
              {todasBasesProcessadas && (
                <div className="text-sm text-slate-600">
                  Valor total processado: {formatarMoeda(basesProcessamento.reduce((acc, base) => acc + base.totalGeral, 0))}
                </div>
              )}
            </div>
            
            <Button
              onClick={passarProximoModulo}
              disabled={!todasBasesProcessadas}
              size="lg"
              className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
            >
              Prosseguir para Correção
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}