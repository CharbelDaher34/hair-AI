from typing import Optional, List, Dict
from sqlmodel import SQLModel
from models.models import JobBase, Job
from utils.pydantic_utils import make_optional

class JobCreate(JobBase):
    pass


@make_optional
class JobUpdate(JobBase):
    id: int

class JobRead(JobBase):
    id: int
