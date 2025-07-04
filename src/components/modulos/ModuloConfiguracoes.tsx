
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, Clock, Target, Calendar } from "lucide-react";

const bibliotecas = [
  { nome: "pandas", versao: "2.1.0", descricao: "Manipulação de dados", icone: "🐼" },
  { nome: "numpy", versao: "1.24.0", descricao: "Computação numérica", icone: "🔢" },
  { nome: "datetime", versao: "built-in", descricao: "Manipulação de datas", icone: "📅" },
  { nome: "warnings", versao: "built-in", descricao: "Controle de avisos", icone: "⚠️" },
  { nome: "re", versao: "built-in", descricao: "Expressões regulares", icone: "🔍" },
  { nome: "typing", versao: "built-in", descricao: "Tipagem estática", icone: "📝" },
];

const configuracoes = [
  { nome: "display.max_columns", valor: "None", descricao: "Exibir todas as colunas" },
  { nome: "display.max_rows", valor: "20", descricao: "Máximo 20 linhas" },
  { nome: "display.float_format", valor: "'{:.2f}'.format", descricao: "2 casas decimais" },
];

export function ModuloConfiguracoes() {
  const [etapaAtual, setEtapaAtual] = useState(0);
  const [bibliotecasCarregadas, setBibliotecasCarregadas] = useState<string[]>([]);
  const [configurado, setConfigurado] = useState(false);
  const [dataExecucao, setDataExecucao] = useState("");

  useEffect(() => {
    if (etapaAtual > 0) {
      const timer = setTimeout(() => {
        if (bibliotecasCarregadas.length < bibliotecas.length) {
          setBibliotecasCarregadas(prev => [...prev, bibliotecas[prev.length].nome]);
        }
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [etapaAtual, bibliotecasCarregadas]);

  const iniciarCarregamento = () => {
    setEtapaAtual(1);
    setDataExecucao(new Date().toLocaleString('pt-BR'));
    setBibliotecasCarregadas([]);
    
    setTimeout(() => {
      setConfigurado(true);
    }, bibliotecas.length * 500 + 1000);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Cabeçalho do Módulo */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-slate-800 mb-2">
          CÁLCULO DE VALOR CORRIGIDO - BASES ESS E VOLTZ
        </h1>
        <h2 className="text-xl text-slate-600 mb-4">
          Notebook Fase 1: Da Base Original até Valor Corrigido
        </h2>
        <div className="flex justify-center gap-4 text-sm text-slate-500">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            <span>Objetivo: Calcular valor corrigido das bases ESS e Voltz</span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            <span>Escopo: Correção monetária, multa e juros</span>
          </div>
        </div>
        {dataExecucao && (
          <div className="mt-4 text-sm text-slate-600">
            📅 Data de execução: {dataExecucao}
          </div>
        )}
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card className="border-2 border-dashed border-cyan-200">
          <CardContent className="p-6 text-center">
            <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <h3 className="font-semibold text-green-700">Bibliotecas</h3>
            <p className="text-sm text-slate-600">
              {bibliotecasCarregadas.length}/{bibliotecas.length} carregadas
            </p>
          </CardContent>
        </Card>
        
        <Card className="border-2 border-dashed border-blue-200">
          <CardContent className="p-6 text-center">
            <Clock className="h-8 w-8 text-blue-500 mx-auto mb-2" />
            <h3 className="font-semibold text-blue-700">Status</h3>
            <p className="text-sm text-slate-600">
              {configurado ? "Configurado" : "Aguardando"}
            </p>
          </CardContent>
        </Card>
        
        <Card className="border-2 border-dashed border-purple-200">
          <CardContent className="p-6 text-center">
            <Target className="h-8 w-8 text-purple-500 mx-auto mb-2" />
            <h3 className="font-semibold text-purple-700">Ambiente</h3>
            <p className="text-sm text-slate-600">Produção</p>
          </CardContent>
        </Card>
      </div>

      {/* Carregamento de Bibliotecas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">📚</span>
            Carregamento de Bibliotecas
          </CardTitle>
          <CardDescription>
            Importação e configuração das dependências necessárias
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {bibliotecas.map((lib, index) => (
              <div
                key={lib.nome}
                className={`p-4 rounded-lg border-2 transition-all duration-500 ${
                  bibliotecasCarregadas.includes(lib.nome)
                    ? "border-green-200 bg-green-50"
                    : "border-slate-200 bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{lib.icone}</span>
                    <span className="font-mono font-semibold">{lib.nome}</span>
                  </div>
                  {bibliotecasCarregadas.includes(lib.nome) && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                </div>
                <p className="text-sm text-slate-600 mb-1">{lib.descricao}</p>
                <Badge variant="outline" className="text-xs">
                  v{lib.versao}
                </Badge>
              </div>
            ))}
          </div>
          
          {!configurado && (
            <div className="text-center">
              <Button 
                onClick={iniciarCarregamento}
                className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white px-8 py-2"
                disabled={etapaAtual > 0}
              >
                {etapaAtual === 0 ? "Executar Configurações" : "Carregando..."}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configurações do Pandas */}
      {etapaAtual > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">⚙️</span>
              Configurações do Pandas
            </CardTitle>
            <CardDescription>
              Definição dos parâmetros de exibição de dados
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {configuracoes.map((config, index) => (
                <div
                  key={config.nome}
                  className="flex items-center justify-between p-4 bg-slate-50 rounded-lg"
                >
                  <div>
                    <code className="font-mono text-sm bg-slate-200 px-2 py-1 rounded">
                      pd.set_option('{config.nome}', {config.valor})
                    </code>
                    <p className="text-sm text-slate-600 mt-1">{config.descricao}</p>
                  </div>
                  {bibliotecasCarregadas.includes("pandas") && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mensagens de Status */}
      {configurado && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-6">
            <div className="space-y-2 text-center">
              <div className="text-green-700 font-semibold text-lg">
                ✅ Bibliotecas carregadas com sucesso!
              </div>
              <div className="text-green-600">
                📅 Data de execução: {dataExecucao}
              </div>
              <div className="text-green-600">
                🎯 Objetivo: Calcular valor corrigido das bases ESS e Voltz
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Console de Logs */}
      {etapaAtual > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">💻</span>
              Console de Execução
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-green-400 h-48 overflow-y-auto">
              <div>Python 3.11.0 | FIDC Calculator Environment</div>
              <div className="text-slate-500">Copyright (c) 2025 Energisa Data Refactor Wizard</div>
              <div className="mt-2">
                {bibliotecasCarregadas.map((lib, index) => (
                  <div key={lib} className="text-cyan-400">
                    {`>>> import ${lib} ✓`}
                  </div>
                ))}
              </div>
              {configurado && (
                <div className="mt-2 text-yellow-400">
                  {`>>> Configurações aplicadas com sucesso!`}
                  <br />
                  {`>>> Sistema pronto para processamento das bases ESS e Voltz`}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
