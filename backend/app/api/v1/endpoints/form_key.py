from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session

from core.database import get_session
from crud import crud_form_key
from schemas import FormKeyCreate, FormKeyUpdate, FormKeyRead
from core.security import TokenData

router = APIRouter()

@router.post("/", response_model=FormKeyRead, status_code=status.HTTP_201_CREATED)
def create_form_key(
    *,
    db: Session = Depends(get_session),
    form_key_in: FormKeyCreate,
    request: Request
) -> FormKeyRead:
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    form_key_in.employer_id = current_user.employer_id
    
    print("form_key_data", form_key_in)
    try:
        form_key_in = FormKeyCreate(**form_key_in.model_dump())
        form_key = crud_form_key.create_form_key(db=db, form_key_in=form_key_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return form_key

@router.get("/{form_key_id}", response_model=FormKeyRead)
def read_form_key(
    *,
    db: Session = Depends(get_session),
    form_key_id: int,
    request: Request
) -> FormKeyRead:
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    form_key = crud_form_key.get_form_key(db=db, form_key_id=form_key_id)
    if not form_key:
        raise HTTPException(status_code=404, detail="FormKey not found")
    
    # Check if the form key belongs to the current user's company
    if form_key.employer_id != current_user.employer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return form_key

@router.get("/", response_model=List[FormKeyRead])
def read_form_keys_by_company(
    *,
    db: Session = Depends(get_session),
    request: Request,
    skip: int = 0,
    limit: int = 100
) -> List[FormKeyRead]:
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    return crud_form_key.get_form_keys_by_company(
        db=db, 
        employer_id=current_user.employer_id, 
        skip=skip, 
        limit=limit
    )

@router.patch("/{form_key_id}", response_model=FormKeyRead)
def update_form_key(
    *,
    db: Session = Depends(get_session),
    form_key_id: int,
    form_key_in: FormKeyUpdate,
    request: Request
) -> FormKeyRead:
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    form_key = crud_form_key.get_form_key(db=db, form_key_id=form_key_id)
    if not form_key:
        raise HTTPException(status_code=404, detail="FormKey not found")
    
    # Check if the form key belongs to the current user's company
    if form_key.employer_id != current_user.employer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return crud_form_key.update_form_key(db=db, db_form_key=form_key, form_key_in=form_key_in)

@router.delete("/{form_key_id}", response_model=FormKeyRead)
def delete_form_key(
    *,
    db: Session = Depends(get_session),
    form_key_id: int,
    request: Request
) -> FormKeyRead:
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    form_key = crud_form_key.get_form_key(db=db, form_key_id=form_key_id)
    if not form_key:
        raise HTTPException(status_code=404, detail="FormKey not found")
    
    # Check if the form key belongs to the current user's company
    if form_key.employer_id != current_user.employer_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    form_key = crud_form_key.delete_form_key(db=db, form_key_id=form_key_id)
    if not form_key:
        raise HTTPException(status_code=404, detail="FormKey not found")
    return form_key
