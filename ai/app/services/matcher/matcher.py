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
            float: Cosine similarity score between 0 and 1
        """
        embedding_one = self.get_embedding(text_one)
        embedding_two = self.get_embedding(text_two)

        # Calculate cosine similarity
        if np.linalg.norm(embedding_one) == 0 or np.linalg.norm(embedding_two) == 0:
            return 0.0
        similarity = np.dot(embedding_one, embedding_two) / (
            np.linalg.norm(embedding_one) * np.linalg.norm(embedding_two)
        )
        return float(similarity)


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
        weights: Optional[Dict[str, float]] = None,
        fuzzy_threshold: float = 80.0
    ) -> List[Dict]:
        """
        Rank candidates against a job using fuzzy skill matching and embedding similarity.

        Args:
            job: Job description dictionary
            candidates: List of candidate dictionaries
            weights: Optional weights for different scoring components
            fuzzy_threshold: Minimum fuzzy match score for skills (0-100)

        Returns:
            List of candidate matches with detailed analysis
        """

        if not candidates:
            return []

        # ---------- 1. Weight preparation ----------
        default_weights = {
            "hard_skills": 0.30,
            "soft_skills": 0.20,
            "extracted_skills": 0.25,
            "embedding_similarity": 0.25,
        }
        weights = weights or default_weights
        # Strip zero-weight keys & renormalise
        weights = {k: v for k, v in weights.items() if v > 0}
        total_w = sum(weights.values())
        weights = {k: v / total_w for k, v in weights.items()}

        # ---------- 2. Job preprocessing ----------
        job_hard_skills = [s.lower() for s in job.get("skills", {}).get("hard_skills", [])]
        job_soft_skills = [s.lower() for s in job.get("skills", {}).get("soft_skills", [])]
        job_extracted_skills = [
            s.lower()
            for s in skill_ner.extract_skills(render_model(job))
        ]

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

            # ---------- 4. Fuzzy skill matching analysis ----------
            hard_skills_analysis = self.fuzzy_match_skills(job_hard_skills, cand_hard, fuzzy_threshold)
            soft_skills_analysis = self.fuzzy_match_skills(job_soft_skills, cand_soft, fuzzy_threshold)
            extracted_skills_analysis = self.fuzzy_match_skills(job_extracted_skills, cand_extracted, fuzzy_threshold)
            
            missing_skills = list(set(hard_skills_analysis["missing_skills"] + soft_skills_analysis["missing_skills"] + extracted_skills_analysis["missing_skills"]))
            extra_skills = list(set(hard_skills_analysis["extra_skills"] + soft_skills_analysis["extra_skills"] + extracted_skills_analysis["extra_skills"]))
            matching_skills = list(set(hard_skills_analysis["matching_skills"] + soft_skills_analysis["matching_skills"] + extracted_skills_analysis["matching_skills"]))
            
            # ---------- 5. Calculate scores ----------
            hard_score = hard_skills_analysis["match_percentage"] / 100
            soft_score = soft_skills_analysis["match_percentage"] / 100
            extracted_score = extracted_skills_analysis["match_percentage"] / 100

            # Embedding similarity
            cand_full_text = render_model(cand)
            embedding_similarity = self.calculate_text_similarity(cand_full_text, job_full_text)

            # ---------- 6. Calculate weighted final score ----------
            score_components = {}
            final_score = 0

            if "hard_skills" in weights:
                score_components["hard_skills"] = hard_score
                final_score += weights["hard_skills"] * hard_score

            if "soft_skills" in weights:
                score_components["soft_skills"] = soft_score
                final_score += weights["soft_skills"] * soft_score

            if "extracted_skills" in weights:
                score_components["extracted_skills"] = extracted_score
                final_score += weights["extracted_skills"] * extracted_score

            if "embedding_similarity" in weights:
                score_components["embedding_similarity"] = embedding_similarity
                final_score += weights["embedding_similarity"] * embedding_similarity

            # ---------- 7. Compile result ----------
            result = {
                "candidate": cand.get("candidate_name") or cand.get("full_name"),
                "score": round(final_score, 3),
                "score_breakdown": {k: round(v, 3) for k, v in score_components.items()},
                "missing_skills": missing_skills,
                "extra_skills": extra_skills,
                "matching_skills": matching_skills,
                "embedding_similarity": round(embedding_similarity, 3),
                "weights_used": weights
            }

            results.append(result)

        return sorted(results, key=lambda x: x["score"], reverse=True)


# Example usage
if __name__ == "__main__":
    # Initialize the matcher
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
        print(f"Embedding Similarity: {match['embedding_similarity']:.3f}")

        print("\nScore Breakdown:")
        for component, score in match["score_breakdown"].items():
            print(f"- {component}: {score}")

        print("\nSkill Analysis:")
        print(f"  Hard Skills:")
        print(f"    Match Percentage: {match['skill_analysis']['hard_skills']['match_percentage']}%")
        print(
            f"    Matching Skills: {', '.join(match['skill_analysis']['hard_skills']['matching_skills'])}"
        )
        print(
            f"    Missing Skills: {', '.join(match['skill_analysis']['hard_skills']['missing_skills'])}"
        )
        print(f"    Extra Skills: {', '.join(match['skill_analysis']['hard_skills']['extra_skills'])}")
        print(
            f"    Total Required: {match['skill_analysis']['hard_skills']['total_required']}"
        )
        print(
            f"    Matching Count: {match['skill_analysis']['hard_skills']['matching_count']}"
        )

        print(f"\n  Soft Skills:")
        print(f"    Match Percentage: {match['skill_analysis']['soft_skills']['match_percentage']}%")
        print(
            f"    Matching Skills: {', '.join(match['skill_analysis']['soft_skills']['matching_skills'])}"
        )
        print(
            f"    Missing Skills: {', '.join(match['skill_analysis']['soft_skills']['missing_skills'])}"
        )
        print(f"    Extra Skills: {', '.join(match['skill_analysis']['soft_skills']['extra_skills'])}")
        print(
            f"    Total Required: {match['skill_analysis']['soft_skills']['total_required']}"
        )
        print(
            f"    Matching Count: {match['skill_analysis']['soft_skills']['matching_count']}"
        )

        print(f"\n  Extracted Skills:")
        print(f"    Match Percentage: {match['skill_analysis']['extracted_skills']['match_percentage']}%")
        print(
            f"    Matching Skills: {', '.join(match['skill_analysis']['extracted_skills']['matching_skills'])}"
        )
        print(
            f"    Missing Skills: {', '.join(match['skill_analysis']['extracted_skills']['missing_skills'])}"
        )
        print(f"    Extra Skills: {', '.join(match['skill_analysis']['extracted_skills']['extra_skills'])}")
        print(
            f"    Total Required: {match['skill_analysis']['extracted_skills']['total_required']}"
        )
        print(
            f"    Matching Count: {match['skill_analysis']['extracted_skills']['matching_count']}"
        )

        print("\n-" * 80)
