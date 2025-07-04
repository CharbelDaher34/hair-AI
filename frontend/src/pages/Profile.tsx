import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Building2, User, Save, Edit3, Eye, EyeOff, Plus, Trash2 } from "lucide-react";
import { toast } from "@/components/ui/sonner";
import apiService from "@/services/api";

interface CompanyData {
  id: number;
  name: string;
  domain?: string;
  description?: string;
  industry?: string;
  website?: string;
  bio?: string;
  logo_url?: string;
  interviews_types?: string[];
}

interface HRData {
  id: number;
  full_name: string;
  email: string;
  role: string;
  employer_id: number;
  department?: string;
  created_at?: string;
  updated_at?: string;
  interviews_types?: string[];
}

interface RecruiterCompanyLink {
  id: number;
  recruiter_id: number;
  target_employer_id: number;
  created_at: string;
  updated_at: string;
}

interface RecruiterCompanyLinkWithCompany extends RecruiterCompanyLink {
  target_company?: CompanyData;
}

const Profile = () => {
  const [company_data, set_company_data] = useState<CompanyData | null>(null);
  const [hr_data, set_hr_data] = useState<HRData | null>(null);
  const [recruitable_companies, set_recruitable_companies] = useState<RecruiterCompanyLinkWithCompany[]>([]);
  const [employees, set_employees] = useState<HRData[]>([]);
  const [is_loading, set_is_loading] = useState(true);
  const [is_saving, set_is_saving] = useState(false);
  const [is_editing_company, set_is_editing_company] = useState(false);
  const [is_editing_personal, set_is_editing_personal] = useState(false);
  const [is_add_company_open, set_is_add_company_open] = useState(false);
  const [is_add_employee_open, set_is_add_employee_open] = useState(false);
  
  // Form states
  const [company_form, set_company_form] = useState<Partial<CompanyData>>({});
  const [personal_form, set_personal_form] = useState<Partial<HRData>>({});

  const [new_company_form, set_new_company_form] = useState({
    name: "",
    domain: "",
    description: "",
    industry: "",
    website: "",
    bio: "",
  });
  const [new_employee_form, set_new_employee_form] = useState({
    full_name: "",
    email: "",
    role: "",
    department: "",
    password: "",
  });


  const [new_interview_type, set_new_interview_type] = useState("");
  const [employee_interview_types, set_employee_interview_types] = useState<{[key: number]: string[]}>({});

  useEffect(() => {
    load_profile_data();
  }, []);

  const load_profile_data = async () => {
    set_is_loading(true);
    try {
      // Get current user info from token
      const token = localStorage.getItem("token");
      if (!token) {
        toast.error("No authentication token found");
        return;
      }

      // Load company data using the by_hr endpoint
      const company_response = await apiService.getCurrentCompany();
      set_company_data(company_response);
      set_company_form(company_response);

      // Load HR data using the HR endpoint
      const hr_response = await apiService.getCurrentUser();
      set_hr_data(hr_response);
      set_personal_form(hr_response);

      // Load recruitable companies
      await load_recruitable_companies();

      // Load employees
      await load_employees();

    } catch (error: any) {
      toast.error("Failed to load profile data", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_loading(false);
    }
  };

  const load_recruitable_companies = async () => {
    try {
      const links = await apiService.getRecruiterCompanyLinksByRecruiter();
      // For each link, we need to get the target company details
      const links_with_companies = await Promise.all(
        links.map(async (link: RecruiterCompanyLink) => {
          try {
            const target_company = await apiService.getCompany(link.target_employer_id);
            return { ...link, target_company };
          } catch (error) {
            console.error(`Failed to load company ${link.target_employer_id}:`, error);
            return link;
          }
        })
      );
      set_recruitable_companies(links_with_companies);
    } catch (error: any) {
      console.error("Failed to load recruitable companies:", error);
    }
  };

  const load_employees = async () => {
    try {
      const employees_data = await apiService.getCompanyEmployees();
      set_employees(employees_data);
      
      // Initialize employee interview types state
      const interview_types_map: {[key: number]: string[]} = {};
      employees_data.forEach((employee: HRData) => {
        interview_types_map[employee.id] = employee.interviews_types || [];
      });
      set_employee_interview_types(interview_types_map);
    } catch (error: any) {
      console.error("Failed to load employees:", error);
    }
  };

  const handle_company_form_change = (field: string, value: string) => {
    if (field === "interviews_types") {
      const parsed_value = JSON.parse(value);
      set_company_form(prev => ({ ...prev, [field]: parsed_value }));
    } else {
      set_company_form(prev => ({ ...prev, [field]: value }));
    }
  };

  const handle_personal_form_change = (field: string, value: string) => {
    set_personal_form(prev => ({ ...prev, [field]: value }));
  };

  const handle_new_company_form_change = (field: string, value: string) => {
    set_new_company_form(prev => ({ ...prev, [field]: value }));
  };

  const handle_new_employee_form_change = (field: string, value: string) => {
    set_new_employee_form(prev => ({ ...prev, [field]: value }));
  };

  const save_company_changes = async () => {
    if (!company_data?.id) return;

    set_is_saving(true);
    try {
      const updated_company = await apiService.updateCompany(company_data.id, company_form);
      set_company_data(updated_company);
      set_is_editing_company(false);
      toast.success("Company information updated successfully!");
    } catch (error: any) {
      toast.error("Failed to update company information", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_saving(false);
    }
  };

  const save_personal_changes = async () => {
    if (!hr_data?.id) return;

    set_is_saving(true);
    try {
      // Note: You'll need to implement updateHR endpoint
      const updated_hr = await apiService.updateHR(hr_data.id, personal_form);
      set_hr_data(updated_hr);
      set_is_editing_personal(false);
      toast.success("Personal information updated successfully!");
    } catch (error: any) {
      toast.error("Failed to update personal information", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_saving(false);
    }
  };

  const add_recruitable_company = async () => {
    if (!new_company_form.name.trim()) {
      toast.error("Company name is required");
      return;
    }

    if (!hr_data?.employer_id) {
      toast.error("Current company ID not found");
      return;
    }

    set_is_saving(true);
    try {
      // First create the company
      const company_payload = {
        name: new_company_form.name,
        description: new_company_form.description || "",
        industry: new_company_form.industry || "",
        website: new_company_form.website || "",
        bio: new_company_form.bio || "",
        ...(new_company_form.domain && { domain: new_company_form.domain }),
      };

      const created_company = await apiService.createCompany(company_payload);

      // Then create the recruiter company link
      const link_payload = {
        employer_id: hr_data.employer_id,
        recruiter_id: hr_data.employer_id,
        target_employer_id: created_company.id,
      };

      await apiService.createRecruiterCompanyLink(link_payload);

      // Reset form and close dialog
      set_new_company_form({
        name: "",
        domain: "",
        description: "",
        industry: "",
        website: "",
        bio: "",
      });
      set_is_add_company_open(false);

      // Reload recruitable companies
      await load_recruitable_companies();

      toast.success("Recruitable company added successfully!");
    } catch (error: any) {
      toast.error("Failed to add recruitable company", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_saving(false);
    }
  };

  const remove_recruitable_company = async (link_id: number) => {
    set_is_saving(true);
    try {
      await apiService.deleteRecruiterCompanyLink(link_id);
      await load_recruitable_companies();
      toast.success("Recruitable company removed successfully!");
    } catch (error: any) {
      toast.error("Failed to remove recruitable company", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_saving(false);
    }
  };

  const add_employee = async () => {
    if (!new_employee_form.full_name.trim() || !new_employee_form.email.trim() || !new_employee_form.role.trim()) {
      toast.error("Please fill in all required fields");
      return;
    }

    set_is_saving(true);
    try {
      const employee_payload = {
        full_name: new_employee_form.full_name,
        email: new_employee_form.email,
        role: new_employee_form.role,
        department: new_employee_form.department || null,
        password: new_employee_form.password || "defaultPassword123", // You might want to generate a random password
      };

      await apiService.createHR(employee_payload);

      // Reset form and close dialog
      set_new_employee_form({
        full_name: "",
        email: "",
        role: "",
        department: "",
        password: "",
      });
      set_is_add_employee_open(false);

      // Reload employees
      await load_employees();

      toast.success("Employee added successfully!");
    } catch (error: any) {
      toast.error("Failed to add employee", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_saving(false);
    }
  };

  const remove_employee = async (employee_id: number) => {
    set_is_saving(true);
    try {
      await apiService.deleteHR(employee_id);
      await load_employees();
      toast.success("Employee removed successfully!");
    } catch (error: any) {
      toast.error("Failed to remove employee", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_saving(false);
    }
  };

  const cancel_company_edit = () => {
    set_company_form(company_data || {});
    set_is_editing_company(false);
  };

  const cancel_personal_edit = () => {
    set_personal_form(hr_data || {});
    set_is_editing_personal(false);
  };

  const AddInterviewType = () => {
    if (!new_interview_type.trim()) return;
    
    const current_types = company_form.interviews_types || [];
    const normalized_type = new_interview_type.trim().toLowerCase().replace(/\s+/g, '_');
    
    if (!current_types.includes(normalized_type)) {
      const updated_types = [...current_types, normalized_type];
      handle_company_form_change("interviews_types", JSON.stringify(updated_types));
    }
    
    set_new_interview_type("");
  };

  const RemoveInterviewType = (interview_type: string) => {
    const current_types = company_form.interviews_types || [];
    const updated_types = current_types.filter(type => type !== interview_type);
    handle_company_form_change("interviews_types", JSON.stringify(updated_types));
  };



  const HandleEmployeeInterviewTypeToggle = (employee_id: number, interview_type: string) => {
    const current_types = employee_interview_types[employee_id] || [];
    const updated_types = current_types.includes(interview_type)
      ? current_types.filter(type => type !== interview_type)
      : [...current_types, interview_type];
    
    set_employee_interview_types(prev => ({
      ...prev,
      [employee_id]: updated_types
    }));
  };

  const SaveEmployeeInterviewTypes = async (employee_id: number) => {
    set_is_saving(true);
    try {
      const interview_types = employee_interview_types[employee_id] || [];
      await apiService.updateHR(employee_id, { interviews_types: interview_types });
      
      // Update the local employee data to reflect the change
      set_employees(prev => 
        prev.map(employee => 
          employee.id === employee_id 
            ? { ...employee, interviews_types: interview_types }
            : employee
        )
      );
      
      toast.success("Employee interview types updated successfully!");
    } catch (error: any) {
      toast.error("Failed to update employee interview types", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_saving(false);
    }
  };

  const FormatInterviewType = (type: string) => {
    return type.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  if (is_loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto"></div>
          <p className="text-lg font-medium text-gray-700">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="px-8">
        <div className="mb-8 space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Profile Settings
          </h1>
          <p className="text-lg text-gray-600">Manage your company and personal information</p>
        </div>

        <Tabs defaultValue="company" className="space-y-8 max-w-full">
          <TabsList className="grid w-full grid-cols-4 bg-white shadow-lg rounded-xl p-2 border-0">
            <TabsTrigger value="company" className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-500 data-[state=active]:text-white rounded-lg transition-all duration-300">
              <Building2 className="h-4 w-4" />
              Company
            </TabsTrigger>
            <TabsTrigger value="personal" className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-500 data-[state=active]:text-white rounded-lg transition-all duration-300">
              <User className="h-4 w-4" />
              Personal
            </TabsTrigger>
            <TabsTrigger value="employees" className="flex items-center gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-500 data-[state=active]:text-white rounded-lg transition-all duration-300">
              <User className="h-4 w-4" />
              Employees
            </TabsTrigger>
            <TabsTrigger value="recruitable" className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-500 data-[state=active]:text-white rounded-lg transition-all duration-300">Companies you recruit to</TabsTrigger>
          </TabsList>

          <TabsContent value="company">
            <Card className="card shadow-xl hover:shadow-2xl transition-all duration-300 border-0">
              <CardHeader className="pb-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-gray-800">Company Information</CardTitle>
                    <CardDescription className="text-base text-gray-600">
                      Update your company details and branding
                    </CardDescription>
                  </div>
                  {!is_editing_company && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => set_is_editing_company(true)}
                      className="shadow-md hover:shadow-lg transition-all duration-300"
                    >
                      <Edit3 className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="company_name" className="text-sm font-semibold text-gray-700">Company Name</Label>
                    <Input
                      id="company_name"
                      value={company_form.name || ""}
                      onChange={(e) => handle_company_form_change("name", e.target.value)}
                      disabled={!is_editing_company}
                      className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="company_domain" className="text-sm font-semibold text-gray-700">Domain</Label>
                    <Input
                      id="company_domain"
                      value={company_form.domain || ""}
                      onChange={(e) => handle_company_form_change("domain", e.target.value)}
                      disabled={!is_editing_company}
                      placeholder="yourcompany.com"
                      className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="industry" className="text-sm font-semibold text-gray-700">Industry</Label>
                    <Select
                      value={company_form.industry || ""}
                      onValueChange={(value) => handle_company_form_change("industry", value)}
                      disabled={!is_editing_company}
                    >
                      <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                        <SelectValue placeholder="Select industry" />
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
                    <Label htmlFor="website" className="text-sm font-semibold text-gray-700">Website</Label>
                    <Input
                      id="website"
                      type="url"
                      value={company_form.website || ""}
                      onChange={(e) => handle_company_form_change("website", e.target.value)}
                      disabled={!is_editing_company}
                      placeholder="https://yourcompany.com"
                      className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description" className="text-sm font-semibold text-gray-700">Description</Label>
                  <Textarea
                    id="description"
                    value={company_form.description || ""}
                    onChange={(e) => handle_company_form_change("description", e.target.value)}
                    disabled={!is_editing_company}
                    rows={3}
                    placeholder="Brief description of your company"
                    className="shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500 resize-none"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bio" className="text-sm font-semibold text-gray-700">Company Bio</Label>
                  <Textarea
                    id="bio"
                    value={company_form.bio || ""}
                    onChange={(e) => handle_company_form_change("bio", e.target.value)}
                    disabled={!is_editing_company}
                    rows={4}
                    placeholder="Tell us about your company culture and values"
                    className="shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500 resize-none"
                  />
                </div>

                <div className="space-y-4">
                  <Label className="text-sm font-semibold text-gray-700">Interview Types</Label>
                  <p className="text-sm text-gray-600">Manage the types of interviews your company conducts</p>
                  
                  {is_editing_company && (
                    <div className="flex gap-2">
                      <Input
                        placeholder="Add new interview type..."
                        value={new_interview_type}
                        onChange={(e) => set_new_interview_type(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            AddInterviewType();
                          }
                        }}
                        className="flex-1"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={AddInterviewType}
                        disabled={!new_interview_type.trim()}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Add
                      </Button>
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    {(company_form.interviews_types || []).length === 0 ? (
                      <p className="text-sm text-gray-500 italic">No interview types configured</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {(company_form.interviews_types || []).map((interview_type, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
                          >
                            <span className="text-sm font-medium text-gray-700">
                              {FormatInterviewType(interview_type)}
                            </span>
                            {is_editing_company && (
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => RemoveInterviewType(interview_type)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50 h-6 w-6 p-0"
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {is_editing_company && (
                  <div className="flex gap-3 pt-6 border-t border-gray-200">
                    <Button
                      onClick={save_company_changes}
                      disabled={is_saving}
                      className="button shadow-lg hover:shadow-xl transition-all duration-300"
                    >
                      <Save className="h-4 w-4 mr-2" />
                      {is_saving ? "Saving..." : "Save Changes"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={cancel_company_edit}
                      disabled={is_saving}
                      className="shadow-md hover:shadow-lg transition-all duration-300"
                    >
                      Cancel
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="personal">
            <Card className="card shadow-xl hover:shadow-2xl transition-all duration-300 border-0">
              <CardHeader className="pb-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-gray-800">Personal Information</CardTitle>
                    <CardDescription className="text-base text-gray-600">
                      Update your personal details
                    </CardDescription>
                  </div>
                  {!is_editing_personal && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => set_is_editing_personal(true)}
                      className="shadow-md hover:shadow-lg transition-all duration-300"
                    >
                      <Edit3 className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="full_name" className="text-sm font-semibold text-gray-700">Full Name</Label>
                    <Input
                      id="full_name"
                      value={personal_form.full_name || ""}
                      onChange={(e) => handle_personal_form_change("full_name", e.target.value)}
                      disabled={!is_editing_personal}
                      className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-sm font-semibold text-gray-700">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={personal_form.email || ""}
                      onChange={(e) => handle_personal_form_change("email", e.target.value)}
                      disabled={!is_editing_personal}
                      className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="role" className="text-sm font-semibold text-gray-700">Role</Label>
                    <Input
                      id="role"
                      value={personal_form.role || ""}
                      onChange={(e) => handle_personal_form_change("role", e.target.value)}
                      disabled={!is_editing_personal}
                      className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department" className="text-sm font-semibold text-gray-700">Department</Label>
                    <Input
                      id="department"
                      value={personal_form.department || ""}
                      onChange={(e) => handle_personal_form_change("department", e.target.value)}
                      disabled={!is_editing_personal}
                      placeholder="e.g., Human Resources, Recruitment"
                      className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {is_editing_personal && (
                  <div className="flex gap-3 pt-6 border-t border-gray-200">
                    <Button
                      onClick={save_personal_changes}
                      disabled={is_saving}
                      className="button shadow-lg hover:shadow-xl transition-all duration-300"
                    >
                      <Save className="h-4 w-4 mr-2" />
                      {is_saving ? "Saving..." : "Save Changes"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={cancel_personal_edit}
                      disabled={is_saving}
                      className="shadow-md hover:shadow-lg transition-all duration-300"
                    >
                      Cancel
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="employees">
            <Card className="card shadow-xl hover:shadow-2xl transition-all duration-300 border-0">
              <CardHeader className="pb-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-gray-800">Company Employees</CardTitle>
                    <CardDescription className="text-base text-gray-600">
                      Manage your company's employees and their roles
                    </CardDescription>
                  </div>
                  <Dialog open={is_add_employee_open} onOpenChange={set_is_add_employee_open}>
                    <DialogTrigger asChild>
                      <Button className="shadow-md hover:shadow-lg transition-all duration-300">
                        <Plus className="h-4 w-4 mr-2" />
                        Add Employee
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Add New Employee</DialogTitle>
                        <DialogDescription>
                          Add a new employee to your company with their role and department information.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="new_employee_name">Full Name *</Label>
                            <Input
                              id="new_employee_name"
                              value={new_employee_form.full_name}
                              onChange={(e) => handle_new_employee_form_change("full_name", e.target.value)}
                              placeholder="Enter full name"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="new_employee_email">Email *</Label>
                            <Input
                              id="new_employee_email"
                              type="email"
                              value={new_employee_form.email}
                              onChange={(e) => handle_new_employee_form_change("email", e.target.value)}
                              placeholder="employee@company.com"
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="new_employee_role">Role *</Label>
                            <Input
                              id="new_employee_role"
                              value={new_employee_form.role}
                              onChange={(e) => handle_new_employee_form_change("role", e.target.value)}
                              placeholder="Enter role (e.g., HR Manager, Recruiter, Admin)"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="new_employee_department">Department</Label>
                            <Input
                              id="new_employee_department"
                              value={new_employee_form.department}
                              onChange={(e) => handle_new_employee_form_change("department", e.target.value)}
                              placeholder="Enter department (e.g., Human Resources, Recruitment)"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="new_employee_password">Temporary Password</Label>
                          <Input
                            id="new_employee_password"
                            type="password"
                            value={new_employee_form.password}
                            onChange={(e) => handle_new_employee_form_change("password", e.target.value)}
                            placeholder="Leave empty for default password"
                          />
                          <p className="text-sm text-muted-foreground">
                            If left empty, a default password will be assigned. The employee should change it on first login.
                          </p>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button
                          variant="outline"
                          onClick={() => set_is_add_employee_open(false)}
                          disabled={is_saving}
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={add_employee}
                          disabled={is_saving}
                        >
                          {is_saving ? "Adding..." : "Add Employee"}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                {employees.length === 0 ? (
                  <div className="text-center py-8">
                    <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">No employees found</h3>
                    <p className="text-muted-foreground mb-4">
                      Add employees to manage your company's HR team.
                    </p>
                  </div>
                                ) : (
                  <div className="space-y-6">
                    {employees.map((employee) => (
                      <Card key={employee.id} className="border border-gray-200 shadow-sm">
                        <CardContent className="p-6">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex-1">
                              <h3 className="text-lg font-semibold text-gray-900">{employee.full_name}</h3>
                              <p className="text-sm text-gray-600">{employee.email}</p>
                              <div className="flex gap-4 mt-2 text-sm text-gray-500">
                                <span>Role: <span className="capitalize">{employee.role.replace('_', ' ')}</span></span>
                                <span>Department: {employee.department || "-"}</span>
                                <span>Added: {employee.created_at ? new Date(employee.created_at).toLocaleDateString() : "-"}</span>
                              </div>
                            </div>
                            {employee.id !== hr_data?.id && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => remove_employee(employee.id)}
                                disabled={is_saving}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                          
                          <Separator className="my-4" />
                          
                          <div className="space-y-3">
                            <div className="flex items-center justify-between">
                              <Label className="text-sm font-semibold text-gray-700">Interview Types</Label>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => SaveEmployeeInterviewTypes(employee.id)}
                                disabled={is_saving}
                                className="text-xs"
                              >
                                <Save className="h-3 w-3 mr-1" />
                                Save
                              </Button>
                            </div>
                            <p className="text-xs text-gray-600">Select interview types this employee can conduct</p>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                              {(company_data?.interviews_types || []).length === 0 ? (
                                <p className="text-xs text-gray-500 italic col-span-full">
                                  No interview types configured for company. Please configure company interview types first.
                                </p>
                              ) : (
                                (company_data?.interviews_types || []).map((interview_type) => (
                                  <div key={`${employee.id}_${interview_type}`} className="flex items-center space-x-2">
                                    <input
                                      type="checkbox"
                                      id={`employee_${employee.id}_${interview_type}`}
                                      checked={(employee_interview_types[employee.id] || []).includes(interview_type)}
                                      onChange={() => HandleEmployeeInterviewTypeToggle(employee.id, interview_type)}
                                      className="h-3 w-3 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                    />
                                    <Label
                                      htmlFor={`employee_${employee.id}_${interview_type}`}
                                      className="text-xs font-medium text-gray-700 cursor-pointer"
                                    >
                                      {FormatInterviewType(interview_type)}
                                    </Label>
                                  </div>
                                ))
                              )}
                            </div>
                            {(employee_interview_types[employee.id] || []).length > 0 && (
                              <div className="mt-3 p-2 bg-blue-50 rounded-md">
                                <p className="text-xs text-blue-800 font-medium">
                                  Selected: {(employee_interview_types[employee.id] || []).map(type => FormatInterviewType(type)).join(', ')}
                                </p>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="recruitable">
            <Card className="card shadow-xl hover:shadow-2xl transition-all duration-300 border-0">
              <CardHeader className="pb-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-2xl font-bold text-gray-800">Recruitable Companies</CardTitle>
                    <CardDescription className="text-base text-gray-600">
                      Manage companies that your organization can recruit for
                    </CardDescription>
                  </div>
                  <Dialog open={is_add_company_open} onOpenChange={set_is_add_company_open}>
                    <DialogTrigger asChild>
                      <Button className="shadow-md hover:shadow-lg transition-all duration-300">
                        <Plus className="h-4 w-4 mr-2" />
                        Add Company
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Add Recruitable Company</DialogTitle>
                        <DialogDescription>
                          Create a new company that your organization can recruit for.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="new_company_name">Company Name *</Label>
                            <Input
                              id="new_company_name"
                              value={new_company_form.name}
                              onChange={(e) => handle_new_company_form_change("name", e.target.value)}
                              placeholder="Enter company name"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="new_company_domain">Domain</Label>
                            <Input
                              id="new_company_domain"
                              value={new_company_form.domain}
                              onChange={(e) => handle_new_company_form_change("domain", e.target.value)}
                              placeholder="company.com"
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="new_industry">Industry</Label>
                            <Select
                              value={new_company_form.industry}
                              onValueChange={(value) => handle_new_company_form_change("industry", value)}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Select industry" />
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
                            <Label htmlFor="new_website">Website</Label>
                            <Input
                              id="new_website"
                              type="url"
                              value={new_company_form.website}
                              onChange={(e) => handle_new_company_form_change("website", e.target.value)}
                              placeholder="https://company.com"
                            />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="new_description">Description</Label>
                          <Textarea
                            id="new_description"
                            value={new_company_form.description}
                            onChange={(e) => handle_new_company_form_change("description", e.target.value)}
                            placeholder="Brief description of the company"
                            rows={3}
                          />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button
                          variant="outline"
                          onClick={() => set_is_add_company_open(false)}
                          disabled={is_saving}
                        >
                          Cancel
                        </Button>
                        <Button
                          onClick={add_recruitable_company}
                          disabled={is_saving}
                        >
                          {is_saving ? "Adding..." : "Add Company"}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                {recruitable_companies.length === 0 ? (
                  <div className="text-center py-8">
                    <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">No recruitable companies</h3>
                    <p className="text-muted-foreground mb-4">
                      Add companies that your organization can recruit for.
                    </p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Company Name</TableHead>
                        <TableHead>Industry</TableHead>
                        <TableHead>Website</TableHead>
                        <TableHead>Added</TableHead>
                        <TableHead></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {recruitable_companies.map((link) => (
                        <TableRow key={link.id}>
                          <TableCell className="font-medium">
                            {link.target_company?.name || "Unknown Company"}
                          </TableCell>
                          <TableCell>
                            {link.target_company?.industry || "-"}
                          </TableCell>
                          <TableCell>
                            {link.target_company?.website ? (
                              <a
                                href={link.target_company.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline"
                              >
                                {link.target_company.website}
                              </a>
                            ) : (
                              "-"
                            )}
                          </TableCell>
                          <TableCell>
                            {new Date(link.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => remove_recruitable_company(link.id)}
                              disabled={is_saving}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>


        </Tabs>
      </div>
    </div>
  );
};

export default Profile; 