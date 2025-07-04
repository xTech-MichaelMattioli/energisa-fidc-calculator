
import { useLocation, useNavigate } from "react-router-dom";
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { ModuloConfiguracoes } from "@/components/modulos/ModuloConfiguracoes";
import { ModuloParametros } from "@/components/modulos/ModuloParametros";
import { ModuloCarregamento } from "@/components/modulos/ModuloCarregamento";
import { ModuloMapeamento } from "@/components/modulos/ModuloMapeamento";
import { ModuloAging } from "@/components/modulos/ModuloAging";
import { ModuloCorrecao } from "@/components/modulos/ModuloCorrecao";
import { ModuloAnalise } from "@/components/modulos/ModuloAnalise";
import { ModuloExportacao } from "@/components/modulos/ModuloExportacao";
import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function MainContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;
  const [isTransitioning, setIsTransitioning] = useState(false);

  const routes = [
    { path: "/", name: "Configurações" },
    { path: "/parametros", name: "Parâmetros" },
    { path: "/carregamento", name: "Carregamento" },
    { path: "/mapeamento", name: "Mapeamento" },
    { path: "/aging", name: "Aging" },
    { path: "/correcao", name: "Correção" },
    { path: "/analise", name: "Análise" },
    { path: "/exportacao", name: "Exportação" }
  ];

  const currentIndex = routes.findIndex(route => route.path === currentPath);
  const canGoNext = currentIndex < routes.length - 1;
  const canGoPrev = currentIndex > 0;

  const navigateToNext = () => {
    if (canGoNext && !isTransitioning) {
      setIsTransitioning(true);
      setTimeout(() => {
        navigate(routes[currentIndex + 1].path);
        setTimeout(() => setIsTransitioning(false), 300);
      }, 150);
    }
  };

  const navigateToPrev = () => {
    if (canGoPrev && !isTransitioning) {
      setIsTransitioning(true);
      setTimeout(() => {
        navigate(routes[currentIndex - 1].path);
        setTimeout(() => setIsTransitioning(false), 300);
      }, 150);
    }
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'ArrowRight' || event.key === ' ') {
        event.preventDefault();
        navigateToNext();
      } else if (event.key === 'ArrowLeft') {
        event.preventDefault();
        navigateToPrev();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, isTransitioning]);

  // Touch/swipe navigation
  useEffect(() => {
    let startX = 0;
    let endX = 0;

    const handleTouchStart = (e: TouchEvent) => {
      startX = e.changedTouches[0].screenX;
    };

    const handleTouchEnd = (e: TouchEvent) => {
      endX = e.changedTouches[0].screenX;
      const diff = startX - endX;
      
      if (Math.abs(diff) > 50) { // minimum swipe distance
        if (diff > 0) {
          navigateToNext(); // swipe left = next
        } else {
          navigateToPrev(); // swipe right = prev
        }
      }
    };

    window.addEventListener('touchstart', handleTouchStart);
    window.addEventListener('touchend', handleTouchEnd);
    
    return () => {
      window.removeEventListener('touchstart', handleTouchStart);
      window.removeEventListener('touchend', handleTouchEnd);
    };
  }, [currentIndex, isTransitioning]);

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
    <SidebarInset className="flex-1 relative group">
      <header className="flex h-16 items-center gap-2 border-b border-slate-200 bg-white px-6 shadow-sm">
        <SidebarTrigger className="-ml-1" />
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <span>FIDC - Energisa Data Refactor Wizard</span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="text-xs text-slate-500">
            {currentIndex + 1} / {routes.length} - {routes[currentIndex]?.name}
          </div>
          <div className="flex gap-1">
            {routes.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-colors ${
                  i === currentIndex ? 'bg-indigo-600' : 'bg-slate-300'
                }`}
              />
            ))}
          </div>
        </div>
      </header>
      
      {/* Navigation arrows */}
      {canGoPrev && (
        <button
          onClick={navigateToPrev}
          className="absolute left-4 top-1/2 -translate-y-1/2 z-10 bg-white/90 hover:bg-white shadow-lg rounded-full p-3 opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-110"
          disabled={isTransitioning}
        >
          <ChevronLeft className="h-6 w-6 text-slate-600" />
        </button>
      )}
      
      {canGoNext && (
        <button
          onClick={navigateToNext}
          className="absolute right-4 top-1/2 -translate-y-1/2 z-10 bg-white/90 hover:bg-white shadow-lg rounded-full p-3 opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-110"
          disabled={isTransitioning}
        >
          <ChevronRight className="h-6 w-6 text-slate-600" />
        </button>
      )}
      
      <main className={`flex-1 overflow-auto transition-all duration-300 ${
        isTransitioning ? 'opacity-0 transform scale-95' : 'opacity-100 transform scale-100'
      }`}>
        {renderModule()}
      </main>

      {/* Instructions */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs text-slate-400 bg-white/80 px-3 py-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
        Use ← → ou swipe para navegar • Espaço para avançar
      </div>
    </SidebarInset>
  );
}
