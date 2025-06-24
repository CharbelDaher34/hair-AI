import numpy as np
from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path
import traceback
# Add parent directory to path for imports
# project_root = Path(__file__).resolve().parent.parent.parent
# sys.path.insert(0, str(project_root))

from services.skills_module.ner_skills import skill_ner
from sentence_transformers import SentenceTransformer
import logging
from utils import render_model
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Matcher:
    def __init__(self, model_name: str = "TechWolf/JobBERT-v2"):
        """
        Initialize the Matcher with a sentence transformer model.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.embedding_model = SentenceTransformer(model_name)
        logger.error(f"Initialized embedding model: {model_name}")

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a given text.

        Args:
            text: Input text to generate embedding for

        Returns:
            numpy array containing the embedding
        """
        return self.embedding_model.encode(text)

    def calculate_embedding_similarity(self, embedding_one: np.ndarray, embedding_two: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Returns:
            float: Raw cosine similarity score in range [-1, 1]
        """
        return np.dot(embedding_one, embedding_two) / (np.linalg.norm(embedding_one) * np.linalg.norm(embedding_two))

    def calculate_normalized_embedding_similarity(self, embedding_one: np.ndarray, embedding_two: np.ndarray) -> float:
        """
        Calculate normalized cosine similarity between two embeddings.
        
        Returns:
            float: Normalized cosine similarity score in range [0, 1]
        """
        raw_similarity = self.calculate_embedding_similarity(embedding_one, embedding_two)
        return (raw_similarity + 1.0) / 2.0

    def calculate_text_similarity(self, text_one: str, text_two: str) -> float:
        """
        Calculate cosine similarity between embeddings of two texts.

        Args:
            text_one: First text
            text_two: Second text

        Returns:
            float: Cosine similarity score between 0 and 1 (normalized from -1 to 1 range)
        """
        embedding_one = self.get_embedding(text_one)
        embedding_two = self.get_embedding(text_two)

        # Calculate cosine similarity
        if np.linalg.norm(embedding_one) == 0 or np.linalg.norm(embedding_two) == 0:
            return 0.0
        similarity = np.dot(embedding_one, embedding_two) / (
            np.linalg.norm(embedding_one) * np.linalg.norm(embedding_two)
        )
        
        # Normalize cosine similarity from [-1, 1] to [0, 1] to prevent negative scores
        # This ensures embedding similarity contributes positively to the final score
        normalized_similarity = (similarity + 1.0) / 2.0
        
        return float(max(0.0, min(1.0, normalized_similarity)))


    def fuzzy_match_skills(self, required_skills: List[str], candidate_skills: List[str], threshold: float = 0.6) -> Dict:
        """
        Perform fuzzy matching between required and candidate skills using the ner_skills match_skills method.
        
        Args:
            required_skills: List of required skills
            candidate_skills: List of candidate skills
            fthreshold: Minimum fuzzy match score to consider a match (0-1)
            
        Returns:
            Dict containing matching, missing, and extra skills with analysis
        """
        print(f"Required skills: {required_skills}")
        print(f"Candidate skills: {candidate_skills}")
        print(f"Threshold: {threshold}")
        

        # Use the existing match_skills method from ner_skills
        match_result = skill_ner.match_skills(required_skills, candidate_skills, threshold)
       
        # Convert to the expected format with additional details
        # Extract skill names from the matching_skills dictionaries
        matching_skills = []
        if match_result["matching_skills"]:
            for match in match_result["matching_skills"]:
                if isinstance(match, dict) and "job" in match:
                    matching_skills.append(match["job"])
                elif isinstance(match, str):
                    matching_skills.append(match)
        
        missing_skills = list(match_result["missing_skills"]) if match_result["missing_skills"] else []
        extra_skills = list(match_result["extra_skills"]) if match_result["extra_skills"] else []
        
        match_percentage = (len(matching_skills) / len(required_skills) * 100) if required_skills else 0
        # Ensure match_percentage is never negative
        match_percentage = max(0.0, match_percentage)
        
        return {
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "extra_skills": extra_skills,
            "match_percentage": round(match_percentage, 1),
        }

    def _prepare_job_data(self, job: Dict) -> Dict:
        """Pre-processes job data, extracts skills, and generates embeddings."""
        # Extract hard and soft skills from the job data
        hard_skills = [s.lower() for s in job.get("skills", {}).get("hard_skills", [])]
        soft_skills = [s.lower() for s in job.get("skills", {}).get("soft_skills", [])]

        # Render the full job model to text for skill extraction
        job_full_text = render_model(job)

        # Extract skills from the rendered text using NER
        try:
            extracted_skills = [s.lower() for s in skill_ner.extract_skills(job_full_text)]
        except Exception as e:
            logger.error(f"Error extracting skills from job: {e}\n{traceback.format_exc()}")
            extracted_skills = []

        # Deduplicate skills to avoid overlap between provided and extracted skills
        # This gives a more accurate representation for matching
        unique_hard = sorted(list(set(hard_skills)))
        unique_soft = sorted(list(set(soft_skills)))
        # Extracted skills might overlap with hard/soft, so we find what's truly "other"
        unique_extracted = sorted(list(set(extracted_skills) - set(unique_hard) - set(unique_soft)))

        # Create a unified text representation of all unique skills for embedding
        all_skills_text = " ".join(unique_hard + unique_soft + unique_extracted)
        
        return {
            "hard_skills": unique_hard,
            "soft_skills": unique_soft,
            "extracted_skills": unique_extracted,
            "all_skills_text": all_skills_text,
            "full_text": job_full_text,
            "skills_embedding": self.get_embedding(all_skills_text),
            "full_text_embedding": self.get_embedding(job_full_text),
        }
        
    def _score_candidate(self, cand: Dict, job_data: Dict, weights: Dict, fuzzy_threshold: float) -> Dict:
        """Scores a single candidate against pre-processed job data."""
        # Candidate skill extraction
        cand_hard = [s["name"].lower() for s in cand.get("skills", []) if s.get("type") == "Hard" and s.get("name")]
        cand_soft = [s["name"].lower() for s in cand.get("skills", []) if s.get("type") == "Soft" and s.get("name")]
        
        cand_full_text = render_model(cand)
        try:
            cand_extracted = [s.lower() for s in skill_ner.extract_skills(cand_full_text)]
        except Exception as e:
            logger.error(f"Error extracting skills from candidate: {e}\n{traceback.format_exc()}")
            cand_extracted = []
        
        cand_all_skills_text = " ".join(cand_hard + cand_soft + cand_extracted)
        
        # Fuzzy skill matching analysis
        hard_analysis = self.fuzzy_match_skills(job_data["hard_skills"], cand_hard, fuzzy_threshold)
        soft_analysis = self.fuzzy_match_skills(job_data["soft_skills"], cand_soft, fuzzy_threshold)
        extracted_analysis = self.fuzzy_match_skills(job_data["extracted_skills"], cand_extracted, fuzzy_threshold)
        
        all_missing = (hard_analysis.get("missing_skills", []) or []) + (soft_analysis.get("missing_skills", []) or []) + (extracted_analysis.get("missing_skills", []) or [])
        all_extra = (hard_analysis.get("extra_skills", []) or []) + (soft_analysis.get("extra_skills", []) or []) + (extracted_analysis.get("extra_skills", []) or [])
        all_matching = (hard_analysis.get("matching_skills", []) or []) + (soft_analysis.get("matching_skills", []) or []) + (extracted_analysis.get("matching_skills", []) or [])
        
        # Calculate component scores
        hard_score = (hard_analysis.get("match_percentage", 0) or 0) / 100
        soft_score = (soft_analysis.get("match_percentage", 0) or 0) / 100
        extracted_score = (extracted_analysis.get("match_percentage", 0) or 0) / 100
        
        cand_skills_embedding = self.get_embedding(cand_all_skills_text)
        skills_sim = self.calculate_normalized_embedding_similarity(cand_skills_embedding, job_data["skills_embedding"])
        
        cand_full_text_embedding = self.get_embedding(cand_full_text)
        overall_sim = self.calculate_normalized_embedding_similarity(cand_full_text_embedding, job_data["full_text_embedding"])

        # Calculate composite skills_score
        skill_weights = weights["skill_weights"]
        skills_score_components = {
            "hard_skills": hard_score,
            "soft_skills": soft_score,
            "extracted_skills": extracted_score,
            "skills_embedding_similarity": skills_sim,
        }
        skills_score = sum(skill_weights.get(k, 0) * v for k, v in skills_score_components.items() if k in skill_weights)

        # Calculate final weighted score
        final_weights = weights["final_weights"]
        final_score_components = {
            "skills_score": skills_score,
            "overall_similarity": overall_sim,
        }
        final_score = sum(final_weights.get(k, 0) * v for k, v in final_score_components.items() if k in final_weights)

        return {
            "candidate": cand.get("candidate_name") or cand.get("full_name"),
            "score": round(max(0.0, final_score), 3),
            "score_breakdown": final_score_components,
            "missing_skills": sorted(list(set(all_missing))),
            "extra_skills": sorted(list(set(all_extra))),
            "matching_skills": sorted(list(set(all_matching))),
        }

    def match_candidates(
        self,
        job: Dict,
        candidates: List[Dict],
        weights: Optional[Dict] = None,
        fuzzy_threshold: float = 0.60
    ) -> List[Dict]:
        """
        Rank candidates against a job using a two-level scoring model.

        Args:
            job: Job description dictionary
            candidates: List of candidate dictionaries
            weights: Optional nested dictionary for different scoring components.
                     Example:
                     {
                         "final_score_weights": {
                             "skills_score": 0.6,
                             "overall_similarity": 0.4,
                         },
                         "skill_score_weights": {
                             "hard_skills": 0.30,
                             "soft_skills": 0.20,
                             "extracted_skills": 0.25,
                             "skills_embedding_similarity": 0.25,
                         }
                     }
            fuzzy_threshold: Minimum fuzzy match score for skills (0-100)

        Returns:
            List of candidate matches with detailed analysis
        """
        
        if not candidates:
            return []
        try:
            # ---------- 1. Weight preparation ----------
            default_weights = {
                "final_score_weights": {
                    "skills_score": 0.5,
                    "overall_similarity": 0.5,
                },
                "skill_score_weights": {
                    "hard_skills": 0.05,
                    "soft_skills": 0.05,
                    "extracted_skills": 0.05,
                    "skills_embedding_similarity": 0.85,
                }
            }
            
            user_final_weights = (weights or {}).get("final_score_weights", {})
            final_weights = {**default_weights["final_score_weights"], **user_final_weights}
    
            user_skill_weights = (weights or {}).get("skill_score_weights", {})
            skill_weights = {**default_weights["skill_score_weights"], **user_skill_weights}
    
            # Strip zero-weight keys & renormalise for final score
            final_weights = {k: v for k, v in final_weights.items() if v > 0}
            total_final_w = sum(final_weights.values())
            if total_final_w > 0:
                final_weights = {k: v / total_final_w for k, v in final_weights.items()}
    
            # Strip zero-weight keys & renormalise for skill score
            skill_weights = {k: v for k, v in skill_weights.items() if v > 0}
            total_skill_w = sum(skill_weights.values())
            if total_skill_w > 0:
                skill_weights = {k: v / total_skill_w for k, v in skill_weights.items()}
            
            processed_weights = {
                "final_weights": final_weights,
                "skill_weights": skill_weights
            }

            # ---------- 2. Job preprocessing ----------
            job_data = self._prepare_job_data(job)
    
            # ---------- 3. Score all candidates ----------
            results = []
            for cand in candidates:
                result = self._score_candidate(cand, job_data, processed_weights, fuzzy_threshold)
                result["weights_used"] = processed_weights
                results.append(result)
    
            return sorted(results, key=lambda x: x["score"], reverse=True)
        except Exception as e:
            logger.error(f"Error during candidate matching: {e}\n{traceback.format_exc()}")
            return []

    
    
# Exampl    e usage
if __name__ == "__main__":
    # In  itialize the matcher
    matcher = Matcher()

    # Example job description
    job_description = {
        "title": "Senior Machine Learning Engineer",
        "responsibilities": [
            "Design and implement machine learning models",
            "Work with large datasets",
            "Deploy models to production",
        ],
        "skills": {
            "hard_skills": [
                "Python",
                "Machine Learning",
                "Deep Learning",
                "TensorFlow",
                "PyTorch",
            ]
        },
    }

    # Example candidates
    candidates = [
        {
            "full_name": "John Doe",
            "skills": [
                {"name": "Python", "type": "Hard"},
                {"name": "Machine Learning", "type": "Hard"},
                {"name": "TensorFlow", "type": "Hard"},
            ],
            "work_history": [
                {
                    "job_title": "Machine Learning Engineer",
                    "summary": "Developed and deployed ML models.",
                },
                {
                    "job_title": "Software Engineer",
                    "summary": "Built backend systems.",
                },
            ],
        },
        {
            "full_name": "Jane Smith",
            "skills": [
                {"name": "Java", "type": "Hard"},
                {"name": "Spring", "type": "Hard"},
            ],
            "work_history": [
                {
                    "job_title": "Senior Software Engineer",
                    "summary": "Focused on backend development with Java.",
                }
            ],
        },
    ]

    # Get matches with detailed analysis
    matches = matcher.match_candidates(job_description, candidates)

    # Print detailed results
    print("\nMatching Results:")
    print("=" * 80)

    for match in matches:
        print(f"\nCandidate: {match['candidate']}")
        print(f"Final Score: {match['score']:.3f}")
        print(f"Overall Embedding Similarity: {match['overall_embedding_similarity']:.3f}")
        print(f"Skills Embedding Similarity: {match['skills_embedding_similarity']:.3f}")

        print("\nScore Breakdown:")
        print("  Final Score Components:")
        for component, score in match["score_breakdown"]["final_score_components"].items():
            print(f"  - {component}: {score}")
            
        print("\n  Skills Score Components:")
        for component, score in match["score_breakdown"]["skills_score_components"].items():
            print(f"  - {component}: {score}")

        print("\nSkill Analysis:")
        print(f"  Matching Skills: {', '.join(match['matching_skills'])}")
        print(f"  Missing Skills: {', '.join(match['missing_skills'])}")
        print(f"  Extra Skills: {', '.join(match['extra_skills'])}")

        print("\n-" * 80)
