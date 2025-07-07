from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session

from core.database import get_session
from crud import crud_hr
from schemas.hr import HRCreate, HRUpdate, HRRead
from core.security import TokenData  # For type hinting
import logging
from core.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=HRRead, status_code=status.HTTP_201_CREATED)
def create_hr(
    *, db: Session = Depends(get_session), hr_in: HRCreate, request: Request
) -> HRRead:
    """
    Create a new HR user/employee.
    """
    current_user = get_current_user(request)

    # Check if email already exists
    if crud_hr.get_hr_by_email(db=db, email=hr_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Set the employer_id from the current user's token
    hr_in.employer_id = current_user.employer_id

    hr = crud_hr.create_hr(db=db, hr_in=hr_in)
    return hr


@router.get("/", response_model=HRRead)
def read_hr(*, db: Session = Depends(get_session), request: Request) -> HRRead:
    """
    Get a specific HR user by ID.
    """
    current_user = get_current_user(request)
    logger.debug(f"Current user: {current_user}")
    hr_id = current_user.id
    hr = crud_hr.get_hr(db=db, hr_id=hr_id)
    if not hr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HR user not found"
        )
    return hr


@router.get("/all", response_model=List[HRRead])
def read_hrs(
    *, db: Session = Depends(get_session), skip: int = 0, limit: int = 100
) -> List[HRRead]:
    """
    Get all HR users with pagination.
    """
    hrs = crud_hr.get_hrs(db=db, skip=skip, limit=limit)
    return hrs


@router.get("/by-email/{email}", response_model=HRRead)
def read_hr_by_email(*, db: Session = Depends(get_session), email: str) -> HRRead:
    """
    Get a specific HR user by email.
    """
    hr = crud_hr.get_hr_by_email(db=db, email=email)
    if not hr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HR user not found"
        )
    return hr


@router.get("/by-company/{employer_id}", response_model=List[HRRead])
def read_hrs_by_company(
    *,
    db: Session = Depends(get_session),
    employer_id: int,
    skip: int = 0,
    limit: int = 100,
) -> List[HRRead]:
    """
    Get all HR users for a specific company with pagination.
    """
    hrs = crud_hr.get_hrs_by_company(
        db=db, employer_id=employer_id, skip=skip, limit=limit
    )
    return hrs


@router.get("/employees", response_model=List[HRRead])
def read_company_employees(
    *,
    db: Session = Depends(get_session),
    request: Request,
    skip: int = 0,
    limit: int = 100,
) -> List[HRRead]:
    """
    Get all employees for the current user's company.
    """
    current_user = get_current_user(request)
    hrs = crud_hr.get_hrs_by_company(
        db=db, employer_id=current_user.employer_id, skip=skip, limit=limit
    )
    return hrs


@router.patch("/{hr_id}", response_model=HRRead)
def update_hr(
    *, db: Session = Depends(get_session), hr_id: int, hr_in: HRUpdate
) -> HRRead:
    """
    Update an HR user.
    """
    hr = crud_hr.get_hr(db=db, hr_id=hr_id)
    if not hr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HR user not found"
        )

    # If email is being updated, check if new email already exists
    if hr_in.email and hr_in.email != hr.email:
        if crud_hr.get_hr_by_email(db=db, email=hr_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    hr = crud_hr.update_hr(db=db, db_hr=hr, hr_in=hr_in)
    return hr


@router.delete("/{hr_id}", response_model=HRRead)
def delete_hr(*, db: Session = Depends(get_session), hr_id: int) -> HRRead:
    """
    Delete an HR user.
    """
    hr = crud_hr.delete_hr(db=db, hr_id=hr_id)
    if not hr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="HR user not found"
        )
    return hr
