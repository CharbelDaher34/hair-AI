from typing import Any, Dict, Optional, Union, List

from sqlmodel import Session, select, func

from models.models import Candidate, Application, Job, Company, CandidateEmployerLink, Interview
from schemas import CandidateCreate, CandidateUpdate, InterviewRead


def get_candidate(db: Session, candidate_id: int) -> Optional[Candidate]:
    return db.get(Candidate, candidate_id)


def get_candidate_by_email(db: Session, email: str) -> Optional[Candidate]:
    statement = select(Candidate).where(Candidate.email == email)
    return db.exec(statement).first()


def get_candidates(db: Session, skip: int = 0, limit: int = 100) -> List[Candidate]:
    statement = select(Candidate).offset(skip).limit(limit)
    
    return db.exec(statement).all()


def create_candidate(db: Session, *, candidate_in: CandidateCreate) -> Candidate:
    # Check if candidate already exists by email
    existing_candidate = get_candidate_by_email(db, candidate_in.email)
    if existing_candidate:
        return existing_candidate

    db_candidate = Candidate.model_validate(candidate_in)
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate


def update_candidate(
    db: Session,
    *,
    db_candidate: Candidate,
    candidate_in: Union[CandidateUpdate, Dict[str, Any]],
) -> Candidate:
    if isinstance(candidate_in, dict):
        update_data = candidate_in
    else:
        update_data = candidate_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_candidate, field, value)

    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate


def delete_candidate(db: Session, *, candidate_id: int) -> Optional[Candidate]:
    db_candidate = db.get(Candidate, candidate_id)
    if db_candidate:
        db.delete(db_candidate)
        db.commit()
    return db_candidate


def get_candidates_by_company(db: Session, *, employer_id: int):
    """Get candidates associated with a company through applications or direct association"""
    # Get candidates through applications
    statement_1 = (
        select(Candidate)
        .join(Application, Application.candidate_id == Candidate.id)
        .join(Job, Job.id == Application.job_id)
        .where(Job.employer_id == employer_id)
    )
    
    # Get candidates through direct many-to-many association
    statement_2 = (
        select(Candidate)
        .join(CandidateEmployerLink, CandidateEmployerLink.candidate_id == Candidate.id)
        .where(CandidateEmployerLink.employer_id == employer_id)
    )
    
    candidates_1 = db.exec(statement_1).all()
    candidates_2 = db.exec(statement_2).all()
    unique_candidates = {
        candidate.id: candidate for candidate in candidates_1 + candidates_2
    }
    return list(unique_candidates.values())


def add_candidate_to_employer(db: Session, *, candidate_id: int, employer_id: int) -> bool:
    """Add a candidate to an employer's candidate pool"""
    # Check if relationship already exists
    existing_link = db.exec(
        select(CandidateEmployerLink).where(
            CandidateEmployerLink.candidate_id == candidate_id,
            CandidateEmployerLink.employer_id == employer_id
        )
    ).first()
    
    if existing_link:
        return False  # Relationship already exists
    
    # Create new relationship
    link = CandidateEmployerLink(candidate_id=candidate_id, employer_id=employer_id)
    db.add(link)
    db.commit()
    return True


def remove_candidate_from_employer(db: Session, *, candidate_id: int, employer_id: int) -> bool:
    """Remove a candidate from an employer's candidate pool"""
    link = db.exec(
        select(CandidateEmployerLink).where(
            CandidateEmployerLink.candidate_id == candidate_id,
            CandidateEmployerLink.employer_id == employer_id
        )
    ).first()
    
    if link:
        db.delete(link)
        db.commit()
        return True
    return False


def get_candidate_employers(db: Session, *, candidate_id: int) -> List[Company]:
    """Get all employers associated with a candidate"""
    statement = (
        select(Company)
        .join(CandidateEmployerLink, CandidateEmployerLink.employer_id == Company.id)
        .where(CandidateEmployerLink.candidate_id == candidate_id)
    )
    return db.exec(statement).all()


def get_candidates_table_by_company(db: Session, *, employer_id: int) -> List[Dict[str, Any]]:
    """Get candidates with their application and interview counts for a specific company"""
    # Get candidates associated with the company through applications or direct association
    candidates = get_candidates_by_company(db, employer_id=employer_id)
    
    result = []
    for candidate in candidates:
        # Count applications for this candidate
        applications_count = db.exec(
            select(func.count(Application.id))
            .join(Job, Application.job_id == Job.id)
            .where(Application.candidate_id == candidate.id)
            .where(Job.employer_id == employer_id)
        ).one()
        
        # Count interviews for this candidate (through applications)
        interviews_count = db.exec(
            select(func.count(Interview.id))
            .join(Application, Interview.application_id == Application.id)
            .join(Job, Application.job_id == Job.id)
            .where(Application.candidate_id == candidate.id)
            .where(Job.employer_id == employer_id)
        ).one()
        
        # Handle tuple results from func.count
        if isinstance(applications_count, tuple):
            applications_count = applications_count[0]
        if isinstance(interviews_count, tuple):
            interviews_count = interviews_count[0]
        
        result.append({
            "candidate": candidate,
            "applications_count": applications_count,
            "interviews_count": interviews_count
        })
    
    return result


# def get_candidate_with_details(db: Session, candidate_id: int) -> Optional[CandidateWithDetails]:
#     """Get candidate with applications and their interviews"""
#     candidate = get_candidate(db=db, candidate_id=candidate_id)
#     if not candidate:
#         return None
    
#     # Get applications for this candidate
#     applications_statement = select(Application).where(Application.candidate_id == candidate_id)
#     applications = db.exec(applications_statement).all()
    
#     # Build ApplicationWithInterviews objects
#     applications_with_interviews = []
#     for application in applications:
#         # Get interviews for this application
#         interviews_statement = select(Interview).where(Interview.application_id == application.id)
#         interviews = db.exec(interviews_statement).all()
        
#         # Convert interviews to InterviewRead objects
#         interview_reads = [InterviewRead.model_validate(interview) for interview in interviews]
        
#         # Create ApplicationWithInterviews object
#         app_with_interviews = ApplicationWithInterviews(
#             **application.model_dump(),
#             interviews=interview_reads
#         )
#         applications_with_interviews.append(app_with_interviews)
    
    
#     # Create and return CandidateWithDetails
#     return CandidateWithDetails(
#         **candidate.model_dump(),
#         data=applications_with_interviews
#     )
