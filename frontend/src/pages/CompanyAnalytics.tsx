import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from "recharts";
import { TrendingUp, Users, FileText, Calendar, Target } from "lucide-react";
import { useEffect, useState } from "react";
import apiService from "@/services/api";

const CompanyAnalytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        // Hardcoded company ID for now
        const data = await apiService.getCompanyAnalytics();
        setAnalyticsData(data);
      } catch (error) {
        console.error("Failed to fetch company analytics:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center h-screen">
        <div className="text-2xl font-semibold">Loading analytics...</div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="flex-1 flex items-center justify-center h-screen">
        <div className="text-2xl font-semibold text-red-500">Failed to load analytics data.</div>
      </div>
    );
  }

  const stats = [
    { title: "Total Jobs", value: analyticsData.total_jobs, icon: FileText, change: "+16.7%" },
    { title: "Total Applications", value: analyticsData.total_applications, icon: Users, change: "+23.1%" },
    { title: "Total Interviews", value: analyticsData.total_interviews, icon: Calendar, change: "+12.5%" },
    { title: "Hire Rate", value: `${analyticsData.hire_rate}%`, icon: Target, change: "+5.2%" },
  ];

  const applicationsOverTime = analyticsData.applications_over_time;
  const jobPerformance = analyticsData.job_performance;

  const completionRates = [
    { stage: "Form Started", value: 100, count: 248 },
    { stage: "Basic Info", value: 85, count: 211 },
    { stage: "Experience", value: 72, count: 179 },
    { stage: "Portfolio", value: 58, count: 144 },
    { stage: "Submitted", value: 45, count: 112 },
  ];

  const dropoffPoints = [
    { name: "Experience Section", value: 35, color: "#ef4444" },
    { name: "Portfolio Upload", value: 25, color: "#f97316" },
    { name: "Cover Letter", value: 20, color: "#eab308" },
    { name: "References", value: 15, color: "#22c55e" },
    { name: "Other", value: 5, color: "#6b7280" },
  ];

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Company Analytics
          </h1>
          <p className="text-lg text-gray-600">
            Overview of your recruitment performance and insights
          </p>
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

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Applications Over Time */}
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Applications Over Time</CardTitle>
            <CardDescription className="text-base text-gray-600">Monthly application volume trends</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={applicationsOverTime}>
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
          </CardContent>
        </Card>

        {/* Job Performance */}
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Top Performing Jobs</CardTitle>
            <CardDescription className="text-base text-gray-600">Jobs with highest application to hire ratio</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={jobPerformance}>
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
          </CardContent>
        </Card>

        {/* Form Completion Rates */}
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Form Completion Rates</CardTitle>
            <CardDescription className="text-base text-gray-600">How candidates progress through application forms</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {completionRates.map((stage, index) => (
                <div key={stage.stage} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-gray-700">{stage.stage}</span>
                    <div className="flex items-center space-x-3">
                      <span className="text-gray-600 font-medium">{stage.count} candidates</span>
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">{stage.value}%</Badge>
                    </div>
                  </div>
                  <Progress value={stage.value} className="h-3" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Candidate Drop-off Points */}
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Candidate Drop-off Points</CardTitle>
            <CardDescription className="text-base text-gray-600">Where candidates abandon their applications</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={dropoffPoints}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {dropoffPoints.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e2e8f0', 
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }} 
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Performance Summary */}
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
                <li>• Frontend Developer roles show highest conversion</li>
                <li>• 23% increase in applications this month</li>
                <li>• Interview-to-hire ratio improved by 12%</li>
              </ul>
            </div>
            <div className="space-y-3 p-4 bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg border border-orange-200">
              <h4 className="font-bold text-orange-700 flex items-center gap-2">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                Areas for Improvement
              </h4>
              <ul className="text-sm text-gray-700 space-y-2">
                <li>• 35% drop-off at experience section</li>
                <li>• Portfolio upload causing abandonment</li>
                <li>• Consider simplifying application form</li>
              </ul>
            </div>
            <div className="space-y-3 p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
              <h4 className="font-bold text-blue-700 flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                Recommendations
              </h4>
              <ul className="text-sm text-gray-700 space-y-2">
                <li>• Add progress indicators to forms</li>
                <li>• Make portfolio upload optional initially</li>
                <li>• A/B test shorter application forms</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CompanyAnalytics;
