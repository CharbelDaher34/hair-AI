from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import sys
from pathlib import Path

from services.matcher.matcher import Matcher
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
matcher_instance = Matcher()


class MatchRequest(BaseModel):
    job: Dict = Field(..., description="Job description and requirements")
    candidates: List[Dict] = Field(
        ..., description="List of candidates to match against the job"
    )
    weights: Optional[Dict] = Field(
        default=None,
        description="Optional nested dictionary for weights",
        example={
            "final_score_weights": {
                "skills_score": 0.6,
                "overall_similarity": 0.4,
            },
            "skill_score_weights": {
                "hard_skills": 0.30,
                "soft_skills": 0.20,
                "extracted_skills": 0.25,
                "skills_embedding_similarity": 0.25,
            },
        },
    )
    fuzzy_threshold: Optional[float] = Field(
        default=80.0,
        ge=0,
        le=100,
        description="Minimum fuzzy match score for skills (0-100)",
    )


class ScoreBreakdown(BaseModel):
    skills_score: float
    overall_similarity: float


class WeightsUsed(BaseModel):
    final_weights: Dict[str, float]
    skill_weights: Dict[str, float]


class MatchResult(BaseModel):
    candidate: str = Field(..., description="Candidate name")
    score: float = Field(..., description="Overall matching score")
    score_breakdown: ScoreBreakdown = Field(
        ..., description="Breakdown of score components"
    )
    missing_skills: List[str] = Field(..., description="Missing skills")
    extra_skills: List[str] = Field(..., description="Extra skills")
    matching_skills: List[str] = Field(..., description="Matching skills")
    weights_used: WeightsUsed = Field(..., description="Weights used in calculation")
    analysis: str = Field(..., description="Analysis of the match")


class MatchResponse(BaseModel):
    results: List[MatchResult] = Field(..., description="List of matching results")
    total_candidates: int = Field(
        ..., description="Total number of candidates processed"
    )


@router.post("/match_candidates", response_model=MatchResponse)
async def match_candidates_endpoint(request: MatchRequest):
    """
    Matches a list of candidates against a job using fuzzy skill matching and embedding similarity.

    Returns detailed analysis including:
    - Overall matching scores with breakdown
    - Skill analysis showing matching, missing, and extra skills
    - Fuzzy matching details for each skill category
    - Embedding similarity scores
    """
    if not request.job or not request.candidates:
        raise HTTPException(
            status_code=400,
            detail="Job and candidates list cannot be empty.",
        )

    try:
        # Job and candidates are already dicts
        job_dict = request.job
        candidates_dicts = request.candidates

        # Call the matcher with the new fuzzy matching implementation
        matched_results = await matcher_instance.match_candidates(
            job=job_dict,
            candidates=candidates_dicts,
            weights=request.weights,
            fuzzy_threshold=request.fuzzy_threshold,
        )

        # Convert results to response format
        response_results = []
        for result in matched_results:
            match_result = MatchResult(
                candidate=result["candidate"],
                score=result["score"],
                score_breakdown=result["score_breakdown"],
                missing_skills=result["missing_skills"],
                extra_skills=result["extra_skills"],
                matching_skills=result["matching_skills"],
                weights_used=result["weights_used"],
                analysis=result["analysis"],
            )
            print(f"\n\n\n\nMatch result: {match_result}")
            response_results.append(match_result)

        return MatchResponse(
            results=response_results, total_candidates=len(request.candidates)
        )

    except Exception as e:
        # Log the exception for debugging
        logger.error(f"Error during candidate matching: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during the matching process: {str(e)}",
        )


# Example usage and testing
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    import json

    app = FastAPI(title="Candidate Matcher API", version="1.0.0")
    app.include_router(router, prefix="/matcher", tags=["Matcher"])

    # Example test data using Dict format
    test_job = {
        "title": "Senior Python Developer",
        "description": "We are looking for an experienced Python developer",
        "responsibilities": [
            "Develop web applications",
            "Write clean code",
            "Collaborate with team",
        ],
        "seniority_level": "Senior",
        "job_type": "Full-time",
        "skills": {
            "hard_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            "soft_skills": ["Communication", "Teamwork", "Problem Solving"],
        },
    }

    test_candidates = [
        {
            "full_name": "John Doe",
            "skills": [
                {"name": "Python", "type": "Hard"},
                {"name": "FastAPI", "type": "Hard"},
                {"name": "MySQL", "type": "Hard"},
                {"name": "Communication", "type": "Soft"},
                {"name": "Leadership", "type": "Soft"},
            ],
            "work_history": [
                {
                    "job_title": "Python Developer",
                    "company": "Tech Corp",
                    "summary": "Developed web applications using Python and FastAPI",
                }
            ],
        },
        {
            "full_name": "Jane Smith",
            "skills": [
                {"name": "Java", "type": "Hard"},
                {"name": "Spring Boot", "type": "Hard"},
                {"name": "Teamwork", "type": "Soft"},
            ],
            "work_history": [
                {
                    "job_title": "Java Developer",
                    "company": "Enterprise Inc",
                    "summary": "Backend development with Java and Spring",
                }
            ],
        },
    ]

    print("Matcher Router updated successfully!")
    print("Example request structure:")
    print(f"Job: {json.dumps(test_job, indent=2)}")
    print(f"Candidates: {json.dumps(test_candidates, indent=2)}")

    # Uncomment to run the server
    # uvicorn.run(app, host="0.0.0.0", port=8000)
