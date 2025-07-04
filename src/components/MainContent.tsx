
import { useLocation } from "react-router-dom";
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { ModuloConfiguracoes } from "@/components/modulos/ModuloConfiguracoes";
import { ModuloParametros } from "@/components/modulos/ModuloParametros";
import { ModuloCarregamento } from "@/components/modulos/ModuloCarregamento";
import { ModuloMapeamento } from "@/components/modulos/ModuloMapeamento";
import { ModuloAging } from "@/components/modulos/ModuloAging";
import { ModuloCorrecao } from "@/components/modulos/ModuloCorrecao";
import { ModuloAnalise } from "@/components/modulos/ModuloAnalise";
import { ModuloExportacao } from "@/components/modulos/ModuloExportacao";

export function MainContent() {
  const location = useLocation();
  const currentPath = location.pathname;

  const renderModule = () => {
    switch (currentPath) {
      case "/":
        return <ModuloConfiguracoes />;
      case "/parametros":
        return <ModuloParametros />;
      case "/carregamento":
        return <ModuloCarregamento />;
      case "/mapeamento":
        return <ModuloMapeamento />;
      case "/aging":
        return <ModuloAging />;
      case "/correcao":
        return <ModuloCorrecao />;
      case "/analise":
        return <ModuloAnalise />;
      case "/exportacao":
        return <ModuloExportacao />;
      default:
        return <ModuloConfiguracoes />;
    }
  };

  return (
    <SidebarInset className="flex-1">
      <header className="flex h-16 items-center gap-2 border-b border-slate-200 bg-white px-6 shadow-sm">
        <SidebarTrigger className="-ml-1" />
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <span>FIDC - Energisa Data Refactor Wizard</span>
        </div>
      </header>
      
      <main className="flex-1 overflow-auto">
        {renderModule()}
      </main>
    </SidebarInset>
  );
}
