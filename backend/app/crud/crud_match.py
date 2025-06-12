from typing import Any, Dict, Optional, Union, List, Tuple
from copy import deepcopy
import time
from sqlmodel import Session, select

from models.models import Match, Application, Candidate, Job
from models.candidate_pydantic import CandidateResume
from schemas import MatchCreate, MatchUpdate
from services.matching import match_candidates_client
from utils.pydantic_utils import render_model


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
    print("match_in to create match", match_in)
    application = db.get(Application, match_in.application_id)
    if not application:
        raise ValueError(f"Application with id {match_in.application_id} not found")
    candidate = db.get(Candidate, application.candidate_id)
    job = db.get(Job, application.job_id)
    if not candidate or not job:
        raise ValueError("Candidate or Job not found for the application")

    # Format comprehensive job description
    job_description_parts = [
        f"Job Title: {job.title}",
        f"Description: {job.description}",
        f"Job Type: {job.job_type.value}",
        f"Seniority Level: {job.seniority_level.value}",
        f"Experience Level: {job.experience_level.value}",
    ]

    if job.job_category:
        job_description_parts.append(f"Category: {job.job_category}")

    job_description = "\n".join(job_description_parts)

    candidate_text = render_model(candidate.parsed_resume)
    # Extract structured data from parsed_resume using Pydantic model

    candidates = [candidate_text]

    print(f"\n=== JOB DESCRIPTION ===\n{job_description}")
    print(f"\n=== CANDIDATE TEXT ===\n{candidate_text}")
    candidate_resume = CandidateResume.model_validate(candidate.parsed_resume)
    print(f"\n=== CANDIDATE SKILLS ===\n{candidate_resume.skills}")

    # Call the AI matcher
    ai_response = match_candidates_client(
        job_description=job_description,
        candidates=candidates,
        candidate_skills=[skill.name for skill in candidate_resume.skills]
        if candidate_resume.skills
        else [],
    )

    # print("\n\n\nai_response", ai_response)

    # Extract the first result (since we're matching one candidate)
    if not ai_response or not ai_response.get("results"):
        raise ValueError("No matching results returned from AI service")

    match_result = ai_response["results"][0]  # Get first result
    skill_analysis = match_result["skill_analysis"]
    summary = skill_analysis["summary"]
    weights = match_result["weights"]

    # Prepare match data with individual fields
    match_data = match_in.model_dump()

    # Main match result fields
    match_data["score"] = match_result["score"]
    match_data["embedding_similarity"] = match_result["embedding_similarity"]

    # Skill analysis fields
    match_data["match_percentage"] = skill_analysis["match_percentage"]
    match_data["matching_skills"] = skill_analysis["matching_skills"]
    match_data["missing_skills"] = skill_analysis["missing_skills"]
    match_data["extra_skills"] = skill_analysis["extra_skills"]

    # Summary fields
    match_data["total_required_skills"] = summary["total_required_skills"]
    match_data["matching_skills_count"] = summary["matching_skills_count"]
    match_data["missing_skills_count"] = summary["missing_skills_count"]
    match_data["extra_skills_count"] = summary["extra_skills_count"]

    # Weights
    match_data["skill_weight"] = weights["skill_weight"]
    match_data["embedding_weight"] = weights["embedding_weight"]

    print("\n\n\nmatch_data", match_data)

    # Remove any existing match for this application
    existing_match = db.exec(
        select(Match).where(Match.application_id == match_in.application_id)
    ).first()
    if existing_match:
        db.delete(existing_match)
        db.flush()
        print("deleted existing match", existing_match)

    db_match = Match.model_validate(match_data)
    print("\n\n\nnew match", db_match)
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
