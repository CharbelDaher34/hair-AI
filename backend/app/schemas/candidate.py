from typing import Optional, Dict
from sqlmodel import SQLModel
from models.models import CandidateBase, Candidate
from utils.pydantic_utils import make_optional


class CandidateCreate(CandidateBase):
    pass


@make_optional
class CandidateUpdate(CandidateBase):
    id: int


class CandidateRead(CandidateBase):
    id: int
