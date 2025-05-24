from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from crud import crud_candidate
from schemas import CandidateCreate, CandidateUpdate, CandidateRead

router = APIRouter()

@router.post("/", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_in: CandidateCreate
) -> CandidateRead:
    try:
        candidate = crud_candidate.create_candidate(db=db, candidate_in=candidate_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return candidate

@router.get("/{candidate_id}", response_model=CandidateRead)
def read_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_id: int
) -> CandidateRead:
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.get("/by-email/{email}", response_model=CandidateRead)
def read_candidate_by_email(
    *,
    db: Session = Depends(get_session),
    email: str
) -> CandidateRead:
    candidate = crud_candidate.get_candidate_by_email(db=db, email=email)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.get("/", response_model=List[CandidateRead])
def read_candidates(
    *,
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
) -> List[CandidateRead]:
    return crud_candidate.get_candidates(db=db, skip=skip, limit=limit)

@router.patch("/{candidate_id}", response_model=CandidateRead)
def update_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_id: int,
    candidate_in: CandidateUpdate
) -> CandidateRead:
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return crud_candidate.update_candidate(db=db, db_candidate=candidate, candidate_in=candidate_in)

@router.delete("/{candidate_id}", response_model=CandidateRead)
def delete_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_id: int
) -> CandidateRead:
    candidate = crud_candidate.delete_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
