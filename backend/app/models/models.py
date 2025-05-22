from typing import Optional, List, Dict
from sqlmodel import SQLModel, Field, Relationship, Column, Text
from sqlalchemy import Boolean, JSON
from datetime import datetime


class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    industry: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    is_owner: bool = Field(default=False, sa_column=Column(Boolean),description="Whether the company is created by the owner or by the recruiter")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    hrs: List["HR"] = Relationship(back_populates="company")
    jobs: List["Job"] = Relationship(back_populates="employer")
    form_keys: List["FormKey"] = Relationship(back_populates="company")
    recruiter_links: List["RecruiterCompanyLink"] = Relationship(back_populates="recruiter")
    recruited_to_links: List["RecruiterCompanyLink"] = Relationship(back_populates="target_company", sa_relationship_kwargs={"foreign_keys": '[RecruiterCompanyLink.target_company_id]'})


class HR(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    full_name: str
    company_id: int = Field(foreign_key="company.id")
    role: str  # 'owner', 'hr', 'recruiter'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    company: Optional["Company"] = Relationship(back_populates="hrs")
    jobs: List["Job"] = Relationship(back_populates="created_by_hr")


class RecruiterCompanyLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recruiter_id: int = Field(foreign_key="company.id")
    target_company_id: int = Field(foreign_key="company.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    recruiter: Optional["Company"] = Relationship(back_populates="recruiter_links", sa_relationship_kwargs={"foreign_keys": '[RecruiterCompanyLink.recruiter_id]'})
    target_company: Optional["Company"] = Relationship(back_populates="recruited_to_links", sa_relationship_kwargs={"foreign_keys": '[RecruiterCompanyLink.target_company_id]'})


class FormKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="company.id")
    name: str
    field_type: str  # enum: 'string', 'number', 'boolean', 'date', etc.
    required: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    company: Optional["Company"] = Relationship(back_populates="form_keys")


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_title: str
    occupation_code: str
    employer_id: int = Field(foreign_key="company.id")
    recruited_to_id: Optional[int] = Field(foreign_key="company.id")
    education_requirements: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    skills: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_period: Optional[str] = None
    currency: Optional[str] = None
    remote: Optional[bool] = None
    locations: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    date_posted: Optional[datetime] = None
    date_expired: Optional[datetime] = None
    is_internship: Optional[bool] = None
    is_staffing: Optional[bool] = None
    full_time: Optional[bool] = None
    form_key_ids: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))
    status: str  # 'draft', 'published', 'closed'
    created_by: int = Field(foreign_key="hr.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    employer: Optional["Company"] = Relationship(back_populates="jobs", sa_relationship_kwargs={"foreign_keys": '[Job.employer_id]'})
    recruited_to: Optional["Company"] = Relationship(sa_relationship_kwargs={"foreign_keys": '[Job.recruited_to_id]'})
    created_by_hr: Optional["HR"] = Relationship(back_populates="jobs")
    applications: List["Application"] = Relationship(back_populates="job")
    matches: List["Match"] = Relationship(back_populates="job")


class Candidate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str
    phone: Optional[str] = None
    resume_url: Optional[str] = Field(default=None)
    parsed_resume: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    applications: List["Application"] = Relationship(back_populates="candidate")
    matches: List["Match"] = Relationship(back_populates="candidate")


class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")
    job_id: int = Field(foreign_key="job.id")
    form_responses: Dict = Field(default=None, sa_column=Column(JSON))
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    candidate: Optional["Candidate"] = Relationship(back_populates="applications")
    job: Optional["Job"] = Relationship(back_populates="applications")


class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    candidate_id: int = Field(foreign_key="candidate.id")
    match_score: float
    attribute_scores: Dict = Field(default=None, sa_column=Column(JSON))
    skills_report: Optional[str] = Field(default=None, sa_column=Column(Text))
    narrative_explanation: Optional[str] = Field(default=None, sa_column=Column(Text))

    job: Optional["Job"] = Relationship(back_populates="matches")
    candidate: Optional["Candidate"] = Relationship(back_populates="matches")
    
target_metadata = SQLModel.metadata