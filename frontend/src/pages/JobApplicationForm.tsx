import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { Building2, MapPin, DollarSign, Clock, Briefcase, Upload, Send } from "lucide-react";
import { toast } from "@/components/ui/sonner";

interface JobData {
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
  employer_id: number;
  created_at: string;
}

interface FormKey {
  id: number;
  name: string;
  field_type: string;
  required: boolean;
  enum_values?: string[];
}

interface JobFormData {
  job: JobData;
  form_keys: FormKey[];
}

const JobApplicationForm = () => {
  const { job_id } = useParams<{ job_id: string }>();
  const [job_data, set_job_data] = useState<JobFormData | null>(null);
  const [is_loading, set_is_loading] = useState(true);
  const [is_submitting, set_is_submitting] = useState(false);
  const [resume_file, set_resume_file] = useState<File | null>(null);

  // Candidate form data
  const [candidate_data, set_candidate_data] = useState({
    full_name: "",
    email: "",
    phone: "",
  });

  // Dynamic form responses
  const [form_responses, set_form_responses] = useState<Record<string, any>>({});

  useEffect(() => {
    if (job_id) {
      load_job_data();
    }
  }, [job_id]);

  const load_job_data = async () => {
    set_is_loading(true);
    try {
      // Make a public API call without authentication
      const response = await fetch(`http://84.16.230.94:8017/api/v1/jobs/public/form-data/${job_id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      set_job_data(data);
    } catch (error: any) {
      toast.error("Failed to load job information", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_loading(false);
    }
  };

  const handle_candidate_change = (field: string, value: string) => {
    set_candidate_data(prev => ({ ...prev, [field]: value }));
  };

  const handle_form_response_change = (form_key_id: number, value: any) => {
    set_form_responses(prev => ({ ...prev, [form_key_id]: value }));
  };

  const handle_resume_change = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!allowed_types.includes(file.type)) {
        toast.error("Invalid file type", {
          description: "Please upload a PDF or Word document.",
        });
        return;
      }
      
      // Validate file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        toast.error("File too large", {
          description: "Please upload a file smaller than 5MB.",
        });
        return;
      }
      
      set_resume_file(file);
    }
  };

  const validate_form = () => {
    // Validate candidate data
    if (!candidate_data.full_name.trim()) {
      toast.error("Full name is required");
      return false;
    }
    if (!candidate_data.email.trim()) {
      toast.error("Email is required");
      return false;
    }
    if (!resume_file) {
      toast.error("Resume is required");
      return false;
    }

    // Validate required form fields
    if (job_data?.form_keys) {
      for (const form_key of job_data.form_keys) {
        if (form_key.required && !form_responses[form_key.id]) {
          toast.error(`${form_key.name} is required`);
          return false;
        }
      }
    }

    return true;
  };

  const submit_application = async () => {
    if (!validate_form() || !job_data) return;

    set_is_submitting(true);
    try {
      // Step 1: Create candidate with resume
      const candidate_form_data = new FormData();
      candidate_form_data.append('candidate_in', JSON.stringify(candidate_data));
      candidate_form_data.append('resume', resume_file!);

      const candidate_response = await fetch('http://84.16.230.94:8017/api/v1/candidates/', {
        method: 'POST',
        body: candidate_form_data,
      });

      if (!candidate_response.ok) {
        throw new Error(`Failed to create candidate: ${candidate_response.status}`);
      }

      const created_candidate = await candidate_response.json();

      // Step 2: Create application
      const application_data = {
        candidate_id: created_candidate.id,
        job_id: parseInt(job_id!),
        form_responses: form_responses,
      };

      const application_response = await fetch('http://84.16.230.94:8017/api/v1/applications/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(application_data),
      });

      if (!application_response.ok) {
        throw new Error(`Failed to create application: ${application_response.status}`);
      }

      toast.success("Application submitted successfully!", {
        description: "Thank you for your interest. We'll be in touch soon.",
      });

      // Reset form
      set_candidate_data({ full_name: "", email: "", phone: "" });
      set_form_responses({});
      set_resume_file(null);

    } catch (error: any) {
      toast.error("Failed to submit application", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_submitting(false);
    }
  };

  const render_form_field = (form_key: FormKey) => {
    const value = form_responses[form_key.id] || "";

    switch (form_key.field_type) {
      case "text":
      case "email":
        return (
          <Input
            type={form_key.field_type}
            value={value}
            onChange={(e) => handle_form_response_change(form_key.id, e.target.value)}
            placeholder={`Enter ${form_key.name.toLowerCase()}`}
            required={form_key.required}
          />
        );

      case "number":
        return (
          <Input
            type="number"
            value={value}
            onChange={(e) => handle_form_response_change(form_key.id, e.target.value)}
            placeholder={`Enter ${form_key.name.toLowerCase()}`}
            required={form_key.required}
          />
        );

      case "textarea":
        return (
          <Textarea
            value={value}
            onChange={(e) => handle_form_response_change(form_key.id, e.target.value)}
            placeholder={`Enter ${form_key.name.toLowerCase()}`}
            rows={4}
            required={form_key.required}
          />
        );

      case "select":
        return (
          <Select
            value={value}
            onValueChange={(val) => handle_form_response_change(form_key.id, val)}
            required={form_key.required}
          >
            <SelectTrigger>
              <SelectValue placeholder={`Select ${form_key.name.toLowerCase()}`} />
            </SelectTrigger>
            <SelectContent>
              {form_key.enum_values?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case "checkbox":
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              id={`checkbox-${form_key.id}`}
              checked={value === true}
              onCheckedChange={(checked) => handle_form_response_change(form_key.id, checked)}
              required={form_key.required}
            />
            <Label htmlFor={`checkbox-${form_key.id}`}>
              {form_key.name}
            </Label>
          </div>
        );

      case "date":
        return (
          <Input
            type="date"
            value={value}
            onChange={(e) => handle_form_response_change(form_key.id, e.target.value)}
            required={form_key.required}
          />
        );

      default:
        return (
          <Input
            value={value}
            onChange={(e) => handle_form_response_change(form_key.id, e.target.value)}
            placeholder={`Enter ${form_key.name.toLowerCase()}`}
            required={form_key.required}
          />
        );
    }
  };

  const format_salary = (min?: number, max?: number) => {
    if (min && max) {
      return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    } else if (min) {
      return `$${min.toLocaleString()}+`;
    } else if (max) {
      return `Up to $${max.toLocaleString()}`;
    }
    return "Competitive";
  };

  const format_experience_level = (level: string) => {
    return level.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (is_loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Loading job information...</p>
        </div>
      </div>
    );
  }

  if (!job_data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md">
          <CardContent className="text-center py-8">
            <h2 className="text-xl font-semibold mb-2">Job Not Found</h2>
            <p className="text-muted-foreground">
              The job you're looking for doesn't exist or has been removed.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Job Information */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-2xl mb-2">{job_data.job.title}</CardTitle>
                <div className="flex items-center gap-4 text-muted-foreground mb-4">
                  <div className="flex items-center gap-1">
                    <Building2 className="h-4 w-4" />
                    <span>Company</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    <span>{job_data.job.location}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <DollarSign className="h-4 w-4" />
                    <span>{format_salary(job_data.job.salary_min, job_data.job.salary_max)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1">
                    <Briefcase className="h-4 w-4" />
                    <span>{format_experience_level(job_data.job.job_type)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    <span>{format_experience_level(job_data.job.experience_level)}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Job Description</h3>
                <p className="text-muted-foreground whitespace-pre-wrap">
                  {job_data.job.description}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Application Form */}
        <Card>
          <CardHeader>
            <CardTitle>Apply for this Position</CardTitle>
            <CardDescription>
              Fill out the form below to submit your application
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Candidate Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Personal Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name *</Label>
                  <Input
                    id="full_name"
                    value={candidate_data.full_name}
                    onChange={(e) => handle_candidate_change("full_name", e.target.value)}
                    placeholder="Enter your full name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={candidate_data.email}
                    onChange={(e) => handle_candidate_change("email", e.target.value)}
                    placeholder="Enter your email"
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={candidate_data.phone}
                  onChange={(e) => handle_candidate_change("phone", e.target.value)}
                  placeholder="Enter your phone number"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="resume">Resume *</Label>
                <div className="flex items-center gap-4">
                  <Input
                    id="resume"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handle_resume_change}
                    required
                  />
                  <div className="text-sm text-muted-foreground">
                    PDF, DOC, or DOCX (max 5MB)
                  </div>
                </div>
                {resume_file && (
                  <div className="flex items-center gap-2 text-sm text-green-600">
                    <Upload className="h-4 w-4" />
                    <span>{resume_file.name}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Dynamic Form Fields */}
            {job_data.form_keys.length > 0 && (
              <>
                <Separator />
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Additional Information</h3>
                  {job_data.form_keys.map((form_key) => (
                    <div key={form_key.id} className="space-y-2">
                      <Label htmlFor={`form-${form_key.id}`}>
                        {form_key.name}
                        {form_key.required && <span className="text-red-500 ml-1">*</span>}
                      </Label>
                      {render_form_field(form_key)}
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* Submit Button */}
            <div className="pt-6">
              <Button
                onClick={submit_application}
                disabled={is_submitting}
                className="w-full"
                size="lg"
              >
                {is_submitting ? (
                  "Submitting Application..."
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Submit Application
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default JobApplicationForm; 