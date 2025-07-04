import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { 
  BarChart3, 
  ArrowRight, 
  CheckCircle, 
  AlertTriangle,
  Link,
  Target,
  Database,
  Info,
  Play
} from "lucide-react";

interface CampoMapeamento {
  campoOrigem: string;
  campoDestino: string;
  tipo: string;
  status: 'mapeado' | 'pendente' | 'conflito';
  sugestao?: string;
}

interface BaseMapeamento {
  nome: string;
  registros: number;
  colunas: string[];
  mapeamentos: CampoMapeamento[];
  statusMapeamento: 'pendente' | 'em_progresso' | 'concluido';
  percentualMapeado: number;
}

const camposObrigatorios = [
  'ID_Cliente',
  'Nome_Cliente', 
  'Valor_Original',
  'Data_Vencimento',
  'Data_Base',
  'Status_Contrato',
  'Tipo_Operacao'
];

const tiposCampo = [
  'Texto',
  'Numero', 
  'Data',
  'Moeda',
  'Boolean',
  'Categoria'
];

export function ModuloMapeamento() {
  const [basesCarregadas, setBasesCarregadas] = useState<BaseMapeamento[]>([]);
  const [baseAtiva, setBaseAtiva] = useState<string>('');
  const [mapeamentoAtivo, setMapeamentoAtivo] = useState(false);
  const [progresso, setProgresso] = useState(0);

  useEffect(() => {
    // Carregar dados do módulo anterior
    const dadosCarregamento = localStorage.getItem('dadosCarregamento');
    if (dadosCarregamento) {
      const dados = JSON.parse(dadosCarregamento);
      const basesMapeamento: BaseMapeamento[] = dados.basesCarregadas.map((base: any) => ({
        nome: base.nome,
        registros: base.registros,
        colunas: base.colunas,
        mapeamentos: base.colunas.map((coluna: string) => ({
          campoOrigem: coluna,
          campoDestino: '',
          tipo: 'Texto',
          status: 'pendente' as const
        })),
        statusMapeamento: 'pendente' as const,
        percentualMapeado: 0
      }));
      setBasesCarregadas(basesMapeamento);
      if (basesMapeamento.length > 0) {
        setBaseAtiva(basesMapeamento[0].nome);
      }
    }
  }, []);

  const atualizarMapeamento = (baseNome: string, indiceCampo: number, campoDestino: string, tipo: string) => {
    setBasesCarregadas(prev => prev.map(base => {
      if (base.nome === baseNome) {
        const novosMapeamentos = [...base.mapeamentos];
        novosMapeamentos[indiceCampo] = {
          ...novosMapeamentos[indiceCampo],
          campoDestino,
          tipo,
          status: campoDestino ? 'mapeado' : 'pendente'
        };
        
        const percentualMapeado = Math.round(
          (novosMapeamentos.filter(m => m.status === 'mapeado').length / novosMapeamentos.length) * 100
        );
        
        return {
          ...base,
          mapeamentos: novosMapeamentos,
          percentualMapeado,
          statusMapeamento: percentualMapeado === 100 ? 'concluido' : percentualMapeado > 0 ? 'em_progresso' : 'pendente'
        };
      }
      return base;
    }));
  };

  const executarMapeamentoAutomatico = async (baseNome: string) => {
    setMapeamentoAtivo(true);
    setProgresso(0);
    
    const base = basesCarregadas.find(b => b.nome === baseNome);
    if (!base) return;

    // Simulação de mapeamento automático
    for (let i = 0; i <= 100; i += 20) {
      await new Promise(resolve => setTimeout(resolve, 300));
      setProgresso(i);
    }

    // Aplicar sugestões automáticas
    setBasesCarregadas(prev => prev.map(b => {
      if (b.nome === baseNome) {
        const mapeamentosAtualizados = b.mapeamentos.map(campo => {
          // Lógica de sugestão automática baseada no nome do campo
          let sugestao = '';
          const nomeMinusculo = campo.campoOrigem.toLowerCase();
          
          if (nomeMinusculo.includes('id') || nomeMinusculo.includes('codigo')) {
            sugestao = 'ID_Cliente';
          } else if (nomeMinusculo.includes('nome') || nomeMinusculo.includes('cliente')) {
            sugestao = 'Nome_Cliente';
          } else if (nomeMinusculo.includes('valor') || nomeMinusculo.includes('amount')) {
            sugestao = 'Valor_Original';
          } else if (nomeMinusculo.includes('vencimento') || nomeMinusculo.includes('due')) {
            sugestao = 'Data_Vencimento';
          } else if (nomeMinusculo.includes('base') || nomeMinusculo.includes('ref')) {
            sugestao = 'Data_Base';
          }

          return {
            ...campo,
            campoDestino: sugestao,
            sugestao: sugestao,
            status: sugestao ? 'mapeado' as const : 'pendente' as const
          };
        });

        const percentualMapeado = Math.round(
          (mapeamentosAtualizados.filter(m => m.status === 'mapeado').length / mapeamentosAtualizados.length) * 100
        );

        return {
          ...b,
          mapeamentos: mapeamentosAtualizados,
          percentualMapeado,
          statusMapeamento: percentualMapeado === 100 ? 'concluido' : 'em_progresso'
        };
      }
      return b;
    }));

    setMapeamentoAtivo(false);
    setProgresso(0);
  };

  const baseAtual = basesCarregadas.find(b => b.nome === baseAtiva);
  const todasBasesCompletas = basesCarregadas.every(b => b.statusMapeamento === 'concluido');

  const passarProximoModulo = () => {
    const dadosMapeamento = {
      basesMapeadas: basesCarregadas.map(base => ({
        nome: base.nome,
        mapeamentos: base.mapeamentos.filter(m => m.status === 'mapeado'),
        percentualMapeado: base.percentualMapeado
      })),
      dataMapeamento: new Date().toISOString()
    };
    
    localStorage.setItem('dadosMapeamento', JSON.stringify(dadosMapeamento));
    window.location.href = '/aging';
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header do Módulo */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-slate-800 flex items-center justify-center gap-3">
          <BarChart3 className="h-8 w-8 text-cyan-600" />
          Módulo 4: Mapeamento de Campos
        </h1>
        <p className="text-lg text-slate-600">
          Mapeamento automático e manual dos campos das bases carregadas
        </p>
      </div>

      {/* Status das Bases */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Bases Disponíveis para Mapeamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {basesCarregadas.map((base) => (
              <div key={base.nome} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{base.nome.replace('_', ' ')}</h3>
                  <Badge variant={
                    base.statusMapeamento === 'concluido' ? 'default' :
                    base.statusMapeamento === 'em_progresso' ? 'secondary' : 'outline'
                  }>
                    {base.statusMapeamento === 'concluido' && <CheckCircle className="h-3 w-3 mr-1" />}
                    {base.statusMapeamento}
                  </Badge>
                </div>
                
                <div className="space-y-2">
                  <p className="text-sm text-slate-600">
                    Registros: {base.registros.toLocaleString('pt-BR')}
                  </p>
                  <p className="text-sm text-slate-600">
                    Campos: {base.colunas.length}
                  </p>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>Mapeado:</span>
                      <span>{base.percentualMapeado}%</span>
                    </div>
                    <Progress value={base.percentualMapeado} className="h-2" />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Button
                    size="sm"
                    onClick={() => executarMapeamentoAutomatico(base.nome)}
                    disabled={mapeamentoAtivo || base.statusMapeamento === 'concluido'}
                    className="w-full"
                  >
                    <Target className="h-3 w-3 mr-1" />
                    Mapear Automaticamente
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setBaseAtiva(base.nome)}
                    className="w-full"
                  >
                    Configurar Manualmente
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Progresso do Mapeamento */}
      {mapeamentoAtivo && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Target className="h-5 w-5 text-blue-600 animate-spin" />
                <span className="font-medium">Executando mapeamento automático...</span>
              </div>
              <Progress value={progresso} className="w-full" />
              <p className="text-sm text-blue-600">
                Progresso: {progresso}% - Analisando campos e sugerindo mapeamentos...
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuração de Mapeamento */}
      {baseAtual && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link className="h-5 w-5" />
              Configuração de Mapeamento - {baseAtual.nome.replace('_', ' ')}
            </CardTitle>
            <CardDescription>
              Configure o mapeamento dos campos para os campos padrão do sistema
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm font-medium text-slate-600 border-b pb-2">
                <div>Campo Original</div>
                <div>Campo Destino</div>
                <div>Tipo</div>
                <div>Status</div>
              </div>
              
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {baseAtual.mapeamentos.map((mapeamento, index) => (
                  <div key={index} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center p-3 border rounded-lg">
                    <div className="font-medium">{mapeamento.campoOrigem}</div>
                    
                    <Select
                      value={mapeamento.campoDestino}
                      onValueChange={(valor) => atualizarMapeamento(baseAtual.nome, index, valor, mapeamento.tipo)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecionar campo..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">-- Não mapear --</SelectItem>
                        {camposObrigatorios.map(campo => (
                          <SelectItem key={campo} value={campo}>
                            {campo.replace('_', ' ')}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    <Select
                      value={mapeamento.tipo}
                      onValueChange={(tipo) => atualizarMapeamento(baseAtual.nome, index, mapeamento.campoDestino, tipo)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {tiposCampo.map(tipo => (
                          <SelectItem key={tipo} value={tipo}>
                            {tipo}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    <Badge variant={
                      mapeamento.status === 'mapeado' ? 'default' :
                      mapeamento.status === 'conflito' ? 'destructive' : 'outline'
                    }>
                      {mapeamento.status === 'mapeado' && <CheckCircle className="h-3 w-3 mr-1" />}
                      {mapeamento.status === 'conflito' && <AlertTriangle className="h-3 w-3 mr-1" />}
                      {mapeamento.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Resumo e Passagem para Próximo Módulo */}
      <Card className={todasBasesCompletas ? "border-green-200 bg-green-50" : "border-slate-200"}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold flex items-center gap-2">
                <Info className="h-5 w-5" />
                Resumo do Mapeamento
              </h3>
              <p className="text-sm text-slate-600">
                {basesCarregadas.filter(b => b.statusMapeamento === 'concluido').length} de {basesCarregadas.length} base(s) completamente mapeada(s)
              </p>
              <div className="text-sm text-slate-600">
                Média de mapeamento: {Math.round(basesCarregadas.reduce((acc, base) => acc + base.percentualMapeado, 0) / basesCarregadas.length || 0)}%
              </div>
            </div>
            
            <Button
              onClick={passarProximoModulo}
              disabled={!todasBasesCompletas}
              size="lg"
              className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
            >
              Prosseguir para Aging
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}