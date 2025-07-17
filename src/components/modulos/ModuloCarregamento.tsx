import { useState, useRef, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Upload, 
  FileText, 
  ArrowRight, 
  CheckCircle, 
  AlertTriangle,
  Database,
  Info,
  X,
  Eye,
  FileSpreadsheet
} from "lucide-react";
import DataService, { ArquivoBase } from "@/services/dataService";
import { supabaseExcelService } from "@/services/supabaseExcelService";
import * as XLSX from 'xlsx';

interface CampoObrigatorio {
  nome: string;
  variações: string[];
  descricao: string;
  tipo: 'texto' | 'número' | 'data' | 'monetário';
}

interface ValidacaoResultado {
  valido: boolean;
  camposEncontrados: { [key: string]: string | null };
  camposFaltantes: string[];
  score: number;
}

interface ArquivoCarregado {
  nome: string;
  tamanho: number;
  tipo: string;
  status: 'carregado' | 'processando' | 'validando' | 'validado' | 'mapeado' | 'erro';
  registros?: number;
  colunas?: string[];
  preview?: any[];
  erro?: string;
  progresso?: number;
  base?: ArquivoBase;
  validacao?: ValidacaoResultado;
}

export function ModuloCarregamento() {
  const [arquivos, setArquivos] = useState<ArquivoCarregado[]>([]);
  const [processandoArquivo, setProcessandoArquivo] = useState<string | null>(null);
  const [mostrandoPreview, setMostrandoPreview] = useState<string | null>(null);
  const [usarEdgeFunction, setUsarEdgeFunction] = useState(true); // Preferir Edge Function por padrão
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dataService = DataService.getInstance();

  // Definição dos campos obrigatórios baseado no notebook FIDC
  const camposObrigatorios: CampoObrigatorio[] = [
    {
      nome: 'cliente_nome',
      variações: ['nome', 'cliente', 'razao', 'razão social', 'nome cliente', 'nome_cliente', 'parceiro negocio'],
      descricao: 'Nome/Razão Social do Cliente',
      tipo: 'texto'
    },
    {
      nome: 'documento',
      variações: ['cpf', 'cnpj', 'documento', 'numero cpf', 'numero cnpj', 'cpf/cnpj', 'identificacao'],
      descricao: 'CPF/CNPJ do Cliente',
      tipo: 'texto'
    },
    {
      nome: 'contrato',
      variações: ['contrato', 'conta contrato', 'uc', 'instalacao', 'instalação', 'numero contrato', 'conta'],
      descricao: 'Número do Contrato/UC',
      tipo: 'texto'
    },
    {
      nome: 'valor_principal',
      variações: ['fatura', 'faturas', 'valor fatura', 'partida aberto', 'valor original', 'debito', 'valor'],
      descricao: 'Valor Principal da Fatura',
      tipo: 'monetário'
    },
    {
      nome: 'data_vencimento',
      variações: ['vencimento', 'data vencimento', 'dt vencimento', 'prazo', 'data prazo', 'venc'],
      descricao: 'Data de Vencimento',
      tipo: 'data'
    }
  ];

  const camposOpcionais: CampoObrigatorio[] = [
    {
      nome: 'valor_cosip',
      variações: ['cosip', 'cip', 'iluminacao', 'contrib ilum'],
      descricao: 'Valor COSIP/CIP',
      tipo: 'monetário'
    },
    {
      nome: 'valor_terceiros',
      variações: ['terceiros', 'outros valores', 'terceiro', 'outros'],
      descricao: 'Valores de Terceiros',
      tipo: 'monetário'
    },
    {
      nome: 'juros_multa',
      variações: ['juros', 'multa', 'encargos', 'financeiros'],
      descricao: 'Juros/Multa',
      tipo: 'monetário'
    },
    {
      nome: 'classe',
      variações: ['classe', 'categoria', 'tipo cliente', 'segmento'],
      descricao: 'Classe/Categoria do Cliente',
      tipo: 'texto'
    }
  ];

  // Função para validar estrutura FIDC
  const validarEstruturaFIDC = (colunas: string[]): ValidacaoResultado => {
    console.log('=== VALIDAÇÃO ESTRUTURA FIDC ===');
    console.log('Colunas recebidas:', colunas);
    
    // Garantir que todas as colunas sejam strings válidas
    const colunasLimpas = colunas
      .filter(col => col && typeof col === 'string')
      .map(col => col.toString().trim())
      .filter(col => col !== '');
    
    const colunasLower = colunasLimpas.map(col => col.toLowerCase().trim());
    console.log('Colunas processadas:', colunasLimpas);
    console.log('Colunas em lowercase:', colunasLower);
    
    const camposEncontrados: { [key: string]: string | null } = {};
    const camposFaltantes: string[] = [];

    // Verificar campos obrigatórios
    camposObrigatorios.forEach(campo => {
      console.log(`\n--- Verificando campo: ${campo.nome} ---`);
      console.log(`Variações aceitas: ${campo.variações.join(', ')}`);
      
      let encontrado = false;
      
      for (const variacao of campo.variações) {
        console.log(`  Testando variação: "${variacao}"`);
        
        const colunaEncontrada = colunasLower.find(col => {
          const match1 = col.includes(variacao.toLowerCase());
          const match2 = variacao.toLowerCase().includes(col);
          console.log(`    "${col}" inclui "${variacao.toLowerCase()}"? ${match1}`);
          console.log(`    "${variacao.toLowerCase()}" inclui "${col}"? ${match2}`);
          return match1 || match2;
        });
        
        if (colunaEncontrada) {
          const indiceOriginal = colunasLower.indexOf(colunaEncontrada);
          camposEncontrados[campo.nome] = colunasLimpas[indiceOriginal];
          console.log(`  ✅ ENCONTRADO! Coluna: "${colunasLimpas[indiceOriginal]}" para campo ${campo.nome}`);
          encontrado = true;
          break;
        }
      }
      
      if (!encontrado) {
        console.log(`  ❌ NÃO ENCONTRADO para campo ${campo.nome}`);
        camposFaltantes.push(campo.nome);
        camposEncontrados[campo.nome] = null;
      }
    });

    // Calcular score de compatibilidade
    const camposObrigatoriosEncontrados = camposObrigatorios.length - camposFaltantes.length;
    const score = (camposObrigatoriosEncontrados / camposObrigatorios.length) * 100;

    console.log('\n=== RESULTADO DA VALIDAÇÃO ===');
    console.log('Campos encontrados:', camposEncontrados);
    console.log('Campos faltantes:', camposFaltantes);
    console.log('Score:', score);

    return {
      valido: camposFaltantes.length === 0,
      camposEncontrados,
      camposFaltantes,
      score: Math.round(score)
    };
  };

  const handleFileUpload = useCallback((event: any) => {
    const files = Array.from(event.target.files || []) as File[];
    
    files.forEach(file => {
      // Verificar tipo de arquivo
      if (!file.name.match(/\.(xlsx|xls|csv)$/i)) {
        const arquivoErro: ArquivoCarregado = {
          nome: file.name,
          tamanho: file.size,
          tipo: file.type,
          status: 'erro',
          erro: 'Formato não suportado. Use Excel (.xlsx, .xls) ou CSV (.csv)'
        };
        setArquivos(prev => [...prev, arquivoErro]);
        return;
      }

      const novoArquivo: ArquivoCarregado = {
        nome: file.name,
        tamanho: file.size,
        tipo: file.type,
        status: 'carregado',
        progresso: 0
      };

      setArquivos(prev => [...prev, novoArquivo]);
      
      // Processar arquivo real
      setTimeout(() => processarArquivoReal(file), 500);
    });

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const processarArquivoReal = async (file: File) => {
    setProcessandoArquivo(file.name);
    
    let colunas: string[] = [];
    let dados: any[] = [];
    let validacao: ValidacaoResultado | undefined;
    
    // Atualizar status para processando
    setArquivos(prev => prev.map(arq => 
      arq.nome === file.name 
        ? { ...arq, status: 'processando', progresso: 0 }
        : arq
    ));

    try {
      // Progresso inicial - Upload para Supabase Storage
      setArquivos(prev => prev.map(arq => 
        arq.nome === file.name 
          ? { ...arq, progresso: 10 }
          : arq
      ));

      // 1. Fazer upload do arquivo para o Supabase Storage
      console.log('📤 Fazendo upload para Supabase Storage:', file.name);
      const uploadResult = await supabaseExcelService.uploadFile(file);
      
      if (!uploadResult.success) {
        throw new Error(`Erro no upload: ${uploadResult.error}`);
      }
      
      console.log('✅ Upload concluído:', uploadResult.fileUrl);
      
      // Progresso após upload
      setArquivos(prev => prev.map(arq => 
        arq.nome === file.name 
          ? { ...arq, progresso: 30 }
          : arq
      ));

      // 2. Processar arquivo localmente para obter dados
      if (file.name.toLowerCase().endsWith('.csv')) {
        // Processar CSV
        // Processar CSV
        const texto = await file.text();
        console.log('Conteúdo do arquivo CSV (primeiros 500 chars):', texto.substring(0, 500));
        
        const linhas = texto.split('\n').filter(linha => linha.trim());
        console.log('Total de linhas encontradas:', linhas.length);
        
        if (linhas.length > 0) {
          // Detectar separador analisando a primeira linha
          const primeiraLinha = linhas[0];
          console.log('Primeira linha:', primeiraLinha);
          
          // Contar ocorrências de possíveis separadores
          const contadorVirgula = (primeiraLinha.match(/,/g) || []).length;
          const contadorPontoVirgula = (primeiraLinha.match(/;/g) || []).length;
          const contadorTab = (primeiraLinha.match(/\t/g) || []).length;
          
          console.log('Separadores encontrados:', { vírgula: contadorVirgula, pontoVirgula: contadorPontoVirgula, tab: contadorTab });
          
          // Escolher o separador mais provável
          let separador = ','; // padrão
          if (contadorPontoVirgula > contadorVirgula && contadorPontoVirgula > contadorTab) {
            separador = ';';
          } else if (contadorTab > contadorVirgula && contadorTab > contadorPontoVirgula) {
            separador = '\t';
          }
          
          console.log('Separador escolhido:', separador === '\t' ? 'TAB' : separador);
          
          // Extrair cabeçalhos
          colunas = primeiraLinha.split(separador).map(col => col.trim().replace(/^["']|["']$/g, ''));
          console.log('Colunas extraídas:', colunas);
          
          // Progresso de leitura
          setArquivos(prev => prev.map(arq => 
            arq.nome === file.name 
              ? { ...arq, progresso: 50 }
              : arq
          ));
          
          // Processar dados (máximo 1000 linhas para performance e visualização)
          const linhasDados = linhas.slice(1, Math.min(1001, linhas.length));
          console.log('Processando', linhasDados.length, 'linhas de dados');
          
          dados = linhasDados.map((linha, index) => {
            if (!linha.trim()) return null; // Pular linhas vazias
            
            const valores = linha.split(separador).map(val => val.trim().replace(/^["']|["']$/g, ''));
            const objeto: any = {};
            
            colunas.forEach((col, i) => {
              objeto[col] = valores[i] || '';
            });
            
            return objeto;
          }).filter(obj => obj !== null && Object.values(obj).some(val => String(val).trim() !== ''));
          
          console.log('Dados processados:', dados.length, 'registros válidos');
          console.log('Amostra dos primeiros 3 registros:', dados.slice(0, 3));
        }
      } else {
        // Processar Excel - já foi feito upload, agora tentar Edge Function primeiro
        console.log('Processando arquivo Excel:', file.name);
        
        setArquivos(prev => prev.map(arq => 
          arq.nome === file.name 
            ? { ...arq, progresso: 40 }
            : arq
        ));

        if (usarEdgeFunction) {
          console.log('🚀 Tentando processar via Edge Function do Supabase...');
          
          try {
            const result = await supabaseExcelService.processExcelFile(file);
            
            if (result.success) {
              console.log('✅ Processamento via Edge Function bem-sucedido!');
              
              colunas = result.columns;
              dados = result.preview; // Edge Function já retorna dados processados
              
              // Atualizar progresso
              setArquivos(prev => prev.map(arq => 
                arq.nome === file.name 
                  ? { ...arq, progresso: 80 }
                  : arq
              ));
              
              console.log('Dados da Edge Function:', {
                totalRecords: result.totalRecords,
                columns: result.columns.length,
                previewRecords: result.preview.length,
                score: result.validation.score
              });
              
              // Usar validação da Edge Function
              validacao = result.validation;
              
            } else {
              throw new Error(result.error || 'Edge Function retornou erro');
            }
            
          } catch (edgeError) {
            console.warn('⚠️ Edge Function falhou, usando processamento local:', edgeError);
            // Fallback para processamento local
            await processarExcelLocal();
          }
        } else {
          // Processamento local direto
          await processarExcelLocal();
        }
        
        async function processarExcelLocal() {
          console.log('🔄 Processando Excel localmente...');
          
          setArquivos(prev => prev.map(arq => 
            arq.nome === file.name 
              ? { ...arq, progresso: 50 }
              : arq
          ));

          try {
            // Ler arquivo Excel como ArrayBuffer
            const arrayBuffer = await new Promise<ArrayBuffer>((resolve, reject) => {
              const reader = new FileReader();
              reader.onload = (e) => resolve(e.target?.result as ArrayBuffer);
              reader.onerror = () => reject(new Error('Erro ao ler arquivo'));
              reader.readAsArrayBuffer(file);
            });

            console.log('Arquivo Excel lido como ArrayBuffer, tamanho:', arrayBuffer.byteLength);

            // Parse do arquivo Excel
            const workbook = XLSX.read(arrayBuffer, { type: 'array' });
            console.log('Workbook criado, sheets disponíveis:', workbook.SheetNames);

            // Pegar a primeira planilha
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            console.log('Processando planilha:', firstSheetName);

            // Converter para JSON
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
            console.log('Dados convertidos para JSON, total de linhas:', jsonData.length);

            if (jsonData.length > 0) {
              // Primeira linha como cabeçalhos
              const headers = jsonData[0] as any[];
              colunas = headers
                .map(header => header ? header.toString().trim() : '')
                .filter(header => header !== '');
              console.log('Colunas extraídas do Excel:', colunas);

              // Progresso
              setArquivos(prev => prev.map(arq => 
                arq.nome === file.name 
                  ? { ...arq, progresso: 70 }
                  : arq
              ));

              // Processar dados (máximo 1000 linhas para performance)
              const dataRows = jsonData.slice(1, Math.min(1001, jsonData.length)) as any[][];
              console.log('Processando', dataRows.length, 'linhas de dados do Excel');

              dados = dataRows.map((row, index) => {
                if (!row || row.length === 0) return null;
                
                const objeto: any = {};
                colunas.forEach((col, i) => {
                  // Garantir que col seja uma string válida
                  const coluna = col ? col.toString().trim() : `Coluna_${i}`;
                  if (!coluna) return;
                  
                  const valor = row[i];
                  // Converter valores Excel para string, tratando datas e números
                  if (valor !== undefined && valor !== null) {
                    if (typeof valor === 'number' && valor > 25567 && valor < 100000) {
                      // Possível data Excel (número de dias desde 1900)
                      try {
                        const excelDate = new Date((valor - 25569) * 86400 * 1000);
                        const day = excelDate.getUTCDate().toString().padStart(2, '0');
                        const month = (excelDate.getUTCMonth() + 1).toString().padStart(2, '0');
                        const year = excelDate.getUTCFullYear();
                        objeto[coluna] = `${day}/${month}/${year}`;
                      } catch {
                        objeto[coluna] = valor.toString();
                      }
                    } else {
                      objeto[coluna] = valor.toString();
                    }
                  } else {
                    objeto[coluna] = '';
                  }
                });
                
                return objeto;
              }).filter(obj => obj !== null && Object.values(obj).some(val => String(val).trim() !== ''));

              console.log('Dados do Excel processados:', dados.length, 'registros válidos');
              console.log('Amostra dos primeiros 3 registros:', dados.slice(0, 3));
              
            } else {
              throw new Error('Arquivo Excel vazio ou sem dados');
            }

          } catch (error) {
            console.error('Erro ao processar arquivo Excel:', error);
            throw new Error(`Erro ao processar Excel: ${error instanceof Error ? error.message : 'Erro desconhecido'}`);
          }
        }
      }

      // Progresso da validação
      setArquivos(prev => prev.map(arq => 
        arq.nome === file.name 
          ? { ...arq, status: 'validando', progresso: 80 }
          : arq
      ));

      await new Promise(resolve => setTimeout(resolve, 500));

      // Realizar validação FIDC com dados reais
      console.log('=== INICIANDO VALIDAÇÃO FIDC ===');
      console.log('Colunas para validação:', colunas);
      
      // Se não temos validação da Edge Function, fazer validação local
      if (!validacao) {
        validacao = validarEstruturaFIDC(colunas);
      }
      
      console.log('Resultado da validação:', validacao);

      // Finalizar processamento
      for (let i = 85; i <= 100; i += 5) {
        await new Promise(resolve => setTimeout(resolve, 100));
        
        setArquivos(prev => prev.map(arq => 
          arq.nome === file.name 
            ? { ...arq, progresso: i }
            : arq
        ));
      }

      console.log('=== RESULTADO FINAL ===');
      console.log('Total de registros:', dados.length);
      console.log('Colunas identificadas:', colunas);
      console.log('Preview dos dados:', dados.slice(0, 3));
      console.log('Validação FIDC:', validacao);
      console.log('Arquivo salvo no Supabase Storage:', uploadResult.fileUrl);

      // Resultado final com dados reais
      setArquivos(prev => prev.map(arq => 
        arq.nome === file.name 
          ? { 
              ...arq, 
              status: validacao.valido ? 'validado' : 'erro',
              progresso: 100,
              registros: dados.length,
              colunas: colunas,
              preview: dados.slice(0, 5), // Primeiras 5 linhas reais
              validacao: validacao,
              erro: !validacao.valido ? `Estrutura FIDC incompleta (${validacao.score}% compatível)` : undefined
            }
          : arq
      ));

    } catch (error) {
      console.error('Erro ao processar arquivo:', error);
      
      setArquivos(prev => prev.map(arq => 
        arq.nome === file.name 
          ? { 
              ...arq, 
              status: 'erro',
              progresso: 100,
              erro: `Erro ao processar arquivo: ${error instanceof Error ? error.message : 'Erro desconhecido'}`
            }
          : arq
      ));
    }

    setProcessandoArquivo(null);
  };

  const togglePreview = (nomeArquivo: string) => {
    setMostrandoPreview(prev => prev === nomeArquivo ? null : nomeArquivo);
  };

  const removerArquivo = (nomeArquivo: string) => {
    setArquivos(prev => prev.filter(arq => arq.nome !== nomeArquivo));
    if (mostrandoPreview === nomeArquivo) {
      setMostrandoPreview(null);
    }
  };

  const formatarTamanho = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const todosArquivosMapeados = arquivos.length > 0 && arquivos.every(arq => arq.status === 'mapeado' || arq.status === 'validado');

  const passarProximoModulo = () => {
    const dadosCarregamento = {
      arquivos: arquivos.map(arq => ({
        nome: arq.nome,
        registros: arq.registros,
        colunas: arq.colunas,
        preview: arq.preview
      })),
      dataProcessamento: new Date().toISOString()
    };
    
    localStorage.setItem('dadosCarregamento', JSON.stringify(dadosCarregamento));
    window.location.href = '/mapeamento';
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header do Módulo */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-slate-800 flex items-center justify-center gap-3">
          <Database className="h-8 w-8 text-cyan-600" />
          Módulo 1: Carregamento de Dados
        </h1>
        <p className="text-lg text-slate-600">
          Upload e análise das bases de dados
        </p>
      </div>

      {/* Informações discretas sobre estrutura FIDC */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload de Arquivos
          </CardTitle>
          <CardDescription>
            Faça upload dos arquivos CSV ou Excel das bases ESS e Voltz.
            Os arquivos são sincronizados automaticamente com o Supabase Storage e validados pela estrutura FIDC.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Campos esperados - versão compacta */}
            <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-800">
                <strong>Campos esperados:</strong> Nome do Cliente, CPF/CNPJ, Contrato/UC, Valor da Fatura, Data de Vencimento
              </p>
            </div>

            {/* Formatos suportados - versão compacta */}
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <p className="text-sm text-slate-700">
                <strong>Formatos:</strong> CSV, Excel (.xlsx, .xls) • <strong>Tamanho máximo:</strong> 100MB
              </p>
            </div>
            
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-cyan-400 transition-colors">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                multiple
                onChange={handleFileUpload}
                className="hidden"
              />
              <div className="space-y-4">
                <div className="mx-auto w-12 h-12 bg-cyan-100 rounded-full flex items-center justify-center">
                  <Upload className="h-6 w-6 text-cyan-600" />
                </div>
                <div>
                  <p className="text-lg font-medium text-slate-900">
                    Clique para fazer upload ou arraste arquivos aqui
                  </p>
                  <p className="text-sm text-slate-500">
                    Suporte para CSV, Excel (.xlsx, .xls) - Máximo 100MB por arquivo
                  </p>
                </div>
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-gradient-to-r from-cyan-500 to-blue-500"
                >
                  Selecionar Arquivos
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Arquivos Carregados */}
      {arquivos.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Arquivos Carregados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {arquivos.map((arquivo) => (
                <div key={arquivo.nome} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-slate-500" />
                      <div>
                        <p className="font-medium">{arquivo.nome}</p>
                        <p className="text-sm text-slate-500">
                          {formatarTamanho(arquivo.tamanho)} • {arquivo.tipo}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={
                        arquivo.status === 'validado' ? 'default' :
                        arquivo.status === 'mapeado' ? 'default' :
                        arquivo.status === 'processando' ? 'secondary' :
                        arquivo.status === 'validando' ? 'secondary' :
                        arquivo.status === 'erro' ? 'destructive' : 'outline'
                      }>
                        {(arquivo.status === 'validado' || arquivo.status === 'mapeado') && <CheckCircle className="h-3 w-3 mr-1" />}
                        {arquivo.status === 'erro' && <AlertTriangle className="h-3 w-3 mr-1" />}
                        {arquivo.status === 'validando' ? 'Validando FIDC' : 
                         arquivo.status === 'validado' ? 'Validado e Sincronizado' :
                         arquivo.status === 'mapeado' ? 'Processado e Sincronizado' : 
                         arquivo.status}
                      </Badge>
                      {arquivo.preview && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => togglePreview(arquivo.nome)}
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          Preview
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => removerArquivo(arquivo.nome)}
                        disabled={arquivo.status === 'processando' || arquivo.status === 'validando'}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {(arquivo.status === 'processando' || arquivo.status === 'validando') && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>
                          {arquivo.status === 'processando' ? 
                            (arquivo.progresso < 30 ? 'Enviando para Supabase Storage...' : 'Processando arquivo...') 
                            : 'Validando estrutura FIDC...'}
                        </span>
                        <span>{arquivo.progresso}%</span>
                      </div>
                      <Progress value={arquivo.progresso} className="h-2" />
                    </div>
                  )}

                  {(arquivo.status === 'validado' || arquivo.status === 'mapeado') && arquivo.validacao && (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <FileSpreadsheet className="h-4 w-4 text-green-600" />
                        <span className="text-sm font-medium">Estrutura FIDC Validada</span>
                        <Badge variant="outline" className="bg-green-50 text-green-700">
                          {arquivo.validacao.score}% compatível
                        </Badge>
                      </div>
                      
                      <div className="text-sm text-slate-600 space-y-1">
                        <p>• {arquivo.registros?.toLocaleString('pt-BR')} registros encontrados</p>
                        <p>• {arquivo.colunas?.length} colunas identificadas</p>
                        <p>• {Object.values(arquivo.validacao.camposEncontrados).filter(v => v !== null).length}/{camposObrigatorios.length} campos obrigatórios encontrados</p>
                        <p>• ✅ Arquivo salvo no Supabase Storage</p>
                      </div>

                      {arquivo.validacao.camposFaltantes.length > 0 && (
                        <Alert>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>
                            <span className="font-medium">Campos faltantes:</span> {arquivo.validacao.camposFaltantes.join(', ')}
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  )}

                  {arquivo.status === 'mapeado' && !arquivo.validacao && (
                    <div className="text-sm text-slate-600 space-y-1">
                      <p>• {arquivo.registros?.toLocaleString('pt-BR')} registros encontrados</p>
                      <p>• {arquivo.colunas?.length} colunas identificadas</p>
                      <p>• ✅ Arquivo salvo no Supabase Storage</p>
                    </div>
                  )}

                  {arquivo.status === 'erro' && (
                    <div className="text-sm text-red-600">
                      <p>Erro: {arquivo.erro}</p>
                    </div>
                  )}

                  {/* Preview dos dados */}
                  {mostrandoPreview === arquivo.nome && arquivo.preview && (
                    <div className="mt-4 border-t pt-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Eye className="h-4 w-4 text-blue-600" />
                        <span className="text-sm font-medium">Preview dos Dados</span>
                      </div>
                      
                      <div className="bg-slate-50 rounded-lg p-3 overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              {arquivo.colunas?.slice(0, 6).map((coluna) => (
                                <TableHead key={coluna} className="text-xs font-medium">
                                  {coluna}
                                </TableHead>
                              ))}
                              {arquivo.colunas && arquivo.colunas.length > 6 && (
                                <TableHead className="text-xs text-slate-500">...</TableHead>
                              )}
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {arquivo.preview.slice(0, 3).map((linha, idx) => (
                              <TableRow key={idx}>
                                {arquivo.colunas?.slice(0, 6).map((coluna) => (
                                  <TableCell key={coluna} className="text-xs py-2">
                                    {linha[coluna] || '-'}
                                  </TableCell>
                                ))}
                                {arquivo.colunas && arquivo.colunas.length > 6 && (
                                  <TableCell className="text-xs text-slate-400">...</TableCell>
                                )}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                      
                      <p className="text-xs text-slate-500 mt-2">
                        Mostrando 3 de {arquivo.registros?.toLocaleString('pt-BR')} registros • 
                        {arquivo.colunas && arquivo.colunas.length > 6 
                          ? ` 6 de ${arquivo.colunas.length} colunas` 
                          : ` ${arquivo.colunas?.length} colunas`}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Botão de Próximo Módulo */}
      <Card className={todosArquivosMapeados ? "border-green-200 bg-green-50" : "border-slate-200"}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="font-semibold flex items-center gap-2">
                <Info className="h-5 w-5" />
                Status do Carregamento
              </h3>
              <p className="text-sm text-slate-600">
                {arquivos.filter(arq => arq.status === 'mapeado' || arq.status === 'validado').length} de {arquivos.length} arquivo(s) processado(s)
              </p>
            </div>
            
            <Button
              onClick={passarProximoModulo}
              disabled={!todosArquivosMapeados}
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