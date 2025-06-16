from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select

from models.models import Candidate, Application, Job, Company, CandidateEmployerLink
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
    # Check if candidate already exists by email
    existing_candidate = get_candidate_by_email(db, candidate_in.email)
    if existing_candidate:
        return existing_candidate

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
    """Get candidates associated with a company through applications or direct association"""
    # Get candidates through applications
    statement_1 = (
        select(Candidate)
        .join(Application, Application.candidate_id == Candidate.id)
        .join(Job, Job.id == Application.job_id)
        .where(Job.employer_id == employer_id)
    )
    
    # Get candidates through direct many-to-many association
    statement_2 = (
        select(Candidate)
        .join(CandidateEmployerLink, CandidateEmployerLink.candidate_id == Candidate.id)
        .where(CandidateEmployerLink.employer_id == employer_id)
    )
    
    candidates_1 = db.exec(statement_1).all()
    candidates_2 = db.exec(statement_2).all()
    unique_candidates = {
        candidate.id: candidate for candidate in candidates_1 + candidates_2
    }
    return list(unique_candidates.values())


def add_candidate_to_employer(db: Session, *, candidate_id: int, employer_id: int) -> bool:
    """Add a candidate to an employer's candidate pool"""
    # Check if relationship already exists
    existing_link = db.exec(
        select(CandidateEmployerLink).where(
            CandidateEmployerLink.candidate_id == candidate_id,
            CandidateEmployerLink.employer_id == employer_id
        )
    ).first()
    
    if existing_link:
        return False  # Relationship already exists
    
    # Create new relationship
    link = CandidateEmployerLink(candidate_id=candidate_id, employer_id=employer_id)
    db.add(link)
    db.commit()
    return True


def remove_candidate_from_employer(db: Session, *, candidate_id: int, employer_id: int) -> bool:
    """Remove a candidate from an employer's candidate pool"""
    link = db.exec(
        select(CandidateEmployerLink).where(
            CandidateEmployerLink.candidate_id == candidate_id,
            CandidateEmployerLink.employer_id == employer_id
        )
    ).first()
    
    if link:
        db.delete(link)
        db.commit()
        return True
    return False


def get_candidate_employers(db: Session, *, candidate_id: int) -> List[Company]:
    """Get all employers associated with a candidate"""
    statement = (
        select(Company)
        .join(CandidateEmployerLink, CandidateEmployerLink.employer_id == Company.id)
        .where(CandidateEmployerLink.candidate_id == candidate_id)
    )
    return db.exec(statement).all()
