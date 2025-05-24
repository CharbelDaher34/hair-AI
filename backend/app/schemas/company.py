from typing import Optional
from sqlmodel import SQLModel
from models.models import CompanyBase, Company
from utils.pydantic_utils import make_optional


class CompanyCreate(CompanyBase):
    is_owner: bool = False

@make_optional
class CompanyUpdate(CompanyBase):
    id: int


class CompanyRead(CompanyBase):
    id: int
