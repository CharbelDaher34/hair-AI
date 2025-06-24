#!/usr/bin/env python3
"""
Application Matcher Batch Script

This script processes all applications in the database that don't have matches.
It uses the matching service to create matches and saves them to the database.

Usage:
    python scripts/application_matcher_batch.py
"""

import os
import sys
import time
import json
import logging # Added
import traceback # Added
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from pathlib import Path # Added

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy # Added for type casting in query
from sqlmodel import Session, select, SQLModel
from sqlalchemy.orm import selectinload, joinedload
from core.database import engine
from crud import crud_match # We will add a new function here
from models.models import Application, Match, Candidate, Job
from models.candidate_pydantic import CandidateResume # To validate/structure parsed_resume
# from schemas import MatchCreate # MatchCreate is for single, we'll adapt

# --- Configuration ---
MAX_RETRIES_PER_JOB_BATCH = int(os.getenv("MATCHER_MAX_RETRIES_JOB", "3"))
RETRY_DELAY_SECONDS_JOB = int(os.getenv("MATCHER_RETRY_DELAY_JOB", "10"))
INTER_JOB_BATCH_DELAY_SECONDS = int(os.getenv("MATCHER_INTER_JOB_DELAY", "2"))
# Max candidates to send to AI per job in one call.
# The AI can handle many, but extremely large lists might hit request size limits or timeouts.
# Set to a high number if no immediate issues are known.
MAX_CANDIDATES_PER_AI_CALL = int(os.getenv("MATCHER_MAX_CANDIDATES_PER_AI_CALL", "100"))

# --- Logger Setup ---
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(Path(__file__).stem)


def get_applications_needing_match_grouped_by_job() -> Dict[int, List[Application]]:
    """
    Get all applications that don't have matches, grouped by job_id.
    Eagerly loads Candidate and Job objects to reduce further DB queries.

    Returns:
        Dict where keys are job_id and values are lists of Application objects for that job.
    """
    applications_by_job: Dict[int, List[Application]] = defaultdict(list)
    with Session(engine) as db:
        # Query applications that don't have any matches, joining Candidate for parsed_resume check
        # and Job for job_description check.
        stmt = (
            select(Application)
            .join(Candidate, Application.candidate_id == Candidate.id)
            .join(Job, Application.job_id == Job.id)
            .options(
                joinedload(Application.candidate).joinedload(Candidate.applications), # Eager load candidate
                joinedload(Application.job) # Eager load job
            )
            .where(
                ~Application.id.in_(select(Match.application_id).distinct()) # Application not in Match table
            )
            .where(Candidate.parsed_resume.is_not(None)) # Candidate has parsed resume
            .where(Candidate.parsed_resume.cast(sqlalchemy.types.JSON) != sqlalchemy.cast(None, sqlalchemy.types.JSON)) # Parsed resume is not SQL NULL
            .where(Candidate.parsed_resume.cast(sqlalchemy.types.JSON) != sqlalchemy.cast({}, sqlalchemy.types.JSON)) # Parsed resume is not empty JSON {}
            .where(Job.description.is_not(None)) # Job has a description
            .where(Job.description != "") # Job description is not empty
        )

        applications_to_process = db.exec(stmt).unique().all() # .unique() because of joins

        for app in applications_to_process:
            # Basic checks that should have been covered by the WHERE clauses, but good for sanity.
            if not app.candidate or not app.candidate.parsed_resume:
                logger.warning(f"Skipping application {app.id}: Candidate {app.candidate_id} has no parsed_resume (should be filtered by query).")
                continue
            if not app.job or not app.job.description or not app.job.description.strip():
                logger.warning(f"Skipping application {app.id}: Job {app.job_id} has no valid description (should be filtered by query).")
                continue

            applications_by_job[app.job_id].append(app)

    return applications_by_job


def process_matches_for_job_batch(
    db: Session,
    job: Job,
    applications_for_job: List[Application]
) -> Tuple[int, int]:
    """
    Processes a batch of applications for a single job.
    Calls AI matcher and creates Match records via crud_match.
    """
    successful_matches_for_job = 0
    failed_matches_for_job = 0

    # candidates_payload_for_ai and app_id_to_candidate_id_map are now internal to crud_match.create_matches_for_job_and_applicants
    # This function's role is simplified to mainly call the CRUD function.

    # The main logic of preparing AI data, calling AI, and creating DB objects is now in crud_match.
    # This function just orchestrates the call for a given job and its applications.
    if not applications_for_job:
        logger.info(f"Job {job.id}: No applications to process in this batch.")
        return 0,0

    logger.info(f"Job {job.id}: Preparing to match {len(applications_for_job)} applications.")

    try:
        num_succeeded, num_failed = crud_match.create_matches_for_job_and_applicants(
            db=db,
            job=job,
            applications=applications_for_job,
        )
        successful_matches_for_job += num_succeeded
        failed_matches_for_job += num_failed
    except Exception as e:
        logger.error(f"Job {job.id}: Unhandled exception in create_matches_for_job_and_applicants for {len(applications_for_job)} applications: {e}", exc_info=True)
        # If the CRUD function itself throws a major error not caught internally,
        # all applications in this specific call are considered failed.
        failed_matches_for_job += len(applications_for_job) - successful_matches_for_job # Add remaining as failed

    logger.info(f"Job {job.id}: Processed batch of {len(applications_for_job)} applications. Succeeded: {successful_matches_for_job}, Failed: {failed_matches_for_job}")
    return successful_matches_for_job, failed_matches_for_job


def process_all_applications():
    """
    Process all applications that need matching, grouped by job.
    """
    logger.info(f"Starting batch application matching.")

    applications_by_job = get_applications_needing_match_grouped_by_job()

    if not applications_by_job:
        logger.info("No applications found needing matches with valid prerequisites.")
        return {"successful_matches": 0, "failed_matches": 0, "total_applications_considered": 0, "jobs_processed": 0}

    total_applications_to_match = sum(len(apps) for apps in applications_by_job.values())
    logger.info(f"Found {total_applications_to_match} applications across {len(applications_by_job)} jobs needing matches.")

    overall_successful_matches = 0
    overall_failed_matches = 0
    jobs_processed_count = 0

    for job_id, apps_for_this_job in applications_by_job.items():
        jobs_processed_count += 1
        job_object = apps_for_this_job[0].job

        logger.info(f"Processing job {job_id} ('{job_object.title}') with {len(apps_for_this_job)} applications. ({jobs_processed_count}/{len(applications_by_job)} jobs)")

        for i in range(0, len(apps_for_this_job), MAX_CANDIDATES_PER_AI_CALL):
            application_sub_batch = apps_for_this_job[i:i + MAX_CANDIDATES_PER_AI_CALL]
            sub_batch_num = i // MAX_CANDIDATES_PER_AI_CALL + 1
            if not application_sub_batch:
                continue

            logger.info(f"  - Sub-batch {sub_batch_num} with {len(application_sub_batch)} applications for job {job_id}.")

            for attempt in range(MAX_RETRIES_PER_JOB_BATCH):
                succeeded_in_sub_batch = 0
                failed_in_sub_batch = 0
                try:
                    with Session(engine) as db:
                        succeeded_in_sub_batch, failed_in_sub_batch = process_matches_for_job_batch(
                            db, job_object, application_sub_batch
                        )
                    # Accumulate results from this attempt
                    # Note: If retrying, ensure not to double-count successes from previous attempts of the same sub-batch.
                    # The current structure re-processes the whole sub-batch. If process_matches_for_job_batch
                    # is idempotent (deletes existing before creating), this is fine.
                    # For now, we sum up results from the latest attempt for this sub-batch.
                    # A more complex state management would be needed if only failed items from a sub-batch are retried.

                    if failed_in_sub_batch == 0:
                        logger.info(f"  - Sub-batch {sub_batch_num} for job {job_id} processed successfully on attempt {attempt + 1} ({succeeded_in_sub_batch} matches).")
                        overall_successful_matches += succeeded_in_sub_batch
                        # overall_failed_matches += failed_in_sub_batch # This is 0 here
                        break
                    else:
                        logger.warning(f"  - Sub-batch {sub_batch_num} for job {job_id} had {failed_in_sub_batch} failures (and {succeeded_in_sub_batch} successes) on attempt {attempt + 1}.")
                        if attempt < MAX_RETRIES_PER_JOB_BATCH - 1:
                             logger.info(f"  - Retrying sub-batch {sub_batch_num} for job {job_id} in {RETRY_DELAY_SECONDS_JOB}s...")
                             time.sleep(RETRY_DELAY_SECONDS_JOB)
                        else:
                            logger.error(f"  - Max retries reached for sub-batch {sub_batch_num} of job {job_id}. {failed_in_sub_batch} app(s) failed, {succeeded_in_sub_batch} app(s) succeeded in this final attempt.")
                            overall_successful_matches += succeeded_in_sub_batch
                            overall_failed_matches += failed_in_sub_batch

                except Exception as e: # Catch errors from process_matches_for_job_batch or session handling
                    logger.error(f"  - Critical error processing sub-batch {sub_batch_num} for job {job_id} (attempt {attempt + 1}): {e}", exc_info=True)
                    if attempt < MAX_RETRIES_PER_JOB_BATCH - 1:
                        logger.info(f"  - Retrying sub-batch {sub_batch_num} for job {job_id} due to critical error in {RETRY_DELAY_SECONDS_JOB}s...")
                        time.sleep(RETRY_DELAY_SECONDS_JOB)
                    else:
                        logger.error(f"  - Max retries reached for sub-batch {sub_batch_num} of job {job_id} due to critical error. Marking all {len(application_sub_batch)} apps in this sub-batch as failed for this attempt.")
                        overall_failed_matches += len(application_sub_batch) # Assume all failed if critical error on last attempt

                if failed_in_sub_batch == 0 and attempt < MAX_RETRIES_PER_JOB_BATCH : # Broke from successful attempt
                    break
            # End of retry loop for a sub-batch

        if jobs_processed_count < len(applications_by_job):
            logger.info(f"Waiting {INTER_JOB_BATCH_DELAY_SECONDS}s before processing next job...")
            time.sleep(INTER_JOB_BATCH_DELAY_SECONDS)

    logger.info(f"Batch application matching completed.")
    logger.info(f"Results: {overall_successful_matches} successful matches created, {overall_failed_matches} failed matches.")
    logger.info(f"Total applications considered for matching: {total_applications_to_match} across {jobs_processed_count} jobs.")
    return {"successful_matches": overall_successful_matches, "failed_matches": overall_failed_matches, "total_applications_considered": total_applications_to_match, "jobs_processed": jobs_processed_count}


if __name__ == "__main__":
    process_all_applications()
