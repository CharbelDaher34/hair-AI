from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select

from models.models import FormKey, JobFormKeyConstraint
from schemas import FormKeyCreate, FormKeyUpdate


def get_form_key(db: Session, form_key_id: int) -> Optional[FormKey]:
    return db.get(FormKey, form_key_id)


def get_form_keys_by_company(
    db: Session, employer_id: int, skip: int = 0, limit: int = 100
) -> List[FormKey]:
    statement = (
        select(FormKey)
        .where(FormKey.employer_id == employer_id)
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()


def create_form_key(db: Session, *, form_key_in: FormKeyCreate) -> FormKey:
    db_form_key = FormKey.model_validate(form_key_in)
    db.add(db_form_key)
    db.commit()
    db.refresh(db_form_key)
    return db_form_key


def update_form_key(
    db: Session,
    *,
    db_form_key: FormKey,
    form_key_in: Union[FormKeyUpdate, Dict[str, Any]],
) -> FormKey:
    if isinstance(form_key_in, dict):
        update_data = form_key_in
    else:
        update_data = form_key_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_form_key, field, value)

    db.add(db_form_key)
    db.commit()
    db.refresh(db_form_key)
    return db_form_key


def delete_form_key(db: Session, *, form_key_id: int) -> Optional[FormKey]:
    db_form_key = db.get(FormKey, form_key_id)
    if db_form_key:
        db.query(JobFormKeyConstraint).filter(
            JobFormKeyConstraint.form_key_id == form_key_id
        ).delete()
        db.delete(db_form_key)
        db.commit()
    return db_form_key


def get_form_keys(db: Session, job_id: int) -> List[FormKey]:
    """Get all form keys associated with a specific job through JobFormKeyConstraint"""
    statement = (
        select(FormKey)
        .join(JobFormKeyConstraint, FormKey.id == JobFormKeyConstraint.form_key_id)
        .where(JobFormKeyConstraint.job_id == job_id)
    )
    return db.exec(statement).all()


def get_form_keys_with_constraints(
    db: Session, job_id: int
) -> List[tuple[FormKey, JobFormKeyConstraint]]:
    """Get all form keys with their constraints for a specific job"""
    statement = (
        select(FormKey, JobFormKeyConstraint)
        .join(JobFormKeyConstraint, FormKey.id == JobFormKeyConstraint.form_key_id)
        .where(JobFormKeyConstraint.job_id == job_id)
    )
    return db.exec(statement).all()
