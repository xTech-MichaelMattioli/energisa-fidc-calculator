import { AnimatePresence, motion } from "framer-motion";
import { useApp } from "@/context/AppContext";
import { AppLayout } from "@/components/layout/AppLayout";
import { UploadPage } from "@/pages/UploadPage";
import { MappingPage } from "@/pages/MappingPage";
import { IndicesPage } from "@/pages/IndicesPage";
import { ProcessingPage } from "@/pages/ProcessingPage";
import { ResultsPage } from "@/pages/ResultsPage";
import { Toaster } from "sonner";

const pages = [UploadPage, MappingPage, IndicesPage, ProcessingPage, ResultsPage];

function App() {
  const { currentStep } = useApp();
  const Page = pages[currentStep] ?? UploadPage;

  return (
    <>
      <AppLayout>
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -30 }}
            transition={{ duration: 0.25 }}
          >
            <Page />
          </motion.div>
        </AnimatePresence>
      </AppLayout>
      <Toaster position="bottom-right" richColors />
    </>
  );
}

export default App;
