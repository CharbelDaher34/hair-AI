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

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading interviews...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={fetchInterviews}>Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Interview Tracking</h1>
          <p className="text-muted-foreground">
            Manage and track all candidate interviews
          </p>
        </div>
        <Button asChild>
          <Link to="/interviews/create">
            <Plus className="mr-2 h-4 w-4" />
            Schedule Interview
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            All Interviews ({interviews.length})
          </CardTitle>
          <CardDescription>
            Overview of all scheduled and completed interviews
          </CardDescription>
          <div className="flex items-center space-x-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search interviews..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[200px]">
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
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
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
            <div className="text-center py-8">
              <p className="text-muted-foreground">No interviews found</p>
              {interviews.length === 0 && (
                <Button asChild className="mt-4">
                  <Link to="/interviews/create">
                    <Plus className="mr-2 h-4 w-4" />
                    Schedule Your First Interview
                  </Link>
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Candidate</TableHead>
                  <TableHead>Job</TableHead>
                  <TableHead>Date & Time</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredInterviews.map((interview) => {
                  const dateTime = formatDateTime(interview.date);
                  return (
                    <TableRow key={interview.id}>
                      <TableCell>
                        <div className="font-medium">
                          {interview.application?.candidate?.full_name || "Unknown"}
                        </div>
                      </TableCell>
                      <TableCell>
                        {interview.application?.job?.title || "Unknown"}
                      </TableCell>
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
                        <Badge variant={getStatusVariant(interview.status)}>
                          {interview.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="max-w-[200px] truncate text-sm text-muted-foreground">
                          {interview.notes || "No notes"}
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
          )}
        </CardContent>
      </Card>

      {/* Interview Statistics */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>This Week</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.thisWeek}</div>
            <p className="text-muted-foreground text-sm">Interviews scheduled</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Completion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.successRate}%</div>
            <p className="text-muted-foreground text-sm">Interviews completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Scheduled</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pending}</div>
            <p className="text-muted-foreground text-sm">Awaiting interviews</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InterviewList;
