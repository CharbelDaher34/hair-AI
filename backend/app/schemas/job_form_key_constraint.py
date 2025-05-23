from typing import Optional, Dict
from sqlmodel import SQLModel
from models.models import JobFormKeyConstraintBase, JobFormKeyConstraint
from utils.pydantic_utils import make_optional

class JobFormKeyConstraintCreate(JobFormKeyConstraintBase):
    pass


@make_optional
class JobFormKeyConstraintUpdate(JobFormKeyConstraintBase):
    id: int


class JobFormKeyConstraintRead(JobFormKeyConstraintBase):
    id: int 