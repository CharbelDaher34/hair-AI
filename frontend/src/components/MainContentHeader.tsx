import React from 'react';
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Menu } from "lucide-react";

const MainContentHeader: React.FC = () => {
  return (
    <div className="sticky top-0 z-20 bg-white/80 backdrop-blur-sm border-b border-gray-200/60 p-4">
      <div className="flex items-center gap-4">
        <SidebarTrigger className="hover:bg-blue-50 hover:text-blue-600 transition-colors duration-200 shadow-sm p-2 rounded-md">
          <Menu className="h-5 w-5" />
        </SidebarTrigger>
        <div className="flex-1" />
      </div>
    </div>
  );
};

export default MainContentHeader; 