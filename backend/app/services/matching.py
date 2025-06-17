import httpx
from typing import List, Optional
import requests
import os
import time


def _get_matcher_url():
    """
    Determines the correct matcher URL by checking health endpoints of potential hosts.
    """
    matcher_url = os.getenv("ai_url")
    if matcher_url:
        return f"{matcher_url}/matcher/match_candidates"
    hosts = [os.getenv("AI_HOST", "ai"), "localhost"]
    port = os.getenv("AI_PORT", "8011")

    for host in hosts:
        base_url = f"http://{host}:{port}"
        health_url = f"{base_url}/health"
        try:
            print(f"Trying to connect to {health_url}")
            response = requests.get(health_url, timeout=5)
            response.raise_for_status()
            print(f"✅ AI service is running at {base_url}")
            return f"{base_url}/matcher/match_candidates"
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not connect to {health_url}: {e}")

    print("❌ AI service is not running or not accessible.")
    return ""


try:
    MATCHER_URL = _get_matcher_url()
    print(f"✅ Matcher URL: {MATCHER_URL}")
except Exception as e:
    print(f"❌ Could not get matcher URL: {e}")
    MATCHER_URL = ""


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
