from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select
    
from models.models import Job
from schemas import JobCreate, JobUpdate

def get_job(db: Session, job_id: int) -> Optional[Job]:
    return db.get(Job, job_id)


def get_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[Job]:
    statement = select(Job).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_jobs_by_employer(db: Session, employer_id: int, skip: int = 0, limit: int = 100) -> List[Job]:
    statement = select(Job).where(Job.employer_id == employer_id).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_jobs_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[Job]:
    statement = select(Job).where(Job.status == status).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_job(db: Session, *, job_in: JobCreate) -> Job:
    db_job = Job.model_validate(job_in)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def update_job(
    db: Session, *, db_job: Job, job_in: Union[JobUpdate, Dict[str, Any]]
) -> Job:
    if isinstance(job_in, dict):
        update_data = job_in
    else:
        update_data = job_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_job, field, value)
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job(db: Session, *, job_id: int) -> Optional[Job]:
    db_job = db.get(Job, job_id)
    if db_job:
        db.delete(db_job)
        db.commit()
    return db_job
