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
  const [form_responses, setFormResponses] = useState<Record<string, string>>( {} );
  const [is_submitting, setIsSubmitting] = useState(false);

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
  const handleFormResponseChange = (key_id: string, value: string) => {
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

  // Submit application
  const handleSubmit = async () => {
    if (!selected_candidate_id && !show_new_candidate_form) {
      toast({ title: "Error", description: "Please select or create a candidate.", variant: "destructive" });
      return;
    }
    if (!selected_job_id) {
      toast({ title: "Error", description: "Please select a job.", variant: "destructive" });
      return;
    }
    // Validate required form keys
    const missing_required = form_keys.find(
      (key) => key.required && !form_responses[key.id]
    );
    if (missing_required) {
      toast({ title: "Error", description: `Please fill in the required field: ${missing_required.name}`, variant: "destructive" });
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

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Add New Application</h1>
          <p className="text-muted-foreground">Manually create an application for a candidate</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/applications")}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={is_submitting}>{is_submitting ? "Submitting..." : "Create Application"}</Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Candidate</CardTitle>
              <CardDescription>Select or create a candidate</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="candidateId">Candidate *</Label>
                <Select value={selected_candidate_id} onValueChange={handleCandidateChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a candidate or add new" />
                  </SelectTrigger>
                  <SelectContent>
                    {candidates.map((c) => (
                      <SelectItem key={c.id} value={c.id.toString()}>{c.full_name} ({c.email})</SelectItem>
                    ))}
                    <SelectItem value="new">+ Add New Candidate</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {show_new_candidate_form && (
                <div className="space-y-4 border rounded-lg p-4 bg-muted">
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name *</Label>
                    <Input id="full_name" value={new_candidate_data.full_name} onChange={e => setNewCandidateData({ ...new_candidate_data, full_name: e.target.value })} placeholder="Enter full name" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email *</Label>
                    <Input id="email" type="email" value={new_candidate_data.email} onChange={e => setNewCandidateData({ ...new_candidate_data, email: e.target.value })} placeholder="candidate@email.com" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input id="phone" type="tel" value={new_candidate_data.phone} onChange={e => setNewCandidateData({ ...new_candidate_data, phone: e.target.value })} placeholder="+1 234 567 8900" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="resume">Resume (Optional)</Label>
                    <div className="flex items-center gap-4">
                      <input id="resume" type="file" accept=".pdf,.doc,.docx" onChange={handleFileUpload} className="hidden" />
                      <Button variant="outline" onClick={() => document.getElementById("resume")?.click()} className="w-full">
                        <Upload className="mr-2 h-4 w-4" />
                        {new_candidate_data.resume_file ? new_candidate_data.resume_file.name : "Upload Resume"}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">Accepted formats: PDF, DOC, DOCX (Max 10MB)</p>
                  </div>
                  <div className="flex gap-2">
                    <Button type="button" onClick={handleCreateCandidate}>Create Candidate</Button>
                    <Button type="button" variant="outline" onClick={() => setShowNewCandidateForm(false)}>Cancel</Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Job Selection</CardTitle>
              <CardDescription>Select the position this candidate is applying for</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="jobId">Job Position *</Label>
                <Select value={selected_job_id} onValueChange={setSelectedJobId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a job position" />
                  </SelectTrigger>
                  <SelectContent>
                    {jobs.map((job) => (
                      <SelectItem key={job.id} value={job.id.toString()}>{job.title}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {selected_job && (
                <div className="mt-4 p-3 bg-muted rounded-lg">
                  <p className="text-sm"><strong>Selected:</strong> {selected_job.title}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Form Responses</CardTitle>
              <CardDescription>Fill in the custom form fields for this application</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {form_keys.length === 0 && <div className="text-muted-foreground">Select a job to see form fields.</div>}
              {form_keys.map((form_key) => (
                <div key={form_key.id} className="space-y-2">
                  <Label htmlFor={`formKey-${form_key.id}`}>{form_key.name}{form_key.required && <span className="text-destructive ml-1">*</span>}</Label>
                  {form_key.field_type === "textarea" ? (
                    <Textarea id={`formKey-${form_key.id}`} value={form_responses[form_key.id] || ""} onChange={e => handleFormResponseChange(form_key.id, e.target.value)} placeholder={`Enter ${form_key.name.toLowerCase()}`} rows={3} />
                  ) : form_key.field_type === "date" ? (
                    <Input id={`formKey-${form_key.id}`} type="date" value={form_responses[form_key.id] || ""} onChange={e => handleFormResponseChange(form_key.id, e.target.value)} />
                  ) : (
                    <Input id={`formKey-${form_key.id}`} type={form_key.field_type || "text"} value={form_responses[form_key.id] || ""} onChange={e => handleFormResponseChange(form_key.id, e.target.value)} placeholder={`Enter ${form_key.name.toLowerCase()}`} />
                  )}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Application Preview</CardTitle>
              <CardDescription>Review the application details before creating</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div><strong>Candidate:</strong> {selected_candidate_id ? (candidates.find(c => c.id.toString() === selected_candidate_id)?.full_name) : show_new_candidate_form ? new_candidate_data.full_name : "Not specified"}</div>
              <div><strong>Email:</strong> {selected_candidate_id ? (candidates.find(c => c.id.toString() === selected_candidate_id)?.email) : show_new_candidate_form ? new_candidate_data.email : "Not specified"}</div>
              <div><strong>Job:</strong> {selected_job?.title || "Not selected"}</div>
              <div><strong>Resume:</strong> {show_new_candidate_form ? (new_candidate_data.resume_file?.name || "Not uploaded") : selected_candidate_id ? (candidates.find(c => c.id.toString() === selected_candidate_id)?.resume_file_name || "Not uploaded") : "Not uploaded"}</div>
              <div><strong>Form Responses:</strong> {Object.keys(form_responses).length} fields completed</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AddApplication;
