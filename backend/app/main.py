from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback

from core.database import create_db_and_tables, check_db_tables
from core.middlewares import ErrorTracebackMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

from api.v1.endpoints import company, hr, recruiter_company_link, form_key, job, job_form_key_constraint, application, match, candidate

# Get debug mode from environment variable, default to True
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
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
    description="API for the matching application",
    version="1.0.0",
    lifespan=lifespan
)

# # Add error traceback middleware
# app.add_middleware(
#     ErrorTracebackMiddleware,
#     include_traceback=True,
#     debug_mode=DEBUG_MODE
# )
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    tb = traceback.format_exc()
    print(f"\n=== Validation Error ===\nRequest: {request.method} {request.url}\nErrors: {exc.errors()}\nTraceback:\n{tb}\n========================\n")
    content = {
        "detail": exc.errors(),
        "body": exc.body,
        "status_code": 422,
        "path": str(request.url),
        "traceback": tb.split("\n")
    }
    return JSONResponse(status_code=422, content=content)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    tb = traceback.format_exc()
    print(f"\n=== HTTP Exception ===\nRequest: {request.method} {request.url}\nError: {exc.detail}\nTraceback:\n{tb}\n======================\n")
    content = {
        "detail": exc.detail,
        "status_code": exc.status_code,
        "path": str(request.url),
        "traceback": tb.split("\n")
    }
    return JSONResponse(status_code=exc.status_code, content=content)


# Include routers
app.include_router(company.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(hr.router, prefix="/api/v1/hrs", tags=["hrs"])
app.include_router(recruiter_company_link.router, prefix="/api/v1/recruiter-company-links", tags=["recruiter-company-links"])
app.include_router(form_key.router, prefix="/api/v1/form-keys", tags=["form-keys"])
app.include_router(job.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(job_form_key_constraint.router, prefix="/api/v1/job-form-key-constraints", tags=["job-form-key-constraints"])
app.include_router(application.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(match.router, prefix="/api/v1/matches", tags=["matches"])
app.include_router(candidate.router, prefix="/api/v1/candidates", tags=["candidates"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Matching API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "debug_mode": DEBUG_MODE
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8017,
        log_level="debug" if DEBUG_MODE else "info"
    )