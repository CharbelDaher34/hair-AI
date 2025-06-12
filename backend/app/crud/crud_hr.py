from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select

from models.models import HR
from schemas import HRCreate, HRUpdate
from core.security import get_password_hash


def get_hr(db: Session, hr_id: int) -> Optional[HR]:
    return db.get(HR, hr_id)


def get_hr_by_email(db: Session, email: str) -> Optional[HR]:
    statement = select(HR).where(HR.email == email)
    return db.exec(statement).first()


def get_hrs(db: Session, skip: int = 0, limit: int = 100) -> List[HR]:
    statement = select(HR).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_hrs_by_company(
    db: Session, employer_id: int, skip: int = 0, limit: int = 100
) -> List[HR]:
    statement = (
        select(HR).where(HR.employer_id == employer_id).offset(skip).limit(limit)
    )
    return db.exec(statement).all()


def create_hr(db: Session, *, hr_in: HRCreate) -> HR:
    # Here you might want to add password hashing before saving
    # For now, assuming password_hash is already hashed
    db_hr = HR.model_validate(hr_in)
    db_hr.password = get_password_hash(hr_in.password)
    db.add(db_hr)
    db.commit()
    db.refresh(db_hr)
    return db_hr


def update_hr(db: Session, *, db_hr: HR, hr_in: Union[HRUpdate, Dict[str, Any]]) -> HR:
    if isinstance(hr_in, dict):
        update_data = hr_in
    else:
        update_data = hr_in.model_dump(exclude_unset=True)

    # If password is being updated, it should be hashed
    # Example:
    # if "password_hash" in update_data and update_data["password_hash"]:
    #     hashed_password = hash_password(update_data["password_hash"])
    #     update_data["password_hash"] = hashed_password

    for field, value in update_data.items():
        setattr(db_hr, field, value)

    db.add(db_hr)
    db.commit()
    db.refresh(db_hr)
    return db_hr


def delete_hr(db: Session, *, hr_id: int) -> Optional[HR]:
    db_hr = db.get(HR, hr_id)
    if db_hr:
        db.delete(db_hr)
        db.commit()
    return db_hr
