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
from datetime import datetime
from typing import List

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, text
from core.database import engine
from crud import crud_candidate
from models.models import Candidate
from utils.file_utils import get_resume_file_path
from schemas.candidate_pydantic import Candidate as resume_data
from services.resume_upload import ResumeParserClient


def parse_resume_for_candidate(candidate_id: int, resume_file_path: str, max_retries: int = 3) -> bool:
    """
    Parse resume for a single candidate.
    
    Args:
        candidate_id: ID of the candidate
        resume_file_path: Path to the saved resume file
        max_retries: Maximum number of retry attempts
        
    Returns:
        bool: True if successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            print(f"[Batch] Processing candidate {candidate_id} (attempt {attempt + 1}/{max_retries})")
            
            # Ensure the resume_file_path is absolute for the parser client
            absolute_resume_file_path = os.path.abspath(resume_file_path)
            print(f"[Batch] Absolute resume file path: {absolute_resume_file_path}")
            
            # Verify file exists before parsing
            if not os.path.exists(absolute_resume_file_path):
                print(f"[Batch] Resume file not found: {absolute_resume_file_path}")
                return False
            
            # Use ResumeParserClient to parse the resume
            system_prompt = "Extract structured information from resumes. Focus on contact details, skills, and work experience."
            schema = resume_data.model_json_schema()
            
            print(f"[Batch] Creating parser client for candidate {candidate_id}")
            parser_client = ResumeParserClient(system_prompt, schema, [absolute_resume_file_path])
            
            print(f"[Batch] Starting parsing for candidate {candidate_id}")
            parsed_result = parser_client.parse()
            
            print(f"[Batch] Parsing completed for candidate {candidate_id}")
            print(f"[Batch] Parsed result type: {type(parsed_result)}")
            
            if parsed_result is None:
                print(f"[Batch] Parsing returned None for candidate {candidate_id} - API may have failed")
                if attempt < max_retries - 1:
                    print(f"[Batch] Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                else:
                    print(f"[Batch] Max retries reached for candidate {candidate_id}")
                    return False
            
            if isinstance(parsed_result, dict):
                print(f"[Batch] Parsed resume result keys for candidate {candidate_id}: {list(parsed_result.keys())}")
            else:
                print(f"[Batch] Unexpected result type for candidate {candidate_id}: {type(parsed_result)}")
            
            # Update candidate with parsed resume data only if we have valid results
            if parsed_result:
                print(f"[Batch] Updating database for candidate {candidate_id}")
                with Session(engine) as db:
                    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
                    if candidate:
                        crud_candidate.update_candidate(
                            db=db,
                            db_candidate=candidate,
                            candidate_in={"parsed_resume": parsed_result}
                        )
                        print(f"[Batch] Successfully updated candidate {candidate_id} with parsed resume data")
                        return True
                    else:
                        print(f"[Batch] Candidate {candidate_id} not found for resume parsing update")
                        return False
            else:
                print(f"[Batch] No valid parsing results for candidate {candidate_id} - skipping database update")
                return False
                    
        except Exception as parse_err:
            print(f"[Batch] Error parsing resume for candidate {candidate_id} (attempt {attempt + 1}): {str(parse_err)}")
            print(f"[Batch] Error type: {type(parse_err)}")
            
            if attempt < max_retries - 1:
                print(f"[Batch] Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"[Batch] Max retries reached for candidate {candidate_id}")
                import traceback
                print(f"[Batch] Full traceback: {traceback.format_exc()}")
                return False
    
    return False


def get_candidates_without_parsed_resume() -> List[Candidate]:
    """
    Get all candidates that don't have parsed resume data and have a resume file.
    
    Returns:
        List of candidates that need resume parsing
    """
    with Session(engine) as db:
        # Query candidates where parsed_resume is None or empty and resume_url is not None
        # Use text() for proper JSON handling in PostgreSQL
        statement = select(Candidate).where(
            text("(parsed_resume IS NULL OR parsed_resume::text = '{}' OR parsed_resume::text = 'null')") &
            (Candidate.resume_url.is_not(None))
        )
        candidates = db.exec(statement).all()
        
        # Filter candidates that actually have resume files
        candidates_with_files = []
        for candidate in candidates:
            resume_path = get_resume_file_path(candidate.id)
            if resume_path:
                candidates_with_files.append(candidate)
            else:
                print(f"[Batch] Candidate {candidate.id} has resume_url but no file found")
        
        return candidates_with_files


def process_all_candidates():
    """
    Process all candidates that need resume parsing.
    
    Returns:
        dict: Results summary with successful and failed counts
    """
    print(f"[Batch] Starting batch resume parsing at {datetime.now()}")
    
    candidates = get_candidates_without_parsed_resume()
    print(f"[Batch] Found {len(candidates)} candidates that need resume parsing")
    
    if not candidates:
        print("[Batch] No candidates to process")
        return {"successful": 0, "failed": 0, "total": 0}
    
    successful = 0
    failed = 0
    
    for i, candidate in enumerate(candidates, 1):
        print(f"\n[Batch] Processing candidate {i}/{len(candidates)}: {candidate.full_name} (ID: {candidate.id})")
        
        resume_path = get_resume_file_path(candidate.id)
        if not resume_path:
            print(f"[Batch] No resume file found for candidate {candidate.id}")
            failed += 1
            continue
        
        success = parse_resume_for_candidate(candidate.id, resume_path)
        if success:
            successful += 1
            print(f"[Batch] ✅ Successfully processed candidate {candidate.id}")
        else:
            failed += 1
            print(f"[Batch] ❌ Failed to process candidate {candidate.id}")
        
        # Add a small delay between candidates to avoid overwhelming the AI service
        if i < len(candidates):
            print("[Batch] Waiting 2 seconds before next candidate...")
            time.sleep(2)
    
    print(f"\n[Batch] Batch processing completed at {datetime.now()}")
    print(f"[Batch] Results: {successful} successful, {failed} failed")
    
    return {"successful": successful, "failed": failed, "total": len(candidates)}


if __name__ == "__main__":
    process_all_candidates() 