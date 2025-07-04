import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  Database, 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  Info,
  BarChart3,
  ArrowRight,
  Target,
  Link
} from "lucide-react";

interface CampoMapeamento {
  campoOrigem: string;
  campoDestino: string;
  tipo: string;
  status: 'mapeado' | 'pendente' | 'conflito';
  sugestao?: string;
}

interface BaseInfo {
  nome: string;
  arquivo?: File;
  status: 'pendente' | 'carregando' | 'mapeando' | 'concluido' | 'erro';
  registros?: number;
  tamanho?: string;
  ultimaModificacao?: string;
  colunas?: string[];
  preview?: any[];
  mapeamentos?: CampoMapeamento[];
  percentualMapeado?: number;
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

export function ModuloCarregamento() {
  const [bases, setBases] = useState<BaseInfo[]>([]);
  const [progresso, setProgresso] = useState(0);
  const [etapaAtual, setEtapaAtual] = useState<'upload' | 'carregamento' | 'mapeamento'>('upload');
  const [baseAtual, setBaseAtual] = useState('');

  const handleFileUpload = (arquivos: FileList | null) => {
    if (!arquivos) return;
    
    const novasBases: BaseInfo[] = Array.from(arquivos).map((arquivo, index) => ({
      nome: `Base_${index + 1}`,
      arquivo,
      status: 'pendente',
      tamanho: `${(arquivo.size / 1024 / 1024).toFixed(2)} MB`,
      ultimaModificacao: new Date(arquivo.lastModified).toLocaleDateString('pt-BR')
    }));
    
    setBases(novasBases);
  };

  const iniciarProcessamento = async () => {
    if (bases.length === 0) return;

    // Fase 1: Carregamento
    setEtapaAtual('carregamento');
    
    for (let i = 0; i < bases.length; i++) {
      const base = bases[i];
      setBaseAtual(base.nome);
      setProgresso(0);

      // Atualizar status para carregando
      setBases(prev => prev.map((b, idx) => 
        idx === i ? { ...b, status: 'carregando' } : b
      ));

      // Simulação de carregamento
      for (let p = 0; p <= 100; p += 20) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setProgresso(p);
      }

      // Processar dados simulados
      const registrosSimulados = Math.floor(Math.random() * 50000) + 10000;
      const colunasSimuladas = ['ID', 'Cliente', 'Valor', 'Vencimento', 'Status', 'Data_Base'];
      
      setBases(prev => prev.map((b, idx) => 
        idx === i ? {
          ...b,
          status: 'pendente',
          registros: registrosSimulados,
          colunas: colunasSimuladas,
          preview: [
            { ID: '001', Cliente: 'Cliente A', Valor: 'R$ 1.234,56', Vencimento: '2025-01-15', Status: 'Ativo' },
            { ID: '002', Cliente: 'Cliente B', Valor: 'R$ 2.987,43', Vencimento: '2025-02-20', Status: 'Pendente' },
            { ID: '003', Cliente: 'Cliente C', Valor: 'R$ 567,89', Vencimento: '2025-03-10', Status: 'Ativo' }
          ]
        } : b
      ));
    }

    // Fase 2: Mapeamento
    setEtapaAtual('mapeamento');
    
    for (let i = 0; i < bases.length; i++) {
      const base = bases[i];
      setBaseAtual(base.nome);
      setProgresso(0);

      // Atualizar status para mapeando
      setBases(prev => prev.map((b, idx) => 
        idx === i ? { ...b, status: 'mapeando' } : b
      ));

      // Simulação de mapeamento automático
      for (let p = 0; p <= 100; p += 25) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setProgresso(p);
      }

      // Aplicar mapeamentos automáticos
      const mapeamentosAutomaticos = base.colunas?.map(coluna => {
        let sugestao = '';
        const nomeMinusculo = coluna.toLowerCase();
        
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
          campoOrigem: coluna,
          campoDestino: sugestao,
          tipo: 'Texto',
          status: sugestao ? 'mapeado' as const : 'pendente' as const,
          sugestao
        };
      }) || [];

      const percentualMapeado = Math.round(
        (mapeamentosAutomaticos.filter(m => m.status === 'mapeado').length / mapeamentosAutomaticos.length) * 100
      );

      setBases(prev => prev.map((b, idx) => 
        idx === i ? {
          ...b,
          status: 'concluido',
          mapeamentos: mapeamentosAutomaticos,
          percentualMapeado
        } : b
      ));
    }

    setEtapaAtual('upload');
    setProgresso(0);
  };

  const atualizarMapeamento = (baseIndex: number, campoIndex: number, campoDestino: string, tipo: string) => {
    setBases(prev => prev.map((base, bIdx) => {
      if (bIdx === baseIndex && base.mapeamentos) {
        const novosMapeamentos = [...base.mapeamentos];
        novosMapeamentos[campoIndex] = {
          ...novosMapeamentos[campoIndex],
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
          percentualMapeado
        };
      }
      return base;
    }));
  };

  const basesProcessadas = bases.filter(base => base.status === 'concluido');
  const todasBasesCompletas = bases.length > 0 && bases.every(base => base.status === 'concluido');

  const passarProximoModulo = () => {
    const dadosMapeamento = {
      basesMapeadas: basesProcessadas.map(base => ({
        nome: base.nome,
        mapeamentos: base.mapeamentos?.filter(m => m.status === 'mapeado') || [],
        percentualMapeado: base.percentualMapeado,
        registros: base.registros
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
          <Database className="h-8 w-8 text-cyan-600" />
          Módulo 2: Carregamento e Mapeamento
        </h1>
        <p className="text-lg text-slate-600">
          Upload, análise e mapeamento automático de bases de dados
        </p>
      </div>

      {/* Upload de Bases */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload de Bases
          </CardTitle>
          <CardDescription>
            Selecione uma ou mais bases de dados para processamento automático
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="file-upload">Arquivos das Bases</Label>
            <Input
              id="file-upload"
              type="file"
              accept=".csv,.xlsx,.xls"
              multiple
              onChange={(e) => handleFileUpload(e.target.files)}
            />
          </div>
          
          {bases.length > 0 && (
            <Button
              onClick={iniciarProcessamento}
              disabled={etapaAtual !== 'upload'}
              className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600"
            >
              <Target className="h-4 w-4 mr-2" />
              Iniciar Processamento Automático
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Progresso do Processamento */}
      {etapaAtual !== 'upload' && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                {etapaAtual === 'carregamento' && (
                  <>
                    <Database className="h-5 w-5 text-blue-600 animate-spin" />
                    <span className="font-medium">Carregando {baseAtual}...</span>
                  </>
                )}
                {etapaAtual === 'mapeamento' && (
                  <>
                    <Target className="h-5 w-5 text-blue-600 animate-spin" />
                    <span className="font-medium">Mapeando campos de {baseAtual}...</span>
                  </>
                )}
              </div>
              <Progress value={progresso} className="w-full" />
              <p className="text-sm text-blue-600">
                Progresso: {progresso}% - {etapaAtual === 'carregamento' ? 'Processando dados...' : 'Analisando campos e sugerindo mapeamentos...'}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status das Bases */}
      {bases.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Status do Processamento
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {bases.map((base, index) => (
                <div key={index} className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{base.nome}</h3>
                    <Badge variant={
                      base.status === 'concluido' ? 'default' :
                      base.status === 'carregando' || base.status === 'mapeando' ? 'secondary' :
                      base.status === 'erro' ? 'destructive' : 'outline'
                    }>
                      {base.status === 'concluido' && <CheckCircle className="h-3 w-3 mr-1" />}
                      {base.status === 'erro' && <AlertTriangle className="h-3 w-3 mr-1" />}
                      {base.status === 'concluido' ? 'Processado' : base.status}
                    </Badge>
                  </div>
                  
                  {base.tamanho && (
                    <p className="text-sm text-slate-600">
                      Tamanho: {base.tamanho}
                    </p>
                  )}
                  
                  {base.registros && (
                    <p className="text-sm text-slate-600">
                      Registros: {base.registros.toLocaleString('pt-BR')}
                    </p>
                  )}

                  {base.percentualMapeado !== undefined && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>Mapeado:</span>
                        <span>{base.percentualMapeado}%</span>
                      </div>
                      <Progress value={base.percentualMapeado} className="h-2" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuração de Mapeamento */}
      {basesProcessadas.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link className="h-5 w-5" />
              Ajuste de Mapeamentos
            </CardTitle>
            <CardDescription>
              Revise e ajuste os mapeamentos automáticos conforme necessário
            </CardDescription>
          </CardHeader>
          <CardContent>
            {basesProcessadas.map((base, baseIndex) => (
              <div key={baseIndex} className="space-y-4 mb-6">
                <h3 className="font-medium text-lg">{base.nome}</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm font-medium text-slate-600 border-b pb-2">
                  <div>Campo Original</div>
                  <div>Campo Destino</div>
                  <div>Tipo</div>
                  <div>Status</div>
                </div>
                
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {base.mapeamentos?.map((mapeamento, campoIndex) => (
                    <div key={campoIndex} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center p-3 border rounded-lg">
                      <div className="font-medium">{mapeamento.campoOrigem}</div>
                      
                      <Select
                        value={mapeamento.campoDestino}
                        onValueChange={(valor) => atualizarMapeamento(baseIndex, campoIndex, valor, mapeamento.tipo)}
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
                        onValueChange={(tipo) => atualizarMapeamento(baseIndex, campoIndex, mapeamento.campoDestino, tipo)}
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
                  )) || []}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Preview dos Dados */}
      {basesProcessadas.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Preview dos Dados Processados
            </CardTitle>
          </CardHeader>
          <CardContent>
            {basesProcessadas.map((base, index) => (
              <div key={index} className="space-y-4 mb-6">
                <h3 className="font-medium text-lg">{base.nome}</h3>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="bg-slate-50 p-3 rounded">
                    <span className="text-slate-600">Registros:</span>
                    <div className="font-bold">{base.registros?.toLocaleString('pt-BR')}</div>
                  </div>
                  <div className="bg-slate-50 p-3 rounded">
                    <span className="text-slate-600">Colunas:</span>
                    <div className="font-bold">{base.colunas?.length}</div>
                  </div>
                  <div className="bg-slate-50 p-3 rounded">
                    <span className="text-slate-600">Mapeado:</span>
                    <div className="font-bold text-green-600">{base.percentualMapeado}%</div>
                  </div>
                  <div className="bg-slate-50 p-3 rounded">
                    <span className="text-slate-600">Tamanho:</span>
                    <div className="font-bold">{base.tamanho}</div>
                  </div>
                </div>
                
                {base.preview && (
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse border border-slate-300">
                      <thead>
                        <tr className="bg-slate-100">
                          {Object.keys(base.preview[0]).map(coluna => (
                            <th key={coluna} className="border border-slate-300 p-2 text-left">
                              {coluna}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {base.preview.map((linha, idx) => (
                          <tr key={idx} className="even:bg-slate-50">
                            {Object.values(linha).map((valor, cidx) => (
                              <td key={cidx} className="border border-slate-300 p-2">
                                {valor as string}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
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
                Resumo do Processamento
              </h3>
              <p className="text-sm text-slate-600">
                {basesProcessadas.length} de {bases.length} base(s) processada(s)
              </p>
              {basesProcessadas.length > 0 && (
                <div className="text-sm text-slate-600">
                  Média de mapeamento: {Math.round(basesProcessadas.reduce((acc, base) => acc + (base.percentualMapeado || 0), 0) / basesProcessadas.length)}%
                </div>
              )}
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