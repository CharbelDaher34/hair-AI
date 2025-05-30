from enum import Enum
from typing import Optional, List, Dict, Union
from sqlmodel import SQLModel, Field, Relationship, Column, Text
from sqlalchemy import Boolean, JSON, Enum as SQLAlchemyEnum, UniqueConstraint
from datetime import datetime
from pydantic import validator


class TimeBase(SQLModel):
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class CompanyBase(TimeBase):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    is_owner: bool = Field(default=False)
    domain: Optional[str] = Field(default=None,description="The domain of the company example: @gmail.com")


class Company(CompanyBase, table=True):
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


class HRBase(TimeBase):
    email: str = Field(index=True, unique=True)
    password: str
    full_name: str
    employer_id: int = Field(foreign_key="company.id")
    role: str


class HR(HRBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    company: Optional[Company] = Relationship(back_populates="hrs")
    jobs: List["Job"] = Relationship(back_populates="created_by_hr")


class RecruiterCompanyLinkBase(TimeBase):
    recruiter_id: int = Field(foreign_key="company.id")
    target_employer_id: int = Field(foreign_key="company.id")


class RecruiterCompanyLink(RecruiterCompanyLinkBase, table=True):
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

class FormKeyBase(TimeBase):    
    employer_id: int = Field(default=None, foreign_key="company.id")
    name: str
    enum_values: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    required: bool = Field(default=False)
    field_type: FieldType = Field(
        default=FieldType.TEXT,
        sa_column=Column(SQLAlchemyEnum(FieldType, name="fieldtype_enum", create_type=True))
    )

class FormKey(FormKeyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    company: Optional[Company] = Relationship(back_populates="form_keys")
    job_constraints: List["JobFormKeyConstraint"] = Relationship(back_populates="form_key")

    
class JobFormKeyConstraintBase(TimeBase):
    job_id: int = Field(foreign_key="job.id")
    form_key_id: int = Field(foreign_key="formkey.id")
    constraints: Dict = Field(sa_column=Column(JSON))

    __table_args__ = (
        UniqueConstraint("job_id", "form_key_id", name="uq_job_formkey"),
    )
class JobFormKeyConstraint(JobFormKeyConstraintBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    job: Optional["Job"] = Relationship(back_populates="form_key_constraints")
    form_key: Optional[FormKey] = Relationship(back_populates="job_constraints")

class Status(str,Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
class JobType(str,Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
class SeniorityLevel(str,Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
class ExperienceLevel(str,Enum):
    NO_EXPERIENCE = "no_experience"
    ONE_TO_THREE_YEARS = "1-3_years"
    THREE_TO_FIVE_YEARS = "3-5_years"
    FIVE_TO_SEVEN_YEARS = "5-7_years"
    SEVEN_TO_TEN_YEARS = "7-10_years"
    TEN_PLUS_YEARS = "10_plus_years"

class JobBase(TimeBase):
    employer_id: int = Field(foreign_key="company.id")
    recruited_to_id: Optional[int] = Field(default=None, foreign_key="company.id")
    created_by_hr_id: int = Field(foreign_key="hr.id")
    job_data: Dict = Field(sa_column=Column(JSON))
    status: Status = Field(default=Status.DRAFT,sa_column=Column(SQLAlchemyEnum(Status, name="status_enum", create_type=True)))
    title: str
    description: str
    location: str
    salary_min: Optional[int] = Field(default=None)
    salary_max: Optional[int] = Field(default=None)
    experience_level: ExperienceLevel = Field(default=ExperienceLevel.NO_EXPERIENCE,sa_column=Column(SQLAlchemyEnum(ExperienceLevel, name="experiencelevel_enum", create_type=True)))
    seniority_level: SeniorityLevel = Field(default=SeniorityLevel.ENTRY,sa_column=Column(SQLAlchemyEnum(SeniorityLevel, name="senioritylevel_enum", create_type=True)))
    job_type: JobType = Field(default=JobType.FULL_TIME,sa_column=Column(SQLAlchemyEnum(JobType, name="jobtype_enum", create_type=True)))
    job_category: Optional[str] = Field(default=None)


class Job(JobBase, table=True):
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


class CandidateBase(TimeBase):
    full_name: str
    email: str = Field(unique=True)
    phone: Optional[str] = Field(unique=True)
    resume_url: Optional[str] = None
    parsed_resume: Optional[Dict] = Field(default=None, sa_column=Column(JSON))


class Candidate(CandidateBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    applications: List["Application"] = Relationship(back_populates="candidate")


class ApplicationBase(TimeBase):
    candidate_id: int = Field(foreign_key="candidate.id")
    job_id: int = Field(foreign_key="job.id")
    form_responses: Dict = Field(default=None, sa_column=Column(JSON))


class Application(ApplicationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    candidate: Optional[Candidate] = Relationship(back_populates="applications")
    job: Optional[Job] = Relationship(back_populates="applications")
    matches: List["Match"] = Relationship(back_populates="application")
    interviews: List["Interview"] = Relationship(back_populates="application")

class InterviewBase(TimeBase):
    application_id: int = Field(foreign_key="application.id")
    date: datetime
    type: str  # e.g. phone, zoom, in-person
    status: str  # scheduled, done, canceled
    notes: Optional[str] = None


class Interview(InterviewBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    application: Optional[Application] = Relationship(back_populates="interviews")


class MatchBase(TimeBase):
    application_id: int = Field(foreign_key="application.id")
    match_result: Dict = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="pending")

class Match(MatchBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    application: Optional[Application] = Relationship(back_populates="matches")


target_metadata = SQLModel.metadata