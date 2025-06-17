import numpy as np
from typing import List, Dict, Tuple
import sys
from pathlib import Path
from typing import Optional
# Add parent directory to path for imports
# project_root = Path(__file__).resolve().parent.parent.parent
# sys.path.insert(0, str(project_root))

from services.skills_module.ner_skills import skill_ner
from sentence_transformers import SentenceTransformer
import logging

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
        self.skills_ner = skill_ner()

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a given text.

        Args:
            text: Input text to generate embedding for

        Returns:
            numpy array containing the embedding
        """
        return self.embedding_model.encode(text)

    def calculate_embedding_similarity(self, text_one: str, text_two: str) -> float:
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
        similarity = np.dot(embedding_one, embedding_two) / (
            np.linalg.norm(embedding_one) * np.linalg.norm(embedding_two)
        )
        return float(similarity)

    def match_candidates(
        self,
        job_description: str,
        candidates: List[str],
        skill_weight: float = 0.4,
        embedding_weight: float = 0.6,
        candidate_skills: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Match candidates against a job description using both skill and embedding similarity.

        Args:
            job_description: Job description text
            candidates: List of candidate dictionaries containing at least 'text' key
            skill_weight: Weight for skill-based similarity (default: 0.4)
            embedding_weight: Weight for embedding-based similarity (default: 0.6)

        Returns:
            List of dictionaries containing candidate info and detailed matching analysis
        """
        if not candidates:
            return []

        results = []

        for candidate in candidates:
            candidate_text = candidate
            print(f"candidate_skills: {candidate_skills}")
            # Get detailed skill analysis
            skill_analysis = self.skills_ner.get_skill_match_details(
                job_description, candidate_text, candidate_skills
            )

            # Calculate embedding similarity
            embedding_similarity = self.calculate_embedding_similarity(
                job_description, candidate_text
            )

            # Calculate weighted score
            final_score = (
                skill_weight * (skill_analysis["match_percentage"] / 100)
                + embedding_weight * embedding_similarity
            )

            # Create detailed result
            result = {
                "candidate": candidate,
                "score": round(final_score, 3),
                "skill_analysis": {
                    "match_percentage": skill_analysis["match_percentage"],
                    "matching_skills": skill_analysis["skill_analysis"][
                        "matching_skills"
                    ],
                    "missing_skills": skill_analysis["skill_analysis"][
                        "missing_skills"
                    ],
                    "extra_skills": skill_analysis["skill_analysis"]["extra_skills"],
                    "summary": skill_analysis["summary"],
                },
                "embedding_similarity": round(embedding_similarity, 3),
                "weights": {
                    "skill_weight": skill_weight,
                    "embedding_weight": embedding_weight,
                },
            }

            results.append(result)

        # Sort results by score in descending order
        return sorted(results, key=lambda x: x["score"], reverse=True)


# Example usage
if __name__ == "__main__":
    # Initialize the matcher
    matcher = Matcher()

    # Example job description
    job_description = """
    Senior Machine Learning Engineer

    Required Skills:
    - Python programming
    - Machine Learning
    - Deep Learning
    - TensorFlow
    - PyTorch
    - Natural Language Processing
    - Data Analysis
    - Cloud Computing
    - MLOps
    - Docker
    """

    # Example candidates
    candidates = [
        """
            Senior ML Engineer with 8+ years of experience
            - Expert in Python, TensorFlow, and PyTorch
            - Deep Learning and NLP specialist
            - Strong MLOps and cloud experience
            - Docker and Kubernetes expertise
            - Led multiple ML projects from research to production
                """,
        """
            Senior Data Scientist with 7+ years of experience
            - Python and statistical analysis expert
            - Machine Learning and data analysis
            - Basic deep learning knowledge
            - Cloud platform experience
            - Focus on analytics and reporting
            """,
        """
            Senior Software Engineer with 10+ years of experience
            - Java and Spring Boot expert
            - System architecture and design
            - Microservices and cloud platforms
            - Basic ML understanding
            - Focus on backend development
            """,
    ]

    # Get matches with detailed analysis
    matches = matcher.match_candidates(job_description, candidates)

    # Print detailed results
    print("\nMatching Results:")
    print("=" * 80)

    for match in matches:
        candidate = match["candidate"]
        print(f"\nCandidate {candidate}:")
        print(f"Final Score: {match['score']:.3f}")
        print(f"Skill Match: {match['skill_analysis']['match_percentage']}%")
        print(f"Embedding Similarity: {match['embedding_similarity']:.3f}")

        print("\nMatching Skills:")
        for skill in match["skill_analysis"]["matching_skills"]:
            print(f"✓ {skill}")

        print("\nMissing Skills:")
        for skill in match["skill_analysis"]["missing_skills"]:
            print(f"✗ {skill}")

        print("\nExtra Skills:")
        for skill in match["skill_analysis"]["extra_skills"]:
            print(f"+ {skill}")

        print("\nSummary:")
        print(
            f"Total Required Skills: {match['skill_analysis']['summary']['total_required_skills']}"
        )
        print(
            f"Matching Skills Count: {match['skill_analysis']['summary']['matching_skills_count']}"
        )
        print(
            f"Missing Skills Count: {match['skill_analysis']['summary']['missing_skills_count']}"
        )
        print(
            f"Extra Skills Count: {match['skill_analysis']['summary']['extra_skills_count']}"
        )
        print("-" * 80)
