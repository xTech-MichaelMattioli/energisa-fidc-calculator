import { useApp } from "@/context/AppContext";
import { PIPELINE_STEPS } from "@/types";
import {
  Upload,
  GitBranch,
  TrendingUp,
  Calculator,
  BarChart3,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  Upload,
  GitBranch,
  TrendingUp,
  Calculator,
  BarChart3,
};

export function Stepper() {
  const { currentStep, setCurrentStep, results, uploadedFiles, mappedRecords } = useApp();

  const canNavigate = (stepIdx: number) => {
    if (stepIdx === 0) return true;
    if (stepIdx === 1) return uploadedFiles.length > 0;
    if (stepIdx === 2) return mappedRecords.length > 0;
    if (stepIdx === 3) return mappedRecords.length > 0;
    if (stepIdx === 4) return results.length > 0;
    return false;
  };

  return (
    <nav className="flex items-center justify-center gap-0 py-6 px-4">
      {PIPELINE_STEPS.map((step, idx) => {
        const Icon = ICONS[step.icon] ?? Calculator;
        const isActive = idx === currentStep;
        const isCompleted = idx < currentStep;
        const navigable = canNavigate(idx);

        return (
          <div key={step.id} className="flex items-center">
            <button
              onClick={() => navigable && setCurrentStep(idx)}
              disabled={!navigable}
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-300 group",
                isActive && "bg-white shadow-md shadow-blue-100 border border-blue-100",
                !isActive && navigable && "hover:bg-white/60 cursor-pointer",
                !navigable && "opacity-40 cursor-not-allowed"
              )}
            >
              <div
                className={cn(
                  "flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-300",
                  isActive && "bg-primary text-white shadow-sm",
                  isCompleted && "bg-emerald-500 text-white",
                  !isActive && !isCompleted && "bg-slate-100 text-slate-400"
                )}
              >
                {isCompleted ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <div className="hidden lg:block text-left">
                <p
                  className={cn(
                    "text-sm font-medium leading-none",
                    isActive && "text-foreground",
                    !isActive && "text-muted-foreground"
                  )}
                >
                  {step.title}
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  {step.description}
                </p>
              </div>
            </button>

            {idx < PIPELINE_STEPS.length - 1 && (
              <div
                className={cn(
                  "w-8 h-[2px] mx-1 rounded-full transition-colors duration-500",
                  idx < currentStep ? "bg-emerald-400" : "bg-slate-200"
                )}
              />
            )}
          </div>
        );
      })}
    </nav>
  );
}
