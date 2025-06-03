import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Eye, Edit, Trash2, Plus, Search, MoreHorizontal, Filter, Loader2, Calendar, Clock, Users } from "lucide-react";
import { Link } from "react-router-dom";
import apiService from "@/services/api";
import { Application, ApplicationDashboardResponse } from "@/types";
import { toast } from "sonner";

interface Interview {
  id: number;
  application_id: number;
  date: string;
  type: string;
  status: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  application?: {
    id: number;
    candidate: {
      id: number;
      full_name: string;
    };
    job: {
      id: number;
      title: string;
    };
  };
}

const ApplicationDashboard = () => {
  const [search_term, set_search_term] = useState("");
  const [status_filter, set_status_filter] = useState("all");
  const [job_filter, set_job_filter] = useState("all");
  const [applications, set_applications] = useState<Application[]>([]);
  const [loading, set_loading] = useState(true);
  const [total, set_total] = useState(0);
  const [skip, set_skip] = useState(0);
  const [limit] = useState(10);
  const [fetching_more, set_fetching_more] = useState(false);
  const [has_more, set_has_more] = useState(true);
  
  // Interview modal state
  const [selected_application, set_selected_application] = useState<Application | null>(null);
  const [interviews, set_interviews] = useState<Interview[]>([]);
  const [interviews_loading, set_interviews_loading] = useState(false);
  const [interviews_dialog_open, set_interviews_dialog_open] = useState(false);

  const fetch_applications = async (reset = false) => {
    try {
      if (reset) {
        set_loading(true);
        set_skip(0);
      } else {
        set_fetching_more(true);
      }
      const response: ApplicationDashboardResponse = await apiService.getEmployerApplications(reset ? 0 : skip, limit);
      if (reset) {
        set_applications(response.applications);
      } else {
        set_applications(prev => [
          ...prev,
          ...response.applications.filter(a => !prev.some(p => p.id === a.id))
        ]);
      }
      set_total(response.total);
      set_has_more((reset ? response.applications.length : (applications.length + response.applications.length)) < response.total);
    } catch (error) {
      console.error("Failed to fetch applications:", error);
      toast.error("Failed to load applications");
    } finally {
      set_loading(false);
      set_fetching_more(false);
    }
  };

  const fetch_interviews_for_application = async (application: Application) => {
    try {
      set_interviews_loading(true);
      set_selected_application(application);
      const interviews_data = await apiService.getInterviewsByApplication(application.id);
      set_interviews(interviews_data);
      set_interviews_dialog_open(true);
    } catch (error) {
      console.error("Failed to fetch interviews:", error);
      toast.error("Failed to load interviews for this application");
    } finally {
      set_interviews_loading(false);
    }
  };

  useEffect(() => {
    set_skip(0);
    fetch_applications(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search_term, job_filter]);

  useEffect(() => {
    if (skip === 0) return;
    fetch_applications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const get_interview_status_variant = (status: string): "default" | "secondary" | "destructive" => {
    switch (status.toLowerCase()) {
      case "done":
        return "default";
      case "canceled":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const format_date = (date_string: string) => {
    return new Date(date_string).toLocaleDateString();
  };

  const format_date_time = (date_string: string) => {
    const date = new Date(date_string);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
  };

  if (loading) {
    return (
      <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
            <span className="text-lg font-medium text-gray-700">Loading applications...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Application Management
          </h1>
          <p className="text-lg text-gray-600">
            Review and manage candidate applications ({total} total)
          </p>
        </div>
        <Button asChild className="button shadow-lg hover:shadow-xl transition-all duration-300">
          <Link to="/applications/create">
            <Plus className="mr-2 h-4 w-4" />
            Add Application
          </Link>
        </Button>
      </div>

      <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
        <CardHeader className="pb-6">
          <CardTitle className="text-2xl font-bold text-gray-800">All Applications</CardTitle>
          <CardDescription className="text-base text-gray-600">
            Overview of all candidate applications
          </CardDescription>
          <div className="flex items-center space-x-4 pt-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <Input
                placeholder="Search applications..."
                value={search_term}
                onChange={(e) => set_search_term(e.target.value)}
                className="pl-10 h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <Select value={job_filter} onValueChange={set_job_filter}>
              <SelectTrigger className="w-48 h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                <SelectValue placeholder="Filter by job" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Jobs</SelectItem>
                {unique_jobs.map((job) => (
                  <SelectItem key={job} value={job}>
                    {job}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {filtered_applications.length === 0 ? (
            <div className="text-center py-12 space-y-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto">
                <Users className="h-8 w-8 text-blue-600" />
              </div>
              <p className="text-lg text-gray-600 mb-4">No applications found</p>
              <Button asChild className="button shadow-lg hover:shadow-xl transition-all duration-300">
                <Link to="/applications/create">
                  <Plus className="mr-2 h-4 w-4" />
                  Add First Application
                </Link>
              </Button>
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
              <Table>
                <TableHeader className="bg-gradient-to-r from-gray-50 to-blue-50">
                  <TableRow>
                    <TableHead className="font-semibold text-gray-700">Candidate</TableHead>
                    <TableHead className="font-semibold text-gray-700">Job</TableHead>
                    <TableHead className="font-semibold text-gray-700">Applied Date</TableHead>
                    <TableHead className="font-semibold text-gray-700">Status</TableHead>
                    <TableHead className="font-semibold text-gray-700">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered_applications.map((application, index) => (
                    <TableRow key={application.id} className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200">
                      <TableCell>
                        <div className="space-y-1">
                          <div className="font-semibold text-gray-800">{application.candidate?.full_name}</div>
                          <div className="text-sm text-gray-600">{application.candidate?.email}</div>
                        </div>
                      </TableCell>
                      <TableCell className="font-medium text-gray-800">{application.job?.title}</TableCell>
                      <TableCell className="text-gray-600">{format_date(application.created_at)}</TableCell>
                      <TableCell>
                        <Badge variant={get_status_variant(get_status_from_application(application))} className="font-medium">
                          {get_status_from_application(application)}
                        </Badge>
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
                            <DropdownMenuItem 
                              onClick={() => fetch_interviews_for_application(application)}
                              disabled={interviews_loading}
                            >
                              <Calendar className="mr-2 h-4 w-4" />
                              Interviews
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
                  ))}
                </TableBody>
              </Table>
              {/* Show More Button */}
              {has_more && (
                <div className="flex justify-center py-4">
                  <Button
                    variant="outline"
                    onClick={() => set_skip(applications.length)}
                    disabled={fetching_more}
                  >
                    {fetching_more ? (
                      <><Loader2 className="h-4 w-4 animate-spin mr-2" />Loading...</>
                    ) : (
                      "Show More"
                    )}
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Interviews Dialog */}
      <Dialog open={interviews_dialog_open} onOpenChange={set_interviews_dialog_open}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Interviews for {selected_application?.candidate?.full_name}
            </DialogTitle>
            <DialogDescription>
              {selected_application?.job?.title} - Application #{selected_application?.id}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {interviews_loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span className="ml-2">Loading interviews...</span>
              </div>
            ) : interviews.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">No interviews scheduled for this application</p>
                <Button asChild>
                  <Link to={`/interviews/create?application_id=${selected_application?.id}`}>
                    <Plus className="mr-2 h-4 w-4" />
                    Schedule Interview
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Scheduled Interviews ({interviews.length})</h4>
                  <Button asChild size="sm">
                    <Link to={`/interviews/create?application_id=${selected_application?.id}`}>
                      <Plus className="mr-2 h-4 w-4" />
                      Add Interview
                    </Link>
                  </Button>
                </div>
                
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date & Time</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Notes</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {interviews.map((interview) => {
                      const dateTime = format_date_time(interview.date);
                      return (
                        <TableRow key={interview.id}>
                          <TableCell>
                            <div>
                              <div className="font-medium">{dateTime.date}</div>
                              <div className="text-sm text-muted-foreground">{dateTime.time}</div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{interview.type}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={get_interview_status_variant(interview.status)}>
                              {interview.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="max-w-[200px] truncate text-sm text-muted-foreground">
                              {interview.notes || "No notes"}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Button asChild variant="ghost" size="sm">
                                <Link to={`/interviews/${interview.id}/edit`}>
                                  <Edit className="h-4 w-4" />
                                </Link>
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ApplicationDashboard;
