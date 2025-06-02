import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileText, Mail, Phone, User, Calendar, Star, ExternalLink, X, Loader2 } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";
import apiService from "@/services/api";

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

  if (loading) return <div>Loading...</div>;
  if (!application_data) return <div>Application not found.</div>;

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
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Application Details</h1>
          <p className="text-muted-foreground">
            {application_data.candidate?.name} • {application_data.job?.title}
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate("/applications")}>Back to Applications</Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Candidate Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label>Full Name</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span>{application_data.candidate?.name}</span>
                  </div>
                </div>
                <div>
                  <Label>Email</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span>{application_data.candidate?.email}</span>
                  </div>
                </div>
                <div>
                  <Label>Phone</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span>{application_data.candidate?.phone}</span>
                  </div>
                </div>
                <div>
                  <Label>Resume</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    {application_data.candidate?.id && (
                      <Button 
                        variant="link"
                        className="p-0 h-auto text-primary hover:underline flex items-center gap-1"
                        onClick={handle_view_resume}
                        disabled={pdf_loading}
                      >
                        {pdf_loading ? (
                          <>
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Loading...
                          </>
                        ) : (
                          <>
                            View Resume
                            <ExternalLink className="h-3 w-3" />
                          </>
                        )}
                      </Button>
                    )}
                    {!application_data.candidate?.id && application_data.candidate?.resume_url && (
                       <a 
                         href={application_data.candidate?.resume_url} 
                         target="_blank" 
                         rel="noopener noreferrer"
                         className="text-primary hover:underline flex items-center gap-1"
                       >
                         View Resume (URL)
                         <ExternalLink className="h-3 w-3" /> 
                       </a>
                    )}
                    {!application_data.candidate?.id && !application_data.candidate?.resume_url && (
                        <span>No resume available</span>
                    )}
                  </div>
                </div>
              </div>

              {/* PDF Viewer Section */}
              {resume_pdf_url && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <Label>Resume Preview</Label>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handle_close_pdf}
                      className="flex items-center gap-1"
                    >
                      <X className="h-4 w-4" />
                      Close
                    </Button>
                  </div>
                  <div className="border rounded-lg overflow-hidden bg-gray-100">
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

          <Card>
            <CardHeader>
              <CardTitle>Form Responses</CardTitle>
              <CardDescription>Answers to custom application questions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {application_data.form_responses &&
                  Object.entries(application_data.form_responses).map(([key, value]) => (
                    <div key={key}>
                      <Label className="capitalize">
                        {key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                      </Label>
                      <div className="mt-1 p-2 bg-muted rounded-md">{String(value)}</div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Interview History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {application_data.interviews?.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date & Time</TableHead>
                      <TableHead>Interviewer</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Result</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {application_data.interviews.map((interview: any) => (
                      <TableRow key={interview.id}>
                        <TableCell>
                          {new Date(interview.date).toLocaleDateString()} at {interview.time}
                        </TableCell>
                        <TableCell>{interview.interviewer}</TableCell>
                        <TableCell>{interview.type}</TableCell>
                        <TableCell>
                          <Badge variant={interview.result === "Pending" ? "secondary" : "default"}>
                            {interview.result}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-muted-foreground">No interviews scheduled yet.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Application Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Current Status</Label>
                <div className="mt-1">
                  <Badge variant="outline" className="capitalize">
                    {application_data.status}
                  </Badge>
                </div>
              </div>
              <div>
                <Label>Submitted</Label>
                <div className="mt-1 text-muted-foreground">
                  {application_data.submission_date && new Date(application_data.submission_date).toLocaleDateString()}
                </div>
              </div>
              <div>
                <Label>Job Position</Label>
                <div className="mt-1 font-medium">{application_data.job?.title}</div>
              </div>
            </CardContent>
          </Card>

          {application_data.match_score && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Star className="h-5 w-5" />
                  Match Score
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">
                    {application_data.match_score}%
                  </div>
                  <p className="text-muted-foreground">Compatibility with job requirements</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default ViewApplication;
