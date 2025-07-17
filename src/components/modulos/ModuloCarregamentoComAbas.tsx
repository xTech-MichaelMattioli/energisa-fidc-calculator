import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { ModuloCarregamento } from './ModuloCarregamento';
import { UserFilesManager } from '../auth/UserFilesManager';
import { Upload, FolderOpen, BarChart3, FileText, ArrowRight } from 'lucide-react';

export const ModuloCarregamentoComAbas: React.FC = () => {
  const [activeTab, setActiveTab] = useState("upload");

  return (
    <div className="w-full space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Gestão de Arquivos FIDC
          </CardTitle>
          <CardDescription>
            Carregue, processe e gerencie seus arquivos de dados FIDC
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="upload" className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Novo Upload
              </TabsTrigger>
              <TabsTrigger value="files" className="flex items-center gap-2">
                <FolderOpen className="h-4 w-4" />
                Meus Arquivos
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="upload" className="mt-6">
              <ModuloCarregamento />
            </TabsContent>
            
            <TabsContent value="files" className="mt-6">
              <UserFilesManager />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      
      {/* Fluxo de processamento */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Fluxo de Processamento
          </CardTitle>
          <CardDescription>
            Próximos passos após o carregamento dos arquivos
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <div className="flex items-center justify-between space-x-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <Upload className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="font-medium">1. Carregamento</p>
                <p className="text-sm text-gray-600">Upload e validação</p>
              </div>
            </div>
            
            <ArrowRight className="h-4 w-4 text-gray-400" />
            
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <FileText className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="font-medium">2. Mapeamento</p>
                <p className="text-sm text-gray-600">Configurar campos</p>
              </div>
            </div>
            
            <ArrowRight className="h-4 w-4 text-gray-400" />
            
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                <BarChart3 className="h-4 w-4 text-white" />
              </div>
              <div>
                <p className="font-medium">3. Processamento</p>
                <p className="text-sm text-gray-600">Análise e correção</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
