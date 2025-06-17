import spacy
from skillNer.skill_extractor_class import SkillExtractor
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from typing import Dict, List, Set, Tuple
import logging
from typing import Optional
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


class skill_ner:
    # Class variables
    _nlp = None  # Initialize _nlp
    try:
        _nlp = spacy.load("en_core_web_lg")
        logger.info("Successfully loaded en_core_web_lg model.")
    except OSError as e_os:  # Catch OSError specifically for "model not found" (E050)
        logger.warning(
            f"Spacy model 'en_core_web_lg' not found (Original Error: {e_os}). Attempting to download..."
        )
        try:
            spacy.cli.download("en_core_web_lg")
            logger.info("Model 'en_core_web_lg' downloaded. Attempting to load again.")
            _nlp = spacy.load("en_core_web_lg")  # Load after download
            logger.info("Successfully loaded 'en_core_web_lg' after download.")
        except SystemExit as se:  # spacy.cli.download can cause SystemExit
            logger.error(
                f"Spacy download CLI exited with code {se.code}. This may be due to permissions, network issues, or model incompatibility. Model 'en_core_web_lg' may not be loaded."
            )
            # Re-raise a comprehensive error indicating failure to load the model
            raise RuntimeError(
                f"Failed to initialize spaCy model 'en_core_web_lg'. Download command exited (code: {se.code}). Original OSError: {e_os}"
            ) from se
        except Exception as e_after_download:
            logger.error(
                f"Failed to load 'en_core_web_lg' even after download attempt: {e_after_download}"
            )
            # Propagate this new error, including context from the original OSError
            raise RuntimeError(
                f"Failed to initialize spaCy model 'en_core_web_lg' after download attempt. Load error: {e_after_download}. Original OSError: {e_os}"
            ) from e_after_download
    except Exception as e_initial_load:
        # Catch any other unexpected errors during the initial load
        logger.error(
            f"An unexpected error occurred during initial load of 'en_core_web_lg': {e_initial_load}"
        )
        raise RuntimeError(
            f"Unexpected error loading spaCy model 'en_core_web_lg': {e_initial_load}"
        ) from e_initial_load

    if _nlp is None:
        # This state indicates a failure to load the model through all attempts.
        # This should ideally be caught by the exceptions above, but serves as a final check.
        critical_msg = "CRITICAL: SpaCy model 'en_core_web_lg' could not be loaded and _nlp is None. Application cannot proceed."
        logger.critical(critical_msg)
        raise RuntimeError(critical_msg)

    _skill_extractor = SkillExtractor(_nlp, SKILL_DB, PhraseMatcher)

    @classmethod
    def extract_skills(cls, text: str) -> Set[str]:
        """Extract skills using the current SkillNER output format"""
        annotations = cls._skill_extractor.annotate(text)
        skills = set()

        # Handle full matches
        for match in annotations["results"]["full_matches"]:
            skills.add(match["doc_node_value"].strip())

        # Handle ngram matches (new format)
        for ngram in annotations["results"]["ngram_scored"]:
            if "skill_id" in ngram:
                skills.add(ngram["doc_node_value"].strip())
            else:
                skills.add(ngram["doc_node_value"].strip())

        return sorted(skills)

    def match_skills(
        job_skills: list[str], candidate_skills: list[str], threshold: float = 85.0
    ):
        job_skills_set = set([x.lower() for x in job_skills])
        candidate_skills_set = set([x.lower() for x in candidate_skills])

        matched = set()
        missing = set(job_skills_set)
        matched_candidate_skills = set()

        # If no candidate skills, all job skills are missing
        if not candidate_skills_set:
            return {
                "matching_skills": matched,
                "missing_skills": missing,
                "extra_skills": set(),
            }

        for job_skill in job_skills_set:
            result = process.extractOne(
                job_skill,
                candidate_skills_set,
                scorer=fuzz.ratio,
            )
            if result is not None:
                best_match, score, match_index = result
                if score >= threshold:
                    matched.add(job_skill)
                    missing.discard(job_skill)
                    matched_candidate_skills.add(best_match)

        extra = candidate_skills_set - matched_candidate_skills

        return {
            "matching_skills": matched,
            "missing_skills": missing,
            "extra_skills": extra,
        }

    @classmethod
    def analyze_skills(
        cls,
        job_text: str,
        candidate_text: str,
        candidate_skills: Optional[List[str]] = None,
    ) -> Dict:
        """
        Analyze skills between job description and candidate profile.
        Returns detailed analysis including matching, missing, and extra skills.
        """
        job_skills = cls.extract_skills(job_text)

        resume_skills = cls.extract_skills(candidate_text)
        try:
            candidate_skills = candidate_skills if candidate_skills else []
            candidate_skills.extend(resume_skills)
        except Exception as e:
            print(f"Error: {e}")
            candidate_skills = resume_skills

        match_skills = cls.match_skills(job_skills, candidate_skills)
        # matching_skills = job_skills & candidate_skills
        # missing_skills = job_skills - candidate_skills
        # extra_skills = candidate_skills - job_skills

        return {
            "matching_skills": list(match_skills["matching_skills"]),
            "missing_skills": list(match_skills["missing_skills"]),
            "extra_skills": list(match_skills["extra_skills"]),
            "total_job_skills": len(job_skills),
            "total_candidate_skills": len(candidate_skills),
            "matching_skills_count": len(match_skills["matching_skills"]),
            "missing_skills_count": len(match_skills["missing_skills"]),
            "extra_skills_count": len(match_skills["extra_skills"]),
        }

    @classmethod
    def calculate_skills_resemblance_rate(
        cls, text_one: str, text_two: str
    ) -> Tuple[float, Dict]:
        """
        Calculate the rate of resemblance between skills in two texts with detailed analysis.
        Returns both the resemblance rate and detailed skill analysis.
        """
        skills_one = set(cls.extract_skills(text_one))
        skills_two = set(cls.extract_skills(text_two))

        if not skills_one and not skills_two:
            return 1.0, {
                "matching_skills": [],
                "missing_skills": [],
                "extra_skills": [],
            }
        if not skills_one or not skills_two:
            return 0.0, {
                "matching_skills": [],
                "missing_skills": [],
                "extra_skills": [],
            }

        intersection_count = len(skills_one & skills_two)
        union_count = len(skills_one | skills_two)
        resemblance_rate = intersection_count / union_count

        # Calculate skill analysis
        analysis = cls.analyze_skills(text_one, text_two)

        # Log detailed analysis
        logger.info(f"Skill Analysis:")
        logger.info(f"Matching Skills: {analysis['matching_skills']}")
        logger.info(f"Missing Skills: {analysis['missing_skills']}")
        logger.info(f"Extra Skills: {analysis['extra_skills']}")
        logger.info(f"Resemblance Rate: {resemblance_rate:.2f}")

        return resemblance_rate, analysis

    @classmethod
    def get_skill_match_details(
        cls,
        job_text: str,
        candidate_text: str,
        candidate_skills: Optional[List[str]] = None,
    ) -> Dict:
        """
        Get detailed skill matching information between job and candidate.
        Includes skill categories and match percentages.
        """
        analysis = cls.analyze_skills(job_text, candidate_text, candidate_skills)

        # Calculate match percentages
        total_required = analysis["total_job_skills"]
        if total_required > 0:
            match_percentage = (
                analysis["matching_skills_count"] / total_required
            ) * 100
        else:
            match_percentage = 0

        return {
            "match_percentage": round(match_percentage, 2),
            "skill_analysis": analysis,
            "summary": {
                "total_required_skills": total_required,
                "matching_skills_count": analysis["matching_skills_count"],
                "missing_skills_count": analysis["missing_skills_count"],
                "extra_skills_count": analysis["extra_skills_count"],
            },
        }


# Example usage
if __name__ == "__main__":
    skills_ner = skill_ner()

    # Example job description
    job_text = """
    Required Skills:
    - Python programming
    - Machine Learning
    - Deep Learning
    - TensorFlow
    - PyTorch
    - Natural Language Processing
    - Data Analysis
    - Cloud Computing
    """

    # Example candidate profile
    candidate_text = """
    Skills:
    - Python
    - Machine Learning
    - Deep Learning
    - TensorFlow
    - Data Analysis
    - SQL
    - Docker
    """

    # Get detailed skill analysis
    match_details = skills_ner.get_skill_match_details(job_text, candidate_text)

    print("\nSkill Match Analysis:")
    print("=" * 50)
    print(f"Match Percentage: {match_details['match_percentage']}%")
    print("\nMatching Skills:")
    for skill in match_details["skill_analysis"]["matching_skills"]:
        print(f"✓ {skill}")
    print("\nMissing Skills:")
    for skill in match_details["skill_analysis"]["missing_skills"]:
        print(f"✗ {skill}")
    print("\nExtra Skills:")
    for skill in match_details["skill_analysis"]["extra_skills"]:
        print(f"+ {skill}")
