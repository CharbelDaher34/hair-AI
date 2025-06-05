from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload

from models.models import Application, Match, Job, Candidate, FormKey, JobFormKeyConstraint
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
    """Get applications for jobs belonging to an employer with pagination, ordered by most recent"""
    statement = (
        select(Application)
        .join(Job, Application.job_id == Job.id)
        .where(Job.employer_id == employer_id)
        .order_by(Application.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = db.exec(statement).all()
    print(f"[get_random_applications_by_employer] skip={skip}, limit={limit}, returned_ids={[app.id for app in result]}")
    return result


def get_application_with_details(db: Session, application_id: int) -> Optional[Application]:
    """Get application with candidate, job details, and transformed form_responses."""
    statement = (
        select(Application)
        .where(Application.id == application_id)
        .options(
            selectinload(Application.candidate),
            selectinload(Application.job).selectinload(Job.form_key_constraints).selectinload(JobFormKeyConstraint.form_key)
        )
    )
    application = db.exec(statement).first()

    if application:
        # Transform form_responses from Dict to List[FormResponseItem]
        if application.form_responses and isinstance(application.form_responses, dict) and application.job:
            transformed_responses = []
            
            # Create a mapping of form_key_id to FormKey.name
            form_key_mapping = {}
            if application.job.form_key_constraints:
                for constraint in application.job.form_key_constraints:
                    if constraint.form_key:
                        # Map both the form_key.id and form_key.name as potential keys
                        form_key_mapping[str(constraint.form_key.id)] = constraint.form_key.name
                        form_key_mapping[constraint.form_key.name] = constraint.form_key.name
            
            # Transform the form_responses using the actual FormKey names
            for key, value in application.form_responses.items():
                form_key_name = form_key_mapping.get(key, key)  # Fallback to original key if not found
                transformed_responses.append({"name": form_key_name, "value": value})
            
            application.form_responses = transformed_responses
        elif not application.form_responses:
            # Ensure it's an empty list if None or already empty, to match the new schema type
            application.form_responses = []

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


def get_applications_count_by_employer(db: Session, employer_id: int) -> int:
    job_ids_subquery = select(Job.id).where(Job.employer_id == employer_id)
    statement = select(func.count(Application.id)).where(Application.job_id.in_(job_ids_subquery))
    result = db.exec(statement)
    total = result.one()
    print(f"Total applications: {total}")
    if isinstance(total, tuple):
        total = total[0]
    return total