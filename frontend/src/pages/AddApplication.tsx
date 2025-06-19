import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Upload } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import apiService from "@/services/api";
import { Loader2 } from "lucide-react";

const AddApplication = () => {
  const navigate = useNavigate();

  // State for candidates, jobs, form keys, and UI
  const [candidates, setCandidates] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [form_keys, setFormKeys] = useState<any[]>([]);
  const [selected_candidate_id, setSelectedCandidateId] = useState<string>("");
  const [show_new_candidate_form, setShowNewCandidateForm] = useState(false);
  const [new_candidate_data, setNewCandidateData] = useState({
    full_name: "",
    email: "",
    phone: "",
    resume_file: null as File | null,
  });
  const [selected_job_id, setSelectedJobId] = useState<string>("");
  const [selected_job, setSelectedJob] = useState<any>(null);
  const [form_responses, setFormResponses] = useState<Record<string, any>>( {} );
  const [is_submitting, setIsSubmitting] = useState(false);

  // --- Derived state for button enable/disable ---
  const is_candidate_selected = !show_new_candidate_form && !!selected_candidate_id;
  const is_job_selected = !!selected_job_id;
  const is_form_valid = form_keys.every(
    (key) => !key.required || !!form_responses[key.id]
  );
  const can_create_application = is_candidate_selected && is_job_selected && is_form_valid;

  // Fetch candidates and jobs on mount
  useEffect(() => {
    apiService.getCandidatesForCurrentCompany()
      .then(setCandidates)
      .catch(() => toast({ title: "Error", description: "Failed to load candidates.", variant: "destructive" }));
    apiService.getAllJobs()
      .then(res => setJobs(res))
      .catch(() => toast({ title: "Error", description: "Failed to load jobs.", variant: "destructive" }));
  }, []);

  // Fetch job form keys when job changes
  useEffect(() => {
    if (selected_job_id) {
      apiService.getJobFormData(selected_job_id)
        .then((data) => {
          setFormKeys(data.form_keys || []);
          setSelectedJob(data.job || null);
          setFormResponses({});
        })
        .catch(() => toast({ title: "Error", description: "Failed to load job form fields.", variant: "destructive" }));
    } else {
      setFormKeys([]);
      setSelectedJob(null);
      setFormResponses({});
    }
  }, [selected_job_id]);

  // Candidate dropdown change
  const handleCandidateChange = (value: string) => {
    if (value === "new") {
      setShowNewCandidateForm(true);
      setSelectedCandidateId("");
    } else {
      setShowNewCandidateForm(false);
      setSelectedCandidateId(value);
    }
  };

  // New candidate file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setNewCandidateData({ ...new_candidate_data, resume_file: file });
      toast({ title: "File uploaded", description: `${file.name} has been selected for upload.` });
    }
  };

  // Form response change
  const handleFormResponseChange = (key_id: string, value: any) => {
    setFormResponses({ ...form_responses, [key_id]: value });
  };

  // Create new candidate
  const handleCreateCandidate = async () => {
    if (!new_candidate_data.full_name || !new_candidate_data.email) {
      toast({ title: "Error", description: "Please fill in all required candidate fields.", variant: "destructive" });
      return;
    }
    try {
      const candidate_payload = {
        full_name: new_candidate_data.full_name,
        email: new_candidate_data.email,
        phone: new_candidate_data.phone,
      };
      const created = await apiService.createCandidate(candidate_payload, new_candidate_data.resume_file);
      setCandidates((prev) => [...prev, created]);
      setSelectedCandidateId(created.id.toString());
      setShowNewCandidateForm(false);
      toast({ title: "Success", description: "Candidate created." });
    } catch {
      toast({ title: "Error", description: "Failed to create candidate.", variant: "destructive" });
    }
  };

  // --- Updated Submit Handler ---
  const handle_submit_application = async () => {
    if (!is_candidate_selected) {
      toast({ title: "Error", description: "Please select a candidate.", variant: "destructive" });
      return;
    }
    if (!is_job_selected) {
      toast({ title: "Error", description: "Please select a job.", variant: "destructive" });
      return;
    }
    if (!is_form_valid) {
      const missing_key = form_keys.find((key) => key.required && !form_responses[key.id]);
      toast({ title: "Error", description: `Please fill in the required field: ${missing_key?.name || ''}`, variant: "destructive" });
      return;
    }
    setIsSubmitting(true);
    try {
      const application_payload: any = {
        candidate_id: selected_candidate_id,
        job_id: selected_job_id,
        form_responses: form_responses,
      };
      await apiService.createApplication(application_payload);
      toast({ title: "Success", description: "Application has been created successfully." });
      navigate("/applications");
    } catch (err) {
      console.error('Failed to create application:', err);
      toast({ title: "Error", description: "Failed to create application.", variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Add this function before the return statement
  const render_form_field = (form_key: any) => {
    const common_props = {
      id: `form_key_${form_key.id}`,
      value: form_responses[form_key.id] || '',
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | string) => {
        const value = typeof e === 'string' ? e : e.target.value;
        handleFormResponseChange(form_key.id.toString(), value);
      },
      className: "h-12 bg-white shadow-sm",
      required: form_key.required,
    };
    const select_common_props = {
      id: `form_key_${form_key.id}`,
      value: form_responses[form_key.id] || '',
      onValueChange: (value: string) => handleFormResponseChange(form_key.id.toString(), value),
      required: form_key.required,
    };
    return (
      <div key={form_key.id} className="space-y-2">
        <Label htmlFor={common_props.id} className="text-sm font-semibold text-gray-700">
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
              return <Textarea {...common_props} placeholder={`Tell us about your ${form_key.name.toLowerCase()}...`} rows={4} className="bg-white shadow-sm resize-none" />;
            case "select":
              return (
                <Select {...select_common_props}>
                  <SelectTrigger className="h-12 bg-white shadow-sm">
                    <SelectValue placeholder={`Select ${form_key.name}`} />
                  </SelectTrigger>
                  <SelectContent>
                    {form_key.enum_values?.map((option: string) => (
                      <SelectItem key={option} value={option}>{option}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              );
            case "checkbox":
              return (
                <div className="flex items-center space-x-2 pt-2">
                  <input
                    type="checkbox"
                    id={common_props.id}
                    checked={Boolean(form_responses[form_key.id])}
                    onChange={e => handleFormResponseChange(form_key.id.toString(), e.target.checked)}
                    className="h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
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

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Add New Application
          </h1>
          <p className="text-lg text-gray-600">Manually create an application for a candidate</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate("/applications")} className="shadow-md hover:shadow-lg transition-all duration-300">
            Cancel
          </Button>
          <Button onClick={handle_submit_application} disabled={!can_create_application || is_submitting} className="button shadow-lg hover:shadow-xl transition-all duration-300">
            {is_submitting ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Submitting...</>
            ) : (
              "Create Application"
            )}
          </Button>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Candidate Information</CardTitle>
              <CardDescription className="text-base text-gray-600">Select an existing candidate or add a new one</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 pt-4">
              <div className="space-y-2">
                <Label htmlFor="candidateId" className="text-sm font-semibold text-gray-700">Candidate *</Label>
                <div className="flex gap-4">
                  <Select value={show_new_candidate_form ? "new" : selected_candidate_id} onValueChange={handleCandidateChange}>
                    <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                      <SelectValue placeholder="Select a candidate or add new" />
                    </SelectTrigger>
                    <SelectContent>
                      {candidates.map((c) => (
                        <SelectItem key={c.id} value={c.id.toString()}>{c.full_name} ({c.email})</SelectItem>
                      ))}
                      <SelectItem value="new" className="text-blue-600 font-semibold bg-blue-50 hover:bg-blue-100 transition-colors duration-200">
                        + Add New Candidate
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <Button 
                    variant="outline" 
                    onClick={() => handleCandidateChange("new")} 
                    className="button-outline shadow-md hover:shadow-lg transition-all duration-300 w-full md:w-auto"
                  >
                    + Add New Candidate
                  </Button>
                </div>
              </div>
              {show_new_candidate_form && (
                <div className="space-y-4 border border-blue-200 rounded-lg p-6 bg-gradient-to-r from-blue-50 to-purple-50 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">New Candidate Details</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                      <Label htmlFor="full_name" className="text-sm font-semibold text-gray-700">Full Name *</Label>
                      <Input id="full_name" value={new_candidate_data.full_name} onChange={e => setNewCandidateData({ ...new_candidate_data, full_name: e.target.value })} placeholder="Enter full name" className="h-12 bg-white shadow-sm" />
                  </div>
                  <div className="space-y-2">
                      <Label htmlFor="email" className="text-sm font-semibold text-gray-700">Email *</Label>
                      <Input id="email" type="email" value={new_candidate_data.email} onChange={e => setNewCandidateData({ ...new_candidate_data, email: e.target.value })} placeholder="candidate@example.com" className="h-12 bg-white shadow-sm" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone" className="text-sm font-semibold text-gray-700">Phone</Label>
                    <Input id="phone" type="tel" value={new_candidate_data.phone} onChange={e => setNewCandidateData({ ...new_candidate_data, phone: e.target.value })} placeholder="+1 234 567 8900" className="h-12 bg-white shadow-sm" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="resume" className="text-sm font-semibold text-gray-700">Resume (Optional)</Label>
                    <div className="flex items-center gap-4">
                      <input id="resume" type="file" accept=".pdf,.doc,.docx" onChange={handleFileUpload} className="hidden" />
                      <Button variant="outline" onClick={() => document.getElementById("resume")?.click()} className="w-full h-12 bg-white shadow-sm hover:bg-slate-50">
                        <Upload className="mr-2 h-4 w-4 text-blue-600" />
                        {new_candidate_data.resume_file ? new_candidate_data.resume_file.name : "Upload Resume"}
                      </Button>
                    </div>
                  </div>
                  <Button onClick={handleCreateCandidate} className="button-outline w-full shadow-md hover:shadow-lg transition-all duration-300">
                    Save New Candidate
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className={`card shadow-lg hover:shadow-xl transition-all duration-300 border-0 ${!is_candidate_selected ? 'opacity-50 pointer-events-none' : ''}`}>
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Job Selection</CardTitle>
              <CardDescription className="text-base text-gray-600">Choose the job for this application</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="jobId" className="text-sm font-semibold text-gray-700">Job *</Label>
                <Select value={selected_job_id} onValueChange={setSelectedJobId}>
                  <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                    <SelectValue placeholder="Select a job" />
                  </SelectTrigger>
                  <SelectContent>
                    {jobs.map((job) => (
                      <SelectItem key={job.id} value={job.id.toString()}>{job.title}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {selected_job && (
                <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg space-y-1 border border-blue-100 shadow-sm">
                  <h4 className="font-semibold text-gray-800">{selected_job.title}</h4>
                  <p className="text-sm text-gray-600">Location: {selected_job.location}</p>
                  <p className="text-sm text-gray-600">Type: {selected_job.job_type.replace("_", " ").toUpperCase()}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Application Form</CardTitle>
              <CardDescription className="text-base text-gray-600">Complete any additional fields for this job</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 pt-4">
              {form_keys.length === 0 && selected_job_id && (
                <p className="text-gray-600 italic">No custom form fields for this job.</p>
              )}
              {!selected_job_id && (
                <p className="text-gray-600 italic">Select a job to see its application form fields.</p>
              )}
              {form_keys.map(render_form_field)}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AddApplication;
