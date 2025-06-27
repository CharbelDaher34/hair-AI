from fastapi import Request, HTTPException, status
from core.security import TokenData
from typing import Optional


def get_current_user(request: Request, required: bool = True) -> Optional[TokenData]:
    """Retrieve authenticated user object injected by AuthMiddleware.

    Args:
        request: FastAPI request containing `state.user` set by middleware.
        required: If True, raise HTTPException 401 when user is missing. If False,
                  just return None when user not found.

    Returns:
        TokenData | None
    """
    current_user: Optional[TokenData] = getattr(request.state, "user", None)
    if required and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return current_user
