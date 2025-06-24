from typing import Any, Dict, Optional, Union, List, Tuple
from copy import deepcopy
import time
import re
from datetime import datetime
from urllib.parse import urlparse
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from models.models import (
    Match,
    Application,
    Candidate,
    Job,
    JobFormKeyConstraint,
    FormKey,
    FieldType,
)
from models.candidate_pydantic import CandidateResume
from schemas import MatchCreate, MatchUpdate
from services.matching import match_candidates_client


def validate_form_constraints(
    form_responses: Dict, job_constraints: List[JobFormKeyConstraint]
) -> Dict[str, str]:
    """
    Validate form responses against job constraints.
    Returns a dictionary of constraint violations.
    """
    violations = {}
    
    for constraint in job_constraints:
        form_key = constraint.form_key
        if not form_key:
            continue
            
        form_key_id = str(form_key.id)
        response_value = form_responses.get(form_key_id)
        constraints = constraint.constraints or {}
        
        # Skip validation if no response and field is not required
        if response_value is None and not form_key.required:
            continue
            
        # Check if required field is missing
        if form_key.required and (response_value is None or response_value == ""):
            violations[form_key.name] = f"Required field '{form_key.name}' is missing"
            continue
            
        # Skip further validation if no response
        if response_value is None or response_value == "":
            continue
            
        # Field type specific validations
        if form_key.field_type == FieldType.NUMBER:
            try:
                num_value = float(response_value)
                if "min_value" in constraints and num_value < constraints["min_value"]:
                    violations[form_key.name] = f"{form_key.name}: Value {num_value} is below minimum {constraints['min_value']}"
                if "max_value" in constraints and num_value > constraints["max_value"]:
                    violations[form_key.name] = f"{form_key.name}: Value {num_value} is above maximum {constraints['max_value']}"
            except (ValueError, TypeError):
                violations[form_key.name] = f"{form_key.name}: Invalid number format"
                
        elif form_key.field_type == FieldType.DATE:
            try:
                date_value = datetime.fromisoformat(str(response_value).replace('Z', '+00:00'))
                if "after_date" in constraints:
                    after_date = datetime.fromisoformat(constraints["after_date"])
                    if date_value <= after_date:
                        violations[form_key.name] = f"{form_key.name}: Date must be after {constraints['after_date']}"
                if "before_date" in constraints:
                    before_date = datetime.fromisoformat(constraints["before_date"])
                    if date_value >= before_date:
                        violations[form_key.name] = f"{form_key.name}: Date must be before {constraints['before_date']}"
            except (ValueError, TypeError):
                violations[form_key.name] = f"{form_key.name}: Invalid date format"
                
        elif form_key.field_type == FieldType.LINK:
            try:
                parsed_url = urlparse(str(response_value))
                if not parsed_url.scheme or not parsed_url.netloc:
                    violations[form_key.name] = f"{form_key.name}: Invalid URL format"
                elif "allowed_domain" in constraints and constraints["allowed_domain"]:
                    allowed_domain = constraints["allowed_domain"].lower()
                    actual_domain = parsed_url.netloc.lower()
                    if allowed_domain not in actual_domain:
                        violations[form_key.name] = f"{form_key.name}: URL must be from domain {allowed_domain}"
            except Exception:
                violations[form_key.name] = f"{form_key.name}: Invalid URL"
                
        elif form_key.field_type == FieldType.SELECT:
            if "required_options" in constraints and constraints["required_options"]:
                required_options = constraints["required_options"]
                if str(response_value) not in required_options:
                    violations[form_key.name] = f"{form_key.name}: Must select one of: {', '.join(required_options)}"
                    
        elif form_key.field_type == FieldType.CHECKBOX:
            if "expected_state" in constraints and constraints["expected_state"] is not None:
                expected_state = constraints["expected_state"]
                # Handle different possible boolean representations
                if isinstance(response_value, str):
                    actual_state = response_value.lower() in ('true', '1', 'yes', 'on')
                else:
                    actual_state = bool(response_value)
                    
                if actual_state != expected_state:
                    expected_text = "checked" if expected_state else "unchecked"
                    violations[form_key.name] = f"{form_key.name}: Must be {expected_text}"
    
    return violations


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
    match_data["score_breakdown"] = match_result.get("score_breakdown", {})

    # Direct skill fields from matcher
    match_data["matching_skills"] = match_result.get("matching_skills", [])
    match_data["missing_skills"] = match_result.get("missing_skills", [])
    match_data["extra_skills"] = match_result.get("extra_skills", [])

    # Weights used in matching
    match_data["weights_used"] = match_result.get("weights_used", {})

    # Validate form constraints and add violations to flags
    flags = {}
    
    # Get job constraints with form keys
    job_constraints = db.exec(
        select(JobFormKeyConstraint)
        .options(
            # Eager load the form_key relationship
            selectinload(JobFormKeyConstraint.form_key)
        )
        .where(JobFormKeyConstraint.job_id == job.id)
    ).all()
    
    # Validate form responses against constraints
    if application.form_responses and job_constraints:
        constraint_violations = validate_form_constraints(
            application.form_responses, job_constraints
        )
        if constraint_violations:
            flags["constraint_violations"] = constraint_violations
    
    # Add flags to match data
    match_data["flags"] = flags if flags else None

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
