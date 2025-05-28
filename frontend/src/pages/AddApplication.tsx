
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Upload } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "@/hooks/use-toast";

const AddApplication = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    candidateName: "",
    candidateEmail: "",
    candidatePhone: "",
    jobId: "",
    resumeFile: null as File | null,
    formResponses: {} as Record<string, string>,
  });

  // Mock data
  const jobs = [
    { id: 1, title: "Senior Frontend Developer" },
    { id: 2, title: "Product Manager" },
    { id: 3, title: "UX Designer" },
    { id: 4, title: "Backend Engineer" },
  ];

  const formKeys = [
    { id: 1, name: "Experience Years", fieldType: "number", required: true },
    { id: 2, name: "Portfolio URL", fieldType: "text", required: false },
    { id: 3, name: "Availability", fieldType: "date", required: true },
    { id: 4, name: "Expected Salary", fieldType: "text", required: false },
  ];

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setFormData({ ...formData, resumeFile: file });
      toast({
        title: "File uploaded",
        description: `${file.name} has been selected for upload.`,
      });
    }
  };

  const handleFormResponseChange = (keyId: number, value: string) => {
    setFormData({
      ...formData,
      formResponses: {
        ...formData.formResponses,
        [keyId]: value,
      },
    });
  };

  const handleSubmit = () => {
    if (!formData.candidateName || !formData.candidateEmail || !formData.jobId) {
      toast({
        title: "Error",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    // Validate required form keys
    const requiredKeys = formKeys.filter(key => key.required);
    const missingRequired = requiredKeys.find(key => !formData.formResponses[key.id]);
    
    if (missingRequired) {
      toast({
        title: "Error",
        description: `Please fill in the required field: ${missingRequired.name}`,
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "Success",
      description: "Application has been created successfully.",
    });
    navigate("/applications");
  };

  const selectedJob = jobs.find(job => job.id.toString() === formData.jobId);

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Add New Application</h1>
          <p className="text-muted-foreground">
            Manually create an application for a candidate
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/applications")}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Create Application</Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Candidate Information</CardTitle>
              <CardDescription>Basic details about the candidate</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="candidateName">Full Name *</Label>
                <Input
                  id="candidateName"
                  value={formData.candidateName}
                  onChange={(e) => setFormData({...formData, candidateName: e.target.value})}
                  placeholder="Enter candidate's full name"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="candidateEmail">Email *</Label>
                <Input
                  id="candidateEmail"
                  type="email"
                  value={formData.candidateEmail}
                  onChange={(e) => setFormData({...formData, candidateEmail: e.target.value})}
                  placeholder="candidate@email.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="candidatePhone">Phone</Label>
                <Input
                  id="candidatePhone"
                  type="tel"
                  value={formData.candidatePhone}
                  onChange={(e) => setFormData({...formData, candidatePhone: e.target.value})}
                  placeholder="+1 234 567 8900"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="resume">Resume (Optional)</Label>
                <div className="flex items-center gap-4">
                  <input
                    id="resume"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <Button
                    variant="outline"
                    onClick={() => document.getElementById("resume")?.click()}
                    className="w-full"
                  >
                    <Upload className="mr-2 h-4 w-4" />
                    {formData.resumeFile ? formData.resumeFile.name : "Upload Resume"}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Accepted formats: PDF, DOC, DOCX (Max 10MB)
                </p>
              </div>
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
                <Select
                  value={formData.jobId}
                  onValueChange={(value) => setFormData({...formData, jobId: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a job position" />
                  </SelectTrigger>
                  <SelectContent>
                    {jobs.map((job) => (
                      <SelectItem key={job.id} value={job.id.toString()}>
                        {job.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {selectedJob && (
                <div className="mt-4 p-3 bg-muted rounded-lg">
                  <p className="text-sm">
                    <strong>Selected:</strong> {selectedJob.title}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Form Responses</CardTitle>
              <CardDescription>
                Fill in the custom form fields for this application
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {formKeys.map((formKey) => (
                <div key={formKey.id} className="space-y-2">
                  <Label htmlFor={`formKey-${formKey.id}`}>
                    {formKey.name}
                    {formKey.required && <span className="text-destructive ml-1">*</span>}
                  </Label>
                  
                  {formKey.fieldType === "textarea" ? (
                    <Textarea
                      id={`formKey-${formKey.id}`}
                      value={formData.formResponses[formKey.id] || ""}
                      onChange={(e) => handleFormResponseChange(formKey.id, e.target.value)}
                      placeholder={`Enter ${formKey.name.toLowerCase()}`}
                      rows={3}
                    />
                  ) : formKey.fieldType === "date" ? (
                    <Input
                      id={`formKey-${formKey.id}`}
                      type="date"
                      value={formData.formResponses[formKey.id] || ""}
                      onChange={(e) => handleFormResponseChange(formKey.id, e.target.value)}
                    />
                  ) : (
                    <Input
                      id={`formKey-${formKey.id}`}
                      type={formKey.fieldType}
                      value={formData.formResponses[formKey.id] || ""}
                      onChange={(e) => handleFormResponseChange(formKey.id, e.target.value)}
                      placeholder={`Enter ${formKey.name.toLowerCase()}`}
                    />
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
              <div>
                <strong>Candidate:</strong> {formData.candidateName || "Not specified"}
              </div>
              <div>
                <strong>Email:</strong> {formData.candidateEmail || "Not specified"}
              </div>
              <div>
                <strong>Job:</strong> {selectedJob?.title || "Not selected"}
              </div>
              <div>
                <strong>Resume:</strong> {formData.resumeFile?.name || "Not uploaded"}
              </div>
              <div>
                <strong>Form Responses:</strong> {Object.keys(formData.formResponses).length} fields completed
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AddApplication;
