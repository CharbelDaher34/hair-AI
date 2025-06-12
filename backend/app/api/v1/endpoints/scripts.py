from fastapi import APIRouter, BackgroundTasks, HTTPException
import os
import sys

# Add the scripts directory to the path so we can import from it
from scripts.resume_parser_batch import (
    process_all_candidates,
    get_candidates_without_parsed_resume,
)
from scripts.application_matcher_batch import (
    process_all_applications,
    get_applications_without_matches,
)

router = APIRouter()


@router.post("/batch-parse-resumes", summary="Run batch resume parsing")
async def run_batch_resume_parsing(background_tasks: BackgroundTasks):
    """
    Run batch processing to parse all candidate resumes that haven't been processed yet.
    This runs in the background and returns immediately.
    """

    def run_batch_processing():
        try:
            result = process_all_candidates()
            print(f"[API] Batch processing completed: {result}")
        except Exception as e:
            print(f"[API] Batch processing failed: {str(e)}")
            import traceback

            print(f"[API] Full traceback: {traceback.format_exc()}")

    background_tasks.add_task(run_batch_processing)

    return {
        "message": "Batch resume parsing started in background",
        "status": "processing",
    }


@router.get("/batch-parse-resumes/status", summary="Get batch parsing status")
async def get_batch_parsing_status():
    """
    Get the current status of candidates that need resume parsing.
    """
    try:
        candidates = get_candidates_without_parsed_resume()

        return {
            "candidates_needing_parsing": len(candidates),
            "status": "ready" if candidates else "all_processed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking batch status: {str(e)}"
        )


@router.post("/batch-match-applications", summary="Run batch application matching")
async def run_batch_application_matching(background_tasks: BackgroundTasks):
    """
    Run batch processing to create matches for all applications that don't have matches yet.
    This runs in the background and returns immediately.
    """

    def run_batch_matching():
        try:
            result = process_all_applications()
            print(f"[API] Batch matching completed: {result}")
        except Exception as e:
            print(f"[API] Batch matching failed: {str(e)}")
            import traceback

            print(f"[API] Full traceback: {traceback.format_exc()}")

    background_tasks.add_task(run_batch_matching)

    return {
        "message": "Batch application matching started in background",
        "status": "processing",
    }


@router.get("/batch-match-applications/status", summary="Get batch matching status")
async def get_batch_matching_status():
    """
    Get the current status of applications that need matching.
    """
    try:
        applications = get_applications_without_matches()

        return {
            "applications_needing_matching": len(applications),
            "status": "ready" if applications else "all_processed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking batch matching status: {str(e)}"
        )
