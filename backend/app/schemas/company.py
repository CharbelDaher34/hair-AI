from typing import Optional
from sqlmodel import SQLModel
from models.models import CompanyBase, Company
from utils.pydantic_utils import make_optional


class CompanyCreate(CompanyBase):
    pass


@make_optional
class CompanyUpdate(CompanyBase):
    id: int


class CompanyRead(CompanyBase):
    id: int
