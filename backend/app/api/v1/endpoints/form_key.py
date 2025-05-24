from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from crud import crud_form_key
from schemas import FormKeyCreate, FormKeyUpdate, FormKeyRead

router = APIRouter()

@router.post("/", response_model=FormKeyRead, status_code=status.HTTP_201_CREATED)
def create_form_key(
    *,
    db: Session = Depends(get_session),
    form_key_in: FormKeyCreate
) -> FormKeyRead:
    try:
        form_key = crud_form_key.create_form_key(db=db, form_key_in=form_key_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return form_key

@router.get("/{form_key_id}", response_model=FormKeyRead)
def read_form_key(
    *,
    db: Session = Depends(get_session),
    form_key_id: int
) -> FormKeyRead:
    form_key = crud_form_key.get_form_key(db=db, form_key_id=form_key_id)
    if not form_key:
        raise HTTPException(status_code=404, detail="FormKey not found")
    return form_key

@router.get("/by-company/{company_id}", response_model=List[FormKeyRead])
def read_form_keys_by_company(
    *,
    db: Session = Depends(get_session),
    company_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[FormKeyRead]:
    return crud_form_key.get_form_keys_by_company(db=db, company_id=company_id, skip=skip, limit=limit)

@router.patch("/{form_key_id}", response_model=FormKeyRead)
def update_form_key(
    *,
    db: Session = Depends(get_session),
    form_key_id: int,
    form_key_in: FormKeyUpdate
) -> FormKeyRead:
    form_key = crud_form_key.get_form_key(db=db, form_key_id=form_key_id)
    if not form_key:
        raise HTTPException(status_code=404, detail="FormKey not found")
    return crud_form_key.update_form_key(db=db, db_form_key=form_key, form_key_in=form_key_in)

@router.delete("/{form_key_id}", response_model=FormKeyRead)
def delete_form_key(
    *,
    db: Session = Depends(get_session),
    form_key_id: int
) -> FormKeyRead:
    form_key = crud_form_key.delete_form_key(db=db, form_key_id=form_key_id)
    if not form_key:
        raise HTTPException(status_code=404, detail="FormKey not found")
    return form_key
