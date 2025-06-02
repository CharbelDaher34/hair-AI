import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Calendar, Clock, User, Loader2 } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import apiService from "@/services/api";

interface Application {
  id: number;
  candidate: {
    id: number;
    full_name: string;
  };
  job: {
    id: number;
    title: string;
  };
}

interface InterviewFormData {
  application_id: string;
  date: string;
  type: string;
  status: string;
  notes: string;
}

const AddEditInterview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [interviewData, setInterviewData] = useState<InterviewFormData>({
    application_id: "",
    date: "",
    type: "phone",
    status: "scheduled",
    notes: "",
  });

  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const interviewTypes = [
    { value: "phone", label: "Phone" },
    { value: "online", label: "Online" },
    { value: "in_person", label: "In Person" },
  ];

  const interviewStatuses = [
    { value: "scheduled", label: "Scheduled" },
    { value: "done", label: "Done" },
    { value: "canceled", label: "Canceled" },
  ];

  const fetchApplications = async () => {
    try {
      const data = await apiService.getEmployerApplications();
      console.log("Applications API response:", data);
      
      const applicationsArray = data?.applications || [];
      setApplications(Array.isArray(applicationsArray) ? applicationsArray : []);
    } catch (err) {
      console.error("Error fetching applications:", err);
      setApplications([]);
      toast({
        title: "Error",
        description: "Failed to fetch applications",
        variant: "destructive",
      });
    }
  };

  const fetchInterview = async (interviewId: string) => {
    try {
      const data = await apiService.getInterview(parseInt(interviewId));
      
      // Convert the date to the format expected by the datetime-local input
      const date = new Date(data.date);
      const formattedDate = date.toISOString().slice(0, 16); // YYYY-MM-DDTHH:mm
      
      setInterviewData({
        application_id: data.application_id.toString(),
        date: formattedDate,
        type: data.type,
        status: data.status,
        notes: data.notes || "",
      });
    } catch (err) {
      console.error("Error fetching interview:", err);
      setError("Failed to fetch interview details");
      toast({
        title: "Error",
        description: "Failed to fetch interview details",
        variant: "destructive",
      });
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        await fetchApplications();
        
        if (isEditing && id) {
          await fetchInterview(id);
        } else {
          // Check if application_id is passed as URL parameter
          const urlParams = new URLSearchParams(window.location.search);
          const applicationId = urlParams.get('application_id');
          if (applicationId) {
            setInterviewData(prev => ({
              ...prev,
              application_id: applicationId
            }));
          }
        }
      } catch (err) {
        setError("Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id, isEditing]);

  const getSelectedApplication = () => {
    if (!Array.isArray(applications)) {
      return undefined;
    }
    return applications.find(app => app.id.toString() === interviewData.application_id);
  };

  const handleSubmit = async () => {
    if (!interviewData.application_id || !interviewData.date) {
      toast({
        title: "Error",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    
    try {
      const submitData = {
        application_id: parseInt(interviewData.application_id),
        date: new Date(interviewData.date).toISOString(),
        type: interviewData.type,
        status: interviewData.status,
        notes: interviewData.notes || null,
      };

      if (isEditing && id) {
        await apiService.updateInterview(parseInt(id), submitData);
        toast({
          title: "Success",
          description: "Interview updated successfully.",
        });
      } else {
        await apiService.createInterview(submitData);
        toast({
          title: "Success",
          description: "Interview scheduled successfully.",
        });
      }
      
      navigate("/interviews");
    } catch (err) {
      console.error("Error saving interview:", err);
      toast({
        title: "Error",
        description: `Failed to ${isEditing ? "update" : "create"} interview.`,
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={() => navigate("/interviews")}>Go Back</Button>
        </div>
      </div>
    );
  }

  const selectedApplication = getSelectedApplication();

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {isEditing ? "Edit Interview" : "Schedule Interview"}
          </h1>
          <p className="text-muted-foreground">
            {isEditing ? "Update interview details" : "Schedule a new interview with a candidate"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/interviews")}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEditing ? "Update Interview" : "Schedule Interview"}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Application Details
              </CardTitle>
              <CardDescription>Select the candidate and position</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="application">Application *</Label>
                <Select
                  value={interviewData.application_id}
                  onValueChange={(value) => setInterviewData({...interviewData, application_id: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an application" />
                  </SelectTrigger>
                  <SelectContent>
                    {Array.isArray(applications) && applications.map((app) => (
                      <SelectItem key={app.id} value={app.id.toString()}>
                        {app.candidate.full_name} - {app.job.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedApplication && (
                <div className="p-3 bg-muted rounded-lg space-y-2">
                  <div>
                    <strong>Candidate:</strong> {selectedApplication.candidate.full_name}
                  </div>
                  <div>
                    <strong>Position:</strong> {selectedApplication.job.title}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Interview Schedule
              </CardTitle>
              <CardDescription>Set the date and time</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="date">Date & Time *</Label>
                <Input
                  id="date"
                  type="datetime-local"
                  value={interviewData.date}
                  onChange={(e) => setInterviewData({...interviewData, date: e.target.value})}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Interview Details</CardTitle>
              <CardDescription>Specify interview type and status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="type">Interview Type *</Label>
                <Select
                  value={interviewData.type}
                  onValueChange={(value) => setInterviewData({...interviewData, type: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select interview type" />
                  </SelectTrigger>
                  <SelectContent>
                    {interviewTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="status">Interview Status</Label>
                <Select
                  value={interviewData.status}
                  onValueChange={(value) => setInterviewData({...interviewData, status: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {interviewStatuses.map((status) => (
                      <SelectItem key={status.value} value={status.value}>
                        {status.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Notes</CardTitle>
              <CardDescription>Additional information and preparation notes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="notes">Interview Notes</Label>
                <Textarea
                  id="notes"
                  value={interviewData.notes}
                  onChange={(e) => setInterviewData({...interviewData, notes: e.target.value})}
                  placeholder="Add any notes about the interview, preparation items, or outcomes..."
                  rows={6}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Interview Summary</CardTitle>
              <CardDescription>Review the interview details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <strong>Candidate:</strong> {selectedApplication?.candidate.full_name || "Not selected"}
              </div>
              <div>
                <strong>Position:</strong> {selectedApplication?.job.title || "Not selected"}
              </div>
              <div>
                <strong>Date & Time:</strong> {
                  interviewData.date
                    ? new Date(interviewData.date).toLocaleString()
                    : "Not scheduled"
                }
              </div>
              <div>
                <strong>Type:</strong> {interviewTypes.find(t => t.value === interviewData.type)?.label || "Not specified"}
              </div>
              <div>
                <strong>Status:</strong> {interviewStatuses.find(s => s.value === interviewData.status)?.label || "Not specified"}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AddEditInterview;
