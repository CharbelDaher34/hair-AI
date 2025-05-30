import React, { Suspense, lazy } from 'react';
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";

// Lazy load page components
const Index = lazy(() => import("./pages/Index"));
const Signup = lazy(() => import("./pages/SignUp"));
const JobDashboard = lazy(() => import("./pages/JobDashboard"));
const FormKeysManagement = lazy(() => import("./pages/FormKeysManagement"));
const CreateEditJob = lazy(() => import("./pages/CreateEditJob"));
const JobDetails = lazy(() => import("./pages/JobDetails"));
const ApplicationDashboard = lazy(() => import("./pages/ApplicationDashboard"));
const ViewEditApplication = lazy(() => import("./pages/ViewEditApplication"));
const AddApplication = lazy(() => import("./pages/AddApplication"));
const CompanyAnalytics = lazy(() => import("./pages/CompanyAnalytics"));
const JobAnalytics = lazy(() => import("./pages/JobAnalytics"));
const InterviewList = lazy(() => import("./pages/InterviewList"));
const AddEditInterview = lazy(() => import("./pages/AddEditInterview"));
const ChatBot = lazy(() => import("./pages/ChatBot"));
const MatchedCandidates = lazy(() => import("./pages/MatchedCandidates"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Login = lazy(() => import("./pages/Login"));
const Profile = lazy(() => import("./pages/Profile"));
const JobApplicationForm = lazy(() => import("./pages/JobApplicationForm"));

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
        <Suspense fallback={<div>Loading...</div>}>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/apply/:job_id" element={<JobApplicationForm />} />
            
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
        </Suspense>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
