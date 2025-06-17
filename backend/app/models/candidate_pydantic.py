from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from datetime import date, datetime
from enum import Enum


# Enums
class EducationLevel(str, Enum):
    high_school = "High School"
    associate = "Associate"
    bachelor = "Bachelor’s"
    master = "Master’s"
    doctorate = "Doctorate"
    diploma = "Diploma"
    certificate = "Certificate"
    other = "Other"


class EmploymentType(str, Enum):
    full_time = "Full-time"
    part_time = "Part-time"
    contract = "Contract"
    internship = "Internship"
    freelance = "Freelance"
    volunteer = "Volunteer"


class DegreeType(str, Enum):
    bachelor = "Bachelor’s"
    master = "Master’s"
    doctorate = "Doctorate"
    diploma = "Diploma"
    other = "Other"


# Sub-models
class WorkHistoryItem(BaseModel):
    job_title: str = Field(..., description="Job title in this role.")
    employer: str = Field(..., description="Name of the employer.")
    location: str = Field(..., description="Location where the job was held.")
    employment_type: EmploymentType = Field(
        ..., description="Type of employment (e.g., Full-time, Part-time)."
    )
    # naics_code: Optional[str] = Field(None, description="Industry classification code (NAICS).")
    # naics_industry_name: Optional[str] = Field(None, description="Industry name from NAICS code.")
    start_date: date | str = Field(..., description="Job start date.")
    end_date: Optional[date | str] = Field(
        None, description="Job end date, null if currently employed."
    )
    summary: str = Field(..., description="Brief summary of role and responsibilities.")


class EducationItem(BaseModel):
    level: EducationLevel = Field(
        ..., description="Education level (e.g., Bachelor’s, Master’s)."
    )
    degree_type: DegreeType = Field(
        ..., description="Degree name (e.g., BS in Computer Science)."
    )
    subject: str = Field(..., description="Major or field of study.")
    start_date: date | str = Field(..., description="Start date of the program.")
    end_date: Optional[date | str] = Field(
        None, description="End or expected graduation date."
    )
    institution: str = Field(..., description="Name of the educational institution.")
    gpa: Optional[float] = Field(None, description="Grade Point Average if available.")
    summary: Optional[str] = Field(
        None, description="Additional notes such as honors or thesis."
    )


class SkillItem(BaseModel):
    name: str = Field(..., description="Name of the skill (e.g., Python).")
    category: str = Field(
        ..., description="Category of the skill (e.g., Programming Language)."
    )
    level: str = Field(
        ..., description="Proficiency level (e.g., Beginner, Intermediate, Expert)."
    )


class CertificationItem(BaseModel):
    certification: str = Field(..., description="Name of the certification.")
    certification_group: Optional[str] = Field(
        None, description="High-level category of the certification."
    )
    # certification_family: Optional[str] = Field(None, description="Sub-category of the certification.")
    issued_by: Optional[str] = Field(
        None, description="Issuing organization (e.g., AWS)."
    )
    issue_date: Optional[date | str] = Field(
        None, description="Date when the certification was issued."
    )
  

# Main model with flattened contact fields
class CandidateResume(BaseModel):
    full_name: str = Field(..., description="Full name of the candidate.")
    email: Optional[EmailStr] = Field(None, description="Email of the candidate.")
    phone: Optional[str] = Field(None, description="Phone number of the candidate.")

    # Candidate background
    work_history: Optional[List[WorkHistoryItem]] = Field(
        None, description="List of work experience entries."
    )
    education: Optional[List[EducationItem]] = Field(
        None, description="List of education history entries."
    )
    skills: Optional[List[SkillItem]] = Field(
        None, description="List of skills the candidate possesses."
    )
    certifications: Optional[List[CertificationItem]] = Field(
        None, description="List of certifications held by the candidate."
    )


    # created_at: datetime = Field(..., description="Datetime when this record was created.")
    # updated_at: datetime = Field(..., description="Datetime when this record was last updated.")

    # # Contact info fields
    # prefix: Optional[str] = Field(None, description="Title or prefix (e.g., Mr., Dr.).")
    # full_name: str = Field(..., description="Full name of the candidate.")
    # first_name: Optional[str] = Field(None, description="First name.")
    # middle_name: Optional[str] = Field(None, description="Middle name.")
    # last_name: Optional[str] = Field(None, description="Last name.")
    # suffix: Optional[str] = Field(None, description="Name suffix (e.g., Jr., Sr.).")

    # city_name: Optional[str] = Field(None, description="City of residence.")
    # county_name: Optional[str] = Field(None, description="County of residence.")
    # state_name: Optional[str] = Field(None, description="State of residence.")
    # geo_coordinates: Optional[str] = Field(None, description="Latitude and longitude as string.")
    # postal_code: Optional[str] = Field(None, description="Postal code.")
    # street_address: Optional[str] = Field(None, description="Street address.")

    # telephones: List[str] = Field(..., description="List of phone numbers with type and normalization.")
    # email_addresses: List[EmailStr] = Field(..., description="List of valid email addresses.")
    # web_addresses: List[HttpUrl] = Field(..., description="List of personal/professional websites.")
