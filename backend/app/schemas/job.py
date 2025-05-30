from typing import Optional, List, Dict
from sqlmodel import SQLModel
from models.models import JobBase, Job
from utils.pydantic_utils import make_optional

@make_optional
class JobCreate(JobBase):
    pass
    # employer_id and created_by_hr_id are set from token on backend


@make_optional
class JobUpdate(JobBase):
    id: int

class JobRead(JobBase):
    id: int
