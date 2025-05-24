from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from crud import crud_recruiter_company_link
from schemas import RecruiterCompanyLinkCreate, RecruiterCompanyLinkUpdate, RecruiterCompanyLinkRead

router = APIRouter()

@router.post("/", response_model=RecruiterCompanyLinkRead, status_code=status.HTTP_201_CREATED)
def create_recruiter_company_link(
    *,
    db: Session = Depends(get_session),
    link_in: RecruiterCompanyLinkCreate
) -> RecruiterCompanyLinkRead:
    try:
        link = crud_recruiter_company_link.create_recruiter_company_link(db=db, link_in=link_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return link

@router.get("/{link_id}", response_model=RecruiterCompanyLinkRead)
def read_recruiter_company_link(
    *,
    db: Session = Depends(get_session),
    link_id: int
) -> RecruiterCompanyLinkRead:
    link = crud_recruiter_company_link.get_recruiter_company_link(db=db, link_id=link_id)
    if not link:
        raise HTTPException(status_code=404, detail="RecruiterCompanyLink not found")
    return link

@router.get("/by-recruiter/{recruiter_id}", response_model=List[RecruiterCompanyLinkRead])
def read_links_by_recruiter(
    *,
    db: Session = Depends(get_session),
    recruiter_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[RecruiterCompanyLinkRead]:
    return crud_recruiter_company_link.get_recruiter_company_links_by_recruiter(db=db, recruiter_id=recruiter_id, skip=skip, limit=limit)

@router.get("/by-target-company/{target_company_id}", response_model=List[RecruiterCompanyLinkRead])
def read_links_by_target_company(
    *,
    db: Session = Depends(get_session),
    target_company_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[RecruiterCompanyLinkRead]:
    return crud_recruiter_company_link.get_recruiter_company_links_by_target_company(db=db, target_company_id=target_company_id, skip=skip, limit=limit)

@router.patch("/{link_id}", response_model=RecruiterCompanyLinkRead)
def update_recruiter_company_link(
    *,
    db: Session = Depends(get_session),
    link_id: int,
    link_in: RecruiterCompanyLinkUpdate
) -> RecruiterCompanyLinkRead:
    link = crud_recruiter_company_link.get_recruiter_company_link(db=db, link_id=link_id)
    if not link:
        raise HTTPException(status_code=404, detail="RecruiterCompanyLink not found")
    return crud_recruiter_company_link.update_recruiter_company_link(db=db, db_link=link, link_in=link_in)

@router.delete("/{link_id}", response_model=RecruiterCompanyLinkRead)
def delete_recruiter_company_link(
    *,
    db: Session = Depends(get_session),
    link_id: int
) -> RecruiterCompanyLinkRead:
    link = crud_recruiter_company_link.delete_recruiter_company_link(db=db, link_id=link_id)
    if not link:
        raise HTTPException(status_code=404, detail="RecruiterCompanyLink not found")
    return link 