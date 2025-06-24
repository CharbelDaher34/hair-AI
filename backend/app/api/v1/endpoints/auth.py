from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  # For form data
from sqlmodel import Session
import time # time module is imported but not used. Consider removing if truly unused.
import logging # Added
from core.database import get_session
from core.security import (
    create_access_token,
    verify_password,
    Token,
    # get_password_hash is used in crud_hr, not directly here anymore
)

# Assuming your CRUD functions are structured like this. Adjust path if necessary.
from crud.crud_hr import (
    get_hr_by_email,
    create_hr as crud_create_hr,
)  # Aliased to avoid conflict
from models.models import HR # HR model for type hinting, HRBase not directly used here
from schemas import HRCreate

router = APIRouter()
logger = logging.getLogger(__name__) # Logger for this router


@router.post(
    "/register",
    response_model=Token,
    summary="HR Register and Get Token",
    status_code=status.HTTP_201_CREATED,
)
async def register_hr_and_get_token(
    form_data: HRCreate, db: Session = Depends(get_session)
):
    """
    Registers an HR user and returns user details along with an access token.
    The password in HRCreate is plain text and will be hashed by crud_create_hr.
    """
    logger.info(f"Attempting to register HR with email: {form_data.email}")

    # Check if user already exists
    db_hr_check = get_hr_by_email(db, email=form_data.email)
    if db_hr_check:
        logger.warning(f"Registration failed for email {form_data.email}: Email already registered.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Sensitive data like form_data.password should not be logged directly.
    # logging.debug(f"HRCreate form data (excluding password): {form_data.model_dump(exclude={'password'})}")
    # Password hashing is handled by crud_create_hr

    created_hr_user: Optional[HR] = crud_create_hr(db=db, hr_in=form_data)

    if not created_hr_user:
        logger.error(f"Failed to create HR user for email: {form_data.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create HR user.",
        )

    access_token = create_access_token(
        data={
            "sub": created_hr_user.email,
            "user_type": "hr",
            "id": created_hr_user.id,
            "employer_id": created_hr_user.employer_id, # Assuming employer_id is mandatory and set
        }
    )
    logger.info(f"HR user {created_hr_user.email} registered successfully and token generated.")
    return Token(
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/login", response_model=Token, summary="HR Login for Access Token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)
):
    """
    Logs in an HR user with email (username field) and password.
    Returns an access token.
    """
    logger.info(f"Login attempt for username (email): {form_data.username}")
    hr_user: Optional[HR] = get_hr_by_email(db=db, email=form_data.username)

    if not hr_user:
        logger.warning(f"Login failed for {form_data.username}: User not found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the plain password against the stored hashed password
    if not verify_password(form_data.password, hr_user.password):
        logger.warning(f"Login failed for {form_data.username}: Incorrect password.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not hr_user.id or not hasattr(hr_user, "employer_id") or not hr_user.employer_id:
        logger.error(f"Login successful for {hr_user.email}, but user data is incomplete (ID: {hr_user.id}, EmployerID: {getattr(hr_user, 'employer_id', 'N/A')}). Cannot issue token.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User data is incomplete (missing ID or employer_id).",
        )

    access_token = create_access_token(
        data={
            "sub": hr_user.email,
            "user_type": "hr", # TODO: Consider Enum/constant for "hr" if multiple user types
            "id": hr_user.id, # Should be safe as it's checked above
            "employer_id": hr_user.employer_id, # Should be safe as it's checked above
        }
    )
    logger.info(f"Login successful for {hr_user.email}, token generated.")
    return Token(access_token=access_token, token_type="bearer")


# Google OAuth endpoints were previously removed.
# If HR user creation needs more complex logic or different fields than HRCreate allows,
# it might warrant its own service function beyond the basic crud_create_hr.
# For now, crud_create_hr handles password hashing.
from typing import Optional # Ensure Optional is imported if used for type hints like Optional[HR]
