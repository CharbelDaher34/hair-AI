
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, FileText, Calendar, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";

const Index = () => {
  const stats = [
    { title: "Total Jobs", value: "12", icon: FileText, change: "+2 this week" },
    { title: "Active Applications", value: "48", icon: Users, change: "+15 this week" },
    { title: "Interviews Scheduled", value: "8", icon: Calendar, change: "+3 this week" },
    { title: "Hire Rate", value: "68%", icon: TrendingUp, change: "+5% this month" },
  ];

  const recentJobs = [
    { title: "Senior Frontend Developer", applications: 12, status: "Active" },
    { title: "Product Manager", applications: 8, status: "Draft" },
    { title: "UX Designer", applications: 15, status: "Active" },
  ];

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's what's happening with your recruitment.
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild>
            <Link to="/jobs/create">Create Job</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/profile">Profile</Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Jobs</CardTitle>
            <CardDescription>Your latest job postings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentJobs.map((job, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{job.title}</p>
                    <p className="text-sm text-muted-foreground">
                      {job.applications} applications
                    </p>
                  </div>
                  <Badge variant={job.status === "Active" ? "default" : "secondary"}>
                    {job.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks to get you started</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button asChild className="w-full justify-start">
              <Link to="/jobs/create">
                <FileText className="mr-2 h-4 w-4" />
                Create New Job
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link to="/applications">
                <Users className="mr-2 h-4 w-4" />
                Review Applications
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link to="/interviews/create">
                <Calendar className="mr-2 h-4 w-4" />
                Schedule Interview
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link to="/analytics">
                <TrendingUp className="mr-2 h-4 w-4" />
                View Analytics
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Index;
