from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select

from models.models import Candidate, Application, Job
from schemas import CandidateCreate, CandidateUpdate


def get_candidate(db: Session, candidate_id: int) -> Optional[Candidate]:
    return db.get(Candidate, candidate_id)


def get_candidate_by_email(db: Session, email: str) -> Optional[Candidate]:
    statement = select(Candidate).where(Candidate.email == email)
    return db.exec(statement).first()


def get_candidates(db: Session, skip: int = 0, limit: int = 100) -> List[Candidate]:
    statement = select(Candidate).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_candidate(db: Session, *, candidate_in: CandidateCreate) -> Candidate:
    db_candidate = Candidate.model_validate(candidate_in)
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate


def update_candidate(
    db: Session,
    *,
    db_candidate: Candidate,
    candidate_in: Union[CandidateUpdate, Dict[str, Any]],
) -> Candidate:
    if isinstance(candidate_in, dict):
        update_data = candidate_in
    else:
        update_data = candidate_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_candidate, field, value)

    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate


def delete_candidate(db: Session, *, candidate_id: int) -> Optional[Candidate]:
    db_candidate = db.get(Candidate, candidate_id)
    if db_candidate:
        db.delete(db_candidate)
        db.commit()
    return db_candidate


def get_candidates_by_company(db: Session, *, employer_id: int):
    statement_1 = (
        select(Candidate)
        .join(Application, Application.candidate_id == Candidate.id)
        .join(Job, Job.id == Application.job_id)
        .where(Job.employer_id == employer_id)
    )
    statement_2 = select(Candidate).where(Candidate.employer_id == employer_id)
    candidates_1 = db.exec(statement_1).all()
    candidates_2 = db.exec(statement_2).all()
    unique_candidates = {
        candidate.id: candidate for candidate in candidates_1 + candidates_2
    }
    return list(unique_candidates.values())
