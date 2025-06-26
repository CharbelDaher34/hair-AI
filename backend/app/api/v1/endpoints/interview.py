from datetime import datetime
from typing import Any, List, Optional

from core.database import get_session
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from crud import crud_interview
from schemas import (
    InterviewCreate,
    InterviewUpdate,
    InterviewRead,
    InterviewReadWithApplication,
)
from core.security import TokenData, verify_interview_review_token  # For type hinting

router = APIRouter()

class InterviewerReviewUpdate(BaseModel):
    interviewer_review: str

class InterviewReviewFormSubmission(BaseModel):
    review_text: str
    token: str


@router.post("/", response_model=InterviewRead)
def create_interview(
    *,
    db: Session = Depends(get_session),
    interview_in: InterviewCreate,
    request: Request,
) -> Any:
    """
    Create new interview.
    """
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not interview_in.interviewer_id:
        interview_in.interviewer_id = current_user.employer_id
    interview = crud_interview.create_interview(db=db, obj_in=interview_in)
    return interview


@router.get(
    "/by-application/{application_id}",
    response_model=List[InterviewReadWithApplication],
)
def read_interviews_by_application(
    *,
    db: Session = Depends(get_session),
    application_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get interviews by application ID with application details.
    """
    interviews = crud_interview.get_interviews_by_application_id_with_details(
        db=db, application_id=application_id
    )
    return interviews


@router.get("/{interview_id}", response_model=InterviewReadWithApplication)
def read_interview(
    *,
    db: Session = Depends(get_session),
    interview_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get interview by ID with application details.
    """
    interview = crud_interview.get_interview_with_application(
        db=db, interview_id=interview_id
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    # if not crud.user.is_superuser(current_user) and (interview.application_id not in [app.id for app in current_user.applications]):
    #     raise HTTPException(status_code=400, detail="Not enough permissions")
    return interview


@router.get("/", response_model=List[InterviewReadWithApplication])
def read_interviews(
    request: Request,
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve interviews with application details.
    """
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    interviews = crud_interview.get_interviews_with_application(
        db, skip=skip, limit=limit, employer_id=current_user.employer_id
    )

    return interviews


@router.put("/{interview_id}", response_model=InterviewRead)
def update_interview(
    *,
    db: Session = Depends(get_session),
    interview_id: int,
    interview_in: InterviewUpdate,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an interview.
    """
    interview = crud_interview.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    # if not crud.user.is_superuser(current_user) and (interview.application.candidate_id != current_user.id): # type: ignore
    #     raise HTTPException(status_code=400, detail="Not enough permissions")
    interview = crud_interview.update_interview(
        db=db, db_obj=interview, obj_in=interview_in
    )
    return interview

@router.patch("/{interview_id}/status", response_model=InterviewRead)
def update_interview_status(
    *,
    db: Session = Depends(get_session),
    interview_id: int,
    reason: Optional[str] = None,
    interview_in: InterviewUpdate,
) -> Any:
    """
    Update interview status.
    """
    interview = crud_interview.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    interview_in = InterviewUpdate(status=interview_in.status,updated_at=datetime.now())
    if interview_in.status in ["cancelled", "canceled","Canceled","Cancelled"]:
        interview = crud_interview.update_interview(
            db=db, db_obj=interview, obj_in=interview_in, notify=True, reason=reason
        )
    else:
        interview = crud_interview.update_interview(
            db=db, db_obj=interview, obj_in=interview_in, notify=True
        )
    return interview

@router.delete("/{interview_id}", response_model=InterviewRead)
def delete_interview(
    *,
    db: Session = Depends(get_session),
    interview_id: int,
    # current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an interview.
    """
    interview = crud_interview.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    # if not crud.user.is_superuser(current_user) and (interview.application.candidate_id != current_user.id): # type: ignore
    #     raise HTTPException(status_code=400, detail="Not enough permissions")
    interview = crud_interview.delete_interview(db=db, interview_id=interview_id)
    return interview

@router.patch("/{interview_id}/review", response_model=InterviewRead)
def update_interviewer_review(
    *,
    db: Session = Depends(get_session),
    interview_id: int,
    review_data: InterviewerReviewUpdate,
    request: Request,
) -> Any:
    """
    Update interviewer review for an interview.
    Only the interviewer or HR from the same company can update the review.
    """
    current_user: Optional[TokenData] = request.state.user
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    interview = crud_interview.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Check if the current user is the interviewer or has HR permissions
    if (interview.interviewer_id != current_user.id and 
        current_user.user_type != "hr"):
        raise HTTPException(status_code=403, detail="Not authorized to update this review")
    
    # Update only the interviewer_review field
    interview_update = InterviewUpdate(
        interviewer_review=review_data.interviewer_review,
        updated_at=datetime.now()
    )
    
    interview = crud_interview.update_interview(
        db=db, db_obj=interview, obj_in=interview_update
    )
    return interview

@router.get("/review-form/{token}", response_class=HTMLResponse)
def get_interview_review_form(token: str, db: Session = Depends(get_session)) -> str:
    """
    Serve the interview review form using a secure token
    """
    try:
        # Verify token and get interview details
        token_data = verify_interview_review_token(token)
        interview_id = token_data["interview_id"]
        interviewer_id = token_data["interviewer_id"]
        
        # Get interview details
        interview = crud_interview.get_interview_with_application(db=db, interview_id=interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Verify the interviewer
        if interview.interviewer_id != interviewer_id:
            raise HTTPException(status_code=403, detail="Unauthorized access")
        
        # Get current review if exists
        current_review = interview.interviewer_review or ""
        
        # Create HTML form
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Interview Review Form</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
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
                    border-bottom: 2px solid #e9ecef;
                    padding-bottom: 20px;
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
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                    padding: 5px 0;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #374151;
                }}
                .detail-value {{
                    color: #6b7280;
                }}
                .form-group {{
                    margin-bottom: 20px;
                }}
                label {{
                    display: block;
                    margin-bottom: 8px;
                    font-weight: bold;
                    color: #374151;
                }}
                textarea {{
                    width: 100%;
                    min-height: 200px;
                    padding: 12px;
                    border: 2px solid #e5e7eb;
                    border-radius: 8px;
                    font-size: 14px;
                    font-family: inherit;
                    resize: vertical;
                    box-sizing: border-box;
                }}
                textarea:focus {{
                    outline: none;
                    border-color: #6366f1;
                    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
                }}
                .btn {{
                    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                    color: white;
                    padding: 12px 30px;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
                }}
                .btn:disabled {{
                    background: #9ca3af;
                    cursor: not-allowed;
                    transform: none;
                    box-shadow: none;
                }}
                .success-message {{
                    background-color: #d1fae5;
                    color: #065f46;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #10b981;
                    display: none;
                }}
                .error-message {{
                    background-color: #fee2e2;
                    color: #991b1b;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #ef4444;
                    display: none;
                }}
                .instructions {{
                    background-color: #eff6ff;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #3b82f6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🏢 HR Platform</div>
                    <h1 class="title">Interview Review Form</h1>
                    <p class="subtitle">Please provide your feedback on the interview</p>
                </div>

                <div class="interview-details">
                    <h3 style="margin-top: 0; color: #374151;">Interview Details</h3>
                    <div class="detail-row">
                        <span class="detail-label">Candidate:</span>
                        <span class="detail-value">{interview.application.candidate.full_name if interview.application and interview.application.candidate else 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Position:</span>
                        <span class="detail-value">{interview.application.job.title if interview.application and interview.application.job else 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Date:</span>
                        <span class="detail-value">{interview.date.strftime('%B %d, %Y at %I:%M %p')}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Type:</span>
                        <span class="detail-value">{interview.type.replace('_', ' ').title()}</span>
                    </div>
                </div>

                <div class="instructions">
                    <h4 style="margin-top: 0;">📝 Review Guidelines</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Provide honest and constructive feedback about the candidate's performance</li>
                        <li>Include specific examples and observations from the interview</li>
                        <li>Comment on technical skills, communication, and cultural fit</li>
                        <li>Mention any concerns or standout qualities</li>
                        <li>Your review is confidential and will only be visible to HR and other interviewers</li>
                    </ul>
                </div>

                <form id="reviewForm">
                    <div class="form-group">
                        <label for="review_text">Your Interview Review *</label>
                        <textarea 
                            id="review_text" 
                            name="review_text" 
                            required 
                            placeholder="Please share your detailed feedback about the candidate's performance during the interview..."
                        >{current_review}</textarea>
                    </div>
                    
                    <input type="hidden" name="token" value="{token}">
                    
                    <button type="submit" class="btn" id="submitBtn">
                        💾 Submit Review
                    </button>
                </form>

                <div id="successMessage" class="success-message">
                    ✅ Your review has been submitted successfully! Thank you for your feedback.
                </div>

                <div id="errorMessage" class="error-message">
                    ❌ There was an error submitting your review. Please try again.
                </div>
            </div>

            <script>
                document.getElementById('reviewForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const submitBtn = document.getElementById('submitBtn');
                    const successMessage = document.getElementById('successMessage');
                    const errorMessage = document.getElementById('errorMessage');
                    
                    // Hide previous messages
                    successMessage.style.display = 'none';
                    errorMessage.style.display = 'none';
                    
                    // Disable submit button
                    submitBtn.disabled = true;
                    submitBtn.textContent = '⏳ Submitting...';
                    
                    try {{
                        const formData = new FormData(this);
                        const response = await fetch('/api/v1/interviews/submit-review', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                review_text: formData.get('review_text'),
                                token: formData.get('token')
                            }})
                        }});
                        
                        if (response.ok) {{
                            successMessage.style.display = 'block';
                            submitBtn.textContent = '✅ Review Submitted';
                        }} else {{
                            throw new Error('Failed to submit review');
                        }}
                    }} catch (error) {{
                        console.error('Error:', error);
                        errorMessage.style.display = 'block';
                        submitBtn.disabled = false;
                        submitBtn.textContent = '💾 Submit Review';
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        # Return error page
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Access Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <h1 class="error">Access Error</h1>
            <p>Invalid or expired review link. Please contact HR for assistance.</p>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """
        return error_html

@router.post("/submit-review")
def submit_interview_review(
    review_submission: InterviewReviewFormSubmission,
    db: Session = Depends(get_session)
) -> dict:
    """
    Submit interview review via the form
    """
    print(review_submission)
    try:
        # Verify token
        token_data = verify_interview_review_token(review_submission.token)
        interview_id = token_data["interview_id"]
        interviewer_id = token_data["interviewer_id"]
        
        # Get interview
        interview = crud_interview.get_interview(db=db, interview_id=interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Verify interviewer
        if interview.interviewer_id != interviewer_id:
            print("tomato is food")
            raise HTTPException(status_code=403, detail="Unauthorized access")
        
        # Update the review
        interview_update = InterviewUpdate(
            interviewer_review=review_submission.review_text,
            updated_at=datetime.now()
        )
        
        crud_interview.update_interview(
            db=db, db_obj=interview, obj_in=interview_update
        )
        
        return {"message": "Review submitted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
