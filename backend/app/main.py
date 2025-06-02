from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPBearer
import traceback

from core.database import create_db_and_tables, check_db_tables
from core.auth_middleware import AuthMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware
from api.v1.endpoints import company, hr, recruiter_company_link, form_key, job, job_form_key_constraint, application, match, candidate, auth, interview
# from api.v1.endpoints import auth as auth_router

# Import batch processing function
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
from resume_parser_batch import process_all_candidates

# Get debug mode from environment variable, default to True
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

# Define a bearer scheme for Swagger UI. 
# auto_error=False because our AuthMiddleware handles the actual enforcement.
# This is primarily for documentation and enabling the "Authorize" button.
swagger_ui_bearer_scheme = HTTPBearer(auto_error=False, bearerFormat="JWT", scheme_name="JWTBearerAuth")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    # create_db_and_tables()
    all_exist, missing_tables = check_db_tables()
    if not all_exist:
        print("Creating database tables...")
        create_db_and_tables()
    else:
        print(f"Database already exists. Missing tables: {missing_tables}")
    
    yield  # Control passes to the application here

    # Shutdown logic (optional)
    # e.g., cleanup, close DB connections

app = FastAPI(
    title="Matching API",
    description="API for the matching application with JWT Bearer authentication.",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(swagger_ui_bearer_scheme)] # Add as global dependency for Swagger UI
)

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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(company.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(hr.router, prefix="/api/v1/hrs", tags=["hrs"])
app.include_router(recruiter_company_link.router, prefix="/api/v1/recruiter_company_links", tags=["recruiter_company_links"])
app.include_router(form_key.router, prefix="/api/v1/form_keys", tags=["form_keys"])
app.include_router(job.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(job_form_key_constraint.router, prefix="/api/v1/job_form_key_constraints", tags=["job_form_key_constraints"])
app.include_router(application.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(match.router, prefix="/api/v1/matches", tags=["matches"])
app.include_router(interview.router, prefix="/api/v1/interviews", tags=["interviews"])
app.include_router(candidate.router, prefix="/api/v1/candidates", tags=["candidates"])

@app.get("/", summary="Root endpoint for API health and info")
async def root():
    return {
        "message": "Welcome to the Matching API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "debug_mode": DEBUG_MODE
    }

@app.post("/api/v1/admin/batch-parse-resumes", summary="Run batch resume parsing")
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
        "status": "processing"
    }

@app.get("/api/v1/admin/batch-parse-resumes/status", summary="Get batch parsing status")
async def get_batch_parsing_status():
    """
    Get the current status of candidates that need resume parsing.
    """
    try:
        # Import here to avoid circular imports
        from scripts.resume_parser_batch import get_candidates_without_parsed_resume
        
        candidates = get_candidates_without_parsed_resume()
        
        return {
            "candidates_needing_parsing": len(candidates),
            "status": "ready" if candidates else "all_processed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking batch status: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8017,
        log_level="debug" if DEBUG_MODE else "info",
        # reload=DEBUG_MODE
    )