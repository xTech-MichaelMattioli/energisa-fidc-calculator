
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Calendar, TrendingUp, BarChart3, Settings, Target } from "lucide-react";

// Dicionário de índices IGPM replicando exatamente o notebook
const indicesIGPM = {
  "2020.01": 520.45, "2020.02": 521.78, "2020.03": 523.12, "2020.04": 524.47,
  "2020.05": 525.83, "2020.06": 527.19, "2020.07": 528.56, "2020.08": 529.94,
  "2020.09": 531.33, "2020.10": 532.72, "2020.11": 534.12, "2020.12": 535.53,
  "2021.01": 536.95, "2021.02": 538.37, "2021.03": 539.80, "2021.04": 541.24,
  "2021.05": 542.69, "2021.06": 544.14, "2021.07": 545.60, "2021.08": 547.07,
  "2021.09": 548.55, "2021.10": 550.03, "2021.11": 551.52, "2021.12": 553.02,
  "2022.01": 554.53, "2022.02": 556.04, "2022.03": 557.56, "2022.04": 559.09,
  "2022.05": 560.63, "2022.06": 562.17, "2022.07": 563.72, "2022.08": 565.28,
  "2022.09": 566.85, "2022.10": 568.42, "2022.11": 570.00, "2022.12": 571.59,
  "2023.01": 573.19, "2023.02": 574.79, "2023.03": 576.40, "2023.04": 578.02,
  "2023.05": 579.65, "2023.06": 581.28, "2023.07": 582.92, "2023.08": 584.57,
  "2023.09": 586.23, "2023.10": 587.89, "2023.11": 589.56, "2023.12": 591.24,
  "2024.01": 592.93, "2024.02": 594.62, "2024.03": 596.32, "2024.04": 598.03,
  "2024.05": 599.75, "2024.06": 601.47, "2024.07": 603.20, "2024.08": 604.94,
  "2024.09": 606.69, "2024.10": 608.44, "2024.11": 610.20, "2024.12": 611.97,
  "2025.01": 613.75, "2025.02": 615.53, "2025.03": 617.32, "2025.04": 624.40
};

export function ModuloParametros() {
  const [taxaMulta, setTaxaMulta] = useState(2.0);
  const [taxaJuros, setTaxaJuros] = useState(1.0);
  const [parametrosExibidos, setParametrosExibidos] = useState(false);
  const [buscaData, setBuscaData] = useState("");
  const [resultadoBusca, setResultadoBusca] = useState<number | null>(null);

  const buscarIndiceIGPM = (periodo: string) => {
    return indicesIGPM[periodo as keyof typeof indicesIGPM] || 624.40;
  };

  const handleBuscaIndice = () => {
    if (buscaData) {
      const indice = buscarIndiceIGPM(buscaData);
      setResultadoBusca(indice);
    }
  };

  const exibirParametros = () => {
    setParametrosExibidos(true);
  };

  // Dados para o gráfico de linha IGPM
  const dadosGrafico = Object.entries(indicesIGPM).map(([periodo, valor]) => ({
    periodo,
    valor,
    ano: periodo.split('.')[0]
  }));

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Cabeçalho do Módulo */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-slate-800 mb-2">
          ⚙️ MÓDULO 2: PARÂMETROS DE CORREÇÃO
        </h1>
        <div className="border-b border-slate-300 w-full mb-4">
          <div className="text-center text-slate-400 text-sm">
            {"=".repeat(50)}
          </div>
        </div>
        <div className="flex justify-center gap-4 text-sm text-slate-500">
          <div className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            <span>Configuração dos parâmetros financeiros e metodológicos</span>
          </div>
        </div>
      </div>

      {/* Cards de Parâmetros Financeiros */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Taxa de Multa */}
        <Card className="border-2 border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-700">
              <span className="text-2xl">⚖️</span>
              Taxa de Multa
            </CardTitle>
            <CardDescription>
              Aplicada sobre o valor líquido para registros em atraso
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center mb-4">
              <div className="relative w-32 h-32">
                <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="3"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#dc2626"
                    strokeWidth="3"
                    strokeDasharray={`${taxaMulta * 5}, 100`}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold text-red-700">{taxaMulta.toFixed(1)}%</span>
                </div>
              </div>
            </div>
            <Slider 
              value={[taxaMulta]} 
              onValueChange={(value) => setTaxaMulta(value[0])}
              max={5}
              min={0}
              step={0.1}
              className="w-full"
            />
            <p className="text-sm text-slate-600 mt-2">
              Valor configurado: {taxaMulta.toFixed(1)}% (self.taxa_multa = {(taxaMulta/100).toFixed(3)})
            </p>
          </CardContent>
        </Card>

        {/* Taxa de Juros */}
        <Card className="border-2 border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-700">
              <span className="text-2xl">📈</span>
              Taxa de Juros Mensal
            </CardTitle>
            <CardDescription>
              Juros moratórios aplicados proporcionalmente ao tempo de atraso
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center mb-4">
              <div className="relative w-32 h-32">
                <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="3"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#2563eb"
                    strokeWidth="3"
                    strokeDasharray={`${taxaJuros * 10}, 100`}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold text-blue-700">{taxaJuros.toFixed(1)}%</span>
                </div>
              </div>
            </div>
            <Slider 
              value={[taxaJuros]} 
              onValueChange={(value) => setTaxaJuros(value[0])}
              max={3}
              min={0}
              step={0.1}
              className="w-full"
            />
            <p className="text-sm text-slate-600 mt-2">
              Valor configurado: {taxaJuros.toFixed(1)}% a.m. (self.taxa_juros_mensal = {(taxaJuros/100).toFixed(3)})
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Índices IGPM */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">📊</span>
            Índices IGPM - Correção Monetária
          </CardTitle>
          <CardDescription>
            {Object.keys(indicesIGPM).length} períodos disponíveis de {Object.keys(indicesIGPM)[0]} a {Object.keys(indicesIGPM)[Object.keys(indicesIGPM).length - 1]}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-6">
            <div className="h-64 bg-slate-50 border rounded-lg p-4 overflow-hidden">
              <svg width="100%" height="100%" viewBox="0 0 800 200">
                <defs>
                  <linearGradient id="igpmGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#06b6d4" />
                    <stop offset="50%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
                
                {/* Linha do gráfico */}
                <polyline
                  fill="none"
                  stroke="url(#igpmGradient)"
                  strokeWidth="3"
                  points={dadosGrafico.map((item, index) => {
                    const x = (index / (dadosGrafico.length - 1)) * 760 + 20;
                    const y = 180 - ((item.valor - 520) / (630 - 520)) * 160;
                    return `${x},${y}`;
                  }).join(' ')}
                />
                
                {/* Pontos do gráfico */}
                {dadosGrafico.map((item, index) => {
                  const x = (index / (dadosGrafico.length - 1)) * 760 + 20;
                  const y = 180 - ((item.valor - 520) / (630 - 520)) * 160;
                  return (
                    <circle
                      key={item.periodo}
                      cx={x}
                      cy={y}
                      r="3"
                      fill="#3b82f6"
                      className="hover:r-5 transition-all cursor-pointer"
                    >
                      <title>{`${item.periodo}: ${item.valor}`}</title>
                    </circle>
                  );
                })}
                
                {/* Labels dos anos */}
                {['2020', '2021', '2022', '2023', '2024', '2025'].map((ano, index) => (
                  <text key={ano} x={20 + (index * 760/5)} y={195} textAnchor="middle" className="text-xs fill-slate-600">
                    {ano}
                  </text>
                ))}
              </svg>
            </div>
            <div className="flex justify-between text-sm text-slate-600 mt-2">
              <span>Valor mínimo: {Math.min(...Object.values(indicesIGPM)).toFixed(2)}</span>
              <span>Valor máximo: {Math.max(...Object.values(indicesIGPM)).toFixed(2)}</span>
            </div>
          </div>

          {/* Busca de Índices */}
          <div className="border-t pt-4">
            <h4 className="font-medium mb-3 flex items-center gap-2">
              <span className="text-lg">🔍</span>
              Buscar Índice IGPM
            </h4>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={buscaData}
                onChange={(e) => setBuscaData(e.target.value)}
                placeholder="Ex: 2024.06"
                className="flex-1 px-3 py-2 border border-slate-300 rounded-md"
              />
              <Button onClick={handleBuscaIndice} className="bg-blue-500 hover:bg-blue-600">
                Buscar
              </Button>
            </div>
            {resultadoBusca !== null && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-blue-800">
                  <strong>Resultado:</strong> {resultadoBusca} 
                  {resultadoBusca === 624.40 && buscaData && !indicesIGPM[buscaData as keyof typeof indicesIGPM] && 
                    " (valor padrão - período não encontrado)"
                  }
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Botão para Exibir Parâmetros */}
      {!parametrosExibidos && (
        <div className="text-center">
          <Button 
            onClick={exibirParametros}
            className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white px-8 py-3 text-lg"
          >
            <Settings className="mr-2 h-5 w-5" />
            Exibir Resumo dos Parâmetros
          </Button>
        </div>
      )}

      {/* Output dos Parâmetros */}
      {parametrosExibidos && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-6">
            <div className="font-mono text-sm space-y-1 text-green-800">
              <div className="text-lg font-bold mb-2">⚙️ PARÂMETROS DE CORREÇÃO CONFIGURADOS</div>
              <div className="border-b border-green-300 text-green-600 mb-3">
                {"=".repeat(50)}
              </div>
              <div>⚖️  Taxa de multa: {taxaMulta.toFixed(1)}%</div>
              <div>📈 Taxa de juros mensal: {taxaJuros.toFixed(1)}%</div>
              <div>📊 Índices IGPM: {Object.keys(indicesIGPM).length} períodos disponíveis</div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Grid de Índices IGPM */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">📋</span>
            Tabela Completa de Índices IGPM
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2 max-h-96 overflow-y-auto">
            {Object.entries(indicesIGPM).map(([periodo, valor]) => (
              <div key={periodo} className="p-2 bg-slate-50 border rounded text-center">
                <div className="text-xs font-medium text-slate-600">{periodo}</div>
                <div className="text-sm font-bold text-slate-800">{valor.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
