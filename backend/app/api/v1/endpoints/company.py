from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from crud import crud_company
from schemas import CompanyCreate, CompanyUpdate, CompanyRead

router = APIRouter()

@router.post("/", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    *,
    db: Session = Depends(get_session),
    company_in: CompanyCreate
) -> CompanyRead:
    """
    Create a new company.
    """
    try:
        print(f"Creating company: {company_in}")
        company = crud_company.create_company(db=db, company_in=company_in)
    except Exception as e:
        print(f"Error creating company: {e}")
        raise e
    return company

@router.get("/{company_id}", response_model=CompanyRead)
def read_company(
    *,
    db: Session = Depends(get_session),
    company_id: int
) -> CompanyRead:
    """
    Get a specific company by ID.
    """
    company = crud_company.get_company(db=db, company_id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company

@router.get("/", response_model=List[CompanyRead])
def read_companies(
    *,
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
) -> List[CompanyRead]:
    """
    Get all companies with pagination.
    """
    companies = crud_company.get_companies(db=db, skip=skip, limit=limit)
    return companies

@router.get("/by-name/{name}", response_model=CompanyRead)
def read_company_by_name(
    *,
    db: Session = Depends(get_session),
    name: str
) -> CompanyRead:
    """
    Get a specific company by name.
    """
    company = crud_company.get_company_by_name(db=db, name=name)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company

@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    *,
    db: Session = Depends(get_session),
    company_id: int,
    company_in: CompanyUpdate
) -> CompanyRead:
    """
    Update a company.
    """
    company = crud_company.get_company(db=db, company_id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    company = crud_company.update_company(db=db, db_company=company, company_in=company_in)
    return company

@router.delete("/{company_id}", response_model=CompanyRead)
def delete_company(
    *,
    db: Session = Depends(get_session),
    company_id: int
) -> CompanyRead:
    """
    Delete a company.
    """
    company = crud_company.delete_company(db=db, company_id=company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company
