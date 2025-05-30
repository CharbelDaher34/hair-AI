import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Copy, ExternalLink, Loader2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import apiService from "@/services/api";

interface FormKey {
  id: number;
  name: string;
  field_type: string;
  required: boolean;
  enum_values?: string[] | null;
  employer_id: number;
}

interface JobFormKeyConstraint {
  id?: number;
  job_id?: number;
  form_key_id: number;
  constraints: Record<string, any>;
}

interface Company {
  id: number;
  name: string;
  description?: string;
  industry?: string;
}

// Enums matching the backend
const JobStatus = {
  DRAFT: "draft",
  PUBLISHED: "published",
  CLOSED: "closed",
};

const JobType = {
  FULL_TIME: "full_time",
  PART_TIME: "part_time",
  CONTRACT: "contract",
  INTERNSHIP: "internship",
};

const SeniorityLevel = {
  ENTRY: "entry",
  MID: "mid",
  SENIOR: "senior",
};

const ExperienceLevel = {
  NO_EXPERIENCE: "no_experience",
  ONE_TO_THREE_YEARS: "1-3_years",
  THREE_TO_FIVE_YEARS: "3-5_years",
  FIVE_TO_SEVEN_YEARS: "5-7_years",
  SEVEN_TO_TEN_YEARS: "7-10_years",
  TEN_PLUS_YEARS: "10_plus_years",
};

const CreateEditJob = () => {
  const navigate = useNavigate();
  const { job_id, id } = useParams();
  const current_job_id = job_id || id;
  const is_editing = Boolean(current_job_id);

  console.log("CreateEditJob params:", { job_id, id, current_job_id, is_editing }); // Debug log

  const [job_data, set_job_data] = useState({
    title: "",
    description: "",
    location: "",
    salary_min: "",
    salary_max: "",
    experience_level: ExperienceLevel.NO_EXPERIENCE,
    seniority_level: SeniorityLevel.ENTRY,
    job_type: JobType.FULL_TIME,
    job_category: "",
    status: JobStatus.DRAFT,
    recruited_to_id: null,
    // Legacy fields for job_data JSON
    overview: "",
    requirements: "",
    objectives: "",
    auto_generate: false,
  });

  const [selected_form_keys, set_selected_form_keys] = useState<number[]>([]);
  const [constraints, set_constraints] = useState<Record<number, any>>({});
  const [form_keys, set_form_keys] = useState<FormKey[]>([]);
  const [recruit_to_companies, set_recruit_to_companies] = useState<Company[]>([]);
  const [is_loading, set_is_loading] = useState(true);
  const [is_submitting, set_is_submitting] = useState(false);
  const [error, set_error] = useState<string | null>(null);
  const [generated_url, set_generated_url] = useState<string>("");

  const fetch_form_keys = async () => {
    try {
      const response = await apiService.getFormKeysByCompany();
      set_form_keys(response || []);
    } catch (error) {
      console.error('Failed to fetch form keys:', error);
      set_error(error.message || 'Failed to fetch form keys');
      toast({
        title: "Error",
        description: "Failed to fetch form keys",
        variant: "destructive",
      });
    }
  };

  const fetch_recruit_to_companies = async () => {
    try {
      const response = await apiService.getRecruitToCompanies();
      set_recruit_to_companies(response || []);
    } catch (error) {
      console.error('Failed to fetch recruit-to companies:', error);
      // Don't set error state for this as it's not critical
      toast({
        title: "Warning",
        description: "Failed to fetch recruit-to companies",
        variant: "destructive",
      });
    }
  };

  const fetch_job_data = async (job_id: string) => {
    try {
      console.log("Fetching job data for ID:", job_id); // Debug log
      const job = await apiService.getJob(parseInt(job_id));
      const job_info = job.job_data || {};
      
      console.log("Fetched job data:", job); // Debug log
      
      // Handle recruited_to_id properly
      let recruited_to_value = null;
      if (job.recruited_to_id !== null && job.recruited_to_id !== undefined) {
        recruited_to_value = job.recruited_to_id;
      }
      
      const new_job_data = {
        title: job.title || "",
        description: job.description || "",
        location: job.location || "",
        salary_min: job.salary_min?.toString() || "",
        salary_max: job.salary_max?.toString() || "",
        experience_level: job.experience_level || ExperienceLevel.NO_EXPERIENCE,
        seniority_level: job.seniority_level || SeniorityLevel.ENTRY,
        job_type: job.job_type || JobType.FULL_TIME,
        job_category: job.job_category || "",
        status: job.status || JobStatus.DRAFT,
        recruited_to_id: recruited_to_value,
        // Legacy fields from job_data JSON
        overview: job_info.overview || "",
        requirements: job_info.requirements || "",
        objectives: job_info.objectives || "",
        auto_generate: job_info.auto_generate || false,
      };
      
      console.log("Setting job data:", new_job_data); // Debug log
      set_job_data(new_job_data);

      // Fetch constraints for this job
      try {
        const constraints_response = await apiService.getConstraintsByJob(parseInt(job_id));
        const job_constraints: Record<number, any> = {};
        const selected_keys: number[] = [];

        if (constraints_response && Array.isArray(constraints_response)) {
          constraints_response.forEach((constraint: JobFormKeyConstraint) => {
            selected_keys.push(constraint.form_key_id);
            job_constraints[constraint.form_key_id] = constraint.constraints;
          });
        }

        console.log("Setting constraints:", job_constraints, "Selected keys:", selected_keys); // Debug log
        set_selected_form_keys(selected_keys);
        set_constraints(job_constraints);
      } catch (constraintError) {
        console.warn("Failed to fetch constraints:", constraintError);
        // Don't fail the whole operation if constraints fail
      }
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
      console.log("useEffect triggered with:", { is_editing, current_job_id }); // Debug log
      set_is_loading(true);
      set_error(null);
      
      try {
        // Always fetch form keys and recruit-to companies
        await Promise.all([
          fetch_form_keys(),
          fetch_recruit_to_companies()
        ]);
        
        // Only fetch job data if we're editing and have a job ID
        if (is_editing && current_job_id) {
          console.log("Loading job data for editing..."); // Debug log
          await fetch_job_data(current_job_id);
        } else {
          console.log("Creating new job - no data to load"); // Debug log
        }
      } catch (error) {
        console.error('Failed to load data:', error);
        set_error(error.message || 'Failed to load data');
      } finally {
        set_is_loading(false);
      }
    };

    load_data();
  }, [is_editing, current_job_id]); // Dependencies ensure effect runs when these change

  const handle_form_key_toggle = (key_id: number) => {
    if (selected_form_keys.includes(key_id)) {
      set_selected_form_keys(selected_form_keys.filter(id => id !== key_id));
      const new_constraints = { ...constraints };
      delete new_constraints[key_id];
      set_constraints(new_constraints);
    } else {
      set_selected_form_keys([...selected_form_keys, key_id]);
    }
  };

  const handle_constraint_change = (key_id: number, constraint_type: string, value: any) => {
    set_constraints({
      ...constraints,
      [key_id]: {
        ...constraints[key_id],
        [constraint_type]: value,
      },
    });
  };

  const generate_form_url = () => {
    const url = `${window.location.origin}/apply/job-${Date.now()}`;
    navigator.clipboard.writeText(url);
    set_generated_url(url);
    toast({
      title: "URL Copied!",
      description: "The application form URL has been copied to your clipboard.",
    });
    return url;
  };

  const handle_save = async () => {
    if (!job_data.title || !job_data.description || !job_data.location) {
      toast({
        title: "Error",
        description: "Please fill in all required fields (title, description, location).",
        variant: "destructive",
      });
      return;
    }

    set_is_submitting(true);

    try {
      const job_payload = {
        title: job_data.title,
        description: job_data.description,
        location: job_data.location,
        salary_min: job_data.salary_min ? parseInt(job_data.salary_min) : null,
        salary_max: job_data.salary_max ? parseInt(job_data.salary_max) : null,
        experience_level: job_data.experience_level,
        seniority_level: job_data.seniority_level,
        job_type: job_data.job_type,
        job_category: job_data.job_category || null,
        status: job_data.status,
        recruited_to_id: job_data.recruited_to_id === "none" ? null : job_data.recruited_to_id,
        job_data: {
          overview: job_data.overview,
          requirements: job_data.requirements,
          objectives: job_data.objectives,
          auto_generate: job_data.auto_generate,
        },
      };

      let saved_job;
      if (is_editing && current_job_id) {
        saved_job = await apiService.updateJob(parseInt(current_job_id), job_payload);
        toast({
          title: "Success",
          description: "Job has been updated successfully.",
        });
      } else {
        saved_job = await apiService.createJob(job_payload);
        toast({
          title: "Success",
          description: "Job has been created successfully.",
        });
      }

      // Save constraints
      if (saved_job && saved_job.id) {
        // If editing, we might want to delete existing constraints first
        // For now, we'll just create new ones
        
        for (const form_key_id of selected_form_keys) {
          const constraint_data = {
            job_id: saved_job.id,
            form_key_id: form_key_id,
            constraints: constraints[form_key_id] || {},
          };

          try {
            await apiService.createJobFormKeyConstraint(constraint_data);
          } catch (error) {
            console.error(`Failed to save constraint for form key ${form_key_id}:`, error);
            // Continue with other constraints even if one fails
          }
        }
      }

      navigate("/jobs");
    } catch (error) {
      console.error('Failed to save job:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to save job.",
        variant: "destructive",
      });
    } finally {
      set_is_submitting(false);
    }
  };

  if (is_loading) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-destructive mb-4">Error: {error}</p>
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
          <h1 className="text-3xl font-bold tracking-tight">
            {is_editing ? "Edit Job" : "Create New Job"}
          </h1>
          <p className="text-muted-foreground">
            {is_editing ? "Update job posting details" : "Set up a new job posting with custom requirements"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/jobs")} disabled={is_submitting}>
            Cancel
          </Button>
          <Button onClick={handle_save} disabled={is_submitting}>
            {is_submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {is_editing ? "Updating..." : "Creating..."}
              </>
            ) : (
              is_editing ? "Update Job" : "Save Job"
            )}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Job Information</CardTitle>
              <CardDescription>Basic details about the position</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Job Title</Label>
                <Input
                  id="title"
                  value={job_data.title}
                  onChange={(e) => set_job_data({...job_data, title: e.target.value})}
                  placeholder="e.g., Senior Frontend Developer"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={job_data.description}
                  onChange={(e) => set_job_data({...job_data, description: e.target.value})}
                  placeholder="Brief description of the role and company"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  value={job_data.location}
                  onChange={(e) => set_job_data({...job_data, location: e.target.value})}
                  placeholder="e.g., New York, NY"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="salary_min">Salary Min</Label>
                <Input
                  id="salary_min"
                  value={job_data.salary_min}
                  onChange={(e) => set_job_data({...job_data, salary_min: e.target.value})}
                  placeholder="e.g., 50000"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="salary_max">Salary Max</Label>
                <Input
                  id="salary_max"
                  value={job_data.salary_max}
                  onChange={(e) => set_job_data({...job_data, salary_max: e.target.value})}
                  placeholder="e.g., 100000"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="experience_level">Experience Level</Label>
                <Select
                  value={job_data.experience_level}
                  onValueChange={(value) => set_job_data({...job_data, experience_level: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select experience level" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(ExperienceLevel).map(([key, value]) => (
                      <SelectItem key={key} value={value}>
                        {key}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="seniority_level">Seniority Level</Label>
                <Select
                  value={job_data.seniority_level}
                  onValueChange={(value) => set_job_data({...job_data, seniority_level: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select seniority level" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(SeniorityLevel).map(([key, value]) => (
                      <SelectItem key={key} value={value}>
                        {key}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="job_type">Job Type</Label>
                <Select
                  value={job_data.job_type}
                  onValueChange={(value) => set_job_data({...job_data, job_type: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select job type" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(JobType).map(([key, value]) => (
                      <SelectItem key={key} value={value}>
                        {key}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="job_category">Job Category</Label>
                <Input
                  id="job_category"
                  value={job_data.job_category}
                  onChange={(e) => set_job_data({...job_data, job_category: e.target.value})}
                  placeholder="e.g., Technology"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={job_data.status}
                  onValueChange={(value) => set_job_data({...job_data, status: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select job status" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(JobStatus).map(([key, value]) => (
                      <SelectItem key={key} value={value}>
                        {key}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="recruited_to_id">Recruited To</Label>
                <Select
                  value={job_data.recruited_to_id?.toString() || "none"}
                  onValueChange={(value) => set_job_data({...job_data, recruited_to_id: value === "none" ? null : parseInt(value)})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a company (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    {recruit_to_companies.length === 0 ? (
                      <SelectItem value="" disabled>No companies available</SelectItem>
                    ) : (
                      recruit_to_companies.map((company) => (
                        <SelectItem key={company.id} value={company.id.toString()}>
                          {company.name}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Select a company you are recruiting for (leave empty if recruiting for your own company)
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Application Form URL</CardTitle>
              <CardDescription>Generate a public URL for external applications</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <Input
                  value={generated_url || "Click generate to create URL"}
                  readOnly
                  className="flex-1"
                />
                <Button variant="outline" onClick={generate_form_url}>
                  <Copy className="mr-2 h-4 w-4" />
                  Generate
                </Button>
                {generated_url && (
                  <Button variant="outline" size="sm" onClick={() => window.open(generated_url, '_blank')}>
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Form Keys & Constraints</CardTitle>
              <CardDescription>
                Attach custom form fields and set requirements
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {form_keys.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">No form keys available</p>
                  <Button variant="outline" onClick={() => navigate("/form-keys")}>
                    Create Form Keys
                  </Button>
                </div>
              ) : (
                form_keys.map((form_key, index) => (
                  <div key={form_key.id} className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id={`formKey-${form_key.id}`}
                        checked={selected_form_keys.includes(form_key.id)}
                        onCheckedChange={() => handle_form_key_toggle(form_key.id)}
                      />
                      <Label htmlFor={`formKey-${form_key.id}`} className="flex-1">
                        {form_key.name}
                      </Label>
                      <Badge variant="outline">{form_key.field_type}</Badge>
                      {form_key.required && (
                        <Badge variant="secondary" className="text-xs">Required</Badge>
                      )}
                    </div>

                    {selected_form_keys.includes(form_key.id) && (
                      <div className="ml-6 space-y-2 p-3 bg-muted rounded-lg">
                        <Label className="text-sm font-medium">Constraints</Label>
                        {form_key.field_type === "number" && (
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <Label className="text-xs">Min Value</Label>
                              <Input
                                type="number"
                                placeholder="0"
                                value={constraints[form_key.id]?.min_value || ""}
                                onChange={(e) => 
                                  handle_constraint_change(form_key.id, "min_value", e.target.value)
                                }
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Max Value</Label>
                              <Input
                                type="number"
                                placeholder="10"
                                value={constraints[form_key.id]?.max_value || ""}
                                onChange={(e) => 
                                  handle_constraint_change(form_key.id, "max_value", e.target.value)
                                }
                              />
                            </div>
                          </div>
                        )}
                        {form_key.field_type === "text" && (
                          <div>
                            <Label className="text-xs">Pattern (Regex)</Label>
                            <Input
                              placeholder="e.g., https://.*"
                              value={constraints[form_key.id]?.pattern || ""}
                              onChange={(e) => 
                                handle_constraint_change(form_key.id, "pattern", e.target.value)
                              }
                            />
                          </div>
                        )}
                        {form_key.field_type === "date" && (
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <Label className="text-xs">After Date</Label>
                              <Input
                                type="date"
                                value={constraints[form_key.id]?.after_date || ""}
                                onChange={(e) => 
                                  handle_constraint_change(form_key.id, "after_date", e.target.value)
                                }
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Before Date</Label>
                              <Input
                                type="date"
                                value={constraints[form_key.id]?.before_date || ""}
                                onChange={(e) => 
                                  handle_constraint_change(form_key.id, "before_date", e.target.value)
                                }
                              />
                            </div>
                          </div>
                        )}
                        {form_key.field_type === "select" && form_key.enum_values && (
                          <div>
                            <Label className="text-xs">Required Options</Label>
                            <div className="space-y-1">
                              {form_key.enum_values.map((option, opt_index) => (
                                <div key={opt_index} className="flex items-center space-x-2">
                                  <Checkbox
                                    id={`option-${form_key.id}-${opt_index}`}
                                    checked={constraints[form_key.id]?.required_options?.includes(option) || false}
                                    onCheckedChange={(checked) => {
                                      const current_options = constraints[form_key.id]?.required_options || [];
                                      const new_options = checked 
                                        ? [...current_options, option]
                                        : current_options.filter((opt: string) => opt !== option);
                                      handle_constraint_change(form_key.id, "required_options", new_options);
                                    }}
                                  />
                                  <Label htmlFor={`option-${form_key.id}-${opt_index}`} className="text-xs">
                                    {option}
                                  </Label>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    {index !== form_keys.length - 1 && <Separator />}
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Additional Details</CardTitle>
              <CardDescription>Optional additional information about the position</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="overview">Overview</Label>
                <Textarea
                  id="overview"
                  value={job_data.overview}
                  onChange={(e) => set_job_data({...job_data, overview: e.target.value})}
                  placeholder="Brief overview of the role and company"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="requirements">Requirements</Label>
                <Textarea
                  id="requirements"
                  value={job_data.requirements}
                  onChange={(e) => set_job_data({...job_data, requirements: e.target.value})}
                  placeholder="List the key requirements for this position"
                  rows={4}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="objectives">Objectives</Label>
                <Textarea
                  id="objectives"
                  value={job_data.objectives}
                  onChange={(e) => set_job_data({...job_data, objectives: e.target.value})}
                  placeholder="What will the successful candidate achieve?"
                  rows={4}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="auto_generate"
                  checked={job_data.auto_generate}
                  onCheckedChange={(checked) => set_job_data({...job_data, auto_generate: checked})}
                />
                <Label htmlFor="auto_generate">Auto-generate job description</Label>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CreateEditJob;
