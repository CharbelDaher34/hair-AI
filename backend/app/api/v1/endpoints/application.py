from typing import List
from pydantic import BaseModel
from schemas.candidate import CandidateRead
from schemas.job import JobRead
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session
import traceback
from core.database import get_session
from crud import crud_application, crud_job
from schemas import ApplicationCreate, ApplicationUpdate, ApplicationRead, ApplicationWithDetails

# Import for matching
from crud import crud_match
from models.models import Candidate, Job
from services.matching import match_candidates_client

router = APIRouter()

@router.post("/", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    *,
    db: Session = Depends(get_session),
    application_in: ApplicationCreate
) -> ApplicationRead:
    application = crud_application.create_application(db=db, application_in=application_in)
   
    return application

class ApplicationDashboardResponse(BaseModel):
    applications: List[ApplicationWithDetails]
    total: int

@router.get("/employer-applications", response_model=ApplicationDashboardResponse)
def get_employer_applications(
    *,
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    request: Request
) -> ApplicationDashboardResponse:
    """Get random applications for the current employer with pagination"""
    current_user = request.state.user
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    employer_id = current_user.employer_id
    if not employer_id:
        raise HTTPException(status_code=400, detail="User is not associated with an employer")
    
    # Get random applications for this employer
    applications = crud_application.get_random_applications_by_employer(
        db=db, 
        employer_id=employer_id, 
        skip=skip, 
        limit=limit
    )
    
    # Convert to ApplicationWithDetails format
    applications_with_details = []
    for app in applications:
        # Load relationships if not already loaded
        if not app.candidate:
            db.refresh(app, ["candidate"])
        if not app.job:
            db.refresh(app, ["job"])
            
        app_detail = ApplicationWithDetails(
            id=app.id,
            candidate_id=app.candidate_id,
            job_id=app.job_id,
            form_responses=app.form_responses,
            candidate=app.candidate,
            job=app.job
        )
        applications_with_details.append(app_detail)
    
    # For now, we'll return the count of applications returned
    # In a real scenario, you might want to get the total count separately
    total = len(applications_with_details)
    
    return ApplicationDashboardResponse(
        applications=applications_with_details,
        total=total
    )

@router.get("/{application_id}", response_model=ApplicationRead)
def read_application(
    *,
    db: Session = Depends(get_session),
    application_id: int
) -> ApplicationRead:
    application = crud_application.get_application(db=db, application_id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.get("/by-job/{job_id}", response_model=List[ApplicationRead])
def read_applications_by_job(
    *,
    db: Session = Depends(get_session),
    job_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ApplicationRead]:
    return crud_application.get_applications_by_job(db=db, job_id=job_id, skip=skip, limit=limit)

@router.get("/by-candidate/{candidate_id}", response_model=List[ApplicationRead])
def read_applications_by_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ApplicationRead]:
    return crud_application.get_applications_by_candidate(db=db, candidate_id=candidate_id, skip=skip, limit=limit)

@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    *,
    db: Session = Depends(get_session),
    application_id: int,
    application_in: ApplicationUpdate
) -> ApplicationRead:
    db_application = crud_application.get_application(db=db, application_id=application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    updated_application = crud_application.update_application(
        db=db, db_application=db_application, application_in=application_in
    )
    return updated_application

@router.delete("/{application_id}", response_model=ApplicationRead)
def delete_application(
    *,
    db: Session = Depends(get_session),
    application_id: int
) -> ApplicationRead:
    application = crud_application.delete_application(db=db, application_id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application