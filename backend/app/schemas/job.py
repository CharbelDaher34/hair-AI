from typing import Optional, List, Dict
from sqlmodel import SQLModel
from models.models import JobBase, Job
from utils.pydantic_utils import make_optional

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
    
