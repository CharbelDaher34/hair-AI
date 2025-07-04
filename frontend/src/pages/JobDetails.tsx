import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Edit, BarChart3, Users, ExternalLink, Copy, Loader2 } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import apiService from "@/services/api";

interface Compensation {
  base_salary?: number;
  benefits?: string[];
}

interface Skills {
  hard_skills?: string[];
  soft_skills?: string[];
}

interface TailoredQuestion {
  question: string;
  ideal_answer: string;
  tags: string[];
  difficulty: string;
}

interface Job {
  id: number;
  title: string;
  description: string;
  location: string;
  department?: string;
  compensation: Compensation;
  experience_level: string;
  seniority_level: string;
  job_type: string;
  job_category?: string;
  responsibilities?: string[];
  skills: Skills;
  interviews_sequence?: string[];
  tailored_questions?: TailoredQuestion[];
  status: string;
  recruited_to_id?: number;
  created_at?: string;
}

interface FormKey {
  id: number;
  name: string;
  field_type: string;
  required: boolean;
  enum_values?: string[] | null;
}

interface JobFormKeyConstraint {
  id: number;
  job_id: number;
  form_key_id: number;
  constraints: Record<string, any>;
  form_key?: FormKey;
}

const JobDetails = () => {
  const { id } = useParams();
  const [job, set_job] = useState<Job | null>(null);
  const [constraints, set_constraints] = useState<JobFormKeyConstraint[]>([]);
  const [is_loading, set_is_loading] = useState(true);
  const [error, set_error] = useState<string | null>(null);
  const [generated_url, set_generated_url] = useState<string>("");

  const fetch_job_data = async () => {
    if (!id) return;
    
    try {
      const job_response = await apiService.getJob(parseInt(id));
      set_job(job_response);

      // Fetch constraints for this job
      const constraints_response = await apiService.getConstraintsByJob(parseInt(id));
      set_constraints(constraints_response || []);
    } catch (error) {
      console.error('Failed to fetch job data:', error);
      set_error(error.message || 'Failed to fetch job data');
      toast({
        title: "Error",
        description: "Failed to fetch job data",
        variant: "destructive",
      });
    }
  };

  useEffect(() => {
    const load_data = async () => {
      set_is_loading(true);
      set_error(null);
      
      try {
        await fetch_job_data();
      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        set_is_loading(false);
      }
    };

    load_data();
  }, [id]);

  const copy_url = () => {
    const url = generated_url || `${window.location.origin}/apply/${id}`;
    navigator.clipboard.writeText(url);
    toast({
      title: "URL Copied!",
      description: "The application URL has been copied to your clipboard.",
    });
  };

  const generate_url = () => {
    const url = `${window.location.origin}/apply/${id}`;
    set_generated_url(url);
    copy_url();
  };

  const format_salary = (compensation: Compensation) => {
    if (!compensation) return "Not specified";
    const { base_salary } = compensation;
    if (base_salary) return `$${base_salary.toLocaleString()}`;
    return "Not specified";
  };

  const format_enum_value = (value: string) => {
    if (!value) return '';
    return value.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
  };

  const format_interview_type = (type: string) => {
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  if (is_loading) {
    return (
      <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="flex items-center justify-center h-64">
          <div className="text-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
            <span className="text-lg font-medium text-gray-700">Loading job details...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="flex items-center justify-center h-64">
          <Card className="w-full max-w-md shadow-xl border-0">
            <CardContent className="text-center p-8 space-y-4">
              <p className="text-red-600 font-semibold text-lg mb-4">Error: {error || "Job not found"}</p>
              <Button onClick={() => window.location.reload()} className="button shadow-lg hover:shadow-xl transition-all duration-300">
              Retry
            </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-3">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            {job.title}
          </h1>
          <div className="flex items-center space-x-4">
            <Badge 
              variant={job.status === "published" ? "default" : job.status === "draft" ? "secondary" : "destructive"}
              className="font-medium px-3 py-1"
            >
              {format_enum_value(job.status)}
            </Badge>
            <span className="text-gray-600 font-medium">
              📍 {job.location}
            </span>
            {job.created_at && (
              <span className="text-gray-600">
                📅 Created: {new Date(job.created_at).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" asChild className="shadow-md hover:shadow-lg transition-all duration-300">
            <Link to={`/jobs/${id}/edit`}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Link>
          </Button>
          <Button variant="outline" asChild className="shadow-md hover:shadow-lg transition-all duration-300">
            <Link to={`/jobs/${id}/analytics`}>
              <BarChart3 className="mr-2 h-4 w-4" />
              Analytics
            </Link>
          </Button>
          <Button variant="outline" asChild className="shadow-md hover:shadow-lg transition-all duration-300">
            <Link to={`/jobs/${id}/matches`}>
              <Users className="mr-2 h-4 w-4" />
              View Matches
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Job Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 leading-relaxed text-base">{job.description}</p>
            </CardContent>
          </Card>

          {job.responsibilities && job.responsibilities.length > 0 && (
            <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl font-bold text-gray-800">Responsibilities</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc pl-5 space-y-2 text-gray-700">
                  {job.responsibilities.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {(job.skills?.hard_skills?.length > 0 || job.skills?.soft_skills?.length > 0) && (
             <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl font-bold text-gray-800">Skills</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {job.skills.hard_skills && job.skills.hard_skills.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-2">Hard Skills</h4>
                    <div className="flex flex-wrap gap-2">
                      {job.skills.hard_skills.map((skill, index) => (
                        <Badge key={index} variant="secondary">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {job.skills.soft_skills && job.skills.soft_skills.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-2">Soft Skills</h4>
                    <div className="flex flex-wrap gap-2">
                      {job.skills.soft_skills.map((skill, index) => (
                        <Badge key={index} variant="outline">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {job.interviews_sequence && job.interviews_sequence.length > 0 && (
            <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl font-bold text-gray-800">Interview Process</CardTitle>
                <CardDescription>Candidates will go through {job.interviews_sequence.length} interview steps</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {job.interviews_sequence.map((interview_type, index) => (
                    <div key={`${interview_type}-${index}`} className="relative">
                      {/* Connection line for all except last item */}
                      {index < job.interviews_sequence.length - 1 && (
                        <div className="absolute left-6 top-12 w-0.5 h-8 bg-gradient-to-b from-blue-300 to-blue-500"></div>
                      )}
                      
                      <div className="flex items-start space-x-4">
                        {/* Step number circle */}
                        <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
                          <span className="text-white font-bold text-sm">{index + 1}</span>
                        </div>
                        
                        {/* Interview details */}
                        <div className="flex-1 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200 shadow-sm">
                          <h4 className="font-semibold text-gray-900 text-lg mb-1">
                            {format_interview_type(interview_type)}
                          </h4>
                          <p className="text-sm text-gray-600">
                            {index === 0 && "Initial screening and evaluation"}
                            {index === job.interviews_sequence.length - 1 && index > 0 && "Final interview round"}
                            {index > 0 && index < job.interviews_sequence.length - 1 && `Interview round ${index + 1}`}
                          </p>
                          
                          {/* Progress indicator */}
                          <div className="mt-3 flex items-center space-x-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${((index + 1) / job.interviews_sequence.length) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-xs text-gray-500 font-medium">
                              Step {index + 1} of {job.interviews_sequence.length}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {/* Completion indicator */}
                  <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div>
                        <h4 className="font-semibold text-green-800">Interview Process Complete</h4>
                        <p className="text-sm text-green-600">Candidate evaluation and decision making</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {job.tailored_questions && job.tailored_questions.length > 0 && (
            <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl font-bold text-gray-800">Interview Questions</CardTitle>
                <CardDescription>
                  {job.tailored_questions.length} tailored question{job.tailored_questions.length !== 1 ? 's' : ''} for this position
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {job.tailored_questions.map((question, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-5 bg-gradient-to-r from-gray-50 to-blue-50">
                      <div className="flex items-start justify-between mb-4">
                        <Badge variant="outline" className="text-sm font-medium">
                          Question {index + 1}
                        </Badge>
                        <div className="flex items-center space-x-2">
                          {question.tags.map((tag, tagIndex) => (
                            <Badge key={tagIndex} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                          <Badge 
                            variant={
                              question.difficulty === 'easy' ? 'default' : 
                              question.difficulty === 'medium' ? 'secondary' : 
                              'destructive'
                            }
                            className="text-xs"
                          >
                            {question.difficulty}
                          </Badge>
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                            <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm mr-2">
                              Q
                            </span>
                            Question
                          </h4>
                          <p className="text-gray-700 leading-relaxed pl-8">
                            {question.question}
                          </p>
                        </div>
                        
                        <div className="border-t border-gray-200 pt-4">
                          <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                            <span className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-sm mr-2">
                              A
                            </span>
                            Ideal Answer
                          </h4>
                          <div className="pl-8 bg-green-50 border-l-4 border-green-400 p-3 rounded-r-lg">
                            <p className="text-gray-700 leading-relaxed">
                              {question.ideal_answer}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Job Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center text-gray-700">
                <span className="font-semibold">Salary</span>
                <Badge variant="default" className="text-base">{format_salary(job.compensation)}</Badge>
              </div>
              <Separator />
              <div className="flex justify-between items-center text-gray-700">
                <span className="font-semibold">Job Type</span>
                <span className="font-medium">{format_enum_value(job.job_type)}</span>
              </div>
              <Separator />
              <div className="flex justify-between items-center text-gray-700">
                <span className="font-semibold">Experience</span>
                <span className="font-medium">{format_enum_value(job.experience_level)}</span>
              </div>
              <Separator />
              <div className="flex justify-between items-center text-gray-700">
                <span className="font-semibold">Seniority</span>
                <span className="font-medium">{format_enum_value(job.seniority_level)}</span>
              </div>
               {job.department && (
                <>
                  <Separator />
                  <div className="flex justify-between items-center text-gray-700">
                    <span className="font-semibold">Department</span>
                    <span className="font-medium">{job.department}</span>
                  </div>
                </>
              )}
              {job.job_category && (
                <>
                  <Separator />
                  <div className="flex justify-between items-center text-gray-700">
                    <span className="font-semibold">Category</span>
                    <span className="font-medium">{job.job_category}</span>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {job.compensation?.benefits && job.compensation.benefits.length > 0 && (
            <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl font-bold text-gray-800">Benefits</CardTitle>
              </CardHeader>
              <CardContent>
                 <ul className="list-disc pl-5 space-y-2 text-gray-700">
                  {job.compensation.benefits.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Application Form</CardTitle>
              <CardDescription>Public URL for candidates to apply</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" onClick={generate_url}>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy URL
                </Button>
                {generated_url && (
                  <Button variant="outline" size="sm" asChild>
                    <a href={generated_url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Open
                    </a>
                  </Button>
                )}
              </div>
              {generated_url && (
                <p className="text-xs text-gray-700 break-all">
                  {generated_url}
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Form Keys & Constraints</CardTitle>
              <CardDescription>Custom fields attached to this job</CardDescription>
            </CardHeader>
            <CardContent>
              {constraints.length > 0 ? (
                <div className="space-y-4">
                  {constraints.map((constraint, index) => (
                    <div key={constraint.id}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{constraint.form_key?.name || `Form Key ${constraint.form_key_id}`}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {constraint.form_key?.field_type || "unknown"}
                            </Badge>
                            {constraint.form_key?.required && (
                              <Badge variant="secondary" className="text-xs">
                                Required
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      {constraint.constraints && Object.keys(constraint.constraints).length > 0 && (
                        <div className="mt-2 p-2 bg-gray-200 rounded text-xs">
                          <strong>Constraints:</strong>
                          <div className="mt-1">
                            {Object.entries(constraint.constraints).map(([key, value]) => (
                              <div key={key}>
                                {key}: {String(value)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {index < constraints.length - 1 && <Separator className="mt-4" />}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-700 text-sm">No form keys attached</p>
              )}
            </CardContent>
          </Card>

          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start" asChild>
                <Link to="/applications">
                  <Users className="mr-2 h-4 w-4" />
                  View All Applications
                </Link>
              </Button>
              <Button variant="outline" className="w-full justify-start" asChild>
                <Link to={`/jobs/${id}/analytics`}>
                  <BarChart3 className="mr-2 h-4 w-4" />
                  View Analytics
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default JobDetails;
