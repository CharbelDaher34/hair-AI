from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel

from pydantic import BaseModel

from models.models import  InterviewBase
from schemas.application import ApplicationWithDetails
from utils.pydantic_utils import make_optional



class InterviewCreate(InterviewBase):
    pass


@make_optional
class InterviewUpdate(InterviewBase):
    id: int


class InterviewRead(InterviewBase):
    id: int


    model_config = {"from_attributes": True}


class InterviewReadWithApplication(InterviewRead):
    application: ApplicationWithDetails

    model_config = {"from_attributes": True} 