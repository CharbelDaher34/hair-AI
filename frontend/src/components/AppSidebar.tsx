import {
  Building2,
  Users,
  FileText,
  Calendar,
  Settings,
  Home,
  BrainCircuit,
  LogOut,
  User,
  UserCheck
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "@/components/ui/sonner";

const menuItems = [
  {
    title: "Home",
    url: "/",
    icon: Home,
  },
  {
    title: "Jobs",
    url: "/jobs",
    icon: FileText,
  },
  {
    title: "Applications",
    url: "/applications", 
    icon: Users,
  },
  {
    title: "Candidates",
    url: "/candidates",
    icon: UserCheck,
  },
  {
    title: "Interviews",
    url: "/interviews",
    icon: Calendar,
  },
  // {
  //   title: "Form Keys",
  //   url: "/form-keys",
  //   icon: Settings,
  // },
  {
    title: "AI Assistant",
    url: "/chatbot",
    icon: BrainCircuit,
  },
  {
    title: "Profile",
    url: "/profile",
    icon: Building2,
  },
];

export function AppSidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    toast.success("Logged out successfully");
    navigate("/login");
  };

  return (
    <Sidebar className="border-r-0 shadow-2xl bg-gradient-to-b from-slate-50 via-white to-blue-50">
      <SidebarHeader className="border-b border-gray-200/60 p-6 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="flex items-center gap-3">
          <div className="relative">
            <img 
              src="/hair_logo.png" 
              alt="Eurisko Logo" 
              className="h-10 w-10 rounded-full object-cover ring-2 ring-white/30 shadow-lg"
            />
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white shadow-sm"></div>
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-xl text-white drop-shadow-sm">AI HR</span>
            <span className="text-xs text-blue-100 font-medium">Management Suite</span>
          </div>
        </div>
        <SidebarTrigger className="ml-auto text-white hover:bg-white/20 transition-colors duration-200 data-[state=open]:rotate-180" />
      </SidebarHeader>
      
      <SidebarContent className="py-6">
        <SidebarGroup>
          <SidebarGroupLabel className="text-gray-500 font-semibold text-sm uppercase tracking-wider px-6 mb-4">
            Navigation
          </SidebarGroupLabel>
          <SidebarGroupContent className="px-3">
            <SidebarMenu className="space-y-2">
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton 
                    asChild
                    isActive={location.pathname === item.url}
                    className={`
                      relative group h-12 rounded-xl transition-all duration-300 ease-in-out
                      ${location.pathname === item.url 
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/25 scale-105' 
                        : 'hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 hover:text-blue-700 hover:scale-102 hover:shadow-md'
                      }
                    `}
                  >
                    <Link to={item.url} className="flex items-center gap-4 px-4 w-full">
                      <div className={`
                        p-2 rounded-lg transition-all duration-300
                        ${location.pathname === item.url 
                          ? 'bg-white/20' 
                          : 'bg-gray-100 group-hover:bg-blue-100 group-hover:text-blue-600'
                        }
                      `}>
                        <item.icon className="h-5 w-5" />
                      </div>
                      <span className="font-medium text-sm">{item.title}</span>
                      {location.pathname === item.url && (
                        <div className="absolute right-2 w-2 h-2 bg-white rounded-full shadow-sm"></div>
                      )}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      
      <SidebarFooter className="border-t border-gray-200/60 p-4 bg-gradient-to-r from-gray-50 to-blue-50">
        <Button 
          variant="ghost" 
          className="w-full justify-start gap-3 text-gray-600 hover:text-red-600 hover:bg-red-50 transition-all duration-300 h-12 rounded-xl group"
          onClick={handleLogout}
        >
          <div className="p-2 bg-gray-100 group-hover:bg-red-100 rounded-lg transition-all duration-300">
            <LogOut className="h-4 w-4" />
          </div>
          <span className="font-medium">Logout</span>
        </Button>
        <div className="text-xs text-gray-400 text-center mt-4 font-medium">
          <div className="flex items-center justify-center gap-1">
            <span>© 2025 HR Platform</span>
            <div className="w-1 h-1 bg-gray-300 rounded-full"></div>
            <span className="text-blue-500">v2.0</span>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
