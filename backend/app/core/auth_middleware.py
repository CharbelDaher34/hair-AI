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
]

# HTTPBearer scheme for extracting token
# auto_error=False allows us to manually handle missing token or errors
bearer_scheme = HTTPBearer(auto_error=False)

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
            if public_prefix == "/" and current_path == "/": # Exact match for root
                is_public_path = True
                break
            # Check if current_path starts with public_prefix or is exactly public_prefix (for /docs, /openapi.json etc)
            if public_prefix != "/" and (current_path.startswith(public_prefix + "/") or current_path == public_prefix):
                is_public_path = True
                break
        
        # Special handling for /openapi.json if requested by /docs or /redoc for schema loading
        if current_path == "/openapi.json":
            referer = request.headers.get("referer")
            if referer:
                if referer.endswith("/docs") or referer.endswith("/redoc"):
                    is_public_path = True

        if is_public_path:
            print(f"is_public_path: {is_public_path}")
            # For public paths, proceed without authentication enforcement
            response = await call_next(request)
            return response
        else:
            print(f"is_public_path: {is_public_path}")
            # For non-public paths, enforce authentication
            credentials: Optional[HTTPAuthorizationCredentials] = await bearer_scheme(request)
            # print(f"credentials: {credentials}")
            # print(request.headers.get("Authorization"))
            if not credentials:
                # Fallback: try to extract token manually
                auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ", 1)[1]
                    
                    token_data: Optional[TokenData] = decode_access_token(token)
                    
                    if token_data is None:
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"detail": "Invalid or expired token, or insufficient permissions."},
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                    
                    # Token is valid, attach user data to request state
                    request.state.user = token_data
                    response = await call_next(request)
                    return response
                
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Not authenticated. Authorization header missing or invalid."},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token = credentials.credentials
            token_data: Optional[TokenData] = decode_access_token(token)
            # decode_access_token itself checks for user_type == 'hr' and presence of employer_id
            if token_data is None: 
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token, or insufficient permissions."},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Token is valid, attach user data to request state
            request.state.user = token_data
            
            response = await call_next(request)
            return response 