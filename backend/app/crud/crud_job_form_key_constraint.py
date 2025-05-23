from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select

from models.models import JobFormKeyConstraint
from schemas import JobFormKeyConstraintCreate, JobFormKeyConstraintUpdate


def get_job_form_key_constraint(db: Session, constraint_id: int) -> Optional[JobFormKeyConstraint]:
    return db.get(JobFormKeyConstraint, constraint_id)


def get_job_form_key_constraints_by_job(db: Session, job_id: int, skip: int = 0, limit: int = 100) -> List[JobFormKeyConstraint]:
    statement = select(JobFormKeyConstraint).where(JobFormKeyConstraint.job_id == job_id).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_job_form_key_constraint(db: Session, *, constraint_in: JobFormKeyConstraintCreate) -> JobFormKeyConstraint:
    db_constraint = JobFormKeyConstraint.model_validate(constraint_in)
    db.add(db_constraint)
    db.commit()
    db.refresh(db_constraint)
    return db_constraint


def update_job_form_key_constraint(
    db: Session, *, db_constraint: JobFormKeyConstraint, constraint_in: Union[JobFormKeyConstraintUpdate, Dict[str, Any]]
) -> JobFormKeyConstraint:
    if isinstance(constraint_in, dict):
        update_data = constraint_in
    else:
        update_data = constraint_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_constraint, field, value)
    
    db.add(db_constraint)
    db.commit()
    db.refresh(db_constraint)
    return db_constraint


def delete_job_form_key_constraint(db: Session, *, constraint_id: int) -> Optional[JobFormKeyConstraint]:
    db_constraint = db.get(JobFormKeyConstraint, constraint_id)
    if db_constraint:
        db.delete(db_constraint)
        db.commit()
    return db_constraint 