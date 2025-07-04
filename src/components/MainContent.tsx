
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
  const [showControls, setShowControls] = useState(false);
  const [mouseY, setMouseY] = useState(0);
  const [mouseX, setMouseX] = useState(0);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);

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

  // Mouse and navigation controls
  useEffect(() => {
    let mouseTimeout: NodeJS.Timeout;
    
    const handleMouseMove = (e: MouseEvent) => {
      setMouseY(e.clientY);
      setMouseX(e.clientX);
      setShowControls(true);
      
      // Mostrar setas apenas quando próximo das bordas
      const windowWidth = window.innerWidth;
      const proximityThreshold = 100; // 100px da borda
      
      setShowLeftArrow(canGoPrev && e.clientX <= proximityThreshold);
      setShowRightArrow(canGoNext && e.clientX >= windowWidth - proximityThreshold);
      
      clearTimeout(mouseTimeout);
      mouseTimeout = setTimeout(() => {
        setShowControls(false);
        setShowLeftArrow(false);
        setShowRightArrow(false);
      }, 3000);
    };

    // Navegação apenas com Ctrl + Scroll para não interferir no scroll normal
    const handleScroll = (e: WheelEvent) => {
      // Só navega se Ctrl estiver pressionado
      if (e.ctrlKey && Math.abs(e.deltaY) > 20 && !isTransitioning) {
        e.preventDefault();
        if (e.deltaY > 0) {
          navigateToNext();
        } else {
          navigateToPrev();
        }
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('wheel', handleScroll, { passive: false });
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('wheel', handleScroll);
      clearTimeout(mouseTimeout);
    };
  }, [currentIndex, isTransitioning, canGoPrev, canGoNext]);

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
    <SidebarInset className="flex-1 relative overflow-hidden">
      <header className="flex h-16 items-center gap-2 border-b border-slate-200 bg-white px-6 shadow-sm relative z-20">
        <SidebarTrigger className="-ml-1" />
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <span>FIDC - Energisa Data Refactor Wizard</span>
        </div>
        
        {/* Floating progress indicator */}
        <div className={`ml-auto flex items-center gap-3 transition-all duration-500 ${
          showControls ? 'opacity-100 translate-y-0' : 'opacity-40 translate-y-1'
        }`}>
          <div className="text-xs text-slate-500 font-medium">
            {routes[currentIndex]?.name}
          </div>
          <div className="flex gap-1.5">
            {routes.map((route, i) => (
              <button
                key={i}
                onClick={() => {
                  if (!isTransitioning && i !== currentIndex) {
                    setIsTransitioning(true);
                    setTimeout(() => {
                      navigate(route.path);
                      setTimeout(() => setIsTransitioning(false), 300);
                    }, 150);
                  }
                }}
                className={`w-1.5 h-1.5 rounded-full transition-all duration-300 cursor-pointer ${
                  i === currentIndex 
                    ? 'bg-indigo-600 scale-125 shadow-sm' 
                    : i < currentIndex 
                      ? 'bg-indigo-400 hover:bg-indigo-500' 
                      : 'bg-slate-300 hover:bg-slate-400'
                }`}
                title={route.name}
              />
            ))}
          </div>
        </div>
      </header>
      
      {/* Navigation zones - aparecem apenas quando mouse próximo das bordas */}
      {showLeftArrow && (
        <div
          onClick={navigateToPrev}
          className="absolute left-0 top-16 bottom-0 w-20 z-10 cursor-pointer group/nav hover:bg-black/5 transition-colors"
        >
          <div className="absolute left-3 top-1/2 -translate-y-1/2 bg-black/70 hover:bg-black/90 text-white rounded-full p-3 transition-all duration-300 opacity-90 scale-100">
            <ChevronLeft className="h-5 w-5" />
          </div>
        </div>
      )}
      
      {showRightArrow && (
        <div
          onClick={navigateToNext}
          className="absolute right-0 top-16 bottom-0 w-20 z-10 cursor-pointer group/nav hover:bg-black/5 transition-colors"
        >
          <div className="absolute right-3 top-1/2 -translate-y-1/2 bg-black/70 hover:bg-black/90 text-white rounded-full p-3 transition-all duration-300 opacity-90 scale-100">
            <ChevronRight className="h-5 w-5" />
          </div>
        </div>
      )}
      
      <main className={`flex-1 overflow-auto transition-all duration-500 ease-out ${
        isTransitioning 
          ? 'opacity-0 transform translate-x-4 scale-98' 
          : 'opacity-100 transform translate-x-0 scale-100'
      }`}>
        {renderModule()}
      </main>

      {/* Floating help text */}
      <div className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-30 transition-all duration-700 ${
        showControls && currentIndex === 0
          ? 'opacity-100 translate-y-0' 
          : 'opacity-0 translate-y-2 pointer-events-none'
      }`}>
        <div className="bg-black/90 text-white text-xs px-4 py-2 rounded-full backdrop-blur-sm">
          Use Ctrl + scroll, setas ou clique nos indicadores para navegar
        </div>
      </div>
      
      {/* Progress bar at bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-200">
        <div 
          className="h-full bg-gradient-to-r from-indigo-500 to-indigo-600 transition-all duration-700 ease-out"
          style={{ width: `${((currentIndex + 1) / routes.length) * 100}%` }}
        />
      </div>
    </SidebarInset>
  );
}
