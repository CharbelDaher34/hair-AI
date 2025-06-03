import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { Link } from "react-router-dom";
import { Users, Eye, CheckCircle, XCircle, Loader2, TrendingUp, Calendar, Target, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { toast } from "@/components/ui/sonner";
import apiService from "@/services/api";

interface JobAnalyticsData {
  job_id: number;
  job_title: string;
  job_status: string;
  total_applications: number;
  applications_by_status: Record<string, number>;
  total_matches: number;
  matches_by_status: Record<string, number>;
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
  embedding_similarity: number;
  match_percentage: number;
  matching_skills: string[];
  missing_skills: string[];
  extra_skills: string[];
  total_required_skills: number;
  matching_skills_count: number;
  missing_skills_count: number;
  extra_skills_count: number;
  skill_weight: number;
  embedding_weight: number;
  status: string;
  created_at: string;
  updated_at: string;
  // Candidate fields
  full_name: string;
  email: string;
  phone?: string;
  resume_url?: string;
  parsed_resume?: any;
  employer_id?: number;
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

type SortField = 'score' | 'match_percentage' | 'embedding_similarity' | 'full_name' | 'matching_skills_count';
type SortDirection = 'asc' | 'desc';

const JobAnalytics = () => {
  const { id } = useParams<{ id: string }>();
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
          apiService.getJobMatches(id!)
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

  const getMatchPercentageColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading analytics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-destructive mb-4">Error loading analytics: {error}</p>
            <Button onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">No analytics data available</p>
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

  const matchStatusData: ChartData[] = Object.entries(analytics.matches_by_status || {}).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    color: status === 'completed' ? '#10b981' : status === 'pending' ? '#f59e0b' : '#ef4444'
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
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Job Analytics</h1>
          <p className="text-muted-foreground">{analytics.job_title}</p>
          <Badge variant={getStatusVariant(analytics.job_status)} className="mt-2">
            {analytics.job_status.charAt(0).toUpperCase() + analytics.job_status.slice(1)}
          </Badge>
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
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_applications}</div>
            <p className="text-xs text-muted-foreground">
              {analytics.applications_last_7_days} in last 7 days
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Matches</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_matches}</div>
            <p className="text-xs text-muted-foreground">
              {analytics.application_to_match_rate}% conversion rate
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Interviews</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics.total_interviews}</div>
            <p className="text-xs text-muted-foreground">
              {analytics.application_to_interview_rate}% from applications
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Match Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics.average_match_score ? `${(analytics.average_match_score * 100).toFixed(1)}%` : 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              Top: {analytics.top_match_score ? `${(analytics.top_match_score * 100).toFixed(1)}%` : 'N/A'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Candidate Matches Table */}
      <Card>
        <CardHeader>
          <CardTitle>Candidate Matches</CardTitle>
          <CardDescription>
            Detailed view of all candidate matches with scores and skills
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingMatches ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="ml-2">Loading matches...</span>
            </div>
          ) : matches.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No matches found for this job</p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      <Button
                        variant="ghost"
                        onClick={() => handleSort('full_name')}
                        className="h-auto p-0 font-semibold"
                      >
                        Candidate {getSortIcon('full_name')}
                      </Button>
                    </TableHead>
                    <TableHead>
                      <Button
                        variant="ghost"
                        onClick={() => handleSort('score')}
                        className="h-auto p-0 font-semibold"
                      >
                        Overall Score {getSortIcon('score')}
                      </Button>
                    </TableHead>
                    <TableHead>
                      <Button
                        variant="ghost"
                        onClick={() => handleSort('match_percentage')}
                        className="h-auto p-0 font-semibold"
                      >
                        Skill Match {getSortIcon('match_percentage')}
                      </Button>
                    </TableHead>
                    <TableHead>
                      <Button
                        variant="ghost"
                        onClick={() => handleSort('embedding_similarity')}
                        className="h-auto p-0 font-semibold"
                      >
                        Similarity {getSortIcon('embedding_similarity')}
                      </Button>
                    </TableHead>
                    <TableHead>
                      <Button
                        variant="ghost"
                        onClick={() => handleSort('matching_skills_count')}
                        className="h-auto p-0 font-semibold"
                      >
                        Skills Match {getSortIcon('matching_skills_count')}
                      </Button>
                    </TableHead>
                    <TableHead>Matching Skills</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedMatches.map((match) => (
                    <TableRow key={match.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{match.full_name}</div>
                          <div className="text-sm text-muted-foreground">{match.email}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className={`font-semibold ${getScoreColor(match.score)}`}>
                          {(match.score * 100).toFixed(1)}%
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className={`font-semibold ${getMatchPercentageColor(match.match_percentage)}`}>
                          {match.match_percentage.toFixed(1)}%
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">
                          {(match.embedding_similarity * 100).toFixed(1)}%
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">
                          {match.matching_skills_count}/{match.total_required_skills}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {match.matching_skills?.slice(0, 3).map((skill, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {skill}
                            </Badge>
                          ))}
                          {match.matching_skills?.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{match.matching_skills.length - 3} more
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(match.status)}>
                          {match.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Interview Types */}
        {interviewTypeData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Interview Types</CardTitle>
              <CardDescription>Distribution of interview types</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={interviewTypeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="hsl(var(--primary))" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Match Status */}
        {matchStatusData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Match Status</CardTitle>
              <CardDescription>Current status of all matches</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={matchStatusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {matchStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Interview Status */}
        {interviewStatusData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Interview Status</CardTitle>
              <CardDescription>Current status of all interviews</CardDescription>
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
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Candidate Insights */}
        <Card>
          <CardHeader>
            <CardTitle>Candidate Insights</CardTitle>
            <CardDescription>Overview of candidate pool</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Unique Candidates</span>
                <Badge variant="outline">{analytics.unique_candidates}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">With Parsed Resumes</span>
                <Badge variant="outline">
                  {analytics.candidates_with_parsed_resumes}/{analytics.unique_candidates}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Applications (30 days)</span>
                <Badge variant="outline">{analytics.applications_last_30_days}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Skills */}
      {analytics.top_skills_from_candidates && analytics.top_skills_from_candidates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Skills from Candidates</CardTitle>
            <CardDescription>
              Most common skills found in candidate resumes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {analytics.top_skills_from_candidates.map((skill, index) => (
                <Badge key={index} variant="secondary" className="text-sm">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Conversion Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Conversion Metrics</CardTitle>
          <CardDescription>
            Recruitment funnel performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {analytics.application_to_match_rate}%
              </div>
              <p className="text-sm text-muted-foreground">Application → Match</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {analytics.application_to_interview_rate}%
              </div>
              <p className="text-sm text-muted-foreground">Application → Interview</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {analytics.match_to_interview_rate}%
              </div>
              <p className="text-sm text-muted-foreground">Match → Interview</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default JobAnalytics;
