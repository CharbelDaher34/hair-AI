from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select

from models.models import RecruiterCompanyLink
from schemas import RecruiterCompanyLinkCreate, RecruiterCompanyLinkUpdate


def get_recruiter_company_link(db: Session, link_id: int) -> Optional[RecruiterCompanyLink]:
    return db.get(RecruiterCompanyLink, link_id)


def get_recruiter_company_links_by_recruiter(db: Session, recruiter_id: int, skip: int = 0, limit: int = 100) -> List[RecruiterCompanyLink]:
    statement = select(RecruiterCompanyLink).where(RecruiterCompanyLink.recruiter_id == recruiter_id).offset(skip).limit(limit)
    return db.exec(statement).all()


def get_recruiter_company_links_by_target_company(db: Session, target_company_id: int, skip: int = 0, limit: int = 100) -> List[RecruiterCompanyLink]:
    statement = select(RecruiterCompanyLink).where(RecruiterCompanyLink.target_company_id == target_company_id).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_recruiter_company_link(db: Session, *, link_in: RecruiterCompanyLinkCreate) -> RecruiterCompanyLink:
    db_link = RecruiterCompanyLink.model_validate(link_in)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link


def update_recruiter_company_link(
    db: Session, *, db_link: RecruiterCompanyLink, link_in: Union[RecruiterCompanyLinkUpdate, Dict[str, Any]]
) -> RecruiterCompanyLink:
    if isinstance(link_in, dict):
        update_data = link_in
    else:
        update_data = link_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_link, field, value)
    
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link


def delete_recruiter_company_link(db: Session, *, link_id: int) -> Optional[RecruiterCompanyLink]:
    db_link = db.get(RecruiterCompanyLink, link_id)
    if db_link:
        db.delete(db_link)
        db.commit()
    return db_link 