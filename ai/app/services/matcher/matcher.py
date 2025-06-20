import numpy as np
from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path
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
        """
        return np.dot(embedding_one, embedding_two) / (np.linalg.norm(embedding_one) * np.linalg.norm(embedding_two))

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


    def fuzzy_match_skills(self, required_skills: List[str], candidate_skills: List[str], threshold: float = 85.0) -> Dict:
        """
        Perform fuzzy matching between required and candidate skills using the ner_skills match_skills method.
        
        Args:
            required_skills: List of required skills
            candidate_skills: List of candidate skills
            threshold: Minimum fuzzy match score to consider a match (0-100)
            
        Returns:
            Dict containing matching, missing, and extra skills with analysis
        """
        print(f"Required skills: {required_skills}")
        print(f"Candidate skills: {candidate_skills}")
        print(f"Threshold: {threshold}")
        # Use the existing match_skills method from ner_skills
        match_result = skill_ner.match_skills(required_skills, candidate_skills, threshold)
       
        # Convert to the expected format with additional details
        matching_skills = list(match_result["matching_skills"])
        missing_skills = list(match_result["missing_skills"])
        extra_skills = list(match_result["extra_skills"])
        
    
        match_percentage = (len(matching_skills) / len(required_skills) * 100) if required_skills else 0
        # Ensure match_percentage is never negative
        match_percentage = max(0.0, match_percentage)
        
        return {
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "extra_skills": extra_skills,
            "match_percentage": round(match_percentage, 1),
        }

    def match_candidates(
        self,
        job: Dict,
        candidates: List[Dict],
        weights: Optional[Dict] = None,
        fuzzy_threshold: float = 80.0
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
                             "overall_embedding_similarity": 0.4,
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
                    "skills_score": 0.6,
                    "overall_embedding_similarity": 0.4,
                },
                "skill_score_weights": {
                    "hard_skills": 0.30,
                    "soft_skills": 0.20,
                    "extracted_skills": 0.25,
                    "skills_embedding_similarity": 0.25,
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
    
            # ---------- 2. Job preprocessing ----------
            job_hard_skills = [s.lower() for s in job.get("skills", {}).get("hard_skills", [])]
            job_soft_skills = [s.lower() for s in job.get("skills", {}).get("soft_skills", [])]
            job_extracted_skills = [
                s.lower()
                for s in skill_ner.extract_skills(render_model(job))
            ]
            job_all_skills_text = " ".join(job_hard_skills + job_soft_skills + job_extracted_skills)
    
            job_full_text = " ".join([
                job.get("title", ""),
                job.get("description", ""),
                " ".join(job.get("responsibilities", [])),
                job.get("seniority_level", ""),
                job.get("job_type", ""),
            ])
    
            results = []
            for cand in candidates:
                # ---------- 3. Candidate skill extraction ----------
                cand_hard = [
                    s["name"].lower()
                    for s in cand.get("skills", [])
                    if s.get("type") == "Hard" and s.get("name")
                ]
                cand_soft = [
                    s["name"].lower()
                    for s in cand.get("skills", [])
                    if s.get("type") == "Soft" and s.get("name")
                ]
                cand_extracted = [
                    s.lower() for s in skill_ner.extract_skills(render_model(cand))
                ]
                cand_all_skills_text = " ".join(cand_hard + cand_soft + cand_extracted)
    
                # ---------- 4. Fuzzy skill matching analysis ----------
                hard_skills_analysis = self.fuzzy_match_skills(job_hard_skills, cand_hard, fuzzy_threshold)
                soft_skills_analysis = self.fuzzy_match_skills(job_soft_skills, cand_soft, fuzzy_threshold)
                extracted_skills_analysis = self.fuzzy_match_skills(job_extracted_skills, cand_extracted, fuzzy_threshold)
                
                missing_skills = list(set(hard_skills_analysis["missing_skills"] + soft_skills_analysis["missing_skills"] + extracted_skills_analysis["missing_skills"]))
                extra_skills = list(set(hard_skills_analysis["extra_skills"] + soft_skills_analysis["extra_skills"] + extracted_skills_analysis["extra_skills"]))
                matching_skills = list(set(hard_skills_analysis["matching_skills"] + soft_skills_analysis["matching_skills"] + extracted_skills_analysis["matching_skills"]))
                
                # ---------- 5. Calculate component scores ----------
                hard_score = max(0.0, hard_skills_analysis["match_percentage"] / 100)
                soft_score = max(0.0, soft_skills_analysis["match_percentage"] / 100)
                extracted_score = max(0.0, extracted_skills_analysis["match_percentage"] / 100)
                
                skills_embedding_similarity = self.calculate_text_similarity(cand_all_skills_text, job_all_skills_text)
    
                cand_full_text = render_model(cand)
                overall_embedding_similarity = self.calculate_text_similarity(cand_full_text, job_full_text)
    
                # ---------- 6. Calculate intermediate and final scores ----------
                # 6a. Calculate the composite "skills_score"
                skills_score_components = {}
                skills_score = 0
    
                if "hard_skills" in skill_weights:
                    skills_score_components["hard_skills"] = hard_score
                    skills_score += skill_weights["hard_skills"] * hard_score
    
                if "soft_skills" in skill_weights:
                    skills_score_components["soft_skills"] = soft_score
                    skills_score += skill_weights["soft_skills"] * soft_score
    
                if "extracted_skills" in skill_weights:
                    skills_score_components["extracted_skills"] = extracted_score
                    skills_score += skill_weights["extracted_skills"] * extracted_score
                    
                if "skills_embedding_similarity" in skill_weights:
                    skills_score_components["skills_embedding_similarity"] = skills_embedding_similarity
                    skills_score += skill_weights["skills_embedding_similarity"] * skills_embedding_similarity
                
                # 6b. Calculate the final weighted score
                final_score_components = {}
                final_score = 0
                
                if "skills_score" in final_weights:
                    final_score_components["skills_score"] = skills_score
                    final_score += final_weights["skills_score"] * skills_score
                
                if "overall_embedding_similarity" in final_weights:
                    final_score_components["overall_embedding_similarity"] = overall_embedding_similarity
                    final_score += final_weights["overall_embedding_similarity"] * overall_embedding_similarity
    
                # Debug logging for negative scores
                if final_score < 0:
                    logger.warning(f"Negative score detected for candidate {cand.get('candidate_name') or cand.get('full_name')}: {final_score}")
                    logger.warning(f"Final Score components: {final_score_components}")
                    logger.warning(f"Skill Score components: {skills_score_components}")
                    logger.warning(f"Weights: final_weights={final_weights}, skill_weights={skill_weights}")
    
                # ---------- 7. Compile result ----------
                # Ensure final score is never negative
                final_score = max(0.0, final_score)
                
                result = {
                    "candidate": cand.get("candidate_name") or cand.get("full_name"),
                    "score": round(final_score, 3),
                    "score_breakdown": {
                        "final_score_components": {k: round(v, 3) for k, v in final_score_components.items()},
                        "skills_score_components": {k: round(v, 3) for k, v in skills_score_components.items()}
                    },
                    "missing_skills": missing_skills,
                    "extra_skills": extra_skills,
                    "matching_skills": matching_skills,
                    "skills_embedding_similarity": round(skills_embedding_similarity, 3),
                    "overall_embedding_similarity": round(overall_embedding_similarity, 3),
                    "weights_used": {
                        "final_weights": final_weights,
                        "skill_weights": skill_weights,
                    }
                }
    
                results.append(result)
    
            return sorted(results, key=lambda x: x["score"], reverse=True)
        except Exception as e:
            import traceback
            print(traceback)

    
    
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
