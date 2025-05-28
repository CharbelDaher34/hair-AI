
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Calendar, Plus, Search, MoreHorizontal, Edit, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";

const InterviewList = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [jobFilter, setJobFilter] = useState("all");
  const [resultFilter, setResultFilter] = useState("all");

  const interviews = [
    {
      id: 1,
      candidateName: "John Doe",
      jobTitle: "Senior Frontend Developer",
      date: "2024-01-25",
      time: "14:00",
      interviewer: "Sarah Wilson",
      type: "Technical",
      result: "Pending",
      notes: "Strong technical skills, good communication",
    },
    {
      id: 2,
      candidateName: "Jane Smith",
      jobTitle: "Product Manager",
      date: "2024-01-24",
      time: "10:30",
      interviewer: "Mike Johnson",
      type: "Behavioral",
      result: "Accepted",
      notes: "Excellent leadership experience",
    },
    {
      id: 3,
      candidateName: "Bob Wilson",
      jobTitle: "UX Designer",
      date: "2024-01-23",
      time: "15:00",
      interviewer: "Lisa Anderson",
      type: "Portfolio Review",
      result: "Rejected",
      notes: "Portfolio lacks recent work",
    },
    {
      id: 4,
      candidateName: "Alice Brown",
      jobTitle: "Backend Engineer",
      date: "2024-01-26",
      time: "11:00",
      interviewer: "Tom Davis",
      type: "Technical",
      result: "Pending",
      notes: "Scheduled for system design discussion",
    },
  ];

  const jobs = [
    "Senior Frontend Developer",
    "Product Manager", 
    "UX Designer",
    "Backend Engineer"
  ];

  const filteredInterviews = interviews.filter(interview => {
    const matchesSearch = interview.candidateName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         interview.jobTitle.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesJob = jobFilter === "all" || interview.jobTitle === jobFilter;
    const matchesResult = resultFilter === "all" || interview.result.toLowerCase() === resultFilter;
    
    return matchesSearch && matchesJob && matchesResult;
  });

  const getResultVariant = (result: string): "default" | "secondary" | "destructive" => {
    switch (result.toLowerCase()) {
      case "accepted":
        return "default";
      case "rejected":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const formatDateTime = (date: string, time: string) => {
    const dateObj = new Date(date);
    return {
      date: dateObj.toLocaleDateString(),
      time: time,
    };
  };

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
            All Interviews
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
            <Select value={jobFilter} onValueChange={setJobFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filter by job" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Jobs</SelectItem>
                {jobs.map((job) => (
                  <SelectItem key={job} value={job}>
                    {job}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={resultFilter} onValueChange={setResultFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Filter by result" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Results</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Candidate</TableHead>
                <TableHead>Job</TableHead>
                <TableHead>Date & Time</TableHead>
                <TableHead>Interviewer</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Result</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredInterviews.map((interview) => {
                const dateTime = formatDateTime(interview.date, interview.time);
                return (
                  <TableRow key={interview.id}>
                    <TableCell>
                      <div className="font-medium">{interview.candidateName}</div>
                    </TableCell>
                    <TableCell>{interview.jobTitle}</TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{dateTime.date}</div>
                        <div className="text-sm text-muted-foreground">{dateTime.time}</div>
                      </div>
                    </TableCell>
                    <TableCell>{interview.interviewer}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{interview.type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getResultVariant(interview.result)}>
                        {interview.result}
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
                            <Link to={`/interviews/${interview.id}/edit`}>
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
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Interview Statistics */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>This Week</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8</div>
            <p className="text-muted-foreground text-sm">Interviews scheduled</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">75%</div>
            <p className="text-muted-foreground text-sm">Positive outcomes</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {interviews.filter(i => i.result === "Pending").length}
            </div>
            <p className="text-muted-foreground text-sm">Awaiting results</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InterviewList;
