import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  BarChart3, 
  ArrowRight, 
  CheckCircle, 
  AlertTriangle,
  Target,
  Info,
  Settings,
  FileText
} from "lucide-react";

interface CampoMapeamento {
  original: string;
  mapeado: string;
  tipo: 'obrigatorio' | 'opcional' | 'ignorado';
  status: 'mapeado' | 'pendente' | 'conflito';
}

interface BaseMapeamento {
  nome: string;
  registros: number;
  colunas: string[];
  campos: CampoMapeamento[];
  statusMapeamento: 'pendente' | 'mapeando' | 'concluido';
  progressoMapeamento: number;
}

const camposPadrao = [
  { nome: 'ID_CONTRATO', descricao: 'Identificador único do contrato', obrigatorio: true },
  { nome: 'NOME_CLIENTE', descricao: 'Nome completo do cliente', obrigatorio: true },
  { nome: 'CPF_CNPJ', descricao: 'CPF ou CNPJ do cliente', obrigatorio: true },
  { nome: 'VALOR_ORIGINAL', descricao: 'Valor original da operação', obrigatorio: true },
  { nome: 'DATA_VENCIMENTO', descricao: 'Data de vencimento', obrigatorio: true },
  { nome: 'DATA_OPERACAO', descricao: 'Data da operação/contrato', obrigatorio: false },
  { nome: 'STATUS', descricao: 'Status do contrato', obrigatorio: false },
  { nome: 'PRODUTO', descricao: 'Tipo de produto financeiro', obrigatorio: false },
  { nome: 'AGENCIA', descricao: 'Código da agência', obrigatorio: false },
  { nome: 'CONTA', descricao: 'Número da conta', obrigatorio: false }
];

export function ModuloMapeamento() {
  const [basesMapeamento, setBasesMapeamento] = useState<BaseMapeamento[]>([]);
  const [mapeamentoAtivo, setMapeamentoAtivo] = useState(false);
  const [baseAtual, setBaseAtual] = useState('');

  useEffect(() => {
    // Carregar dados do módulo anterior
    const dadosCarregamento = localStorage.getItem('dadosCarregamento');
    if (dadosCarregamento) {
      const dados = JSON.parse(dadosCarregamento);
      const bases: BaseMapeamento[] = dados.arquivos.map((arquivo: any) => ({
        nome: arquivo.nome,
        registros: arquivo.registros,
        colunas: arquivo.colunas,
        campos: arquivo.colunas.map((coluna: string) => {
          // Auto-mapeamento inteligente
          const campoCorrespondente = camposPadrao.find(campo => 
            coluna.toLowerCase().includes(campo.nome.toLowerCase().replace('_', '')) ||
            campo.nome.toLowerCase().includes(coluna.toLowerCase())
          );
          
          return {
            original: coluna,
            mapeado: campoCorrespondente ? campoCorrespondente.nome : '',
            tipo: campoCorrespondente ? (campoCorrespondente.obrigatorio ? 'obrigatorio' : 'opcional') : 'ignorado',
            status: campoCorrespondente ? 'mapeado' : 'pendente'
          };
        }),
        statusMapeamento: 'pendente',
        progressoMapeamento: 0
      }));
      
      setBasesMapeamento(bases);
    }
  }, []);

  const atualizarMapeamento = (nomeBase: string, campoOriginal: string, novoMapeamento: string) => {
    const valorMapeamento = novoMapeamento === 'none' ? '' : novoMapeamento;
    setBasesMapeamento(prev => prev.map(base => 
      base.nome === nomeBase 
        ? {
            ...base,
            campos: base.campos.map(campo => 
              campo.original === campoOriginal
                ? {
                    ...campo,
                    mapeado: valorMapeamento,
                    tipo: valorMapeamento ? (camposPadrao.find(c => c.nome === valorMapeamento)?.obrigatorio ? 'obrigatorio' : 'opcional') : 'ignorado',
                    status: valorMapeamento ? 'mapeado' : 'pendente'
                  }
                : campo
            )
          }
        : base
    ));
  };

  const validarMapeamento = async (nomeBase: string) => {
    setMapeamentoAtivo(true);
    setBaseAtual(nomeBase);
    
    const base = basesMapeamento.find(b => b.nome === nomeBase);
    if (!base) return;

    // Atualizar status para mapeando
    setBasesMapeamento(prev => prev.map(b => 
      b.nome === nomeBase 
        ? { ...b, statusMapeamento: 'mapeando', progressoMapeamento: 0 }
        : b
    ));

    // Simular validação
    for (let i = 0; i <= 100; i += 20) {
      await new Promise(resolve => setTimeout(resolve, 300));
      
      setBasesMapeamento(prev => prev.map(b => 
        b.nome === nomeBase 
          ? { ...b, progressoMapeamento: i }
          : b
      ));
    }

    // Verificar campos obrigatórios
    const camposObrigatorios = camposPadrao.filter(c => c.obrigatorio);
    const camposMapeados = base.campos.filter(c => c.mapeado && c.status === 'mapeado');
    
    const todosObrigatoriosMapeados = camposObrigatorios.every(obrigatorio => 
      camposMapeados.some(mapeado => mapeado.mapeado === obrigatorio.nome)
    );

    // Finalizar validação
    setBasesMapeamento(prev => prev.map(b => 
      b.nome === nomeBase 
        ? { 
            ...b, 
            statusMapeamento: 'concluido',
            progressoMapeamento: 100,
            campos: b.campos.map(campo => ({
              ...campo,
              status: todosObrigatoriosMapeados ? campo.status : 
                      (campo.tipo === 'obrigatorio' && !campo.mapeado ? 'conflito' : campo.status)
            }))
          }
        : b
    ));

    setMapeamentoAtivo(false);
  };

  const validarTodasBases = async () => {
    for (const base of basesMapeamento) {
      if (base.statusMapeamento !== 'concluido') {
        await validarMapeamento(base.nome);
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  };

  const todasBasesValidadas = basesMapeamento.every(b => b.statusMapeamento === 'concluido');
  const mapeamentoCompleto = basesMapeamento.every(base => 
    camposPadrao.filter(c => c.obrigatorio).every(obrigatorio => 
      base.campos.some(campo => campo.mapeado === obrigatorio.nome && campo.status === 'mapeado')
    )
  );

  const passarProximoModulo = () => {
    const dadosMapeamento = {
      basesMapeadas: basesMapeamento.map(base => ({
        nome: base.nome,
        registros: base.registros,
        mapeamento: base.campos.reduce((acc, campo) => {
          if (campo.mapeado) {
            acc[campo.mapeado] = campo.original;
          }
          return acc;
        }, {} as Record<string, string>)
      })),
      dataProcessamento: new Date().toISOString()
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
          Módulo 2: Mapeamento de Campos
        </h1>
        <p className="text-lg text-slate-600">
          Mapeamento dos campos das bases para o modelo padrão do sistema
        </p>
      </div>

      {/* Botão de Validação Geral */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Controles de Mapeamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            onClick={validarTodasBases}
            disabled={mapeamentoAtivo}
            className="bg-gradient-to-r from-cyan-500 to-blue-500"
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            Validar Todas as Bases
          </Button>
        </CardContent>
      </Card>

      {/* Progresso do Mapeamento */}
      {mapeamentoAtivo && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-600 animate-pulse" />
                <span className="font-medium">Validando mapeamento da base {baseAtual}...</span>
              </div>
              <p className="text-sm text-blue-600">
                Verificando campos obrigatórios e consistência dos dados...
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mapeamento por Base */}
      {basesMapeamento.length > 0 && (
        <Tabs defaultValue={basesMapeamento[0]?.nome} className="w-full">
          <TabsList className="grid w-full grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {basesMapeamento.slice(0, 3).map((base) => (
              <TabsTrigger key={base.nome} value={base.nome} className="text-xs">
                <div className="flex items-center gap-2">
                  <span>{base.nome.replace(/\.[^/.]+$/, "")}</span>
                  {base.statusMapeamento === 'concluido' && <CheckCircle className="h-3 w-3 text-green-600" />}
                  {base.statusMapeamento === 'mapeando' && <div className="h-3 w-3 bg-blue-600 rounded-full animate-pulse" />}
                </div>
              </TabsTrigger>
            ))}
          </TabsList>
          
          {basesMapeamento.map((base) => (
            <TabsContent key={base.nome} value={base.nome} className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      {base.nome}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={
                        base.statusMapeamento === 'concluido' ? 'default' :
                        base.statusMapeamento === 'mapeando' ? 'secondary' : 'outline'
                      }>
                        {base.statusMapeamento === 'concluido' && <CheckCircle className="h-3 w-3 mr-1" />}
                        {base.statusMapeamento}
                      </Badge>
                      <Button
                        size="sm"
                        onClick={() => validarMapeamento(base.nome)}
                        disabled={mapeamentoAtivo}
                      >
                        Validar
                      </Button>
                    </div>
                  </CardTitle>
                  <CardDescription>
                    {base.registros.toLocaleString('pt-BR')} registros • {base.colunas.length} colunas
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {base.statusMapeamento === 'mapeando' && (
                    <div className="mb-6">
                      <div className="flex justify-between text-sm mb-2">
                        <span>Validando mapeamento...</span>
                        <span>{base.progressoMapeamento}%</span>
                      </div>
                      <Progress value={base.progressoMapeamento} className="h-2" />
                    </div>
                  )}
                  
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <h4 className="font-medium mb-2 text-green-700">Campos Obrigatórios</h4>
                        <div className="space-y-2">
                          {camposPadrao.filter(c => c.obrigatorio).map((campo) => {
                            const mapeado = base.campos.find(c => c.mapeado === campo.nome);
                            return (
                              <div key={campo.nome} className={`p-2 rounded border ${
                                mapeado ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                              }`}>
                                <div className="flex items-center gap-2">
                                  {mapeado ? <CheckCircle className="h-4 w-4 text-green-600" /> : <AlertTriangle className="h-4 w-4 text-red-600" />}
                                  <span className="font-medium">{campo.nome}</span>
                                </div>
                                <div className="text-xs text-slate-600">{campo.descricao}</div>
                                {mapeado && <div className="text-xs text-green-600">Mapeado de: {mapeado.original}</div>}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium mb-2 text-blue-700">Campos Opcionais</h4>
                        <div className="space-y-2">
                          {camposPadrao.filter(c => !c.obrigatorio).map((campo) => {
                            const mapeado = base.campos.find(c => c.mapeado === campo.nome);
                            return (
                              <div key={campo.nome} className={`p-2 rounded border ${
                                mapeado ? 'bg-blue-50 border-blue-200' : 'bg-slate-50 border-slate-200'
                              }`}>
                                <div className="flex items-center gap-2">
                                  {mapeado ? <CheckCircle className="h-4 w-4 text-blue-600" /> : <div className="h-4 w-4 rounded-full border-2 border-slate-300" />}
                                  <span className="font-medium">{campo.nome}</span>
                                </div>
                                <div className="text-xs text-slate-600">{campo.descricao}</div>
                                {mapeado && <div className="text-xs text-blue-600">Mapeado de: {mapeado.original}</div>}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                    
                    <div className="border-t pt-4">
                      <h4 className="font-medium mb-3">Mapeamento Detalhado</h4>
                      <div className="space-y-2">
                        {base.campos.map((campo) => (
                          <div key={campo.original} className="flex items-center gap-4 p-2 border rounded">
                            <div className="flex-1">
                              <span className="font-medium">{campo.original}</span>
                            </div>
                            <div className="flex-1">
                              <Select
                                value={campo.mapeado || 'none'}
                                onValueChange={(valor) => atualizarMapeamento(base.nome, campo.original, valor)}
                              >
                                <SelectTrigger className="h-8">
                                  <SelectValue placeholder="Selecione o campo" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="none">Não mapear</SelectItem>
                                  {camposPadrao.map((campoPadrao) => (
                                    <SelectItem key={campoPadrao.nome} value={campoPadrao.nome}>
                                      {campoPadrao.nome} {campoPadrao.obrigatorio && '*'}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="w-24">
                              <Badge variant={
                                campo.status === 'mapeado' ? 'default' :
                                campo.status === 'conflito' ? 'destructive' : 'outline'
                              } className="text-xs">
                                {campo.tipo}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      )}

      {/* Resumo e Próximo Módulo */}
      <Card className={mapeamentoCompleto ? "border-green-200 bg-green-50" : "border-slate-200"}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold flex items-center gap-2">
                <Info className="h-5 w-5" />
                Resumo do Mapeamento
              </h3>
              <p className="text-sm text-slate-600">
                {basesMapeamento.filter(b => b.statusMapeamento === 'concluido').length} de {basesMapeamento.length} base(s) validada(s)
              </p>
              {!mapeamentoCompleto && todasBasesValidadas && (
                <p className="text-sm text-amber-600">
                  ⚠️ Alguns campos obrigatórios não foram mapeados
                </p>
              )}
            </div>
            
            <Button
              onClick={passarProximoModulo}
              disabled={!mapeamentoCompleto}
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