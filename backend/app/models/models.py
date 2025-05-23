import enum
from typing import Optional, List, Dict
from sqlmodel import SQLModel, Field, Relationship, Column, Text
from sqlalchemy import Boolean, JSON, Enum as SAEnum
from datetime import datetime


class TimeBase(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Company Models
class CompanyBase(SQLModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = Field(unique=True)
    logo_url: Optional[str] = None

class Company(CompanyBase, TimeBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_owner: bool = Field(default=False, sa_column=Column(Boolean),description="Whether the company is created by the owner or by the recruiter")

    hrs: List["HR"] = Relationship(back_populates="company")
    jobs: List["Job"] = Relationship(back_populates="employer")
    form_keys: List["FormKey"] = Relationship(back_populates="company")
    recruiter_links: List["RecruiterCompanyLink"] = Relationship(back_populates="recruiter")
    recruited_to_links: List["RecruiterCompanyLink"] = Relationship(back_populates="target_company", sa_relationship_kwargs={"foreign_keys": '[RecruiterCompanyLink.target_company_id]'})
    recruited_jobs: List["Job"] = Relationship(back_populates="recruited_to", sa_relationship_kwargs={"foreign_keys": '[Job.recruited_to_id]'})

# HR Models
class HRBase(SQLModel):
    email: str = Field(index=True, unique=True)
    password_hash: str
    full_name: str
    company_id: int = Field(foreign_key="company.id")
    role: str

class HR(HRBase, TimeBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    company: Optional["Company"] = Relationship(back_populates="hrs")
    jobs: List["Job"] = Relationship(back_populates="created_by_hr")

# RecruiterCompanyLink Models
class RecruiterCompanyLinkBase(SQLModel):
    recruiter_id: int = Field(foreign_key="company.id")
    target_company_id: int = Field(foreign_key="company.id")

class RecruiterCompanyLink(RecruiterCompanyLinkBase, TimeBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    recruiter: Optional["Company"] = Relationship(back_populates="recruiter_links", sa_relationship_kwargs={"foreign_keys": '[RecruiterCompanyLink.recruiter_id]'})
    target_company: Optional["Company"] = Relationship(back_populates="recruited_to_links", sa_relationship_kwargs={"foreign_keys": '[RecruiterCompanyLink.target_company_id]'})

# FormKey Models
class FormKeyBase(SQLModel):
    company_id: int = Field(foreign_key="company.id")
    name: str
    field_type: str
    enum_values: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    required: bool = Field(default=False)

class FormKey(FormKeyBase, TimeBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    company: Optional["Company"] = Relationship(back_populates="form_keys")
    job_constraints: List["JobFormKeyConstraint"] = Relationship(back_populates="form_key")

# JobFormKeyConstraint Models
class JobFormKeyConstraintBase(SQLModel):
    job_id: int = Field(foreign_key="job.id")
    form_key_id: int = Field(foreign_key="formkey.id")
    constraints: Dict = Field(sa_column=Column(JSON))

class JobFormKeyConstraint(JobFormKeyConstraintBase, TimeBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    job: Optional["Job"] = Relationship(back_populates="form_key_constraints")
    form_key: Optional["FormKey"] = Relationship(back_populates="job_constraints")

# Job Models
class JobBase(SQLModel):
    employer_id: int = Field(foreign_key="company.id")
    recruited_to_id: Optional[int] = Field(default=None, foreign_key="company.id")
    job_data: Dict = Field(sa_column=Column(JSON))
    status: str
    created_by: int = Field(foreign_key="hr.id")

class Job(JobBase, TimeBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    employer: Optional["Company"] = Relationship(back_populates="jobs", sa_relationship_kwargs={"foreign_keys": '[Job.employer_id]'})
    recruited_to: Optional["Company"] = Relationship(back_populates="recruited_jobs", sa_relationship_kwargs={"foreign_keys": '[Job.recruited_to_id]'})
    created_by_hr: Optional["HR"] = Relationship(back_populates="jobs")
    applications: List["Application"] = Relationship(back_populates="job")
    form_key_constraints: List["JobFormKeyConstraint"] = Relationship(back_populates="job")

# Candidate Models
class CandidateBase(SQLModel):
    full_name: str
    email: str = Field(unique=True)
    phone: Optional[str] = Field(unique=True)
    resume_url: Optional[str] = None
    parsed_resume: Optional[Dict] = Field(default=None, sa_column=Column(JSON))

class Candidate(CandidateBase, TimeBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    applications: List["Application"] = Relationship(back_populates="candidate")
    
# Application Models
class ApplicationBase(SQLModel):
    candidate_id: int = Field(foreign_key="candidate.id")
    job_id: int = Field(foreign_key="job.id")
    form_responses: Dict = Field(default=None, sa_column=Column(JSON))

class Application(ApplicationBase, TimeBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    candidate: Optional["Candidate"] = Relationship(back_populates="applications")
    job: Optional["Job"] = Relationship(back_populates="applications")
    matches: List["Match"] = Relationship(back_populates="application")

# Match Models
class MatchBase(SQLModel):
    application_id: int = Field(foreign_key="application.id")
    match_score: float
    attribute_scores: Dict = Field(default=None, sa_column=Column(JSON))
    skills_report: Optional[str] = Field(default=None, sa_column=Column(Text))
    narrative_explanation: Optional[str] = Field(default=None, sa_column=Column(Text))

class Match(MatchBase, TimeBase, SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    application: Optional["Application"] = Relationship(back_populates="matches")
    
target_metadata = SQLModel.metadata