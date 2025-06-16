from typing import List, Optional
from crud import crud_candidate
from schemas.candidate import CandidateRead
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session

from core.database import get_session
from crud import crud_company
from schemas import CompanyCreate, CompanyUpdate, CompanyRead
from core.security import TokenData

router = APIRouter()


@router.post("/", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    *, db: Session = Depends(get_session), company_in: CompanyCreate
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


@router.get("/recruit_to", response_model=List[CompanyRead])
def read_recruit_to_companies(
    *, db: Session = Depends(get_session), request: Request
) -> List[CompanyRead]:
    """
    Get all companies that the current user can recruit to.
    """
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    employer_id = current_user.employer_id
    print(f"employer_id: {employer_id}")
    companies = crud_company.get_recruit_to_companies(db=db, employer_id=employer_id)
    return companies


@router.get("/{employer_id}", response_model=CompanyRead)
def read_company(
    *, db: Session = Depends(get_session), employer_id: int
) -> CompanyRead:
    """
    Get a specific company by ID.
    """
    company = crud_company.get_company(db=db, employer_id=employer_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return company


@router.get("/", response_model=List[CompanyRead])
def read_companies(
    *, db: Session = Depends(get_session), skip: int = 0, limit: int = 100
) -> List[CompanyRead]:
    """
    Get all companies with pagination.
    """
    companies = crud_company.get_companies(db=db, skip=skip, limit=limit)
    return companies


@router.get("/by-name/{name}", response_model=CompanyRead)
def read_company_by_name(
    *, db: Session = Depends(get_session), name: str
) -> CompanyRead:
    """
    Get a specific company by name.
    """
    company = crud_company.get_company_by_name(db=db, name=name)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return company


@router.patch("/{employer_id}", response_model=CompanyRead)
def update_company(
    *, db: Session = Depends(get_session), employer_id: int, company_in: CompanyUpdate
) -> CompanyRead:
    """
    Update a company.
    """
    company = crud_company.get_company(db=db, employer_id=employer_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    company = crud_company.update_company(
        db=db, db_company=company, company_in=company_in
    )
    return company


@router.delete("/{employer_id}", response_model=CompanyRead)
def delete_company(
    *, db: Session = Depends(get_session), employer_id: int
) -> CompanyRead:
    """
    Delete a company.
    """
    company = crud_company.delete_company(db=db, employer_id=employer_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return company


@router.get("/by_hr/", response_model=CompanyRead)
def get_current_company(
    *, db: Session = Depends(get_session), request: Request
) -> CompanyRead:
    """
    Get the current company.
    """
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    company = crud_company.get_company(db=db, employer_id=current_user.employer_id)
    return company


@router.get("/candidates/", response_model=List[CandidateRead])
def get_candidates_by_company(
    *, db: Session = Depends(get_session), request: Request
) -> List[CandidateRead]:
    """
    Get all candidates for the current company.
    """
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    candidates = crud_candidate.get_candidates_by_company(
        db=db, employer_id=current_user.employer_id
    )
    return candidates


@router.get("/{employer_id}/candidates", response_model=List[CandidateRead])
def get_candidates_by_company_id(
    *, 
    db: Session = Depends(get_session), 
    employer_id: int,
    request: Request
) -> List[CandidateRead]:
    """
    Get all candidates for a specific company.
    """
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    # Check if user has permission to access this company's candidates
    if current_user.employer_id != employer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this company's candidates",
        )
    
    # Check if company exists
    company = crud_company.get_company(db=db, employer_id=employer_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    
    candidates = crud_candidate.get_candidates_by_company(
        db=db, employer_id=employer_id
    )
    return candidates
