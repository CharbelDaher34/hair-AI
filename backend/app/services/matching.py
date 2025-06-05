import httpx
from typing import List, Optional

MATCHER_URL = "http://localhost:8011/matcher/match_candidates"

def match_candidates_client(
    job_description: str,
    candidates: List[str],
    skill_weight: Optional[float] = 0.4,
    embedding_weight: Optional[float] = 0.6,
    matcher_url: str = MATCHER_URL,
    candidate_skills: Optional[List[str]] = None
):
    payload = {
        "job_description": job_description,
        "candidates": candidates,
        "skill_weight": skill_weight,
        "embedding_weight": embedding_weight,
        "candidate_skills": candidate_skills
    }
    with httpx.Client() as client:
        response = client.post(matcher_url, json=payload,timeout=None)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    # Example usage
    job_desc = "Looking for a Python developer with FastAPI experience."
    candidates = [
        "Experienced Python developer, worked with Django and Flask. Some FastAPI knowledge.",
        "Java developer with 10 years of experience. No Python.",
        "Junior Python dev, very interested in FastAPI."
    ]
    result = match_candidates_client(job_desc, candidates)
    import json
    print(json.dumps(result, indent=2))
