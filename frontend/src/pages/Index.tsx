import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import { Users, FileText, Calendar, TrendingUp, Target } from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import apiService from "@/services/api";

const Index = () => {
  const [analytics_data, set_analytics_data] = useState(null);
  const [loading, set_loading] = useState(true);
  const [error, set_error] = useState(null);

  useEffect(() => {
    const fetch_analytics = async () => {
      try {
        const data = await apiService.getCompanyAnalytics();
        set_analytics_data(data);
        set_error(null);
      } catch (error) {
        console.error("Failed to fetch company analytics:", error);
        set_error("Failed to load analytics data");
      } finally {
        set_loading(false);
      }
    };

    fetch_analytics();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center h-screen">
        <div className="text-2xl font-semibold">Loading dashboard...</div>
      </div>
    );
  }

  if (error || !analytics_data) {
    return (
      <div className="flex-1 flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-2xl font-semibold text-red-500 mb-4">
            {error || "No analytics data available"}
          </div>
          <Button onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const stats = [
    { title: "Total Jobs", value: analytics_data.total_jobs, icon: FileText, change: "+16.7%" },
    { title: "Total Applications", value: analytics_data.total_applications, icon: Users, change: "+23.1%" },
    { title: "Total Interviews", value: analytics_data.total_interviews, icon: Calendar, change: "+12.5%" },
    { title: "Hire Rate", value: `${analytics_data.hire_rate}%`, icon: Target, change: "+5.2%" },
  ];

  const applications_over_time = analytics_data.applications_over_time;
  const job_performance = analytics_data.job_performance;
  const recent_jobs = analytics_data.recent_jobs;

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

      {/* Key Metrics */}
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
              <div className="flex items-center space-x-2 text-xs">
                <TrendingUp className="h-3 w-3 text-green-500" />
                <span className="text-green-600 font-medium">{stat.change}</span>
                <span className="text-gray-600">from last month</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Quick Actions - Moved to first position */}
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

        {/* Applications Over Time */}
        <Card className="lg:col-span-2 card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Applications Over Time</CardTitle>
            <CardDescription className="text-base text-gray-600">Monthly application volume trends</CardDescription>
          </CardHeader>
          <CardContent>
            {applications_over_time.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={applications_over_time}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }} 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="applications" 
                    stroke="#3b82f6" 
                    strokeWidth={3}
                    dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500">
                No application data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Recent Jobs */}
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Recent Jobs</CardTitle>
            <CardDescription className="text-base text-gray-600">Your latest job postings</CardDescription>
          </CardHeader>
          <CardContent>
            {recent_jobs.length > 0 ? (
              <div className="space-y-4">
                {recent_jobs.map((job, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg hover:from-blue-50 hover:to-purple-50 transition-all duration-300">
                    <div>
                      <p className="font-semibold text-gray-800">{job.title}</p>
                      <p className="text-sm text-gray-600">
                        {job.applications} applications
                      </p>
                    </div>
                    <Badge 
                      variant={job.status === "published" ? "default" : "secondary"}
                      className={job.status === "published" ? "bg-green-100 text-green-800 hover:bg-green-200" : ""}
                    >
                      {job.status}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-[200px] text-gray-500">
                No jobs created yet
              </div>
            )}
          </CardContent>
        </Card>

        {/* Job Performance */}
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Top Performing Jobs</CardTitle>
            <CardDescription className="text-base text-gray-600">Jobs with highest application counts</CardDescription>
          </CardHeader>
          <CardContent>
            {job_performance.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={job_performance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="job" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }} 
                  />
                  <Bar dataKey="applications" fill="#3b82f6" name="Applications" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500">
                No job performance data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>



      {/* Performance Summary */}
      <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
        <CardHeader className="pb-6">
          <CardTitle className="text-2xl font-bold text-gray-800">Performance Summary</CardTitle>
          <CardDescription className="text-base text-gray-600">Key insights from your recruitment data</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-3 p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border border-green-200">
              <h4 className="font-bold text-green-700 flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                Strong Performance
              </h4>
              <ul className="text-sm text-gray-700 space-y-2">
                <li>• {analytics_data.hire_rate}% hire rate achieved</li>
                <li>• {analytics_data.total_applications} total applications received</li>
                <li>• {analytics_data.total_interviews} interviews conducted</li>
              </ul>
            </div>
            <div className="space-y-3 p-4 bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg border border-orange-200">
              <h4 className="font-bold text-orange-700 flex items-center gap-2">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                Areas for Improvement
              </h4>
              <ul className="text-sm text-gray-700 space-y-2">
                <li>• Monitor application completion rates</li>
                <li>• Track candidate engagement patterns</li>
                <li>• Optimize job posting performance</li>
              </ul>
            </div>
            <div className="space-y-3 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
              <h4 className="font-bold text-blue-700 flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                Recommendations
              </h4>
              <ul className="text-sm text-gray-700 space-y-2">
                <li>• Create more jobs to increase reach</li>
                <li>• Improve application process flow</li>
                <li>• Analyze top performing job patterns</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Index;
