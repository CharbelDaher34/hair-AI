from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlmodel import (
    Session,
)  # Kept for potential use with CRUD, though not directly in this file now

from core.config import settings
# Removed HR model import, assuming it's handled by CRUD
# Removed HR CRUD imports, assuming they are used in the router directly

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    user_type: Optional[str] = None  # Should be 'hr'
    id: Optional[int] = None
    employer_id: Optional[int] = None


# Removed GoogleUserInfo class


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: Optional[str] = payload.get("sub")
        user_type: Optional[str] = payload.get("user_type")
        user_id: Optional[int] = payload.get("id")
        employer_id: Optional[int] = payload.get("employer_id")
        if email is None or user_type != "hr" or user_id is None or employer_id is None:
            # Consider if employer_id is strictly required for all token types or just HR
            return None
        return TokenData(
            email=email, user_type=user_type, id=user_id, employer_id=employer_id
        )
    except JWTError:
        return None


# Removed get_google_user_info
# Removed exchange_google_code_for_token
# Removed get_google_auth_url

# Removed placeholder CRUD functions for HR as they should be directly used in the router
# or through a dedicated CRUD layer imported there.


def create_interview_review_token(interview_id: int, interviewer_id: int) -> str:
    """Create a secure token for interview review form access"""
    import secrets
    from datetime import datetime, timedelta

    # Create payload with interview and interviewer info plus expiration
    payload = {
        "interview_id": interview_id,
        "interviewer_id": interviewer_id,
        "exp": datetime.utcnow() + timedelta(days=30),  # Token valid for 30 days
        "type": "interview_review",
    }

    # Create JWT token
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def verify_interview_review_token(token: str) -> dict:
    """Verify and decode interview review token"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Check if token is for interview review
        if payload.get("type") != "interview_review":
            raise HTTPException(status_code=401, detail="Invalid token type")

        # Check expiration
        if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
            raise HTTPException(status_code=401, detail="Token has expired")

        return {
            "interview_id": payload["interview_id"],
            "interviewer_id": payload["interviewer_id"],
        }
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
