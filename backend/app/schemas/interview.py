from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel

from pydantic import BaseModel

from models.models import InterviewBase
from .application import ApplicationWithDetails
from .hr import HRRead
from utils.pydantic_utils import make_optional


class InterviewCreate(InterviewBase):
    pass


@make_optional
class InterviewUpdate(InterviewBase):
    id: int


class InterviewRead(InterviewBase):
    id: int
    interviewer: Optional[HRRead] = None

    model_config = {"from_attributes": True}


class InterviewReadWithApplication(InterviewRead):
    application: ApplicationWithDetails
    interviewer: Optional[HRRead] = None

    model_config = {"from_attributes": True}
