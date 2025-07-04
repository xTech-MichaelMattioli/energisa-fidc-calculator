
import { useLocation } from "react-router-dom";
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { ModuloConfiguracoes } from "@/components/modulos/ModuloConfiguracoes";
import { ModuloParametros } from "@/components/modulos/ModuloParametros";
import { ModuloCarregamento } from "@/components/modulos/ModuloCarregamento";

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
        return <div className="p-6 text-center text-slate-600">Módulo 4: Mapeamento - Em construção</div>;
      case "/aging":
        return <div className="p-6 text-center text-slate-600">Módulo 5: Aging - Em construção</div>;
      case "/correcao":
        return <div className="p-6 text-center text-slate-600">Módulo 6: Correção - Em construção</div>;
      case "/analise":
        return <div className="p-6 text-center text-slate-600">Módulo 7: Análise - Em construção</div>;
      case "/exportacao":
        return <div className="p-6 text-center text-slate-600">Módulo 8: Exportação - Em construção</div>;
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
