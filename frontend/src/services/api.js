// Determine the API base URL based on environment
const get_api_base_url = () => {
  // Check if we're running in Docker (set via environment variable)
  const is_docker = import.meta.env.VITE_DOCKER === 'true';
  
  if (is_docker) {
    // In Docker, use the server IP since the browser runs on the host
    return "http://84.16.230.94:8017/api/v1";
  } else {
    // For local development, use localhost
    return "http://localhost:8017/api/v1";
  }
};

const API_V1_PREFIX = get_api_base_url();

class ApiService {
  constructor() {
    this.baseURL = API_V1_PREFIX;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    console.log('API Request:', url, options);
    
    // Get token from localStorage and include it in headers if it exists
    const token = localStorage.getItem('token');
    
    // Only set Content-Type if body is not FormData
    const headers = {};
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
    
    // Add Authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Only merge if options.headers is provided and not empty
    if (options.headers && Object.keys(options.headers).length > 0) {
      Object.assign(headers, options.headers);
    }
    
    const config = {
      headers,
      ...options,
    };

    try {
      console.log('Making fetch request to:', url, 'with config:', config);
      const response = await fetch(url, config);
      console.log('Response received:', response.status, response.statusText);
      
      if (!response.ok) {
        // Handle 401 Unauthorized - token might be expired
        if (response.status === 401) {
          localStorage.removeItem('token'); // Clear invalid token
          // Optionally redirect to login page
          if (window.location.pathname !== '/login' && window.location.pathname !== '/signup') {
            window.location.href = '/login';
          }
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Company endpoints
  async createCompany(companyData) {
    return this.request('/companies/', {
      method: 'POST',
      body: JSON.stringify(companyData),
    });
  }

  async getCompany(companyId) {
    return this.request(`/companies/${companyId}`);
  }

  async updateCompany(companyId, updateData) {
    return this.request(`/companies/${companyId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  }

  async deleteCompany(companyId) {
    return this.request(`/companies/${companyId}`, {
      method: 'DELETE',
    });
  }

  async getAllCompanies() {
    return this.request('/companies/');
  }

  async getRecruitToCompanies() {
    return this.request('/companies/recruit_to');
  }

  async getCurrentCompany() {
    return this.request('/companies/by_hr/');
  }

  async getCandidatesForCurrentCompany() {
    return this.request('/companies/candidates/');
  }

  // HR endpoints
  async createHR(hrData) {
    return this.request('/hrs/', {
      method: 'POST',
      body: JSON.stringify(hrData),
    });
  }

  async getHR(hrId) {
    return this.request(`/hrs/${hrId}`);
  }

  async updateHR(hrId, updateData) {
    return this.request(`/hrs/${hrId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  }

  async deleteHR(hrId) {
    return this.request(`/hrs/${hrId}`, {
      method: 'DELETE',
    });
  }

  async getCompanyEmployees(skip = 0, limit = 100) {
    return this.request(`/hrs/employees?skip=${skip}&limit=${limit}`);
  }

  // Job endpoints
  async createJob(jobData) {
    return this.request('/jobs/', {
      method: 'POST',
      body: JSON.stringify(jobData),
    });
  }

  async getJob(jobId) {
    return this.request(`/jobs/${jobId}`);
  }

  async updateJob(jobId, updateData) {
    return this.request(`/jobs/${jobId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  }

  async deleteJob(jobId) {
    return this.request(`/jobs/${jobId}`, {
      method: 'DELETE',
    });
  }

  async getJobFormData(jobId) {
    return this.request(`/jobs/form-data/${jobId}`);
  }

  // Application endpoints
  async createApplication(applicationData) {
    return this.request('/applications/', {
      method: 'POST',
      body: JSON.stringify(applicationData),
    });
  }

  async getApplication(applicationId) {
    return this.request(`/applications/${applicationId}`);
  }

  async getApplicationWithDetails(applicationId) {
    return this.request(`/applications/${applicationId}/details`);
  }

  async updateApplication(applicationId, updateData) {
    return this.request(`/applications/${applicationId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  }

  async deleteApplication(applicationId) {
    return this.request(`/applications/${applicationId}`, {
      method: 'DELETE',
    });
  }

  async getEmployerApplications(skip = 0, limit = 100) {
    return this.request(`/applications/employer-applications?skip=${skip}&limit=${limit}`);
  }

  async updateApplicationStatus(applicationId, status) {
    return this.request(`/applications/${applicationId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  // Candidate endpoints
  async createCandidate(candidateData, resumeFile = null) {
    const formData = new FormData();
    formData.append('candidate_in', JSON.stringify(candidateData));
    
    if (resumeFile) {
      formData.append('resume', resumeFile);
    }

    // Do NOT set headers here!
    return this.request('/candidates/', {
      method: 'POST',
      body: formData,
    });
  }

  async getCandidate(candidateId) {
    return this.request(`/candidates/${candidateId}`);
  }

  async updateCandidate(candidateId, updateData) {
    return this.request(`/candidates/${candidateId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  }

  async deleteCandidate(candidateId) {
    return this.request(`/candidates/${candidateId}`, {
      method: 'DELETE',
    });
  }

  async getCandidateResume(candidateId) {
    const url = `${this.baseURL}/candidates/${candidateId}/resume`;
    
    // Get token from localStorage
    const token = localStorage.getItem('token');
    
    const headers = {
      'Accept': 'application/pdf',
    };
    
    // Add Authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
      });
      
      if (!response.ok) {
        // Handle 401 Unauthorized - token might be expired
        if (response.status === 401) {
          localStorage.removeItem('token');
          if (window.location.pathname !== '/login' && window.location.pathname !== '/signup') {
            window.location.href = '/login';
          }
        }
        throw new Error(`Failed to fetch resume: ${response.status} ${response.statusText}`);
      }
      
      // Check if the response is actually a PDF
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/pdf')) {
        throw new Error('Response is not a PDF file');
      }
      
      return await response.blob();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async getCandidateParsingStatus(candidateId) {
    return this.request(`/candidates/${candidateId}/parsing-status`);
  }

  async getAllCandidates(skip = 0, limit = 100) {
    return this.request(`/candidates/?skip=${skip}&limit=${limit}`);
  }

  async getCandidatesTable() {
    return this.request('/candidates/table');
  }

  async getCandidateDetails(candidateId) {
    return this.request(`/candidates/${candidateId}/details`);
  }

  // OTP endpoints
  async sendOTP(email, fullName = '') {
    return this.request('/candidates/send-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        full_name: fullName
      }),
    });
  }

  async verifyOTP(email, otpCode) {
    return this.request('/candidates/verify-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        otp_code: otpCode
      }),
    });
  }

  async getOTPStatus(email) {
    return this.request(`/candidates/otp-status/${encodeURIComponent(email)}`, {
      method: 'GET',
    });
  }

  // Form Key endpoints
  async createFormKey(formKeyData) {
    // Remove employer_id from the data since it's extracted from token on backend
    const { employer_id, ...dataWithoutEmployerId } = formKeyData;
    return this.request('/form_keys/', {
      method: 'POST',
      body: JSON.stringify(dataWithoutEmployerId),
    });
  }

  async getFormKey(formKeyId) {
    return this.request(`/form_keys/${formKeyId}`);
  }

  async getFormKeysByCompany(skip = 0, limit = 100) {
    return this.request(`/form_keys/?skip=${skip}&limit=${limit}`);
  }

  async updateFormKey(formKeyId, updateData) {
    // Remove employer_id from the data since it's extracted from token on backend
    const { employer_id, ...dataWithoutEmployerId } = updateData;
    return this.request(`/form_keys/${formKeyId}`, {
      method: 'PATCH',
      body: JSON.stringify(dataWithoutEmployerId),
    });
  }

  async deleteFormKey(formKeyId) {
    return this.request(`/form_keys/${formKeyId}`, {
      method: 'DELETE',
    });
  }

  // Match endpoints
  async getMatchesByApplication(applicationId) {
    return this.request(`/matches/by-application/${applicationId}`);
  }

  async updateMatch(matchId, updateData) {
    return this.request(`/matches/${matchId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  }

  // Job Form Key Constraint endpoints
  async createJobFormKeyConstraint(constraintData) {
    return this.request('/job_form_key_constraints/', {
      method: 'POST',
      body: JSON.stringify(constraintData),
    });
  }

  async getJobFormKeyConstraint(constraintId) {
    return this.request(`/job_form_key_constraints/${constraintId}`);
  }

  async getConstraintsByJob(jobId, skip = 0, limit = 100) {
    return this.request(`/job_form_key_constraints/by-job/${jobId}?skip=${skip}&limit=${limit}`);
  }

  async updateJobFormKeyConstraint(constraintId, updateData) {
    return this.request(`/job_form_key_constraints/${constraintId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  }

  async deleteJobFormKeyConstraint(constraintId) {
    return this.request(`/job_form_key_constraints/${constraintId}`, {
      method: 'DELETE',
    });
  }

  // Batch method to set constraints for a job
  async setConstraintsForJob(jobId, constraints) {
    try {
      // First, get existing constraints for this job
      const existingConstraints = await this.getConstraintsByJob(jobId);
      const existingConstraintMap = new Map();
      
      if (existingConstraints && Array.isArray(existingConstraints)) {
        existingConstraints.forEach(constraint => {
          existingConstraintMap.set(constraint.form_key_id, constraint);
        });
      }

      const results = [];
      
      // Create or update constraints
      for (const constraint of constraints) {
        const existingConstraint = existingConstraintMap.get(constraint.form_key_id);
        
        if (existingConstraint) {
          // Update existing constraint
          const updateData = {
            constraints: constraint.constraints
          };
          const result = await this.updateJobFormKeyConstraint(existingConstraint.id, updateData);
          results.push(result);
          existingConstraintMap.delete(constraint.form_key_id); // Mark as processed
        } else {
          // Create new constraint
          const result = await this.createJobFormKeyConstraint(constraint);
          results.push(result);
        }
      }
      
      // Delete constraints that are no longer selected
      for (const [formKeyId, existingConstraint] of existingConstraintMap) {
        await this.deleteJobFormKeyConstraint(existingConstraint.id);
      }
      
      return results;
    } catch (error) {
      console.error('Error setting constraints for job:', error);
      throw error;
    }
  }

  // Recruiter Company Link endpoints
  async createRecruiterCompanyLink(linkData) {
    return this.request('/recruiter_company_links/', {
      method: 'POST',
      body: JSON.stringify(linkData),
    });
  }

  async getRecruiterCompanyLink(linkId) {
    return this.request(`/recruiter_company_links/${linkId}`);
  }

  async getRecruiterCompanyLinksByRecruiter(skip = 0, limit = 100) {
    return this.request(`/recruiter_company_links/by-recruiter/?skip=${skip}&limit=${limit}`);
  }

  async deleteRecruiterCompanyLink(linkId) {
    return this.request(`/recruiter_company_links/${linkId}`, {
      method: 'DELETE',
    });
  }

  // Auth endpoints
  async registerHR(hr_data) {
    console.log("hr_data", hr_data);
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(hr_data),
    });
  }

  async loginHR(email, password) {
    const form_data = new URLSearchParams();
    form_data.append('username', email);
    form_data.append('password', password);
    return this.request('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form_data,
    });
  }

  // Job endpoints
  async getAllJobs(skip = 0, limit = 100) {
    return this.request(`/jobs/?skip=${skip}&limit=${limit}`);
  }

  async getJobsByEmployer(employer_id, skip = 0, limit = 100) {
    return this.request(`/jobs/by-employer/${employer_id}?skip=${skip}&limit=${limit}`);
  }

  async getJobsByStatus(status, skip = 0, limit = 100) {
    return this.request(`/jobs/by-status/${status}?skip=${skip}&limit=${limit}`);
  }

  async getJobAnalytics(jobId) {
    return this.request(`/jobs/analytics/${jobId}`);
  }

  async getJobMatches(jobId) {
    console.log('getJobMatches called with jobId:', jobId);
    return this.request(`/jobs/matches/${jobId}`);
  }

  async generateJobDescription(data) {
    return this.request('/jobs/generate_description', {
      method: 'POST',
      body: JSON.stringify({ data }),
    });
  }

  async getCompanyAnalytics() {
    return this.request(`/analytics/company/`);
  }

  async changePassword(passwordData) {
    return this.request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData),
    });
  }

  async getCurrentUser() {
    return this.request('/hrs/');
  }

  // Interview endpoints
  async createInterview(interviewData) {
    return this.request('/interviews/', {
      method: 'POST',
      body: JSON.stringify(interviewData),
    });
  }

  async getInterview(interviewId) {
    return this.request(`/interviews/${interviewId}`);
  }

  async updateInterview(interviewId, updateData) {
    return this.request(`/interviews/${interviewId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async deleteInterview(interviewId) {
    return this.request(`/interviews/${interviewId}`, {
      method: 'DELETE',
    });
  }

  async getAllInterviews(skip = 0, limit = 100) {
    return this.request(`/interviews/?skip=${skip}&limit=${limit}`);
  }

  async getInterviewsByApplication(applicationId) {
    return this.request(`/interviews/by-application/${applicationId}`);
  }
}

// Create and export a singleton instance
const apiService = new ApiService();
export default apiService;
