from fastapi import FastAPI, Request, HTTPException, Depends, APIRouter
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.database import create_db_and_tables, check_db_tables
from core.auth_middleware import AuthMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
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
)
# from api.v1.endpoints import auth as auth_router

# Get debug mode from environment variable, default to True
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

# Get scheduler configuration from environment variables
RESUME_PARSER_INTERVAL_MINUTES = int(os.getenv("RESUME_PARSER_INTERVAL_MINUTES", "10"))  # Default: 30 minutes
APPLICATION_MATCHER_INTERVAL_MINUTES = int(os.getenv("APPLICATION_MATCHER_INTERVAL_MINUTES", "10"))  # Default: 30 minutes
ENABLE_BATCH_SCHEDULER = os.getenv("ENABLE_BATCH_SCHEDULER", "True").lower() == "true"

# Define a bearer scheme for Swagger UI.
# auto_error=False because our AuthMiddleware handles the actual enforcement.
# This is primarily for documentation and enabling the "Authorize" button.
swagger_ui_bearer_scheme = HTTPBearer(
    auto_error=False, bearerFormat="JWT", scheme_name="JWTBearerAuth"
)

# Import batch processing functions
from scripts.resume_parser_batch import process_all_candidates
from scripts.application_matcher_batch import process_all_applications


# Global scheduler variable
scheduler = None

def safe_process_all_candidates():
    """Wrapper function for resume parsing with error handling"""
    try:
        print(f"[Scheduler] Starting scheduled resume parsing at {os.getenv('TZ', 'UTC')} time")
        result = process_all_candidates()
        print(f"[Scheduler] Resume parsing completed: {result}")
    except Exception as e:
        print(f"[Scheduler] Resume parsing failed: {str(e)}")
        import traceback
        print(f"[Scheduler] Full traceback: {traceback.format_exc()}")

def safe_process_all_applications():
    """Wrapper function for application matching with error handling"""
    try:
        print(f"[Scheduler] Starting scheduled application matching at {os.getenv('TZ', 'UTC')} time")
        result = process_all_applications()
        print(f"[Scheduler] Application matching completed: {result}")
    except Exception as e:
        print(f"[Scheduler] Application matching failed: {str(e)}")
        import traceback
        print(f"[Scheduler] Full traceback: {traceback.format_exc()}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    
    # Startup logic
    create_db_and_tables()

    # Set up APScheduler if enabled
    if ENABLE_BATCH_SCHEDULER:
        print(f"[Scheduler] Setting up batch processing scheduler")
        print(f"[Scheduler] Resume parser interval: {RESUME_PARSER_INTERVAL_MINUTES} minutes")
        print(f"[Scheduler] Application matcher interval: {APPLICATION_MATCHER_INTERVAL_MINUTES} minutes")
        
        scheduler = BackgroundScheduler()
        
        # Add resume parsing job
        scheduler.add_job(
            safe_process_all_candidates,
            IntervalTrigger(minutes=RESUME_PARSER_INTERVAL_MINUTES),
            id='resume_parser_job',
            name='Resume Parser Batch Job',
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,    # Combine multiple pending executions into one
            misfire_grace_time=300  # Allow 5 minutes grace time for missed executions
        )
        
        # Add application matching job
        scheduler.add_job(
            safe_process_all_applications,
            IntervalTrigger(minutes=APPLICATION_MATCHER_INTERVAL_MINUTES),
            id='application_matcher_job',
            name='Application Matcher Batch Job',
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,    # Combine multiple pending executions into one
            misfire_grace_time=300  # Allow 5 minutes grace time for missed executions
        )
        
        scheduler.start()
        print(f"[Scheduler] Batch processing scheduler started successfully")
    else:
        print(f"[Scheduler] Batch processing scheduler is disabled")

    yield  # Control passes to the application here

    # Shutdown logic
    if scheduler and scheduler.running:
        print(f"[Scheduler] Shutting down batch processing scheduler")
        scheduler.shutdown(wait=True)
        print(f"[Scheduler] Scheduler shutdown complete")


app = FastAPI(
    title="Matching API",
    description="API for the matching application with JWT Bearer authentication.",
    version="1.0.0",
    lifespan=lifespan,
)

# Create a router for all API v1 endpoints that need bearer auth for Swagger
api_v1_router = APIRouter(dependencies=[Depends(swagger_ui_bearer_scheme)])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add AuthMiddleware - this should generally be after CORS but before most route-specific logic
app.add_middleware(AuthMiddleware)

# # Add error traceback middleware
# app.add_middleware(
#     ErrorTracebackMiddleware,
#     include_traceback=True,
#     debug_mode=DEBUG_MODE
# # )
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     tb = traceback.format_exc()
#     print(f"\n=== Validation Error ===\nRequest: {request.method} {request.url}\nErrors: {exc.errors()}\nTraceback:\n{tb}\n========================\n")
#     content = {
#         "detail": exc.errors(),
#         "status_code": 422,
#         "path": str(request.url),
#         "traceback": tb.split("\n") if DEBUG_MODE else "Traceback available in debug mode."
#     }
#     return JSONResponse(status_code=422, content=content)


# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     tb = traceback.format_exc()
#     print(f"\n=== HTTP Exception ===\nRequest: {request.method} {request.url}\nError: {exc.detail}\nStatus Code: {exc.status_code}\nTraceback:\n{tb}\n======================\n")
#     content = {
#         "detail": exc.detail,
#         "status_code": exc.status_code,
#         "path": str(request.url),
#         "traceback": tb.split("\n") if DEBUG_MODE else "Traceback available in debug mode."
#     }
#     return JSONResponse(status_code=exc.status_code, content=content)


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


@app.get("/", summary="Root endpoint for API health and info")
async def root():
    scheduler_info = {
        "enabled": ENABLE_BATCH_SCHEDULER,
        "resume_parser_interval_minutes": RESUME_PARSER_INTERVAL_MINUTES,
        "application_matcher_interval_minutes": APPLICATION_MATCHER_INTERVAL_MINUTES,
    }
    
    return {
        "message": "Welcome to the Matching API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "debug_mode": DEBUG_MODE,
        "batch_scheduler": scheduler_info,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8017,
        log_level="debug" if DEBUG_MODE else "info",
        # reload=DEBUG_MODE
    )
