from typing import List, Optional
from crud import crud_candidate
from schemas.candidate import CandidateRead
from crud import crud_match
from crud import crud_company
from schemas.form_key import FormKeyRead
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from pydantic import BaseModel, Field

from core.database import get_session
from crud import crud_job, crud_form_key
from schemas import JobCreate, JobUpdate, JobRead, CompanyRead, MatchRead
from schemas.job import JobAnalytics, jobGeneratedData
from core.security import TokenData
from models.models import Company, JobType, ExperienceLevel, SeniorityLevel
from services.resume_upload import AgentClient
from sqlalchemy import Column
from sqlalchemy.types import Enum as SQLAlchemyEnum

router = APIRouter()

@router.post("/", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    *,
    db: Session = Depends(get_session),
    job_in: JobCreate,
    request: Request
) -> JobRead:
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Create job data with employer_id and created_by_hr_id from token
    job_in.employer_id = current_user.employer_id
    job_in.created_by_hr_id = current_user.id
    print(f"job_data: {job_in}")
    try:
        job = crud_job.create_job(db=db, job_in=job_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return job

@router.get("/{job_id}", response_model=JobRead)
def read_job(
    *,
    db: Session = Depends(get_session),
    job_id: int,
    request: Request
) -> JobRead:
    user = request.state.user
    job = crud_job.get_job(db=db, job_id=job_id)
    if job.recruited_to_id != user.employer_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this job")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/", response_model=List[JobRead])
def read_jobs(
    *,
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    request: Request
) -> List[JobRead]:
    user = request.state.user
    employer_id = user.employer_id
    return crud_job.get_jobs(db=db, skip=skip, limit=limit, employer_id=employer_id)

@router.get("/by-employer/{employer_id}", response_model=List[JobRead])
def read_jobs_by_employer(
    *,
    db: Session = Depends(get_session),
    employer_id: int,
    skip: int = 0,
    limit: int = 100,
    request: Request
) -> List[JobRead]:
    user = request.state.user
    if employer_id != user.employer_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this job")
    return crud_job.get_jobs_by_employer(db=db, employer_id=employer_id, skip=skip, limit=limit)

@router.get("/by-status/{status}", response_model=List[JobRead])
def read_jobs_by_status(
    *,
    db: Session = Depends(get_session),
    status: str,
    skip: int = 0,
    limit: int = 100
) -> List[JobRead]:
    return crud_job.get_jobs_by_status(db=db, status=status, skip=skip, limit=limit)

@router.patch("/{job_id}", response_model=JobRead)
def update_job(
    *,
    db: Session = Depends(get_session),
    job_id: int,
    job_in: JobUpdate
) -> JobRead:
    job = crud_job.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return crud_job.update_job(db=db, db_job=job, job_in=job_in)

@router.delete("/{job_id}", response_model=JobRead)
def delete_job(
    *,
    db: Session = Depends(get_session),
    job_id: int
) -> JobRead:
    job = crud_job.delete_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

class JobFormData(BaseModel):
    job: JobRead
    form_keys: List[FormKeyRead]
    company: CompanyRead

@router.get("/form-data/{job_id}", response_model=JobFormData)
def get_form_data(
    *,
    db: Session = Depends(get_session),
    job_id: int,
    request: Request
) -> JobFormData:
    """Get job data along with its associated form keys"""
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    job = crud_job.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user has access to this job
    if job.employer_id != current_user.employer_id and job.recruited_to_id != current_user.employer_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this job")
    
    form_keys = crud_form_key.get_form_keys(db=db, job_id=job_id)
    company = crud_company.get_company(db=db, employer_id=job.employer_id)
    return JobFormData(
        job=job,
        form_keys=form_keys,
        company=company
    )

@router.get("/public/form-data/{job_id}", response_model=JobFormData)
def get_public_form_data(
    *,
    db: Session = Depends(get_session),
    job_id: int
) -> JobFormData:
    """Public endpoint to get job data along with its associated form keys for application forms"""
    job = crud_job.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Only allow access to active jobs
    if job.status != "published":
        raise HTTPException(status_code=404, detail="Job not available for applications")
    
    form_keys = crud_form_key.get_form_keys(db=db, job_id=job_id)
    company = crud_company.get_company(db=db, employer_id=job.employer_id)
    return JobFormData(
        job=job,
        form_keys=form_keys,
        company=company
    )

@router.get("/analytics/{job_id}", response_model=JobAnalytics)
def get_job_analytics(
    *,
    db: Session = Depends(get_session),
    job_id: int,
    request: Request
) -> JobAnalytics:
    """Get comprehensive analytics for a specific job"""
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get the job first to check permissions
    job = crud_job.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user has access to this job
    if job.employer_id != current_user.employer_id and job.recruited_to_id != current_user.employer_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this job")
    
    try:
        return crud_job.get_job_analytics(db=db, job_id=job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

class MatchCandidateResponse(MatchRead, CandidateRead):
    pass

class MatchResponseWithDetails(BaseModel):
    matches: List[MatchCandidateResponse]
    job: JobRead

class JobGenerationRequest(BaseModel):
    data: str

@router.get("/matches/{job_id}", response_model=MatchResponseWithDetails)
def get_job_matches(
    *,
    db: Session = Depends(get_session),
    job_id: int,
    request: Request
) -> MatchResponseWithDetails:
    """Get all matches for a specific job"""
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get the job first to check permissions
    job = crud_job.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user has access to this job
    if job.employer_id != current_user.employer_id and job.recruited_to_id != current_user.employer_id:
        raise HTTPException(status_code=403, detail="You are not authorized to access this job")
    
    try:
        match_candidate_pairs = crud_job.get_job_matches(db=db, job_id=job_id)
        
        matches_with_candidates = []
        for match, candidate in match_candidate_pairs:
            # Combine match and candidate data into a single object
            combined_data = {
                **match.model_dump(),
                **candidate.model_dump()
            }
            matches_with_candidates.append(MatchCandidateResponse(**combined_data))
        
        return MatchResponseWithDetails(
            matches=matches_with_candidates,
            job=job
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving matches: {str(e)}")
  
  
  
@router.post("/generate_description", response_model=jobGeneratedData)
def generate_description(
    *,
    db: Session = Depends(get_session),
    request_data: JobGenerationRequest,
    request: Request
) -> jobGeneratedData:
    """Generate a description for a job"""
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    employer_id = current_user.employer_id
    company_data = crud_company.get_company_data(db, employer_id)
    if not company_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
        
    input = f'''
    Company data: {company_data}
    Job data: {request_data.data}
    '''
    client = AgentClient(
        system_prompt="""You are an expert in writing and creating job descriptions for companies. You are given company data and job requirements as input text. Generate comprehensive job data based on this information.

IMPORTANT: You must provide ALL fields in the exact JSON structure specified. Do not leave any field empty or null.

Required JSON structure:
{
  "title": "string - Job title",
  "description": "string - Detailed job description",
  "compensation": {
    "base_salary": integer - Annual salary in USD (e.g., 75000),
    "benefits": ["string", "string"] - Array of benefit strings (e.g., ["Health Insurance", "401k Matching", "Remote Work"])
  },
  "job_type": "full_time|part_time|contract|internship",
  "experience_level": "no_experience|1-3_years|3-5_years|5-7_years|7-10_years|10_plus_years",
  "seniority_level": "entry|mid|senior",
  "responsibilities": ["string", "string"] - Array of responsibility strings,
  "skills": {
    "hard_skills": ["string", "string"] - Array of technical skills,
    "soft_skills": ["string", "string"] - Array of soft skills
  },
  "location": "string - Job location",
  "job_category": "string - Job category (e.g., Software Engineering, Marketing, etc.)"
}

Generate realistic and appropriate values for all fields. If specific information is not provided, infer reasonable values based on the job context and company information.""",
        schema=jobGeneratedData.model_json_schema(),
        inputs=[input]
    )
    return client.parse()


