from fastapi import Request, status
from fastapi.security.http import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse
from typing import Optional

from core.security import decode_access_token, TokenData

# Define paths that DO NOT require authentication
PUBLIC_PATHS_PREFIXES = [
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth",  # All routes under /api/v1/auth/ (e.g., /login, /register)
    "/",             # The root path
    "/api/v1/companies",
    "/api/v1/jobs/public",  # Public job endpoints for application forms
    "/api/v1/candidates",   # Public candidate creation
    "/api/v1/applications", # Public application creation
]

# Define paths that require authentication
AUTH_REQUIRED_PATHS_PREFIXES = [
    "/api/v1/companies/recruit_to",
    "/api/v1/companies/by_hr",
    "/api/v1/applications/employer-applications",
    "/api/v1/companies/candidates",
]

# HTTPBearer scheme for extracting token
# auto_error=False allows us to manually handle missing token or errors
bearer_scheme = HTTPBearer(auto_error=False)

def normalize_path(path: str) -> str:
    """Normalize path by removing trailing slash except for root path"""
    if path == "/" or path == "":
        return "/"
    return path.rstrip("/")

def path_matches_prefix(current_path: str, prefix: str) -> bool:
    """Check if current_path matches the prefix, handling trailing slashes consistently"""
    normalized_current = normalize_path(current_path)
    normalized_prefix = normalize_path(prefix)
    
    # Exact match for root path
    if normalized_prefix == "/" and normalized_current == "/":
        return True
    
    # For non-root paths, check if current path starts with prefix
    if normalized_prefix != "/":
        return (normalized_current == normalized_prefix or 
                normalized_current.startswith(normalized_prefix + "/"))
    
    return False

def get_token_data_from_request(request: Request) -> Optional[TokenData]:
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        return decode_access_token(token)
    return None

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request.state.user = None  # Initialize user in request state

        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response

        # Check if the current path is public
        is_public_path = False
        current_path = request.url.path

        for public_prefix in PUBLIC_PATHS_PREFIXES:
            if path_matches_prefix(current_path, public_prefix):
                is_public_path = True
                break
        
        # Special handling for /openapi.json if requested by /docs or /redoc for schema loading
        if normalize_path(current_path) == "/openapi.json":
            referer = request.headers.get("referer")
            if referer:
                if referer.endswith("/docs") or referer.endswith("/redoc"):
                    is_public_path = True
        
        print(f"current_path: {current_path}")
        
        # Check for auth-required paths (these override public paths)
        for auth_prefix in AUTH_REQUIRED_PATHS_PREFIXES:
            if path_matches_prefix(current_path, auth_prefix):
                print(f"auth_prefix: {auth_prefix}")
                is_public_path = False
                break

        token_data: Optional[TokenData] = get_token_data_from_request(request)

        if is_public_path:
            print(f"is_public_path: {is_public_path}")
            # For public paths, proceed without authentication enforcement
            if token_data:
                request.state.user = token_data
            response = await call_next(request)
            return response
        else:
            print(f"is_public_path: {is_public_path}")
            # For non-public paths, enforce authentication
            if not token_data:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated. Authorization header missing or invalid."},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            # Token is valid, attach user data to request state
            request.state.user = token_data
            response = await call_next(request)
            return response 
       