import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Eye, Edit, BarChart3, Trash2, Plus, Search, MoreHorizontal, Settings, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "@/components/ui/sonner";
import apiService from "@/services/api";

const JobDashboard = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

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
      case "open":
      case "active":
        return "default";
      case "draft":
        return "secondary";
      case "closed":
      case "inactive":
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
              Manage Form Keys
            </Link>
          </Button>
          <Button asChild className="button shadow-lg hover:shadow-xl transition-all duration-300">
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
                    <TableHead className="font-semibold text-gray-700">Status</TableHead>
                    <TableHead className="font-semibold text-gray-700">Applications</TableHead>
                    <TableHead className="font-semibold text-gray-700">Recruited To</TableHead>
                    <TableHead className="font-semibold text-gray-700">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                  {filteredJobs.map((job, index) => (
                    <TableRow key={job.id} className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200">
                      <TableCell className="font-semibold text-gray-800">{getJobTitle(job)}</TableCell>
                      <TableCell className="text-gray-600">{formatDate(job.created_at)}</TableCell>
                    <TableCell>
                        <Badge variant={getStatusColor(job.status) as any} className="font-medium">
                        {job.status ? job.status.charAt(0).toUpperCase() + job.status.slice(1) : 'Unknown'}
                      </Badge>
                    </TableCell>
                      <TableCell>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {job.application_count}
                        </span>
                      </TableCell>
                      <TableCell className="text-gray-600">{job.recruited_to_name || 'N/A'}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link to={`/jobs/${job.id}`}>
                              <Eye className="mr-2 h-4 w-4" />
                              View
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link to={`/jobs/${job.id}/edit`}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link to={`/jobs/${job.id}/analytics`}>
                              <BarChart3 className="mr-2 h-4 w-4" />
                              Analytics
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-destructive">
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default JobDashboard;
