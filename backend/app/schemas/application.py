from typing import Optional, Dict
from sqlmodel import SQLModel
from models.models import ApplicationBase, Application
from utils.pydantic_utils import make_optional
from .candidate import CandidateRead
from .job import JobRead
from datetime import datetime

class ApplicationCreate(ApplicationBase):
    pass


@make_optional
class ApplicationUpdate(ApplicationBase):
    id: int


class ApplicationRead(ApplicationBase):
    id: int
    
 


class ApplicationWithDetails(ApplicationRead):
    candidate: Optional[CandidateRead] = None
    job: Optional[JobRead] = None