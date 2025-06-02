from functools import reduce
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request
import shutil
import tempfile
import os
from sqlmodel import Session
import base64
import time
import json
from typing import Optional
from core.auth_middleware import TokenData
from core.database import get_session
from crud import crud_candidate
from schemas import CandidateCreate, CandidateUpdate, CandidateRead
from pydantic import BaseModel
# Import the LLM AI resume parser and Candidate model
# from ai.app.services.llm.llm_agent import LLM
# from ai.app.services.llm.entities_models.candidate_pydantic import Candidate as AICandidate
from schemas.candidate_pydantic import Candidate as resume_data
# Import ResumeParserClient
from services.resume_upload import ResumeParserClient

router = APIRouter()


class post_candidate_payload(BaseModel):
    candidate_in: CandidateCreate
    resume: UploadFile = File(...)


candidateExample = CandidateCreate(
    full_name="John Doe",
    email="john@example.com", 
    phone="123456789",
    resume_url="",
    parsed_resume={}
).model_dump_json()


@router.post("/", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_in: Annotated[str,  Form()],
    resume: Optional[UploadFile] = File(None),
    request: Request
) -> CandidateRead:
    token_data: Optional[TokenData] = request.state.user

    temp_resume_path = None
    try:
        candidateData = json.loads(candidate_in)
        candidateObj = CandidateCreate(**candidateData)
        
        candidate_data = candidateObj.model_dump()
        print(f"[Candidate API] Token data: {token_data}")
        if token_data:
            candidate_data["employer_id"] = token_data.employer_id
            print(f"[Candidate API] Employer ID: {token_data.employer_id}")
        parsed_result = None
        if resume:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_resume:
                    shutil.copyfileobj(resume.file, temp_resume)
                    temp_resume_path = temp_resume.name
                print(f"[Candidate API] Saved PDF to temp file: {temp_resume_path}")
                # Use ResumeParserClient to parse the resume
                system_prompt = "Extract structured information from resumes. Focus on contact details, skills, and work experience."
                schema = resume_data.model_json_schema()
                parser_client = ResumeParserClient(system_prompt, schema, [temp_resume_path])
                parsed_result = parser_client.parse()
                if isinstance(parsed_result, dict):
                    print("[Candidate API] Parsed resume result keys:", list(parsed_result.keys()))
                else:
                    print("[Candidate API] Parsed resume result type:", type(parsed_result))
                candidate_data["parsed_resume"] = parsed_result
            except Exception as parse_err:
                print("[Candidate API] Error during resume processing:", str(parse_err))
                raise HTTPException(status_code=400, detail=f"Resume processing error: {str(parse_err)}")
        candidate = crud_candidate.create_candidate(db=db, candidate_in=CandidateCreate(**candidate_data))
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
    *,
    db: Session = Depends(get_session),
    candidate_id: int
) -> CandidateRead:
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.get("/by-email/{email}", response_model=CandidateRead)
def read_candidate_by_email(
    *,
    db: Session = Depends(get_session),
    email: str
) -> CandidateRead:
    candidate = crud_candidate.get_candidate_by_email(db=db, email=email)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.get("/", response_model=List[CandidateRead])
def read_candidates(
    *,
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100
) -> List[CandidateRead]:
    return crud_candidate.get_candidates(db=db, skip=skip, limit=limit)

@router.patch("/{candidate_id}", response_model=CandidateRead)
def update_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_id: int,
    candidate_in: CandidateUpdate
) -> CandidateRead:
    candidate = crud_candidate.get_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return crud_candidate.update_candidate(db=db, db_candidate=candidate, candidate_in=candidate_in)

@router.delete("/{candidate_id}", response_model=CandidateRead)
def delete_candidate(
    *,
    db: Session = Depends(get_session),
    candidate_id: int
) -> CandidateRead:
    candidate = crud_candidate.delete_candidate(db=db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
