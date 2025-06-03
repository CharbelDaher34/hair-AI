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
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-lg text-gray-600">
            Welcome back! Here's what's happening with your recruitment.
          </p>
        </div>
        <div className="flex gap-3">
          <Button asChild className="button shadow-lg hover:shadow-xl transition-all duration-300">
            <Link to="/jobs/create">Create Job</Link>
          </Button>
          <Button variant="outline" asChild className="shadow-md hover:shadow-lg transition-all duration-300">
            <Link to="/profile">Profile</Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <Card key={stat.title} className="card hover:scale-105 transition-all duration-300 border-0 shadow-lg hover:shadow-xl" style={{animationDelay: `${index * 100}ms`}}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-semibold text-gray-700">{stat.title}</CardTitle>
              <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg">
                <stat.icon className="h-5 w-5 text-blue-600" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-800 mb-1">{stat.value}</div>
              <p className="text-sm text-green-600 font-medium">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Recent Jobs</CardTitle>
            <CardDescription className="text-base text-gray-600">Your latest job postings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentJobs.map((job, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg hover:from-blue-50 hover:to-purple-50 transition-all duration-300">
                  <div>
                    <p className="font-semibold text-gray-800">{job.title}</p>
                    <p className="text-sm text-gray-600">
                      {job.applications} applications
                    </p>
                  </div>
                  <Badge 
                    variant={job.status === "Active" ? "default" : "secondary"}
                    className={job.status === "Active" ? "bg-green-100 text-green-800 hover:bg-green-200" : ""}
                  >
                    {job.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Quick Actions</CardTitle>
            <CardDescription className="text-base text-gray-600">Common tasks to get you started</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button asChild className="w-full justify-start button h-12 text-base font-semibold shadow-md hover:shadow-lg transition-all duration-300">
              <Link to="/jobs/create">
                <FileText className="mr-3 h-5 w-5" />
                Create New Job
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start h-12 text-base font-semibold shadow-sm hover:shadow-md transition-all duration-300 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50">
              <Link to="/applications">
                <Users className="mr-3 h-5 w-5" />
                Review Applications
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start h-12 text-base font-semibold shadow-sm hover:shadow-md transition-all duration-300 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50">
              <Link to="/interviews/create">
                <Calendar className="mr-3 h-5 w-5" />
                Schedule Interview
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start h-12 text-base font-semibold shadow-sm hover:shadow-md transition-all duration-300 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50">
              <Link to="/analytics">
                <TrendingUp className="mr-3 h-5 w-5" />
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
