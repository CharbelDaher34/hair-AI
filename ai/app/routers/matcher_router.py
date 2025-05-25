from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import sys
from pathlib import Path


from services.matcher.matcher import Matcher

router = APIRouter()
matcher_instance = Matcher()


class MatchRequest(BaseModel):
    job_description: str = Field(..., example="We are looking for a software engineer with Python and FastAPI experience.")
    candidates: List[str] = Field(..., example=["I am a python developer with 3 years of experience in FastAPI."])
    skill_weight: Optional[float] = Field(0.4, ge=0, le=1, description="Weight for skill-based similarity, between 0 and 1.")
    embedding_weight: Optional[float] = Field(0.6, ge=0, le=1, description="Weight for embedding-based similarity, between 0 and 1.")

class SkillAnalysisDetail(BaseModel):
    match_percentage: float
    matching_skills: List[str]
    missing_skills: List[str]
    extra_skills: List[str]
    summary: Dict[str, int]

class MatchResult(BaseModel):
    candidate: str
    score: float
    skill_analysis: SkillAnalysisDetail
    embedding_similarity: float
    weights: Dict[str, float]

class MatchResponse(BaseModel):
    results: List[MatchResult]

@router.post("/match_candidates", response_model=MatchResponse)
async def match_candidates_endpoint(request: MatchRequest):
    """
    Matches a list of candidates against a job description.

    - **job_description**: The text of the job description.
    - **candidates**: A list of candidate objects, each with an `id` and `text` (e.g., CV content).
    - **skill_weight**: Optional weight for skill-based similarity (0.0 to 1.0).
    - **embedding_weight**: Optional weight for embedding-based similarity (0.0 to 1.0).
    """
    if not request.job_description or not request.candidates:
        raise HTTPException(status_code=400, detail="Job description and candidates list cannot be empty.")

    try:
        # Convert Pydantic Candidate models to dicts for the Matcher service
        candidates_data = request.candidates
        
        matched_results = matcher_instance.match_candidates(
            job_description=request.job_description,
            candidates=candidates_data,
            skill_weight=request.skill_weight,
            embedding_weight=request.embedding_weight
        )
        
        # Convert results back to Pydantic models for the response
        response_results = []
        for res in matched_results:
            # The Matcher service returns candidate as a dict, convert it back to Candidate model
            # Ensure the 'candidate' dict from Matcher output matches the Candidate Pydantic model structure
            candidate_model = res["candidate"]
            
            skill_analysis_model = SkillAnalysisDetail(**res["skill_analysis"])
            
            response_results.append(MatchResult(
                candidate=candidate_model,
                score=res["score"],
                skill_analysis=skill_analysis_model,
                embedding_similarity=res["embedding_similarity"],
                weights=res["weights"]
            ))
            
        return MatchResponse(results=response_results)
    except Exception as e:
        # Log the exception for debugging
        logger.error(f"Error during candidate matching: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during the matching process: {str(e)}")

# To run this router (example, typically done in a main.py or app.py)
# if __name__ == "__main__":
#     import uvicorn
#     from fastapi import FastAPI
# 
#     app = FastAPI()
#     app.include_router(router, prefix="/matcher", tags=["Matcher"])
# 
#     # Example usage with dummy data
#     test_job_desc = "Looking for a Python developer with FastAPI experience."
#     test_candidates = [
#         {"id": "c1", "text": "Experienced Python developer, worked with Django and Flask. Some FastAPI knowledge."},
#         {"id": "c2", "text": "Java developer with 10 years of experience. No Python."},
#         {"id": "c3", "text": "Junior Python dev, very interested in FastAPI."}
#     ]
# 
#     # This is just for local testing, actual API calls would be via HTTP
#     async def run_test():
#         req = MatchRequest(job_description=test_job_desc, candidates=[Candidate(**c) for c in test_candidates])
#         response = await match_candidates_endpoint(req)
#         print(response.model_dump_json(indent=2))
# 
#     # import asyncio
#     # asyncio.run(run_test())
# 
#     # uvicorn.run(app, host="0.0.0.0", port=8000)
