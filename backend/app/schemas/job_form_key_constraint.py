from typing import Optional, Dict
from sqlmodel import SQLModel
from models.models import JobFormKeyConstraintBase, JobFormKeyConstraint
from utils.pydantic_utils import make_optional
from schemas.form_key import FormKeyRead


class JobFormKeyConstraintCreate(JobFormKeyConstraintBase):
    pass


@make_optional
class JobFormKeyConstraintUpdate(JobFormKeyConstraintBase):
    id: int


class JobFormKeyConstraintRead(JobFormKeyConstraintBase):
    id: int
    form_key: Optional[FormKeyRead] = None
