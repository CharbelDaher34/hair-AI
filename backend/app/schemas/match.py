from typing import Optional, Dict
from sqlmodel import SQLModel
from models.models import MatchBase, Match
from utils.pydantic_utils import make_optional

class MatchCreate(MatchBase):
    pass


@make_optional
class MatchUpdate(MatchBase):
    id: int

class MatchRead(MatchBase):
    id: int 