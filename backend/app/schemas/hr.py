from typing import Optional
from sqlmodel import SQLModel
from models.models import HRBase, HR
from utils.pydantic_utils import make_optional

class HRCreate(HRBase):
    pass


@make_optional
class HRUpdate(HRBase):
    id: int


class HRRead(HRBase):
    id: int
