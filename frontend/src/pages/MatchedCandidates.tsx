import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CheckCircle, XCircle, Eye, Star, Filter, Users, Briefcase, Search, ChevronDown, Loader2, Info } from "lucide-react";
import { useParams, Link, useNavigate } from "react-router-dom";
import apiService from "@/services/api";
import { toast } from "@/components/ui/sonner";

// Interfaces based on your existing structure and potential API responses
interface Candidate {
  id: number;
  full_name: string;
  email: string;
  phone?: string;
  resume_url?: string;
  parsed_resume?: any;
  employer_id?: number;
}

interface Job {
  id: number;
  title: string;
  description: string;
  status: string;
}

interface MatchedCandidateData {
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
  matches: MatchedCandidateData[];
  job: Job;
}

const MatchedCandidatesPage = () => {
  const { id: job_id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  console.log("MatchedCandidatesPage mounted, job_id:", job_id);

  const [job, set_job] = useState<Job | null>(null);
  const [candidates, set_candidates] = useState<MatchedCandidateData[]>([]);
  const [is_loading, set_is_loading] = useState(true);
  const [error, set_error] = useState<string | null>(null);

  const [score_threshold, set_score_threshold] = useState([70]);
  const [search_term, set_search_term] = useState("");

  useEffect(() => {
    console.log("useEffect triggered, job_id:", job_id);
    const fetch_matched_candidates = async () => {
      if (!job_id) {
        console.log("No job_id, returning early");
        return;
      }
      console.log("Starting API call for job_id:", job_id);
      set_is_loading(true);
      set_error(null);
      try {
        console.log("Calling apiService.getJobMatches with job_id:", job_id);
        const data: JobMatchesResponse = await apiService.getJobMatches(job_id);
        console.log("API response:", data);
        
        if (data && data.job) {
          set_job(data.job);
          set_candidates(data.matches || []);
          console.log("Set job and candidates:", data.job, data.matches);
        } else {
          console.log("No data.job, trying to fetch job details separately");
          // If no data, try to fetch job details separately
          try {
            const job_details = await apiService.getJob(job_id);
            console.log("Job details:", job_details);
            set_job(job_details);
            set_candidates([]);
          } catch (job_error) {
            console.error("Failed to fetch job details:", job_error);
            set_job(null);
            set_candidates([]);
            toast.error("Job details not found.");
          }
        }
      } catch (err: any) {
        console.error("Failed to load matched candidates:", err);
        set_error(err.message || "Failed to load candidates.");
        toast.error("Failed to load matched candidates", { description: err.message });
      } finally {
        set_is_loading(false);
        console.log("Loading finished");
      }
    };
    fetch_matched_candidates();
  }, [job_id]);

  const filtered_candidates = candidates
    .filter(mc => (mc.score * 100) >= score_threshold[0])
    .filter(mc => 
      mc.full_name.toLowerCase().includes(search_term.toLowerCase()) ||
      mc.email.toLowerCase().includes(search_term.toLowerCase())
    );

  const get_score_color_class = (score: number) => {
    const actual_score = score * 100;
    if (actual_score >= 90) return "text-green-600 font-bold";
    if (actual_score >= 80) return "text-blue-600 font-semibold";
    if (actual_score >= 70) return "text-yellow-600 font-medium";
    return "text-red-600";
  };
  
  if (is_loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-8">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <p className="text-lg font-medium text-gray-700">Loading matched candidates...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-8">
        <Card className="w-full max-w-md shadow-2xl border-0 text-center">
          <CardHeader>
            <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <CardTitle className="text-3xl font-bold text-gray-800">Error Loading Data</CardTitle>
            <CardDescription className="text-lg text-gray-600 mt-2">{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate(0)} className="button shadow-lg hover:shadow-xl transition-all duration-300 w-full">
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Matched Candidates
          </h1>
          <p className="text-lg text-gray-600 flex items-center gap-2">
            <Briefcase className="h-5 w-5 text-blue-500" /> 
            {job?.title || "Loading job title..."} 
            <span className="text-sm text-gray-500">({filtered_candidates.length} of {candidates.length} shown)</span>
          </p>
        </div>
        <Button variant="outline" asChild className="button-outline shadow-md hover:shadow-lg transition-all duration-300">
          <Link to={`/jobs/${job_id}/details`}>
            <Eye className="mr-2 h-4 w-4" />
            View Job Details
          </Link>
        </Button>
      </div>

      {/* Filters Card */}
      <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
            <Filter className="h-6 w-6 text-blue-600" />
            Filter Candidates
          </CardTitle>
           <CardDescription className="text-base text-gray-600">
            Refine the list of candidates based on match score.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
          <div className="space-y-2">
            <Label htmlFor="search_term" className="text-sm font-semibold text-gray-700">Search by Name/Email</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input 
                id="search_term"
                placeholder="Search candidates..."
                value={search_term}
                onChange={(e) => set_search_term(e.target.value)}
                className="h-12 pl-10 bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="score_threshold" className="text-sm font-semibold text-gray-700">Minimum Match Score: <span className="font-bold text-blue-600">{score_threshold[0]}%</span></Label>
            <Slider
              id="score_threshold"
              value={score_threshold}
              onValueChange={set_score_threshold}
              max={100}
              min={0}
              step={5}
              className="[&>.slider-track]:bg-blue-200 [&>.slider-range]:bg-gradient-to-r from-blue-500 to-purple-500 [&>.slider-thumb]:bg-white [&>.slider-thumb]:border-purple-600"
            />
          </div>
        </CardContent>
      </Card>

      {/* Candidates Table/List */}
      {filtered_candidates.length > 0 ? (
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0 overflow-hidden">
          <CardHeader>
             <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <Users className="h-6 w-6 text-blue-600" />
                Candidate List
            </CardTitle>
            <CardDescription className="text-base text-gray-600">
                Review and manage candidates matched for this job.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Candidate</TableHead>
                  <TableHead className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Match Score</TableHead>
                  <TableHead className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody className="divide-y divide-gray-200">
                {filtered_candidates.map((mc) => (
                  <TableRow key={mc.id} className="hover:bg-slate-100 transition-colors duration-150">
                    <TableCell className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 flex-shrink-0 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                          {mc.full_name.charAt(0).toUpperCase()}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-semibold text-gray-900">{mc.full_name}</div>
                          <div className="text-xs text-gray-500">{mc.email}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-lg ${get_score_color_class(mc.score)}`}>
                        {(mc.score * 100).toFixed(1)}%
                      </div>
                      {mc.matching_skills_count !== undefined && mc.total_required_skills !== undefined && (
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button variant="link" size="sm" className="p-0 h-auto text-xs text-gray-500 hover:text-blue-600">
                              ({mc.matching_skills_count}/{mc.total_required_skills} skills matched)
                              <Info className="ml-1 h-3 w-3" />
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-64 text-sm p-3 space-y-2 bg-white shadow-xl rounded-lg border border-gray-200">
                            {mc.matching_skills && mc.matching_skills.length > 0 && 
                              <div><strong className="font-semibold text-green-600">Matched Skills:</strong> {mc.matching_skills.join(", ")}</div>
                            }
                            {mc.missing_skills && mc.missing_skills.length > 0 && 
                              <div><strong className="font-semibold text-red-600">Missing Skills:</strong> {mc.missing_skills.join(", ")}</div>
                            }
                            {mc.extra_skills && mc.extra_skills.length > 0 && 
                              <div><strong className="font-semibold text-blue-600">Extra Skills:</strong> {mc.extra_skills.join(", ")}</div>
                            }
                            {(!mc.matching_skills || mc.matching_skills.length === 0) && 
                             (!mc.missing_skills || mc.missing_skills.length === 0) &&
                             (!mc.extra_skills || mc.extra_skills.length === 0) &&
                              <p className="text-gray-500 italic">No detailed skill info available.</p> }
                          </PopoverContent>
                        </Popover>
                      )}
                    </TableCell>
                    <TableCell className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded-full p-2 transition-all duration-150"
                        onClick={() => navigate(`/applications/${mc.application_id}`)}
                        disabled={!mc.application_id}
                        title="View Application"
                      >
                        <Eye className="h-5 w-5" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          {filtered_candidates.length > 5 && (
            <CardFooter className="py-4 px-6 border-t border-gray-200 bg-slate-50">
              <p className="text-sm text-gray-600">Showing {filtered_candidates.length} candidates.</p>
              {/* Add pagination if necessary */}
            </CardFooter>
          )}
        </Card>
      ) : (
        <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
          <CardContent className="text-center py-16 px-8">
            <Search className="h-16 w-16 text-gray-400 mx-auto mb-6 animate-pulse" />
            <h3 className="text-2xl font-semibold text-gray-800 mb-2">No Candidates Match Your Criteria</h3>
            <p className="text-gray-600 mb-6">
              Try adjusting your filters or check back later as new candidates apply.
            </p>
            <Button 
              variant="outline"
              onClick={() => {
                set_search_term("");
                set_score_threshold([0]);
              }}
              className="button-outline shadow-md hover:shadow-lg transition-all duration-300"
            >
              Clear All Filters
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MatchedCandidatesPage;
