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
from datetime import datetime
from typing import List

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from crud import crud_match
from models.models import Application, Match, Candidate, Job
from schemas import MatchCreate


def get_applications_without_matches() -> List[Application]:
    """
    Get all applications that don't have matches.

    Returns:
        List of applications that need matching
    """
    with Session(engine) as db:
        # Query applications that don't have any matches
        statement = select(Application).where(
            ~Application.id.in_(select(Match.application_id))
        )
        applications = db.exec(statement).all()

        return applications


def create_match_for_application(application_id: int, max_retries: int = 3) -> bool:
    """
    Create a match for a single application.

    Args:
        application_id: ID of the application
        max_retries: Maximum number of retry attempts

    Returns:
        bool: True if successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            print(
                f"[Matcher] Processing application {application_id} (attempt {attempt + 1}/{max_retries})"
            )

            with Session(engine) as db:
                # Get the application with related data
                application = db.get(Application, application_id)
                if not application:
                    print(f"[Matcher] Application {application_id} not found")
                    return False

                # Get candidate and job data for validation
                candidate = db.get(Candidate, application.candidate_id)
                job = db.get(Job, application.job_id)

                if not candidate or not job:
                    print(
                        f"[Matcher] Missing candidate or job data for application {application_id}"
                    )
                    return False

                # Check if candidate has parsed resume data
                if not candidate.parsed_resume:
                    print(
                        f"[Matcher] Candidate {candidate.id} has no parsed resume data - skipping"
                    )
                    return False

                # Check if job has description
                if not job.description or not job.description.strip():
                    print(f"[Matcher] Job {job.id} has no description - skipping")
                    return False

                print(f"[Matcher] Creating match for application {application_id}")
                print(f"[Matcher] Job: {job.title}")
                print(f"[Matcher] Candidate: {candidate.full_name}")

                # Create match using CRUD (which will call the AI service)
                match_create = MatchCreate(application_id=application_id)

                new_match = crud_match.create_match(db=db, match_in=match_create)

                if new_match:
                    print(
                        f"[Matcher] Successfully created match {new_match.id} for application {application_id}"
                    )
                    print(f"[Matcher] Match score: {new_match.score:.3f}")
                    print(f"[Matcher] Matching skills: {len(new_match.matching_skills or [])}")
                    print(f"[Matcher] Missing skills: {len(new_match.missing_skills or [])}")
                    print(f"[Matcher] Extra skills: {len(new_match.extra_skills or [])}")
                    return True
                else:
                    print(
                        f"[Matcher] Failed to create match for application {application_id}"
                    )
                    return False

        except Exception as match_err:
            print(
                f"[Matcher] Error creating match for application {application_id} (attempt {attempt + 1}): {str(match_err)}"
            )
            print(f"[Matcher] Error type: {type(match_err)}")

            if attempt < max_retries - 1:
                print(f"[Matcher] Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"[Matcher] Max retries reached for application {application_id}")
                import traceback

                print(f"[Matcher] Full traceback: {traceback.format_exc()}")
                return False

    return False


def process_all_applications():
    """
    Process all applications that need matching.

    Returns:
        dict: Results summary with successful and failed counts
    """
    print(f"[Matcher] Starting batch application matching at {datetime.now()}")

    applications = get_applications_without_matches()
    print(f"[Matcher] Found {len(applications)} applications that need matching")

    if not applications:
        print("[Matcher] No applications to process")
        return {"successful": 0, "failed": 0, "total": 0}

    successful = 0
    failed = 0

    for i, application in enumerate(applications, 1):
        print(
            f"\n[Matcher] Processing application {i}/{len(applications)}: ID {application.id}"
        )

        success = create_match_for_application(application.id)
        if success:
            successful += 1
            print(f"[Matcher] ✅ Successfully processed application {application.id}")
        else:
            failed += 1
            print(f"[Matcher] ❌ Failed to process application {application.id}")

        # Add a small delay between applications to avoid overwhelming the matching service
        if i < len(applications):
            print("[Matcher] Waiting 2 seconds before next application...")
            time.sleep(2)

    print(f"\n[Matcher] Batch matching completed at {datetime.now()}")
    print(f"[Matcher] Results: {successful} successful, {failed} failed")

    return {"successful": successful, "failed": failed, "total": len(applications)}


if __name__ == "__main__":
    process_all_applications()
