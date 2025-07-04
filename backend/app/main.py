import asyncio
import logging
from contextlib import asynccontextmanager
import os

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.database import create_db_and_tables, check_db_tables
from core.auth_middleware import AuthMiddleware
from core.config import settings
from contextlib import asynccontextmanager
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import (
    company,
    hr,
    recruiter_company_link,
    form_key,
    job,
    job_form_key_constraint,
    application,
    match,
    candidate,
    auth,
    interview,
    scripts,
    analytics,
    chatbot,
    ai_interviewer,
)
# from api.v1.endpoints import auth as auth_router

# Define a bearer scheme for Swagger UI.
# auto_error=False because our AuthMiddleware handles the actual enforcement.
# This is primarily for documentation and enabling the "Authorize" button.
swagger_ui_bearer_scheme = HTTPBearer(
    auto_error=False, bearerFormat="JWT", scheme_name="JWTBearerAuth"
)

# Import batch processing functions
from scripts.resume_parser_batch import process_all_candidates
from scripts.application_matcher_batch import process_all_applications
from services.otp_service import cleanup_expired_otps_task


# Global scheduler variable
scheduler = None
# Global OTP cleanup task
otp_cleanup_task = None
import logging

# Dedicated loggers for specific parts of main.py
scheduler_logger = logging.getLogger("api.scheduler")
lifespan_logger = logging.getLogger("api.lifespan")


def safe_process_all_candidates():
    """Wrapper function for resume parsing with error handling"""
    try:
        scheduler_logger.info(
            f"Starting scheduled resume parsing (Scheduler configured to UTC)."
        )
        result = process_all_candidates()
        scheduler_logger.info(f"Resume parsing completed: {result}")
    except Exception as e:
        scheduler_logger.error(f"Resume parsing failed: {str(e)}", exc_info=True)


def safe_process_all_applications():
    """Wrapper function for application matching with error handling"""
    try:
        scheduler_logger.info(
            f"Starting scheduled application matching (Scheduler configured to UTC)."
        )
        result = process_all_applications()
        scheduler_logger.info(f"Application matching completed: {result}")
    except Exception as e:
        scheduler_logger.error(f"Application matching failed: {str(e)}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler, otp_cleanup_task
    lifespan_logger.info("Application lifespan startup sequence initiated.")

    # Startup logic
    create_db_and_tables(drop=False)
    lifespan_logger.info("Database tables checked/created.")

    # Start OTP cleanup background task
    lifespan_logger.info("Starting OTP cleanup background task.")
    otp_cleanup_task = asyncio.create_task(cleanup_expired_otps_task())

    # Set up APScheduler if enabled
    if settings.ENABLE_BATCH_SCHEDULER:
        lifespan_logger.info(
            "Setting up batch processing scheduler as ENABLE_BATCH_SCHEDULER is true."
        )
        lifespan_logger.info(
            f"Resume parser interval: {settings.RESUME_PARSER_INTERVAL_MINUTES} minutes"
        )
        lifespan_logger.info(
            f"Application matcher interval: {settings.APPLICATION_MATCHER_INTERVAL_MINUTES} minutes"
        )

        scheduler = BackgroundScheduler()
        lifespan_logger.info("APScheduler initialized with UTC timezone.")

        # Add resume parsing job
        scheduler.add_job(
            safe_process_all_candidates,
            IntervalTrigger(minutes=settings.RESUME_PARSER_INTERVAL_MINUTES),
            id="resume_parser_job",
            name="Resume Parser Batch Job",
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,  # Combine multiple pending executions into one
            misfire_grace_time=300,  # Allow 5 minutes grace time for missed executions
        )

        # Add application matching job
        scheduler.add_job(
            safe_process_all_applications,
            IntervalTrigger(minutes=settings.APPLICATION_MATCHER_INTERVAL_MINUTES),
            id="application_matcher_job",
            name="Application Matcher Batch Job",
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,  # Combine multiple pending executions into one
            misfire_grace_time=300,  # Allow 5 minutes grace time for missed executions
        )

        scheduler.start()
        lifespan_logger.info("Batch processing scheduler started successfully.")
    else:
        lifespan_logger.info(
            "Batch processing scheduler is disabled (ENABLE_BATCH_SCHEDULER is false)."
        )

    yield  # Control passes to the application here

    # Shutdown logic
    lifespan_logger.info("Application lifespan shutdown sequence initiated.")
    if otp_cleanup_task and not otp_cleanup_task.done():
        lifespan_logger.info("Shutting down OTP cleanup task.")
        otp_cleanup_task.cancel()
        try:
            await otp_cleanup_task
        except asyncio.CancelledError:
            lifespan_logger.info("OTP cleanup task cancelled successfully.")
        except Exception as e:
            lifespan_logger.error(
                f"Error during OTP cleanup task shutdown: {e}", exc_info=True
            )

    if scheduler and scheduler.running:
        lifespan_logger.info("Shutting down batch processing scheduler.")
        try:
            scheduler.shutdown(wait=True)
            lifespan_logger.info("Scheduler shutdown complete.")
        except Exception as e:
            lifespan_logger.error(
                f"Error during scheduler shutdown: {e}", exc_info=True
            )
    lifespan_logger.info("Application shutdown complete.")


app = FastAPI(
    title="Matching API",
    description="API for the matching application with JWT Bearer authentication.",
    version="1.0.0",
    lifespan=lifespan,
)

# Create a router for all API v1 endpoints that need bearer auth for Swagger
api_v1_router = APIRouter(dependencies=[Depends(swagger_ui_bearer_scheme)])

# CORS Configuration
if settings.DEBUG_MODE and settings.CORS_ALLOWED_ORIGINS == ["*"]:
    lifespan_logger.warning(
        "CORS allow_origins set to '*' because DEBUG_MODE is true and CORS_ALLOWED_ORIGINS is not set."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,  # Adjust as needed, often True for JWT/cookie auth
    allow_methods=["*"],  # Or specify methods: ["GET", "POST", "PUT", "DELETE"]
    allow_headers=["*"],  # Or specify headers
)
# Include AI interviewer router BEFORE auth middleware (no auth required for candidates)
app.include_router(ai_interviewer.router, prefix="/api/v1/ai-interviewer", tags=["ai-interviewer"])

# Add AuthMiddleware - this should generally be after CORS but before most route-specific logic
app.add_middleware(AuthMiddleware)

# --- Logging Setup for FastAPI app ---
# Using uvicorn's default logging for now, which is configured via uvicorn.run()
# For more advanced logging, one might integrate structlog or custom logging middleware.
# The batch scripts have their own loggers.
import logging  # Added

logger = logging.getLogger("api")  # General API logger
if settings.DEBUG_MODE:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
# Ensure uvicorn loggers also respect this level if needed, though uvicorn.run controls its own.


# --- Custom Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the detailed error for server-side debugging
    logger.error(
        f"Validation error for request: {request.method} {request.url}\n"
        f"Details: {exc.errors()}",
        exc_info=True,  # Includes traceback
    )
    # Return a Pydantic-like error response
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTP exception for request: {request.method} {request.url}\n"
        f"Status Code: {exc.status_code}, Detail: {exc.detail}",
        exc_info=True,  # Includes traceback for unexpected HTTPExceptions
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # This will catch any unhandled exceptions (500 errors)
    error_id = os.urandom(8).hex()  # Generate a unique error ID
    logger.critical(
        f"Unhandled exception (Error ID: {error_id}) for request: {request.method} {request.url}",
        exc_info=True,  # Includes traceback
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error. Please contact support.",
            "error_id": error_id,  # Client can provide this ID for faster debugging
        },
    )


# Include routers
api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(company.router, prefix="/companies", tags=["companies"])
api_v1_router.include_router(hr.router, prefix="/hrs", tags=["hrs"])
api_v1_router.include_router(
    recruiter_company_link.router,
    prefix="/recruiter_company_links",
    tags=["recruiter_company_links"],
)
api_v1_router.include_router(form_key.router, prefix="/form_keys", tags=["form_keys"])
api_v1_router.include_router(job.router, prefix="/jobs", tags=["jobs"])
api_v1_router.include_router(
    job_form_key_constraint.router,
    prefix="/job_form_key_constraints",
    tags=["job_form_key_constraints"],
)
api_v1_router.include_router(
    application.router, prefix="/applications", tags=["applications"]
)
api_v1_router.include_router(match.router, prefix="/matches", tags=["matches"])
api_v1_router.include_router(
    interview.router, prefix="/interviews", tags=["interviews"]
)
api_v1_router.include_router(
    candidate.router, prefix="/candidates", tags=["candidates"]
)
api_v1_router.include_router(
    scripts.router, prefix="/admin/scripts", tags=["admin-scripts"]
)
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# Include the v1 router into the main app
app.include_router(api_v1_router, prefix="/api/v1")

# Include the chatbot router separately since it uses WebSocket protocol
app.include_router(chatbot.router, prefix="/api/v1", tags=["chatbot"])


@app.get("/", summary="Root endpoint for API health and info.")
async def root():
    """
    Provides basic information about the API.
    - **version**: The current version of the API.
    - **debug_mode**: Indicates if the API is running in debug mode.
    - **scheduler_status**: The status of the background task scheduler.
    """
    scheduler_status = "Not running"
    if settings.ENABLE_BATCH_SCHEDULER:
        if scheduler and scheduler.running:
            jobs = scheduler.get_jobs()
            job_details = [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time),
                }
                for job in jobs
            ]
            scheduler_status = {
                "status": "Running",
                "jobs": job_details,
            }
        else:
            scheduler_status = "Enabled but not running"

    return {
        "version": app.version,
        "debug_mode": settings.DEBUG_MODE,
        "scheduler_status": scheduler_status,
        "message": "Welcome to the Matching API. See /docs for documentation.",
    }


if __name__ == "__main__":
    # For local development, run the app with uvicorn
    # In production, this would be run by a process manager like Gunicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8017,
        reload=settings.DEBUG_MODE,
        log_level="debug" if settings.DEBUG_MODE else "info",
    )
