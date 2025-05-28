
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FileText, Mail, Phone, User, Calendar, Star, ExternalLink } from "lucide-react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "@/hooks/use-toast";

const ViewEditApplication = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);

  // Mock application data
  const [applicationData, setApplicationData] = useState({
    id: 1,
    candidate: {
      name: "John Doe",
      email: "john.doe@email.com",
      phone: "+1 234 567 8900",
      resumeUrl: "https://example.com/resume.pdf",
      parsedResume: {
        skills: ["React", "TypeScript", "Node.js", "AWS"],
        experience: "5 years",
        education: "Bachelor's in Computer Science",
        summary: "Experienced full-stack developer with expertise in modern web technologies.",
      },
    },
    job: {
      title: "Senior Frontend Developer",
      company: "TechCorp Inc.",
    },
    status: "review",
    submissionDate: "2024-01-20",
    formResponses: {
      "experience_years": "5",
      "portfolio_url": "https://johndoe.dev",
      "availability": "Immediate",
      "expected_salary": "$120,000",
    },
    matchScore: 85,
    interviews: [
      {
        id: 1,
        date: "2024-01-25",
        time: "14:00",
        interviewer: "Sarah Wilson",
        type: "Technical",
        result: "Pending",
      },
    ],
  });

  const handleStatusChange = (newStatus: string) => {
    setApplicationData({
      ...applicationData,
      status: newStatus,
    });
    toast({
      title: "Status Updated",
      description: `Application status changed to ${newStatus}`,
    });
  };

  const handleSave = () => {
    setIsEditing(false);
    toast({
      title: "Application Updated",
      description: "Changes have been saved successfully.",
    });
  };

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Application Details</h1>
          <p className="text-muted-foreground">
            {applicationData.candidate.name} • {applicationData.job.title}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/applications")}>
            Back to Applications
          </Button>
          {isEditing ? (
            <>
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave}>Save Changes</Button>
            </>
          ) : (
            <Button onClick={() => setIsEditing(true)}>Edit Application</Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Candidate Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label>Full Name</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span>{applicationData.candidate.name}</span>
                  </div>
                </div>
                <div>
                  <Label>Email</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span>{applicationData.candidate.email}</span>
                  </div>
                </div>
                <div>
                  <Label>Phone</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <span>{applicationData.candidate.phone}</span>
                  </div>
                </div>
                <div>
                  <Label>Resume</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <a
                      href={applicationData.candidate.resumeUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline flex items-center gap-1"
                    >
                      View Resume
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              </div>

              <Separator />

              <div>
                <Label>Parsed Resume Summary</Label>
                <div className="mt-2 space-y-3">
                  <div>
                    <span className="font-medium">Skills:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {applicationData.candidate.parsedResume.skills.map((skill, index) => (
                        <Badge key={index} variant="secondary">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="font-medium">Experience:</span>
                    <span className="ml-2">{applicationData.candidate.parsedResume.experience}</span>
                  </div>
                  <div>
                    <span className="font-medium">Education:</span>
                    <span className="ml-2">{applicationData.candidate.parsedResume.education}</span>
                  </div>
                  <div>
                    <span className="font-medium">Summary:</span>
                    <p className="mt-1 text-muted-foreground">
                      {applicationData.candidate.parsedResume.summary}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Form Responses</CardTitle>
              <CardDescription>Answers to custom application questions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(applicationData.formResponses).map(([key, value]) => (
                  <div key={key}>
                    <Label className="capitalize">
                      {key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                    </Label>
                    {isEditing ? (
                      <Input
                        value={value}
                        onChange={(e) => {
                          setApplicationData({
                            ...applicationData,
                            formResponses: {
                              ...applicationData.formResponses,
                              [key]: e.target.value,
                            },
                          });
                        }}
                        className="mt-1"
                      />
                    ) : (
                      <div className="mt-1 p-2 bg-muted rounded-md">{value}</div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Interview History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {applicationData.interviews.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date & Time</TableHead>
                      <TableHead>Interviewer</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Result</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {applicationData.interviews.map((interview) => (
                      <TableRow key={interview.id}>
                        <TableCell>
                          {new Date(interview.date).toLocaleDateString()} at {interview.time}
                        </TableCell>
                        <TableCell>{interview.interviewer}</TableCell>
                        <TableCell>{interview.type}</TableCell>
                        <TableCell>
                          <Badge variant={interview.result === "Pending" ? "secondary" : "default"}>
                            {interview.result}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="text-muted-foreground">No interviews scheduled yet.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Application Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Current Status</Label>
                {isEditing ? (
                  <Select
                    value={applicationData.status}
                    onValueChange={(value) => setApplicationData({...applicationData, status: value})}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="review">Under Review</SelectItem>
                      <SelectItem value="interview">Interview Scheduled</SelectItem>
                      <SelectItem value="hired">Hired</SelectItem>
                      <SelectItem value="rejected">Rejected</SelectItem>
                    </SelectContent>
                  </Select>
                ) : (
                  <div className="mt-1">
                    <Badge variant="outline" className="capitalize">
                      {applicationData.status}
                    </Badge>
                  </div>
                )}
              </div>
              <div>
                <Label>Submitted</Label>
                <div className="mt-1 text-muted-foreground">
                  {new Date(applicationData.submissionDate).toLocaleDateString()}
                </div>
              </div>
              <div>
                <Label>Job Position</Label>
                <div className="mt-1 font-medium">{applicationData.job.title}</div>
              </div>
            </CardContent>
          </Card>

          {applicationData.matchScore && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Star className="h-5 w-5" />
                  Match Score
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">
                    {applicationData.matchScore}%
                  </div>
                  <p className="text-muted-foreground">Compatibility with job requirements</p>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleStatusChange("interview")}
                disabled={applicationData.status === "interview"}
              >
                Schedule Interview
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleStatusChange("hired")}
                disabled={applicationData.status === "hired"}
              >
                Mark as Hired
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start text-destructive hover:text-destructive"
                onClick={() => handleStatusChange("rejected")}
                disabled={applicationData.status === "rejected"}
              >
                Reject Application
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ViewEditApplication;
