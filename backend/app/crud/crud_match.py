from typing import Any, Dict, Optional, Union, List, Tuple
from copy import deepcopy
import time
from sqlmodel import Session, select

from models.models import (
    Match,
    Application,
    Candidate,
    Job,
)
from models.candidate_pydantic import CandidateResume
from schemas import MatchCreate, MatchUpdate
from services.matching import match_candidates_client


def get_match(db: Session, match_id: int) -> Optional[Match]:
    return db.get(Match, match_id)


def get_matches_by_application(
    db: Session, application_id: int, skip: int = 0, limit: int = 100
) -> List[tuple[Match, Candidate]]:
    statement = (
        select(Match, Candidate)
        .join(Application, Match.application_id == Application.id)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .where(Match.application_id == application_id)
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()


def create_match(db: Session, *, match_in: MatchCreate) -> Match:
    # Fetch application, candidate, and job info
    application = db.get(Application, match_in.application_id)
    if not application:
        raise ValueError(f"Application with id {match_in.application_id} not found")
    candidate = db.get(Candidate, application.candidate_id)
    job = db.get(Job, application.job_id)
    if not candidate or not job:
        raise ValueError("Candidate or Job not found for the application")

    # Prepare structured job and candidate data
    job_data = job.model_dump(mode="json")

    if not candidate.parsed_resume:
        raise ValueError(f"Candidate {candidate.id} has no parsed resume")

    candidate_resume = CandidateResume.model_validate(candidate.parsed_resume)
    candidate_data = candidate_resume.model_dump(mode="json")

    # Call the AI matcher with structured data
    ai_response = match_candidates_client(
        job=job_data,
        candidates=[candidate_data],
    )

    # Extract the first result (since we're matching one candidate)
    if not ai_response or not ai_response.get("results"):
        raise ValueError("No matching results returned from AI service")

    match_result = ai_response["results"][0]  # Get first result

    # Prepare match data with the new structure
    match_data = match_in.model_dump()

    # Main match result fields
    match_data["score"] = match_result.get("score", 0.0)
    match_data["embedding_similarity"] = match_result.get("embedding_similarity", 0.0)
    match_data["score_breakdown"] = match_result.get("score_breakdown", {})

    # Direct skill fields from matcher
    match_data["matching_skills"] = match_result.get("matching_skills", [])
    match_data["missing_skills"] = match_result.get("missing_skills", [])
    match_data["extra_skills"] = match_result.get("extra_skills", [])

    # Weights used in matching
    match_data["weights_used"] = match_result.get("weights_used", {})

    # Calculate legacy fields for backward compatibility
    total_matching = len(match_data["matching_skills"])
    total_missing = len(match_data["missing_skills"])
    total_extra = len(match_data["extra_skills"])
    total_required = total_matching + total_missing

    match_data["matching_skills_count"] = total_matching
    match_data["missing_skills_count"] = total_missing
    match_data["extra_skills_count"] = total_extra
    match_data["total_required_skills"] = total_required
    match_data["match_percentage"] = (total_matching / total_required * 100) if total_required > 0 else 0.0

    # Legacy weights field (copy from weights_used)
    match_data["weights"] = match_data["weights_used"]

    # Remove any existing match for this application
    existing_match = db.exec(
        select(Match).where(Match.application_id == match_in.application_id)
    ).first()
    if existing_match:
        db.delete(existing_match)
        db.flush()

    db_match = Match.model_validate(match_data)
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


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
