import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Link, useNavigate } from "react-router-dom";
import { Building2, Eye, EyeOff, ArrowLeft, ArrowRight, Check } from "lucide-react";
import { toast } from "@/components/ui/sonner";
import apiService from "../services/api";

const SignUp = () => {
  const [current_step, set_current_step] = useState(1);
  const [is_loading, set_is_loading] = useState(false);
  const [created_company_id, set_created_company_id] = useState<number | null>(null);
  const navigate = useNavigate();

  // Form data state
  const [company_data, set_company_data] = useState({
    name: "",
    domain: "",
    description: "",
    industry: "",
    website: "",
    bio: "",
  });

  const [hr_data, set_hr_data] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });

  const [show_password, set_show_password] = useState(false);
  const [show_confirm_password, set_show_confirm_password] = useState(false);

  const handle_company_data_change = (field: string, value: string) => {
    set_company_data(prev => ({ ...prev, [field]: value }));
  };

  const handle_hr_data_change = (field: string, value: string) => {
    set_hr_data(prev => ({ ...prev, [field]: value }));
  };

  const handle_step_1_submit = async () => {
    if (!company_data.name.trim()) {
      toast.error("Company name is required");
      return;
    }

    set_is_loading(true);
    try {
      const company_payload = {
        name: company_data.name,
        description: company_data.description || "",
        industry: company_data.industry || "",
        website: company_data.website || "",
        bio: company_data.bio || "",
        ...(company_data.domain && { domain: company_data.domain }),
      };

      const company_response = await apiService.createCompany(company_payload);
      if (company_response?.id) {
        set_created_company_id(company_response.id);
        toast.success("Company created successfully!");
        set_current_step(2);
      } else {
        toast.error("Failed to create company");
      }
    } catch (error: any) {
      toast.error("Company creation failed", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_loading(false);
    }
  };

  const handle_step_2_submit = async () => {
    // Validation
    if (!hr_data.full_name.trim() || !hr_data.email.trim() || !hr_data.password) {
      toast.error("All fields are required");
      return;
    }

    if (hr_data.password !== hr_data.confirm_password) {
      toast.error("Passwords don't match");
      return;
    }

    if (!created_company_id) {
      toast.error("Company ID is missing");
      return;
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
      if (hr_response?.access_token) {
        localStorage.setItem("token", hr_response.access_token);
        toast.success("Account created successfully!", {
          description: "Welcome to HR Platform!",
        });
        navigate("/");
      } else {
        toast.error("Failed to create HR account");
      }
    } catch (error: any) {
      toast.error("Account creation failed", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_loading(false);
    }
  };

  const handle_back = () => {
    if (current_step > 1) {
      set_current_step(current_step - 1);
    }
  };

  const render_step_1 = () => (
    <Card className="w-full max-w-md shadow-2xl">
      <CardHeader className="text-center space-y-2 pt-8">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Building2 className="h-10 w-10 text-primary" />
          <span className="font-bold text-3xl text-gray-800">HR Platform</span>
        </div>
        <CardTitle className="text-3xl font-bold">Company Information</CardTitle>
        <CardDescription className="text-base">
          Let's start by setting up your company
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 pb-8">
        <div className="space-y-2">
          <Label htmlFor="company_name" className="text-sm font-semibold">Company Name *</Label>
          <Input
            id="company_name"
            type="text"
            placeholder="Enter your company name"
            value={company_data.name}
            onChange={(e) => handle_company_data_change("name", e.target.value)}
            required
            disabled={is_loading}
            className="h-12"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="company_domain" className="text-sm font-semibold">Company Domain</Label>
          <Input
            id="company_domain"
            type="text"
            placeholder="e.g., yourcompany.com"
            value={company_data.domain}
            onChange={(e) => handle_company_data_change("domain", e.target.value)}
            disabled={is_loading}
            className="h-12"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="industry" className="text-sm font-semibold">Industry</Label>
          <Select
            value={company_data.industry}
            onValueChange={(value) => handle_company_data_change("industry", value)}
            disabled={is_loading}
          >
            <SelectTrigger className="h-12">
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
          <Label htmlFor="website" className="text-sm font-semibold">Website</Label>
          <Input
            id="website"
            type="url"
            placeholder="https://yourcompany.com"
            value={company_data.website}
            onChange={(e) => handle_company_data_change("website", e.target.value)}
            disabled={is_loading}
            className="h-12"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="description" className="text-sm font-semibold">Description</Label>
          <Textarea
            id="description"
            placeholder="Tell us about your company..."
            value={company_data.description}
            onChange={(e) => handle_company_data_change("description", e.target.value)}
            disabled={is_loading}
            className="min-h-[100px] resize-none"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="bio" className="text-sm font-semibold">Company Bio</Label>
          <Textarea
            id="bio"
            placeholder="A brief bio about your company culture and values..."
            value={company_data.bio}
            onChange={(e) => handle_company_data_change("bio", e.target.value)}
            disabled={is_loading}
            className="min-h-[100px] resize-none"
          />
        </div>
        <Button
          onClick={handle_step_1_submit}
          className="w-full button mt-8 py-3 text-base font-semibold"
          disabled={is_loading}
        >
          {is_loading ? "Creating Company..." : "Continue"}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  );

  const render_step_2 = () => (
    <Card className="w-full max-w-md shadow-2xl">
      <CardHeader className="text-center space-y-2 pt-8">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Building2 className="h-10 w-10 text-primary" />
          <span className="font-bold text-3xl text-gray-800">HR Platform</span>
        </div>
        <CardTitle className="text-3xl font-bold">Create Your Account</CardTitle>
        <CardDescription className="text-base">
          Set up your HR manager account
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 pb-8">
        <div className="space-y-2">
          <Label htmlFor="full_name" className="text-sm font-semibold">Full Name *</Label>
          <Input
            id="full_name"
            type="text"
            placeholder="Enter your full name"
            value={hr_data.full_name}
            onChange={(e) => handle_hr_data_change("full_name", e.target.value)}
            required
            disabled={is_loading}
            className="h-12"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email" className="text-sm font-semibold">Email Address *</Label>
          <Input
            id="email"
            type="email"
            placeholder="Enter your email address"
            value={hr_data.email}
            onChange={(e) => handle_hr_data_change("email", e.target.value)}
            required
            disabled={is_loading}
            className="h-12"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password" className="text-sm font-semibold">Password *</Label>
          <div className="relative flex items-center">
            <Input
              id="password"
              type={show_password ? "text" : "password"}
              placeholder="Create a strong password"
              value={hr_data.password}
              onChange={(e) => handle_hr_data_change("password", e.target.value)}
              required
              disabled={is_loading}
              className="h-12 pr-12"
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-0 top-1/2 transform -translate-y-1/2 h-full px-3 py-2 hover:bg-transparent text-gray-500 hover:text-gray-700"
              onClick={() => set_show_password(!show_password)}
              disabled={is_loading}
            >
              {show_password ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirm_password" className="text-sm font-semibold">Confirm Password *</Label>
          <div className="relative flex items-center">
            <Input
              id="confirm_password"
              type={show_confirm_password ? "text" : "password"}
              placeholder="Confirm your password"
              value={hr_data.confirm_password}
              onChange={(e) => handle_hr_data_change("confirm_password", e.target.value)}
              required
              disabled={is_loading}
              className="h-12 pr-12"
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-0 top-1/2 transform -translate-y-1/2 h-full px-3 py-2 hover:bg-transparent text-gray-500 hover:text-gray-700"
              onClick={() => set_show_confirm_password(!show_confirm_password)}
              disabled={is_loading}
            >
              {show_confirm_password ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
        <div className="flex gap-3 mt-8">
          <Button
            variant="outline"
            onClick={handle_back}
            className="flex-1 py-3 text-base font-semibold"
            disabled={is_loading}
          >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          <Button
            onClick={handle_step_2_submit}
            className="flex-1 button py-3 text-base font-semibold"
            disabled={is_loading}
          >
            {is_loading ? "Creating Account..." : "Create Account"}
            <Check className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const render_progress_indicator = () => (
    <div className="flex items-center justify-center mb-8">
      <div className="flex items-center space-x-4">
        <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
          current_step >= 1 ? 'bg-primary border-primary text-white' : 'border-gray-300 text-gray-300'
        }`}>
          {current_step > 1 ? <Check className="h-5 w-5" /> : '1'}
        </div>
        <div className={`h-1 w-16 ${current_step > 1 ? 'bg-primary' : 'bg-gray-300'}`} />
        <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
          current_step >= 2 ? 'bg-primary border-primary text-white' : 'border-gray-300 text-gray-300'
        }`}>
          2
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8">
      {render_progress_indicator()}
      {current_step === 1 ? render_step_1() : render_step_2()}
      <div className="mt-8 text-center text-sm">
        <span className="text-gray-600">Already have an account? </span>
        <Link
          to="/login"
          className="text-primary hover:underline font-semibold"
        >
          Sign In
        </Link>
      </div>
    </div>
  );
};

export default SignUp;
