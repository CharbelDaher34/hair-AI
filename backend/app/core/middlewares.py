import traceback
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class ErrorTracebackMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        include_traceback: bool = True,
        debug_mode: bool = True
    ):
        super().__init__(app)
        self.include_traceback = include_traceback
        self.debug_mode = debug_mode

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            print("Request received")
            return await call_next(request)
        except Exception as e:
            # Get the full traceback
            tb = traceback.format_exc()
            
            # Print the error and traceback for debugging
            print("\n=== Error Traceback ===")
            print(f"Request: {request.method} {request.url}")
            print(f"Error: {str(e)}")
            print("Traceback:")
            print(tb)
            print("=====================\n")

            # Prepare error response
            error_response = {
                "detail": str(e),
                "status_code": 500,
                "path": str(request.url)
            }

            # Include traceback in response only if debug mode is enabled
            if self.debug_mode and self.include_traceback:
                error_response["traceback"] = tb.split("\n")

            return JSONResponse(
                status_code=500,
                content=error_response
            )
