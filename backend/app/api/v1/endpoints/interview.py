from typing import Any, List

from core.database import get_session
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from crud import crud_interview
from schemas import (
    InterviewCreate,
    InterviewUpdate,
    InterviewRead,
    InterviewReadWithApplication,
)

router = APIRouter()


@router.post("/", response_model=InterviewRead)
def create_interview(
    *,
    db: Session = Depends(get_session),
    interview_in: InterviewCreate,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new interview.
    """
    # if not crud.user.is_superuser(current_user) and (interview_in.application_id not in [app.id for app in current_user.applications]):
    #     raise HTTPException(status_code=400, detail="Not enough permissions")
    interview = crud_interview.create_interview(db=db, obj_in=interview_in)
    return interview


@router.get(
    "/by-application/{application_id}",
    response_model=List[InterviewReadWithApplication],
)
def read_interviews_by_application(
    *,
    db: Session = Depends(get_session),
    application_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get interviews by application ID with application details.
    """
    interviews = crud_interview.get_interviews_by_application_id_with_details(
        db=db, application_id=application_id
    )
    return interviews


@router.get("/{interview_id}", response_model=InterviewReadWithApplication)
def read_interview(
    *,
    db: Session = Depends(get_session),
    interview_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get interview by ID with application details.
    """
    interview = crud_interview.get_interview_with_application(
        db=db, interview_id=interview_id
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    # if not crud.user.is_superuser(current_user) and (interview.application_id not in [app.id for app in current_user.applications]):
    #     raise HTTPException(status_code=400, detail="Not enough permissions")
    return interview


@router.get("/", response_model=List[InterviewReadWithApplication])
def read_interviews(
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve interviews with application details.
    """
    interviews = crud_interview.get_interviews_with_application(
        db, skip=skip, limit=limit
    )

    return interviews


@router.put("/{interview_id}", response_model=InterviewRead)
def update_interview(
    *,
    db: Session = Depends(get_session),
    interview_id: int,
    interview_in: InterviewUpdate,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an interview.
    """
    interview = crud_interview.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    # if not crud.user.is_superuser(current_user) and (interview.application.candidate_id != current_user.id): # type: ignore
    #     raise HTTPException(status_code=400, detail="Not enough permissions")
    interview = crud_interview.update_interview(
        db=db, db_obj=interview, obj_in=interview_in
    )
    return interview


@router.delete("/{interview_id}", response_model=InterviewRead)
def delete_interview(
    *,
    db: Session = Depends(get_session),
    interview_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an interview.
    """
    interview = crud_interview.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    # if not crud.user.is_superuser(current_user) and (interview.application.candidate_id != current_user.id): # type: ignore
    #     raise HTTPException(status_code=400, detail="Not enough permissions")
    interview = crud_interview.delete_interview(db=db, interview_id=interview_id)
    return interview
