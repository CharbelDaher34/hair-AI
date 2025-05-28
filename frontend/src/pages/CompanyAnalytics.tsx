
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from "recharts";
import { TrendingUp, Users, FileText, Calendar, Target } from "lucide-react";

const CompanyAnalytics = () => {
  const stats = [
    { title: "Total Jobs", value: "12", icon: FileText, change: "+16.7%" },
    { title: "Total Applications", value: "248", icon: Users, change: "+23.1%" },
    { title: "Total Interviews", value: "42", icon: Calendar, change: "+12.5%" },
    { title: "Hire Rate", value: "68%", icon: Target, change: "+5.2%" },
  ];

  const applicationsOverTime = [
    { month: "Jan", applications: 45 },
    { month: "Feb", applications: 52 },
    { month: "Mar", applications: 48 },
    { month: "Apr", applications: 61 },
    { month: "May", applications: 55 },
    { month: "Jun", applications: 67 },
  ];

  const jobPerformance = [
    { job: "Frontend Dev", applications: 45, hired: 8 },
    { job: "Backend Dev", applications: 38, hired: 6 },
    { job: "Product Manager", applications: 32, hired: 4 },
    { job: "UX Designer", applications: 28, hired: 5 },
    { job: "Data Analyst", applications: 22, hired: 3 },
  ];

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
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Company Analytics</h1>
          <p className="text-muted-foreground">
            Overview of your recruitment performance and insights
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <TrendingUp className="h-3 w-3 text-green-500" />
                <span className="text-green-500">{stat.change}</span>
                <span>from last month</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Applications Over Time */}
        <Card>
          <CardHeader>
            <CardTitle>Applications Over Time</CardTitle>
            <CardDescription>Monthly application volume trends</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={applicationsOverTime}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="applications" 
                  stroke="hsl(var(--primary))" 
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Job Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Top Performing Jobs</CardTitle>
            <CardDescription>Jobs with highest application to hire ratio</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={jobPerformance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="job" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="applications" fill="hsl(var(--primary))" name="Applications" />
                <Bar dataKey="hired" fill="hsl(var(--secondary))" name="Hired" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Form Completion Rates */}
        <Card>
          <CardHeader>
            <CardTitle>Form Completion Rates</CardTitle>
            <CardDescription>How candidates progress through application forms</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {completionRates.map((stage, index) => (
                <div key={stage.stage}>
                  <div className="flex items-center justify-between text-sm">
                    <span>{stage.stage}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-muted-foreground">{stage.count}</span>
                      <Badge variant="outline">{stage.value}%</Badge>
                    </div>
                  </div>
                  <Progress value={stage.value} className="mt-1" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Candidate Drop-off Points */}
        <Card>
          <CardHeader>
            <CardTitle>Candidate Drop-off Points</CardTitle>
            <CardDescription>Where candidates abandon their applications</CardDescription>
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
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Performance Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Summary</CardTitle>
          <CardDescription>Key insights from your recruitment data</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <h4 className="font-semibold text-green-600">Strong Performance</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Frontend Developer roles show highest conversion</li>
                <li>• 23% increase in applications this month</li>
                <li>• Interview-to-hire ratio improved by 12%</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-orange-600">Areas for Improvement</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• 35% drop-off at experience section</li>
                <li>• Portfolio upload causing abandonment</li>
                <li>• Consider simplifying application form</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-blue-600">Recommendations</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Make portfolio upload optional initially</li>
                <li>• Add progress indicator to forms</li>
                <li>• Implement auto-save functionality</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CompanyAnalytics;
