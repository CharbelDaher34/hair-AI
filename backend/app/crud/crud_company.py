from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select

from models.models import Company
from schemas import CompanyCreate, CompanyUpdate


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
