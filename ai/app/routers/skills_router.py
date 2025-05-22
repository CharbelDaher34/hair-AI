from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Set, Tuple
import sys
from pathlib import Path


from services.skills_module.ner_skills import skill_ner

router = APIRouter()
# skill_ner uses class methods, so no instance is needed for the class itself.

# --- Pydantic Models ---
class TextRequest(BaseModel):
    text: str = Field(..., example="Experienced in Python, Java, and SQL.")

class SkillsListResponse(BaseModel):
    skills: List[str] # Changed from Set[str] to List[str] for JSON compatibility

class CompareTextsRequest(BaseModel):
    text_one: str = Field(..., example="Job requires Python, Machine Learning, and AWS.")
    text_two: str = Field(..., example="Candidate proficient in Python, Docker, and Azure.")

class SkillAnalysisResponse(BaseModel):
    matching_skills: List[str]
    missing_skills: List[str] # Skills in text_one (e.g. job) but not in text_two (e.g. candidate)
    extra_skills: List[str]   # Skills in text_two (e.g. candidate) but not in text_one (e.g. job)
    total_text_one_skills: int = Field(alias="total_job_skills") # Alias for clarity if text_one is job
    total_text_two_skills: int = Field(alias="total_candidate_skills") # Alias for clarity if text_two is candidate
    matching_skills_count: int
    missing_skills_count: int
    extra_skills_count: int

class SkillResemblanceResponse(BaseModel):
    resemblance_rate: float
    skill_analysis: SkillAnalysisResponse

class SkillMatchSummary(BaseModel):
    total_required_skills: int
    matching_skills_count: int
    missing_skills_count: int
    extra_skills_count: int

class SkillMatchDetailsResponse(BaseModel):
    match_percentage: float
    skill_analysis: SkillAnalysisResponse # Reusing the detailed analysis model
    summary: SkillMatchSummary

# --- API Endpoints ---

@router.post("/extract_skills", response_model=SkillsListResponse)
async def extract_skills_endpoint(request: TextRequest):
    """
    Extracts unique skills from the provided text.
    - **text**: The input string from which to extract skills.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        extracted_skills = skill_ner.extract_skills(request.text)
        # Convert set to list for JSON response
        return SkillsListResponse(skills=list(extracted_skills))
    except Exception as e:
        # logger.error(f"Error in extract_skills_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_skills", response_model=SkillAnalysisResponse)
async def analyze_skills_endpoint(request: CompareTextsRequest):
    """
    Analyzes and compares skills between two texts (e.g., job description vs. candidate CV).

    - **text_one**: The first text (e.g., job description).
    - **text_two**: The second text (e.g., candidate CV).
    
    Returns a detailed breakdown of matching, missing (from text_one's perspective),
    and extra skills (in text_two).
    """
    if not request.text_one.strip() or not request.text_two.strip():
        raise HTTPException(status_code=400, detail="Both texts must be provided and cannot be empty.")
    try:
        analysis_result = skill_ner.analyze_skills(request.text_one, request.text_two)
        return SkillAnalysisResponse(**analysis_result)
    except Exception as e:
        # logger.error(f"Error in analyze_skills_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/skill_resemblance_rate", response_model=SkillResemblanceResponse)
async def get_skill_resemblance_rate_endpoint(request: CompareTextsRequest):
    """
    Calculates the resemblance rate (Jaccard-like index) based on common skills between two texts.
    
    - **text_one**: The first text.
    - **text_two**: The second text.
    
    Returns the resemblance rate and a detailed skill analysis.
    """
    if not request.text_one.strip() or not request.text_two.strip():
        raise HTTPException(status_code=400, detail="Both texts must be provided and cannot be empty.")
    try:
        rate, analysis = skill_ner.calculate_skills_resemblance_rate(request.text_one, request.text_two)
        # The analysis from calculate_skills_resemblance_rate matches SkillAnalysisResponse structure
        return SkillResemblanceResponse(resemblance_rate=rate, skill_analysis=SkillAnalysisResponse(**analysis))
    except Exception as e:
        # logger.error(f"Error in get_skill_resemblance_rate_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/skill_match_details", response_model=SkillMatchDetailsResponse)
async def get_skill_match_details_endpoint(request: CompareTextsRequest):
    """
    Provides a detailed skill match report between a primary text (e.g., job description)
    and a secondary text (e.g., candidate CV).

    - **text_one**: The primary text (e.g., job description, skills from this text are considered 'required').
    - **text_two**: The secondary text (e.g., candidate CV).
    
    Returns match percentage, detailed skill breakdown, and summary counts.
    """
    if not request.text_one.strip() or not request.text_two.strip():
        raise HTTPException(status_code=400, detail="Both texts must be provided and cannot be empty.")
    try:
        match_details = skill_ner.get_skill_match_details(request.text_one, request.text_two)
        
        # Ensure the nested dictionaries map correctly to Pydantic models
        skill_analysis_data = match_details["skill_analysis"]
        summary_data = match_details["summary"]
        
        return SkillMatchDetailsResponse(
            match_percentage=match_details["match_percentage"],
            skill_analysis=SkillAnalysisResponse(**skill_analysis_data),
            summary=SkillMatchSummary(**summary_data)
        )
    except Exception as e:
        # logger.error(f"Error in get_skill_match_details_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Example usage (typically in a main.py or app.py)
# if __name__ == "__main__":
#     import uvicorn
#     from fastapi import FastAPI
#
#     app = FastAPI()
#     app.include_router(router, prefix="/skills", tags=["Skills NER"])
#
#     uvicorn.run(app, host="0.0.0.0", port=8001) # Use a different port if matcher is also running
