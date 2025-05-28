// Company types
export const CompanyBase = {
  name: 'string',
  description: 'string | null',
  industry: 'string | null',
  bio: 'string | null',
  website: 'string | null',
  logo_url: 'string | null',
  is_owner: 'boolean',
  domain: 'string | null', // The domain of the company example: @gmail.com
};

export const Company = {
  id: 'number',
  ...CompanyBase,
  
  // Relationships (populated when included)
  hrs: 'HR[]',
  jobs: 'Job[]',
  form_keys: 'FormKey[]',
  recruiter_links: 'RecruiterCompanyLink[]',
  recruited_to_links: 'RecruiterCompanyLink[]',
  recruited_jobs: 'Job[]',
};

// HR types
export const HRBase = {
  email: 'string',
  password: 'string',
  full_name: 'string',
  employer_id: 'number',
  role: 'string',
};

export const HR = {
  id: 'number',
  ...HRBase,
  
  // Relationships
  company: 'Company | null',
  jobs: 'Job[]',
};

// RecruiterCompanyLink types
export const RecruiterCompanyLinkBase = {
  recruiter_id: 'number',
  target_employer_id: 'number',
};

export const RecruiterCompanyLink = {
  id: 'number',
  ...RecruiterCompanyLinkBase,
  
  // Relationships
  recruiter: 'Company | null',
  target_company: 'Company | null',
};

// FormKey types
export const FormKeyBase = {
  employer_id: 'number',
  name: 'string',
  field_type: 'string',
  enum_values: 'string[] | null',
  required: 'boolean',
};

export const FormKey = {
  id: 'number',
  ...FormKeyBase,
  
  // Relationships
  company: 'Company | null',
  job_constraints: 'JobFormKeyConstraint[]',
};

// JobFormKeyConstraint types
export const JobFormKeyConstraintBase = {
  job_id: 'number',
  form_key_id: 'number',
  constraints: 'object', // JSON object
};

export const JobFormKeyConstraint = {
  id: 'number',
  ...JobFormKeyConstraintBase,
  
  // Relationships
  job: 'Job | null',
  form_key: 'FormKey | null',
};

// Job types
export const JobBase = {
  employer_id: 'number',
  recruited_to_id: 'number | null',
  job_data: 'object', // JSON object containing job details like title, description, etc.
  status: 'string', // e.g., 'open', 'closed', 'draft'
  created_by_hr_id: 'number',
};

export const Job = {
  id: 'number',
  ...JobBase,
  
  // Relationships
  employer: 'Company | null',
  recruited_to: 'Company | null',
  created_by_hr: 'HR | null',
  applications: 'Application[]',
  form_key_constraints: 'JobFormKeyConstraint[]',
};

// Candidate types
export const CandidateBase = {
  full_name: 'string',
  email: 'string',
  phone: 'string | null',
  resume_url: 'string | null',
  parsed_resume: 'object | null', // JSON object with parsed resume data
};

export const Candidate = {
  id: 'number',
  ...CandidateBase,
  
  // Relationships
  applications: 'Application[]',
};

// Application types
export const ApplicationBase = {
  candidate_id: 'number',
  job_id: 'number',
  form_responses: 'object | null', // JSON object with form field responses
};

export const Application = {
  id: 'number',
  ...ApplicationBase,
  
  // Relationships
  candidate: 'Candidate | null',
  job: 'Job | null',
  matches: 'Match[]',
  interviews: 'Interview[]',
};

// Interview types
export const InterviewBase = {
  application_id: 'number',
  date: 'string', // ISO datetime string
  type: 'string', // e.g., 'phone', 'zoom', 'in-person'
  status: 'string', // e.g., 'scheduled', 'done', 'canceled'
  notes: 'string | null',
};

export const Interview = {
  id: 'number',
  ...InterviewBase,
  
  // Relationships
  application: 'Application | null',
};

// Match types
export const MatchBase = {
  application_id: 'number',
  match_result: 'object | null', // JSON object with matching algorithm results
  status: 'string', // default: 'pending'
};

export const Match = {
  id: 'number',
  ...MatchBase,
  
  // Relationships
  application: 'Application | null',
};

// Common status enums
export const JobStatus = {
  OPEN: 'open',
  CLOSED: 'closed',
  DRAFT: 'draft',
  ACTIVE: 'active',
  INACTIVE: 'inactive',
};

export const InterviewStatus = {
  SCHEDULED: 'scheduled',
  DONE: 'done',
  CANCELED: 'canceled',
};

export const InterviewType = {
  PHONE: 'phone',
  ZOOM: 'zoom',
  IN_PERSON: 'in-person',
  VIDEO: 'video',
};

export const MatchStatus = {
  PENDING: 'pending',
  REVIEWED: 'reviewed',
  ACCEPTED: 'accepted',
  REJECTED: 'rejected',
};

export const HRRole = {
  HR_MANAGER: 'hr_manager',
  RECRUITER: 'recruiter',
  ADMIN: 'admin',
};

export const FormFieldType = {
  TEXT: 'text',
  EMAIL: 'email',
  NUMBER: 'number',
  SELECT: 'select',
  MULTISELECT: 'multiselect',
  TEXTAREA: 'textarea',
  CHECKBOX: 'checkbox',
  RADIO: 'radio',
  DATE: 'date',
  FILE: 'file',
};

// API Response types
export const ApiResponse = {
  success: 'boolean',
  data: 'any',
  message: 'string',
  error: 'string | null',
};

export const PaginatedResponse = {
  items: 'any[]',
  total: 'number',
  page: 'number',
  size: 'number',
  pages: 'number',
};

// Auth types
export const LoginRequest = {
  username: 'string', // email
  password: 'string',
};

export const LoginResponse = {
  access_token: 'string',
  token_type: 'string', // 'bearer'
};

export const TokenData = {
  sub: 'string', // subject (user email)
  user_type: 'string', // 'hr'
  employer_id: 'number',
  exp: 'number', // expiration timestamp
};

// Create/Update request types (without id, timestamps, and relationships)
export const CompanyCreate = {
  name: 'string',
  description: 'string | null',
  industry: 'string | null',
  bio: 'string | null',
  website: 'string | null',
  logo_url: 'string | null',
  is_owner: 'boolean',
  domain: 'string | null',
};

export const CompanyUpdate = {
  name: 'string | undefined',
  description: 'string | null | undefined',
  industry: 'string | null | undefined',
  bio: 'string | null | undefined',
  website: 'string | null | undefined',
  logo_url: 'string | null | undefined',
  is_owner: 'boolean | undefined',
  domain: 'string | null | undefined',
};

export const HRCreate = {
  email: 'string',
  password: 'string',
  full_name: 'string',
  employer_id: 'number',
  role: 'string',
};

export const HRUpdate = {
  email: 'string | undefined',
  password: 'string | undefined',
  full_name: 'string | undefined',
  employer_id: 'number | undefined',
  role: 'string | undefined',
};

export const JobCreate = {
  employer_id: 'number',
  recruited_to_id: 'number | null',
  job_data: 'object',
  status: 'string',
  created_by_hr_id: 'number',
};

export const JobUpdate = {
  employer_id: 'number | undefined',
  recruited_to_id: 'number | null | undefined',
  job_data: 'object | undefined',
  status: 'string | undefined',
  created_by_hr_id: 'number | undefined',
};

export const CandidateCreate = {
  full_name: 'string',
  email: 'string',
  phone: 'string | null',
  resume_url: 'string | null',
  parsed_resume: 'object | null',
};

export const ApplicationCreate = {
  candidate_id: 'number',
  job_id: 'number',
  form_responses: 'object | null',
};

export const InterviewCreate = {
  application_id: 'number',
  date: 'string',
  type: 'string',
  status: 'string',
  notes: 'string | null',
};

// Helper functions for type checking (optional)
export const isValidJobStatus = (status) => {
  return Object.values(JobStatus).includes(status);
};

export const isValidInterviewStatus = (status) => {
  return Object.values(InterviewStatus).includes(status);
};

export const isValidInterviewType = (type) => {
  return Object.values(InterviewType).includes(type);
};

export const isValidHRRole = (role) => {
  return Object.values(HRRole).includes(role);
};

export const isValidFormFieldType = (type) => {
  return Object.values(FormFieldType).includes(type);
}; 