from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from crud import crud_application
from schemas import ApplicationCreate, ApplicationUpdate, ApplicationRead

router = APIRouter()

@router.post("/", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    *,
    db: Session = Depends(get_session),
    application_in: ApplicationCreate
) -> ApplicationRead:
    try:
        application = crud_application.create_application(db=db, application_in=application_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return application

@router.get("/{application_id}", response_model=ApplicationRead)
def read_application(
    *,
    db: Session = Depends(get_session),
    application_id: int
) -> ApplicationRead:
    application = crud_application.get_application(db=db, application_id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.get("/by-job/{job_id}", response_model=List[ApplicationRead])
def read_applications_by_job(
    *,
    db: Session = Depends(get_session),
    job_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ApplicationRead]:
    return crud_application.get_applications_by_job(db=db, job_id=job_id, skip=skip, limit=limit)

@router.get("/by-candidate/{candidate_id}", response_model=List[ApplicationRead])
def read_applications_by_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[ApplicationRead]:
    return crud_application.get_applications_by_candidate(db=db, candidate_id=candidate_id, skip=skip, limit=limit)

@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    *,
    db: Session = Depends(get_session),
    application_id: int,
    application_in: ApplicationUpdate
) -> ApplicationRead:
    application = crud_application.get_application(db=db, application_id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return crud_application.update_application(db=db, db_application=application, application_in=application_in)

@router.delete("/{application_id}", response_model=ApplicationRead)
def delete_application(
    *,
    db: Session = Depends(get_session),
    application_id: int
) -> ApplicationRead:
    application = crud_application.delete_application(db=db, application_id=application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application
