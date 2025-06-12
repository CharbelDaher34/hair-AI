from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  # For form data
from sqlmodel import Session
import time
from core.database import get_session
from core.security import (
    create_access_token,
    verify_password,
    Token,
    get_password_hash,  # Added get_password_hash
)

# Assuming your CRUD functions are structured like this. Adjust path if necessary.
from crud.crud_hr import (
    get_hr_by_email,
    create_hr as crud_create_hr,
)  # Aliased to avoid conflict
from models.models import HR, HRBase  # HR model for type hinting
from schemas import HRCreate

router = APIRouter()


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
    The password in HRCreate is plain text and will be hashed here.
    """
    print(f"Registering HR: {form_data}")

    # Check if user already exists
    db_hr_check = get_hr_by_email(db, email=form_data.email)
    if db_hr_check:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    print(f"form_data: {form_data.password}")
    created_hr_user: HR = crud_create_hr(
        db=db, hr_in=form_data
    )  # Pass the HR model instance
    print(f"created_hr_user: {created_hr_user}")
    if not created_hr_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create HR user.",
        )

    access_token = create_access_token(
        data={
            "sub": created_hr_user.email,
            "user_type": "hr",
            "id": created_hr_user.id,
            "employer_id": created_hr_user.employer_id,
        }
    )
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
    hr_user: HR = get_hr_by_email(db=db, email=form_data.username)

    if not hr_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the plain password against the stored hashed password
    if not verify_password(form_data.password, hr_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not hr_user.id or not hasattr(hr_user, "employer_id") or not hr_user.employer_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User data is incomplete (missing ID or employer_id).",
        )

    access_token = create_access_token(
        data={
            "sub": hr_user.email,
            "user_type": "hr",
            "id": hr_user.id,
            "employer_id": hr_user.employer_id,
        }
    )

    return Token(access_token=access_token, token_type="bearer")


# Removed Google OAuth endpoints (login_google_hr, google_callback_hr_endpoint)
# Removed process_google_callback_hr function
# Removed related imports like Request, RedirectResponse, Query, etc.
# Removed schemas like HRCreate as user creation is not part of this login endpoint.
# If HR user creation is needed, it should be a separate endpoint, possibly protected.
