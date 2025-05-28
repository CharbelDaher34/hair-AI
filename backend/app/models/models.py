from enum import Enum
from typing import Optional, List, Dict, Union
from sqlmodel import SQLModel, Field, Relationship, Column, Text
from sqlalchemy import Boolean, JSON, Enum as SQLAlchemyEnum
from datetime import datetime
from pydantic import validator


class TimeBase(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CompanyBase(SQLModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    is_owner: bool = Field(default=False)
    domain: Optional[str] = Field(default=None,description="The domain of the company example: @gmail.com")


class Company(CompanyBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    hrs: List["HR"] = Relationship(back_populates="company")
    jobs: List["Job"] = Relationship(
        back_populates="employer",
        sa_relationship_kwargs={"foreign_keys": "Job.employer_id"}
    )
    form_keys: List["FormKey"] = Relationship(back_populates="company")
    recruiter_links: List["RecruiterCompanyLink"] = Relationship(
        back_populates="recruiter",
        sa_relationship_kwargs={"foreign_keys": "RecruiterCompanyLink.recruiter_id"}
    )
    recruited_to_links: List["RecruiterCompanyLink"] = Relationship(
        back_populates="target_company",
        sa_relationship_kwargs={"foreign_keys": "RecruiterCompanyLink.target_employer_id"}
    )
    recruited_jobs: List["Job"] = Relationship(
        back_populates="recruited_to",
        sa_relationship_kwargs={"foreign_keys": "Job.recruited_to_id"}
    )


class HRBase(SQLModel):
    email: str = Field(index=True, unique=True)
    password: str
    full_name: str
    employer_id: int = Field(foreign_key="company.id")
    role: str


class HR(HRBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    company: Optional[Company] = Relationship(back_populates="hrs")
    jobs: List["Job"] = Relationship(back_populates="created_by_hr")


class RecruiterCompanyLinkBase(SQLModel):
    recruiter_id: int = Field(foreign_key="company.id")
    target_employer_id: int = Field(foreign_key="company.id")


class RecruiterCompanyLink(RecruiterCompanyLinkBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    recruiter: Optional[Company] = Relationship(
        back_populates="recruiter_links",
        sa_relationship_kwargs={"foreign_keys": "RecruiterCompanyLink.recruiter_id"}
    )
    target_company: Optional[Company] = Relationship(
        back_populates="recruited_to_links",
        sa_relationship_kwargs={"foreign_keys": "RecruiterCompanyLink.target_employer_id"}
    )

class FieldType(str,Enum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    DATE = "date"
    SELECT = "select"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"

class FormKeyBase(SQLModel):    
    employer_id: int = Field(foreign_key="company.id")
    name: str
    # field_type: FieldType = Field(default=FieldType.TEXT, sa_column=Column(SQLAlchemyEnum(FieldType)))
    enum_values: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    required: bool = Field(default=False)
    field_type: FieldType = Field(
        default=FieldType.TEXT,
        sa_column=Column(SQLAlchemyEnum(FieldType, name="fieldtype_enum", create_type=True))
    )

class FormKey(FormKeyBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    company: Optional[Company] = Relationship(back_populates="form_keys")
    job_constraints: List["JobFormKeyConstraint"] = Relationship(back_populates="form_key")


class JobFormKeyConstraintBase(SQLModel):
    job_id: int = Field(foreign_key="job.id")
    form_key_id: int = Field(foreign_key="formkey.id")
    constraints: Dict = Field(sa_column=Column(JSON))


class JobFormKeyConstraint(JobFormKeyConstraintBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    job: Optional["Job"] = Relationship(back_populates="form_key_constraints")
    form_key: Optional[FormKey] = Relationship(back_populates="job_constraints")


class JobBase(SQLModel):
    employer_id: int = Field(foreign_key="company.id")
    recruited_to_id: Optional[int] = Field(default=None, foreign_key="company.id")
    job_data: Dict = Field(sa_column=Column(JSON))
    status: str
    created_by_hr_id: int = Field(foreign_key="hr.id")


class Job(JobBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    employer: Optional[Company] = Relationship(
        back_populates="jobs",
        sa_relationship_kwargs={"foreign_keys": "Job.employer_id"}
    )
    recruited_to: Optional[Company] = Relationship(
        back_populates="recruited_jobs",
        sa_relationship_kwargs={"foreign_keys": "Job.recruited_to_id"}
    )
    created_by_hr: Optional[HR] = Relationship(back_populates="jobs")
    applications: List["Application"] = Relationship(back_populates="job")
    form_key_constraints: List[JobFormKeyConstraint] = Relationship(back_populates="job")


class CandidateBase(SQLModel):
    full_name: str
    email: str = Field(unique=True)
    phone: Optional[str] = Field(unique=True)
    resume_url: Optional[str] = None
    parsed_resume: Optional[Dict] = Field(default=None, sa_column=Column(JSON))


class Candidate(CandidateBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    applications: List["Application"] = Relationship(back_populates="candidate")


class ApplicationBase(SQLModel):
    candidate_id: int = Field(foreign_key="candidate.id")
    job_id: int = Field(foreign_key="job.id")
    form_responses: Dict = Field(default=None, sa_column=Column(JSON))


class Application(ApplicationBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    candidate: Optional[Candidate] = Relationship(back_populates="applications")
    job: Optional[Job] = Relationship(back_populates="applications")
    matches: List["Match"] = Relationship(back_populates="application")
    interviews: List["Interview"] = Relationship(back_populates="application")

class InterviewBase(SQLModel):
    application_id: int = Field(foreign_key="application.id")
    date: datetime
    type: str  # e.g. phone, zoom, in-person
    status: str  # scheduled, done, canceled
    notes: Optional[str] = None


class Interview(InterviewBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    application: Optional[Application] = Relationship(back_populates="interviews")


class MatchBase(SQLModel):
    application_id: int = Field(foreign_key="application.id")
    match_result: Dict = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="pending")

class Match(MatchBase, TimeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    application: Optional[Application] = Relationship(back_populates="matches")


target_metadata = SQLModel.metadata