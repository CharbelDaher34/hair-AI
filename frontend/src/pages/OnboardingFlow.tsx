import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Plus, Trash2, Upload } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "@/components/ui/sonner";
import apiService from "@/services/api";

const Signup = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [companyName, setCompanyName] = useState("");
  const [companyDomain, setCompanyDomain] = useState("");
  const [createdCompanyId, setCreatedCompanyId] = useState<number | null>(null);
  
  const [hrData, setHrData] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [profileData, setProfileData] = useState({
    description: "",
    industry: "",
    website: "",
    bio: "",
  });
  const [recruitableCompanies, setRecruitableCompanies] = useState([
    { name: "", industry: "", location: "" }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleCompanySubmit = async () => {
    setIsLoading(true);
    try {
      const company_payload: { name: string; description: string; industry: string; website: string; domain?: string } = {
        name: companyName,
        description: '',
        industry: '',
        website: '',
      };
      if (companyDomain) {
        company_payload.domain = companyDomain;
      }

      const company_response = await apiService.createCompany(company_payload);
      if (company_response && company_response.id) {
        setCreatedCompanyId(company_response.id);
        toast.success("Company created successfully!", {
          description: `Company ID: ${company_response.id}`,
        });
        setCurrentStep(currentStep + 1);
      } else {
        toast.error("Company creation failed", {
          description: "Could not retrieve company ID after creation.",
        });
      }
    } catch (error: any) {
      toast.error("Company creation failed", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleHRSubmit = async () => {
    if (hrData.password !== hrData.confirm_password) {
      toast.error("Passwords do not match");
      return;
    }
    if (!createdCompanyId) {
      toast.error("Company ID is missing. Please create a company first.");
      return;
    }
    setIsLoading(true);
    try {
      const hr_payload = {
        email: hrData.email,
        password: hrData.password,
        full_name: hrData.full_name,
        employer_id: createdCompanyId,
        role: "hr_manager",
      };
      const hr_response = await apiService.registerHR(hr_payload);
      if (hr_response && hr_response.access_token) {
        localStorage.setItem("token", hr_response.access_token);
        toast.success("HR account created successfully!", {
          description: "You are now logged in.",
        });
        setCurrentStep(currentStep + 1);
      } else {
        toast.error("HR account creation failed", {
          description: "Could not retrieve access token.",
        });
      }
    } catch (error: any) {
      toast.error("HR account creation failed", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleProfileSubmit = async () => {
    if (!createdCompanyId) {
        toast.error("Company ID not found. Cannot update profile.");
        return;
    }
    setIsLoading(true);
    try {
        const profile_update_payload = { ...profileData };
        const response = await apiService.updateCompany(createdCompanyId, profile_update_payload);
        toast.success("Company profile updated successfully!");
        setCurrentStep(currentStep + 1);
    } catch (error: any) {
        toast.error("Failed to update company profile", {
            description: error?.message || "An unexpected error occurred."
        });
    } finally {
        setIsLoading(false);
    }
  };

  const handleNext = async () => {
    if (currentStep === 1) {
      await handleCompanySubmit();
    } else if (currentStep === 2) {
      await handleHRSubmit();
    } else if (currentStep === 3) {
      await handleProfileSubmit();
    } else if (currentStep === 4) {
      toast.success("Setup Complete!", {
        description: "Your HR platform is ready to use.",
      });
      navigate("/");
    }
  };

  const addRecruitableCompany = () => {
    setRecruitableCompanies([...recruitableCompanies, { name: "", industry: "", location: "" }]);
  };

  const removeRecruitableCompany = (index: number) => {
    setRecruitableCompanies(recruitableCompanies.filter((_, i) => i !== index));
  };

  const updateRecruitableCompany = (index: number, field: string, value: string) => {
    const updated = recruitableCompanies.map((company, i) => 
      i === index ? { ...company, [field]: value } : company
    );
    setRecruitableCompanies(updated);
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Create Your Company</CardTitle>
              <CardDescription>Let's start by setting up your company.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="companyName">Company Name</Label>
                <Input
                  id="companyName"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Enter your company name"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="companyDomain">Company Domain (Optional)</Label>
                <Input
                  id="companyDomain"
                  value={companyDomain}
                  onChange={(e) => setCompanyDomain(e.target.value)}
                  placeholder="e.g., yourcompany.com"
                  disabled={isLoading}
                />
              </div>
            </CardContent>
          </Card>
        );

      case 2:
        return (
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Create Your HR Manager Account</CardTitle>
              <CardDescription>This account will manage your company (ID: {createdCompanyId || 'N/A'})</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="hrName">Full Name</Label>
                <Input
                  id="hrName"
                  value={hrData.full_name}
                  onChange={(e) => setHrData({...hrData, full_name: e.target.value})}
                  placeholder="Enter your full name"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hrEmail">Email</Label>
                <Input
                  id="hrEmail"
                  type="email"
                  value={hrData.email}
                  onChange={(e) => setHrData({...hrData, email: e.target.value})}
                  placeholder="your.email@example.com"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hrPassword">Password</Label>
                <Input
                  id="hrPassword"
                  type="password"
                  value={hrData.password}
                  onChange={(e) => setHrData({...hrData, password: e.target.value})}
                  placeholder="Create a strong password"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hrConfirmPassword">Confirm Password</Label>
                <Input
                  id="hrConfirmPassword"
                  type="password"
                  value={hrData.confirm_password}
                  onChange={(e) => setHrData({...hrData, confirm_password: e.target.value})}
                  placeholder="Confirm your password"
                  disabled={isLoading}
                />
              </div>
            </CardContent>
          </Card>
        );

      case 3:
        return (
          <Card className="w-full max-w-2xl">
            <CardHeader>
              <CardTitle>Company Profile Information</CardTitle>
              <CardDescription>Tell us more about your company (ID: {createdCompanyId || 'N/A'})</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="description">Company Description</Label>
                <Textarea
                  id="description"
                  value={profileData.description}
                  onChange={(e) => setProfileData({...profileData, description: e.target.value})}
                  placeholder="Describe what your company does"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="industry">Industry</Label>
                <Select
                  value={profileData.industry}
                  onValueChange={(value) => setProfileData({...profileData, industry: value})}
                  disabled={isLoading}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select your industry" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="healthcare">Healthcare</SelectItem>
                    <SelectItem value="finance">Finance</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="retail">Retail</SelectItem>
                    <SelectItem value="manufacturing">Manufacturing</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="website">Website</Label>
                <Input
                  id="website"
                  type="url"
                  value={profileData.website}
                  onChange={(e) => setProfileData({...profileData, website: e.target.value})}
                  placeholder="https://yourcompany.com"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="logo">Company Logo</Label>
                <div className="flex items-center gap-4">
                  <Button variant="outline" size="sm" disabled={isLoading} >
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Logo
                  </Button>
                  <span className="text-sm text-muted-foreground">PNG, JPG up to 5MB (Feature TBD)</span>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="bio">Company Bio</Label>
                <Textarea
                  id="bio"
                  value={profileData.bio}
                  onChange={(e) => setProfileData({...profileData, bio: e.target.value})}
                  placeholder="A brief bio about your company culture and values"
                  disabled={isLoading}
                />
              </div>
            </CardContent>
          </Card>
        );

      case 4:
        return (
          <Card className="w-full max-w-4xl">
            <CardHeader>
              <CardTitle>Add Recruitable Companies (Optional)</CardTitle>
              <CardDescription>Specify companies you can recruit for. This can be configured later.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Company Name</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recruitableCompanies.map((company, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Input
                          value={company.name}
                          onChange={(e) => updateRecruitableCompany(index, "name", e.target.value)}
                          placeholder="Company name"
                          disabled={isLoading}
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          value={company.industry}
                          onChange={(e) => updateRecruitableCompany(index, "industry", e.target.value)}
                          placeholder="Industry"
                          disabled={isLoading}
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          value={company.location}
                          onChange={(e) => updateRecruitableCompany(index, "location", e.target.value)}
                          placeholder="Location"
                          disabled={isLoading}
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeRecruitableCompany(index)}
                          disabled={recruitableCompanies.length === 1 || isLoading}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <Button variant="outline" onClick={addRecruitableCompany} disabled={isLoading}>
                <Plus className="mr-2 h-4 w-4" />
                Add Another
              </Button>
            </CardContent>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="flex flex-col items-center space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold">Welcome to HR Platform</h1>
          <p className="text-muted-foreground">Let's get your account set up in just a few steps</p>
        </div>

        <div className="flex items-center space-x-4">
          {[1, 2, 3, 4].map((step) => (
            <div key={step} className="flex items-center space-x-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${ 
                  step < currentStep ? "bg-green-500 text-white" :
                  step === currentStep
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {step}
              </div>
              {step < 4 && (
                <div
                  className={`w-16 h-0.5 ${ 
                    step < currentStep ? "bg-green-500" : "bg-muted"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {renderStep()}

        <div className="flex space-x-4 mt-8">
          {currentStep > 1 && (
            <Button variant="outline" onClick={() => setCurrentStep(currentStep - 1)} disabled={isLoading || (currentStep === 2 && createdCompanyId === null)}>
              Previous
            </Button>
          )}
          <Button onClick={handleNext} disabled={isLoading || (currentStep === 1 && !companyName) || (currentStep === 2 && (!hrData.email || !hrData.password || !hrData.confirm_password || !hrData.full_name)) }>
            {isLoading ? "Processing..." : currentStep === 4 ? "Finish Setup" : "Next"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Signup;
