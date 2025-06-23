from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from models.models import JobFormKeyConstraint, FormKey
from schemas import JobFormKeyConstraintCreate, JobFormKeyConstraintUpdate


def get_job_form_key_constraint(
    db: Session, constraint_id: int
) -> Optional[JobFormKeyConstraint]:
    constraint = db.get(JobFormKeyConstraint, constraint_id)
    if constraint:
        # Ensure form_key relationship is loaded
        db.refresh(constraint, ["form_key"])
    return constraint


def get_job_form_key_constraints_by_job(
    db: Session, job_id: int, skip: int = 0, limit: int = 100
) -> List[JobFormKeyConstraint]:
    statement = (
        select(JobFormKeyConstraint)
        .options(selectinload(JobFormKeyConstraint.form_key))
        .where(JobFormKeyConstraint.job_id == job_id)
        .offset(skip)
        .limit(limit)
    )
    constraints = db.exec(statement).all()
    
    # Ensure form_key relationships are loaded
    for constraint in constraints:
        if constraint.form_key_id and not constraint.form_key:
            db.refresh(constraint, ["form_key"])
    
    return constraints


def create_job_form_key_constraint(
    db: Session, *, constraint_in: JobFormKeyConstraintCreate
) -> JobFormKeyConstraint:
    db_constraint = JobFormKeyConstraint.model_validate(constraint_in)
    db.add(db_constraint)
    db.commit()
    db.refresh(db_constraint, ["form_key"])
    return db_constraint


def update_job_form_key_constraint(
    db: Session,
    *,
    db_constraint: JobFormKeyConstraint,
    constraint_in: Union[JobFormKeyConstraintUpdate, Dict[str, Any]],
) -> JobFormKeyConstraint:
    if isinstance(constraint_in, dict):
        update_data = constraint_in
    else:
        update_data = constraint_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_constraint, field, value)

    db.add(db_constraint)
    db.commit()
    db.refresh(db_constraint, ["form_key"])
    return db_constraint


def delete_job_form_key_constraint(
    db: Session, *, constraint_id: int
) -> Optional[JobFormKeyConstraint]:
    db_constraint = db.get(JobFormKeyConstraint, constraint_id)
    if db_constraint:
        # Load the relationship before deletion
        db.refresh(db_constraint, ["form_key"])
        db.delete(db_constraint)
        db.commit()
    return db_constraint
