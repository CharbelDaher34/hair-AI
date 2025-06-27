from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from core.database import get_session
from crud import crud_match
from schemas import MatchCreate, MatchUpdate, MatchRead
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=MatchRead, status_code=status.HTTP_201_CREATED)
def create_match(
    *, db: Session = Depends(get_session), match_in: MatchCreate
) -> MatchRead:
    try:
        logger.debug(f"Creating match: {match_in}")
        return crud_match.create_match(db=db, match_in=match_in)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{match_id}", response_model=MatchRead)
def read_match(*, db: Session = Depends(get_session), match_id: int) -> MatchRead:
    if not (match := crud_match.get_match(db=db, match_id=match_id)):
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.get("/by-application/{application_id}", response_model=List[MatchRead])
def read_matches_by_application(
    *,
    db: Session = Depends(get_session),
    application_id: int,
    skip: int = 0,
    limit: int = 100,
) -> List[MatchRead]:
    return crud_match.get_matches_by_application(
        db=db, application_id=application_id, skip=skip, limit=limit
    )


@router.patch("/{match_id}", response_model=MatchRead)
def update_match(
    *, db: Session = Depends(get_session), match_id: int, match_in: MatchUpdate
) -> MatchRead:
    if not (match := crud_match.get_match(db=db, match_id=match_id)):
        raise HTTPException(status_code=404, detail="Match not found")
    return crud_match.update_match(db=db, db_match=match, match_in=match_in)


@router.delete("/{match_id}", response_model=MatchRead)
def delete_match(*, db: Session = Depends(get_session), match_id: int) -> MatchRead:
    if not (match := crud_match.delete_match(db=db, match_id=match_id)):
        raise HTTPException(status_code=404, detail="Match not found")
    return match
