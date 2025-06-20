from typing import Any, Dict, Optional, Union, List
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import true
from sqlmodel import select

from models.models import Interview, Application, Job, Status, InterviewStatus
from schemas import InterviewCreate, InterviewUpdate
from services.email_service import email_service


async def _send_interview_email(interview: Interview, action: str, db: Session) -> None:
    """
    Send email notification for interview operations to both candidate and interviewer.
    
    Args:
        interview: Interview object
        action: Type of action ('created', 'updated', 'deleted')
        db: Database session
    """
    try:
        # Load the application with candidate and job details
        db.refresh(interview, ["application"])
        if not interview.application:
            return
            
        db.refresh(interview.application, ["candidate", "job"])
        if not interview.application.candidate or not interview.application.job:
            return
            
        candidate = interview.application.candidate
        job = interview.application.job
        
        # Load the employer relationship for the job
        db.refresh(job, ["employer"])
        
        # Load the interviewer relationship
        if interview.interviewer_id:
            db.refresh(interview, ["interviewer"])
        
        # Format interview date
        interview_date = interview.date.strftime("%B %d, %Y at %I:%M %p")
        
        # Send email to candidate
        await _send_candidate_interview_email(interview, action, candidate, job, interview_date)
        
        # Send email to interviewer if exists
        if interview.interviewer:
            await _send_interviewer_interview_email(interview, action, candidate, job, interview_date)
        
    except Exception as e:
        # Log error but don't fail the operation
        print(f"Failed to send interview email: {str(e)}")


async def _send_candidate_interview_email(interview: Interview, action: str, candidate, job, interview_date: str) -> None:
    """Send interview notification email to the candidate."""
    subject = f"Interview {action.title()} - {job.title}"
    
    # Create HTML content for candidate
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Interview {action.title()}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .container {{
                background-color: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                color: #6366f1;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 28px;
                font-weight: bold;
                color: #1f2937;
                margin-bottom: 10px;
            }}
            .subtitle {{
                color: #6b7280;
                font-size: 16px;
            }}
            .interview-details {{
                background-color: #f3f4f6;
                padding: 25px;
                border-radius: 10px;
                margin: 25px 0;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                padding: 8px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .detail-label {{
                font-weight: bold;
                color: #374151;
            }}
            .detail-value {{
                color: #6b7280;
            }}
            .action-created {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            }}
            .action-updated {{
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            }}
            .action-deleted {{
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                color: #6b7280;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🏢 HR Platform</div>
                <h1 class="title">Interview {action.title()}</h1>
                <p class="subtitle">Hello {candidate.full_name}!</p>
            </div>

            <div class="action-{action}">
                <strong>📅 Your interview has been {action}</strong>
            </div>

            <div class="interview-details">
                <h3 style="margin-top: 0; color: #374151;">Interview Details</h3>
                <div class="detail-row">
                    <span class="detail-label">Position:</span>
                    <span class="detail-value">{job.title}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Company:</span>
                    <span class="detail-value">{job.employer.name if job.employer else 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Date & Time:</span>
                    <span class="detail-value">{interview_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">{interview.type.replace('_', ' ').title()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value">{interview.status.replace('_', ' ').title()}</span>
                </div>
                {"<div class='detail-row'><span class='detail-label'>Interviewer:</span><span class='detail-value'>" + interview.interviewer.full_name + "</span></div>" if interview.interviewer else ""}
                {"<div class='detail-row'><span class='detail-label'>Notes:</span><span class='detail-value'>" + interview.notes + "</span></div>" if interview.notes else ""}
            </div>

            <div class="footer">
                <p>This is an automated message. Please contact HR if you have any questions.</p>
                <p>© 2025 HR Platform. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Create text content as fallback
    text_content = f"""
    Interview {action.title()} - HR Platform

    Hello {candidate.full_name}!

    Your interview has been {action}.

    Interview Details:
    - Position: {job.title}
    - Company: {job.employer.name if job.employer else 'N/A'}
    - Date & Time: {interview_date}
    - Type: {interview.type.replace('_', ' ').title()}
    - Status: {interview.status.replace('_', ' ').title()}
    {"- Interviewer: " + interview.interviewer.full_name if interview.interviewer else ""}
    {"- Notes: " + interview.notes if interview.notes else ""}

    Please contact HR if you have any questions.

    ---
    HR Platform
    This is an automated message.
    """

    # Send email to candidate
    await email_service.send_email(
        to_email=candidate.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


async def _send_interviewer_interview_email(interview: Interview, action: str, candidate, job, interview_date: str) -> None:
    """Send interview notification email to the interviewer."""
    subject = f"Interview {action.title()} - {job.title} with {candidate.full_name}"
    
    # Create HTML content for interviewer
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Interview {action.title()}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .container {{
                background-color: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                color: #6366f1;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 28px;
                font-weight: bold;
                color: #1f2937;
                margin-bottom: 10px;
            }}
            .subtitle {{
                color: #6b7280;
                font-size: 16px;
            }}
            .interview-details {{
                background-color: #f3f4f6;
                padding: 25px;
                border-radius: 10px;
                margin: 25px 0;
            }}
            .detail-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                padding: 8px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .detail-label {{
                font-weight: bold;
                color: #374151;
            }}
            .detail-value {{
                color: #6b7280;
            }}
            .action-created {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            }}
            .action-updated {{
                background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            }}
            .action-deleted {{
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                color: #6b7280;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🏢 HR Platform</div>
                <h1 class="title">Interview {action.title()}</h1>
                <p class="subtitle">Hello {interview.interviewer.full_name}!</p>
            </div>

            <div class="action-{action}">
                <strong>📅 Interview has been {action}</strong>
            </div>

            <div class="interview-details">
                <h3 style="margin-top: 0; color: #374151;">Interview Details</h3>
                <div class="detail-row">
                    <span class="detail-label">Position:</span>
                    <span class="detail-value">{job.title}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Company:</span>
                    <span class="detail-value">{job.employer.name if job.employer else 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Candidate:</span>
                    <span class="detail-value">{candidate.full_name}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Candidate Email:</span>
                    <span class="detail-value">{candidate.email}</span>
                </div>
                {"<div class='detail-row'><span class='detail-label'>Candidate Phone:</span><span class='detail-value'>" + candidate.phone + "</span></div>" if candidate.phone else ""}
                <div class="detail-row">
                    <span class="detail-label">Date & Time:</span>
                    <span class="detail-value">{interview_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">{interview.type.replace('_', ' ').title()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value">{interview.status.replace('_', ' ').title()}</span>
                </div>
                {"<div class='detail-row'><span class='detail-label'>Notes:</span><span class='detail-value'>" + interview.notes + "</span></div>" if interview.notes else ""}
            </div>

            <div class="footer">
                <p>This is an automated message from the HR Platform.</p>
                <p>© 2025 HR Platform. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Create text content as fallback
    text_content = f"""
    Interview {action.title()} - HR Platform

    Hello {interview.interviewer.full_name}!

    An interview has been {action}.

    Interview Details:
    - Position: {job.title}
    - Company: {job.employer.name if job.employer else 'N/A'}
    - Candidate: {candidate.full_name}
    - Candidate Email: {candidate.email}
    {"- Candidate Phone: " + candidate.phone if candidate.phone else ""}
    - Date & Time: {interview_date}
    - Type: {interview.type.replace('_', ' ').title()}
    - Status: {interview.status.replace('_', ' ').title()}
    {"- Notes: " + interview.notes if interview.notes else ""}

    ---
    HR Platform
    This is an automated message.
    """

    # Send email to interviewer
    await email_service.send_email(
        to_email=interview.interviewer.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )


def create_interview(db: Session, *, obj_in: InterviewCreate) -> Interview:
    db_obj = Interview(**obj_in.model_dump())

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # Send email notification asynchronously
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_send_interview_email(db_obj, "created", db))
        loop.close()
    except Exception as e:
        print(f"Failed to send interview creation email: {str(e)}")
    
    return db_obj


def get_interview(db: Session, interview_id: int) -> Optional[Interview]:
    return db.query(Interview).filter(Interview.id == interview_id).first()


def get_interview_with_application(
    db: Session, interview_id: int
) -> Optional[Interview]:
    """Get interview with application details (candidate and job)"""
    statement = select(Interview).where(Interview.id == interview_id)
    interview = db.exec(statement).first()
    if interview:
        # Load application relationship and its nested relationships
        db.refresh(interview, ["application", "interviewer"])
        if interview.application:
            db.refresh(interview.application, ["candidate", "job"])
    return interview


def get_interviews(db: Session, skip: int = 0, limit: int = 100) -> List[Interview]:
    return db.query(Interview).offset(skip).limit(limit).all()


def get_interviews_by_employer_with_application(
    db: Session, employer_id: int, skip: int = 0, limit: int = 100
) -> List[Interview]:
    statement = (
        select(Interview.id, Interview.date, Interview.type, Interview.status, Interview.notes, Interview.interviewer_id, Interview.application_id, Interview.created_at, Interview.updated_at, Interview.employer_id)
        .where(Interview.status == InterviewStatus.SCHEDULED)
        .join(Application)
        .join(Job)
        .where(Job.status != Status.CLOSED)
        .where(Job.employer_id == employer_id)
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()

def get_interviews_with_application(
    db: Session, skip: int = 0, limit: int = 100, employer_id: int = None
) -> List[Interview]:
    """Get interviews with application details (candidate and job) loaded"""
    statement = (
        select(Interview)
        .where(Interview.status.in_(["SCHEDULED", "scheduled"]))
        .join(Application)
        .join(Job)
        .where(Job.status != Status.CLOSED)
        .where(Job.employer_id == employer_id)
        .offset(skip)
        .limit(limit)
    )
    interviews = db.exec(statement).all()

    # Load relationships for each interview
    for interview in interviews:
        db.refresh(interview, ["application", "interviewer"])
        if interview.application:
            db.refresh(interview.application, ["candidate", "job"])

    return interviews


def update_interview(
    db: Session, *, db_obj: Interview, obj_in: InterviewUpdate
) -> Interview:
    obj_data = obj_in.model_dump(exclude_unset=True)
    for field, value in obj_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    # Send email notification asynchronously
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_send_interview_email(db_obj, "updated", db))
        loop.close()
    except Exception as e:
        print(f"Failed to send interview update email: {str(e)}")
    
    return db_obj


def delete_interview(db: Session, interview_id: int) -> Optional[Interview]:
    obj = db.query(Interview).filter(Interview.id == interview_id).first()
    if obj:
        # Send email notification before deletion
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_send_interview_email(obj, "deleted", db))
            loop.close()
        except Exception as e:
            print(f"Failed to send interview deletion email: {str(e)}")
        
        db.delete(obj)
        db.commit()
    return obj


def get_interviews_by_application_id(
    db: Session, application_id: int
) -> List[Interview]:
    return db.query(Interview).filter(Interview.application_id == application_id).all()


def get_interviews_by_application_id_with_details(
    db: Session, application_id: int
) -> List[Interview]:
    """Get interviews by application ID with application details (candidate and job) loaded"""
    statement = select(Interview).where(Interview.application_id == application_id)
    interviews = db.exec(statement).all()

    # Load relationships for each interview
    for interview in interviews:
        db.refresh(interview, ["application", "interviewer"])
        if interview.application:
            db.refresh(interview.application, ["candidate", "job"])

    return interviews


def get_interviews_by_candidate(
    db: Session, candidate_id: int, skip: int = 0, limit: int = 100
) -> List[Interview]:
    """Get interviews by candidate ID through applications"""
    from models.models import Application
    
    statement = (
        select(Interview)
        .join(Application, Interview.application_id == Application.id)
        .where(Application.candidate_id == candidate_id)
        .offset(skip)
        .limit(limit)
    )
    return db.exec(statement).all()

def update_interview_status(db: Session, *, db_obj: Interview, obj_in: InterviewUpdate) -> Interview:
    obj_data = obj_in.model_dump(exclude_unset=True)
    for field, value in obj_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj