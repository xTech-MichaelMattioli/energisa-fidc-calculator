
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { MainContent } from "@/components/MainContent";
import { UserHeader } from "@/components/auth/UserHeader";

const Index = () => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex flex-col w-full bg-gradient-to-br from-slate-50 to-blue-50">
        <UserHeader />
        <div className="flex flex-1">
          <AppSidebar />
          <MainContent />
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Index;
