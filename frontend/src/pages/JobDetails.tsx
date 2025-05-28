
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Edit, BarChart3, Users, ExternalLink, Copy } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { toast } from "@/hooks/use-toast";

const JobDetails = () => {
  const { id } = useParams();

  // Mock job data
  const job = {
    id: 1,
    title: "Senior Frontend Developer",
    status: "open",
    createdDate: "2024-01-15",
    overview: "We are looking for an experienced frontend developer to join our dynamic team. You will be responsible for creating user-friendly web applications using modern technologies.",
    requirements: "• 5+ years of experience with React and TypeScript\n• Strong understanding of modern JavaScript (ES6+)\n• Experience with state management (Redux/Zustand)\n• Familiarity with testing frameworks (Jest, React Testing Library)\n• Knowledge of responsive design and CSS frameworks",
    objectives: "• Develop and maintain high-quality frontend applications\n• Collaborate with designers and backend developers\n• Implement new features and improve existing ones\n• Ensure code quality through testing and code reviews\n• Mentor junior developers",
    applicationUrl: "https://yourcompany.com/apply/job-123",
    applications: 12,
  };

  const formKeys = [
    {
      id: 1,
      name: "Experience Years",
      fieldType: "number",
      required: true,
      constraints: { minValue: 3, maxValue: 15 },
    },
    {
      id: 2,
      name: "Portfolio URL",
      fieldType: "text",
      required: true,
      constraints: { pattern: "https://.*" },
    },
  ];

  const copyUrl = () => {
    navigator.clipboard.writeText(job.applicationUrl);
    toast({
      title: "URL Copied!",
      description: "The application URL has been copied to your clipboard.",
    });
  };

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{job.title}</h1>
          <div className="flex items-center space-x-4 mt-2">
            <Badge variant={job.status === "open" ? "default" : "secondary"}>
              {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
            </Badge>
            <span className="text-muted-foreground">
              Created: {new Date(job.createdDate).toLocaleDateString()}
            </span>
            <span className="text-muted-foreground">
              {job.applications} applications
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to={`/jobs/${id}/edit`}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/jobs/${id}/analytics`}>
              <BarChart3 className="mr-2 h-4 w-4" />
              Analytics
            </Link>
          </Button>
          <Button asChild>
            <Link to={`/jobs/${id}/matches`}>
              <Users className="mr-2 h-4 w-4" />
              View Matches
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Job Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground leading-relaxed">{job.overview}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Requirements</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="whitespace-pre-line text-muted-foreground">
                {job.requirements}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Objectives</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="whitespace-pre-line text-muted-foreground">
                {job.objectives}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Application Form</CardTitle>
              <CardDescription>Public URL for candidates to apply</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" onClick={copyUrl}>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy URL
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <a href={job.applicationUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Open
                  </a>
                </Button>
              </div>
              <p className="text-xs text-muted-foreground break-all">
                {job.applicationUrl}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Form Keys & Constraints</CardTitle>
              <CardDescription>Custom fields attached to this job</CardDescription>
            </CardHeader>
            <CardContent>
              {formKeys.length > 0 ? (
                <div className="space-y-4">
                  {formKeys.map((formKey, index) => (
                    <div key={formKey.id}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{formKey.name}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            <Badge variant="outline" className="text-xs">
                              {formKey.fieldType}
                            </Badge>
                            {formKey.required && (
                              <Badge variant="secondary" className="text-xs">
                                Required
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      {formKey.constraints && Object.keys(formKey.constraints).length > 0 && (
                        <div className="mt-2 p-2 bg-muted rounded text-xs">
                          <strong>Constraints:</strong>
                          <div className="mt-1">
                            {Object.entries(formKey.constraints).map(([key, value]) => (
                              <div key={key}>
                                {key}: {String(value)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {index < formKeys.length - 1 && <Separator className="mt-4" />}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">No form keys attached</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start" asChild>
                <Link to="/applications">
                  <Users className="mr-2 h-4 w-4" />
                  View All Applications
                </Link>
              </Button>
              <Button variant="outline" className="w-full justify-start" asChild>
                <Link to={`/jobs/${id}/analytics`}>
                  <BarChart3 className="mr-2 h-4 w-4" />
                  View Analytics
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default JobDetails;
