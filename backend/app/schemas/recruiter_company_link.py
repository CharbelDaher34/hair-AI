from typing import Optional
from sqlmodel import SQLModel
from models.models import RecruiterCompanyLinkBase, RecruiterCompanyLink
from utils.pydantic_utils import make_optional


class RecruiterCompanyLinkCreate(RecruiterCompanyLinkBase):
    pass


@make_optional
class RecruiterCompanyLinkUpdate(RecruiterCompanyLinkBase):
    id: int


class RecruiterCompanyLinkRead(RecruiterCompanyLinkBase):
    id: int
