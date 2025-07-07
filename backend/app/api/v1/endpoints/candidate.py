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
from crud import crud_interview, crud_application, crud_job
from schemas import ApplicationRead
from schemas import InterviewRead
from core.auth_middleware import TokenData
from core.database import get_session, engine, admin_engine, get_admin_session
from core.config import RESUME_STORAGE_DIR
from crud import crud_candidate
from schemas import (
    CandidateCreate,
    CandidateUpdate,
    CandidateRead,
    CandidateWithDetails,
)
from models.models import Candidate
from utils.file_utils import save_resume_file, get_resume_file_path, delete_resume_file
from models.candidate_pydantic import CandidateResume
from services.resume_upload import AgentClient
from services.otp_service import otp_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Admin engine for bypassing RLS when needed


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
            logger.info(
                "Starting resume parsing for candidate %s (attempt %d/%d)",
                candidate_id,
                attempt + 1,
                max_retries,
            )

            # Ensure the resume_file_path is absolute for the parser client
            absolute_resume_file_path = os.path.abspath(resume_file_path)
            logger.info("Absolute resume file path: %s", absolute_resume_file_path)

            # Verify file exists before parsing
            if not os.path.exists(absolute_resume_file_path):
                logger.warning("Resume file not found: %s", absolute_resume_file_path)
                return

            # Use AgentClient to parse the resume
            system_prompt = """Here's an enhanced version of your prompt with clearer structure, better flow, and a more detailed explanation for extracting **skills** across all sections:

---

### 🧠 **Resume Image Parsing Instructions**

You are an expert in extracting structured information from resume **images**. Your goal is to accurately identify and extract key candidate details such as contact information, work experience, education, skills, and certifications. This requires careful attention to the **document layout, formatting cues, section headers, and textual structure** to interpret the visual context accurately.

---

## ✅ **Extraction Guidelines**

---

### 1. **Contact Information**

* Extract:

  * **Full name**
  * **Email address**
  * **Phone number**
* These are usually found:

  * At the **top of the document**
  * In **headers or footers**
  * Near **name or title blocks**

---

### 2. **Work Experience**

* Extract:

  * **Job title**
  * **Company name**
  * **Company location**
  * **Employment type** (Full-time, Part-time, Internship, Contract)
  * **Start date** and **End date** (normalize to `YYYY-MM-DD`)
  * **Role summary** (responsibilities and achievements)
* Look under sections such as:

  * "Work Experience"
  * "Professional Experience"
  * "Employment History"

---

### 3. **Education**

* Extract:

  * **Education level** (e.g., Bachelor's, Master's, PhD)
  * **Degree type and field of study**
  * **Institution name**
  * **Start and end dates** (standardized)
  * **GPA** (if available)
  * **Honors, thesis, or special achievements**
* Typical section headers:

  * "Education"
  * "Academic Background"
  * "Degrees"

---

### 4. **Skills**

**🧩 General Objective:**
Extract **all skills mentioned in the resume**, not just those listed under a dedicated "Skills" section.

**🔍 Scope of Extraction:**

* Search **across all sections**, including:

  * **Work experience** (e.g., "developed RESTful APIs in Python" → extract `Python`, `RESTful APIs`)
  * **Education** (e.g., "used MATLAB for simulations" → extract `MATLAB`)
  * **Certifications** (e.g., "certified in Excel Advanced" → extract `Excel`)
  * **Projects or Publications** (e.g., "Built an AI chatbot using TensorFlow" → extract `AI`, `Chatbot`, `TensorFlow`)

**📚 Categories:**
Categorize each extracted skill as either:

* **Hard Skill**: Technical or domain-specific (e.g., Python, SQL, Docker, Excel)
* **Soft Skill**: Behavioral or interpersonal (e.g., Leadership, Communication, Problem-Solving)

**🎯 Optional Metadata:**

* **Proficiency level**, if mentioned (e.g., Beginner, Intermediate, Expert)
* **Context**, such as the section it was found in (optional but useful)

**📌 Examples:**
From this sentence in Work Experience:

> "Led a team using Agile methodologies and wrote microservices in Go."

You should extract:

```json
[
  { "skill": "Agile", "type": "Soft", "proficiency": "", "source": "Work Experience" },
  { "skill": "Go", "type": "Hard", "proficiency": "", "source": "Work Experience" },
  { "skill": "Team Leadership", "type": "Soft", "proficiency": "", "source": "Work Experience" }
]
```

---

### 5. **Certifications**

* Extract:

  * **Certification name**
  * **Issuing organization**
  * **Issue date** (normalize format)
  * **Group or category** (if stated)
* Located under:

  * "Certifications"
  * "Licenses"
  * Mentioned inline in summary or education

---

## ⚙️ **General Instructions**

* Use `null` or an empty string (`""`) if a field is missing or not explicitly stated.
* Normalize all **dates** to `YYYY-MM-DD`.
* Ensure accuracy based on **visual layout, font size/weight, indentation, and section labels**.
* Do not include duplicated information — prefer structured data over free text.
* Be resilient to varied layouts, styles, and ordering of sections.
"""
            schema = CandidateResume.model_json_schema()

            logger.info("Creating parser client for candidate %s", candidate_id)
            try:
                parser_client = AgentClient()
                if parser_client.base_url is None:
                    logger.warning(
                        "AI service is not available for candidate %s - skipping resume parsing",
                        candidate_id,
                    )
                    return
            except Exception as client_err:
                logger.error(
                    "Failed to create AgentClient for candidate %s: %s",
                    candidate_id,
                    client_err,
                )
                return

            logger.info("Starting parsing for candidate %s", candidate_id)
            parsed_result = parser_client.parse(
                system_prompt, schema, [absolute_resume_file_path]
            )

            logger.info("Parsing completed for candidate %s", candidate_id)
            logger.debug("Parsed result type: %s", type(parsed_result))

            ## parsed result is a dictionary , get to the skills key and check if it is a list

            if parsed_result is None:
                logger.warning(
                    "Parsing returned None for candidate %s - API may have failed",
                    candidate_id,
                )
                if attempt < max_retries - 1:
                    logger.info("Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                else:
                    break

            # Check if parsed_result is a dictionary and process it
            if isinstance(parsed_result, dict):
                # Now you can safely access keys
                skills_list = parsed_result.get("skills", [])
                if isinstance(skills_list, list):
                    logger.info(
                        "Successfully extracted %d skills for candidate %s",
                        len(skills_list),
                        candidate_id,
                    )
                else:
                    logger.warning(
                        "Parsed 'skills' is not a list for candidate %s. Type: %s",
                        candidate_id,
                        type(skills_list),
                    )

                logger.info("Updating database for candidate %s", candidate_id)
                with Session(engine) as session:
                    candidate = crud_candidate.get_candidate(session, candidate_id)
                    if candidate is None:
                        logger.warning(
                            "Candidate with id %s not found in background resume parsing. Skipping update.",
                            candidate_id,
                        )
                        break  # Exit retry loop if candidate is missing
                    crud_candidate.update_candidate(
                        session, db_candidate=candidate, candidate_in={"parsed_resume": parsed_result}
                    )
                logger.info("Database updated for candidate %s", candidate_id)
                break  # Exit retry loop on success
            else:
                logger.error(
                    "Parsed result is not a dictionary for candidate %s. Type: %s",
                    candidate_id,
                    type(parsed_result),
                )
                # Decide if you want to retry for this case
                if attempt < max_retries - 1:
                    logger.info("Retrying in 5 seconds...")
                    time.sleep(5)
                continue

        except Exception as parse_err:
            logger.error(
                "Error processing resume for candidate %s (attempt %d/%d): %s",
                candidate_id,
                attempt + 1,
                max_retries,
                parse_err,
            )
            logger.debug("Error type: %s", type(parse_err))
            if attempt < max_retries - 1:
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.error("Max retries reached for candidate %s", candidate_id)

            import traceback

            logger.debug("Full traceback: %s", traceback.format_exc())


@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(request: SendOTPRequest) -> dict:
    """
    Send OTP to candidate's email for verification.
    """
    try:
        success = await otp_service.send_otp(request.email, request.full_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email.",
            )
        return {"message": "OTP sent successfully."}
    except Exception as e:
        logger.error("Error sending OTP: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while sending the OTP.",
        )


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(request: VerifyOTPRequest) -> dict:
    """
    Verify OTP code for candidate's email.
    """
    try:
        result = otp_service.verify_otp(request.email, request.otp_code)
        if not result.get("success"):
            error_code = result.get("error_code")
            message = result.get("message")
            status_code = status.HTTP_400_BAD_REQUEST

            if error_code == "OTP_EXPIRED":
                status_code = status.HTTP_410_GONE
            elif error_code == "TOO_MANY_ATTEMPTS":
                status_code = status.HTTP_429_TOO_MANY_REQUESTS

            raise HTTPException(status_code=status_code, detail=message)

        return {"message": "Email verified successfully."}
    except Exception as e:
        logger.error("Error verifying OTP: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during OTP verification.",
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
        logger.error("Error getting OTP status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching OTP status.",
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
                    "created_at": candidate.created_at.isoformat()
                    if candidate.created_at
                    else None,
                },
            }
        else:
            return {"exists": False, "candidate": None}
    except Exception as e:
        logger.error("Error checking candidate email: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking candidate email.",
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
        result.append(
            CandidateTable(
                candidate=data["candidate"],
                applications_count=data["applications_count"],
                interviews_count=data["interviews_count"],
            )
        )

    return result


@router.post("/", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(
    *,
    db: Session = Depends(get_admin_session),
    candidate_in: Annotated[str, Form()],
    resume: Optional[UploadFile] = File(None),
    job_id: Optional[int] = Form(None),
    request: Request,
    background_tasks: BackgroundTasks,
) -> CandidateRead:
    token_data: Optional[TokenData] = request.state.user

    temp_resume_path = None
    try:
        candidate_data_json = json.loads(candidate_in)
        candidate_obj = CandidateCreate(**candidate_data_json)

        candidate_data = candidate_obj.model_dump()
        logger.info(f"[Candidate API] Token data: {token_data}")

        # Check if email is verified (only for public applications, not HR-created candidates)
        if not token_data:  # Public application
            if not otp_service.is_email_verified(candidate_data["email"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "message": "Email verification required. Please verify your email before submitting the application.",
                        "error_code": "EMAIL_NOT_VERIFIED",
                        "email": candidate_data["email"],
                    },
                )

        # Check if candidate already exists by email
        existing_candidate = crud_candidate.get_candidate_by_email(
            db=db, email=candidate_data["email"]
        )

        if existing_candidate:
            # For existing candidates, update their information if provided and different
            update_data = {}
            if (
                candidate_data.get("full_name")
                and candidate_data["full_name"] != existing_candidate.full_name
            ):
                update_data["full_name"] = candidate_data["full_name"]
            if (
                candidate_data.get("phone")
                and candidate_data["phone"] != existing_candidate.phone
            ):
                # Check if phone is already used by another candidate
                phone_check = crud_candidate.check_candidate_exists(
                    db=db, candidate_email="", phone=candidate_data["phone"]
                )
                if phone_check and phone_check == "Phone already exists":
                    other_candidate = db.exec(
                        select(Candidate).where(
                            Candidate.phone == candidate_data["phone"]
                        )
                    ).first()
                    if other_candidate and other_candidate.id != existing_candidate.id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Phone number is already used by another candidate",
                        )
                update_data["phone"] = candidate_data["phone"]

            # Update candidate if there are changes
            if update_data:
                candidate = crud_candidate.update_candidate(
                    db=db, db_candidate=existing_candidate, candidate_in=update_data
                )
            else:
                candidate = existing_candidate

            logger.info(
                f"[Candidate API] Using existing candidate with ID: {candidate.id}"
            )
        else:
            # Check phone conflict first using the same DB session
            phone_check = crud_candidate.check_candidate_exists(
                db=db, candidate_email="", phone=candidate_data["phone"]
            )
            if phone_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=phone_check
                )

            # Create new candidate using ADMIN session to bypass RLS policies
            candidate = crud_candidate.create_candidate(
                db, candidate_in=CandidateCreate(**candidate_data)
            )
            logger.info(
                f"[Candidate API] Created new candidate with ID: {candidate.id} (public route)"
            )

        # Associate candidate with employer based on job_id or authenticated user
        employer_id_to_associate = None

        # If job_id is provided, get the employer from the job
        if job_id:
            try:
                job = crud_job.get_job(db=db, job_id=job_id)
                if job and job.employer_id:
                    employer_id_to_associate = job.employer_id
                    logger.info(
                        f"[Candidate API] Found employer {job.employer_id} from job {job_id}"
                    )
                else:
                    logger.warning(
                        f"[Candidate API] Job {job_id} not found or has no employer"
                    )
            except Exception as job_err:
                logger.error(
                    f"[Candidate API] Error getting job {job_id}: {str(job_err)}"
                )

        # If user is authenticated and no job_id employer found, use their employer
        if not employer_id_to_associate and token_data and token_data.employer_id:
            employer_id_to_associate = token_data.employer_id
            logger.info(
                f"[Candidate API] Using authenticated user's employer {token_data.employer_id}"
            )

        # Associate candidate with the determined employer
        if employer_id_to_associate:
            try:
                crud_candidate.add_candidate_to_employer(
                    db=db,
                    candidate_id=candidate.id,
                    employer_id=employer_id_to_associate,
                )
                logger.info(
                    f"[Candidate API] Associated candidate {candidate.id} with employer {employer_id_to_associate}"
                )
            except Exception as assoc_err:
                logger.error(
                    f"[Candidate API] Error associating candidate {candidate.id} with employer {employer_id_to_associate}: {str(assoc_err)}"
                )
                # Don't fail the operation if association fails

        logger.info(f"[Candidate API] Created candidate with ID: {candidate.id}")

        # If resume was uploaded, save it permanently with candidate ID as filename
        if resume:
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as temp_resume:
                    shutil.copyfileobj(resume.file, temp_resume)
                    temp_resume_path = temp_resume.name
                logger.info(
                    f"[Candidate API] Saved PDF to temp file: {temp_resume_path}"
                )

                # Save resume permanently
                permanent_resume_path = save_resume_file(temp_resume_path, candidate.id)
                logger.info(f"[Candidate API] Saved resume to: {permanent_resume_path}")

                # Update candidate with resume URL immediately
                candidate = crud_candidate.update_candidate(
                    db=db,
                    db_candidate=candidate,
                    candidate_in={"resume_url": permanent_resume_path},
                )

                # Schedule resume parsing as background task
                try:
                    background_tasks.add_task(
                        parse_resume_background, candidate.id, permanent_resume_path
                    )
                    logger.info(
                        f"[Candidate API] Scheduled background resume parsing for candidate {candidate.id}"
                    )
                except Exception as bg_task_err:
                    logger.error(
                        f"[Candidate API] Error scheduling background resume parsing for candidate {candidate.id}: {str(bg_task_err)}"
                    )
                    # Don't fail the entire operation if background task scheduling fails

            except Exception as save_err:
                logger.error(f"[Candidate API] Error saving resume: {str(save_err)}")
                # Don't fail the entire operation if resume saving fails

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[Candidate API] General error:", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        # Clean up temp file
        if temp_resume_path:
            try:
                os.remove(temp_resume_path)
            except Exception:
                logger.warning(
                    f"[Candidate API] Failed to remove temp file: {temp_resume_path}"
                )

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
        logger.info(f"[Candidate API] Deleted resume file for candidate {candidate_id}")
    except Exception as e:
        logger.error(
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
        candidate_employers = crud_candidate.get_candidate_employers(
            db=db, candidate_id=candidate_id
        )
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
                status_code=403,
                detail="Not authorized to add candidates to this employer",
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
        logger.error(f"[Candidate API] Error adding candidate to employer: {str(e)}")
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
            status_code=403,
            detail="Not authorized to remove candidates from this employer",
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
                status_code=403,
                detail="Not authorized to access this candidate's employer data",
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

    candidate_with_details = crud_candidate.get_candidate_with_details(
        db=db, candidate_id=candidate_id
    )
    if not candidate_with_details:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return candidate_with_details
