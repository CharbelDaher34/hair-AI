from typing import Optional, List, Dict
from sqlmodel import SQLModel, Field, Column
from models.models import JobBase, Job, JobType, ExperienceLevel, SeniorityLevel, compensation_base, skills_base
from utils.pydantic_utils import make_optional
from sqlalchemy import Enum as SQLAlchemyEnum

@make_optional
class JobCreate(JobBase):
    pass
    # employer_id and created_by_hr_id are set from token on backend


@make_optional
class JobUpdate(JobBase):
    id: int

class JobRead(JobBase):
    id: int


class JobAnalytics(SQLModel):
    job_id: int
    job_title: str
    job_status: str
    
    # Application metrics
    total_applications: int
    applications_by_status: Dict[str, int]
    
    # Matching metrics
    total_matches: int
    matches_by_status: Dict[str, int]
    average_match_score: Optional[float]
    top_match_score: Optional[float]
    
    # Interview metrics
    total_interviews: int
    interviews_by_type: Dict[str, int]
    interviews_by_status: Dict[str, int]
    
    # Candidate metrics
    unique_candidates: int
    candidates_with_parsed_resumes: int
    top_skills_from_candidates: List[str]
    
    # Time-based metrics
    applications_last_7_days: int
    applications_last_30_days: int
    
    # Conversion metrics
    application_to_match_rate: float
    application_to_interview_rate: float
    match_to_interview_rate: float
    
# class JobAnalyticsWithDetails(JobAnalytics):
#     job: JobRead
#     applications: List[ApplicationRead]
#     matches: List[MatchRead]
#     interviews: List[InterviewRead]
#     candidates: List[CandidateRead]
    
class jobGeneratedData(SQLModel):
    title: str
    description: str
    compensation: compensation_base = Field(default=None,description="The compensation for the job, example: {'base_salary': 100000, 'benefits': ['Health Insurance', '401(k) Matching', 'Remote Work']}")
    job_type: JobType = Field(default=JobType.FULL_TIME,sa_column=Column(SQLAlchemyEnum(JobType, name="jobtype_enum", create_type=True)))    
    experience_level: ExperienceLevel = Field(default=ExperienceLevel.NO_EXPERIENCE,sa_column=Column(SQLAlchemyEnum(ExperienceLevel, name="experiencelevel_enum", create_type=True)))
    seniority_level: SeniorityLevel = Field(default=SeniorityLevel.ENTRY,sa_column=Column(SQLAlchemyEnum(SeniorityLevel, name="senioritylevel_enum", create_type=True)))
    responsibilities: List[str] = Field(default=None,description="The responsibilities of the job, example: ['Develop and maintain API endpoints', 'Write clean, maintainable code', 'Collaborate with cross-functional teams', 'Participate in code reviews']")
    skills: skills_base = Field(default=None,description="The soft and hard skills required for the job, example: {'hard_skills': ['Python', 'SQL', 'AWS'], 'soft_skills': ['Communication', 'Problem Solving', 'Teamwork']}")
    location: Optional[str] = Field(default=None)
    job_category: Optional[str] = Field(default=None,description="The category of the job, example: 'Software Engineering', 'Data Science', 'Product Management', 'Marketing', 'Sales', 'Finance', 'HR', 'Legal', 'Customer Support', 'Design', 'Other'")
    

    