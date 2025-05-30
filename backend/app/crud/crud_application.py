from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select, func

from models.models import Application, Match, Job, Candidate
from schemas import ApplicationCreate, ApplicationUpdate
from .crud_job import get_job


def get_application(db: Session, application_id: int) -> Optional[Application]:
    return db.get(Application, application_id)


def get_applications_by_job(db: Session, job_id: int, skip: int = 0, limit: int = 100) -> List[Application]:
    statement = select(Application).where(Application.job_id == job_id).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_applications_by_candidate(db: Session, candidate_id: int, skip: int = 0, limit: int = 100) -> List[Application]:
    statement = select(Application).where(Application.candidate_id == candidate_id).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_random_applications_by_employer(db: Session, employer_id: int, skip: int = 0, limit: int = 100) -> List[Application]:
    """Get random applications for jobs belonging to an employer with pagination"""
    statement = (
        select(Application)
        .join(Job, Application.job_id == Job.id)
        .where(Job.employer_id == employer_id)
        .order_by(func.random())
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()


def get_application_with_details(db: Session, application_id: int) -> Optional[Application]:
    """Get application with candidate and job details"""
    statement = (
        select(Application)
        .where(Application.id == application_id)
    )
    application = db.exec(statement).first()
    if application:
        # Load relationships
        db.refresh(application, ["candidate", "job"])
    return application


def create_application(db: Session, *, application_in: ApplicationCreate) -> Application:
    db_application = Application.model_validate(application_in)
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


def update_application(
    db: Session, *, db_application: Application, application_in: Union[ApplicationUpdate, Dict[str, Any]]
) -> Application:
    if isinstance(application_in, dict):
        update_data = application_in
    else:
        update_data = application_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_application, field, value)
    
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


def delete_application(db: Session, *, application_id: int) -> Optional[Application]:
    db_application = db.get(Application, application_id)
    match=db.get(Match,db_application.id)
    if match:
        db.delete(match)
    if db_application:
        db.delete(db_application)
        db.commit()
    return db_application