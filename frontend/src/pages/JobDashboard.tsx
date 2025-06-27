import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Eye, Trash2, Plus, Search, Settings, Loader2, RefreshCw, Copy, ExternalLink, ChevronDown } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "@/components/ui/sonner";
import apiService from "@/services/api";
import { JobStatus } from "@/types";

const JobDashboard = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [jobToClose, setJobToClose] = useState(null);
  const [isClosingJob, setIsClosingJob] = useState(false);
  const [jobToDelete, setJobToDelete] = useState(null);
  const [isDeletingJob, setIsDeletingJob] = useState(false);

  // Fetch jobs on component mount
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Try to get jobs by employer first (if we have employer_id from token)
        const token = localStorage.getItem('token');
        if (token) {
          // Decode token to get employer_id (simple decode, in production use proper JWT library)
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
         
            // Fallback to all jobs if no employer_id
            const response = await apiService.getJobsByEmployer(payload.employer_id);
            setJobs(response || []);
            
          } catch (tokenError) {
            // If token parsing fails, get all jobs
            const response = await apiService.getAllJobs();
            setJobs(response || []);
          }
        } else {
          setJobs([]);
        }
      } catch (error) {
        console.error('Failed to fetch jobs:', error);
        setError(error.message || 'Failed to fetch jobs');
        toast.error("Failed to fetch jobs", {
          description: error.message || "An unexpected error occurred.",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchJobs();
  }, []);

  const filteredJobs = jobs.filter(job => {
    // Handle both job_data.title and direct title field
    const title = job.job_data?.title || job.title || '';
    return title.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "published":
        return "default";
      case "draft":
        return "secondary";
      case "closed":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Invalid Date';
    }
  };

  const getJobTitle = (job) => {
    return job.job_data?.title || job.title || 'Untitled Job';
  };

  const getApplicationCount = (job) => {
    return job.applications?.length || 0;
  };

  const handleStatusUpdate = async (job_id, new_status) => {
    // If trying to close a job, show confirmation dialog
    if (new_status === JobStatus.CLOSED) {
      const job = jobs.find(j => j.id === job_id);
      setJobToClose(job);
      return;
    }

    try {
      await apiService.updateJobStatus(job_id, new_status);
      
      // Update the job in the local state
      setJobs(prev_jobs => 
        prev_jobs.map(job => 
          job.id === job_id 
            ? { ...job, status: new_status }
            : job
        )
      );
      
      toast.success("Job status updated successfully", {
        description: `Status changed to ${new_status.charAt(0).toUpperCase() + new_status.slice(1)}`,
      });
    } catch (error) {
      console.error('Failed to update job status:', error);
      toast.error("Failed to update job status", {
        description: error.message || "An unexpected error occurred.",
      });
    }
  };

  const confirmCloseJob = async () => {
    if (!jobToClose) return;

    setIsClosingJob(true);
    try {
      await apiService.updateJobStatus(jobToClose.id, JobStatus.CLOSED);
      
      // Remove the job from the local state since closed jobs don't appear in the list
      setJobs(prev_jobs => prev_jobs.filter(job => job.id !== jobToClose.id));
      
      toast.success("Job closed successfully", {
        description: "The job has been closed and will no longer appear in the dashboard.",
      });
    } catch (error) {
      console.error('Failed to close job:', error);
      toast.error("Failed to close job", {
        description: error.message || "An unexpected error occurred.",
      });
    } finally {
      setIsClosingJob(false);
      setJobToClose(null);
    }
  };

  const copyJobUrl = async (job_id) => {
    const url = `${window.location.origin}/apply/${job_id}`;
    
    try {
      // Try modern clipboard API first
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(url);
        toast.success("URL Copied!", {
          description: "The application URL has been copied to your clipboard.",
        });
      } else {
        // Fallback for older browsers or non-HTTPS
        const text_area = document.createElement('textarea');
        text_area.value = url;
        text_area.style.position = 'fixed';
        text_area.style.opacity = '0';
        document.body.appendChild(text_area);
        text_area.select();
        document.execCommand('copy');
        document.body.removeChild(text_area);
        
        toast.success("URL Copied!", {
          description: "The application URL has been copied to your clipboard.",
        });
      }
    } catch (error) {
      console.error('Failed to copy URL:', error);
      // Show the URL in a toast so user can copy manually
      toast.error("Failed to copy URL", {
        description: `Please copy manually: ${url}`,
        duration: 10000, // Show longer so user can copy
      });
    }
  };

  const handleDeleteJob = (job) => {
    setJobToDelete(job);
  };

  const confirmDeleteJob = async () => {
    if (!jobToDelete) return;

    setIsDeletingJob(true);
    try {
      await apiService.deleteJob(jobToDelete.id);
      
      setJobs(prev_jobs => prev_jobs.filter(job => job.id !== jobToDelete.id));
      
      toast.success("Job deleted successfully", {
        description: `"${getJobTitle(jobToDelete)}" has been permanently deleted.`,
      });
    } catch (error) {
      console.error('Failed to delete job:', error);
      toast.error("Failed to delete job", {
        description: error.message || "An unexpected error occurred.",
      });
    } finally {
      setIsDeletingJob(false);
      setJobToDelete(null);
    }
  };

  const getStatusOptions = (current_status) => {
    return Object.values(JobStatus).filter(status => status !== current_status);
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
            <span className="text-lg font-medium text-gray-700">Loading jobs...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="flex items-center justify-center h-64">
          <Card className="w-full max-w-md shadow-xl border-0">
            <CardContent className="text-center p-8 space-y-4">
              <p className="text-red-600 font-semibold text-lg mb-4">Error loading jobs: {error}</p>
              <Button onClick={() => window.location.reload()} className="button shadow-lg hover:shadow-xl transition-all duration-300">
              Retry
            </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Job Management
          </h1>
          <p className="text-lg text-gray-600">
            Manage your job postings and track applications
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" asChild className="shadow-md hover:shadow-lg transition-all duration-300">
            <Link to="/form-keys">
              <Settings className="mr-2 h-4 w-4" />
              Configure application form data
            </Link>
          </Button>
          <Button variant="outline" asChild className="shadow-lg hover:shadow-xl transition-all duration-300">
            <Link to="/jobs/create">
              <Plus className="mr-2 h-4 w-4" />
              Create Job
            </Link>
          </Button>
        </div>
      </div>

      <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
        <CardHeader className="pb-6">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl font-bold text-gray-800">All Jobs ({jobs.length})</CardTitle>
              <CardDescription className="text-base text-gray-600 mt-1">
            Overview of all your job postings
          </CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2 pt-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <Input
                placeholder="Search jobs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {jobs.length === 0 ? (
            <div className="text-center py-12 space-y-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto">
                <Plus className="h-8 w-8 text-blue-600" />
              </div>
              <p className="text-lg text-gray-600 mb-4">No jobs found</p>
              <Button asChild className="button shadow-lg hover:shadow-xl transition-all duration-300">
                <Link to="/jobs/create">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Job
                </Link>
              </Button>
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
            <Table>
                <TableHeader className="bg-gradient-to-r from-gray-50 to-blue-50">
                <TableRow>
                    <TableHead className="font-semibold text-gray-700">Job Title</TableHead>
                    <TableHead className="font-semibold text-gray-700">Created Date</TableHead>
                    <TableHead className="font-semibold text-gray-700">Status (Click to change)</TableHead>
                    <TableHead className="font-semibold text-gray-700">Applications</TableHead>
                    <TableHead className="font-semibold text-gray-700">Recruited To</TableHead>
                    <TableHead className="font-semibold text-gray-700">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                  {filteredJobs.map((job, index) => (
                    <TableRow
                      key={job.id}
                      className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200 cursor-pointer"
                      onClick={e => {
                        // Prevent navigation if Delete button is clicked
                        if ((e.target as HTMLElement).closest('.job-delete-btn')) return;
                        window.location.href = `/jobs/${job.id}`;
                      }}
                    >
                      <TableCell className="font-semibold text-gray-800">{getJobTitle(job)}</TableCell>
                      <TableCell className="text-gray-600">{formatDate(job.created_at)}</TableCell>
                    <TableCell>
                      <div onClick={(e) => e.stopPropagation()} className="flex items-center gap-2">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="outline" className="flex items-center gap-2 capitalize h-8">
                              <Badge variant={getStatusColor(job.status) as any} className="font-medium">
                                {job.status ? job.status.charAt(0).toUpperCase() + job.status.slice(1) : 'Unknown'}
                              </Badge>
                              <ChevronDown className="h-4 w-4 text-muted-foreground" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            {getStatusOptions(job.status).map(status => (
                              <DropdownMenuItem 
                                key={status} 
                                onSelect={() => handleStatusUpdate(job.id, status)}
                                className="capitalize"
                              >
                                {status.charAt(0).toUpperCase() + status.slice(1)}
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuContent>
                        </DropdownMenu>
                        {job.status === JobStatus.PUBLISHED && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => copyJobUrl(job.id)}
                            className="h-7 px-2 text-xs"
                          >
                            <Copy className="h-3 w-3 mr-1" />
                            Copy URL
                          </Button>
                        )}
                      </div>
                    </TableCell>
                      <TableCell>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {job.application_count}
                        </span>
                      </TableCell>
                      <TableCell className="text-gray-600">{job.recruited_to_name || 'N/A'}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        <Button variant="destructive" size="sm" onClick={() => handleDeleteJob(job)} className="job-delete-btn">
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialog for Closing Jobs */}
      <AlertDialog open={!!jobToClose} onOpenChange={() => setJobToClose(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Close Job?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to close "{jobToClose ? getJobTitle(jobToClose) : 'this job'}"? 
              Once closed, it will no longer appear in your dashboard and candidates won't be able to apply.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isClosingJob}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmCloseJob}
              disabled={isClosingJob}
              className="bg-red-600 hover:bg-red-700"
            >
              {isClosingJob ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Closing...
                </>
              ) : (
                'Close Job'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Confirmation Dialog for Deleting Jobs */}
      <AlertDialog open={!!jobToDelete} onOpenChange={() => setJobToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Job?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to permanently delete "{jobToDelete ? getJobTitle(jobToDelete) : 'this job'}"? 
              All associated applications and data will be lost.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeletingJob}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteJob}
              disabled={isDeletingJob}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeletingJob ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete Job'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default JobDashboard;
