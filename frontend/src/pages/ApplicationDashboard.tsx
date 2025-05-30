import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Eye, Edit, Trash2, Plus, Search, MoreHorizontal, Filter, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import apiService from "@/services/api";
import { Application, ApplicationDashboardResponse } from "@/types";
import { toast } from "sonner";

const ApplicationDashboard = () => {
  const [search_term, set_search_term] = useState("");
  const [status_filter, set_status_filter] = useState("all");
  const [job_filter, set_job_filter] = useState("all");
  const [applications, set_applications] = useState<Application[]>([]);
  const [loading, set_loading] = useState(true);
  const [total, set_total] = useState(0);
  const [skip, set_skip] = useState(0);
  const [limit] = useState(10);

  const fetch_applications = async () => {
    try {
      set_loading(true);
      const response: ApplicationDashboardResponse = await apiService.getEmployerApplications(skip, limit);
      set_applications(response.applications);
      set_total(response.total);
    } catch (error) {
      console.error("Failed to fetch applications:", error);
      toast.error("Failed to load applications");
    } finally {
      set_loading(false);
    }
  };

  useEffect(() => {
    fetch_applications();
  }, [skip]);

  // Get unique job titles for filter
  const unique_jobs = Array.from(new Set(applications.map(app => app.job?.title).filter(Boolean)));

  const filtered_applications = applications.filter(app => {
    const matches_search = app.candidate?.full_name?.toLowerCase().includes(search_term.toLowerCase()) ||
                          app.job?.title?.toLowerCase().includes(search_term.toLowerCase()) ||
                          app.candidate?.email?.toLowerCase().includes(search_term.toLowerCase());
    const matches_job = job_filter === "all" || app.job?.title === job_filter;
    
    return matches_search && matches_job;
  });

  const get_status_from_application = (application: Application): string => {
    // Since we don't have a status field, we'll derive it from other data
    if (application.matches && application.matches.length > 0) {
      const latest_match = application.matches[application.matches.length - 1];
      return latest_match.status || "review";
    }
    return "review";
  };

  const get_status_color = (status: string) => {
    switch (status) {
      case "review":
        return "default";
      case "interview":
        return "secondary";
      case "hired":
        return "default";
      case "rejected":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const get_status_variant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case "hired":
        return "default";
      case "interview":
        return "secondary";
      case "rejected":
        return "destructive";
      default:
        return "outline";
    }
  };

  const format_date = (date_string: string) => {
    return new Date(date_string).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Application Management</h1>
          <p className="text-muted-foreground">
            Review and manage candidate applications ({total} total)
          </p>
        </div>
        <Button asChild>
          <Link to="/applications/create">
            <Plus className="mr-2 h-4 w-4" />
            Add Application
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Applications</CardTitle>
          <CardDescription>
            Overview of all candidate applications
          </CardDescription>
          <div className="flex items-center space-x-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search applications..."
                value={search_term}
                onChange={(e) => set_search_term(e.target.value)}
                className="pl-8"
              />
            </div>
            <Select value={job_filter} onValueChange={set_job_filter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by job" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Jobs</SelectItem>
                {unique_jobs.map((job_title) => (
                  <SelectItem key={job_title} value={job_title}>
                    {job_title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button 
              variant="outline" 
              onClick={fetch_applications}
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Refresh"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Candidate Name</TableHead>
                <TableHead>Job Title</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Submission Date</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered_applications.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    No applications found
                  </TableCell>
                </TableRow>
              ) : (
                filtered_applications.map((application) => {
                  const status = get_status_from_application(application);
                  return (
                    <TableRow key={application.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{application.candidate?.full_name || "Unknown"}</div>
                          <div className="text-sm text-muted-foreground">{application.candidate?.email || "No email"}</div>
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        {application.job?.title || "Unknown Job"}
                      </TableCell>
                      <TableCell>
                        <Badge variant={get_status_variant(status)}>
                          {status.charAt(0).toUpperCase() + status.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {application.created_at ? format_date(application.created_at) : "Unknown"}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="h-8 w-8 p-0">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem asChild>
                              <Link to={`/applications/${application.id}`}>
                                <Eye className="mr-2 h-4 w-4" />
                                View
                              </Link>
                            </DropdownMenuItem>
                            <DropdownMenuItem asChild>
                              <Link to={`/applications/${application.id}/edit`}>
                                <Edit className="mr-2 h-4 w-4" />
                                Edit
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
                  );
                })
              )}
            </TableBody>
          </Table>
          
          {/* Pagination */}
          {total > limit && (
            <div className="flex items-center justify-between space-x-2 py-4">
              <div className="text-sm text-muted-foreground">
                Showing {skip + 1} to {Math.min(skip + limit, total)} of {total} applications
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => set_skip(Math.max(0, skip - limit))}
                  disabled={skip === 0}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => set_skip(skip + limit)}
                  disabled={skip + limit >= total}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ApplicationDashboard;
