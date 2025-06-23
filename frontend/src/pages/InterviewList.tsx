import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Calendar, Plus, Search, MoreHorizontal, Edit, Trash2, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import apiService from "@/services/api";

interface Interview {
  id: number;
  application_id: number;
  date: string;
  type: string;
  status: string;
  notes?: string;
  interviewer_id?: number;
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
  interviewer?: {
    id: number;
    full_name: string;
    email: string;
  };
}

const InterviewList = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInterviews = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getAllInterviews();
      setInterviews(data);
    } catch (err) {
      setError("Failed to fetch interviews");
      console.error("Error fetching interviews:", err);
      toast({
        title: "Error",
        description: "Failed to fetch interviews",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterviews();
  }, []);

  const handleDeleteInterview = async (interviewId: number) => {
    if (!confirm("Are you sure you want to delete this interview?")) {
      return;
    }

    try {
      await apiService.deleteInterview(interviewId);
      toast({
        title: "Success",
        description: "Interview deleted successfully",
      });
      // Refresh the list
      fetchInterviews();
    } catch (err) {
      console.error("Error deleting interview:", err);
      toast({
        title: "Error",
        description: "Failed to delete interview",
        variant: "destructive",
      });
    }
  };

  const handleStatusUpdate = async (interviewId: number, newStatus: string) => {
    try {
      await apiService.updateInterviewStatus(interviewId, newStatus);
      toast({
        title: "Success",
        description: "Interview status updated successfully",
      });
      // Refresh the list
      fetchInterviews();
    } catch (err) {
      console.error("Error updating interview status:", err);
      toast({
        title: "Error",
        description: "Failed to update interview status",
        variant: "destructive",
      });
    }
  };

  const filteredInterviews = interviews.filter(interview => {
    const candidateName = interview.application?.candidate?.full_name || "";
    const jobTitle = interview.application?.job?.title || "";
    
    const matchesSearch = candidateName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         jobTitle.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || interview.status.toLowerCase() === statusFilter;
    const matchesType = typeFilter === "all" || interview.type.toLowerCase() === typeFilter;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" => {
    switch (status.toLowerCase()) {
      case "done":
        return "default";
      case "canceled":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
  };

  const getUniqueTypes = () => {
    const types = interviews.map(interview => interview.type).filter(Boolean);
    return [...new Set(types)];
  };

  const getStatistics = () => {
    const thisWeek = interviews.filter(interview => {
      const interviewDate = new Date(interview.date);
      const now = new Date();
      const weekStart = new Date(now.setDate(now.getDate() - now.getDay()));
      return interviewDate >= weekStart;
    }).length;

    const completed = interviews.filter(i => i.status === "done").length;
    const successRate = interviews.length > 0 ? Math.round((completed / interviews.length) * 100) : 0;
    
    const pending = interviews.filter(i => i.status === "scheduled").length;

    return { thisWeek, successRate, pending };
  };

  const stats = getStatistics();

  // Define stat items with explicit typing for clarity
  interface StatItem {
    title: string;
    value: string | number;
    note: string;
    icon: React.FC<React.SVGProps<SVGSVGElement>>; // Type for Lucide icons
  }


  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <span className="text-lg font-medium text-gray-700">Loading interviews...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <Card className="w-full max-w-md shadow-xl border-0">
          <CardContent className="text-center p-8 space-y-4">
            <p className="text-red-600 font-semibold text-lg mb-4">{error}</p>
            <Button onClick={fetchInterviews} className="button shadow-lg hover:shadow-xl transition-all duration-300">
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Interview Tracking
          </h1>
          <p className="text-lg text-gray-600">
            Manage and track all candidate interviews
          </p>
        </div>
        <Button asChild className="button shadow-lg hover:shadow-xl transition-all duration-300">
          <Link to="/interviews/create">
            <Plus className="mr-2 h-4 w-4" />
            Schedule Interview
          </Link>
        </Button>
      </div>

      <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
        <CardHeader className="pb-6">
          <CardTitle className="flex items-center gap-3 text-2xl font-bold text-gray-800">
            <Calendar className="h-6 w-6 text-blue-600" />
            All Interviews ({interviews.length})
          </CardTitle>
          <CardDescription className="text-base text-gray-600 mt-1">
            Overview of all scheduled and completed interviews
          </CardDescription>
          <div className="flex items-center space-x-4 pt-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <Input
                placeholder="Search interviews..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            {/* <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48 h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {getUniqueTypes().map((type) => (
                  <SelectItem key={type} value={type.toLowerCase()}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select> */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48 h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="done">Done</SelectItem>
                <SelectItem value="canceled">Canceled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {filteredInterviews.length === 0 ? (
            <div className="text-center py-12 space-y-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto">
                <Calendar className="h-8 w-8 text-blue-600" />
              </div>
              <p className="text-lg text-gray-600 mb-4">
                {interviews.length === 0 ? "No interviews scheduled yet." : "No interviews match your filters."}
              </p>
              {interviews.length === 0 && (
                <Button asChild className="button shadow-lg hover:shadow-xl transition-all duration-300">
                  <Link to="/interviews/create">
                    <Plus className="mr-2 h-4 w-4" />
                    Schedule Your First Interview
                  </Link>
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
            <Table>
                <TableHeader className="bg-gradient-to-r from-gray-50 to-blue-50">
                <TableRow>
                    <TableHead className="font-semibold text-gray-700">Candidate</TableHead>
                    <TableHead className="font-semibold text-gray-700">Job</TableHead>
                    <TableHead className="font-semibold text-gray-700">Date & Time</TableHead>
                    <TableHead className="font-semibold text-gray-700">Type</TableHead>
                    <TableHead className="font-semibold text-gray-700">Status</TableHead>
                    <TableHead className="font-semibold text-gray-700">Interviewer</TableHead>
                    <TableHead className="font-semibold text-gray-700">Notes</TableHead>
                    <TableHead className="font-semibold text-gray-700">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredInterviews.map((interview) => {
                  const dateTime = formatDateTime(interview.date);
                  return (
                      <TableRow key={interview.id} className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200">
                      <TableCell>
                          <div className="font-semibold text-gray-800">
                          {interview.application?.candidate?.full_name || "Unknown"}
                        </div>
                      </TableCell>
                        <TableCell className="font-medium text-gray-800">
                        {interview.application?.job?.title || "Unknown"}
                      </TableCell>
                      <TableCell>
                          <div className="space-y-1">
                            <div className="font-semibold text-gray-800">{dateTime.date}</div>
                            <div className="text-sm text-gray-600">{dateTime.time}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                          <Badge variant="outline" className="font-medium bg-blue-50 text-blue-700 border-blue-200">
                            {interview.type}
                          </Badge>
                      </TableCell>
                      <TableCell>
                        <Select
                          value={interview.status}
                          onValueChange={(newStatus) => handleStatusUpdate(interview.id, newStatus)}
                        >
                          <SelectTrigger className="w-32 h-8 text-xs">
                            <SelectValue>
                              <Badge variant={getStatusVariant(interview.status)} className="font-medium text-xs px-2 py-1">
                                {interview.status}
                              </Badge>
                            </SelectValue>
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="scheduled">
                              <Badge variant="secondary" className="font-medium text-xs">
                                Scheduled
                              </Badge>
                            </SelectItem>
                            <SelectItem value="done">
                              <Badge variant="default" className="font-medium text-xs">
                                Done
                              </Badge>
                            </SelectItem>
                            <SelectItem value="canceled">
                              <Badge variant="destructive" className="font-medium text-xs">
                                Canceled
                              </Badge>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                          <div className="font-medium text-gray-800">
                            {interview.interviewer?.full_name || "-"}
                          </div>
                          {interview.interviewer?.email && (
                            <div className="text-xs text-gray-500">
                              {interview.interviewer.email}
                            </div>
                          )}
                      </TableCell>
                      <TableCell>
                          <div className="max-w-[200px] truncate text-sm text-gray-600">
                            {interview.notes || "-"}
                        </div>
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
                              <Link to={`/interviews/${interview.id}/edit`}>
                                <Edit className="mr-2 h-4 w-4" />
                                Edit
                              </Link>
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              className="text-destructive"
                              onClick={() => handleDeleteInterview(interview.id)}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            </div>
          )}
        </CardContent>
      </Card>

    </div>
  );
};

export default InterviewList;
