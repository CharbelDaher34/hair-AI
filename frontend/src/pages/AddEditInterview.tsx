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
  interviewer_id: string;
}

interface HR {
  id: number;
  full_name: string;
  email: string;
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
    interviewer_id: "",
  });

  const [applications, setApplications] = useState<Application[]>([]);
  const [hrUsers, setHrUsers] = useState<HR[]>([]);
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

  const fetchHrUsers = async () => {
    try {
      const data = await apiService.getCompanyEmployees();
      console.log("HR users API response:", data);
      
      setHrUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Error fetching HR users:", err);
      setHrUsers([]);
      toast({
        title: "Error",
        description: "Failed to fetch HR users",
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
        interviewer_id: data.interviewer_id?.toString() || "",
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
        await Promise.all([fetchApplications(), fetchHrUsers()]);
        
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

  // Set first HR user as default when hrUsers is loaded and we're not editing
  useEffect(() => {
    if (!isEditing && hrUsers.length > 0 && !interviewData.interviewer_id) {
      setInterviewData(prev => ({
        ...prev,
        interviewer_id: hrUsers[0].id.toString()
      }));
    }
  }, [hrUsers, isEditing, interviewData.interviewer_id]);

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
        interviewer_id: interviewData.interviewer_id ? parseInt(interviewData.interviewer_id) : null,
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
      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
          <span className="text-lg font-medium text-gray-700">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
        <Card className="w-full max-w-md shadow-xl border-0">
          <CardContent className="text-center p-8 space-y-4">
            <p className="text-red-600 font-semibold text-lg mb-4">{error}</p>
            <Button onClick={() => navigate("/interviews")} className="button shadow-lg hover:shadow-xl transition-all duration-300">
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const selectedApplication = getSelectedApplication();

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            {isEditing ? "Edit Interview" : "Schedule Interview"}
          </h1>
          <p className="text-lg text-gray-600">
            {isEditing ? "Update interview details" : "Schedule a new interview with a candidate"}
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate("/interviews")} className="shadow-md hover:shadow-lg transition-all duration-300">
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting} className="button shadow-lg hover:shadow-xl transition-all duration-300">
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEditing ? "Update Interview" : "Schedule Interview"}
          </Button>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <User className="h-5 w-5 text-blue-600" />
                Application Details
              </CardTitle>
              <CardDescription className="text-base text-gray-600">Select the candidate and position</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="application" className="text-sm font-semibold text-gray-700">Application *</Label>
                <Select
                  value={interviewData.application_id}
                  onValueChange={(value) => setInterviewData({...interviewData, application_id: value})}
                >
                  <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
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
                <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg space-y-2 border border-blue-100 shadow-sm">
                  <div>
                    <strong className="text-gray-700">Candidate:</strong> <span className="text-gray-800 font-medium">{selectedApplication.candidate.full_name}</span>
                  </div>
                  <div>
                    <strong className="text-gray-700">Position:</strong> <span className="text-gray-800 font-medium">{selectedApplication.job.title}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <Calendar className="h-5 w-5 text-blue-600" />
                Interview Schedule
              </CardTitle>
              <CardDescription className="text-base text-gray-600">Set the date and time</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="date" className="text-sm font-semibold text-gray-700">Date & Time *</Label>
                <Input
                  id="date"
                  type="datetime-local"
                  value={interviewData.date}
                  onChange={(e) => setInterviewData({...interviewData, date: e.target.value})}
                  className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Interview Details</CardTitle>
              <CardDescription className="text-base text-gray-600">Specify interview type and status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="type" className="text-sm font-semibold text-gray-700">Interview Type *</Label>
                <Select
                  value={interviewData.type}
                  onValueChange={(value) => setInterviewData({...interviewData, type: value})}
                >
                  <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
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
                <Label htmlFor="status" className="text-sm font-semibold text-gray-700">Interview Status</Label>
                <Select
                  value={interviewData.status}
                  onValueChange={(value) => setInterviewData({...interviewData, status: value})}
                >
                  <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
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

              <div className="space-y-2">
                <Label htmlFor="interviewer" className="text-sm font-semibold text-gray-700">Interviewer</Label>
                <Select
                  value={interviewData.interviewer_id}
                  onValueChange={(value) => setInterviewData({...interviewData, interviewer_id: value})}
                >
                  <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                    <SelectValue placeholder="Select an interviewer" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="None">No interviewer assigned</SelectItem>
                    {hrUsers.map((hr) => (
                      <SelectItem key={hr.id} value={hr.id.toString()}>
                        {hr.full_name} ({hr.email})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Notes</CardTitle>
              <CardDescription className="text-base text-gray-600">Additional information and preparation notes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="notes" className="text-sm font-semibold text-gray-700">Interview Notes</Label>
                <Textarea
                  id="notes"
                  value={interviewData.notes}
                  onChange={(e) => setInterviewData({...interviewData, notes: e.target.value})}
                  placeholder="Add any notes about the interview, preparation items, or outcomes..."
                  rows={6}
                  className="shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500 resize-none"
                />
              </div>
            </CardContent>
          </Card>

          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Interview Summary</CardTitle>
              <CardDescription className="text-base text-gray-600">Review the interview details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-100 shadow-sm">
              <div>
                <strong className="text-gray-700">Candidate:</strong> <span className="text-gray-800 font-medium">{selectedApplication?.candidate.full_name || "Not selected"}</span>
              </div>
              <div>
                <strong className="text-gray-700">Position:</strong> <span className="text-gray-800 font-medium">{selectedApplication?.job.title || "Not selected"}</span>
              </div>
              <div>
                <strong className="text-gray-700">Date & Time:</strong> <span className="text-gray-800 font-medium">{
                  interviewData.date
                    ? new Date(interviewData.date).toLocaleString()
                    : "Not scheduled"
                }</span>
              </div>
              <div>
                <strong className="text-gray-700">Type:</strong> <span className="text-gray-800 font-medium">{interviewTypes.find(t => t.value === interviewData.type)?.label || "Not specified"}</span>
              </div>
              <div>
                <strong className="text-gray-700">Status:</strong> <span className="text-gray-800 font-medium">{interviewStatuses.find(s => s.value === interviewData.status)?.label || "Not specified"}</span>
              </div>
              <div>
                <strong className="text-gray-700">Interviewer:</strong> <span className="text-gray-800 font-medium">{
                  interviewData.interviewer_id 
                    ? hrUsers.find(hr => hr.id.toString() === interviewData.interviewer_id)?.full_name || "Unknown"
                    : "Not assigned"
                }</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AddEditInterview;
