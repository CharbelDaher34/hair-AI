import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Link } from "react-router-dom";
import { Users, Eye, CheckCircle, XCircle, Loader2, TrendingUp, Calendar, Target, ArrowUpDown, ArrowUp, ArrowDown, AlertTriangle, Flag } from "lucide-react";
import { toast } from "@/components/ui/sonner";
import apiService from "@/services/api";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface JobAnalyticsData {
  job_id: number;
  job_title: string;
  job_status: string;
  total_applications: number;
  applications_by_status: Record<string, number>;
  total_matches: number;
  average_match_score: number | null;
  top_match_score: number | null;
  total_interviews: number;
  interviews_by_type: Record<string, number>;
  interviews_by_status: Record<string, number>;
  unique_candidates: number;
  candidates_with_parsed_resumes: number;
  top_skills_from_candidates: string[];
  applications_last_7_days: number;
  applications_last_30_days: number;
  application_to_match_rate: number;
  application_to_interview_rate: number;
  match_to_interview_rate: number;
}

interface MatchCandidate {
  // Match fields
  id: number;
  application_id: number;
  score: number;
  score_breakdown?: {
    skills_score?: number;
    [key: string]: any;
  };
  weights_used?: {
    final_weights?: Record<string, number>;
    skill_weights?: Record<string, number>;
  };
  matching_skills?: string[];
  missing_skills?: string[];
  extra_skills?: string[];
  flags?: {
    constraint_violations?: Record<string, string>;
  };
  created_at: string;
  updated_at: string;
  // Candidate fields
  full_name: string;
  email: string;
  phone?: string;
  resume_url?: string;
  parsed_resume?: any;
  employer_id?: number;
  // Application status
  application_status?: string;
}

interface JobMatchesResponse {
  matches: MatchCandidate[];
  job: {
    id: number;
    title: string;
    description: string;
    status: string;
  };
}

interface ChartData {
  type?: string;
  name?: string;
  value?: number;
  count?: number;
  color?: string;
}

type SortField = 'score' | 'full_name';
type SortDirection = 'asc' | 'desc';

const JobAnalytics = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<JobAnalyticsData | null>(null);
  const [matches, setMatches] = useState<MatchCandidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMatches, setIsLoadingMatches] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('score');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Fetch analytics and matches in parallel
        const [analyticsData, matchesData] = await Promise.all([
          apiService.getJobAnalytics(id!),
          apiService.getJobMatches(id!, true)
        ]);
        
        setAnalytics(analyticsData);
        setMatches(matchesData.matches);
      } catch (error: any) {
        console.error('Failed to fetch job data:', error);
        setError(error.message || 'Failed to fetch data');
        toast.error("Failed to fetch job data", {
          description: error.message || "An unexpected error occurred.",
        });
      } finally {
        setIsLoading(false);
        setIsLoadingMatches(false);
      }
    };

    if (id) {
      fetchData();
    }
  }, [id]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedMatches = [...matches].sort((a, b) => {
    let aValue: any = a[sortField];
    let bValue: any = b[sortField];

    // Handle string sorting for name
    if (sortField === 'full_name') {
      aValue = aValue?.toLowerCase() || '';
      bValue = bValue?.toLowerCase() || '';
    }

    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4" />;
    }
    return sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />;
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.8) return 'text-green-600';
    if (similarity >= 0.6) return 'text-blue-600';
    return 'text-gray-600';
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
            <span className="text-lg font-medium text-gray-700">Loading analytics...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="flex items-center justify-center h-64">
          <Card className="w-full max-w-md shadow-xl border-0">
            <CardContent className="text-center p-8 space-y-4">
              <p className="text-red-600 font-semibold text-lg mb-4">Error loading analytics: {error}</p>
              <Button onClick={() => window.location.reload()} className="button shadow-lg hover:shadow-xl transition-all duration-300">
              Retry
            </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="flex items-center justify-center h-64">
          <Card className="w-full max-w-md shadow-xl border-0">
            <CardContent className="text-center p-8 space-y-4">
              <p className="text-lg text-gray-600">No analytics data available for this job.</p>
              <Button asChild className="button shadow-lg hover:shadow-xl transition-all duration-300">
                <Link to={`/jobs`}>Back to Jobs</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Transform data for charts
  const interviewTypeData: ChartData[] = Object.entries(analytics.interviews_by_type || {}).map(([type, count]) => ({
    type: type.charAt(0).toUpperCase() + type.slice(1),
    count
  }));

  const interviewStatusData: ChartData[] = Object.entries(analytics.interviews_by_status || {}).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    color: status === 'done' ? '#10b981' : status === 'scheduled' ? '#f59e0b' : '#ef4444'
  }));

  const applicationStatusData: ChartData[] = Object.entries(analytics.applications_by_status || {}).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    color: status === 'hired' ? '#10b981' : status === 'pending' ? '#f59e0b' : status === 'rejected' ? '#ef4444' : '#3b82f6'
  }));

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" => {
    switch (status.toLowerCase()) {
      case "completed":
      case "done":
        return "default";
      case "rejected":
      case "canceled":
        return "destructive";
      default:
        return "secondary";
    }
  };

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Job Analytics: {analytics.job_title}
          </h1>
          <Badge variant={getStatusVariant(analytics.job_status)} className="font-medium px-3 py-1 text-base">
            {analytics.job_status.charAt(0).toUpperCase() + analytics.job_status.slice(1)}
          </Badge>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" asChild className="shadow-md hover:shadow-lg transition-all duration-300">
            <Link to={`/jobs/${id}`}>
              <Eye className="mr-2 h-4 w-4" />
              View Job
            </Link>
          </Button>
          <Button variant="outline" asChild className="shadow-md hover:shadow-lg transition-all duration-300">
            <Link to={`/jobs/${id}/matches`}>
              <Users className="mr-2 h-4 w-4" />
              View All Matches
            </Link>
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[ 
          { title: "Total Applications", value: analytics.total_applications, icon: Users, note: `${analytics.applications_last_7_days} in last 7 days` },
          { title: "Total Matches", value: analytics.total_matches, icon: Target, note: `${analytics.application_to_match_rate}% conversion` },
          { title: "Interviews", value: analytics.total_interviews, icon: Calendar, note: `${analytics.application_to_interview_rate}% from applications` },
          { title: "Avg Match Score", value: analytics.average_match_score ? `${(analytics.average_match_score * 100).toFixed(1)}%` : 'N/A', icon: TrendingUp, note: `Top: ${analytics.top_match_score ? `${(analytics.top_match_score * 100).toFixed(1)}%` : 'N/A'}` }
        ].map((stat, index) => (
          <Card key={stat.title} className="card hover:scale-105 transition-all duration-300 border-0 shadow-lg hover:shadow-xl" style={{animationDelay: `${index * 100}ms`}}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-semibold text-gray-700">{stat.title}</CardTitle>
              <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg">
                <stat.icon className="h-5 w-5 text-blue-600" />
              </div>
          </CardHeader>
          <CardContent>
              <div className="text-3xl font-bold text-gray-800 mb-1">{stat.value}</div>
              <p className="text-xs text-gray-600">{stat.note}</p>
          </CardContent>
        </Card>
        ))}
      </div>

      {/* Candidate Matches Table */}
      <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
        <CardHeader className="pb-6">
          <CardTitle className="text-2xl font-bold text-gray-800">Top 5 Candidates</CardTitle>
          <CardDescription className="text-base text-gray-600">
            Detailed view of all candidate matches with scores and skills
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingMatches ? (
            <div className="flex items-center justify-center h-40">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <span className="ml-3 text-lg font-medium text-gray-700">Loading matches...</span>
            </div>
          ) : matches.length === 0 ? (
            <div className="text-center py-12 space-y-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto">
                <Users className="h-8 w-8 text-blue-600" />
              </div>
              <p className="text-lg text-gray-600 mb-4">No matches found for this job yet.</p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
              <Table>
                <TableHeader className="bg-gradient-to-r from-gray-50 to-blue-50">
                  <TableRow>
                    <TableHead>
                      <Button
                        variant="ghost"
                        onClick={() => handleSort('full_name')}
                        className="h-auto p-2 font-semibold text-gray-700 hover:bg-gray-200 transition-colors duration-200"
                      >
                        Candidate {getSortIcon('full_name')}
                      </Button>
                    </TableHead>
                    <TableHead>
                      <Button
                        variant="ghost"
                        onClick={() => handleSort('score')}
                        className="h-auto p-2 font-semibold text-gray-700 hover:bg-gray-200 transition-colors duration-200"
                      >
                        Overall Score {getSortIcon('score')}
                      </Button>
                    </TableHead>
                    <TableHead className="font-semibold text-gray-700">Score Breakdown</TableHead>
                    <TableHead className="font-semibold text-gray-700">Matching Skills</TableHead>
                    <TableHead className="font-semibold text-gray-700">Status</TableHead>
                    <TableHead className="font-semibold text-gray-700">Flags</TableHead>
                    <TableHead className="font-semibold text-gray-700">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedMatches.map((match) => (
                    <TableRow key={match.id} className="hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200">
                      <TableCell>
                        <div className="space-y-1">
                          <div className="font-semibold text-gray-800">{match.full_name}</div>
                          <div className="text-sm text-gray-600">{match.email}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className={`font-bold text-lg ${getScoreColor(match.score)}`}>
                          {(match.score * 100).toFixed(1)}%
                        </div>
                      </TableCell>
                      <TableCell>
                        {match.score_breakdown ? (
                          <div className="text-xs space-y-1">
                            {Object.entries(match.score_breakdown).slice(0, 2).map(([key, value]) => (
                              <div key={key} className="text-gray-600">
                                {key.replace(/_/g, ' ')}: {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : String(value)}
                              </div>
                            ))}
                            {Object.keys(match.score_breakdown).length > 2 && (
                              <div className="text-gray-500 italic">+{Object.keys(match.score_breakdown).length - 2} more</div>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-gray-500 italic">No breakdown</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {match.matching_skills && match.matching_skills.length > 0 ? (
                            <>
                              {match.matching_skills.slice(0, 3).map((skill, index) => (
                                <Badge key={index} variant="secondary" className="text-xs bg-green-100 text-green-700">
                                  {skill}
                                </Badge>
                              ))}
                              {match.matching_skills.length > 3 && (
                                <Badge variant="outline" className="text-xs border-green-200 text-green-600">
                                  +{match.matching_skills.length - 3} more
                                </Badge>
                              )}
                            </>
                          ) : (
                            <span className="text-xs text-gray-500 italic">No matching skills</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(match.application_status || 'pending')} className="font-medium">
                          {match.application_status || 'pending'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {match.flags?.constraint_violations && Object.keys(match.flags.constraint_violations).length > 0 ? (
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button 
                                variant="outline" 
                                size="sm" 
                                className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300 transition-all duration-150"
                              >
                                <AlertTriangle className="h-4 w-4 mr-1" />
                                {Object.keys(match.flags.constraint_violations).length} Issue{Object.keys(match.flags.constraint_violations).length !== 1 ? 's' : ''}
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-80 p-4 bg-white shadow-xl rounded-lg border border-red-200">
                              <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                  <Flag className="h-5 w-5 text-red-600" />
                                  <h4 className="font-semibold text-red-800">Constraint Violations</h4>
                                </div>
                                <div className="space-y-2">
                                  {Object.entries(match.flags.constraint_violations).map(([field, violation]) => (
                                    <div key={field} className="p-2 bg-red-50 rounded border border-red-200">
                                      <div className="font-medium text-red-800 text-sm">{field}</div>
                                      <div className="text-red-600 text-xs mt-1">{violation}</div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </PopoverContent>
                          </Popover>
                        ) : (
                          <Badge variant="secondary" className="text-green-700 bg-green-100 border-green-200">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            No Issues
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="text-green-600 hover:text-green-800 hover:bg-green-100 transition-all duration-150"
                          onClick={() => navigate(`/interviews/create?application_id=${match.application_id}`)}
                          disabled={!match.application_id}
                          title="Schedule Interview"
                        >
                          <Calendar className="h-4 w-4 mr-1" />
                          Schedule Interview
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Interview Types */}
        {interviewTypeData.length > 0 && (
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Interview Types</CardTitle>
              <CardDescription className="text-base text-gray-600">Distribution of interview types</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={interviewTypeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="type" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }} 
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Application Status */}
        {applicationStatusData.length > 0 && (
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Application Status</CardTitle>
              <CardDescription className="text-base text-gray-600">Current status of all applications</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={applicationStatusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {applicationStatusData.map((entry, index) => (
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
        )}

        {/* Interview Status */}
        {interviewStatusData.length > 0 && (
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Interview Status</CardTitle>
              <CardDescription className="text-base text-gray-600">Current status of all interviews</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={interviewStatusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {interviewStatusData.map((entry, index) => (
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
        )}

        {/* Candidate Insights */}
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Candidate Insights</CardTitle>
            <CardDescription className="text-base text-gray-600">Overview of candidate pool</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Unique Candidates</span>
                <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">{analytics.unique_candidates}</Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">With Parsed Resumes</span>
                <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">
                  {analytics.candidates_with_parsed_resumes}/{analytics.unique_candidates}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Applications (30 days)</span>
                <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-200">{analytics.applications_last_30_days}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Skills */}
      {analytics.top_skills_from_candidates && analytics.top_skills_from_candidates.length > 0 && (
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-bold text-gray-800">Top Skills from Candidates</CardTitle>
            <CardDescription className="text-base text-gray-600">
              Most common skills found in candidate resumes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {analytics.top_skills_from_candidates.map((skill, index) => (
                <Badge key={index} className="text-sm px-3 py-1 bg-gradient-to-r from-blue-100 to-purple-100 text-blue-700 border-blue-200">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Conversion Metrics */}
      <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
        <CardHeader className="pb-6">
          <CardTitle className="text-2xl font-bold text-gray-800">Conversion Metrics</CardTitle>
          <CardDescription className="text-base text-gray-600">
            Recruitment funnel performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border border-blue-200">
              <div className="text-4xl font-bold text-blue-600 mb-2">
                {analytics.application_to_match_rate}%
              </div>
              <p className="text-sm text-gray-700 font-medium">Application → Match</p>
            </div>
            <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border border-blue-200">
              <div className="text-4xl font-bold text-purple-600 mb-2">
                {analytics.application_to_interview_rate}%
              </div>
              <p className="text-sm text-gray-700 font-medium">Application → Interview</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default JobAnalytics;
