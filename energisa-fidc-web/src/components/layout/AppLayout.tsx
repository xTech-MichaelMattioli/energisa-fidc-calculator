import { Stepper } from "./Stepper";
import { Zap } from "lucide-react";
import type { ReactNode } from "react";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-200/60">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-sm">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-foreground leading-none">
                Energisa FIDC
              </h1>
              <p className="text-[11px] text-muted-foreground">
                Calculadora de Valor Justo
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="px-2 py-1 rounded-md bg-blue-50 text-blue-600 font-medium">
              v2.0
            </span>
          </div>
        </div>

        {/* ── Stepper ── */}
        <div className="max-w-7xl mx-auto px-6 border-t border-slate-100">
          <Stepper />
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
        {children}
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-200/60 bg-white/60 backdrop-blur-sm py-4">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between text-xs text-muted-foreground">
          <span>© 2025 Business Integration Partners — Energisa S.A.</span>
          <span>Desenvolvido por BIP Group</span>
        </div>
      </footer>
    </div>
  );
}
