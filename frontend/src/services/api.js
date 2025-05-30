const API_V1_PREFIX = "http://84.16.230.94:8017/api/v1";

class ApiService {
  constructor() {
    this.baseURL = API_V1_PREFIX;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    // Get token from localStorage and include it in headers if it exists
    const token = localStorage.getItem('token');
    
    // Start with default headers
    const headers = {
      'Content-Type': 'application/json',
    };
    
    // Add Authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Merge with any custom headers from options (this will override defaults)
    Object.assign(headers, options.headers || {});
    
    const config = {
      headers,
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
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
      
      return await response.json();
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

  // Candidate endpoints
  async createCandidate(candidateData, resumeFile = null) {
    const formData = new FormData();
    formData.append('candidate_in', JSON.stringify(candidateData));
    
    if (resumeFile) {
      formData.append('resume', resumeFile);
    }

    return this.request('/candidates/', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
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

  async changePassword(passwordData) {
    return this.request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData),
    });
  }

  async getCurrentUser() {
    return this.request('/hrs/');
  }
}

// Create and export a singleton instance
const apiService = new ApiService();
export default apiService;
