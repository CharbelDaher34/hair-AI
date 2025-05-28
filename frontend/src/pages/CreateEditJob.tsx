
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Copy, ExternalLink } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "@/hooks/use-toast";

const CreateEditJob = () => {
  const navigate = useNavigate();
  const [jobData, setJobData] = useState({
    title: "",
    overview: "",
    requirements: "",
    objectives: "",
    autoGenerate: false,
  });

  const [selectedFormKeys, setSelectedFormKeys] = useState<number[]>([]);
  const [constraints, setConstraints] = useState<Record<number, any>>({});

  // Mock form keys data
  const formKeys = [
    { id: 1, name: "Experience Years", fieldType: "number", required: true },
    { id: 2, name: "Education Level", fieldType: "select", required: true },
    { id: 3, name: "Portfolio URL", fieldType: "text", required: false },
    { id: 4, name: "Availability", fieldType: "date", required: true },
  ];

  const handleFormKeyToggle = (keyId: number) => {
    if (selectedFormKeys.includes(keyId)) {
      setSelectedFormKeys(selectedFormKeys.filter(id => id !== keyId));
      const newConstraints = { ...constraints };
      delete newConstraints[keyId];
      setConstraints(newConstraints);
    } else {
      setSelectedFormKeys([...selectedFormKeys, keyId]);
    }
  };

  const handleConstraintChange = (keyId: number, constraintType: string, value: any) => {
    setConstraints({
      ...constraints,
      [keyId]: {
        ...constraints[keyId],
        [constraintType]: value,
      },
    });
  };

  const generateFormUrl = () => {
    const url = `https://yourcompany.com/apply/job-${Date.now()}`;
    navigator.clipboard.writeText(url);
    toast({
      title: "URL Copied!",
      description: "The application form URL has been copied to your clipboard.",
    });
    return url;
  };

  const handleSave = () => {
    if (!jobData.title) {
      toast({
        title: "Error",
        description: "Please provide a job title.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "Success",
      description: "Job has been saved successfully.",
    });
    navigate("/jobs");
  };

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Create New Job</h1>
          <p className="text-muted-foreground">
            Set up a new job posting with custom requirements
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/jobs")}>
            Cancel
          </Button>
          <Button onClick={handleSave}>Save Job</Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Job Information</CardTitle>
              <CardDescription>Basic details about the position</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Job Title</Label>
                <Input
                  id="title"
                  value={jobData.title}
                  onChange={(e) => setJobData({...jobData, title: e.target.value})}
                  placeholder="e.g., Senior Frontend Developer"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="overview">Overview</Label>
                <Textarea
                  id="overview"
                  value={jobData.overview}
                  onChange={(e) => setJobData({...jobData, overview: e.target.value})}
                  placeholder="Brief overview of the role and company"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="requirements">Requirements</Label>
                <Textarea
                  id="requirements"
                  value={jobData.requirements}
                  onChange={(e) => setJobData({...jobData, requirements: e.target.value})}
                  placeholder="List the key requirements for this position"
                  rows={4}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="objectives">Objectives</Label>
                <Textarea
                  id="objectives"
                  value={jobData.objectives}
                  onChange={(e) => setJobData({...jobData, objectives: e.target.value})}
                  placeholder="What will the successful candidate achieve?"
                  rows={4}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="autoGenerate"
                  checked={jobData.autoGenerate}
                  onCheckedChange={(checked) => setJobData({...jobData, autoGenerate: checked})}
                />
                <Label htmlFor="autoGenerate">Auto-generate job description</Label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Application Form URL</CardTitle>
              <CardDescription>Generate a public URL for external applications</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <Input
                  value="Click generate to create URL"
                  readOnly
                  className="flex-1"
                />
                <Button variant="outline" onClick={generateFormUrl}>
                  <Copy className="mr-2 h-4 w-4" />
                  Generate
                </Button>
                <Button variant="outline" size="sm">
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Form Keys & Constraints</CardTitle>
              <CardDescription>
                Attach custom form fields and set requirements
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {formKeys.map((formKey) => (
                <div key={formKey.id} className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id={`formKey-${formKey.id}`}
                      checked={selectedFormKeys.includes(formKey.id)}
                      onCheckedChange={() => handleFormKeyToggle(formKey.id)}
                    />
                    <Label htmlFor={`formKey-${formKey.id}`} className="flex-1">
                      {formKey.name}
                    </Label>
                    <Badge variant="outline">{formKey.fieldType}</Badge>
                    {formKey.required && (
                      <Badge variant="secondary" className="text-xs">Required</Badge>
                    )}
                  </div>

                  {selectedFormKeys.includes(formKey.id) && (
                    <div className="ml-6 space-y-2 p-3 bg-muted rounded-lg">
                      <Label className="text-sm font-medium">Constraints</Label>
                      {formKey.fieldType === "number" && (
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <Label className="text-xs">Min Value</Label>
                            <Input
                              type="number"
                              placeholder="0"
                              onChange={(e) => 
                                handleConstraintChange(formKey.id, "minValue", e.target.value)
                              }
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Max Value</Label>
                            <Input
                              type="number"
                              placeholder="10"
                              onChange={(e) => 
                                handleConstraintChange(formKey.id, "maxValue", e.target.value)
                              }
                            />
                          </div>
                        </div>
                      )}
                      {formKey.fieldType === "text" && (
                        <div>
                          <Label className="text-xs">Pattern (Regex)</Label>
                          <Input
                            placeholder="e.g., https://.*"
                            onChange={(e) => 
                              handleConstraintChange(formKey.id, "pattern", e.target.value)
                            }
                          />
                        </div>
                      )}
                      {formKey.fieldType === "date" && (
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <Label className="text-xs">After Date</Label>
                            <Input
                              type="date"
                              onChange={(e) => 
                                handleConstraintChange(formKey.id, "afterDate", e.target.value)
                              }
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Before Date</Label>
                            <Input
                              type="date"
                              onChange={(e) => 
                                handleConstraintChange(formKey.id, "beforeDate", e.target.value)
                              }
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {formKey.id !== formKeys[formKeys.length - 1].id && <Separator />}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CreateEditJob;
