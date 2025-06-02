from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import true
from sqlmodel import select

from models.models import Interview, Application
from schemas.interview import InterviewCreate, InterviewUpdate


def create_interview(db: Session, *, obj_in: InterviewCreate) -> Interview:
    db_obj = Interview(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_interview(db: Session, interview_id: int) -> Optional[Interview]:
    return db.query(Interview).filter(Interview.id == interview_id).first()

def get_interview_with_application(db: Session, interview_id: int) -> Optional[Interview]:
    """Get interview with application details (candidate and job)"""
    statement = (
        select(Interview)
        .where(Interview.id == interview_id)
    )
    interview = db.exec(statement).first()
    if interview:
        # Load application relationship and its nested relationships
        db.refresh(interview, ["application"])
        if interview.application:
            db.refresh(interview.application, ["candidate", "job"])
    return interview

def get_interviews(db: Session, skip: int = 0, limit: int = 100) -> List[Interview]:
    return db.query(Interview).offset(skip).limit(limit).all()

def get_interviews_with_application(db: Session, skip: int = 0, limit: int = 100) -> List[Interview]:
    """Get interviews with application details (candidate and job) loaded"""
    statement = (
        select(Interview)
        .offset(skip)
        .limit(limit)
    )
    interviews = db.exec(statement).all()
    
    # Load relationships for each interview
    for interview in interviews:
        db.refresh(interview, ["application"])
        if interview.application:
            db.refresh(interview.application, ["candidate", "job"])
    
    return interviews

def update_interview(db: Session, *, db_obj: Interview, obj_in: InterviewUpdate) -> Interview:
    obj_data = obj_in.model_dump(exclude_unset=True)
    for field, value in obj_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_interview(db: Session, interview_id: int) -> Optional[Interview]:
    obj = db.query(Interview).filter(Interview.id == interview_id).first()
    if obj:
        db.delete(obj)
        db.commit()
    return obj

def get_interviews_by_application_id(db: Session, application_id: int) -> List[Interview]:
    return db.query(Interview).filter(Interview.application_id == application_id).all()

def get_interviews_by_application_id_with_details(db: Session, application_id: int) -> List[Interview]:
    """Get interviews by application ID with application details (candidate and job) loaded"""
    statement = (
        select(Interview)
        .where(Interview.application_id == application_id)
    )
    interviews = db.exec(statement).all()
    
    # Load relationships for each interview
    for interview in interviews:
        db.refresh(interview, ["application"])
        if interview.application:
            db.refresh(interview.application, ["candidate", "job"])
    
    return interviews


