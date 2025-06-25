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
    get_applications_needing_match_grouped_by_job,
)

router = APIRouter()


# Import scheduler from main module (will be set during app startup)
def get_scheduler():
    """Get the scheduler instance from main module"""
    try:
        from main import scheduler

        return scheduler
    except ImportError:
        return None


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
        applications_by_job = get_applications_needing_match_grouped_by_job()
        total_applications = sum(len(apps) for apps in applications_by_job.values())

        return {
            "applications_needing_matching": total_applications,
            "jobs_with_applications": len(applications_by_job),
            "status": "ready" if total_applications > 0 else "all_processed",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking batch matching status: {str(e)}"
        )


@router.get("/scheduler/status", summary="Get scheduler status")
async def get_scheduler_status():
    """
    Get the current status of the batch processing scheduler.
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            return {
                "scheduler_enabled": False,
                "status": "disabled",
                "message": "Scheduler is not enabled or not available",
            }

        jobs = scheduler.get_jobs()
        job_info = []

        for job in jobs:
            job_info.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                    "trigger": str(job.trigger),
                }
            )

        return {
            "scheduler_enabled": True,
            "status": "running" if scheduler.running else "stopped",
            "jobs": job_info,
            "total_jobs": len(jobs),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting scheduler status: {str(e)}"
        )


@router.post(
    "/scheduler/trigger-resume-parsing", summary="Manually trigger resume parsing job"
)
async def trigger_resume_parsing():
    """
    Manually trigger the resume parsing job immediately.
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            raise HTTPException(
                status_code=400, detail="Scheduler is not enabled or not available"
            )

        # Trigger the job immediately
        job = scheduler.get_job("resume_parser_job")
        if job:
            scheduler.modify_job("resume_parser_job", next_run_time=None)
            return {
                "message": "Resume parsing job triggered successfully",
                "job_id": "resume_parser_job",
                "status": "triggered",
            }
        else:
            raise HTTPException(
                status_code=404, detail="Resume parsing job not found in scheduler"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error triggering resume parsing job: {str(e)}"
        )


@router.post(
    "/scheduler/trigger-application-matching",
    summary="Manually trigger application matching job",
)
async def trigger_application_matching():
    """
    Manually trigger the application matching job immediately.
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            raise HTTPException(
                status_code=400, detail="Scheduler is not enabled or not available"
            )

        # Trigger the job immediately
        job = scheduler.get_job("application_matcher_job")
        if job:
            scheduler.modify_job("application_matcher_job", next_run_time=None)
            return {
                "message": "Application matching job triggered successfully",
                "job_id": "application_matcher_job",
                "status": "triggered",
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Application matching job not found in scheduler",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error triggering application matching job: {str(e)}",
        )
