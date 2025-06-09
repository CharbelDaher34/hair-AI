from typing import Optional, List, Any
from pydantic import BaseModel, field_validator
from models.models import ApplicationBase
from utils.pydantic_utils import make_optional
from schemas.candidate import CandidateRead
from schemas.job import JobRead


# New schema for individual form response items
class FormResponseItem(BaseModel):
    name: str  # The name/key of the form field
    value: Any # The value submitted for this form field


class ApplicationCreate(ApplicationBase):
    pass


@make_optional
class ApplicationUpdate(ApplicationBase):
    id: int


class ApplicationRead(ApplicationBase):
    id: int
    # form_responses here is inherited from ApplicationBase as Dict


class ApplicationWithDetails(ApplicationRead):
    candidate: Optional[CandidateRead] = None
    job: Optional[JobRead] = None
    # Override form_responses to use the new structure
    form_responses: Optional[List[FormResponseItem]] = None

    @field_validator("form_responses",mode="before")
    def transform_form_responses_dict_to_list(cls, v):
        if isinstance(v, dict):
            return [{"name": str(key), "value": value} for key, value in v.items()]
        return v