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
    time.sleep(10)
except Exception as e:
    print(f"❌ Could not get matcher URL: {e}")
    MATCHER_URL = ""


def match_candidates_client(
    job_description: str,
    candidates: List[str],
    skill_weight: Optional[float] = 0.4,
    embedding_weight: Optional[float] = 0.6,
    matcher_url: str = MATCHER_URL,
    candidate_skills: Optional[List[str]] = None,
):
    payload = {
        "job_description": job_description,
        "candidates": candidates,
        "skill_weight": skill_weight,
        "embedding_weight": embedding_weight,
        "candidate_skills": candidate_skills,
    }
    with httpx.Client() as client:
        print(f"Sending payload to {matcher_url}")
        print(payload)
        time.sleep(10)
        response = client.post(matcher_url, json=payload, timeout=None)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    # Example usage
    job_desc = "Looking for a Python developer with FastAPI experience."
    candidates = [
        "Experienced Python developer, worked with Django and Flask. Some FastAPI knowledge.",
        "Java developer with 10 years of experience. No Python.",
        "Junior Python dev, very interested in FastAPI.",
    ]
    result = match_candidates_client(job_desc, candidates)
    import json

    print(json.dumps(result, indent=2))
