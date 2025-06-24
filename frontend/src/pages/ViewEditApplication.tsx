import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileText, Mail, Phone, User, Calendar, Star, ExternalLink, X, Loader2, XCircle } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";
import apiService from "@/services/api";
import { ApplicationStatus } from "@/types";

const ViewApplication = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [application_data, set_application_data] = useState<any>(null);
  const [loading, set_loading] = useState(true);
  const [resume_pdf_url, set_resume_pdf_url] = useState<string | null>(null);
  const [pdf_loading, set_pdf_loading] = useState(false);

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
        <Button variant="outline" onClick={() => navigate("/applications")} className="button-outline shadow-md hover:shadow-lg transition-all duration-300">
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
