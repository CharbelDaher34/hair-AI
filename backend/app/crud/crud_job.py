from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
from collections import Counter

from sqlmodel import Session, select, func

from models.models import Job, Application, Match, Interview, Candidate, Status, Company
from schemas import JobCreate, JobUpdate
from schemas import JobAnalytics, JobRead


def get_job(db: Session, job_id: int) -> Optional[Job]:
    return db.get(Job, job_id)


def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    employer_id: int = None,
    closed: bool = False,
) -> List[JobRead]:
    if closed:
        statement = (
            select(Job, Company.name.label("recruited_to_name"))
            .outerjoin(Company, Job.recruited_to_id == Company.id)
            .where(Job.employer_id == employer_id)
            .offset(skip)
            .limit(limit)
        )
    else:
        statement = (
            select(Job, Company.name.label("recruited_to_name"))
            .outerjoin(Company, Job.recruited_to_id == Company.id)
            .where(Job.employer_id == employer_id, Job.status != Status.CLOSED)
            .offset(skip)
            .limit(limit)
        )

    results = db.exec(statement).all()
    return [
        JobRead(**job.__dict__, recruited_to_name=recruited_to_name)
        for job, recruited_to_name in results
    ]


def get_jobs_by_employer(
    db: Session, employer_id: int, skip: int = 0, limit: int = 100, closed: bool = False
) -> List[JobRead]:
    if closed:
        statement = (
            select(Job, Company.name.label("recruited_to_name"))
            .outerjoin(Company, Job.recruited_to_id == Company.id)
            .where(Job.employer_id == employer_id)
            .offset(skip)
            .limit(limit)
        )
    else:
        statement = (
            select(Job, Company.name.label("recruited_to_name"))
            .outerjoin(Company, Job.recruited_to_id == Company.id)
            .where(Job.employer_id == employer_id, Job.status != Status.CLOSED)
            .offset(skip)
            .limit(limit)
        )

    results = db.exec(statement).all()
    return [
        JobRead(**job.__dict__, recruited_to_name=recruited_to_name)
        for job, recruited_to_name in results
    ]


def get_jobs_by_status(
    db: Session, status: str, skip: int = 0, limit: int = 100
) -> List[Job]:
    statement = select(Job).where(Job.status == status).offset(skip).limit(limit)
    return db.exec(statement).all()


def create_job(db: Session, *, job_in: JobCreate) -> Job:
    db_job = Job.model_validate(job_in)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def update_job(
    db: Session, *, db_job: Job, job_in: Union[JobUpdate, Dict[str, Any]]
) -> Job:
    if isinstance(job_in, dict):
        update_data = job_in
    else:
        update_data = job_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_job, field, value)

    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job(db: Session, *, job_id: int) -> Optional[Job]:
    db_job = db.get(Job, job_id)
    if db_job:
        db.delete(db_job)
        db.commit()
    return db_job


def get_job_matches(db: Session, job_id: int, top_5: bool = False) -> List[tuple[Match, Candidate]]:
    # Get matches with candidates through applications since matches are linked to applications, not directly to jobs
    statement = (
        select(Match, Candidate)
        .join(Application, Match.application_id == Application.id)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .where(Application.job_id == job_id)
        .order_by(Match.score.desc())
        .limit(5 if top_5 else None)
    )
    return db.exec(statement).all()


def get_job_analytics(db: Session, job_id: int) -> JobAnalytics:
    """
    Get simple and meaningful analytics for a specific job.
    """
    # Get the job
    job = db.get(Job, job_id)
    if not job:
        raise ValueError(f"Job with id {job_id} not found")

    # Get all applications for this job
    applications = db.exec(
        select(Application).where(Application.job_id == job_id)
    ).all()

    # Get all matches for these applications
    application_ids = [app.id for app in applications] if applications else []
    matches = []
    if application_ids:
        matches = db.exec(
            select(Match).where(Match.application_id.in_(application_ids))
        ).all()

    # Get all interviews for these applications
    interviews = []
    if application_ids:
        interviews = db.exec(
            select(Interview).where(Interview.application_id.in_(application_ids))
        ).all()

    # Get unique candidates
    candidate_ids = (
        list(set([app.candidate_id for app in applications])) if applications else []
    )
    candidates = []
    if candidate_ids:
        candidates = db.exec(
            select(Candidate).where(Candidate.id.in_(candidate_ids))
        ).all()

    # Calculate basic metrics
    total_applications = len(applications)
    total_matches = len(matches)
    total_interviews = len(interviews)
    unique_candidates = len(candidates)

    # Calculate time-based metrics (last 7 and 30 days)
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    applications_last_7_days = sum(
        1 for app in applications if app.created_at and app.created_at >= seven_days_ago
    )
    applications_last_30_days = sum(
        1
        for app in applications
        if app.created_at and app.created_at >= thirty_days_ago
    )

    # Calculate match scores
    match_scores = [match.score for match in matches if match.score is not None]
    average_match_score = (
        sum(match_scores) / len(match_scores) if match_scores else None
    )
    top_match_score = max(match_scores) if match_scores else None

    # Group applications by status (status moved from match to application)
    applications_by_status = {}
    for application in applications:
        status = application.status.value if application.status else "pending"
        applications_by_status[status] = applications_by_status.get(status, 0) + 1

    # Group interviews by type and status
    interviews_by_type = {}
    interviews_by_status = {}
    for interview in interviews:
        # Handle interview type
        interview_type = interview.type or "unknown"
        interviews_by_type[interview_type] = (
            interviews_by_type.get(interview_type, 0) + 1
        )

        # Handle interview status
        interview_status = interview.status or "unknown"
        interviews_by_status[interview_status] = (
            interviews_by_status.get(interview_status, 0) + 1
        )

    # Count candidates with parsed resumes
    candidates_with_parsed_resumes = sum(
        1 for candidate in candidates if candidate.parsed_resume is not None
    )

    # Extract top skills from candidates (simplified)
    all_skills = []
    for candidate in candidates:
        if candidate.parsed_resume and hasattr(candidate.parsed_resume, "skills"):
            try:
                for skill in candidate.parsed_resume.skills or []:
                    if hasattr(skill, "name") and skill.name:
                        all_skills.append(skill.name.lower().strip())
            except:
                continue

    # Get top 10 most common skills
    skill_counter = Counter(all_skills)
    top_skills_from_candidates = [
        skill for skill, count in skill_counter.most_common(10)
    ]

    # Calculate conversion rates
    application_to_match_rate = (
        round((total_matches / total_applications * 100), 1)
        if total_applications > 0
        else 0.0
    )
    application_to_interview_rate = (
        round((total_interviews / total_applications * 100), 1)
        if total_applications > 0
        else 0.0
    )
    match_to_interview_rate = (
        round((total_interviews / total_matches * 100), 1) if total_matches > 0 else 0.0
    )
    
    # Get top 5 matches
    top_5_matches = db.exec(
        select(Match).where(Match.application_id.in_(application_ids))
        .order_by(Match.score.desc())
        .limit(5)
    ).all()

    return JobAnalytics(
        job_id=job.id,
        job_title=job.title,
        job_status=job.status.value if job.status else "draft",
        # Application metrics
        total_applications=total_applications,
        applications_by_status=applications_by_status,
        # Matching metrics
        total_matches=total_matches,
        average_match_score=average_match_score,
        top_match_score=top_match_score,
        # Interview metrics
        total_interviews=total_interviews,
        interviews_by_type=interviews_by_type,
        interviews_by_status=interviews_by_status,
        # Candidate metrics
        unique_candidates=unique_candidates,
        candidates_with_parsed_resumes=candidates_with_parsed_resumes,
        top_skills_from_candidates=top_skills_from_candidates,
        # Time-based metrics
        applications_last_7_days=applications_last_7_days,
        applications_last_30_days=applications_last_30_days,
        # Conversion metrics
        application_to_match_rate=application_to_match_rate,
        application_to_interview_rate=application_to_interview_rate,
        match_to_interview_rate=match_to_interview_rate,
        top_5_matches=top_5_matches,
    )
