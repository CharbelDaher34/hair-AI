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

interface Job {
  id: number;
  title: string;
  description: string;
  location: string;
  salary_min?: number;
  salary_max?: number;
  experience_level: string;
  seniority_level: string;
  job_type: string;
  job_category?: string;
  status: string;
  recruited_to_id?: number;
  job_data?: {
    overview?: string;
    requirements?: string;
    objectives?: string;
    auto_generate?: boolean;
  };
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
    const url = generated_url || `${window.location.origin}/apply/job-${id}`;
    navigator.clipboard.writeText(url);
    toast({
      title: "URL Copied!",
      description: "The application URL has been copied to your clipboard.",
    });
  };

  const generate_url = () => {
    const url = `${window.location.origin}/apply/job-${id}`;
    set_generated_url(url);
    copy_url();
  };

  const format_salary = (min?: number, max?: number) => {
    if (!min && !max) return "Not specified";
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    if (min) return `$${min.toLocaleString()}+`;
    if (max) return `Up to $${max.toLocaleString()}`;
    return "Not specified";
  };

  const format_enum_value = (value: string) => {
    return value.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ');
  };

  if (is_loading) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading job details...</span>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-destructive mb-4">Error: {error || "Job not found"}</p>
            <Button onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{job.title}</h1>
          <div className="flex items-center space-x-4 mt-2">
            <Badge variant={job.status === "published" ? "default" : job.status === "draft" ? "secondary" : "destructive"}>
              {format_enum_value(job.status)}
            </Badge>
            <span className="text-muted-foreground">
              Location: {job.location}
            </span>
            {job.created_at && (
              <span className="text-muted-foreground">
                Created: {new Date(job.created_at).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to={`/jobs/${id}/edit`}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/jobs/${id}/analytics`}>
              <BarChart3 className="mr-2 h-4 w-4" />
              Analytics
            </Link>
          </Button>
          <Button asChild>
            <Link to={`/jobs/${id}/matches`}>
              <Users className="mr-2 h-4 w-4" />
              View Matches
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Job Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground leading-relaxed">{job.description}</p>
            </CardContent>
          </Card>

          {job.job_data?.overview && (
            <Card>
              <CardHeader>
                <CardTitle>Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground leading-relaxed">{job.job_data.overview}</p>
              </CardContent>
            </Card>
          )}

          {job.job_data?.requirements && (
            <Card>
              <CardHeader>
                <CardTitle>Requirements</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="whitespace-pre-line text-muted-foreground">
                  {job.job_data.requirements}
                </div>
              </CardContent>
            </Card>
          )}

          {job.job_data?.objectives && (
            <Card>
              <CardHeader>
                <CardTitle>Objectives</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="whitespace-pre-line text-muted-foreground">
                  {job.job_data.objectives}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Job Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Salary:</span>
                <span className="text-sm text-muted-foreground">
                  {format_salary(job.salary_min, job.salary_max)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Job Type:</span>
                <span className="text-sm text-muted-foreground">
                  {format_enum_value(job.job_type)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Experience Level:</span>
                <span className="text-sm text-muted-foreground">
                  {format_enum_value(job.experience_level)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Seniority Level:</span>
                <span className="text-sm text-muted-foreground">
                  {format_enum_value(job.seniority_level)}
                </span>
              </div>
              {job.job_category && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Category:</span>
                  <span className="text-sm text-muted-foreground">
                    {job.job_category}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Application Form</CardTitle>
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
                <p className="text-xs text-muted-foreground break-all">
                  {generated_url}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Form Keys & Constraints</CardTitle>
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
                        <div className="mt-2 p-2 bg-muted rounded text-xs">
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
                <p className="text-muted-foreground text-sm">No form keys attached</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
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
