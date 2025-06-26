import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend } from "recharts";
import { Users, FileText, Calendar, TrendingUp, Target, UserCheck, Bot } from "lucide-react";
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
        <div className="text-2xl font-semibold">Loading home page...</div>
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
    { title: "Open Jobs", value: analytics_data.total_open_jobs, icon: FileText, change: "+16.7%" },
    { title: "Total Applications", value: analytics_data.total_applications, icon: Users, change: "+23.1%" },
    { title: "Total Candidates", value: analytics_data.total_candidates || 0, icon: UserCheck, change: "+18.3%" },
    { title: "Total Interviews", value: analytics_data.total_interviews, icon: Calendar, change: "+12.5%" },
    { title: "Hire Rate", value: `${analytics_data.hire_rate}%`, icon: Target, change: "+5.2%" },
    { title: "Avg. Match Score", value: `${analytics_data.average_match_score}%`, icon: Bot, change: "+2.1%" }
  ];

  const applications_over_time = analytics_data.applications_over_time;
  const job_performance = analytics_data.job_performance;
  const recent_jobs = analytics_data.recent_jobs;
  const applications_by_status = analytics_data.applications_by_status;

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#AF19FF', '#FF1919'];

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Home
          </h1>
          <p className="text-lg text-gray-600">
            Welcome back! Here's what's happening with your recruitment.
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" asChild className="shadow-lg hover:shadow-xl transition-all duration-300">
            <Link to="/jobs/create">Create Job</Link>
          </Button>
          <Button variant="outline" asChild className="shadow-lg hover:shadow-xl transition-all duration-300">
            <Link to="/profile">Profile</Link>
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-6 md:grid-cols-3 lg:grid-cols-6">
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
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
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

        {/* Application Status Distribution */}
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Application Status</CardTitle>
            <CardDescription className="text-base text-gray-600">Distribution of application stages</CardDescription>
          </CardHeader>
          <CardContent>
            {applications_by_status && applications_by_status.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={applications_by_status}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                    nameKey="status"
                    label={({ cx, cy, midAngle, innerRadius, outerRadius, percent, index }) => {
                        const RADIAN = Math.PI / 180;
                        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                        const x = cx + radius * Math.cos(-midAngle * RADIAN);
                        const y = cy + radius * Math.sin(-midAngle * RADIAN);
                        return (
                          <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
                            {`${(percent * 100).toFixed(0)}%`}
                          </text>
                        );
                      }}
                  >
                    {applications_by_status.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500">
                No application status data available
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
                  <div key={index} className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-100 to-purple-100 rounded-lg hover:from-blue-200 hover:to-purple-200 transition-all duration-300 border border-blue-200">
                    <div>
                      <p className="font-semibold text-blue-900">{job.title}</p>
                      <p className="text-sm text-blue-700 font-medium">
                        {job.applications} applications
                      </p>
                    </div>
                    <Badge 
                      variant={job.status === "published" ? "default" : "secondary"}
                      className={job.status === "published" ? "bg-green-500 text-white hover:bg-green-600 font-semibold" : "bg-gray-500 text-white font-semibold"}
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
            <CardTitle className="text-xl font-bold text-gray-800">Popular Jobs</CardTitle>
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

    </div>
  );
};

export default Index;
