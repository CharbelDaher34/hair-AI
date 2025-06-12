from fastapi import FastAPI, Request, HTTPException, Depends, APIRouter
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

# Define a bearer scheme for Swagger UI.
# auto_error=False because our AuthMiddleware handles the actual enforcement.
# This is primarily for documentation and enabling the "Authorize" button.
swagger_ui_bearer_scheme = HTTPBearer(
    auto_error=False, bearerFormat="JWT", scheme_name="JWTBearerAuth"
)


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
    return {
        "message": "Welcome to the Matching API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "debug_mode": DEBUG_MODE,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8017,
        log_level="debug" if DEBUG_MODE else "info",
        # reload=DEBUG_MODE
    )
