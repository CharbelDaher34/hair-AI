import React from 'react';
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import FloatingBackground from "@/components/FloatingBackground";
import MainContentHeader from "@/components/MainContentHeader";

// Import page components directly
import Signup from "./pages/SignUp";
import JobDashboard from "./pages/JobDashboard";
import FormKeysManagement from "./pages/FormKeysManagement";
import CreateEditJob from "./pages/CreateEditJob";
import JobDetails from "./pages/JobDetails";
import ApplicationDashboard from "./pages/ApplicationDashboard";
import ViewEditApplication from "./pages/ViewEditApplication";
import AddApplication from "./pages/AddApplication";
import Candidates from "./pages/Candidates";
import Index from "./pages/Index";
import JobAnalytics from "./pages/JobAnalytics";
import InterviewList from "./pages/InterviewList";
import AddEditInterview from "./pages/AddEditInterview";
import ChatBot from "./pages/ChatBot";
import MatchedCandidates from "./pages/MatchedCandidates";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import JobApplicationForm from "./pages/JobApplicationForm";

const queryClient = new QueryClient();

// Layout for authenticated routes
const AuthenticatedLayout = () => {
  const token = localStorage.getItem('token');

  if (!token) {
    // Redirect to login if no token
    return <Navigate to="/login" replace />;
  }

  return (
    <SidebarProvider defaultOpen={true}>
      <div className="min-h-screen flex w-full relative">
        <FloatingBackground />
        <AppSidebar />
        <main className="flex-1 relative z-10">
          <MainContentHeader />
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
        <div className="relative min-h-screen">
          <FloatingBackground />
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<div className="relative z-10"><Login /></div>} />
            <Route path="/signup" element={<div className="relative z-10"><Signup /></div>} />
            <Route path="/apply/:job_id" element={<div className="relative z-10"><JobApplicationForm /></div>} />
          
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
            <Route path="/candidates" element={<Candidates />} />
            <Route path="/interviews" element={<InterviewList />} />
            <Route path="/interviews/create" element={<AddEditInterview />} />
            <Route path="/interviews/:id/edit" element={<AddEditInterview />} />
            <Route path="/chatbot" element={<ChatBot />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
        </div>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
