from typing import Any, Dict, Optional, Union, List
import time
import logging
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload

from models.models import (
    Application,
    Match,
    Job,
    Candidate,
    FormKey,
    JobFormKeyConstraint,
    Status,
    ApplicationStatus,
)
from schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    MatchCreate,
    ApplicationWithDetails,
)
from . import crud_job
from . import crud_match
from . import crud_candidate
from core.database import engine

# --- Logger Setup ---
logger = logging.getLogger(__name__)
# Configure if not already configured by a higher-level module
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_application(db: Session, application_id: int) -> Optional[Application]:
    return db.get(Application, application_id)


def get_applications_by_job(
    db: Session, job_id: int, skip: int = 0, limit: int = 100
) -> List[Application]:
    statement = (
        select(Application)
        .where(Application.job_id == job_id)
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()


def get_applications_by_candidate(
    db: Session, candidate_id: int, skip: int = 0, limit: int = 100
) -> List[Application]:
    statement = (
        select(Application)
        .where(Application.candidate_id == candidate_id)
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()


def get_random_applications_by_employer(
    db: Session, employer_id: int, skip: int = 0, limit: int = 100
) -> List[Application]:
    """Get applications for jobs belonging to an employer with pagination, ordered by most recent"""
    statement = (
        select(Application)
        .join(Job, Application.job_id == Job.id)
        .where(Job.employer_id == employer_id)
        .where(Job.status != Status.CLOSED)
        .order_by(Application.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = db.exec(statement).all()
    logger.info(
        f"[get_random_applications_by_employer] skip={skip}, limit={limit}, returned_ids={[app.id for app in result]}"
    )
    return result


def get_application_with_details(
    db: Session, application_id: int
) -> Optional[ApplicationWithDetails]:
    """Get application with candidate, job details, and transformed form_responses."""
    statement = (
        select(Application)
        .join(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
        .where(Job.status != Status.CLOSED)
        .options(
            selectinload(Application.candidate),
            selectinload(Application.job)
            .selectinload(Job.form_key_constraints)
            .selectinload(JobFormKeyConstraint.form_key),
            selectinload(Application.matches),
        )
    )
    application = db.exec(statement).first()

    if application:
        # Transform form_responses from Dict to List[FormResponseItem]
        if (
            application.form_responses
            and isinstance(application.form_responses, dict)
            and application.job
        ):
            transformed_responses = []

            # Create a mapping of form_key_id to FormKey.name
            form_key_mapping = {}
            if application.job.form_key_constraints:
                for constraint in application.job.form_key_constraints:
                    if constraint.form_key:
                        # Map both the form_key.id and form_key.name as potential keys
                        form_key_mapping[str(constraint.form_key.id)] = (
                            constraint.form_key.name
                        )
                        form_key_mapping[constraint.form_key.name] = (
                            constraint.form_key.name
                        )

            # Transform the form_responses using the actual FormKey names
            for key, value in application.form_responses.items():
                form_key_name = form_key_mapping.get(
                    key, key
                )  # Fallback to original key if not found
                transformed_responses.append({"name": form_key_name, "value": value})

            application.form_responses = transformed_responses
        elif not application.form_responses:
            # Ensure it's an empty list if None or already empty, to match the new schema type
            application.form_responses = []

        # Convert to ApplicationWithDetails schema
        # Get the first match if available (since schema expects single match)
        match_data = application.matches[0] if application.matches else None

        return ApplicationWithDetails(
            **application.model_dump(),
            candidate=application.candidate,
            job=application.job,
            match=match_data,
        )

    return None


def create_match_background(application_id: int, max_retries: int = 3):
    """
    Background task to create match for an application.

    Args:
        application_id: ID of the application
        max_retries: Maximum number of retry attempts
    """
    for attempt in range(max_retries):
        try:
            logger.info(
                f"[Background] Starting match creation for application {application_id} (attempt {attempt + 1}/{max_retries})"
            )

            with Session(engine) as db:
                # Get candidate and job data for validation
                application = db.get(Application, application_id)
                if not application:
                    logger.warning(
                        f"[Background] Application {application_id} not found"
                    )
                    return

                candidate = db.get(Candidate, application.candidate_id)
                job = db.get(Job, application.job_id)

                # Check if we have the necessary data for matching
                if (
                    candidate
                    and job
                    and candidate.parsed_resume
                    and job.description
                    and job.description.strip()
                ):
                    logger.info(
                        f"[Background] Creating match for application {application_id}"
                    )
                    logger.info(f"[Background] Job: {job.title}")
                    logger.info(f"[Background] Candidate: {candidate.full_name}")

                    # Create match using CRUD (which will call the AI service)
                    match_create = MatchCreate(application_id=application_id)
                    new_match = crud_match.create_match(db=db, match_in=match_create)

                    if new_match:
                        db.commit()
                        logger.info(
                            f"[Background] Successfully created match {new_match.id} for application {application_id}"
                        )
                        return  # Success - exit the retry loop
                    else:
                        logger.warning(
                            f"[Background] Failed to create match for application {application_id}"
                        )
                        if attempt < max_retries - 1:
                            logger.info(f"[Background] Retrying in 5 seconds...")
                            time.sleep(5)
                            continue
                        else:
                            logger.error(
                                f"[Background] Max retries reached for application {application_id}"
                            )
                            return
                else:
                    # Log why matching was skipped
                    if not candidate:
                        logger.warning(
                            f"[Background] Candidate not found for application {application_id}"
                        )
                    elif not job:
                        logger.warning(
                            f"[Background] Job not found for application {application_id}"
                        )
                    elif not candidate.parsed_resume:
                        logger.warning(
                            f"[Background] Candidate {candidate.id} has no parsed resume data - skipping match creation"
                        )
                    elif not job.description or not job.description.strip():
                        logger.warning(
                            f"[Background] Job {job.id} has no description - skipping match creation"
                        )
                    return

        except Exception as match_err:
            logger.error(
                f"[Background] Error creating match for application {application_id} (attempt {attempt + 1}): {match_err}",
                exc_info=True,
            )

            if attempt < max_retries - 1:
                logger.info(f"[Background] Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.error(
                    f"[Background] Max retries reached for application {application_id}"
                )
                return


def create_application(
    db: Session, *, application_in: ApplicationCreate
) -> Application:
    db_application = Application.model_validate(application_in)
    db.add(db_application)
    db.commit()
    db.refresh(db_application)

    # Add candidate to employer
    if db_application.candidate_id:
        candidate = db.get(Candidate, db_application.candidate_id)
        if candidate:
            crud_candidate.add_candidate_to_employer(
                db,
                candidate_id=candidate.id,
                employer_id=db_application.job.employer_id,
            )

    logger.info(
        f"[CreateApplication] Application {db_application.id} created successfully"
    )
    logger.info(f"[CreateApplication] Match creation will be handled in background")

    return db_application


def update_application(
    db: Session,
    *,
    db_application: Application,
    application_in: Union[ApplicationUpdate, Dict[str, Any]],
) -> Application:
    if isinstance(application_in, dict):
        update_data = application_in
    else:
        update_data = application_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_application, field, value)

    db.add(db_application)
    db.commit()
    db.refresh(db_application)

    return db_application


def delete_application(db: Session, *, application_id: int) -> Optional[Application]:
    db_application = db.get(Application, application_id)
    match = db.get(Match, db_application.id)
    if match:
        db.delete(match)
    if db_application:
        db.delete(db_application)
        db.commit()
    return db_application


def get_applications_count_by_employer(db: Session, employer_id: int) -> int:
    job_ids_subquery = (
        select(Job.id)
        .where(Job.employer_id == employer_id)
        .where(Job.status != Status.CLOSED)
    )
    statement = select(func.count(Application.id)).where(
        Application.job_id.in_(job_ids_subquery)
    )
    result = db.exec(statement)
    total = result.one()
    logger.info(f"Total applications: {total}")
    if isinstance(total, tuple):
        total = total[0]
    return total


def get_application_count_by_job_id(db: Session, job_id: int) -> int:
    statement = select(func.count(Application.id)).where(Application.job_id == job_id)
    result = db.exec(statement)
    total = result.one()
    if isinstance(total, tuple):
        total = total[0]
    return total
