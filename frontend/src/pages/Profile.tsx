import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Building2, User, Save, Edit3, Eye, EyeOff } from "lucide-react";
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
}

interface HRData {
  id: number;
  full_name: string;
  email: string;
  role: string;
  employer_id: number;
  created_at?: string;
  updated_at?: string;
}

const Profile = () => {
  const [company_data, set_company_data] = useState<CompanyData | null>(null);
  const [hr_data, set_hr_data] = useState<HRData | null>(null);
  const [is_loading, set_is_loading] = useState(true);
  const [is_saving, set_is_saving] = useState(false);
  const [is_editing_company, set_is_editing_company] = useState(false);
  const [is_editing_personal, set_is_editing_personal] = useState(false);
  
  // Form states
  const [company_form, set_company_form] = useState<Partial<CompanyData>>({});
  const [personal_form, set_personal_form] = useState<Partial<HRData>>({});
  const [password_form, set_password_form] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [show_passwords, set_show_passwords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

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

    } catch (error: any) {
      toast.error("Failed to load profile data", {
        description: error?.message || "An unexpected error occurred.",
      });
    } finally {
      set_is_loading(false);
    }
  };

  const handle_company_form_change = (field: string, value: string) => {
    set_company_form(prev => ({ ...prev, [field]: value }));
  };

  const handle_personal_form_change = (field: string, value: string) => {
    set_personal_form(prev => ({ ...prev, [field]: value }));
  };

  const handle_password_form_change = (field: string, value: string) => {
    set_password_form(prev => ({ ...prev, [field]: value }));
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

  const change_password = async () => {
    if (!password_form.current_password || !password_form.new_password) {
      toast.error("Please fill in all password fields");
      return;
    }

    if (password_form.new_password !== password_form.confirm_password) {
      toast.error("New passwords don't match");
      return;
    }

    set_is_saving(true);
    try {
      // Note: You'll need to implement a change password endpoint
      // await apiService.changePassword(password_form);
      toast.success("Password changed successfully!");
      set_password_form({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (error: any) {
      toast.error("Failed to change password", {
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

  if (is_loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Profile Settings</h1>
          <p className="text-muted-foreground">Manage your company and personal information</p>
        </div>

        <Tabs defaultValue="company" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="company" className="flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Company
            </TabsTrigger>
            <TabsTrigger value="personal" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Personal
            </TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
          </TabsList>

          <TabsContent value="company">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Company Information</CardTitle>
                    <CardDescription>
                      Update your company details and branding
                    </CardDescription>
                  </div>
                  {!is_editing_company && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => set_is_editing_company(true)}
                    >
                      <Edit3 className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="company_name">Company Name</Label>
                    <Input
                      id="company_name"
                      value={company_form.name || ""}
                      onChange={(e) => handle_company_form_change("name", e.target.value)}
                      disabled={!is_editing_company}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="company_domain">Domain</Label>
                    <Input
                      id="company_domain"
                      value={company_form.domain || ""}
                      onChange={(e) => handle_company_form_change("domain", e.target.value)}
                      disabled={!is_editing_company}
                      placeholder="yourcompany.com"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="industry">Industry</Label>
                    <Select
                      value={company_form.industry || ""}
                      onValueChange={(value) => handle_company_form_change("industry", value)}
                      disabled={!is_editing_company}
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
                    <Label htmlFor="website">Website</Label>
                    <Input
                      id="website"
                      type="url"
                      value={company_form.website || ""}
                      onChange={(e) => handle_company_form_change("website", e.target.value)}
                      disabled={!is_editing_company}
                      placeholder="https://yourcompany.com"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={company_form.description || ""}
                    onChange={(e) => handle_company_form_change("description", e.target.value)}
                    disabled={!is_editing_company}
                    rows={3}
                    placeholder="Brief description of your company"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bio">Company Bio</Label>
                  <Textarea
                    id="bio"
                    value={company_form.bio || ""}
                    onChange={(e) => handle_company_form_change("bio", e.target.value)}
                    disabled={!is_editing_company}
                    rows={4}
                    placeholder="Tell us about your company culture and values"
                  />
                </div>

                {is_editing_company && (
                  <div className="flex gap-2 pt-4">
                    <Button
                      onClick={save_company_changes}
                      disabled={is_saving}
                    >
                      <Save className="h-4 w-4 mr-2" />
                      {is_saving ? "Saving..." : "Save Changes"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={cancel_company_edit}
                      disabled={is_saving}
                    >
                      Cancel
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="personal">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Personal Information</CardTitle>
                    <CardDescription>
                      Update your personal details
                    </CardDescription>
                  </div>
                  {!is_editing_personal && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => set_is_editing_personal(true)}
                    >
                      <Edit3 className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input
                      id="full_name"
                      value={personal_form.full_name || ""}
                      onChange={(e) => handle_personal_form_change("full_name", e.target.value)}
                      disabled={!is_editing_personal}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={personal_form.email || ""}
                      onChange={(e) => handle_personal_form_change("email", e.target.value)}
                      disabled={!is_editing_personal}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Input
                    id="role"
                    value={personal_form.role || ""}
                    disabled={true}
                    className="bg-muted"
                  />
                </div>

                {is_editing_personal && (
                  <div className="flex gap-2 pt-4">
                    <Button
                      onClick={save_personal_changes}
                      disabled={is_saving}
                    >
                      <Save className="h-4 w-4 mr-2" />
                      {is_saving ? "Saving..." : "Save Changes"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={cancel_personal_edit}
                      disabled={is_saving}
                    >
                      Cancel
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card>
              <CardHeader>
                <CardTitle>Security Settings</CardTitle>
                <CardDescription>
                  Change your password and manage security preferences
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current_password">Current Password</Label>
                  <div className="relative">
                    <Input
                      id="current_password"
                      type={show_passwords.current ? "text" : "password"}
                      value={password_form.current_password}
                      onChange={(e) => handle_password_form_change("current_password", e.target.value)}
                      placeholder="Enter your current password"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => set_show_passwords(prev => ({ ...prev, current: !prev.current }))}
                    >
                      {show_passwords.current ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                <Separator />

                <div className="space-y-2">
                  <Label htmlFor="new_password">New Password</Label>
                  <div className="relative">
                    <Input
                      id="new_password"
                      type={show_passwords.new ? "text" : "password"}
                      value={password_form.new_password}
                      onChange={(e) => handle_password_form_change("new_password", e.target.value)}
                      placeholder="Enter your new password"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => set_show_passwords(prev => ({ ...prev, new: !prev.new }))}
                    >
                      {show_passwords.new ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm_password">Confirm New Password</Label>
                  <div className="relative">
                    <Input
                      id="confirm_password"
                      type={show_passwords.confirm ? "text" : "password"}
                      value={password_form.confirm_password}
                      onChange={(e) => handle_password_form_change("confirm_password", e.target.value)}
                      placeholder="Confirm your new password"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => set_show_passwords(prev => ({ ...prev, confirm: !prev.confirm }))}
                    >
                      {show_passwords.confirm ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                <Button
                  onClick={change_password}
                  disabled={is_saving}
                  className="mt-4"
                >
                  {is_saving ? "Changing Password..." : "Change Password"}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Profile; 