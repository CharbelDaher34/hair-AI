import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";
import { Users, FileText, Mail, Phone, User, Search, Eye, Loader2, XCircle, Calendar, Star, ExternalLink, X } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import apiService from "@/services/api";
import { CandidateTable, CandidateDetails } from "@/types";

const Candidates = () => {
  const navigate = useNavigate();
  const [candidates_data, set_candidates_data] = useState<CandidateTable[]>([]);
  const [loading, set_loading] = useState(true);
  const [error, set_error] = useState<string | null>(null);
  const [search_term, set_search_term] = useState("");
  const [filtered_candidates, set_filtered_candidates] = useState<CandidateTable[]>([]);
  const [selected_candidate, set_selected_candidate] = useState<CandidateDetails | null>(null);
  const [candidate_details_loading, set_candidate_details_loading] = useState(false);
  const [candidate_dialog_open, set_candidate_dialog_open] = useState(false);
  const [resume_pdf_url, set_resume_pdf_url] = useState<string | null>(null);
  const [pdf_loading, set_pdf_loading] = useState(false);
  const [match_dialog_open, set_match_dialog_open] = useState(false);
  const [selected_match, set_selected_match] = useState<any>(null);
  const [match_loading, set_match_loading] = useState(false);

  useEffect(() => {
    const fetch_candidates = async () => {
      try {
        set_loading(true);
        const data = await apiService.getCandidatesTable();
        set_candidates_data(data);
        set_filtered_candidates(data);
        set_error(null);
      } catch (error) {
        console.error("Failed to fetch candidates:", error);
        set_error("Failed to load candidates data");
      } finally {
        set_loading(false);
      }
    };

    fetch_candidates();
  }, []);

  useEffect(() => {
    if (search_term.trim() === "") {
      set_filtered_candidates(candidates_data);
    } else {
      const filtered = candidates_data.filter(
        (candidateTable) =>
          candidateTable.candidate.full_name.toLowerCase().includes(search_term.toLowerCase()) ||
          candidateTable.candidate.email.toLowerCase().includes(search_term.toLowerCase()) ||
          (candidateTable.candidate.phone && candidateTable.candidate.phone.toLowerCase().includes(search_term.toLowerCase()))
      );
      set_filtered_candidates(filtered);
    }
  }, [search_term, candidates_data]);

  const handle_view_candidate = async (candidate_id: number) => {
    try {
      set_candidate_details_loading(true);
      const details = await apiService.getCandidateDetails(candidate_id);
      set_selected_candidate(details);
      set_candidate_dialog_open(true);
    } catch (error) {
      console.error("Failed to fetch candidate details:", error);
    } finally {
      set_candidate_details_loading(false);
    }
  };

  const handle_view_resume = async (candidate_id: number) => {
    set_pdf_loading(true);
    try {
      const blob = await apiService.getCandidateResume(candidate_id);
      const pdf_blob = new Blob([blob], { type: 'application/pdf' });
      const pdf_url = URL.createObjectURL(pdf_blob);
      set_resume_pdf_url(pdf_url);
    } catch (error) {
      console.error('Error fetching resume:', error);
      alert('Failed to load resume. Please try again.');
    } finally {
      set_pdf_loading(false);
    }
  };

  const handle_close_pdf = () => {
    if (resume_pdf_url) {
      URL.revokeObjectURL(resume_pdf_url);
      set_resume_pdf_url(null);
    }
  };

  const handle_view_match = async (match: any) => {
    if (!match) {
      alert('No match data available for this application.');
      return;
    }
    set_selected_match(match);
    set_match_dialog_open(true);
  };

  // Cleanup object URL on component unmount
  useEffect(() => {
    return () => {
      if (resume_pdf_url) {
        URL.revokeObjectURL(resume_pdf_url);
      }
    };
  }, [resume_pdf_url]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <p className="text-lg font-medium text-gray-700">Loading candidates...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center h-screen">
        <Card className="w-full max-w-md shadow-2xl border-0">
          <CardContent className="text-center p-10 space-y-5">
            <XCircle className="h-16 w-16 text-red-500 mx-auto" />
            <h2 className="text-2xl font-bold text-gray-800">Error Loading Candidates</h2>
            <p className="text-gray-600">{error}</p>
            <Button 
              onClick={() => window.location.reload()} 
              className="button shadow-lg hover:shadow-xl transition-all duration-300 w-full"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Candidates
          </h1>
          <p className="text-lg text-gray-600">
            Manage and review all candidates in your talent pool.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search candidates..."
              value={search_term}
              onChange={(e) => set_search_term(e.target.value)}
              className="pl-10 w-64 shadow-md border-gray-300 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {/* <div className="grid gap-6 md:grid-cols-3">
        <Card className="card hover:scale-105 transition-all duration-300 border-0 shadow-lg hover:shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">Total Candidates</CardTitle>
            <div className="p-2 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg">
              <Users className="h-5 w-5 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-800">{candidates_data.length}</div>
            <p className="text-xs text-gray-600 mt-1">
              {filtered_candidates.length !== candidates_data.length && 
                `${filtered_candidates.length} shown after filtering`
              }
            </p>
          </CardContent>
        </Card>

        <Card className="card hover:scale-105 transition-all duration-300 border-0 shadow-lg hover:shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">With Resumes</CardTitle>
            <div className="p-2 bg-gradient-to-br from-green-100 to-emerald-100 rounded-lg">
              <FileText className="h-5 w-5 text-green-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-800">
              {candidates_data.filter(c => c.candidate.resume_url).length}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {((candidates_data.filter(c => c.candidate.resume_url).length / candidates_data.length) * 100).toFixed(1)}% of total
            </p>
          </CardContent>
        </Card>

        <Card className="card hover:scale-105 transition-all duration-300 border-0 shadow-lg hover:shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">With Applications</CardTitle>
            <div className="p-2 bg-gradient-to-br from-orange-100 to-amber-100 rounded-lg">
              <User className="h-5 w-5 text-orange-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-800">
              {candidates_data.filter(c => c.applications_count > 0).length}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Active in recruitment process
            </p>
          </CardContent>
        </Card>
      </div> */}

      {/* Candidates Table */}
      <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
        <CardHeader className="pb-4">
          <CardTitle className="text-xl font-bold text-gray-800 flex items-center gap-3">
            <Users className="h-6 w-6 text-blue-600" />
            All Candidates
          </CardTitle>
          <CardDescription className="text-base text-gray-600">
            {filtered_candidates.length} candidate{filtered_candidates.length !== 1 ? 's' : ''} 
            {search_term && ` matching "${search_term}"`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filtered_candidates.length > 0 ? (
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50 hover:bg-gray-50">
                    <TableHead className="font-semibold text-gray-700">Name</TableHead>
                    <TableHead className="font-semibold text-gray-700">Email</TableHead>
                    <TableHead className="font-semibold text-gray-700">Phone</TableHead>
                    <TableHead className="font-semibold text-gray-700">Resume</TableHead>
                    <TableHead className="font-semibold text-gray-700">Applications</TableHead>
                    <TableHead className="font-semibold text-gray-700">Date Added</TableHead>
                    <TableHead className="font-semibold text-gray-700 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered_candidates.map((candidateTable) => (
                    <TableRow key={candidateTable.candidate.id} className="hover:bg-slate-50 transition-colors">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center">
                            <User className="h-5 w-5 text-blue-600" />
                          </div>
                          <div>
                            <p className="font-semibold text-gray-800">{candidateTable.candidate.full_name}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-700">{candidateTable.candidate.email}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {candidateTable.candidate.phone ? (
                          <div className="flex items-center gap-2">
                            <Phone className="h-4 w-4 text-gray-400" />
                            <span className="text-gray-700">{candidateTable.candidate.phone}</span>
                          </div>
                        ) : (
                          <span className="text-gray-400 italic">No phone</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {candidateTable.candidate.resume_url ? (
                          <Badge variant="secondary" className="bg-green-100 text-green-700 border-green-200">
                            <FileText className="h-3 w-3 mr-1" />
                            Available
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-gray-500 border-gray-300">
                            None
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-semibold">
                          {candidateTable.applications_count}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-gray-600">
                          {new Date(candidateTable.candidate.created_at).toLocaleDateString()}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handle_view_candidate(candidateTable.candidate.id)}
                            className="button-outline shadow-sm hover:shadow-md transition-all duration-300"
                            disabled={candidate_details_loading}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            View Details
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-center">
              <div className="space-y-3">
                <Users className="h-16 w-16 text-gray-300 mx-auto" />
                <h3 className="text-lg font-semibold text-gray-600">
                  {search_term ? "No candidates match your search" : "No candidates found"}
                </h3>
                <p className="text-gray-500">
                  {search_term 
                    ? "Try adjusting your search terms or clear the search to see all candidates."
                    : "Candidates will appear here once they start applying to your jobs."
                  }
                </p>
                {search_term && (
                  <Button
                    variant="outline"
                    onClick={() => set_search_term("")}
                    className="mt-3"
                  >
                    Clear Search
                  </Button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Candidate Details Dialog */}
      <Dialog open={candidate_dialog_open} onOpenChange={set_candidate_dialog_open}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {candidate_details_loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <span className="ml-2">Loading candidate details...</span>
            </div>
          ) : selected_candidate ? (
            <>
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold text-gray-800">
                  {selected_candidate.full_name}
                </DialogTitle>
                <DialogDescription className="text-gray-600">
                  Candidate profile and application history
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-6 mt-4">
                {/* Contact Information */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <User className="h-5 w-5 text-blue-600" />
                      Contact Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <Label className="text-sm font-semibold text-gray-700">Email</Label>
                        <div className="flex items-center gap-2 mt-1 p-2 bg-slate-100 rounded-md">
                          <Mail className="h-4 w-4 text-blue-600" />
                          <span className="text-gray-800">{selected_candidate.email}</span>
                        </div>
                      </div>
                      <div>
                        <Label className="text-sm font-semibold text-gray-700">Phone</Label>
                        <div className="flex items-center gap-2 mt-1 p-2 bg-slate-100 rounded-md">
                          <Phone className="h-4 w-4 text-blue-600" />
                          <span className="text-gray-800">
                            {selected_candidate.phone || "Not provided"}
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    {selected_candidate.resume_url && (
                      <div>
                        <Label className="text-sm font-semibold text-gray-700">Resume</Label>
                        <div className="flex items-center gap-2 mt-1">
                          <Button 
                            variant="link"
                            className="p-0 h-auto text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1"
                            onClick={() => handle_view_resume(selected_candidate.id)}
                            disabled={pdf_loading}
                          >
                            {pdf_loading ? (
                              <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Loading...
                              </>
                            ) : (
                              <>
                                <FileText className="h-4 w-4" />
                                View Resume
                                <ExternalLink className="h-4 w-4 ml-1" />
                              </>
                            )}
                          </Button>
                        </div>
                      </div>
                    )}

                    {/* PDF Viewer */}
                    {resume_pdf_url && (
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="flex items-center justify-between mb-3">
                          <Label className="text-lg font-semibold text-gray-800">Resume Preview</Label>
                          <Button 
                            variant="outline" 
                            size="icon"
                            onClick={handle_close_pdf}
                            className="rounded-full"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                        <div className="border border-gray-300 rounded-lg overflow-hidden bg-gray-50">
                          <object
                            data={resume_pdf_url}
                            type="application/pdf"
                            width="100%"
                            height="500px"
                            className="border-0"
                          >
                            <div className="flex items-center justify-center h-96 text-center p-4">
                              <div>
                                <p className="text-muted-foreground mb-2">
                                  Unable to display PDF in browser.
                                </p>
                                <Button 
                                  variant="outline" 
                                  onClick={() => {
                                    const link = document.createElement('a');
                                    link.href = resume_pdf_url;
                                    link.download = `${selected_candidate.full_name}_resume.pdf`;
                                    link.click();
                                  }}
                                >
                                  Download PDF
                                </Button>
                              </div>
                            </div>
                          </object>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Applications */}
                {selected_candidate.applications.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5 text-blue-600" />
                        Applications ({selected_candidate.applications.length})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {selected_candidate.applications.map((application) => (
                          <div key={application.id} className="p-4 border border-gray-200 rounded-lg hover:bg-slate-50">
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <h4 className="font-semibold text-gray-800">
                                  {application.job?.title || "Unknown Job"}
                                </h4>
                                <p className="text-sm text-gray-600">
                                  Applied on {new Date(application.created_at).toLocaleDateString()}
                                </p>
                                {application.matches && application.matches.length > 0 && (
                                  <div className="mt-2">
                                    <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                                      <Star className="h-3 w-3 mr-1" />
                                      Match: {(application.matches[0].score * 100).toFixed(1)}%
                                    </Badge>
                                  </div>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="capitalize">
                                  {application.status}
                                </Badge>
                                {application.matches && application.matches.length > 0 && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handle_view_match(application.matches[0])}
                                    className="button-outline shadow-sm hover:shadow-md transition-all duration-300"
                                  >
                                    <Star className="h-4 w-4 mr-1" />
                                    Match
                                  </Button>
                                )}
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => {
                                    set_candidate_dialog_open(false);
                                    navigate(`/applications/${application.id}`);
                                  }}
                                >
                                  <Eye className="h-4 w-4 mr-1" />
                                  View
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Interviews */}
                {selected_candidate.applications.some(app => app.interviews && app.interviews.length > 0) && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-blue-600" />
                        Interviews ({selected_candidate.applications.reduce((total, app) => total + (app.interviews?.length || 0), 0)})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {selected_candidate.applications.flatMap(app => app.interviews || []).map((interview) => (
                          <div key={interview.id} className="p-4 border border-gray-200 rounded-lg">
                            <div className="flex items-center justify-between">
                              <div>
                                <h4 className="font-semibold text-gray-800">
                                  {interview.type} Interview
                                </h4>
                                <p className="text-sm text-gray-600">
                                  {new Date(interview.date).toLocaleString()}
                                </p>
                                {interview.notes && (
                                  <p className="text-sm text-gray-700 mt-1">{interview.notes}</p>
                                )}
                              </div>
                              <Badge variant="outline" className="capitalize">
                                {interview.status}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Parsed Resume Data */}
                {selected_candidate.parsed_resume && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Star className="h-5 w-5 text-yellow-500" />
                        Parsed Resume Data
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {/* Skills */}
                        {(selected_candidate.parsed_resume as any)?.skills && (
                          <div>
                            <Label className="text-sm font-semibold text-gray-700">Skills</Label>
                            <div className="flex flex-wrap gap-2 mt-2">
                              {(selected_candidate.parsed_resume as any).skills.map((skill: any, index: number) => (
                                <Badge key={index} variant="secondary" className="bg-blue-100 text-blue-700">
                                  {typeof skill === 'string' ? skill : skill.name}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Work History */}
                        {(selected_candidate.parsed_resume as any)?.work_history && (
                          <div>
                            <Label className="text-sm font-semibold text-gray-700">Work History</Label>
                            <div className="mt-2 space-y-3">
                              {(selected_candidate.parsed_resume as any).work_history.map((job: any, index: number) => (
                                <div key={index} className="p-3 bg-slate-100 rounded-md">
                                  <h4 className="font-semibold text-gray-800">{job.job_title} at {job.employer}</h4>
                                  <p className="text-sm text-gray-600">
                                    {job.start_date} - {job.end_date || "Present"} | {job.location}
                                  </p>
                                  {job.summary && <p className="text-sm text-gray-700 mt-1">{job.summary}</p>}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Education */}
                        {(selected_candidate.parsed_resume as any)?.education && (
                          <div>
                            <Label className="text-sm font-semibold text-gray-700">Education</Label>
                            <div className="mt-2 space-y-3">
                              {(selected_candidate.parsed_resume as any).education.map((edu: any, index: number) => (
                                <div key={index} className="p-3 bg-slate-100 rounded-md">
                                  <h4 className="font-semibold text-gray-800">
                                    {edu.degree_type} in {edu.subject}
                                  </h4>
                                  <p className="text-sm text-gray-600">
                                    {edu.institution} ({edu.start_date} - {edu.end_date || "Present"})
                                  </p>
                                  {edu.gpa && <p className="text-sm text-gray-700">GPA: {edu.gpa}</p>}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Match Details Dialog */}
      <Dialog open={match_dialog_open} onOpenChange={set_match_dialog_open}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <Star className="h-6 w-6 text-yellow-500" />
              Match Analysis
            </DialogTitle>
            <DialogDescription className="text-gray-600">
              Detailed matching analysis for this application
            </DialogDescription>
          </DialogHeader>

          {selected_match && (
            <div className="space-y-6 mt-4">
              {/* Overall Score */}
              <div className="text-center p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
                <Label className="text-sm font-semibold text-gray-700 block mb-2">Overall Match Score</Label>
                <Badge variant="outline" className="font-bold text-2xl text-green-600 border-green-300 bg-green-50 px-4 py-2">
                  {selected_match.score ? (selected_match.score * 100).toFixed(1) : 'N/A'}%
                </Badge>
                <div className="text-sm text-gray-600 mt-2 space-x-4">
                  {selected_match.overall_embedding_similarity && (
                    <span>
                      Overall Similarity: {(selected_match.overall_embedding_similarity * 100).toFixed(1)}%
                    </span>
                  )}
                   {selected_match.skills_embedding_similarity && (
                    <span>
                      Skills Similarity: {(selected_match.skills_embedding_similarity * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>

              {/* Skills Analysis */}
              <div className="grid gap-4 md:grid-cols-3">
                {/* Matching Skills */}
                {selected_match.matching_skills && selected_match.matching_skills.length > 0 && (
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <Label className="text-sm font-semibold text-green-700 block mb-2">
                      Matching Skills ({selected_match.matching_skills.length})
                    </Label>
                    <div className="flex flex-wrap gap-1">
                      {selected_match.matching_skills.map((skill: string, index: number) => (
                        <Badge key={index} variant="secondary" className="bg-green-100 text-green-700 border-green-200 text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Missing Skills */}
                {selected_match.missing_skills && selected_match.missing_skills.length > 0 && (
                  <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                    <Label className="text-sm font-semibold text-red-700 block mb-2">
                      Missing Skills ({selected_match.missing_skills.length})
                    </Label>
                    <div className="flex flex-wrap gap-1">
                      {selected_match.missing_skills.map((skill: string, index: number) => (
                        <Badge key={index} variant="secondary" className="bg-red-100 text-red-700 border-red-200 text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Extra Skills */}
                {selected_match.extra_skills && selected_match.extra_skills.length > 0 && (
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <Label className="text-sm font-semibold text-blue-700 block mb-2">
                      Additional Skills ({selected_match.extra_skills.length})
                    </Label>
                    <div className="flex flex-wrap gap-1">
                      {selected_match.extra_skills.map((skill: string, index: number) => (
                        <Badge key={index} variant="secondary" className="bg-blue-100 text-blue-700 border-blue-200 text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Score Breakdown */}
              {selected_match.score_breakdown && (
                <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <Label className="text-sm font-semibold text-gray-700 block mb-3">Score Breakdown</Label>
                  <div className="grid gap-4 md:grid-cols-2">
                    {selected_match.score_breakdown.final_score_components && (
                      <div>
                        <h4 className="font-medium text-gray-800 mb-2">Final Score Components</h4>
                        <div className="space-y-1">
                          {Object.entries(selected_match.score_breakdown.final_score_components).map(([key, value]: [string, any]) => (
                            <div key={key} className="flex justify-between items-center p-2 bg-white rounded border">
                              <span className="text-sm font-medium text-gray-700 capitalize">
                                {key.replace(/_/g, ' ')}
                              </span>
                              <span className="text-sm font-bold text-gray-800">
                                {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {selected_match.score_breakdown.skills_score_components && (
                      <div>
                        <h4 className="font-medium text-gray-800 mb-2">Skills Score Components</h4>
                        <div className="space-y-1">
                          {Object.entries(selected_match.score_breakdown.skills_score_components).map(([key, value]: [string, any]) => (
                            <div key={key} className="flex justify-between items-center p-2 bg-white rounded border">
                              <span className="text-sm font-medium text-gray-700 capitalize">
                                {key.replace(/_/g, ' ')}
                              </span>
                              <span className="text-sm font-bold text-gray-800">
                                {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Weights Used */}
              {selected_match.weights_used && (
                <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <Label className="text-sm font-semibold text-yellow-700 block mb-3">Matching Weights</Label>
                   <div className="grid gap-4 md:grid-cols-2">
                    {selected_match.weights_used.final_weights && (
                      <div>
                        <h4 className="font-medium text-yellow-800 mb-2">Final Weights</h4>
                        <div className="space-y-1">
                          {Object.entries(selected_match.weights_used.final_weights).map(([key, value]: [string, any]) => (
                            <div key={key} className="flex justify-between items-center p-2 bg-white rounded border">
                              <span className="text-sm font-medium text-gray-700 capitalize">
                                {key.replace(/_/g, ' ')}
                              </span>
                              <span className="text-sm font-bold text-gray-800">
                                {typeof value === 'number' ? value.toFixed(2) : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {selected_match.weights_used.skill_weights && (
                       <div>
                        <h4 className="font-medium text-yellow-800 mb-2">Skill Weights</h4>
                        <div className="space-y-1">
                          {Object.entries(selected_match.weights_used.skill_weights).map(([key, value]: [string, any]) => (
                            <div key={key} className="flex justify-between items-center p-2 bg-white rounded border">
                              <span className="text-sm font-medium text-gray-700 capitalize">
                                {key.replace(/_/g, ' ')}
                              </span>
                              <span className="text-sm font-bold text-gray-800">
                                {typeof value === 'number' ? value.toFixed(2) : String(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Flags */}
              {selected_match.flags && Object.keys(selected_match.flags).length > 0 && (
                <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <Label className="text-sm font-semibold text-purple-700 block mb-3">Match Flags</Label>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(selected_match.flags).map(([key, value]: [string, any]) => (
                      <Badge key={key} variant="outline" className={`text-xs ${
                        value ? 'bg-purple-100 text-purple-700 border-purple-200' : 'bg-gray-100 text-gray-600 border-gray-200'
                      }`}>
                        {key.replace(/_/g, ' ')}: {String(value)}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Candidates; 