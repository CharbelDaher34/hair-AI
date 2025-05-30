from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select

from models.models import Company, RecruiterCompanyLink
from schemas import CompanyCreate, CompanyUpdate, CompanyRead


def get_company(db: Session, employer_id: int) -> Optional[Company]:
    return db.get(Company, employer_id)


def get_company_by_name(db: Session, name: str) -> Optional[Company]:
    statement = select(Company).where(Company.name == name)
    return db.exec(statement).first()


def get_companies(db: Session, skip: int = 0, limit: int = 100) -> List[Company]:
    statement = select(Company).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_company(db: Session, *, company_in: CompanyCreate) -> Company:
    db_company = Company.model_validate(company_in)
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


def update_company(
    db: Session, *, db_company: Company, company_in: Union[CompanyUpdate, Dict[str, Any]]
) -> Company:
    if isinstance(company_in, dict):
        update_data = company_in
    else:
        update_data = company_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


def delete_company(db: Session, *, employer_id: int) -> Optional[Company]:
    db_company = db.get(Company, employer_id)
    if db_company:
        db.delete(db_company)
        db.commit()
    return db_company


def get_recruit_to_companies(db: Session, employer_id: int) -> List[CompanyRead]:
    """Get all companies that are recruited to by a given employer_id (recruiter_id)"""
    print(f"recruited_to_id: {employer_id}")
    statement = select(RecruiterCompanyLink).where(
        RecruiterCompanyLink.recruiter_id == employer_id
    )
    
    recruited_to_links = db.exec(statement).all()
    target_employer_ids = [link.target_employer_id for link in recruited_to_links]
    statement = select(Company).where(Company.id.in_(target_employer_ids))
    companies = db.exec(statement).all()
    
    current_company = get_company(db, employer_id)
    if current_company:
        companies.append(current_company)
    
    return [CompanyRead.model_validate(company) for company in companies]
  

  

