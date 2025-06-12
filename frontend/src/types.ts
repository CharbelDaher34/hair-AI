export interface CompanyBase {
  name: string;
  description: string | null;
  industry: string | null;
  bio: string | null;
  website: string | null;
  logo_url: string | null;
  is_owner: boolean;
  domain: string | null; // The domain of the company example: @gmail.com
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface Company extends CompanyBase {
  id: number;
  // Relationships (populated when included)
  hrs: HR[];
  jobs: Job[];
  form_keys: FormKey[];
  recruiter_links: RecruiterCompanyLink[];
  recruited_to_links: RecruiterCompanyLink[];
  recruited_jobs: Job[];
}

// HR types
export interface HRBase {
  email: string;
  password: string;
  full_name: string;
  employer_id: number;
  role: string;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface HR extends HRBase {
  id: number;
  // Relationships
  company: Company | null;
  jobs: Job[];
}

// RecruiterCompanyLink types
export interface RecruiterCompanyLinkBase {
  recruiter_id: number;
  target_employer_id: number;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface RecruiterCompanyLink extends RecruiterCompanyLinkBase {
  id: number;
  // Relationships
  recruiter: Company | null;
  target_company: Company | null;
}

// FormKey types
export interface FormKeyBase {
  employer_id: number;
  name: string;
  field_type: FormFieldType;
  enum_values: string[] | null;
  required: boolean;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface FormKey extends FormKeyBase {
  id: number;
  // Relationships
  company: Company | null;
  job_constraints: JobFormKeyConstraint[];
}

// JobFormKeyConstraint types
export interface JobFormKeyConstraintBase {
  job_id: number;
  form_key_id: number;
  constraints: object; // JSON object
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface JobFormKeyConstraint extends JobFormKeyConstraintBase {
  id: number;
  // Relationships
  job: Job | null;
  form_key: FormKey | null;
}

// Job types
export interface JobBase {
  employer_id: number;
  recruited_to_id: number | null;
  created_by_hr_id: number;
  job_data: object; // JSON object for additional data
  status: JobStatus;
  title: string;
  description: string;
  location: string;
  salary_min: number | null;
  salary_max: number | null;
  experience_level: ExperienceLevel;
  seniority_level: SeniorityLevel;
  job_type: JobType;
  job_category: string | null;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface Job extends JobBase {
  id: number;
  // Relationships
  employer: Company | null;
  recruited_to: Company | null;
  created_by_hr: HR | null;
  applications: Application[];
  form_key_constraints: JobFormKeyConstraint[];
}

// Candidate types
export interface CandidateBase {
  full_name: string;
  email: string;
  phone: string | null;
  resume_url: string | null;
  parsed_resume: object | null; // JSON object with parsed resume data
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface Candidate extends CandidateBase {
  id: number;
  // Relationships
  applications: Application[];
}

// Application types
export interface ApplicationBase {
  candidate_id: number;
  job_id: number;
  form_responses: object | null; // JSON object with form field responses
  status: ApplicationStatus;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface Application extends ApplicationBase {
  id: number;
  // Relationships
  candidate: Candidate | null;
  job: Job | null;
  matches: Match[];
  interviews: Interview[];
}

export interface ApplicationDashboardResponse {
  applications: Application[];
  total: number;
}

// Interview types
export interface InterviewBase {
  application_id: number;
  date: string; // ISO datetime string
  type: string; // e.g., 'phone', 'zoom', 'in-person'
  status: string; // e.g., 'scheduled', 'done', 'canceled'
  notes: string | null;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface Interview extends InterviewBase {
  id: number;
  // Relationships
  application: Application | null;
}

// Match types
export interface MatchBase {
  application_id: number;
  match_result: object | null; // JSON object with matching algorithm results
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface Match extends MatchBase {
  id: number;
  // Relationships
  application: Application | null;
}

// Common status enums
export enum JobStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  CLOSED = 'closed',
}

export enum JobType {
  FULL_TIME = 'full_time',
  PART_TIME = 'part_time',
  CONTRACT = 'contract',
  INTERNSHIP = 'internship',
}

export enum SeniorityLevel {
  ENTRY = 'entry',
  MID = 'mid',
  SENIOR = 'senior',
}

export enum ExperienceLevel {
  NO_EXPERIENCE = 'no_experience',
  ONE_TO_THREE_YEARS = '1-3_years',
  THREE_TO_FIVE_YEARS = '3-5_years',
  FIVE_TO_SEVEN_YEARS = '5-7_years',
  SEVEN_TO_TEN_YEARS = '7-10_years',
  TEN_PLUS_YEARS = '10_plus_years',
}

export enum InterviewStatus {
  SCHEDULED = 'scheduled',
  DONE = 'done',
  CANCELED = 'canceled',
}

export enum InterviewType {
  PHONE = 'phone',
  ZOOM = 'zoom',
  IN_PERSON = 'in-person',
  VIDEO = 'video',
}

export enum MatchStatus {
  PENDING = 'pending',
  REVIEWED = 'reviewed',
  ACCEPTED = 'accepted',
  REJECTED = 'rejected',
}

export enum HRRole {
  HR_MANAGER = 'hr_manager',
  RECRUITER = 'recruiter',
  ADMIN = 'admin',
}

export enum FormFieldType {
  TEXT = 'text',
  EMAIL = 'email',
  NUMBER = 'number',
  SELECT = 'select',
  TEXTAREA = 'textarea',
  CHECKBOX = 'checkbox',
}

export enum ApplicationStatus {
  PENDING = "pending",
  REVIEWING = "reviewing",
  INTERVIEWING = "interviewing",
  OFFER_SENT = "offer_sent",
  HIRED = "hired",
  REJECTED = "rejected",
}

// API Response types
export interface ApiResponse {
  success: boolean;
  data: any;
  message: string;
  error: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Auth types
export interface LoginRequest {
  username: string; // email
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string; // 'bearer'
}

export interface TokenData {
  sub: string; // subject (user email)
  user_type: string; // 'hr'
  employer_id: number;
  exp: number; // expiration timestamp
}

// Create/Update request types (without id, timestamps, and relationships)
export interface CompanyCreate {
  name: string;
  description?: string | null;
  industry?: string | null;
  bio?: string | null;
  website?: string | null;
  logo_url?: string | null;
  is_owner: boolean;
  domain?: string | null;
}

export interface CompanyUpdate {
  name?: string;
  description?: string | null;
  industry?: string | null;
  bio?: string | null;
  website?: string | null;
  logo_url?: string | null;
  is_owner?: boolean;
  domain?: string | null;
}

export interface HRCreate {
  email: string;
  password: string;
  full_name: string;
  employer_id: number;
  role: string;
}

export interface HRUpdate {
  email?: string;
  password?: string;
  full_name?: string;
  employer_id?: number;
  role?: string;
}

export interface JobCreate {
  employer_id: number;
  recruited_to_id?: number | null;
  job_data: object;
  status: string;
  created_by_hr_id: number;
}

export interface JobUpdate {
  employer_id?: number;
  recruited_to_id?: number | null;
  job_data?: object;
  status?: string;
  created_by_hr_id?: number;
}

export interface CandidateCreate {
  full_name: string;
  email: string;
  phone?: string | null;
  resume_url?: string | null;
  parsed_resume?: object | null;
}

export interface ApplicationCreate {
  candidate_id: number;
  job_id: number;
  form_responses?: object | null;
}

export interface InterviewCreate {
  application_id: number;
  date: string;
  type: string;
  status: string;
  notes?: string | null;
} 