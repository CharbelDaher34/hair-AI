import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Progress } from "@/components/ui/progress";
import { Plus, Trash2, Upload, Building, User, Briefcase, CheckCircle, Loader2, ArrowRight, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "@/components/ui/sonner";
import apiService from "@/services/api";

const TOTAL_STEPS = 4;

const OnboardingFlow = () => {
  const [current_step, set_current_step] = useState(1);
  const [company_name, set_company_name] = useState("");
  const [company_domain, set_company_domain] = useState("");
  const [created_company_id, set_created_company_id] = useState<number | null>(null);
  
  const [hr_data, set_hr_data] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [profile_data, set_profile_data] = useState({
    description: "",
    industry: "",
    website: "",
    bio: "",
  });
  const [recruitable_companies, set_recruitable_companies] = useState([
    { name: "", industry: "", location: "" }
  ]);
  const [is_loading, set_is_loading] = useState(false);
  const navigate = useNavigate();

  const progress_value = (current_step / TOTAL_STEPS) * 100;

  const handle_company_submit = async () => {
    if (!company_name.trim()) {
      toast.error("Company Name is required.");
      return false;
    }
    set_is_loading(true);
    try {
      const company_payload: { name: string; description: string; industry: string; website: string; domain?: string } = {
        name: company_name,
        description: profile_data.description || '',
        industry: profile_data.industry || '',
        website: profile_data.website || '',
      };
      if (company_domain) {
        company_payload.domain = company_domain;
      }

      const company_response = await apiService.createCompany(company_payload);
      if (company_response && company_response.id) {
        set_created_company_id(company_response.id);
        toast.success("Company created successfully!", {
          description: `Company ID: ${company_response.id}`,
        });
        set_is_loading(false);
        return true;
      } else {
        toast.error("Company creation failed", {
          description: "Could not retrieve company ID after creation.",
        });
        set_is_loading(false);
        return false;
      }
    } catch (error: any) {
      toast.error("Company creation failed", {
        description: error?.message || "An unexpected error occurred.",
      });
      set_is_loading(false);
      return false;
    }
  };

  const handle_hr_submit = async () => {
    if (hr_data.password !== hr_data.confirm_password) {
      toast.error("Passwords do not match");
      return false;
    }
    if (!hr_data.email.trim() || !hr_data.password.trim() || !hr_data.full_name.trim()){
      toast.error("All HR account fields are required.");
      return false;
    }
    if (!created_company_id) {
      toast.error("Company ID is missing. Please create a company first.");
      return false;
    }
    set_is_loading(true);
    try {
      const hr_payload = {
        email: hr_data.email,
        password: hr_data.password,
        full_name: hr_data.full_name,
        employer_id: created_company_id,
        role: "hr_manager",
      };
      const hr_response = await apiService.registerHR(hr_payload);
      if (hr_response && hr_response.access_token) {
        localStorage.setItem("token", hr_response.access_token);
        toast.success("HR account created successfully!", {
          description: "You are now logged in.",
        });
        set_is_loading(false);
        return true;
      } else {
        toast.error("HR account creation failed", {
          description: "Could not retrieve access token.",
        });
        set_is_loading(false);
        return false;
      }
    } catch (error: any) {
      toast.error("HR account creation failed", {
        description: error?.message || "An unexpected error occurred.",
      });
      set_is_loading(false);
      return false;
    }
  };
  
  const handle_profile_submit = async () => {
    if (!created_company_id) {
        toast.error("Company ID not found. Cannot update profile.");
        return false;
    }
    set_is_loading(true);
    try {
        // Use profile_data which is already up-to-date
        const response = await apiService.updateCompany(created_company_id, profile_data);
        toast.success("Company profile updated successfully!");
        set_is_loading(false);
        return true;
    } catch (error: any) {
        toast.error("Failed to update company profile", {
            description: error?.message || "An unexpected error occurred."
        });
        set_is_loading(false);
        return false;
    }
  };

  const handle_next_step = async () => {
    let success = false;
    if (current_step === 1) {
      success = await handle_company_submit();
    } else if (current_step === 2) {
      success = await handle_hr_submit();
    } else if (current_step === 3) {
      success = await handle_profile_submit();
    } else if (current_step === TOTAL_STEPS) {
      toast.success("Setup Complete!", {
        description: "Your HR platform is ready to use.",
        icon: <CheckCircle className="h-5 w-5 text-green-500" />
      });
      navigate("/"); // Navigate to dashboard or main page
      return;
    }
    if (success) {
      set_current_step(current_step + 1);
    }
  };

  const handle_prev_step = () => {
    if (current_step > 1) {
      set_current_step(current_step - 1);
    }
  };

  const add_recruitable_company = () => {
    set_recruitable_companies([...recruitable_companies, { name: "", industry: "", location: "" }]);
  };

  const remove_recruitable_company = (index: number) => {
    set_recruitable_companies(recruitable_companies.filter((_, i) => i !== index));
  };

  const update_recruitable_company = (index: number, field: string, value: string) => {
    const updated = recruitable_companies.map((company, i) => 
      i === index ? { ...company, [field]: value } : company
    );
    set_recruitable_companies(updated);
  };

  const render_step_content = () => {
    switch (current_step) {
      case 1: // Create Company
        return (
          <Card className="w-full max-w-2xl shadow-2xl border-0 animate-fadeIn">
            <CardHeader className="text-center">
              <Building className="h-12 w-12 mx-auto text-blue-600 mb-3" />
              <CardTitle className="text-3xl font-bold text-gray-800">Create Your Company</CardTitle>
              <CardDescription className="text-base text-gray-600">
                Let's start by setting up your company profile.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 p-8">
              <div className="space-y-2">
                <Label htmlFor="company_name" className="text-base font-semibold text-gray-700">Company Name *</Label>
                <Input
                  id="company_name"
                  value={company_name}
                  onChange={(e) => set_company_name(e.target.value)}
                  placeholder="Your Company Inc."
                  disabled={is_loading}
                  className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_domain" className="text-base font-semibold text-gray-700">Company Domain (Optional)</Label>
                <Input
                  id="company_domain"
                  value={company_domain}
                  onChange={(e) => set_company_domain(e.target.value)}
                  placeholder="e.g., yourcompany.com"
                  disabled={is_loading}
                  className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                />
                <p className="text-xs text-gray-500">This helps in verifying employees and branding.</p>
              </div>
            </CardContent>
          </Card>
        );

      case 2: // Create HR Account
        return (
          <Card className="w-full max-w-2xl shadow-2xl border-0 animate-fadeIn">
            <CardHeader className="text-center">
              <User className="h-12 w-12 mx-auto text-blue-600 mb-3" />
              <CardTitle className="text-3xl font-bold text-gray-800">Create HR Manager Account</CardTitle>
              <CardDescription className="text-base text-gray-600">
                This account will manage your company: <span className="font-semibold text-blue-700">{company_name || "Your Company"}</span>.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 p-8">
              <div className="space-y-2">
                <Label htmlFor="hr_full_name" className="text-base font-semibold text-gray-700">Full Name *</Label>
                <Input
                  id="hr_full_name"
                  value={hr_data.full_name}
                  onChange={(e) => set_hr_data({ ...hr_data, full_name: e.target.value })}
                  placeholder="Your Full Name"
                  disabled={is_loading}
                  className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hr_email" className="text-base font-semibold text-gray-700">Email Address *</Label>
                <Input
                  id="hr_email"
                  type="email"
                  value={hr_data.email}
                  onChange={(e) => set_hr_data({ ...hr_data, email: e.target.value })}
                  placeholder="manager@yourcompany.com"
                  disabled={is_loading}
                  className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                  required
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                  <Label htmlFor="hr_password" className="text-base font-semibold text-gray-700">Password *</Label>
                <Input
                    id="hr_password"
                  type="password"
                    value={hr_data.password}
                    onChange={(e) => set_hr_data({ ...hr_data, password: e.target.value })}
                    placeholder="Enter a strong password"
                    disabled={is_loading}
                    className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                    required
                />
              </div>
              <div className="space-y-2">
                  <Label htmlFor="hr_confirm_password" className="text-base font-semibold text-gray-700">Confirm Password *</Label>
                <Input
                    id="hr_confirm_password"
                  type="password"
                    value={hr_data.confirm_password}
                    onChange={(e) => set_hr_data({ ...hr_data, confirm_password: e.target.value })}
                  placeholder="Confirm your password"
                    disabled={is_loading}
                    className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                    required
                />
                </div>
              </div>
            </CardContent>
          </Card>
        );

      case 3: // Company Profile Details
        return (
          <Card className="w-full max-w-2xl shadow-2xl border-0 animate-fadeIn">
            <CardHeader className="text-center">
              <Briefcase className="h-12 w-12 mx-auto text-blue-600 mb-3" />
              <CardTitle className="text-3xl font-bold text-gray-800">Tell Us More About {company_name}</CardTitle>
              <CardDescription className="text-base text-gray-600">
                Provide some additional details to complete your company profile.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 p-8">
              <div className="space-y-2">
                <Label htmlFor="company_industry" className="text-base font-semibold text-gray-700">Industry</Label>
                <Input
                  id="company_industry"
                  value={profile_data.industry}
                  onChange={(e) => set_profile_data({ ...profile_data, industry: e.target.value })}
                  placeholder="e.g., Technology, Healthcare, Finance"
                  disabled={is_loading}
                  className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_website" className="text-base font-semibold text-gray-700">Company Website</Label>
                <Input
                  id="company_website"
                  type="url"
                  value={profile_data.website}
                  onChange={(e) => set_profile_data({ ...profile_data, website: e.target.value })}
                  placeholder="https://yourcompany.com"
                  disabled={is_loading}
                  className="h-12 text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_bio" className="text-base font-semibold text-gray-700">Company Bio / Short Description</Label>
                <Textarea
                  id="company_bio"
                  value={profile_data.bio}
                  onChange={(e) => set_profile_data({ ...profile_data, bio: e.target.value })}
                  placeholder="Briefly describe your company's mission and values (max 200 characters)"
                  disabled={is_loading}
                  maxLength={200}
                  rows={3}
                  className="text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500 resize-none"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_description" className="text-base font-semibold text-gray-700">Detailed Company Description (Optional)</Label>
                <Textarea
                  id="company_description"
                  value={profile_data.description}
                  onChange={(e) => set_profile_data({ ...profile_data, description: e.target.value })}
                  placeholder="Provide a more detailed description of your company, its culture, and what it's like to work there."
                  disabled={is_loading}
                  rows={5}
                  className="text-base bg-white shadow-sm focus:ring-purple-500 focus:border-purple-500 resize-none"
                />
              </div>
            </CardContent>
          </Card>
        );

      case 4: // Setup Recruitable Companies (Optional Step)
        return (
          <Card className="w-full max-w-3xl shadow-2xl border-0 animate-fadeIn">
            <CardHeader className="text-center">
                <Building className="h-12 w-12 mx-auto text-blue-600 mb-3" /> 
                <CardTitle className="text-3xl font-bold text-gray-800">Target Companies (Optional)</CardTitle>
                <CardDescription className="text-base text-gray-600">
                    Specify companies you actively recruit from. This helps our AI understand your hiring patterns.
                </CardDescription>
            </CardHeader>
            <CardContent className="p-8 space-y-6">
                {recruitable_companies.map((company, index) => (
                    <div key={index} className="p-4 border rounded-lg space-y-3 bg-slate-50 shadow-sm relative">
                        <Button
                          variant="ghost"
                            size="icon" 
                            className="absolute top-2 right-2 text-red-500 hover:text-red-700 hover:bg-red-100"
                            onClick={() => remove_recruitable_company(index)}
                            disabled={is_loading || recruitable_companies.length === 1}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="space-y-1">
                                <Label htmlFor={`rc_name_${index}`} className="text-sm font-medium text-gray-700">Company Name</Label>
                                <Input 
                                    id={`rc_name_${index}`} 
                                    value={company.name} 
                                    onChange={(e) => update_recruitable_company(index, 'name', e.target.value)} 
                                    placeholder="e.g., Competitor Inc."
                                    className="h-10 bg-white"
                                    disabled={is_loading}
                                />
                            </div>
                            <div className="space-y-1">
                                <Label htmlFor={`rc_industry_${index}`} className="text-sm font-medium text-gray-700">Industry</Label>
                                <Input 
                                    id={`rc_industry_${index}`} 
                                    value={company.industry} 
                                    onChange={(e) => update_recruitable_company(index, 'industry', e.target.value)} 
                                    placeholder="e.g., Tech"
                                    className="h-10 bg-white"
                                    disabled={is_loading}
                                />
                            </div>
                            <div className="space-y-1">
                                <Label htmlFor={`rc_location_${index}`} className="text-sm font-medium text-gray-700">Location (Optional)</Label>
                                <Input 
                                    id={`rc_location_${index}`} 
                                    value={company.location} 
                                    onChange={(e) => update_recruitable_company(index, 'location', e.target.value)} 
                                    placeholder="e.g., San Francisco, CA"
                                    className="h-10 bg-white"
                                    disabled={is_loading}
                                />
                            </div>
                        </div>
                    </div>
                ))}
                <Button 
                    type="button" 
                    variant="outline"
                    onClick={add_recruitable_company} 
                    className="w-full button-outline shadow-md hover:shadow-lg transition-all duration-300 flex items-center gap-2"
                    disabled={is_loading}
                >
                    <Plus className="h-4 w-4" /> Add Another Company
              </Button>
            </CardContent>
          </Card>
        );

      default:
        return <p>Loading step...</p>;
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-100 to-blue-100 p-4 sm:p-8">
      <div className="w-full max-w-md mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-blue-700">Step {current_step} of {TOTAL_STEPS}</span>
          <span className="text-sm font-medium text-blue-700">{(progress_value).toFixed(0)}% Complete</span>
        </div>
        <Progress value={progress_value} className="w-full h-3 bg-blue-200 [&>*]:bg-gradient-to-r [&>*]:from-blue-500 [&>*]:to-purple-500 transition-all duration-500" />
        </div>

      {render_step_content()}

      <div className="mt-10 flex w-full max-w-2xl justify-between">
        <Button
          onClick={handle_prev_step}
          variant="outline"
          disabled={current_step === 1 || is_loading}
          className="button-outline text-base py-3 px-6 shadow-md hover:shadow-lg transition-all duration-300 flex items-center gap-2"
        >
          <ArrowLeft className="h-5 w-5" />
              Previous
            </Button>
        <Button
          onClick={handle_next_step}
          disabled={is_loading}
          className="button text-base py-3 px-6 shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2"
        >
          {is_loading ? (
            <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Processing...</>
          ) : current_step === TOTAL_STEPS ? (
            <><CheckCircle className="mr-2 h-5 w-5" /> Finish Setup</>
          ) : (
            <><ArrowRight className="mr-2 h-5 w-5" /> Next Step</>
          )}
          </Button>
      </div>
      <p className="mt-8 text-sm text-gray-500">
        You can always update these details later in your company settings.
      </p>
    </div>
  );
};

export default OnboardingFlow;
