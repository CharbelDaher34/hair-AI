from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session

from core.database import get_session
from crud import crud_job
from schemas import JobCreate, JobUpdate, JobRead
from core.security import TokenData

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
    print(f"user: {user}")
    return crud_job.get_jobs(db=db, skip=skip, limit=limit)

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
