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
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";
import { Building2, MapPin, DollarSign, Clock, Briefcase, Upload, Send, Loader2, XCircle, User, FileTextIcon, Mail, Shield, CheckCircle, AlertCircle } from "lucide-react";
import { toast } from "@/components/ui/sonner";
import apiService from "@/services/api";

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

  // Email verification states
  const [email_verified, set_email_verified] = useState(false);
  const [otp_sent, set_otp_sent] = useState(false);
  const [is_sending_otp, set_is_sending_otp] = useState(false);
  const [is_verifying_otp, set_is_verifying_otp] = useState(false);
  const [otp_code, set_otp_code] = useState("");
  const [otp_expires_in, set_otp_expires_in] = useState(0);
  const [otp_timer, set_otp_timer] = useState<NodeJS.Timeout | null>(null);
  
  // Existing candidate states
  const [existing_candidate, set_existing_candidate] = useState<any>(null);
  const [is_checking_email, set_is_checking_email] = useState(false);
  const [is_existing_user, set_is_existing_user] = useState(false);
  const [show_existing_data, set_show_existing_data] = useState(false);

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

  // OTP timer effect
  useEffect(() => {
    if (otp_expires_in > 0) {
      const timer = setTimeout(() => {
        set_otp_expires_in(prev => prev - 1);
      }, 1000);
      set_otp_timer(timer);
      return () => clearTimeout(timer);
    } else if (otp_sent && otp_expires_in === 0) {
      set_otp_sent(false);
      toast.error("OTP expired", {
        description: "Please request a new verification code.",
      });
    }
  }, [otp_expires_in, otp_sent]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (otp_timer) {
        clearTimeout(otp_timer);
      }
    };
  }, [otp_timer]);

  const load_job_data = async () => {
    set_is_loading(true);
    try {
      // Make a public API call without authentication
      const response = await fetch(`http://84.16.230.94:8017/api/v1/jobs/public/form-data/${job_id}`);
      if (!response.ok) {
        let error_message = `HTTP error! status: ${response.status}`;
        try {
          const error_data = await response.json();
          error_message = error_data?.detail || error_data?.message || error_message;
        } catch (e) {
          // If response is not JSON, use default message
        }
        toast.error("Failed to load job information", {
          description: error_message,
        });
        throw new Error(error_message);
      }
      const data = await response.json();
      console.log('Received job data:', data);
      console.log('Form keys:', data.form_keys);
      set_job_data(data);
    } catch (error: any) {
      toast.error("Failed to load job information", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_loading(false);
    }
  };

  const check_candidate_email = async (email: string) => {
    if (!email.trim() || !email.includes('@')) return;
    
    set_is_checking_email(true);
    try {
      const response = await apiService.checkCandidateEmail(email);
      
      if (response.exists) {
        set_existing_candidate(response.candidate);
        set_is_existing_user(true);
        // Don't pre-fill data until verified
      } else {
        set_existing_candidate(null);
        set_is_existing_user(false);
      }
    } catch (error: any) {
      console.error("Error checking candidate email:", error);
      // Don't show error to user for this check, just continue as new user
      set_existing_candidate(null);
      set_is_existing_user(false);
    } finally {
      set_is_checking_email(false);
    }
  };

  const handle_candidate_change = (field: string, value: string) => {
    set_candidate_data(prev => {
      // Reset email verification if email changes
      if (field === 'email' && value !== prev.email) {
        set_email_verified(false);
        set_otp_sent(false);
        set_otp_code("");
        set_otp_expires_in(0);
        set_existing_candidate(null);
        set_is_existing_user(false);
        set_show_existing_data(false);
        if (otp_timer) {
          clearTimeout(otp_timer);
          set_otp_timer(null);
        }
        
        // Check if email exists after a short delay
        if (value.trim() && value.includes('@')) {
          setTimeout(() => check_candidate_email(value), 500);
        }
      }
      
      return { ...prev, [field]: value };
    });
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

  const send_otp = async () => {
    if (!candidate_data.email.trim()) {
      toast.error("Please enter your email address first");
      return;
    }

    set_is_sending_otp(true);
    try {
      // Use the full name from existing candidate if available, otherwise use the form data
      const full_name = is_existing_user && existing_candidate 
        ? existing_candidate.full_name 
        : candidate_data.full_name;
        
      const response = await apiService.sendOTP(candidate_data.email, full_name);
      
      if (response.success) {
        set_otp_sent(true);
        set_otp_expires_in(response.expires_in_minutes * 60); // Convert to seconds
        
        if (is_existing_user) {
          toast.success("Verification code sent!", {
            description: `Welcome back! Please check your email at ${candidate_data.email}`,
          });
        } else {
          toast.success("Verification code sent!", {
            description: `Please check your email at ${candidate_data.email}`,
          });
        }
      } else {
        throw new Error(response.message || "Failed to send OTP");
      }
    } catch (error: any) {
      console.error("OTP send error:", error);
      toast.error("Failed to send verification code", {
        description: error?.message || "Please try again.",
      });
    } finally {
      set_is_sending_otp(false);
    }
  };

  const verify_otp = async () => {
    if (!otp_code || otp_code.length !== 6) {
      toast.error("Please enter the complete 6-digit code");
      return;
    }

    set_is_verifying_otp(true);
    try {
      const response = await apiService.verifyOTP(candidate_data.email, otp_code);
      
      if (response.success) {
        set_email_verified(true);
        set_otp_sent(false);
        set_otp_expires_in(0);
        if (otp_timer) {
          clearTimeout(otp_timer);
          set_otp_timer(null);
        }
        
        // If existing user, show their data and pre-fill form after verification
        if (is_existing_user && existing_candidate) {
          set_show_existing_data(true);
          set_candidate_data(prev => ({
            ...prev,
            full_name: existing_candidate.full_name || prev.full_name,
            phone: existing_candidate.phone || prev.phone,
          }));
          toast.success("Welcome back!", {
            description: "Your existing profile has been loaded. You can update your information below.",
          });
        } else {
          toast.success("Email verified successfully!", {
            description: "You can now submit your application.",
          });
        }
      } else {
        throw new Error(response.message || "Invalid verification code");
      }
    } catch (error: any) {
      console.error("OTP verify error:", error);
      
      // Handle different error types
      if (error.status === 410) {
        // OTP expired or not found
        set_otp_sent(false);
        set_otp_expires_in(0);
        toast.error("Verification code expired", {
          description: "Please request a new code.",
        });
      } else {
        toast.error("Invalid verification code", {
          description: error?.detail?.message || error?.message || "Please try again.",
        });
      }
    } finally {
      set_is_verifying_otp(false);
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
    if (!email_verified) {
      toast.error("Email verification is required");
      return false;
    }
    
    // Resume validation: Required for new users, optional for existing users with resume on file
    const has_existing_resume = show_existing_data && existing_candidate?.has_resume;
    if (!resume_file && !has_existing_resume) {
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
      if (resume_file) {
        candidate_form_data.append('resume', resume_file);
      }
      // Add job_id to automatically associate candidate with job's employer
      if (job_id) {
        candidate_form_data.append('job_id', job_id);
      }

      const candidate_response = await fetch('http://84.16.230.94:8017/api/v1/candidates/', {
        method: 'POST',
        body: candidate_form_data,
      });

      if (!candidate_response.ok) {
        const error_data = await candidate_response.json();
        const error_message = error_data?.detail || error_data?.message || `Failed to create candidate: ${candidate_response.status}`;
        toast.error("Failed to create candidate", {
          description: error_message,
        });
        throw new Error(error_message);
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
        const error_data = await application_response.json();
        const error_message = error_data?.detail || error_data?.message || `Failed to create application: ${application_response.status}`;
        toast.error("Failed to create application", {
          description: error_message,
        });
        throw new Error(error_message);
      }

      toast.success("Application submitted successfully!", {
        description: "Thank you for your interest. We'll be in touch soon.",
      });

      // Reset form
      set_candidate_data({ full_name: "", email: "", phone: "" });
      set_form_responses({});
      set_resume_file(null);
      set_email_verified(false);
      set_otp_sent(false);
      set_otp_code("");
      set_existing_candidate(null);
      set_is_existing_user(false);
      set_show_existing_data(false);

    } catch (error: any) {
      console.error("Application submission error:", error);
      toast.error("Failed to submit application", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_submitting(false);
    }
  };

  const format_time = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const render_email_verification = () => {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Mail className="h-5 w-5 text-blue-600" />
          <Label htmlFor="email" className="text-base font-semibold text-gray-700">
            Email Address *
          </Label>
          {is_checking_email && (
            <div className="flex items-center gap-1 text-blue-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm font-medium">Checking...</span>
            </div>
          )}
          {is_existing_user && existing_candidate && (
            <div className="flex items-center gap-1 text-orange-600">
              <User className="h-4 w-4" />
              <span className="text-sm font-medium">Existing Account</span>
            </div>
          )}
          {email_verified && (
            <div className="flex items-center gap-1 text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Verified</span>
            </div>
          )}
        </div>
        
        <div className="flex gap-2">
          <Input
            id="email"
            type="email"
            value={candidate_data.email}
            onChange={(e) => handle_candidate_change('email', e.target.value)} 
            placeholder="your.email@example.com"
            required
            disabled={email_verified}
            className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500 flex-1"
          />
          {!email_verified && (
            <Button
              type="button"
              onClick={send_otp}
              disabled={is_sending_otp || !candidate_data.email.trim() || otp_sent}
              className="h-12 px-6 bg-blue-600 hover:bg-blue-700 text-white font-medium"
            >
              {is_sending_otp ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Sending...
                </>
              ) : otp_sent ? (
                "Code Sent"
              ) : (
                "Send Code"
              )}
            </Button>
          )}
        </div>

        {is_existing_user && !email_verified && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2 text-orange-800">
              <User className="h-5 w-5" />
              <span className="font-medium">Existing Account Detected</span>
            </div>
            <p className="text-orange-700 text-sm">
              We found an existing account with this email address. Please verify your email address 
              to continue with your application and access your profile information.
            </p>
          </div>
        )}

        {otp_sent && !email_verified && (
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-6 space-y-6 shadow-lg">
            <div className="text-center space-y-2">
              <div className="flex justify-center">
                <div className="bg-blue-100 p-3 rounded-full">
                  <Shield className="h-8 w-8 text-blue-600" />
                </div>
              </div>
              <h3 className="text-xl font-bold text-blue-900">Verify Your Email</h3>
              <p className="text-blue-700 text-sm max-w-md mx-auto">
                We've sent a 6-digit verification code to
              </p>
              <p className="font-semibold text-blue-900 text-base">{candidate_data.email}</p>
              {is_existing_user && (
                <p className="text-orange-600 text-sm font-medium bg-orange-50 px-3 py-1 rounded-full inline-block">
                  🔐 This will unlock your existing profile
                </p>
              )}
            </div>
            
            <div className="space-y-4">
              <div className="text-center">
                <Label className="text-sm font-medium text-blue-800 block mb-3">Enter Verification Code</Label>
                <div className="flex justify-center">
                  <InputOTP
                    maxLength={6}
                    value={otp_code}
                    onChange={set_otp_code}
                  >
                    <InputOTPGroup className="gap-3">
                      <InputOTPSlot 
                        index={0} 
                        className="w-14 h-14 text-xl font-bold border-2 border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 rounded-lg bg-white shadow-sm transition-all duration-200 hover:border-blue-400" 
                      />
                      <InputOTPSlot 
                        index={1} 
                        className="w-14 h-14 text-xl font-bold border-2 border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 rounded-lg bg-white shadow-sm transition-all duration-200 hover:border-blue-400" 
                      />
                      <InputOTPSlot 
                        index={2} 
                        className="w-14 h-14 text-xl font-bold border-2 border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 rounded-lg bg-white shadow-sm transition-all duration-200 hover:border-blue-400" 
                      />
                      <InputOTPSlot 
                        index={3} 
                        className="w-14 h-14 text-xl font-bold border-2 border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 rounded-lg bg-white shadow-sm transition-all duration-200 hover:border-blue-400" 
                      />
                      <InputOTPSlot 
                        index={4} 
                        className="w-14 h-14 text-xl font-bold border-2 border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 rounded-lg bg-white shadow-sm transition-all duration-200 hover:border-blue-400" 
                      />
                      <InputOTPSlot 
                        index={5} 
                        className="w-14 h-14 text-xl font-bold border-2 border-blue-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 rounded-lg bg-white shadow-sm transition-all duration-200 hover:border-blue-400" 
                      />
                    </InputOTPGroup>
                  </InputOTP>
                </div>
              </div>
              
              <div className="flex justify-center">
                <Button
                  type="button"
                  onClick={verify_otp}
                  disabled={is_verifying_otp || otp_code.length !== 6}
                  className="h-12 px-8 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {is_verifying_otp ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin mr-2" />
                      Verifying...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-5 w-5 mr-2" />
                      Verify Code
                    </>
                  )}
                </Button>
              </div>
            </div>

            <div className="border-t border-blue-200 pt-4 space-y-3">
              <div className="flex items-center justify-center gap-2 text-sm text-blue-600">
                <Clock className="h-4 w-4" />
                <span>Code expires in: <strong>{format_time(otp_expires_in)}</strong></span>
              </div>
              
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-sm">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={send_otp}
                  disabled={is_sending_otp || otp_expires_in > 0}
                  className="text-blue-600 hover:text-blue-700 hover:bg-blue-100 font-medium transition-colors duration-200"
                >
                  {is_sending_otp ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-1" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Mail className="h-4 w-4 mr-1" />
                      Resend Code
                    </>
                  )}
                </Button>
                
                <p className="text-xs text-blue-500 text-center">
                  💡 Didn't receive the code? Check your spam folder
                </p>
              </div>
            </div>
          </div>
        )}

        {email_verified && !show_existing_data && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span className="text-green-800 font-medium">Email verified successfully!</span>
          </div>
        )}

        {email_verified && show_existing_data && existing_candidate && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2 text-green-800">
              <CheckCircle className="h-5 w-5" />
              <span className="font-medium">Welcome back, {existing_candidate.full_name}!</span>
            </div>
            <p className="text-green-700 text-sm">
              Your existing profile has been loaded. You can update your information below if needed.
            </p>
            <div className="bg-white rounded-md p-3 border border-green-200">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-600">Name:</span>
                  <p className="text-gray-800">{existing_candidate.full_name}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-600">Phone:</span>
                  <p className="text-gray-800">{existing_candidate.phone || 'Not provided'}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-600">Email:</span>
                  <p className="text-gray-800">{existing_candidate.email}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-600">Member since:</span>
                  <p className="text-gray-800">
                    {existing_candidate.created_at 
                      ? new Date(existing_candidate.created_at).toLocaleDateString()
                      : 'Unknown'
                    }
                  </p>
                </div>
                {existing_candidate.has_resume && (
                  <div className="col-span-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium text-gray-600">Resume:</span>
                        <p className="text-green-600 text-sm">✓ Resume on file</p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(`http://84.16.230.94:8017/api/v1/candidates/${existing_candidate.id}/resume`, '_blank')}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        View Current Resume
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
            <p className="text-green-600 text-xs">
              You can update your information in the form below and optionally upload a new resume for this application.
            </p>
          </div>
        )}
      </div>
    );
  };

  const render_form_field = (form_key: FormKey) => {
    const common_props = {
      id: `form_key_${form_key.id}`,
      value: form_responses[form_key.id] || '',
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | string) => {
        const value = typeof e === 'string' ? e : e.target.value;
        handle_form_response_change(form_key.id, value);
      },
      className: "h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500",
      required: form_key.required,
    };
    const select_common_props = {
      id: `form_key_${form_key.id}`,
      value: form_responses[form_key.id] || '',
      onValueChange: (value: string) => handle_form_response_change(form_key.id, value),
      required: form_key.required,
    };

    return (
      <div key={form_key.id} className="space-y-2">
        <Label htmlFor={common_props.id} className="text-base font-semibold text-gray-700">
          {form_key.name} {form_key.required && <span className="text-red-500">*</span>}
        </Label>
        {(() => {
    switch (form_key.field_type) {
      case "text":
      case "number":
      case "date":
        return <Input type={form_key.field_type} {...common_props} placeholder={`Your ${form_key.name.toLowerCase()}`} />;
      case "link":
        return <Input type="url" {...common_props} placeholder={`Your ${form_key.name.toLowerCase()}`} />;
      case "textarea":
        return <Textarea {...common_props} placeholder={`Tell us about your ${form_key.name.toLowerCase()}...`} rows={5} className="text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500 resize-none" />;
      case "select":
        return (
                <Select {...select_common_props}>
                  <SelectTrigger className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500">
              <SelectValue placeholder={`Select ${form_key.name.toLowerCase()}`} />
            </SelectTrigger>
            <SelectContent>
                    {form_key.enum_values?.map(option => (
                      <SelectItem key={option} value={option}>{option}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      case "checkbox":
        return (
                <div className="flex items-center space-x-2 pt-2">
            <Checkbox
                    id={common_props.id} 
                    checked={Boolean(form_responses[form_key.id])} 
                    onCheckedChange={checked => handle_form_response_change(form_key.id, checked)} 
            />
                  <Label htmlFor={common_props.id} className="text-base font-normal text-gray-700 cursor-pointer">
                    {form_key.name}
            </Label>
          </div>
        );
      default:
        return <Input type="text" {...common_props} placeholder={`Your ${form_key.name.toLowerCase()}`} />;
          }
        })()}
      </div>
        );
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-8">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <p className="text-lg font-medium text-gray-700">Loading application form...</p>
        </div>
      </div>
    );
  }

  if (!job_data?.job) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-8">
        <Card className="w-full max-w-lg shadow-2xl border-0 text-center">
          <CardHeader>
            <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <CardTitle className="text-3xl font-bold text-gray-800">Job Not Found</CardTitle>
            <CardDescription className="text-lg text-gray-600 mt-2">
              The job you are trying to apply for could not be found or is no longer available.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => window.history.back()} 
              className="button shadow-lg hover:shadow-xl transition-all duration-300 w-full mt-4"
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { job, form_keys } = job_data;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-blue-100 py-12 px-4 sm:px-6 lg:px-8">
      <header className="mb-12 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent sm:text-6xl">
          Apply for {job.title}
        </h1>
        <p className="mt-4 text-xl text-gray-600 max-w-3xl mx-auto">
          We are excited to see your application! Please fill out the form below to be considered for this role.
        </p>
      </header>

      <div className="max-w-4xl mx-auto space-y-10">
        <Card className="card shadow-2xl border-0 overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-blue-500 to-purple-500 p-6">
            <CardTitle className="text-2xl font-bold text-white flex items-center gap-3">
              <Briefcase className="h-7 w-7" />
              Job Details
            </CardTitle>
            <CardDescription className="text-blue-100 text-base mt-1">
              Review the key information about this position.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-8 grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6 text-base">
            <div className="flex items-center gap-3">
              <MapPin className="h-5 w-5 text-blue-600" />
              <div>
                <Label className="text-sm font-semibold text-gray-500">Location</Label>
                <p className="font-medium text-gray-800">{job.location}</p>
                  </div>
                </div>
            <div className="flex items-center gap-3">
              <DollarSign className="h-5 w-5 text-blue-600" />
              <div>
                <Label className="text-sm font-semibold text-gray-500">Salary</Label>
                <p className="font-medium text-gray-800">{format_salary(job.salary_min, job.salary_max)}</p>
                  </div>
                </div>
            <div className="flex items-center gap-3">
              <Clock className="h-5 w-5 text-blue-600" />
              <div>
                <Label className="text-sm font-semibold text-gray-500">Job Type</Label>
                <p className="font-medium text-gray-800">{job.job_type.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 text-blue-600" />
              <div>
                <Label className="text-sm font-semibold text-gray-500">Experience</Label>
                <p className="font-medium text-gray-800">{format_experience_level(job.experience_level)}</p>
              </div>
            </div>
            <div className="md:col-span-2 pt-2">
              <Label className="text-sm font-semibold text-gray-500 block mb-1">Description</Label>
              <p className="text-gray-700 leading-relaxed text-sm">
                {job.description}
              </p>
            </div>
          </CardContent>
        </Card>

        <form onSubmit={(e) => { e.preventDefault(); submit_application(); }} className="space-y-10">
          <Card className="card shadow-2xl border-0 overflow-hidden">
            <CardHeader className="bg-gradient-to-r from-blue-500 to-purple-500 p-6">
              <CardTitle className="text-2xl font-bold text-white flex items-center gap-3">
                <User className="h-7 w-7" />
                Your Information
              </CardTitle>
              <CardDescription className="text-blue-100 text-base mt-1">
                Tell us about yourself.
            </CardDescription>
          </CardHeader>
            <CardContent className="p-8 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="full_name" className="text-base font-semibold text-gray-700">Full Name *</Label>
                  <Input
                    id="full_name"
                    value={candidate_data.full_name}
                    onChange={(e) => handle_candidate_change('full_name', e.target.value)} 
                    placeholder="Your full name"
                    required
                    className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
                <div className="space-y-2">
                  {render_email_verification()}
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone" className="text-base font-semibold text-gray-700">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={candidate_data.phone}
                  onChange={(e) => handle_candidate_change('phone', e.target.value)} 
                  placeholder="+1 234 567 8900 (Optional)" 
                  className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="resume" className="text-base font-semibold text-gray-700">
                  Upload Resume {(show_existing_data && existing_candidate?.has_resume) ? "(Optional - Update Resume)" : "*"}
                </Label>
                {show_existing_data && existing_candidate?.has_resume && (
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-green-600">
                      ✓ You already have a resume on file. You can optionally upload a new one for this application.
                    </p>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => window.open(`http://84.16.230.94:8017/api/v1/candidates/${existing_candidate.id}/resume`, '_blank')}
                      className="text-blue-600 hover:text-blue-700 text-sm"
                    >
                      View Current Resume
                    </Button>
                  </div>
                )}
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md bg-white hover:border-purple-400 transition-colors duration-200">
                  <div className="space-y-1 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="resume-upload"
                        className="relative cursor-pointer rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                      >
                        <span>Upload a file</span>
                        <input 
                          id="resume-upload" 
                          name="resume-upload" 
                          type="file" 
                          className="sr-only" 
                          onChange={handle_resume_change} 
                          accept=".pdf" 
                          required={!(show_existing_data && existing_candidate?.has_resume)}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    {resume_file ? (
                       <p className="text-sm text-green-600 font-semibold">{resume_file.name} selected</p>
                    ) : (
                       <p className="text-xs text-gray-500">PDF</p>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {form_keys && form_keys.length > 0 && (
            <Card className="card shadow-2xl border-0 overflow-hidden">
              <CardHeader className="bg-gradient-to-r from-blue-500 to-purple-500 p-6">
                <CardTitle className="text-2xl font-bold text-white flex items-center gap-3">
                  <FileTextIcon className="h-7 w-7" />
                  Additional Information
                </CardTitle>
                <CardDescription className="text-blue-100 text-base mt-1">
                  Please provide responses to the following questions.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-8 space-y-8">
                {form_keys.map((form_key) => render_form_field(form_key))}
              </CardContent>
            </Card>
            )}

          <div className="pt-5">
              <Button
              type="submit" 
              disabled={is_submitting || is_loading}
              className="w-full button text-lg py-3 shadow-xl hover:shadow-2xl transition-all duration-300 flex items-center justify-center gap-2"
              >
                {is_submitting ? (
                <><Loader2 className="h-5 w-5 animate-spin" /> Submitting Application...</>
                ) : (
                <><Send className="h-5 w-5" /> Submit Application</>
                )}
              </Button>
            </div>
        </form>
      </div>
    </div>
  );
};

export default JobApplicationForm; 