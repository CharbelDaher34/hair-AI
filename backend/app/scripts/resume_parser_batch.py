#!/usr/bin/env python3
"""
Resume Parser Batch Script

This script processes all candidates in the database that don't have parsed resume data.
It runs once and exits.

Usage:
    python scripts/resume_parser_batch.py
"""

import os
import sys
import time
import json
import logging # Added logging
import traceback # Added for explicit traceback logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, text # type: ignore
from core.database import engine
from crud import crud_candidate
from models.models import Candidate
from utils.file_utils import get_resume_file_path
from models.candidate_pydantic import CandidateResume # This is the Pydantic model for the parsed data
from services.resume_upload import AgentClient

# --- Configuration ---
DEFAULT_SYSTEM_PROMPT = "Extract structured information from resumes. Focus on contact details, skills, and work experience. Ensure output matches the provided schema."
DEFAULT_BATCH_SIZE = int(os.getenv("RESUME_PARSER_BATCH_SIZE", "10"))
MAX_RETRIES = int(os.getenv("RESUME_PARSER_MAX_RETRIES", "3"))
RETRY_DELAY_SECONDS = int(os.getenv("RESUME_PARSER_RETRY_DELAY", "10"))
INTER_BATCH_DELAY_SECONDS = int(os.getenv("RESUME_PARSER_INTER_BATCH_DELAY", "5"))

# --- Logger Setup ---
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to stdout
    ]
)
logger = logging.getLogger(Path(__file__).stem) # Use the script's name as the logger name


def get_candidates_without_parsed_resume() -> List[Candidate]:
    """
    Get all candidates that don't have parsed resume data and have a resume file accessible by the script.

    Returns:
        List of candidates that need resume parsing
    """
    with Session(engine) as db:
        # Query candidates where parsed_resume is None or empty and resume_url is not None
        statement = select(Candidate).where(
            text(
                "(parsed_resume IS NULL OR parsed_resume::text = '{}' OR parsed_resume::text = 'null')"
            )
            & (Candidate.resume_url.is_not(None))
        )
        candidates_from_db = db.exec(statement).all()

        candidates_with_valid_files = []
        for candidate_obj in candidates_from_db:
            resume_path_str = get_resume_file_path(candidate_obj.id) # Gets path based on configured storage
            if resume_path_str and os.path.exists(resume_path_str):
                candidates_with_valid_files.append(candidate_obj)
            else:
                logger.warning(
                    f"Candidate {candidate_obj.id} ({candidate_obj.full_name}) has resume_url but file not found or inaccessible at: {resume_path_str}. Skipping."
                )
        return candidates_with_valid_files


def process_all_candidates():
    """
    Process all candidates that need resume parsing, now in batches.

    Returns:
        dict: Results summary with successful and failed counts
    """
    logger.info(f"Starting batch resume parsing with batch size {DEFAULT_BATCH_SIZE}")

    candidates_to_process = get_candidates_without_parsed_resume()
    total_candidates_to_process = len(candidates_to_process)
    logger.info(f"Found {total_candidates_to_process} candidates that need resume parsing and have accessible files.")

    if not candidates_to_process:
        logger.info("No candidates to process.")
        return {"successful": 0, "failed": 0, "total": 0}

    successful_parses = 0
    failed_parses = 0

    try:
        agent_client = AgentClient() # Initialize once
    except ConnectionError as e:
        logger.critical(f"Could not initialize AgentClient (AI service connection failed): {e}. Cannot process any resumes.")
        return {"successful": 0, "failed": total_candidates_to_process, "total": total_candidates_to_process}

    candidate_schema_str = json.dumps(CandidateResume.model_json_schema())

    for i in range(0, total_candidates_to_process, DEFAULT_BATCH_SIZE):
        current_candidate_batch_objects = candidates_to_process[i:i + DEFAULT_BATCH_SIZE]
        current_batch_num = i // DEFAULT_BATCH_SIZE + 1
        total_batches = (total_candidates_to_process + DEFAULT_BATCH_SIZE - 1) // DEFAULT_BATCH_SIZE

        logger.info(f"Processing batch {current_batch_num}/{total_batches} with {len(current_candidate_batch_objects)} candidates...")

        batch_metadata_for_ai: List[Dict[str, Any]] = []
        # candidate_map_for_batch: Dict[int, Candidate] = {} # Not strictly needed if results map by order
        files_to_upload_for_batch: List[str] = []

        for candidate_obj in current_candidate_batch_objects:
            resume_path_str = get_resume_file_path(candidate_obj.id)
            absolute_resume_file_path = os.path.abspath(resume_path_str)
            # candidate_map_for_batch[candidate_obj.id] = candidate_obj # Map not used if relying on order

            batch_item = {
                "candidate_id": candidate_obj.id,
                "resume_texts": None,
                "resume_files": [Path(absolute_resume_file_path).name],
                "schema_str": candidate_schema_str,
                "system_prompt": DEFAULT_SYSTEM_PROMPT,
            }
            batch_metadata_for_ai.append(batch_item)
            files_to_upload_for_batch.append(absolute_resume_file_path)

        if not batch_metadata_for_ai:
            logger.warning("No candidates prepared for AI in this batch (should not happen if list was not empty). Skipping.")
            continue

        unique_files_for_upload = sorted(list(set(files_to_upload_for_batch)))

        parsed_results_from_ai = None
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES} to parse batch of {len(batch_metadata_for_ai)} resumes via AI.")
                parsed_results_from_ai = agent_client.parse_batch(batch_metadata_for_ai, unique_files_for_upload)

                if parsed_results_from_ai is not None:
                    break

                logger.warning(f"AI service call returned None for batch (attempt {attempt + 1}). Retrying in {RETRY_DELAY_SECONDS}s...")
            except Exception as e:
                logger.error(f"Exception during AI service call for batch (attempt {attempt + 1}): {e}", exc_info=True)

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                logger.error(f"Max retries ({MAX_RETRIES}) reached for calling AI for this batch.")

        if parsed_results_from_ai is None:
            failed_parses += len(current_candidate_batch_objects)
            logger.error(f"Failed to get response from AI for batch {current_batch_num} ({len(current_candidate_batch_objects)} candidates) after {MAX_RETRIES} retries.")
        elif len(parsed_results_from_ai) != len(batch_metadata_for_ai):
            failed_parses += len(current_candidate_batch_objects)
            logger.error(f"Critical: Mismatch in AI results length for batch {current_batch_num}! Expected {len(batch_metadata_for_ai)}, got {len(parsed_results_from_ai)}. Marking all in batch as failed.")
            try:
                problematic_response_json = json.dumps(parsed_results_from_ai)
                logger.debug(f"Problematic AI response (first 1000 chars): {problematic_response_json[:1000]}")
            except Exception:
                logger.debug(f"Problematic AI response (unserializable): {str(parsed_results_from_ai)[:1000]}")
        else:
            with Session(engine) as db:
                processed_in_db_count = 0
                for idx, ai_result_item in enumerate(parsed_results_from_ai):
                    # Relies on batch_metadata_for_ai and parsed_results_from_ai being in the same order
                    original_candidate_id = batch_metadata_for_ai[idx]["candidate_id"]

                    db_candidate_to_update = db.get(Candidate, original_candidate_id)
                    if not db_candidate_to_update:
                        logger.warning(f"Candidate {original_candidate_id} not found in DB session during update attempt for batch {current_batch_num}. Skipping.")
                        failed_parses +=1
                        continue

                    if ai_result_item and isinstance(ai_result_item, dict):
                        try:
                            crud_candidate.update_candidate(
                                db=db,
                                db_candidate=db_candidate_to_update,
                                candidate_in={"parsed_resume": ai_result_item},
                            )
                            logger.info(f"Successfully prepared update for candidate {original_candidate_id} ({db_candidate_to_update.full_name}) in batch {current_batch_num}.")
                            successful_parses += 1
                            processed_in_db_count +=1
                        except Exception as e:
                            logger.error(f"Error during DB update preparation for candidate {original_candidate_id} in batch {current_batch_num}: {e}", exc_info=True)
                            failed_parses += 1
                    else:
                        logger.warning(f"No valid parsed data from AI for candidate {original_candidate_id} in batch {current_batch_num}. AI Result: {ai_result_item}")
                        failed_parses += 1
                try:
                    db.commit()
                    logger.info(f"Committed {processed_in_db_count} DB updates for batch {current_batch_num}.")
                except Exception as e:
                    logger.error(f"Error committing DB updates for batch {current_batch_num}: {e}. Rolling back.", exc_info=True)
                    db.rollback()
                    successful_parses -= processed_in_db_count
                    failed_parses += processed_in_db_count
                    logger.warning(f"All {processed_in_db_count} items in DB transaction for batch {current_batch_num} are now considered failed due to commit error.")

        if i + DEFAULT_BATCH_SIZE < total_candidates_to_process:
            delay_multiplier = 1
            if parsed_results_from_ai is None or \
               (parsed_results_from_ai is not None and len(parsed_results_from_ai) != len(batch_metadata_for_ai)):
                delay_multiplier = 2
            actual_delay = INTER_BATCH_DELAY_SECONDS * delay_multiplier
            logger.info(f"Waiting {actual_delay} seconds before next batch...")
            time.sleep(actual_delay)

    logger.info(f"Batch resume parsing completed. Successful: {successful_parses}, Failed: {failed_parses}, Total considered: {total_candidates_to_process}")
    return {"successful": successful_parses, "failed": failed_parses, "total": total_candidates_to_process}


if __name__ == "__main__":
    process_all_candidates()
