from functools import reduce
from typing import List, Annotated
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
    Form,
    Request,
    BackgroundTasks,
)
from fastapi.responses import FileResponse
import shutil
import tempfile
import os
from sqlmodel import Session, select
import base64
import time
import json
from typing import Optional
from pydantic import BaseModel, EmailStr
from crud import crud_interview, crud_application
from schemas import ApplicationRead
from schemas import InterviewRead
from core.auth_middleware import TokenData
from core.database import get_session, engine
from core.config import RESUME_STORAGE_DIR
from crud import crud_candidate
from schemas import CandidateCreate, CandidateUpdate, CandidateRead, CandidateWithDetails
from models.models import Candidate
from utils.file_utils import save_resume_file, get_resume_file_path, delete_resume_file
from models.candidate_pydantic import CandidateResume
from services.resume_upload import AgentClient
from services.otp_service import otp_service

router = APIRouter()


# Pydantic models for OTP endpoints
class SendOTPRequest(BaseModel):
    email: EmailStr
    full_name: str = ""


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str


class OTPStatusResponse(BaseModel):
    exists: bool
    verified: bool
    expired: bool
    attempts: int
    remaining_attempts: int
    expires_at: Optional[str] = None


def parse_resume_background(
    candidate_id: int, resume_file_path: str, max_retries: int = 3
):
    """
    Background task to parse resume and update candidate record.

    Args:
        candidate_id: ID of the candidate
        resume_file_path: Path to the saved resume file
        max_retries: Maximum number of retry attempts
    """
    for attempt in range(max_retries):
        try:
            print(
                f"[Background] Starting resume parsing for candidate {candidate_id} (attempt {attempt + 1}/{max_retries})"
            )

            # Ensure the resume_file_path is absolute for the parser client
            absolute_resume_file_path = os.path.abspath(resume_file_path)
            print(
                f"[Background] Absolute resume file path: {absolute_resume_file_path}"
            )

            # Verify file exists before parsing
            if not os.path.exists(absolute_resume_file_path):
                print(
                    f"[Background] Resume file not found: {absolute_resume_file_path}"
                )
                return

            # Use AgentClient to parse the resume
            system_prompt = "Extract structured information from resumes. Focus on contact details, skills, and work experience."
            schema = CandidateResume.model_json_schema()

            print(f"[Background] Creating parser client for candidate {candidate_id}")
            parser_client = AgentClient(
                system_prompt, schema, [absolute_resume_file_path]
            )

            print(f"[Background] Starting parsing for candidate {candidate_id}")
            parsed_result = parser_client.parse()

            print(f"[Background] Parsing completed for candidate {candidate_id}")
            print(f"[Background] Parsed result type: {type(parsed_result)}")

            if parsed_result is None:
                print(
                    f"[Background] Parsing returned None for candidate {candidate_id} - API may have failed"
                )
                if attempt < max_retries - 1:
                    print(f"[Background] Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                else:
                    print(
                        f"[Background] Max retries reached for candidate {candidate_id}"
                    )
                    return

            if isinstance(parsed_result, dict):
                print(
                    f"[Background] Parsed resume result keys for candidate {candidate_id}: {list(parsed_result.keys())}"
                )
            else:
                print(
                    f"[Background] Unexpected result type for candidate {candidate_id}: {type(parsed_result)}"
                )

            # Update candidate with parsed resume data only if we have valid results
            if parsed_result:
                print(f"[Background] Updating database for candidate {candidate_id}")
                with Session(engine) as db:
                    candidate = crud_candidate.get_candidate(
                        db=db, candidate_id=candidate_id
                    )
                    if candidate:
                        crud_candidate.update_candidate(
                            db=db,
                            db_candidate=candidate,
                            candidate_in={"parsed_resume": parsed_result},
                        )
                        print(
                            f"[Background] Successfully updated candidate {candidate_id} with parsed resume data"
                        )
                        return  # Success - exit the retry loop
                    else:
                        print(
                            f"[Background] Candidate {candidate_id} not found for resume parsing update"
                        )
                        return
            else:
                print(
                    f"[Background] No valid parsing results for candidate {candidate_id} - skipping database update"
                )
                return

        except Exception as parse_err:
            print(
                f"[Background] Error parsing resume for candidate {candidate_id} (attempt {attempt + 1}): {str(parse_err)}"
            )
            print(f"[Background] Error type: {type(parse_err)}")

            if attempt < max_retries - 1:
                print(f"[Background] Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"[Background] Max retries reached for candidate {candidate_id}")
                import traceback

                print(f"[Background] Full traceback: {traceback.format_exc()}")
            # Don't raise exception in background task - just log the error


@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(request: SendOTPRequest) -> dict:
    """
    Send OTP to candidate's email for verification.
    """
    try:
        success = await otp_service.send_otp(request.email, request.full_name)
        
        if success:
            return {
                "success": True,
                "message": f"OTP sent successfully to {request.email}",
                "expires_in_minutes": otp_service.expire_minutes
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP. Please try again."
            )
    except Exception as e:
        print(f"[OTP] Error sending OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending OTP."
        )


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(request: VerifyOTPRequest) -> dict:
    """
    Verify OTP code for candidate's email.
    """
    try:
        result = otp_service.verify_otp(request.email, request.otp_code)
        
        if result['success']:
            return {
                "success": True,
                "message": result['message'],
                "verified": True
            }
        else:
            # Return appropriate HTTP status based on error type
            if result['error_code'] in ['OTP_EXPIRED', 'OTP_NOT_FOUND', 'TOO_MANY_ATTEMPTS']:
                status_code = status.HTTP_410_GONE  # Gone - need to request new OTP
            else:
                status_code = status.HTTP_400_BAD_REQUEST  # Bad request - invalid OTP
                
            raise HTTPException(
                status_code=status_code,
                detail={
                    "message": result['message'],
                    "error_code": result['error_code'],
                    "remaining_attempts": result.get('remaining_attempts')
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[OTP] Error verifying OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while verifying OTP."
        )


@router.get("/otp-status/{email}", response_model=OTPStatusResponse)
async def get_otp_status(email: str) -> OTPStatusResponse:
    """
    Get the current OTP status for an email.
    """
    try:
        status_data = otp_service.get_otp_status(email)
        return OTPStatusResponse(**status_data)
    except Exception as e:
        print(f"[OTP] Error getting OTP status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking OTP status."
        )


@router.get("/check-email/{email}")
async def check_candidate_email(email: str, db: Session = Depends(get_session)) -> dict:
    """
    Check if a candidate exists with the given email address.
    Returns candidate information if exists, otherwise indicates new candidate.
    """
    try:
        candidate = crud_candidate.get_candidate_by_email(db=db, email=email)
        
        if candidate:
            return {
                "exists": True,
                "candidate": {
                    "id": candidate.id,
                    "full_name": candidate.full_name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "has_resume": bool(candidate.resume_url),
                    "created_at": candidate.created_at.isoformat() if candidate.created_at else None
                }
            }
        else:
            return {
                "exists": False,
                "candidate": None
            }
    except Exception as e:
        print(f"[Candidate API] Error checking candidate email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking candidate email."
        )

class CandidateTable(BaseModel):
    candidate: CandidateRead
    applications_count: int
    interviews_count: int

@router.get("/table", response_model=List[CandidateTable])
def get_candidates_table(
    *,
    db: Session = Depends(get_session),
    request: Request,
) -> List[CandidateTable]:
    token_data: Optional[TokenData] = request.state.user
    
    # Check if user is authenticated
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    # Get candidates table data for the current employer
    candidates_data = crud_candidate.get_candidates_table_by_company(
        db=db, employer_id=token_data.employer_id
    )
    
    # Convert to CandidateTable objects
    result = []
    for data in candidates_data:
        result.append(CandidateTable(
            candidate=data["candidate"],
            applications_count=data["applications_count"],
            interviews_count=data["interviews_count"]
        ))
    
    return result
    

@router.post("/", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_in: Annotated[str, Form()],
    resume: Optional[UploadFile] = File(None),
    request: Request,
    background_tasks: BackgroundTasks,
) -> CandidateRead:
    token_data: Optional[TokenData] = request.state.user

    temp_resume_path = None
    try:
        candidate_data_json = json.loads(candidate_in)
        candidate_obj = CandidateCreate(**candidate_data_json)

        candidate_data = candidate_obj.model_dump()
        print(f"[Candidate API] Token data: {token_data}")

        # Check if email is verified (only for public applications, not HR-created candidates)
        if not token_data:  # Public application
            if not otp_service.is_email_verified(candidate_data['email']):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "message": "Email verification required. Please verify your email before submitting the application.",
                        "error_code": "EMAIL_NOT_VERIFIED",
                        "email": candidate_data['email']
                    }
                )

        # Check if candidate already exists by email
        existing_candidate = crud_candidate.get_candidate_by_email(db=db, email=candidate_data['email'])
        
        if existing_candidate:
            # For existing candidates, update their information if provided and different
            update_data = {}
            if candidate_data.get('full_name') and candidate_data['full_name'] != existing_candidate.full_name:
                update_data['full_name'] = candidate_data['full_name']
            if candidate_data.get('phone') and candidate_data['phone'] != existing_candidate.phone:
                # Check if phone is already used by another candidate
                phone_check = crud_candidate.check_candidate_exists(db=db, candidate_email="", phone=candidate_data['phone'])
                if phone_check and phone_check == "Phone already exists":
                    other_candidate = db.exec(select(Candidate).where(Candidate.phone == candidate_data['phone'])).first()
                    if other_candidate and other_candidate.id != existing_candidate.id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Phone number is already used by another candidate"
                        )
                update_data['phone'] = candidate_data['phone']
            
            # Update candidate if there are changes
            if update_data:
                candidate = crud_candidate.update_candidate(
                    db=db, db_candidate=existing_candidate, candidate_in=update_data
                )
            else:
                candidate = existing_candidate
                
            print(f"[Candidate API] Using existing candidate with ID: {candidate.id}")
        else:
            # Check for phone conflicts for new candidates
            phone_check = crud_candidate.check_candidate_exists(db=db, candidate_email="", phone=candidate_data['phone'])
            if phone_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=phone_check
                )
            
            # Create new candidate
            candidate = crud_candidate.create_candidate(
                db=db, candidate_in=CandidateCreate(**candidate_data)
            )
            print(f"[Candidate API] Created new candidate with ID: {candidate.id}")
        
        # If user is authenticated, associate candidate with their employer
        if token_data and token_data.employer_id:
            crud_candidate.add_candidate_to_employer(
                db=db, candidate_id=candidate.id, employer_id=token_data.employer_id
            )
            print(f"[Candidate API] Associated candidate {candidate.id} with employer {token_data.employer_id}")
        print(f"[Candidate API] Created candidate with ID: {candidate.id}")

        # If resume was uploaded, save it permanently with candidate ID as filename
        if resume:
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as temp_resume:
                    shutil.copyfileobj(resume.file, temp_resume)
                    temp_resume_path = temp_resume.name
                print(f"[Candidate API] Saved PDF to temp file: {temp_resume_path}")

                # Save resume permanently
                permanent_resume_path = save_resume_file(temp_resume_path, candidate.id)
                print(f"[Candidate API] Saved resume to: {permanent_resume_path}")

                # Update candidate with resume URL immediately
                candidate = crud_candidate.update_candidate(
                    db=db,
                    db_candidate=candidate,
                    candidate_in={"resume_url": permanent_resume_path},
                )

                # Schedule resume parsing as background task
                background_tasks.add_task(
                    parse_resume_background, candidate.id, permanent_resume_path
                )
                print(
                    f"[Candidate API] Scheduled background resume parsing for candidate {candidate.id}"
                )

            except Exception as save_err:
                print(f"[Candidate API] Error saving resume: {str(save_err)}")
                # Don't fail the entire operation if resume saving fails

    except HTTPException:
        raise
    except Exception as e:
        print("[Candidate API] General error:", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Clean up temp file
        if temp_resume_path:
            try:
                os.remove(temp_resume_path)
            except Exception:
                print(f"[Candidate API] Failed to remove temp file: {temp_resume_path}")

    return candidate





@router.get("/{candidate_id}", response_model=CandidateRead)
def read_candidate(
    *, db: Session = Depends(get_session), candidate_id: int
) -> CandidateRead:
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.get("/by-email/{email}", response_model=CandidateRead)
def read_candidate_by_email(
    *, db: Session = Depends(get_session), email: str
) -> CandidateRead:
    candidate = crud_candidate.get_candidate_by_email(db=db, email=email)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.get("/", response_model=List[CandidateRead])
def read_candidates(
    *, db: Session = Depends(get_session), skip: int = 0, limit: int = 100
) -> List[CandidateRead]:
    return crud_candidate.get_candidates(db=db, skip=skip, limit=limit)


@router.patch("/{candidate_id}", response_model=CandidateRead)
def update_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_id: int,
    candidate_in: CandidateUpdate,
) -> CandidateRead:
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return crud_candidate.update_candidate(
        db=db, db_candidate=candidate, candidate_in=candidate_in
    )


@router.delete("/{candidate_id}", response_model=CandidateRead)
def delete_candidate(
    *, db: Session = Depends(get_session), candidate_id: int
) -> CandidateRead:
    candidate = crud_candidate.delete_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Clean up resume file
    try:
        delete_resume_file(candidate_id)
        print(f"[Candidate API] Deleted resume file for candidate {candidate_id}")
    except Exception as e:
        print(
            f"[Candidate API] Failed to delete resume file for candidate {candidate_id}: {str(e)}"
        )
        # Don't fail the operation if file deletion fails

    return candidate


@router.get("/{candidate_id}/resume")
def get_candidate_resume(
    *, candidate_id: int, db: Session = Depends(get_session), request: Request
) -> FileResponse:
    """Download a candidate's resume file."""
    token_data: Optional[TokenData] = request.state.user

    # Get candidate to verify it exists and check permissions
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # # Check if user has permission to access this candidate's resume
    # if token_data and (candidate.employer_id != token_data.employer_id:
    #     print(f"[Candidate API] Not authorized to access this resume for candidate {candidate_id}")
    #     raise HTTPException(status_code=403, detail="Not authorized to access this resume")

    # Get resume file path
    resume_path = get_resume_file_path(candidate_id)
    if not resume_path:
        raise HTTPException(status_code=404, detail="Resume file not found")

    # Return file response
    return FileResponse(
        path=resume_path,
        filename=f"{candidate.full_name}_resume.pdf",
        media_type="application/pdf",
    )


@router.get("/{candidate_id}/parsing-status")
def get_resume_parsing_status(
    *, candidate_id: int, db: Session = Depends(get_session), request: Request
) -> dict:
    """Check the parsing status of a candidate's resume."""
    token_data: Optional[TokenData] = request.state.user

    # Get candidate to verify it exists and check permissions
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Check if user has permission to access this candidate's data
    if token_data:
        candidate_employers = crud_candidate.get_candidate_employers(db=db, candidate_id=candidate_id)
        employer_ids = [emp.id for emp in candidate_employers]
        if token_data.employer_id not in employer_ids:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this candidate"
            )

    # Determine parsing status
    has_resume_file = get_resume_file_path(candidate_id) is not None
    has_parsed_data = (
        candidate.parsed_resume is not None and candidate.parsed_resume != {}
    )

    if not has_resume_file:
        status = "no_resume"
        message = "No resume file uploaded"
    elif has_parsed_data:
        status = "completed"
        message = "Resume parsing completed"
    else:
        status = "pending"
        message = "Resume parsing in progress"

    return {
        "candidate_id": candidate_id,
        "parsing_status": status,
        "message": message,
        "has_resume_file": has_resume_file,
        "has_parsed_data": has_parsed_data,
        "resume_url": candidate.resume_url,
    }


@router.post("/{candidate_id}/employers/{employer_id}")
def add_candidate_to_employer(
    *,
    db: Session = Depends(get_session),
    candidate_id: int,
    employer_id: int,
    request: Request,
) -> dict:
    try:
        """Associate a candidate with an employer."""
        token_data: Optional[TokenData] = request.state.user
        
        # Check if user is authenticated and has permission
        if not token_data or token_data.employer_id != employer_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to add candidates to this employer"
            )
        
        # Check if candidate exists
        candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Add the relationship
        success = crud_candidate.add_candidate_to_employer(
            db=db, candidate_id=candidate_id, employer_id=employer_id
        )
        
        if success:
            return {"message": "Candidate successfully added to employer"}
        else:
            return {"message": "Candidate is already associated with this employer"}
    except Exception as e:
        print(f"[Candidate API] Error adding candidate to employer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{candidate_id}/employers/{employer_id}")
def remove_candidate_from_employer(
    *,
    db: Session = Depends(get_session),
    candidate_id: int,
    employer_id: int,
    request: Request,
) -> dict:
    """Remove association between a candidate and an employer."""
    token_data: Optional[TokenData] = request.state.user
    
    # Check if user is authenticated and has permission
    if not token_data or token_data.employer_id != employer_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to remove candidates from this employer"
        )
    
    # Check if candidate exists
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Remove the relationship
    success = crud_candidate.remove_candidate_from_employer(
        db=db, candidate_id=candidate_id, employer_id=employer_id
    )
    
    if success:
        return {"message": "Candidate successfully removed from employer"}
    else:
        raise HTTPException(
            status_code=404, detail="Candidate is not associated with this employer"
        )


@router.get("/{candidate_id}/employers", response_model=List[dict])
def get_candidate_employers(
    *,
    db: Session = Depends(get_session),
    candidate_id: int,
    request: Request,
) -> List[dict]:
    """Get all employers associated with a candidate."""
    token_data: Optional[TokenData] = request.state.user
    
    # Check if candidate exists
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Get candidate's employers
    employers = crud_candidate.get_candidate_employers(db=db, candidate_id=candidate_id)
    
    # If user is authenticated, check if they have permission to see this data
    if token_data:
        employer_ids = [emp.id for emp in employers]
        if token_data.employer_id not in employer_ids:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this candidate's employer data"
            )
    
    return [{"id": emp.id, "name": emp.name, "domain": emp.domain} for emp in employers]



@router.get("/{candidate_id}/details", response_model=CandidateWithDetails)
def get_candidate_details(
    *,
    db: Session = Depends(get_session),
    candidate_id: int,
    request: Request,
) -> CandidateWithDetails:
    token_data: Optional[TokenData] = request.state.user
    
    candidate_with_details = crud_candidate.get_candidate_with_details(db=db, candidate_id=candidate_id)
    if not candidate_with_details:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return candidate_with_details 

