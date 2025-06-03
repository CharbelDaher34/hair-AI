from typing import Optional
from models.models import ApplicationBase, Application
from utils.pydantic_utils import make_optional
from schemas.candidate import CandidateRead
from schemas.job import JobRead


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