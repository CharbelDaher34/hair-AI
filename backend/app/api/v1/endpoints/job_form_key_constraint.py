from typing import List, Optional
from core.security import TokenData
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from core.database import get_session
from crud import crud_job_form_key_constraint
from schemas import JobFormKeyConstraintCreate, JobFormKeyConstraintUpdate, JobFormKeyConstraintRead

router = APIRouter()

@router.post("/", response_model=JobFormKeyConstraintRead, status_code=status.HTTP_201_CREATED)
def create_job_form_key_constraint(
    *,
    db: Session = Depends(get_session),
    constraint_in: JobFormKeyConstraintCreate,
    request: Request
) -> JobFormKeyConstraintRead:
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    try:
        constraint = crud_job_form_key_constraint.create_job_form_key_constraint(db=db, constraint_in=constraint_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return constraint

@router.get("/{constraint_id}", response_model=JobFormKeyConstraintRead)
def read_job_form_key_constraint(
    *,
    db: Session = Depends(get_session),
    constraint_id: int
) -> JobFormKeyConstraintRead:
    constraint = crud_job_form_key_constraint.get_job_form_key_constraint(db=db, constraint_id=constraint_id)
    if not constraint:
        raise HTTPException(status_code=404, detail="JobFormKeyConstraint not found")
    return constraint

@router.get("/by-job/{job_id}", response_model=List[JobFormKeyConstraintRead])
def read_constraints_by_job(
    *,
    db: Session = Depends(get_session),
    job_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[JobFormKeyConstraintRead]:
    return crud_job_form_key_constraint.get_job_form_key_constraints_by_job(db=db, job_id=job_id, skip=skip, limit=limit)

@router.patch("/{constraint_id}", response_model=JobFormKeyConstraintRead)
def update_job_form_key_constraint(
    *,
    db: Session = Depends(get_session),
    constraint_id: int,
    constraint_in: JobFormKeyConstraintUpdate
) -> JobFormKeyConstraintRead:
    constraint = crud_job_form_key_constraint.get_job_form_key_constraint(db=db, constraint_id=constraint_id)
    if not constraint:
        raise HTTPException(status_code=404, detail="JobFormKeyConstraint not found")
    return crud_job_form_key_constraint.update_job_form_key_constraint(db=db, db_constraint=constraint, constraint_in=constraint_in)

@router.delete("/{constraint_id}", response_model=JobFormKeyConstraintRead)
def delete_job_form_key_constraint(
    *,
    db: Session = Depends(get_session),
    constraint_id: int
) -> JobFormKeyConstraintRead:
    constraint = crud_job_form_key_constraint.delete_job_form_key_constraint(db=db, constraint_id=constraint_id)
    if not constraint:
        raise HTTPException(status_code=404, detail="JobFormKeyConstraint not found")
    return constraint 