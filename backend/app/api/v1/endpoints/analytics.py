from fastapi import APIRouter, Depends, HTTPException, Request, status
from core.security import TokenData
from sqlmodel import Session, select, func, case, and_
from sqlalchemy.orm import joinedload
from core.database import get_session
from models.models import (
    Company,
    Job,
    Application,
    Interview,
    Status,
    ApplicationStatus,
    Candidate,
    Match,
)
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


class JobPerformanceData(BaseModel):
    job: str
    applications: int


class ApplicationsOverTimeData(BaseModel):
    month: str
    applications: int


class RecentJobData(BaseModel):
    title: str
    applications: int
    status: str
    created_at: datetime


class ApplicationStatusData(BaseModel):
    status: str
    count: int


class InterviewStatusData(BaseModel):
    status: str
    count: int


class CompanyAnalyticsData(BaseModel):
    total_jobs: int
    total_open_jobs: int
    total_applications: int
    total_interviews: int
    interviews_by_status: List[InterviewStatusData]
    hire_rate: float
    applications_over_time: List[ApplicationsOverTimeData]
    job_performance: List[JobPerformanceData]
    recent_jobs: List[RecentJobData]
    applications_by_status: List[ApplicationStatusData]
    total_candidates: int
    average_match_score: float


@router.get("/company/", response_model=CompanyAnalyticsData)
def get_company_analytics(request: Request, db: Session = Depends(get_session)):
    try:
        current_user: Optional[TokenData] = request.state.user
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        employer_id = current_user.employer_id

        # 1. Total Jobs and Open Jobs
        total_jobs_query = select(
            func.count(Job.id),
            func.count(case((Job.status != Status.CLOSED, Job.id), else_=None)),
        ).where(Job.employer_id == employer_id)
        total_jobs, total_open_jobs = db.exec(total_jobs_query).one()

        # 2. Total Applications
        total_applications = db.exec(
            select(func.count(Application.id))
            .join(Job)
            .where(Job.employer_id == employer_id)
        ).one()

        # 3. Total Interviews and by status
        interviews_by_status_query = (
            select(Interview.status, func.count(Interview.id))
            .join(Application)
            .join(Job)
            .where(Job.employer_id == employer_id)
            .group_by(Interview.status)
        )
        interviews_by_status_results = db.exec(interviews_by_status_query).all()

        interviews_by_status_data = [
            InterviewStatusData(status=status if status else "unknown", count=count)
            for status, count in interviews_by_status_results
        ]

        total_interviews = sum(item.count for item in interviews_by_status_data)

        # 4. Total distinct candidates
        total_candidates = db.exec(
            select(func.count(func.distinct(Candidate.id)))
            .join(Application, Candidate.id == Application.candidate_id)
            .join(Job, Application.job_id == Job.id)
            .where(Job.employer_id == employer_id)
        ).one()

        # 5. Calculate real hire rate
        hired_applications = db.exec(
            select(func.count(Application.id))
            .join(Job)
            .where(Job.employer_id == employer_id)
            .where(Application.status == ApplicationStatus.HIRED)
        ).one()

        hire_rate = (
            round((hired_applications / total_applications) * 100, 1)
            if total_applications > 0
            else 0.0
        )
        # 6. Applications Over Time (last 6 months)
        applications_over_time_data = []
        today = datetime.utcnow()

        for i in range(6):
            # Calculate month boundaries
            if i == 0:
                month_start = today.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
                if today.month == 12:
                    month_end = today.replace(
                        year=today.year + 1, month=1, day=1
                    ) - timedelta(days=1)
                else:
                    month_end = today.replace(month=today.month + 1, day=1) - timedelta(
                        days=1
                    )
            else:
                # Go back i months
                year = today.year
                month = today.month - i
                if month <= 0:
                    month += 12
                    year -= 1
                month_start = datetime(year, month, 1)

                # Calculate month end
                if month == 12:
                    month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = datetime(year, month + 1, 1) - timedelta(days=1)

            count = db.exec(
                select(func.count(Application.id))
                .join(Job)
                .where(Job.employer_id == employer_id)
                .where(Application.created_at >= month_start)
                .where(Application.created_at <= month_end)
            ).one()

            applications_over_time_data.append(
                ApplicationsOverTimeData(
                    month=month_start.strftime("%b"), applications=count
                )
            )

        applications_over_time_data.reverse()

        # 7. Job Performance (top 5 jobs by application count)
        job_performance_query = (
            select(Job.title, func.count(Application.id).label("application_count"))
            .join(Application, Job.id == Application.job_id)
            .where(Job.employer_id == employer_id)
            .group_by(Job.id, Job.title)
            .order_by(func.count(Application.id).desc())
            .limit(5)
        )
        job_performance_results = db.exec(job_performance_query).all()
        job_performance_data = [
            JobPerformanceData(job=title, applications=count)
            for title, count in job_performance_results
        ]

        # 8. Recent Jobs (last 5 jobs with application counts)
        recent_jobs_query = (
            select(
                Job.title,
                func.count(Application.id).label("application_count"),
                Job.status,
                Job.created_at,
            )
            .outerjoin(Application, Job.id == Application.job_id)
            .where(Job.employer_id == employer_id)
            .group_by(Job.id, Job.title, Job.status, Job.created_at)
            .order_by(Job.created_at.desc())
            .limit(5)
        )
        recent_jobs_results = db.exec(recent_jobs_query).all()
        recent_jobs_data = [
            RecentJobData(
                title=title,
                applications=count,
                status=status.value if status else "draft",
                created_at=created_at,
            )
            for title, count, status, created_at in recent_jobs_results
        ]

        # 9. Applications by status
        applications_by_status_query = (
            select(Application.status, func.count(Application.id).label("status_count"))
            .join(Job)
            .where(Job.employer_id == employer_id)
            .group_by(Application.status)
        )
        applications_by_status_results = db.exec(applications_by_status_query).all()
        applications_by_status_data = [
            ApplicationStatusData(
                status=status.value if status else "pending", count=count
            )
            for status, count in applications_by_status_results
        ]

        # 10. Average match score
        average_match_score = (
            db.exec(
                select(func.avg(Match.score))
                .join(Application)
                .join(Job)
                .where(Job.employer_id == employer_id)
                .where(Match.score.isnot(None))
            ).one()
            or 0.0
        )*100

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return CompanyAnalyticsData(
        total_jobs=total_jobs,
        total_open_jobs=total_open_jobs,
        total_applications=total_applications,
        total_interviews=total_interviews,
        interviews_by_status=interviews_by_status_data,
        hire_rate=hire_rate,
        applications_over_time=applications_over_time_data,
        job_performance=job_performance_data,
        recent_jobs=recent_jobs_data,
        applications_by_status=applications_by_status_data,
        total_candidates=total_candidates,
        average_match_score=round(average_match_score, 2),
    )
