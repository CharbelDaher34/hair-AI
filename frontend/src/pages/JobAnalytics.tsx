
import { useParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Link } from "react-router-dom";
import { Users, Eye, CheckCircle, XCircle } from "lucide-react";

const JobAnalytics = () => {
  const { id } = useParams();

  // Mock job data
  const job = {
    id: 1,
    title: "Senior Frontend Developer",
    applications: 45,
    interviews: 12,
    hired: 3,
  };

  const matchedCandidates = [
    {
      id: 1,
      name: "Alice Johnson",
      score: 92,
      satisfiedConstraints: 8,
      totalConstraints: 10,
      status: "pending",
    },
    {
      id: 2,
      name: "Bob Smith",
      score: 88,
      satisfiedConstraints: 7,
      totalConstraints: 10,
      status: "accepted",
    },
    {
      id: 3,
      name: "Carol Williams",
      score: 85,
      satisfiedConstraints: 9,
      totalConstraints: 10,
      status: "pending",
    },
    {
      id: 4,
      name: "David Brown",
      score: 82,
      satisfiedConstraints: 6,
      totalConstraints: 10,
      status: "rejected",
    },
    {
      id: 5,
      name: "Emma Davis",
      score: 79,
      satisfiedConstraints: 7,
      totalConstraints: 10,
      status: "pending",
    },
  ];

  const scoreDistribution = [
    { range: "90-100", count: 8, percentage: 18 },
    { range: "80-89", count: 15, percentage: 33 },
    { range: "70-79", count: 12, percentage: 27 },
    { range: "60-69", count: 7, percentage: 16 },
    { range: "50-59", count: 3, percentage: 6 },
  ];

  const constraintBreakdown = [
    { constraint: "Experience Years", satisfied: 38, total: 45, percentage: 84 },
    { constraint: "Technical Skills", satisfied: 35, total: 45, percentage: 78 },
    { constraint: "Education Level", satisfied: 42, total: 45, percentage: 93 },
    { constraint: "Portfolio Quality", satisfied: 28, total: 45, percentage: 62 },
    { constraint: "Location", satisfied: 40, total: 45, percentage: 89 },
  ];

  const statusColors = [
    { name: "Pending", value: 32, color: "#f59e0b" },
    { name: "Accepted", value: 8, color: "#10b981" },
    { name: "Rejected", value: 5, color: "#ef4444" },
  ];

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" => {
    switch (status) {
      case "accepted":
        return "default";
      case "rejected":
        return "destructive";
      default:
        return "secondary";
    }
  };

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Job Analytics</h1>
          <p className="text-muted-foreground">{job.title}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to={`/jobs/${id}`}>
              <Eye className="mr-2 h-4 w-4" />
              View Job
            </Link>
          </Button>
          <Button asChild>
            <Link to={`/jobs/${id}/matches`}>
              <Users className="mr-2 h-4 w-4" />
              View All Matches
            </Link>
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{job.applications}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Interviews</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{job.interviews}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Hired</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{job.hired}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Math.round((job.hired / job.applications) * 100)}%
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Score Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
            <CardDescription>Distribution of candidate match scores</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scoreDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="hsl(var(--primary))" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Application Status */}
        <Card>
          <CardHeader>
            <CardTitle>Application Status</CardTitle>
            <CardDescription>Current status of all applications</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusColors}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusColors.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Constraint Satisfaction */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Constraint Satisfaction Breakdown</CardTitle>
            <CardDescription>
              How well candidates meet specific job requirements
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {constraintBreakdown.map((constraint) => (
                <div key={constraint.constraint}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{constraint.constraint}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-muted-foreground">
                        {constraint.satisfied}/{constraint.total}
                      </span>
                      <Badge variant="outline">{constraint.percentage}%</Badge>
                    </div>
                  </div>
                  <div className="mt-1 h-2 bg-muted rounded-full">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${constraint.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Matched Candidates */}
      <Card>
        <CardHeader>
          <CardTitle>Top Matched Candidates</CardTitle>
          <CardDescription>
            Candidates with highest match scores for this position
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Constraints Met</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {matchedCandidates.map((candidate) => (
                <TableRow key={candidate.id}>
                  <TableCell className="font-medium">{candidate.name}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold">{candidate.score}%</span>
                      <div className="w-16 h-2 bg-muted rounded-full">
                        <div
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${candidate.score}%` }}
                        />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    {candidate.satisfiedConstraints}/{candidate.totalConstraints}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusVariant(candidate.status)}>
                      {candidate.status.charAt(0).toUpperCase() + candidate.status.slice(1)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex space-x-1">
                      {candidate.status === "pending" && (
                        <>
                          <Button size="sm" variant="outline">
                            <CheckCircle className="h-3 w-3" />
                          </Button>
                          <Button size="sm" variant="outline">
                            <XCircle className="h-3 w-3" />
                          </Button>
                        </>
                      )}
                      <Button size="sm" variant="outline" asChild>
                        <Link to={`/applications/${candidate.id}`}>
                          <Eye className="h-3 w-3" />
                        </Link>
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default JobAnalytics;
