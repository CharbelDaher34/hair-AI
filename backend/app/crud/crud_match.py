from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select

from models.models import Match
from schemas import MatchCreate, MatchUpdate


def get_match(db: Session, match_id: int) -> Optional[Match]:
    return db.get(Match, match_id)


def get_matches_by_application(db: Session, application_id: int, skip: int = 0, limit: int = 100) -> List[Match]:
    statement = select(Match).where(Match.application_id == application_id).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_match(db: Session, *, match_in: MatchCreate) -> Match:
    db_match = Match.model_validate(match_in)
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


def update_match(
    db: Session, *, db_match: Match, match_in: Union[MatchUpdate, Dict[str, Any]]
) -> Match:
    if isinstance(match_in, dict):
        update_data = match_in
    else:
        update_data = match_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_match, field, value)
    
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


def delete_match(db: Session, *, match_id: int) -> Optional[Match]:
    db_match = db.get(Match, match_id)
    if db_match:
        db.delete(db_match)
        db.commit()
    return db_match 