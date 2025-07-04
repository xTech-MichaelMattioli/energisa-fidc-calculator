
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { ModuloConfiguracoes } from "@/components/modulos/ModuloConfiguracoes";

export function MainContent() {
  return (
    <SidebarInset className="flex-1">
      <header className="flex h-16 items-center gap-2 border-b border-slate-200 bg-white px-6 shadow-sm">
        <SidebarTrigger className="-ml-1" />
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <span>FIDC - Energisa Data Refactor Wizard</span>
        </div>
      </header>
      
      <main className="flex-1 overflow-auto">
        <ModuloConfiguracoes />
      </main>
    </SidebarInset>
  );
}
