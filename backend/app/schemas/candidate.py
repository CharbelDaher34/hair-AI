from typing import Optional, Dict, List, Any
from pydantic import BaseModel, field_validator
from sqlmodel import SQLModel
from models.models import CandidateBase, ApplicationBase, InterviewBase
from utils.pydantic_utils import make_optional
from schemas.application import JobRead


class CandidateCreate(CandidateBase):
    pass


@make_optional
class CandidateUpdate(CandidateBase):
    id: int


class CandidateRead(CandidateBase):
    id: int


class ApplicationRead(ApplicationBase):
    id:int
    
class InterviewRead(InterviewBase):
    id:int

  
class ApplicationWithInterviews(ApplicationRead):
    interviews: Optional[List[InterviewRead]] = None
    job: Optional[JobRead] = None
    
class CandidateWithDetails(CandidateRead):
    applications: Optional[List[ApplicationWithInterviews]] = None
    
  
    
    
    