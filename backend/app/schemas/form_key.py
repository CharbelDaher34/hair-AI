from typing import Optional, List
from sqlmodel import SQLModel
from models.models import FormKeyBase, FormKey
from utils.pydantic_utils import make_optional

class FormKeyCreate(FormKeyBase):
    pass


@make_optional
class FormKeyUpdate(FormKeyBase):
    id: int


class FormKeyRead(FormKeyBase):
    id: int 