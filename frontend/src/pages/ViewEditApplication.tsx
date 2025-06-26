import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { FileText, Mail, Phone, User, Calendar, Star, ExternalLink, X, Loader2, XCircle, MessageSquare, Edit3, Save, Users } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";
import apiService from "@/services/api";
import { ApplicationStatus } from "@/types";
import { toast } from "@/hooks/use-toast";

interface Interview {
  id: number;
  application_id: number;
  date: string;
  type: string;
  status: string;
  notes?: string | null;
  interviewer_review?: string | null;
  created_at: string;
  updated_at: string;
  interviewer?: {
    id: number;
    full_name: string;
    email: string;
  };
}

const ViewApplication = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [application_data, set_application_data] = useState<any>(null);
  const [loading, set_loading] = useState(true);
  const [resume_pdf_url, set_resume_pdf_url] = useState<string | null>(null);
  const [pdf_loading, set_pdf_loading] = useState(false);
  
  // Interview-related state
  const [interviews, set_interviews] = useState<Interview[]>([]);
  const [interviews_loading, set_interviews_loading] = useState(false);
  const [editing_review, set_editing_review] = useState<number | null>(null);
  const [review_text, set_review_text] = useState<string>("");
  const [saving_review, set_saving_review] = useState(false);

  useEffect(() => {
    const fetch_application = async () => {
      set_loading(true);
      try {
        const data = await apiService.getApplicationWithDetails(id);
        set_application_data(data);
      } catch (error) {
        // Optionally handle error
      } finally {
        set_loading(false);
      }
    };
    fetch_application();
  }, [id]);

  // Fetch interviews for the application
  useEffect(() => {
    const fetch_interviews = async () => {
      if (!id) return;
      
      set_interviews_loading(true);
      try {
        const interviews_data = await apiService.getInterviewsByApplication(parseInt(id));
        set_interviews(interviews_data);
      } catch (error) {
        console.error('Error fetching interviews:', error);
      } finally {
        set_interviews_loading(false);
      }
    };
    
    fetch_interviews();
  }, [id]);

  const handle_view_resume = async () => {
    if (!application_data.candidate?.id) return;
    
    set_pdf_loading(true);
    try {
      const blob = await apiService.getCandidateResume(application_data.candidate.id);
      
      // Ensure the blob has the correct MIME type
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

  // Cleanup object URL on component unmount
  useEffect(() => {
    return () => {
      if (resume_pdf_url) {
        URL.revokeObjectURL(resume_pdf_url);
      }
    };
  }, [resume_pdf_url]);

  const get_status_variant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status?.toLowerCase()) {
      case "hired":
        return "default";
      case "interviewing":
        return "secondary";
      case "rejected":
        return "destructive";
      case "offer_sent":
        return "secondary";
      case "reviewing":
      case "pending":
      default:
        return "outline";
    }
  };

  const handle_edit_review = (interview_id: number, current_review: string) => {
    set_editing_review(interview_id);
    set_review_text(current_review || "");
  };

  const handle_save_review = async (interview_id: number) => {
    set_saving_review(true);
    try {
      await apiService.updateInterviewerReview(interview_id, review_text);
      
      // Update the local state
      set_interviews(prev => prev.map(interview => 
        interview.id === interview_id 
          ? { ...interview, interviewer_review: review_text }
          : interview
      ));
      
      set_editing_review(null);
      set_review_text("");
      
      toast({
        title: "Success",
        description: "Interviewer review updated successfully",
      });
    } catch (error) {
      console.error('Error saving review:', error);
      toast({
        title: "Error",
        description: "Failed to save interviewer review",
        variant: "destructive",
      });
    } finally {
      set_saving_review(false);
    }
  };

  const handle_cancel_edit = () => {
    set_editing_review(null);
    set_review_text("");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-8">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <p className="text-lg font-medium text-gray-700">Loading application details...</p>
        </div>
      </div>
    );
  }
  
  if (!application_data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-8">
        <Card className="w-full max-w-md shadow-2xl border-0">
          <CardContent className="text-center p-10 space-y-5">
            <XCircle className="h-16 w-16 text-red-500 mx-auto" />
            <h2 className="text-2xl font-bold text-gray-800">Application Not Found</h2>
            <p className="text-gray-600">
              The application you are looking for does not exist or could not be loaded.
            </p>
            <Button 
              onClick={() => navigate("/applications")} 
              className="button shadow-lg hover:shadow-xl transition-all duration-300 w-full"
            >
              Back to Applications
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Helper to safely get parsed_resume
  let parsed_resume = undefined;
  try {
    parsed_resume = application_data.candidate?.parsed_resume;
    if (!parsed_resume || typeof parsed_resume !== 'object') {
      parsed_resume = undefined;
    }
  } catch {
    parsed_resume = undefined;
  }

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Application Details
          </h1>
          <p className="text-lg text-gray-600">
            {application_data.candidate?.full_name} for {application_data.job?.title}
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate("/applications")} className="shadow-md hover:shadow-lg transition-all duration-300">
          Back to Applications
        </Button>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <User className="h-6 w-6 text-blue-600" />
                Candidate Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 pt-4">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-1">
                  <Label className="text-sm font-semibold text-gray-700">Full Name</Label>
                  <div className="flex items-center gap-2 mt-1 p-3 bg-slate-100 rounded-md">
                    <User className="h-4 w-4 text-blue-600" />
                    <span className="text-gray-800 font-medium">{application_data.candidate?.full_name || "N/A"}</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-sm font-semibold text-gray-700">Email</Label>
                  <div className="flex items-center gap-2 mt-1 p-3 bg-slate-100 rounded-md">
                    <Mail className="h-4 w-4 text-blue-600" />
                    <span className="text-gray-800 font-medium">{application_data.candidate?.email || "N/A"}</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-sm font-semibold text-gray-700">Phone</Label>
                  <div className="flex items-center gap-2 mt-1 p-3 bg-slate-100 rounded-md">
                    <Phone className="h-4 w-4 text-blue-600" />
                    <span className="text-gray-800 font-medium">{application_data.candidate?.phone || "N/A"}</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-sm font-semibold text-gray-700">Resume</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <FileText className="h-5 w-5 text-blue-600" />
                    {application_data.candidate?.id && (
                      <Button 
                        variant="link"
                        className="p-0 h-auto text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1 text-base font-medium"
                        onClick={handle_view_resume}
                        disabled={pdf_loading}
                      >
                        {pdf_loading ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Loading...
                          </>
                        ) : (
                          <>
                            View Resume
                            <ExternalLink className="h-4 w-4 ml-1" />
                          </>
                        )}
                      </Button>
                    )}
                    {!application_data.candidate?.id && application_data.candidate?.resume_url && (
                       <a 
                         href={application_data.candidate?.resume_url} 
                         target="_blank" 
                         rel="noopener noreferrer"
                         className="text-blue-600 hover:text-blue-700 hover:underline flex items-center gap-1 text-base font-medium"
                       >
                         View Resume (URL)
                         <ExternalLink className="h-4 w-4 ml-1" /> 
                       </a>
                    )}
                    {!(application_data.candidate?.id || application_data.candidate?.resume_url) && (
                        <span className="text-gray-600 italic">No resume available</span>
                    )}
                  </div>
                </div>
              </div>

              {/* PDF Viewer Section */}
              {resume_pdf_url && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <Label className="text-lg font-semibold text-gray-800">Resume Preview</Label>
                    <Button 
                      variant="outline" 
                      size="icon"
                      onClick={handle_close_pdf}
                      className="button-outline rounded-full shadow-md hover:shadow-lg transition-all duration-300"
                    >
                      <X className="h-5 w-5" />
                    </Button>
                  </div>
                  <div className="border border-gray-300 rounded-lg overflow-hidden bg-gray-50 shadow-inner">
                    <object
                      data={resume_pdf_url}
                      type="application/pdf"
                      width="100%"
                      height="600px"
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
                              link.download = `${application_data.candidate?.name || 'candidate'}_resume.pdf`;
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

              <Separator />

              {/* Parsed Resume Section - only if valid */}
              {parsed_resume && (
                <div>
                  <Label>Parsed Resume Summary</Label>
                  <div className="mt-2 space-y-3">
                    {/* Skills */}
                    {Array.isArray(parsed_resume.skills) && parsed_resume.skills.length > 0 && (
                      <div>
                        <span className="font-medium">Skills:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {parsed_resume.skills.map((skill: any, idx: number) => (
                            <Badge key={idx} variant="secondary">
                              {typeof skill === 'string' ? skill : skill.name}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {/* Education */}
                    {Array.isArray(parsed_resume.education) && parsed_resume.education.length > 0 && (
                      <div>
                        <span className="font-medium">Education:</span>
                        <div className="mt-1 space-y-2">
                          {parsed_resume.education.map((edu: any, idx: number) => (
                            <div key={idx} className="mb-2 p-2 bg-muted rounded">
                              <div>
                                <b>{edu.level}</b> - {edu.degree_type} in {edu.subject}
                              </div>
                              <div>
                                {edu.institution} ({edu.start_date} - {edu.end_date || "Present"})
                              </div>
                              {edu.gpa && <div>GPA: {edu.gpa}</div>}
                              {edu.summary && <div>{edu.summary}</div>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {/* Work History */}
                    {Array.isArray(parsed_resume.work_history) && parsed_resume.work_history.length > 0 && (
                      <div>
                        <span className="font-medium">Work History:</span>
                        <div className="mt-1 space-y-2">
                          {parsed_resume.work_history.map((job: any, idx: number) => (
                            <div key={idx} className="mb-2 p-2 bg-muted rounded">
                              <div>
                                <b>{job.job_title}</b> at {job.employer} ({job.start_date} - {job.end_date || "Present"})
                              </div>
                              <div>{job.location} | {job.employment_type}</div>
                              <div>{job.summary}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {/* Certifications */}
                    {Array.isArray(parsed_resume.certifications) && parsed_resume.certifications.length > 0 && (
                      <div>
                        <span className="font-medium">Certifications:</span>
                        <div className="mt-1 space-y-2">
                          {parsed_resume.certifications.map((cert: any, idx: number) => (
                            <div key={idx} className="mb-2 p-2 bg-muted rounded">
                              <div>
                                <b>{cert.certification}</b> {cert.issued_by && <>by {cert.issued_by}</>}
                                {cert.issue_date && <> ({cert.issue_date})</>}
                              </div>
                              {cert.url && (
                                <a href={cert.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                  View Certificate
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <FileText className="h-6 w-6 text-blue-600" />
                Application Form Data
              </CardTitle>
              <CardDescription className="text-base text-gray-600">
                Information provided by the candidate in the application form.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              {application_data.form_responses && Array.isArray(application_data.form_responses) && application_data.form_responses.length > 0 ? (
                  application_data.form_responses.map((response: any, index: number) => (
                  <div key={index} className="space-y-1 pb-3 mb-3 border-b border-slate-200 last:border-b-0 last:pb-0 last:mb-0">
                    <Label className="text-sm font-semibold text-gray-700">{response.name}</Label>
                    <p className="text-gray-800 bg-slate-100 p-3 rounded-md whitespace-pre-wrap">{String(response.value)}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-600 italic">No additional form data submitted.</p>
              )}
            </CardContent>
          </Card>

          {/* Interviews Section */}
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <Users className="h-6 w-6 text-blue-600" />
                Interviews & Reviews
              </CardTitle>
              <CardDescription className="text-base text-gray-600">
                Interview schedule and private interviewer reviews for this application.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              {interviews_loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                  <span className="ml-2 text-gray-600">Loading interviews...</span>
                </div>
              ) : interviews.length === 0 ? (
                <div className="text-center py-8">
                  <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 mb-4">No interviews scheduled for this application</p>
                  <Button variant="outline" className="button-outline">
                    Schedule Interview
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {interviews.map((interview) => (
                    <div key={interview.id} className="border border-gray-200 rounded-lg p-4 bg-gradient-to-r from-slate-50 to-blue-50">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Calendar className="h-4 w-4 text-blue-600" />
                            <span className="font-semibold text-gray-800">
                              {new Date(interview.date).toLocaleDateString()} at {new Date(interview.date).toLocaleTimeString()}
                            </span>
                            <Badge variant="outline" className="ml-2 capitalize">
                              {interview.type}
                            </Badge>
                            <Badge 
                              variant={interview.status === 'done' ? 'default' : interview.status === 'scheduled' ? 'secondary' : 'destructive'}
                              className="capitalize"
                            >
                              {interview.status}
                            </Badge>
                          </div>
                          {interview.interviewer && (
                            <p className="text-sm text-gray-600 mb-2">
                              <strong>Interviewer:</strong> {interview.interviewer.full_name}
                            </p>
                          )}
                          {interview.notes && (
                            <div className="mb-3">
                              <Label className="text-sm font-semibold text-gray-700">Notes for Candidate:</Label>
                              <p className="text-gray-800 bg-white p-3 rounded-md mt-1 text-sm border border-gray-200">
                                {interview.notes}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <Separator className="my-3" />
                      
                      {/* Interviewer Review Section */}
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                            <MessageSquare className="h-4 w-4 text-purple-600" />
                            Private Interviewer Review
                          </Label>
                          {!editing_review || editing_review !== interview.id ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handle_edit_review(interview.id, interview.interviewer_review || "")}
                              className="flex items-center gap-1 text-xs"
                            >
                              <Edit3 className="h-3 w-3" />
                              {interview.interviewer_review ? 'Edit Review' : 'Add Review'}
                            </Button>
                          ) : null}
                        </div>
                        
                        {editing_review === interview.id ? (
                          <div className="space-y-3">
                            <Textarea
                              value={review_text}
                              onChange={(e) => set_review_text(e.target.value)}
                              placeholder="Enter your private review of this interview..."
                              className="min-h-[100px] bg-white border-gray-300 focus:border-purple-500 focus:ring-purple-500"
                            />
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                onClick={() => handle_save_review(interview.id)}
                                disabled={saving_review}
                                className="flex items-center gap-1"
                              >
                                {saving_review ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Save className="h-3 w-3" />
                                )}
                                Save Review
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={handle_cancel_edit}
                                disabled={saving_review}
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="bg-white p-3 rounded-md border border-gray-200 min-h-[60px]">
                            {interview.interviewer_review ? (
                              <p className="text-gray-800 text-sm whitespace-pre-wrap">
                                {interview.interviewer_review}
                              </p>
                            ) : (
                              <p className="text-gray-500 italic text-sm">
                                No review added yet. Click "Add Review" to provide feedback on this interview.
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

        </div>

        <div className="space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <Calendar className="h-6 w-6 text-blue-600" />
                Job Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-4">
              <div className="space-y-1">
                <Label className="text-sm font-semibold text-gray-700">Job Title</Label>
                <p className="text-gray-800 font-medium">{application_data.job?.title || "N/A"}</p>
              </div>
              <div className="space-y-1">
                <Label className="text-sm font-semibold text-gray-700">Job Status</Label>
                <Badge variant={application_data.job?.status === 'active' ? 'default' : 'secondary'} className="font-medium">
                    {application_data.job?.status || "N/A"}
                </Badge>
              </div>
              <div className="space-y-1">
                <Label className="text-sm font-semibold text-gray-700">Application Status</Label>
                <Badge variant={get_status_variant(application_data.status)} className="font-medium capitalize">
                  {application_data.status || "N/A"}
                </Badge>
              </div>
              <div className="space-y-1">
                <Label className="text-sm font-semibold text-gray-700">Applied On</Label>
                <p className="text-gray-800 font-medium">
                  {application_data.created_at ? new Date(application_data.created_at).toLocaleDateString() : "N/A"}
                </p>
              </div>
            </CardContent>
          </Card>

          {application_data.match && (
            <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                  <Star className="h-6 w-6 text-yellow-500" />
                  Match Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-6">
                {/* Overall Score */}
                <div className="text-center p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
                  <Label className="text-sm font-semibold text-gray-700 block mb-2">Overall Match Score</Label>
                  <Badge variant="outline" className="font-bold text-2xl text-green-600 border-green-300 bg-green-50 px-4 py-2">
                    {application_data.match.score ? (application_data.match.score * 100).toFixed(1) : 'N/A'}%
                  </Badge>
                </div>

                {/* Skills Analysis */}
                <div className="space-y-4">
                  {/* Matching Skills */}
                  {application_data.match.matching_skills && application_data.match.matching_skills.length > 0 && (
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <Label className="text-sm font-semibold text-green-700 block mb-2">
                        Matching Skills ({application_data.match.matching_skills.length})
                      </Label>
                      <div className="flex flex-wrap gap-1">
                        {application_data.match.matching_skills.map((skill: string, index: number) => (
                          <Badge key={index} variant="secondary" className="bg-green-100 text-green-700 border-green-200 text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Missing Skills */}
                  {application_data.match.missing_skills && application_data.match.missing_skills.length > 0 && (
                    <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                      <Label className="text-sm font-semibold text-red-700 block mb-2">
                        Missing Skills ({application_data.match.missing_skills.length})
                      </Label>
                      <div className="flex flex-wrap gap-1">
                        {application_data.match.missing_skills.map((skill: string, index: number) => (
                          <Badge key={index} variant="secondary" className="bg-red-100 text-red-700 border-red-200 text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Extra Skills */}
                  {application_data.match.extra_skills && application_data.match.extra_skills.length > 0 && (
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <Label className="text-sm font-semibold text-blue-700 block mb-2">
                        Additional Skills ({application_data.match.extra_skills.length})
                      </Label>
                      <div className="flex flex-wrap gap-1">
                        {application_data.match.extra_skills.map((skill: string, index: number) => (
                          <Badge key={index} variant="secondary" className="bg-blue-100 text-blue-700 border-blue-200 text-xs">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Score Breakdown */}
                {application_data.match.score_breakdown && (
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <Label className="text-sm font-semibold text-gray-700 block mb-3">Score Breakdown</Label>
                    <div className="space-y-2">
                      {Object.entries(application_data.match.score_breakdown).map(([key, value]: [string, any]) => (
                        <div key={key} className="flex justify-between items-center p-3 bg-white rounded border">
                          <span className="text-sm font-medium text-gray-700">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                          <span className="text-sm font-bold text-gray-800">
                            {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Weights Used */}
                {application_data.match.weights_used && (
                  <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                    <Label className="text-sm font-semibold text-yellow-700 block mb-3">Matching Weights</Label>
                    <div className="space-y-3">
                      {application_data.match.weights_used.final_weights && (
                        <div>
                          <span className="text-sm font-medium text-gray-700">Final Weights:</span>
                          <div className="mt-1 space-y-1">
                            {Object.entries(application_data.match.weights_used.final_weights).map(([key, value]: [string, any]) => (
                              <div key={key} className="flex justify-between items-center p-2 bg-white rounded border">
                                <span className="text-xs text-gray-600">{key.replace(/_/g, ' ').toUpperCase()}</span>
                                <span className="text-xs font-bold text-gray-800">{(value * 100).toFixed(0)}%</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {application_data.match.weights_used.skill_weights && (
                        <div>
                          <span className="text-sm font-medium text-gray-700">Skill Weights:</span>
                          <div className="mt-1 space-y-1">
                            {Object.entries(application_data.match.weights_used.skill_weights).map(([key, value]: [string, any]) => (
                              <div key={key} className="flex justify-between items-center p-2 bg-white rounded border">
                                <span className="text-xs text-gray-600">{key.replace(/_/g, ' ').toUpperCase()}</span>
                                <span className="text-xs font-bold text-gray-800">{(value * 100).toFixed(0)}%</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Flags */}
                {application_data.match.flags && Object.keys(application_data.match.flags).length > 0 && (
                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <Label className="text-sm font-semibold text-purple-700 block mb-3">Match Flags</Label>
                    <div className="space-y-2">
                      {application_data.match.flags.constraint_violations && Object.keys(application_data.match.flags.constraint_violations).length > 0 && (
                        <div>
                          <span className="text-sm font-medium text-red-700">Constraint Violations:</span>
                          <div className="mt-1 space-y-1">
                            {Object.entries(application_data.match.flags.constraint_violations).map(([key, value]: [string, any]) => (
                              <div key={key} className="p-2 bg-red-50 rounded border border-red-200">
                                <div className="font-medium text-red-800 text-xs">{key}</div>
                                <div className="text-red-600 text-xs mt-1">{String(value)}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {Object.entries(application_data.match.flags).filter(([key]) => key !== 'constraint_violations').map(([key, value]: [string, any]) => (
                        <Badge key={key} variant="outline" className={`text-xs ${
                          value ? 'bg-purple-100 text-purple-700 border-purple-200' : 'bg-gray-100 text-gray-600 border-gray-200'
                        }`}>
                          {key.replace(/_/g, ' ')}: {String(value)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

              
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default ViewApplication;
