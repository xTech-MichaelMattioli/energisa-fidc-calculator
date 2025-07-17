
import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Settings,
  Database,
  BarChart3,
  TrendingUp,
  PieChart,
  FileText,
  Download
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  useSidebar,
} from "@/components/ui/sidebar";

const modules = [
  { 
    title: "Carregamento", 
    url: "/", 
    icon: Database, 
    description: "Upload e análise das bases ESS e Voltz" 
  },
  { 
    title: "Mapeamento", 
    url: "/mapeamento", 
    icon: BarChart3, 
    description: "Mapeamento de campos" 
  },
  { 
    title: "Correção", 
    url: "/correcao", 
    icon: TrendingUp, 
    description: "Correção monetária e juros" 
  },
  { 
    title: "Análise", 
    url: "/analise", 
    icon: PieChart, 
    description: "Análise dos resultados" 
  },
  { 
    title: "Exportação", 
    url: "/exportacao", 
    icon: Download, 
    description: "Exportação dos resultados" 
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const location = useLocation();
  const currentPath = location.pathname;

  const isActive = (path: string) => currentPath === path;
  const getNavCls = (active: boolean) =>
    active 
      ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-medium shadow-lg" 
      : "hover:bg-gradient-to-r hover:from-cyan-50 hover:to-blue-50 text-slate-700 hover:text-cyan-600";

  return (
    <Sidebar className="border-r border-slate-200 bg-white shadow-lg">
      <SidebarHeader className="p-6 border-b border-slate-200">
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg flex items-center justify-center mb-3">
            <FileText className="h-6 w-6 text-white" />
          </div>
          {state === "expanded" && (
            <>
              <h1 className="text-lg font-bold text-slate-800">FIDC Calculator</h1>
              <p className="text-sm text-slate-600 mt-1">Cálculo de Valor Corrigido</p>
            </>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="p-4">
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
            Módulos do Sistema
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {modules.map((module, index) => (
                <SidebarMenuItem key={module.title}>
                  <SidebarMenuButton 
                    asChild 
                    className={`${getNavCls(isActive(module.url))} rounded-lg transition-all duration-200 mb-1`}
                  >
                    <NavLink to={module.url} className="flex items-center p-3">
                      <div className="flex items-center min-w-0 flex-1">
                        <div className="flex items-center justify-center w-8 h-8 rounded-md bg-slate-100 mr-3 flex-shrink-0">
                          <span className="text-xs font-bold text-slate-600">{index + 1}</span>
                        </div>
                        <module.icon className="h-4 w-4 mr-3 flex-shrink-0" />
                        {state === "expanded" && (
                          <div className="min-w-0 flex-1">
                            <div className="font-medium text-sm truncate">{module.title}</div>
                            <div className="text-xs opacity-75 truncate">{module.description}</div>
                          </div>
                        )}
                      </div>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
