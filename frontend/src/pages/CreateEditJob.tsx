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
import { Copy, ExternalLink, Loader2, Sparkles, Building2, DollarSign, Briefcase, Target, Users, Settings } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import apiService from "@/services/api";

// Helper component for AI-generated field marker
const AIGeneratedBadge = () => (
  <Badge variant="secondary" className="ml-2 text-xs bg-gradient-to-r from-blue-100 to-purple-100 text-blue-700 border-blue-200">
    <span className="mr-1">🤖</span>
    AI Generated
  </Badge>
);

// Helper component for section headers
const SectionHeader = ({ icon: Icon, title, description }: { icon: any, title: string, description: string }) => (
  <div className="flex items-center space-x-3 mb-6">
    <div className="p-2 bg-blue-100 rounded-lg">
      <Icon className="h-5 w-5 text-blue-600" />
    </div>
    <div>
      <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  </div>
);

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

interface Compensation {
  base_salary?: number | null;
  benefits?: string[] | null;
}

interface Skills {
  hard_skills?: string[] | null;
  soft_skills?: string[] | null;
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
    department: "",
    compensation: {
      base_salary: 0,
      benefits: [],
    } as Compensation,
    experience_level: ExperienceLevel.NO_EXPERIENCE,
    seniority_level: SeniorityLevel.ENTRY,
    job_type: JobType.FULL_TIME,
    job_category: "",
    responsibilities: [],
    skills: {
      hard_skills: [],
      soft_skills: [],
    } as Skills,
    status: JobStatus.DRAFT,
    recruited_to_id: null,
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
  const [ai_input, set_ai_input] = useState<string>("");
  const [is_generating, set_is_generating] = useState(false);
  const [ai_generated_fields, set_ai_generated_fields] = useState<Set<string>>(new Set());

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
      
      console.log("Fetched job data:", job); // Debug log
      console.log("Responsibilities from API:", job.responsibilities); // Debug log
      
      // Handle recruited_to_id properly
      let recruited_to_value = null;
      if (job.recruited_to_id !== null && job.recruited_to_id !== undefined) {
        recruited_to_value = job.recruited_to_id;
      }
      
      const new_job_data = {
        title: job.title || "",
        description: job.description || "",
        location: job.location || "",
        department: job.department || "",
        compensation: {
          base_salary: job.compensation?.base_salary || 0,
          benefits: Array.isArray(job.compensation?.benefits) 
            ? job.compensation.benefits 
            : job.compensation?.benefits && typeof job.compensation.benefits === 'object' 
              ? Object.values(job.compensation.benefits) 
              : []
        },
        experience_level: job.experience_level || ExperienceLevel.NO_EXPERIENCE,
        seniority_level: job.seniority_level || SeniorityLevel.ENTRY,
        job_type: job.job_type || JobType.FULL_TIME,
        job_category: job.job_category || "",
        responsibilities: Array.isArray(job.responsibilities) 
          ? job.responsibilities 
          : job.responsibilities && typeof job.responsibilities === 'object' 
            ? Object.values(job.responsibilities) 
            : [],
        skills: {
          hard_skills: Array.isArray(job.skills?.hard_skills) 
            ? job.skills.hard_skills 
            : job.skills?.hard_skills && typeof job.skills.hard_skills === 'object' 
              ? Object.values(job.skills.hard_skills) 
              : [],
          soft_skills: Array.isArray(job.skills?.soft_skills) 
            ? job.skills.soft_skills 
            : job.skills?.soft_skills && typeof job.skills.soft_skills === 'object' 
              ? Object.values(job.skills.soft_skills) 
              : []
        },
        status: job.status || JobStatus.DRAFT,
        recruited_to_id: recruited_to_value,
        auto_generate: false, // This is a UI state, not from backend model
      };
      
      console.log("Setting job data:", new_job_data); // Debug log
      console.log("Responsibilities in new_job_data:", new_job_data.responsibilities); // Debug log
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
    const new_constraints = {
      ...constraints,
      [key_id]: {
        ...constraints[key_id],
        [constraint_type]: value,
      },
    };
    console.log("Constraint changed:", { key_id, constraint_type, value, new_constraints }); // Debug log
    set_constraints(new_constraints);
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

  const handle_ai_generate = async () => {
    if (!ai_input.trim()) {
      toast({
        title: "Input required",
        description: "Please enter some text to generate job details.",
        variant: "destructive",
      });
      return;
    }

    set_is_generating(true);
    set_ai_generated_fields(new Set()); // Reset on new generation

    try {
      // Fix: Call the API with the correct structure - just pass the data string
      const response = await apiService.generateJobDescription(ai_input);
      
      const new_ai_generated_fields = new Set<string>();

      const update_state_if_changed = (field: keyof typeof job_data, value: any) => {
        if (value !== null && value !== undefined) {
          if (typeof value === 'object' && value !== null) {
            // For nested objects like compensation and skills
            set_job_data(prev => ({ ...prev, [field]: { ...prev[field], ...value } }));
          } else {
            set_job_data(prev => ({ ...prev, [field]: value }));
          }
          new_ai_generated_fields.add(field);
        }
      };
      
      update_state_if_changed("title", response.title);
      update_state_if_changed("description", response.description);
      update_state_if_changed("location", response.location);
      update_state_if_changed("job_type", response.job_type);
      update_state_if_changed("job_category", response.job_category);
      update_state_if_changed("experience_level", response.experience_level);
      update_state_if_changed("seniority_level", response.seniority_level);
      
      if (response.compensation) {
        update_state_if_changed("compensation", response.compensation);
        new_ai_generated_fields.add("compensation.base_salary");
      }
      if (response.responsibilities) {
        update_state_if_changed("responsibilities", response.responsibilities);
      }
      if (response.skills) {
        update_state_if_changed("skills", response.skills);
        new_ai_generated_fields.add("skills.hard_skills");
        new_ai_generated_fields.add("skills.soft_skills");
      }

      set_ai_generated_fields(new_ai_generated_fields);

      toast({
        title: "Success",
        description: "Job details have been generated by AI.",
      });

    } catch (error) {
      console.error("AI generation failed:", error);
      toast({
        title: "AI Generation Failed",
        description: error.message || "An unexpected error occurred.",
        variant: "destructive",
      });
    } finally {
      set_is_generating(false);
    }
  };

  const handle_save = async () => {
    set_is_submitting(true);
    set_error(null);

    // Basic validation
    if (!job_data.title) {
      set_error("Title is required");
      set_is_submitting(false);
      toast({
        title: "Error",
        description: "Job title is required",
        variant: "destructive",
      });
      return;
    }

    // Helper function to convert object-like arrays to proper arrays
    const normalizeArray = (data: any): any[] => {
      if (Array.isArray(data)) {
        return data;
      }
      if (data && typeof data === 'object') {
        return Object.values(data);
      }
      return [];
    };

    // Deep copy and prepare payload
    const payload = JSON.parse(JSON.stringify(job_data));

    // Normalize array fields to ensure they're proper arrays
    payload.responsibilities = normalizeArray(payload.responsibilities);
    
    if (payload.skills) {
      payload.skills.hard_skills = normalizeArray(payload.skills.hard_skills);
      payload.skills.soft_skills = normalizeArray(payload.skills.soft_skills);
    }
    
    if (payload.compensation && payload.compensation.benefits) {
      payload.compensation.benefits = normalizeArray(payload.compensation.benefits);
    }

    // Convert salary to number
    if (payload.compensation.base_salary) {
      payload.compensation.base_salary = parseInt(payload.compensation.base_salary, 10);
      if (isNaN(payload.compensation.base_salary)) {
        payload.compensation.base_salary = null;
      }
    }

    // recruited_to_id should be null if not set, not 0 or empty string
    if (!payload.recruited_to_id) {
      payload.recruited_to_id = null;
    }
    
    // Remove UI-specific fields
    delete payload.auto_generate;

    console.log("Payload being sent to API:", payload); // Debug log

    try {
      let saved_job;
      if (is_editing && current_job_id) {
        saved_job = await apiService.updateJob(parseInt(current_job_id), payload);
      } else {
        saved_job = await apiService.createJob(payload);
      }
      
      const new_job_id = saved_job.id;

      // Save constraints if any are selected
      if (selected_form_keys.length > 0) {
        const constraint_payload: JobFormKeyConstraint[] = selected_form_keys.map(key_id => {
          // Clean up constraints by removing empty values
          const raw_constraints = constraints[key_id] || {};
          const cleaned_constraints = {};
          
          Object.entries(raw_constraints).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== "") {
              cleaned_constraints[key] = value;
            }
          });

          return {
            job_id: new_job_id,
            form_key_id: key_id,
            constraints: cleaned_constraints,
          };
        });

        console.log("Constraint payload being sent:", constraint_payload); // Debug log

        try {
          const result = await apiService.setConstraintsForJob(new_job_id, constraint_payload);
          console.log("Constraints saved successfully:", result); // Debug log
        } catch (constraint_error) {
          console.error("Failed to save constraints:", constraint_error);
          console.error("Constraint error details:", constraint_error.response?.data || constraint_error.message);
          toast({
            title: "Warning",
            description: "Job saved, but failed to save form constraints.",
            variant: "destructive",
          });
        }
      }

      toast({
        title: "Success",
        description: `Job ${is_editing ? 'updated' : 'created'} successfully.`,
      });
      navigate(`/jobs/${new_job_id}`);
    } catch (err) {
      console.error("Failed to save job:", err);
      const error_message = err.response?.data?.detail || err.message || "An unexpected error occurred";
      set_error(error_message);
      toast({
        title: "Error",
        description: `Failed to save job: ${error_message}`,
        variant: "destructive",
      });
    } finally {
      set_is_submitting(false);
    }
  };

  const handle_nested_change = (field: string, subfield: string, value: any) => {
    set_job_data(prev => ({
      ...prev,
      [field]: {
        ...prev[field],
        [subfield]: value,
      },
    }));
  };

  if (is_loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
          <div className="text-center space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
            <span className="text-lg font-medium text-gray-700">
              {is_editing ? "Loading job data..." : "Loading form..."}
            </span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
          <Card className="w-full max-w-md shadow-xl border-0">
            <CardContent className="text-center p-8 space-y-4">
              <p className="text-red-600 font-semibold text-lg mb-4">Error: {error}</p>
            <Button onClick={() => window.location.reload()} className="w-full">
              Retry
            </Button>
            </CardContent>
          </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto p-6 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
            {is_editing ? "Edit Job" : "Create New Job"}
          </h1>
              <p className="text-gray-600 mt-2">
                {is_editing ? "Update the details of the job listing." : "Fill in the form to create a new job listing."}
          </p>
        </div>
        {is_editing && (
          <div className="flex gap-3">
                <Button variant="outline" onClick={generate_form_url}>
              <ExternalLink className="mr-2 h-4 w-4" />
              Generate URL
            </Button>
            {generated_url && (
                  <Button variant="outline" onClick={() => {
                  navigator.clipboard.writeText(generated_url);
                  toast({
                    title: "URL Copied!",
                    description: "The application URL has been copied to your clipboard.",
                  });
                  }}>
                <Copy className="mr-2 h-4 w-4" />
                Copy URL
              </Button>
            )}
          </div>
        )}
          </div>
      </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* AI Generation Section */}
      {!is_editing && (
              <Card className="border-0 shadow-lg bg-gradient-to-r from-blue-50 to-purple-50">
          <CardHeader className="pb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Sparkles className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <CardTitle className="text-xl">AI-Powered Job Generation</CardTitle>
                      <CardDescription>
                        Describe the job in your own words, and let AI fill in the details.
            </CardDescription>
                    </div>
                  </div>
          </CardHeader>
          <CardContent className="space-y-4">
              <Textarea
                    placeholder="e.g., 'We need a senior frontend developer with React and TypeScript experience to build a new design system. The role is remote, pays 80-120k, and requires 3+ years of experience...'"
                value={ai_input}
                onChange={(e) => set_ai_input(e.target.value)}
                    rows={4}
                    className="resize-none"
              />
            <Button 
              onClick={handle_ai_generate} 
              disabled={is_generating || !ai_input.trim()}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            >
              {is_generating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Generate with AI
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

            {/* Core Job Details */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <SectionHeader 
                  icon={Building2} 
                  title="Core Job Details" 
                  description="Essential information about the position"
                />
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <Label htmlFor="title" className="text-sm font-medium">
                      Job Title {ai_generated_fields.has('title') && <AIGeneratedBadge />}
                  </Label>
                  <Input
                    id="title"
                    value={job_data.title}
                    onChange={(e) => set_job_data({ ...job_data, title: e.target.value })}
                    placeholder="e.g., Senior Frontend Developer"
                      className="h-11"
                  />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="location" className="text-sm font-medium">
                      Location {ai_generated_fields.has('location') && <AIGeneratedBadge />}
                  </Label>
                  <Input
                    id="location"
                    value={job_data.location}
                    onChange={(e) => set_job_data({ ...job_data, location: e.target.value })}
                      placeholder="e.g., San Francisco, CA or Remote"
                      className="h-11"
                  />
                </div>
                  <div className="space-y-2">
                    <Label htmlFor="department" className="text-sm font-medium">Department</Label>
                    <Input
                      id="department"
                      value={job_data.department}
                      onChange={(e) => set_job_data({ ...job_data, department: e.target.value })}
                      placeholder="e.g., Engineering, Marketing"
                      className="h-11"
                    />
              </div>
              <div className="space-y-2">
                    <Label htmlFor="job_category" className="text-sm font-medium">
                      Job Category {ai_generated_fields.has('job_category') && <AIGeneratedBadge />}
                    </Label>
                    <Input
                      id="job_category"
                      value={job_data.job_category}
                      onChange={(e) => set_job_data({ ...job_data, job_category: e.target.value })}
                      placeholder="e.g., Software Engineering, Product Management"
                      className="h-11"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description" className="text-sm font-medium">
                    Job Description {ai_generated_fields.has('description') && <AIGeneratedBadge />}
                </Label>
                <Textarea
                  id="description"
                  value={job_data.description}
                  onChange={(e) => set_job_data({ ...job_data, description: e.target.value })}
                  placeholder="Describe the role, responsibilities, and what you're looking for..."
                    rows={6}
                    className="resize-none"
                />
              </div>
              </CardContent>
            </Card>

            {/* Compensation */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <SectionHeader 
                  icon={DollarSign} 
                  title="Compensation" 
                  description="Salary and benefits information"
                />
              </CardHeader>
              <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <Label htmlFor="base_salary" className="text-sm font-medium">
                      Base Salary {ai_generated_fields.has('compensation.base_salary') && <AIGeneratedBadge />}
                  </Label>
                  <Input
                      id="base_salary"
                    type="number"
                      value={job_data.compensation.base_salary || ""}
                      onChange={(e) => handle_nested_change("compensation", "base_salary", e.target.value ? parseInt(e.target.value, 10) : null)}
                      placeholder="e.g., 90000"
                      className="h-11"
                  />
                </div>
                </div>
              <div className="space-y-2">
                  <Label htmlFor="benefits" className="text-sm font-medium">Benefits (one per line)</Label>
                  <Textarea
                    id="benefits"
                    value={Array.isArray(job_data.compensation.benefits) ? job_data.compensation.benefits.join("\n") : ""}
                    onChange={(e) => set_job_data({ ...job_data, compensation: { ...job_data.compensation, benefits: e.target.value.split("\n") } })}
                    placeholder="e.g., Health Insurance&#10;401(k) Matching&#10;Remote Work&#10;Stock Options"
                    rows={4}
                    className="resize-none"
                />
              </div>
            </CardContent>
          </Card>

            {/* Job Attributes */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <SectionHeader 
                  icon={Briefcase} 
                  title="Job Attributes" 
                  description="Type, experience, and seniority requirements"
                />
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                    <Label htmlFor="job_type" className="text-sm font-medium">
                      Job Type {ai_generated_fields.has('job_type') && <AIGeneratedBadge />}
                </Label>
                <Select
                      value={job_data.job_type}
                      onValueChange={(value) => set_job_data({ ...job_data, job_type: value })}
                >
                      <SelectTrigger className="h-11">
                        <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                        {Object.entries(JobType).map(([key, value]) => (
                      <SelectItem key={key} value={value}>
                            {value.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                    <Label htmlFor="experience_level" className="text-sm font-medium">
                      Experience Level {ai_generated_fields.has('experience_level') && <AIGeneratedBadge />}
                </Label>
                <Select
                      value={job_data.experience_level}
                      onValueChange={(value) => set_job_data({ ...job_data, experience_level: value })}
                >
                      <SelectTrigger className="h-11">
                        <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                        {Object.entries(ExperienceLevel).map(([key, value]) => (
                      <SelectItem key={key} value={value}>
                            {value.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                    <Label htmlFor="seniority_level" className="text-sm font-medium">
                      Seniority Level {ai_generated_fields.has('seniority_level') && <AIGeneratedBadge />}
                </Label>
                <Select
                      value={job_data.seniority_level}
                      onValueChange={(value) => set_job_data({ ...job_data, seniority_level: value })}
                >
                      <SelectTrigger className="h-11">
                        <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                        {Object.entries(SeniorityLevel).map(([key, value]) => (
                      <SelectItem key={key} value={value}>
                            {value.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
                </div>
              </CardContent>
            </Card>

            {/* Responsibilities and Skills */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <SectionHeader 
                  icon={Target} 
                  title="Responsibilities & Skills" 
                  description="What the role entails and required competencies"
                />
              </CardHeader>
              <CardContent className="space-y-6">
              <div className="space-y-2">
                  <Label htmlFor="responsibilities" className="text-sm font-medium">
                    Responsibilities (one per line) {ai_generated_fields.has('responsibilities') && <AIGeneratedBadge />}
                  </Label>
                  <Textarea
                    id="responsibilities"
                    value={(() => {
                      let responsibilities = job_data.responsibilities;
                      // Convert object to array if needed
                      if (!Array.isArray(responsibilities) && responsibilities && typeof responsibilities === 'object') {
                        responsibilities = Object.values(responsibilities);
                      }
                      const value = Array.isArray(responsibilities) ? responsibilities.join("\n") : "";
                      console.log("Responsibilities textarea value:", value, "from data:", job_data.responsibilities);
                      return value;
                    })()}
                    onChange={(e) => set_job_data({ ...job_data, responsibilities: e.target.value.split("\n").filter(item => item.trim() !== "") })}
                    placeholder="e.g., Develop and maintain web applications&#10;Collaborate with cross-functional teams&#10;Participate in code reviews&#10;Mentor junior developers"
                    rows={6}
                    className="resize-none"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="hard_skills" className="text-sm font-medium">
                      Hard Skills (one per line) {ai_generated_fields.has('skills.hard_skills') && <AIGeneratedBadge />}
                    </Label>
                    <Textarea
                      id="hard_skills"
                      value={(() => {
                        let hard_skills = job_data.skills.hard_skills;
                        if (!Array.isArray(hard_skills) && hard_skills && typeof hard_skills === 'object') {
                          hard_skills = Object.values(hard_skills);
                        }
                        return Array.isArray(hard_skills) ? hard_skills.join("\n") : "";
                      })()}
                      onChange={(e) => set_job_data({ ...job_data, skills: { ...job_data.skills, hard_skills: e.target.value.split("\n").filter(item => item.trim() !== "") } })}
                      placeholder="e.g., React&#10;TypeScript&#10;Node.js&#10;PostgreSQL"
                      rows={6}
                      className="resize-none"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="soft_skills" className="text-sm font-medium">
                      Soft Skills (one per line) {ai_generated_fields.has('skills.soft_skills') && <AIGeneratedBadge />}
                    </Label>
                    <Textarea
                      id="soft_skills"
                      value={(() => {
                        let soft_skills = job_data.skills.soft_skills;
                        if (!Array.isArray(soft_skills) && soft_skills && typeof soft_skills === 'object') {
                          soft_skills = Object.values(soft_skills);
                        }
                        return Array.isArray(soft_skills) ? soft_skills.join("\n") : "";
                      })()}
                      onChange={(e) => handle_nested_change("skills", "soft_skills", e.target.value.split("\n").filter(item => item.trim() !== ""))}
                      placeholder="e.g., Communication&#10;Problem Solving&#10;Teamwork&#10;Leadership"
                      rows={6}
                      className="resize-none"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Recruitment Settings */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <SectionHeader 
                  icon={Settings} 
                  title="Recruitment Settings" 
                  description="Job status and recruitment options"
                />
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="status" className="text-sm font-medium">Status</Label>
                <Select
                  value={job_data.status}
                  onValueChange={(value) => set_job_data({ ...job_data, status: value })}
                >
                    <SelectTrigger className="h-11">
                      <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(JobStatus).map(([key, value]) => (
                      <SelectItem key={key} value={value}>
                          {value.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                  <Label htmlFor="recruited_to_id" className="text-sm font-medium">Recruited To</Label>
                <Select
                  value={job_data.recruited_to_id?.toString() || "none"}
                  onValueChange={(value) => set_job_data({ ...job_data, recruited_to_id: value === "none" ? null : parseInt(value) })}
                >
                    <SelectTrigger className="h-11">
                    <SelectValue placeholder="Select a company (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    {recruit_to_companies.length === 0 ? (
                      <SelectItem value="no-companies" disabled>No companies available</SelectItem>
                    ) : (
                      recruit_to_companies.map((company) => (
                        <SelectItem key={company.id} value={company.id.toString()}>
                          {company.name}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                  <p className="text-xs text-gray-500">
                  Select a company you are recruiting for (leave empty if recruiting for your own company)
                </p>
              </div>
            </CardContent>
          </Card>

            {/* Form Keys & Constraints */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <SectionHeader 
                  icon={Users} 
                  title="Form Keys & Constraints" 
                  description="Custom application form fields"
                />
            </CardHeader>
              <CardContent className="space-y-4">
              {form_keys.length === 0 ? (
                  <div className="text-center py-6">
                    <p className="text-gray-500 mb-4">No form keys available</p>
                    <Button variant="outline" onClick={() => navigate("/form-keys")} className="w-full">
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
                        <Label htmlFor={`formKey-${form_key.id}`} className="flex-1 text-sm">
                        {form_key.name}
                      </Label>
                        <Badge variant="outline" className="text-xs">{form_key.field_type}</Badge>
                      {form_key.required && (
                        <Badge variant="secondary" className="text-xs">Required</Badge>
                      )}
                    </div>

                    {selected_form_keys.includes(form_key.id) && (
                        <div className="ml-6 space-y-2 p-3 bg-gray-50 rounded-lg">
                          <Label className="text-xs font-medium">Constraints</Label>
                        {form_key.field_type === "number" && (
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <Label className="text-xs">Min Value</Label>
                              <Input
                                type="number"
                                placeholder="0"
                                value={constraints[form_key.id]?.min_value || ""}
                                onChange={(e) => 
                                  handle_constraint_change(form_key.id, "min_value", e.target.value ? parseInt(e.target.value, 10) : "")
                                }
                                  className="h-8 text-xs"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Max Value</Label>
                              <Input
                                type="number"
                                placeholder="10"
                                value={constraints[form_key.id]?.max_value || ""}
                                onChange={(e) => 
                                  handle_constraint_change(form_key.id, "max_value", e.target.value ? parseInt(e.target.value, 10) : "")
                                }
                                  className="h-8 text-xs"
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
                                className="h-8 text-xs"
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
                                  className="h-8 text-xs"
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
                                  className="h-8 text-xs"
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
        </div>
      </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
          <Button variant="outline" onClick={() => navigate("/jobs")} disabled={is_submitting}>
            Cancel
          </Button>
          <Button onClick={handle_save} disabled={is_submitting} className="px-8">
            {is_submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {is_editing ? "Updating..." : "Creating..."}
              </>
            ) : (
              is_editing ? "Update Job" : "Create Job"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CreateEditJob;
