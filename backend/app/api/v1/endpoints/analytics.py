from fastapi import APIRouter, Depends, HTTPException, Request, status
from core.security import TokenData
from sqlmodel import Session, select, func
from sqlalchemy.orm import joinedload
from core.database import get_session
from models.models import Company, Job, Application, Interview
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


class CompanyAnalyticsData(BaseModel):
    total_jobs: int
    total_applications: int
    total_interviews: int
    hire_rate: float
    applications_over_time: List[ApplicationsOverTimeData]
    job_performance: List[JobPerformanceData]


@router.get("/company/", response_model=CompanyAnalyticsData)
def get_company_analytics(request: Request, db: Session = Depends(get_session)):
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
         raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Could not validate credentials"
         )
    
    employer_id = current_user.employer_id   
    # 1. Total Jobs
    total_jobs = db.exec(select(func.count(Job.id)).where(Job.employer_id == employer_id)).one()

    # 2. Total Applications
    total_applications = db.exec(
        select(func.count(Application.id))
        .join(Job)
        .where(Job.employer_id == employer_id)
    ).one()

    # 3. Total Interviews
    total_interviews = db.exec(
        select(func.count(Interview.id))
        .join(Application)
        .join(Job)
        .where(Job.employer_id == employer_id)
    ).one()

    # 4. Hire Rate (dummy data as requested)
    hire_rate = 68.0

    # 5. Applications Over Time (last 6 months)
    applications_over_time_data = []
    today = datetime.utcnow()
    for i in range(6):
        month_end = today - timedelta(days=today.day)
        month_start = (month_end - timedelta(days=1)).replace(day=1)
        
        if i > 0:
            month_start = (datetime(today.year, today.month, 1) - timedelta(days=i*30)).replace(day=1)
            next_month = month_start.replace(day=28) + timedelta(days=4) # to get to next month
            month_end = next_month - timedelta(days=next_month.day)


        count = db.exec(
            select(func.count(Application.id))
            .join(Job)
            .where(Job.employer_id == employer_id)
            .where(Application.created_at >= month_start)
            .where(Application.created_at <= month_end)
        ).one()
        applications_over_time_data.append(
            ApplicationsOverTimeData(month=month_start.strftime("%b"), applications=count)
        )
    applications_over_time_data.reverse()

    # 6. Job Performance (top 5)
    job_performance_query = (
        select(Job.title, func.count(Application.id).label("application_count"))
        .join(Application, Job.id == Application.job_id)
        .where(Job.employer_id == employer_id)
        .group_by(Job.title)
        .order_by(func.count(Application.id).desc())
        .limit(5)
    )
    job_performance_results = db.exec(job_performance_query).all()
    job_performance_data = [
        JobPerformanceData(job=title, applications=count)
        for title, count in job_performance_results
    ]

    return CompanyAnalyticsData(
        total_jobs=total_jobs,
        total_applications=total_applications,
        total_interviews=total_interviews,
        hire_rate=hire_rate,
        applications_over_time=applications_over_time_data,
        job_performance=job_performance_data,
    )