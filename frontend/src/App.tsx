import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import Index from "./pages/Index";
import Signup from "./pages/SignUp";
import JobDashboard from "./pages/JobDashboard";
import FormKeysManagement from "./pages/FormKeysManagement";
import CreateEditJob from "./pages/CreateEditJob";
import JobDetails from "./pages/JobDetails";
import ApplicationDashboard from "./pages/ApplicationDashboard";
import ViewEditApplication from "./pages/ViewEditApplication";
import AddApplication from "./pages/AddApplication";
import CompanyAnalytics from "./pages/CompanyAnalytics";
import JobAnalytics from "./pages/JobAnalytics";
import InterviewList from "./pages/InterviewList";
import AddEditInterview from "./pages/AddEditInterview";
import ChatBot from "./pages/ChatBot";
import MatchedCandidates from "./pages/MatchedCandidates";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import Profile from "./pages/Profile";

const queryClient = new QueryClient();

// Layout for authenticated routes
const AuthenticatedLayout = () => {
  const token = localStorage.getItem('token');

  if (!token) {
    // Redirect to login if no token
    return <Navigate to="/login" replace />;
  }

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <main className="flex-1">
          {/* Outlet renders the matched child route element (e.g., Index, JobDashboard) */}
          <Outlet /> 
        </main>
      </div>
    </SidebarProvider>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <SonnerToaster />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          
          {/* Authenticated Routes */}
          <Route element={<AuthenticatedLayout />}>
            <Route path="/profile" element={<Profile />} />
            <Route path="/" element={<Index />} />
            <Route path="/jobs" element={<JobDashboard />} />
            <Route path="/jobs/create" element={<CreateEditJob />} />
            <Route path="/jobs/:id/edit" element={<CreateEditJob />} />
            <Route path="/jobs/:id" element={<JobDetails />} />
            <Route path="/jobs/:id/analytics" element={<JobAnalytics />} />
            <Route path="/jobs/:id/matches" element={<MatchedCandidates />} />
            <Route path="/form-keys" element={<FormKeysManagement />} />
            <Route path="/applications" element={<ApplicationDashboard />} />
            <Route path="/applications/create" element={<AddApplication />} />
            <Route path="/applications/:id" element={<ViewEditApplication />} />
            <Route path="/applications/:id/edit" element={<ViewEditApplication />} />
            <Route path="/analytics" element={<CompanyAnalytics />} />
            <Route path="/interviews" element={<InterviewList />} />
            <Route path="/interviews/create" element={<AddEditInterview />} />
            <Route path="/interviews/:id/edit" element={<AddEditInterview />} />
            <Route path="/chatbot" element={<ChatBot />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
