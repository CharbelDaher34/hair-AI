import httpx
from typing import List, Optional
import requests
import os
import time

# Define AI Service URL from environment variable
# The environment variable `AI_SERVICE_URL` should be set in the environment (e.g., Docker Compose, Kubernetes).
# Example: AI_SERVICE_URL=http://ai-service:8011
AI_SERVICE_BASE_URL = os.getenv("AI_SERVICE_URL")
if not AI_SERVICE_BASE_URL:
    print("⚠️ WARNING: AI_SERVICE_URL environment variable not set. Falling back to default 'http://ai:8011'.")
    AI_SERVICE_BASE_URL = "http://ai:8011" # Default fallback for local Docker Compose

MATCHER_ENDPOINT = "/matcher/match_candidates"
MATCHER_URL = f"{AI_SERVICE_BASE_URL.rstrip('/')}{MATCHER_ENDPOINT}"

print(f"ℹ️ AI Matcher Service URL configured to: {MATCHER_URL}")

def match_candidates_client(
    job: dict,
    candidates: List[dict],
    weights: Optional[dict] = None,
    fuzzy_threshold: Optional[float] = 80.0,
    matcher_url: str = MATCHER_URL,
):
    """
    Call the AI matcher service with structured job and candidate data.
    
    Args:
        job: Job dictionary with title, description, skills, etc.
        candidates: List of candidate dictionaries with parsed resume data
        weights: Optional weights for different scoring components
        fuzzy_threshold: Minimum fuzzy match score for skills (0-100)
        matcher_url: URL of the matcher service
    
    Returns:
        dict: Matching results from the AI service
    """
    payload = {
        "job": job,
        "candidates": candidates,
        "weights": weights,
        "fuzzy_threshold": fuzzy_threshold,
    }
    with httpx.Client() as client:
        response = client.post(matcher_url, json=payload, timeout=None)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    # Example usage
    job_data = {
        "title": "Senior Python Developer",
        "description": "Looking for a Python developer with FastAPI experience.",
        "skills": {
            "hard_skills": ["Python", "FastAPI", "PostgreSQL"],
            "soft_skills": ["Communication", "Teamwork"]
        }
    }
    candidates_data = [
        {
            "full_name": "John Doe",
            "skills": [
                {"name": "Python", "type": "Hard"},
                {"name": "FastAPI", "type": "Hard"},
                {"name": "Communication", "type": "Soft"}
            ],
            "work_history": [{
                "job_title": "Python Developer",
                "summary": "Experienced Python developer, worked with Django and Flask. Some FastAPI knowledge."
            }]
        }
    ]
    result = match_candidates_client(job_data, candidates_data)
    import json

    print(json.dumps(result, indent=2))
