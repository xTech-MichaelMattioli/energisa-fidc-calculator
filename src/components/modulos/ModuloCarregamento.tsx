
import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Database, 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  Info,
  BarChart3,
  ArrowRight,
  Play
} from "lucide-react";

interface BaseInfo {
  nome: string;
  arquivo?: File;
  status: 'pendente' | 'carregando' | 'sucesso' | 'erro';
  registros?: number;
  tamanho?: string;
  ultimaModificacao?: string;
  colunas?: string[];
  preview?: any[];
}

const basesDisponiveis = [
  'ESS_Principal',
  'Voltz_Principal', 
  'ESS_Secundaria',
  'Voltz_Secundaria',
  'Base_Complementar_1',
  'Base_Complementar_2',
  'Base_Auxiliar_1',
  'Base_Auxiliar_2',
  'Base_Historica'
];

export function ModuloCarregamento() {
  const [baseSelecionada, setBaseSelecionada] = useState('');
  const [bases, setBases] = useState<Record<string, BaseInfo>>({});
  const [progresso, setProgresso] = useState(0);
  const [carregamentoAtivo, setCarregamentoAtivo] = useState(false);
  const [baseAtual, setBaseAtual] = useState('');

  const handleFileUpload = (nomeBase: string, arquivo: File) => {
    setBases(prev => ({
      ...prev,
      [nomeBase]: {
        nome: nomeBase,
        arquivo,
        status: 'pendente',
        tamanho: `${(arquivo.size / 1024 / 1024).toFixed(2)} MB`,
        ultimaModificacao: new Date(arquivo.lastModified).toLocaleDateString('pt-BR')
      }
    }));
  };

  const iniciarCarregamento = async (nomeBase: string) => {
    if (!bases[nomeBase]?.arquivo) return;

    setCarregamentoAtivo(true);
    setBaseAtual(nomeBase);
    setProgresso(0);

    setBases(prev => ({
      ...prev,
      [nomeBase]: { ...prev[nomeBase], status: 'carregando' }
    }));

    // Simulação de carregamento
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 200));
      setProgresso(i);
    }

    // Simulação de dados processados
    const registrosSimulados = Math.floor(Math.random() * 50000) + 10000;
    const colunasSimuladas = ['ID', 'Cliente', 'Valor', 'Vencimento', 'Status', 'Data_Base'];
    
    setBases(prev => ({
      ...prev,
      [nomeBase]: {
        ...prev[nomeBase],
        status: 'sucesso',
        registros: registrosSimulados,
        colunas: colunasSimuladas,
        preview: [
          { ID: '001', Cliente: 'Cliente A', Valor: 'R$ 1.234,56', Vencimento: '2025-01-15', Status: 'Ativo' },
          { ID: '002', Cliente: 'Cliente B', Valor: 'R$ 2.987,43', Vencimento: '2025-02-20', Status: 'Pendente' },
          { ID: '003', Cliente: 'Cliente C', Valor: 'R$ 567,89', Vencimento: '2025-03-10', Status: 'Ativo' }
        ]
      }
    }));

    setCarregamentoAtivo(false);
    setProgresso(0);
  };

  const basesCarregadas = Object.values(bases).filter(base => base.status === 'sucesso');
  const podePassarProximoModulo = basesCarregadas.length > 0;

  const passarProximoModulo = () => {
    // Salvar dados no contexto ou localStorage para próximo módulo
    const dadosCarregamento = {
      basesCarregadas: basesCarregadas.map(base => ({
        nome: base.nome,
        registros: base.registros,
        colunas: base.colunas
      })),
      dataCarregamento: new Date().toISOString()
    };
    
    localStorage.setItem('dadosCarregamento', JSON.stringify(dadosCarregamento));
    
    // Navegar para próximo módulo
    window.location.href = '/mapeamento';
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header do Módulo */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-slate-800 flex items-center justify-center gap-3">
          <Database className="h-8 w-8 text-cyan-600" />
          Módulo 3: Carregamento de Bases
        </h1>
        <p className="text-lg text-slate-600">
          Análise e carregamento das bases de dados (até 9 bases diferentes)
        </p>
      </div>

      {/* Seleção de Base */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Seleção e Upload de Bases
          </CardTitle>
          <CardDescription>
            Selecione uma das 9 bases disponíveis e faça o upload do arquivo
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="base-select">Selecionar Base</Label>
              <Select value={baseSelecionada} onValueChange={setBaseSelecionada}>
                <SelectTrigger id="base-select">
                  <SelectValue placeholder="Escolha uma base..." />
                </SelectTrigger>
                <SelectContent>
                  {basesDisponiveis.map(base => (
                    <SelectItem key={base} value={base}>
                      {base.replace('_', ' ')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="file-upload">Arquivo da Base</Label>
              <Input
                id="file-upload"
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => {
                  const arquivo = e.target.files?.[0];
                  if (arquivo && baseSelecionada) {
                    handleFileUpload(baseSelecionada, arquivo);
                  }
                }}
                disabled={!baseSelecionada}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Status das Bases */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Status do Carregamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(bases).map(([nome, info]) => (
              <div key={nome} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{nome.replace('_', ' ')}</h3>
                  <Badge variant={
                    info.status === 'sucesso' ? 'default' :
                    info.status === 'carregando' ? 'secondary' :
                    info.status === 'erro' ? 'destructive' : 'outline'
                  }>
                    {info.status === 'sucesso' && <CheckCircle className="h-3 w-3 mr-1" />}
                    {info.status === 'erro' && <AlertTriangle className="h-3 w-3 mr-1" />}
                    {info.status}
                  </Badge>
                </div>
                
                {info.tamanho && (
                  <p className="text-sm text-slate-600">
                    Tamanho: {info.tamanho}
                  </p>
                )}
                
                {info.registros && (
                  <p className="text-sm text-slate-600">
                    Registros: {info.registros.toLocaleString('pt-BR')}
                  </p>
                )}
                
                <Button
                  size="sm"
                  onClick={() => iniciarCarregamento(nome)}
                  disabled={!info.arquivo || info.status === 'sucesso' || carregamentoAtivo}
                  className="w-full"
                >
                  <Play className="h-3 w-3 mr-1" />
                  {info.status === 'sucesso' ? 'Carregado' : 'Carregar'}
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Progresso do Carregamento */}
      {carregamentoAtivo && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-600 animate-spin" />
                <span className="font-medium">Carregando {baseAtual}...</span>
              </div>
              <Progress value={progresso} className="w-full" />
              <p className="text-sm text-blue-600">
                Progresso: {progresso}% - Processando dados...
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preview dos Dados */}
      {basesCarregadas.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Preview dos Dados Carregados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue={basesCarregadas[0]?.nome} className="w-full">
              <TabsList className="grid w-full grid-cols-2 lg:grid-cols-3">
                {basesCarregadas.slice(0, 6).map(base => (
                  <TabsTrigger key={base.nome} value={base.nome}>
                    {base.nome.replace('_', ' ')}
                  </TabsTrigger>
                ))}
              </TabsList>
              
              {basesCarregadas.map(base => (
                <TabsContent key={base.nome} value={base.nome} className="space-y-4">
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
                      <span className="text-slate-600">Status:</span>
                      <div className="font-bold text-green-600">Sucesso</div>
                    </div>
                    <div className="bg-slate-50 p-3 rounded">
                      <span className="text-slate-600">Tamanho:</span>
                      <div className="font-bold">{bases[base.nome]?.tamanho}</div>
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
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Resumo e Passagem para Próximo Módulo */}
      <Card className={podePassarProximoModulo ? "border-green-200 bg-green-50" : "border-slate-200"}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold flex items-center gap-2">
                <Info className="h-5 w-5" />
                Resumo do Carregamento
              </h3>
              <p className="text-sm text-slate-600">
                {basesCarregadas.length} base(s) carregada(s) com sucesso
              </p>
              {basesCarregadas.length > 0 && (
                <div className="text-sm text-slate-600">
                  Total de registros: {basesCarregadas.reduce((acc, base) => acc + (base.registros || 0), 0).toLocaleString('pt-BR')}
                </div>
              )}
            </div>
            
            <Button
              onClick={passarProximoModulo}
              disabled={!podePassarProximoModulo}
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
