import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription, DialogClose } from "@/components/ui/dialog";
import { Calendar, Clock, User, Loader2, AlertTriangle, Bot, Users } from "lucide-react";
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
  notes: string;
  interviewer_id: string;
  category: string;
  is_ai_interview: boolean;
}

interface HR {
  id: number;
  full_name: string;
  email: string;
  interviews_types?: string[];
}

interface NextInterviewResponse {
  interview_category: string | null;
  step_number: number | null;
  total_steps: number;
  completed_interviews: string[];
  interview_sequence: string[];
  is_complete: boolean;
  message: string;
}

const INTERVIEW_TYPES = [
  { value: "phone", label: "Phone" },
  { value: "video", label: "Video" },
  { value: "live", label: "Live/In-Person" },
];

const AddEditInterview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const is_editing = Boolean(id);

  const [interview_data, setInterviewData] = useState<InterviewFormData>({
    application_id: "",
    date: "",
    type: "phone",
    notes: "",
    interviewer_id: "",
    category: "",
    is_ai_interview: false,
  });

  const [applications, setApplications] = useState<Application[]>([]);
  const [hr_users, setHrUsers] = useState<HR[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [next_interview_data, setNextInterviewData] = useState<NextInterviewResponse | null>(null);
  const [job_interview_categories, setJobInterviewCategories] = useState<string[]>([]);
  const [available_categories, setAvailableCategories] = useState<string[]>([]);
  const [interviewer_category_warning, setInterviewerCategoryWarning] = useState<string | null>(null);
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiModalDate, setAIModalDate] = useState("");
  const [aiModalLoading, setAIModalLoading] = useState(false);

  // Fetch applications data
  const fetch_applications = async () => {
    try {
      const data = await apiService.getEmployerApplications();
      const applications_array = data?.applications || [];
      setApplications(Array.isArray(applications_array) ? applications_array : []);
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

  // Fetch HR users data
  const fetch_hr_users = async () => {
    try {
      const data = await apiService.getCompanyEmployees();
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

  // Update available categories based on application and interviewer
  const update_available_categories = (application_categories: string[], interviewer_id: string) => {
    if (!application_categories.length) {
      setAvailableCategories([]);
      setInterviewerCategoryWarning(null);
      return;
    }

    if (!interviewer_id || interviewer_id === "none") {
      setAvailableCategories(application_categories);
      setInterviewerCategoryWarning(null);
      return;
    }

    const selected_interviewer = hr_users.find(hr => hr.id.toString() === interviewer_id);
    if (!selected_interviewer || !selected_interviewer.interviews_types) {
      setAvailableCategories(application_categories);
      setInterviewerCategoryWarning(null);
      return;
    }

    const interviewer_categories = selected_interviewer.interviews_types;
    const filtered_categories = application_categories.filter(cat => 
      interviewer_categories.includes(cat)
    );

    setAvailableCategories(filtered_categories);
    
    if (filtered_categories.length === 0) {
      setInterviewerCategoryWarning(
        `${selected_interviewer.full_name} cannot conduct any of the required interview categories for this position. Please select a different interviewer.`
      );
    } else if (filtered_categories.length < application_categories.length) {
      const missing_categories = application_categories.filter(cat => 
        !interviewer_categories.includes(cat)
      );
      setInterviewerCategoryWarning(
        `${selected_interviewer.full_name} cannot conduct: ${missing_categories.join(', ')}. Consider selecting a different interviewer for those categories.`
      );
    } else {
      setInterviewerCategoryWarning(null);
    }

    // Reset category selection if current selection is not available
    if (interview_data.category && !filtered_categories.includes(interview_data.category)) {
      setInterviewData(prev => ({ ...prev, category: "" }));
    }
  };

  // Fetch next interview category for application
  const fetch_next_interview_category = async (application_id: string) => {
    try {
      const data = await apiService.getNextInterviewCategory(parseInt(application_id));
      setNextInterviewData(data);
      
      // Extract unique categories from the job's interview sequence
      let unique_categories: string[] = [];
      if (data.interview_sequence && Array.isArray(data.interview_sequence)) {
        unique_categories = [...new Set(data.interview_sequence as string[])];
        setJobInterviewCategories(unique_categories);
      }
      
      // Update available categories based on current interviewer
      update_available_categories(unique_categories, interview_data.interviewer_id);
      
      // Auto-populate the interview category if available and not editing
      if (data.interview_category && !is_editing) {
        setInterviewData(prev => ({
          ...prev,
          category: data.interview_category
        }));
      }
      
      return data;
    } catch (err) {
      console.error("Error fetching next interview category:", err);
      setNextInterviewData(null);
      setJobInterviewCategories([]);
      setAvailableCategories([]);
      setInterviewerCategoryWarning(null);
      toast({
        title: "Info",
        description: "Could not determine next interview category. Please select manually.",
        variant: "default",
      });
      return null;
    }
  };

  // Fetch interview data for editing
  const fetch_interview = async (interview_id: string) => {
    try {
      const data = await apiService.getInterview(parseInt(interview_id));
      const date = new Date(data.date);
      const formatted_date = date.toISOString().slice(0, 16);
      
      setInterviewData({
        application_id: data.application_id.toString(),
        date: formatted_date,
        type: data.type,
        notes: data.notes || "",
        interviewer_id: data.interviewer_id?.toString() || "",
        category: data.category || "",
        is_ai_interview: data.is_ai_interview || false,
      });

      // Fetch interview categories for this application
      if (data.application_id) {
        await fetch_next_interview_category(data.application_id.toString());
      }
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

  // Load initial data
  useEffect(() => {
    const load_data = async () => {
      setLoading(true);
      setError(null);
      
      try {
        await Promise.all([fetch_applications(), fetch_hr_users()]);
        
        if (is_editing && id) {
          await fetch_interview(id);
        } else {
          // Check for application_id in URL parameters
          const url_params = new URLSearchParams(window.location.search);
          const application_id = url_params.get('application_id');
          if (application_id) {
            setInterviewData(prev => ({
              ...prev,
              application_id: application_id
            }));
            // Fetch next interview category for this application
            await fetch_next_interview_category(application_id);
          }
        }
      } catch (err) {
        setError("Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    load_data();
  }, [id, is_editing]);

  // Set default interviewer when HR users are loaded
  useEffect(() => {
    if (!is_editing && hr_users.length > 0 && !interview_data.interviewer_id) {
      setInterviewData(prev => ({
        ...prev,
        interviewer_id: hr_users[0].id.toString()
      }));
    }
  }, [hr_users, is_editing, interview_data.interviewer_id]);

  // Update available categories when interviewer changes
  useEffect(() => {
    update_available_categories(job_interview_categories, interview_data.interviewer_id);
  }, [interview_data.interviewer_id, job_interview_categories, hr_users]);

  const get_selected_application = () => {
    if (!Array.isArray(applications)) return undefined;
    return applications.find(app => app.id.toString() === interview_data.application_id);
  };

  // Handler for application selection change
  const handle_application_change = async (application_id: string) => {
    setInterviewData(prev => ({
      ...prev,
      application_id: application_id,
      category: "" // Reset category when application changes
    }));
    
    if (application_id) {
      await fetch_next_interview_category(application_id);
    }
  };

  // Handler for interviewer selection change
  const handle_interviewer_change = (interviewer_id: string) => {
    setInterviewData(prev => ({
      ...prev,
      interviewer_id: interviewer_id,
      category: "" // Reset category when interviewer changes
    }));
  };

  // Handler for AI Interview button
  const handle_ai_interview_click = (application_id: string) => {
    setInterviewData(prev => ({ ...prev, application_id, is_ai_interview: true }));
    setAIModalDate("");
    setShowAIModal(true);
  };

  // Handler for AI Interview modal confirm
  const handle_ai_modal_confirm = async () => {
    if (!interview_data.application_id || !aiModalDate) {
      toast({ title: "Error", description: "Please select a date.", variant: "destructive" });
      return;
    }
    setAIModalLoading(true);
    try {
      await apiService.createInterview({
        application_id: parseInt(interview_data.application_id),
        date: new Date(aiModalDate).toISOString(),
        is_ai_interview: true,
        type: "ai",
        status: "SCHEDULED",
      });
      toast({ title: "Success", description: "AI Interview scheduled successfully." });
      setShowAIModal(false);
      navigate("/interviews");
    } catch (err) {
      toast({ title: "Error", description: "Failed to schedule AI interview.", variant: "destructive" });
    } finally {
      setAIModalLoading(false);
    }
  };

  const handle_submit = async () => {
    if (!interview_data.application_id || !interview_data.date) {
      toast({
        title: "Error",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    // Check if interviewer can conduct interviews for this position (only for human interviews)
    if (!interview_data.is_ai_interview && interview_data.interviewer_id && interview_data.interviewer_id !== "none" && available_categories.length === 0) {
      toast({
        title: "Error",
        description: "The selected interviewer cannot conduct any interview categories for this position. Please select a different interviewer.",
        variant: "destructive",
      });
      return;
    }

    setSubmitting(true);
    
    try {
      const submit_data = {
        application_id: parseInt(interview_data.application_id),
        date: new Date(interview_data.date).toISOString(),
        type: interview_data.type,
        status: "SCHEDULED",
        notes: interview_data.notes || null,
        interviewer_id: interview_data.interviewer_id && interview_data.interviewer_id !== "none" ? parseInt(interview_data.interviewer_id) : null,
        category: interview_data.category || null,
        is_ai_interview: interview_data.is_ai_interview,
      };

      if (is_editing && id) {
        await apiService.updateInterview(parseInt(id), submit_data);
        toast({
          title: "Success",
          description: "Interview updated successfully.",
        });
      } else {
        await apiService.createInterview(submit_data);
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
        description: `Failed to ${is_editing ? "update" : "create"} interview.`,
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Loading state
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

  // Error state
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

  const selected_application = get_selected_application();

  return (
    <div className="flex-1 space-y-8 p-8 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            {is_editing ? "Edit Interview" : "Schedule Interview"}
          </h1>
          <p className="text-lg text-gray-600">
            {is_editing ? "Update interview details" : "Schedule a new interview with a candidate"}
          </p>
        </div>
        <div className="flex gap-3">
          <Button 
            variant="outline"
            onClick={() => navigate("/interviews")} 
            className="shadow-md hover:shadow-lg transition-all duration-300"
          >
            Cancel
          </Button>
          <Button 
            variant="outline"
            onClick={handle_submit} 
            disabled={submitting || (!interview_data.is_ai_interview && interview_data.interviewer_id && interview_data.interviewer_id !== "none" && available_categories.length === 0)} 
            className="shadow-lg hover:shadow-xl transition-all duration-300"
          >
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {is_editing ? "Update Interview" : "Schedule Interview"}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Left Column - Main Form */}
        <div className="space-y-6">
          {/* Application Selection */}
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <User className="h-5 w-5 text-blue-600" />
                Application Details
              </CardTitle>
              <CardDescription className="text-base text-gray-600">
                Select the candidate and position for this interview
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="application" className="text-sm font-semibold text-gray-700">
                  Application *
                </Label>
                <Select
                  value={interview_data.application_id}
                  onValueChange={handle_application_change}
                >
                  <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                    <SelectValue placeholder="Select an application" />
                  </SelectTrigger>
                  <SelectContent>
                    {applications.map((app) => (
                      <SelectItem key={app.id} value={app.id.toString()}>
                        {app.candidate.full_name} - {app.job.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  size="sm"
                  variant="secondary"
                  className="mt-2"
                  onClick={() => handle_ai_interview_click(interview_data.application_id)}
                  disabled={!interview_data.application_id}
                >
                  <Bot className="h-4 w-4 mr-1" /> AI Interview
                </Button>
              </div>

              {selected_application && (
                <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg space-y-2 border border-blue-100 shadow-sm">
                  <div>
                    <strong className="text-gray-700">Candidate:</strong>{" "}
                    <span className="text-gray-800 font-medium">{selected_application.candidate.full_name}</span>
                  </div>
                  <div>
                    <strong className="text-gray-700">Position:</strong>{" "}
                    <span className="text-gray-800 font-medium">{selected_application.job.title}</span>
                  </div>
                </div>
              )}

              {/* Interview Sequence Progress */}
              {next_interview_data && (
                <div className="p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-100 shadow-sm">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-green-600" />
                      <strong className="text-gray-700">Interview Progress</strong>
                    </div>
                    
                    {next_interview_data.is_complete ? (
                      <div className="text-green-700 font-medium">
                        ✅ All interviews completed for this position
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <div className="text-blue-700 font-medium">
                          Next: {next_interview_data.interview_category?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} 
                          (Step {next_interview_data.step_number} of {next_interview_data.total_steps})
                        </div>
                        
                        {/* Progress Bar */}
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                            style={{ width: `${((next_interview_data.step_number! - 1) / next_interview_data.total_steps) * 100}%` }}
                          />
                        </div>
                        
                        {/* Interview Sequence */}
                        <div className="flex flex-wrap gap-2 mt-2">
                          {next_interview_data.interview_sequence.map((type, index) => (
                            <span
                              key={index}
                              className={`px-2 py-1 rounded-full text-xs font-medium ${
                                next_interview_data.completed_interviews.includes(type)
                                  ? 'bg-green-100 text-green-700'
                                  : type === next_interview_data.interview_category
                                  ? 'bg-blue-100 text-blue-700 ring-2 ring-blue-300'
                                  : 'bg-gray-100 text-gray-600'
                              }`}
                            >
                              {index + 1}. {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Interview Schedule */}
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3 text-xl font-bold text-gray-800">
                <Calendar className="h-5 w-5 text-blue-600" />
                Interview Schedule
              </CardTitle>
              <CardDescription className="text-base text-gray-600">
                Set the date, time, and interview type
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="date" className="text-sm font-semibold text-gray-700">
                    Date & Time *
                  </Label>
                  <Input
                    id="date"
                    type="datetime-local"
                    value={interview_data.date}
                    onChange={(e) => setInterviewData({...interview_data, date: e.target.value})}
                    className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="type" className="text-sm font-semibold text-gray-700">
                    Interview Type *
                  </Label>
                  <Select
                    value={interview_data.type}
                    onValueChange={(value) => setInterviewData({...interview_data, type: value})}
                  >
                    <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                      <SelectValue placeholder="Select interview type" />
                    </SelectTrigger>
                    <SelectContent>
                      {INTERVIEW_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* AI Interview Toggle */}
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-100">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white rounded-full shadow-sm">
                      {interview_data.is_ai_interview ? (
                        <Bot className="h-5 w-5 text-purple-600" />
                      ) : (
                        <Users className="h-5 w-5 text-blue-600" />
                      )}
                    </div>
                    <div>
                      <Label htmlFor="ai-interview" className="text-sm font-semibold text-gray-700 cursor-pointer">
                        {interview_data.is_ai_interview ? "AI-Powered Interview" : "Traditional Interview"}
                      </Label>
                      <p className="text-xs text-gray-600 mt-1">
                        {interview_data.is_ai_interview 
                          ? "Candidate will be interviewed by an AI system with automated evaluation"
                          : "Candidate will be interviewed by a human interviewer"
                        }
                      </p>
                    </div>
                  </div>
                  <Switch
                    id="ai-interview"
                    checked={interview_data.is_ai_interview}
                    onCheckedChange={(checked) => setInterviewData(prev => ({ ...prev, is_ai_interview: checked }))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="interviewer" className="text-sm font-semibold text-gray-700">
                    Interviewer {interview_data.is_ai_interview && <span className="text-xs text-gray-500">(Optional for AI interviews)</span>}
                  </Label>
                  <Select
                    value={interview_data.interviewer_id}
                    onValueChange={handle_interviewer_change}
                  >
                    <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                      <SelectValue placeholder="Select an interviewer" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No interviewer assigned</SelectItem>
                      {hr_users.map((hr) => (
                        <SelectItem key={hr.id} value={hr.id.toString()}>
                          {hr.full_name} ({hr.email})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category" className="text-sm font-semibold text-gray-700">
                    Category {interview_data.is_ai_interview && <span className="text-xs text-gray-500">(AI will handle all categories)</span>}
                    {!interview_data.is_ai_interview && next_interview_data?.interview_category && !is_editing && (
                      <span className="ml-2 text-xs text-blue-600 font-medium">
                        (Recommended: {next_interview_data.interview_category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())})
                      </span>
                    )}
                  </Label>
                  <Select
                    value={interview_data.category}
                    onValueChange={(value) => setInterviewData({...interview_data, category: value})}
                    disabled={interview_data.is_ai_interview || available_categories.length === 0}
                  >
                    <SelectTrigger className="h-12 shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                      <SelectValue placeholder={
                        interview_data.is_ai_interview 
                          ? "AI will handle all categories automatically" 
                          : available_categories.length === 0 
                            ? "No categories available for selected interviewer" 
                            : "Select interview category"
                      } />
                    </SelectTrigger>
                    <SelectContent>
                      {available_categories.map((category) => (
                        <SelectItem key={category} value={category}>
                          <div className="flex items-center justify-between w-full">
                            <span>{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                            {category === next_interview_data?.interview_category && !is_editing && (
                              <span className="text-xs text-blue-600 font-medium ml-2">Next</span>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Interviewer Category Warning (only for human interviews) */}
              {!interview_data.is_ai_interview && interviewer_category_warning && (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-yellow-800">Interview Category Compatibility</p>
                      <p className="text-sm text-yellow-700 mt-1">{interviewer_category_warning}</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Notes Section */}
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Interview Notes</CardTitle>
              <CardDescription className="text-base text-gray-600">
                Additional information and preparation notes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="notes" className="text-sm font-semibold text-gray-700">
                  Notes
                </Label>
                <Textarea
                  id="notes"
                  value={interview_data.notes}
                  onChange={(e) => setInterviewData({...interview_data, notes: e.target.value})}
                  placeholder="Add any notes about the interview, preparation items, or outcomes..."
                  rows={6}
                  className="shadow-sm border-gray-200 focus:border-blue-500 focus:ring-blue-500 resize-none"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Summary */}
        <div className="space-y-6">
          <Card className="card shadow-lg hover:shadow-xl transition-all duration-300 border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-bold text-gray-800">Interview Summary</CardTitle>
              <CardDescription className="text-base text-gray-600">
                Review the interview details before scheduling
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-100 shadow-sm space-y-3">
                <div>
                  <strong className="text-gray-700">Candidate:</strong>{" "}
                  <span className="text-gray-800 font-medium">
                    {selected_application?.candidate.full_name || "Not selected"}
                  </span>
                </div>
                <div>
                  <strong className="text-gray-700">Position:</strong>{" "}
                  <span className="text-gray-800 font-medium">
                    {selected_application?.job.title || "Not selected"}
                  </span>
                </div>
                <div>
                  <strong className="text-gray-700">Date & Time:</strong>{" "}
                  <span className="text-gray-800 font-medium">
                    {interview_data.date
                      ? new Date(interview_data.date).toLocaleString()
                      : "Not scheduled"}
                  </span>
                </div>
                <div>
                  <strong className="text-gray-700">Type:</strong>{" "}
                  <span className="text-gray-800 font-medium">
                    {INTERVIEW_TYPES.find(t => t.value === interview_data.type)?.label || "Not specified"}
                  </span>
                </div>
                <div>
                  <strong className="text-gray-700">Interview Mode:</strong>{" "}
                  <span className={`text-gray-800 font-medium flex items-center gap-2 ${interview_data.is_ai_interview ? 'text-purple-700' : 'text-blue-700'}`}>
                    {interview_data.is_ai_interview ? (
                      <>
                        <Bot className="h-4 w-4" />
                        AI-Powered Interview
                      </>
                    ) : (
                      <>
                        <Users className="h-4 w-4" />
                        Traditional Interview
                      </>
                    )}
                  </span>
                </div>
                <div>
                  <strong className="text-gray-700">Status:</strong>{" "}
                  <span className="text-gray-800 font-medium">Scheduled</span>
                </div>
                <div>
                  <strong className="text-gray-700">Interviewer:</strong>{" "}
                  <span className="text-gray-800 font-medium">
                    {interview_data.is_ai_interview ? (
                      <span className="flex items-center gap-2 text-purple-700">
                        <Bot className="h-4 w-4" />
                        AI System
                      </span>
                    ) : (
                      interview_data.interviewer_id && interview_data.interviewer_id !== "none"
                        ? hr_users.find(hr => hr.id.toString() === interview_data.interviewer_id)?.full_name || "Unknown"
                        : "Not assigned"
                    )}
                  </span>
                </div>
                <div>
                  <strong className="text-gray-700">Category:</strong>{" "}
                  <span className="text-gray-800 font-medium">
                    {interview_data.category ? interview_data.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : "Not specified"}
                  </span>
                </div>
              </div>

              {/* Warning in summary if interviewer can't conduct interviews (only for human interviews) */}
              {!interview_data.is_ai_interview && interview_data.interviewer_id && interview_data.interviewer_id !== "none" && available_categories.length === 0 && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <p className="text-sm font-medium text-red-800">Cannot Schedule Interview</p>
                  </div>
                  <p className="text-sm text-red-700 mt-1">
                    The selected interviewer cannot conduct any required interview categories for this position.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <Dialog open={showAIModal} onOpenChange={setShowAIModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Schedule AI Interview</DialogTitle>
            <DialogDescription>
              Select a date and time for the AI-powered interview. Only the date is required.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Label htmlFor="ai-date">Date & Time *</Label>
            <Input
              id="ai-date"
              type="datetime-local"
              value={aiModalDate}
              onChange={e => setAIModalDate(e.target.value)}
              className="h-12"
              disabled={aiModalLoading}
            />
          </div>
          <DialogFooter>
            <Button onClick={handle_ai_modal_confirm} disabled={aiModalLoading || !aiModalDate}>
              {aiModalLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Schedule AI Interview
            </Button>
            <DialogClose asChild>
              <Button variant="outline" disabled={aiModalLoading}>Cancel</Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AddEditInterview;
