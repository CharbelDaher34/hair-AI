from typing import Any, Dict, Optional, Union, List, Tuple
from copy import deepcopy
import time
import re
import logging # Added
from datetime import datetime
from urllib.parse import urlparse
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

# Get a logger instance
logger = logging.getLogger(__name__) # Using __name__ will give 'backend.app.crud.crud_match'
# Configure if not already configured by a higher-level module (e.g. main app or script)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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


# This old create_match is for a single application.
# It will be kept for now for other potential uses (e.g. API endpoint for single match)
# but the batch script will use the new create_matches_for_job_and_applicants.
def create_match(db: Session, *, match_in: MatchCreate) -> Optional[Match]:
    application = db.get(Application, match_in.application_id)
    if not application:
        logger.error(f"Application with id {match_in.application_id} not found for match creation.")
        return None

    # Eager load candidate and job if not already loaded (though application passed in might have them)
    if not application.candidate: # Assuming relation is loaded or use selectinload if needed
        application.candidate = db.get(Candidate, application.candidate_id)
    if not application.job:
        application.job = db.get(Job, application.job_id)

    candidate = application.candidate
    job = application.job

    if not candidate or not job:
        logger.error(f"Candidate or Job not found for application {application.id}.")
        return None
    if not candidate.parsed_resume or not isinstance(candidate.parsed_resume, dict) or not candidate.parsed_resume:
        logger.error(f"Candidate {candidate.id} has no valid parsed_resume data for application {application.id}.")
        return None
    if not job.description or not job.description.strip():
        logger.error(f"Job {job.id} has no description for application {application.id}.")
        return None

    job_data = job.model_dump(mode="json")

    # Prepare candidate data for AI. Ensure it has 'candidate_name' or 'full_name'.
    candidate_ai_data = candidate.parsed_resume.copy()
    if 'candidate_name' not in candidate_ai_data and 'full_name' in candidate_ai_data:
        candidate_ai_data['candidate_name'] = candidate_ai_data['full_name']
    elif 'candidate_name' not in candidate_ai_data and candidate.full_name:
        candidate_ai_data['candidate_name'] = candidate.full_name

    try:
        ai_response = match_candidates_client(
            job=job_data,
            candidates=[candidate_ai_data], # Send as a list with one candidate
        )
    except Exception as e:
        logger.error(f"Error calling AI matching service for app {application.id}: {e}", exc_info=True)
        return None

    if not ai_response or not ai_response.get("results") or not ai_response["results"]:
        logger.warning(f"No valid matching results from AI for app {application.id}. AI Response: {ai_response}")
        return None

    match_result_from_ai = ai_response["results"][0]

    match_db_data = {
        "application_id": application.id,
        "score": match_result_from_ai.get("score", 0.0),
        "score_breakdown": match_result_from_ai.get("score_breakdown", {}),
        "matching_skills": match_result_from_ai.get("matching_skills", []),
        "missing_skills": match_result_from_ai.get("missing_skills", []),
        "extra_skills": match_result_from_ai.get("extra_skills", []),
        "weights_used": match_result_from_ai.get("weights_used", {}),
        "analysis": match_result_from_ai.get("analysis", ""),
    }
    
    flags = {}
    job_constraints = db.exec(
        select(JobFormKeyConstraint)
        .options(selectinload(JobFormKeyConstraint.form_key))
        .where(JobFormKeyConstraint.job_id == job.id)
    ).all()
    
    if application.form_responses and job_constraints:
        constraint_violations = validate_form_constraints(application.form_responses, job_constraints)
        if constraint_violations:
            flags["constraint_violations"] = constraint_violations
    match_db_data["flags"] = flags if flags else None

    existing_match = db.exec(select(Match).where(Match.application_id == application.id)).first()
    if existing_match:
        db.delete(existing_match)
        db.flush() # Ensure delete is processed before add if IDs were same (not SQLModel models)

    db_match = Match.model_validate(match_db_data)
    db.add(db_match)
    # db.commit() # Commit is handled by the calling script for batches
    # db.refresh(db_match) # Refresh also handled by caller if needed after commit
    return db_match


def create_matches_for_job_and_applicants(
    db: Session,
    job: Job,
    applications: List[Application]
) -> Tuple[int, int]:
    """
    Creates match records for a given job and a list of its applications.
    Calls the AI matcher once for all candidates of these applications.
    Adds Match objects to the session but does NOT commit. Commit should be handled by the caller.
    Returns (number_of_successes, number_of_failures).
    """
    succeeded = 0
    failed = 0

    if not applications:
        return 0, 0

    job_data_for_ai = job.model_dump(mode="json")
    candidates_data_for_ai: List[Dict[str, Any]] = []
    # Keep applications in the same order as candidates_data_for_ai for result mapping
    ordered_applications_for_results: List[Application] = []

    for app in applications:
        if not app.candidate or not app.candidate.parsed_resume or not isinstance(app.candidate.parsed_resume, dict) or not app.candidate.parsed_resume:
            logger.warning(f"App {app.id} for job {job.id}: Candidate {app.candidate_id} has invalid parsed_resume. Skipping.")
            failed += 1
            continue

        candidate_ai_data = app.candidate.parsed_resume.copy()
        # Ensure 'candidate_name' or 'full_name' is present for AI Matcher service
        if 'candidate_name' not in candidate_ai_data and 'full_name' in candidate_ai_data: # Check if full_name exists before assigning
            candidate_ai_data['candidate_name'] = candidate_ai_data['full_name']
        elif 'candidate_name' not in candidate_ai_data and app.candidate.full_name: # Fallback to Candidate.full_name if available
            candidate_ai_data['candidate_name'] = app.candidate.full_name
        # If neither is available, the AI service might have issues, but we proceed.

        candidates_data_for_ai.append(candidate_ai_data)
        ordered_applications_for_results.append(app)

    if not candidates_data_for_ai:
        logger.warning(f"Job {job.id}: No valid candidate data prepared for AI from {len(applications)} applications.")
        return 0, len(applications) # All considered failed if no data could be sent

    try:
        logger.info(f"Calling AI for job {job.id} ('{job.title}') with {len(candidates_data_for_ai)} candidates.")
        ai_batch_response = match_candidates_client(
            job=job_data_for_ai,
            candidates=candidates_data_for_ai,
            # weights and fuzzy_threshold can be passed if needed, using defaults for now
        )
    except Exception as e:
        logger.error(f"Error calling AI matching service for job {job.id} with {len(candidates_data_for_ai)} candidates: {e}", exc_info=True)
        return 0, len(ordered_applications_for_results) # All failed for this AI call

    if not ai_batch_response or not ai_batch_response.get("results"):
        logger.warning(f"No 'results' field in AI response for job {job.id}. AI Response: {ai_batch_response}")
        return 0, len(ordered_applications_for_results)

    ai_match_results = ai_batch_response["results"]

    if len(ai_match_results) != len(ordered_applications_for_results):
        logger.error(f"Mismatch in AI result count for job {job.id}. Expected {len(ordered_applications_for_results)}, got {len(ai_match_results)}. Marking all as failed for this batch.")
        logger.debug(f"AI Response for job {job.id} (mismatch): {ai_batch_response}")
        return 0, len(ordered_applications_for_results)

    # Get job constraints once for all applications of this job
    job_constraints = db.exec(
        select(JobFormKeyConstraint)
        .options(selectinload(JobFormKeyConstraint.form_key))
        .where(JobFormKeyConstraint.job_id == job.id)
    ).all()

    for idx, match_result_from_ai in enumerate(ai_match_results):
        application_for_this_match = ordered_applications_for_results[idx]

        if not match_result_from_ai or not isinstance(match_result_from_ai, dict):
            logger.warning(f"Invalid AI result item for app {application_for_this_match.id} (job {job.id}). Skipping. AI item: {match_result_from_ai}")
            failed += 1
            continue

        match_db_data = {
            "application_id": application_for_this_match.id,
            "score": match_result_from_ai.get("score", 0.0),
            "score_breakdown": match_result_from_ai.get("score_breakdown", {}),
            "matching_skills": match_result_from_ai.get("matching_skills", []),
            "missing_skills": match_result_from_ai.get("missing_skills", []),
            "extra_skills": match_result_from_ai.get("extra_skills", []),
            "weights_used": match_result_from_ai.get("weights_used", {}),
            "analysis": match_result_from_ai.get("analysis", ""),
        }

        flags = {}
        if application_for_this_match.form_responses and job_constraints:
            constraint_violations = validate_form_constraints(
                application_for_this_match.form_responses, job_constraints
            )
            if constraint_violations:
                flags["constraint_violations"] = constraint_violations
        match_db_data["flags"] = flags if flags else None

        # Remove any existing match for this application before adding new one
        # This handles retries or re-processing scenarios.
        existing_match = db.exec(select(Match).where(Match.application_id == application_for_this_match.id)).first()
        if existing_match:
            logger.info(f"Deleting existing match for application {application_for_this_match.id} (job {job.id}) before creating new one.")
            db.delete(existing_match)
            db.flush() # Ensure delete is processed before add, especially if application_id has unique constraint or similar.

        try:
            db_match = Match.model_validate(match_db_data)
            db.add(db_match)
            succeeded += 1
            logger.info(f"Prepared Match for app {application_for_this_match.id} (job {job.id}), score: {db_match.score:.3f}")
        except Exception as e:
            logger.error(f"Error validating/creating Match object for app {application_for_this_match.id} (job {job.id}): {e}", exc_info=True)
            failed += 1
            # If model_validate fails, the object isn't added to session, so no specific rollback needed here for this item.

    # Caller (application_matcher_batch.py) is responsible for db.commit() or db.rollback() for the session.
    logger.info(f"For job {job.id} ('{job.title}'): {succeeded} matches prepared for DB, {failed} failed.")
    return succeeded, failed


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
        # db.commit() # Commit handled by caller or specific use case
    return db_match
