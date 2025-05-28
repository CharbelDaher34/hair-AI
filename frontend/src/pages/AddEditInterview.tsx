
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Calendar, Clock, User } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "@/hooks/use-toast";

const AddEditInterview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [interviewData, setInterviewData] = useState({
    applicationId: "",
    candidateName: "",
    jobTitle: "",
    date: "",
    time: "",
    interviewer: "",
    interviewType: "",
    location: "",
    notes: "",
    result: "pending",
  });

  // Mock data
  const applications = [
    { id: 1, candidateName: "John Doe", jobTitle: "Senior Frontend Developer" },
    { id: 2, candidateName: "Jane Smith", jobTitle: "Product Manager" },
    { id: 3, candidateName: "Bob Wilson", jobTitle: "UX Designer" },
    { id: 4, candidateName: "Alice Brown", jobTitle: "Backend Engineer" },
  ];

  const interviewers = [
    "Sarah Wilson",
    "Mike Johnson", 
    "Lisa Anderson",
    "Tom Davis",
    "Emma Thompson",
  ];

  const interviewTypes = [
    "Phone Screening",
    "Technical Interview",
    "Behavioral Interview",
    "Portfolio Review",
    "Panel Interview",
    "Final Interview",
  ];

  const handleApplicationChange = (applicationId: string) => {
    const selectedApp = applications.find(app => app.id.toString() === applicationId);
    if (selectedApp) {
      setInterviewData({
        ...interviewData,
        applicationId,
        candidateName: selectedApp.candidateName,
        jobTitle: selectedApp.jobTitle,
      });
    }
  };

  const handleSubmit = () => {
    if (!interviewData.applicationId || !interviewData.date || !interviewData.time || !interviewData.interviewer) {
      toast({
        title: "Error",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "Success",
      description: `Interview has been ${isEditing ? "updated" : "scheduled"} successfully.`,
    });
    navigate("/interviews");
  };

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
          <Button onClick={handleSubmit}>
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
                  value={interviewData.applicationId}
                  onValueChange={handleApplicationChange}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an application" />
                  </SelectTrigger>
                  <SelectContent>
                    {applications.map((app) => (
                      <SelectItem key={app.id} value={app.id.toString()}>
                        {app.candidateName} - {app.jobTitle}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {interviewData.candidateName && (
                <div className="p-3 bg-muted rounded-lg space-y-2">
                  <div>
                    <strong>Candidate:</strong> {interviewData.candidateName}
                  </div>
                  <div>
                    <strong>Position:</strong> {interviewData.jobTitle}
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
              <CardDescription>Set the date, time, and location</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="date">Date *</Label>
                  <Input
                    id="date"
                    type="date"
                    value={interviewData.date}
                    onChange={(e) => setInterviewData({...interviewData, date: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="time">Time *</Label>
                  <Input
                    id="time"
                    type="time"
                    value={interviewData.time}
                    onChange={(e) => setInterviewData({...interviewData, time: e.target.value})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="location">Location / Meeting Link</Label>
                <Input
                  id="location"
                  value={interviewData.location}
                  onChange={(e) => setInterviewData({...interviewData, location: e.target.value})}
                  placeholder="Office room or video call link"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Interview Details</CardTitle>
              <CardDescription>Specify interviewer and interview type</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="interviewer">Interviewer *</Label>
                <Select
                  value={interviewData.interviewer}
                  onValueChange={(value) => setInterviewData({...interviewData, interviewer: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select interviewer" />
                  </SelectTrigger>
                  <SelectContent>
                    {interviewers.map((interviewer) => (
                      <SelectItem key={interviewer} value={interviewer}>
                        {interviewer}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="interviewType">Interview Type</Label>
                <Select
                  value={interviewData.interviewType}
                  onValueChange={(value) => setInterviewData({...interviewData, interviewType: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select interview type" />
                  </SelectTrigger>
                  <SelectContent>
                    {interviewTypes.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {isEditing && (
                <div className="space-y-2">
                  <Label htmlFor="result">Interview Result</Label>
                  <Select
                    value={interviewData.result}
                    onValueChange={(value) => setInterviewData({...interviewData, result: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="accepted">Accepted</SelectItem>
                      <SelectItem value="rejected">Rejected</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
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
                <strong>Candidate:</strong> {interviewData.candidateName || "Not selected"}
              </div>
              <div>
                <strong>Position:</strong> {interviewData.jobTitle || "Not selected"}
              </div>
              <div>
                <strong>Date & Time:</strong> {
                  interviewData.date && interviewData.time
                    ? `${new Date(interviewData.date).toLocaleDateString()} at ${interviewData.time}`
                    : "Not scheduled"
                }
              </div>
              <div>
                <strong>Interviewer:</strong> {interviewData.interviewer || "Not assigned"}
              </div>
              <div>
                <strong>Type:</strong> {interviewData.interviewType || "Not specified"}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AddEditInterview;
