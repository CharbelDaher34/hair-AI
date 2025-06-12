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
from sqlmodel import Session
import base64
import time
import json
from typing import Optional
from core.auth_middleware import TokenData
from core.database import get_session, engine
from core.config import RESUME_STORAGE_DIR
from crud import crud_candidate
from schemas import CandidateCreate, CandidateUpdate, CandidateRead
from utils.file_utils import save_resume_file, get_resume_file_path, delete_resume_file
from models.candidate_pydantic import CandidateResume
from services.resume_upload import AgentClient

router = APIRouter()


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
        if token_data:
            candidate_data["employer_id"] = token_data.employer_id
            print(f"[Candidate API] Employer ID: {token_data.employer_id}")

        # Create candidate first to get the ID
        candidate = crud_candidate.create_candidate(
            db=db, candidate_in=CandidateCreate(**candidate_data)
        )
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
    if token_data and candidate.employer_id != token_data.employer_id:
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
