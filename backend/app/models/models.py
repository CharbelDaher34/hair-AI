from enum import Enum
from typing import Optional, List, Dict, Union
from sqlmodel import SQLModel, Field, Relationship, Column, Text
from sqlalchemy import Boolean, JSON, Enum as SQLAlchemyEnum, UniqueConstraint
from datetime import datetime
from pydantic import field_validator
from models.candidate_pydantic import CandidateResume

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
    

    def get_company_data(self):
        return f"company(name={self.name},/n description={self.description},/n industry={self.industry},/n bio={self.bio},/n website={self.website},/n logo_url={self.logo_url},/n is_owner={self.is_owner},/n domain={self.domain})"


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


class skills_base(SQLModel):
    hard_skills: list[str] = Field(default=[])
    soft_skills: list[str] = Field(default=[])
class compensation_base(SQLModel):
    base_salary: int = Field(default=None)
    benefits: list[str] = Field(default=[])
    

class JobBase(TimeBase):
    employer_id: int = Field(foreign_key="company.id")
    recruited_to_id: Optional[int] = Field(default=None, foreign_key="company.id")
    created_by_hr_id: int = Field(foreign_key="hr.id")
    status: Status = Field(default=Status.DRAFT,sa_column=Column(SQLAlchemyEnum(Status, name="status_enum", create_type=True)))
    department: Optional[str] = Field(default=None)
    title: str
    description: str
    location: str
    compensation: compensation_base = Field(default=None, sa_column=Column(JSON))
    experience_level: ExperienceLevel = Field(default=ExperienceLevel.NO_EXPERIENCE,sa_column=Column(SQLAlchemyEnum(ExperienceLevel, name="experiencelevel_enum", create_type=True)))
    seniority_level: SeniorityLevel = Field(default=SeniorityLevel.ENTRY,sa_column=Column(SQLAlchemyEnum(SeniorityLevel, name="senioritylevel_enum", create_type=True)))
    job_type: JobType = Field(default=JobType.FULL_TIME,sa_column=Column(SQLAlchemyEnum(JobType, name="jobtype_enum", create_type=True)))
    job_category: Optional[str] = Field(default=None)
    responsibilities: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    skills: skills_base = Field(default=None, sa_column=Column(JSON))
    
    @field_validator('compensation','skills')
    def validate_compensation_and_skills(cls, v, info):
        if v is not None:
            # Convert SQLModel objects to dictionaries
            if hasattr(v, 'model_dump'):
                v = v.model_dump()
            
            if not isinstance(v, dict):
                raise ValueError(f"{info.field_name} must be a dictionary")
            
            # Validate compensation structure
            if info.field_name == 'compensation':
                if 'base_salary' not in v:
                    raise ValueError("compensation must contain a base_salary field")
                # Ensure base_salary is an integer or None
                if v.get('base_salary') is not None and not isinstance(v['base_salary'], int):
                    raise ValueError("compensation.base_salary must be an integer or None")
            
            # Validate skills structure
            elif info.field_name == 'skills':
                if 'hard_skills' not in v or 'soft_skills' not in v:
                    raise ValueError("skills must contain hard_skills and soft_skills fields")
                # Ensure skills are lists
                if not isinstance(v.get('hard_skills'), list):
                    raise ValueError("skills.hard_skills must be a list")
                if not isinstance(v.get('soft_skills'), list):
                    raise ValueError("skills.soft_skills must be a list")
        
        return v

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
    parsed_resume: Optional[CandidateResume] = Field(default=None, sa_column=Column(JSON))
    employer_id: Optional[int] = Field(default=None, foreign_key="company.id")


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


class InterviewType(str,Enum):
    PHONE = "phone"
    ONLINE = "online"
    IN_PERSON = "in_person"

class InterviewStatus(str,Enum):
    SCHEDULED = "scheduled"
    DONE = "done"
    CANCELED = "canceled"

class InterviewBase(TimeBase):
    application_id: int = Field(foreign_key="application.id")
    date: datetime
    type:str
    # type: InterviewType = Field(default=InterviewType.PHONE, sa_column=Column(SQLAlchemyEnum(InterviewType, name="interviewtype_enum", create_type=True)))
    status:str
    # status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED, sa_column=Column(SQLAlchemyEnum(InterviewStatus, name="interviewstatus_enum", create_type=True)))
    notes: Optional[str] = None


class Interview(InterviewBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    application: Optional[Application] = Relationship(back_populates="interviews")


class MatchBase(TimeBase):
    application_id: int = Field(foreign_key="application.id")
    
    # Main match result fields
    score: Optional[float] = Field(default=None)
    embedding_similarity: Optional[float] = Field(default=None)
    
    # Skill analysis fields
    match_percentage: Optional[float] = Field(default=None)
    matching_skills: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    missing_skills: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    extra_skills: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Summary fields (from skill_analysis.summary)
    total_required_skills: Optional[int] = Field(default=None)
    matching_skills_count: Optional[int] = Field(default=None)
    missing_skills_count: Optional[int] = Field(default=None)
    extra_skills_count: Optional[int] = Field(default=None)
    
    # Weights used in matching
    skill_weight: Optional[float] = Field(default=None)
    embedding_weight: Optional[float] = Field(default=None)
    
    # Match status
    status: str = Field(default="pending")

class Match(MatchBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    application: Optional[Application] = Relationship(back_populates="matches")


target_metadata = SQLModel.metadata