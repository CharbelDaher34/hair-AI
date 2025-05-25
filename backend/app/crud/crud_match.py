from typing import Any, Dict, Optional, Union, List, Tuple

from sqlmodel import Session, select

from models.models import Match, Application, Candidate, Job
from schemas import MatchCreate, MatchUpdate
from services.matching import match_candidates_client


def get_match(db: Session, match_id: int) -> Optional[Match]:
    return db.get(Match, match_id)


def get_matches_by_application(db: Session, application_id: int, skip: int = 0, limit: int = 100) -> List[Match]:
    statement = select(Match).where(Match.application_id == application_id).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_match(db: Session, *, match_in: MatchCreate) -> Tuple[Match, Dict]:
    # Fetch application, candidate, and job info
    application = db.get(Application, match_in.application_id)
    if not application:
        raise ValueError(f"Application with id {match_in.application_id} not found")
    candidate = db.get(Candidate, application.candidate_id)
    job = db.get(Job, application.job_id)
    if not candidate or not job:
        raise ValueError("Candidate or Job not found for the application")

    # Prepare texts for AI matching
    job_description = str(job.job_data)
    candidate_text = str(candidate.parsed_resume)
    # Fallback to empty string if not available
    candidates = [candidate_text]

    # Call the AI matcher
    ai_response = match_candidates_client(
        job_description=job_description,
        candidates=candidates
    )
    print("ai_response", ai_response)
    # Store the AI response in match_result
    match_in.match_result = ai_response
    db_match = Match.model_validate(match_in)
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match, ai_response


def update_match(
    db: Session, *, db_match: Match, match_in: Union[MatchUpdate, Dict[str, Any]]
) -> Match:
    if isinstance(match_in, dict):
        update_data = match_in
    else:
        update_data = match_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_match, field, value)
    
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


def delete_match(db: Session, *, match_id: int) -> Optional[Match]:
    db_match = db.get(Match, match_id)
    if db_match:
        db.delete(db_match)
        db.commit()
    return db_match 