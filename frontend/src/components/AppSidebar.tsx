import {
  Building2,
  Users,
  FileText,
  Calendar,
  Settings,
  Home,
  BrainCircuit,
  LogOut,
  User
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
    icon: User,
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
    <Sidebar>
      <SidebarHeader className="border-b p-6">
        <div className="flex items-center gap-2">
          <img 
            src="/hair_logo.png" 
            alt="Eurisko Logo" 
            className="h-8 w-8 rounded-full object-cover"
          />
          <span className="font-bold text-lg">AI HR</span>
        </div>
        <SidebarTrigger className="ml-auto" />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton 
                    asChild
                    isActive={location.pathname === item.url}
                  >
                    <Link to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="border-t p-4">
        <Button 
          variant="ghost" 
          className="w-full justify-start gap-2 text-muted-foreground hover:text-foreground"
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </Button>
        <div className="text-xs text-muted-foreground text-center mt-2">
          © 2024 HR Platform
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
