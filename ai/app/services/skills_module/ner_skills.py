import spacy
from skillNer.skill_extractor_class import SkillExtractor
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from typing import Dict, List, Set, Tuple
import logging

logger = logging.getLogger(__name__)

class skill_ner:
    # Class variables
    try:
        _nlp = spacy.load("en_core_web_lg")
    except Exception as e:
        
        spacy.cli.download("en_core_web_lg")
        _nlp = spacy.load("en_core_web_lg")
        logger.error(f"Error loading spacy model: {e}")
        raise e
    
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

    @classmethod
    def analyze_skills(cls, job_text: str, candidate_text: str) -> Dict:
        """
        Analyze skills between job description and candidate profile.
        Returns detailed analysis including matching, missing, and extra skills.
        """
        job_skills = set(cls.extract_skills(job_text))
        candidate_skills = set(cls.extract_skills(candidate_text))
        
        matching_skills = job_skills & candidate_skills
        missing_skills = job_skills - candidate_skills
        extra_skills = candidate_skills - job_skills
        
        return {
            "matching_skills": sorted(matching_skills),
            "missing_skills": sorted(missing_skills),
            "extra_skills": sorted(extra_skills),
            "total_job_skills": len(job_skills),
            "total_candidate_skills": len(candidate_skills),
            "matching_skills_count": len(matching_skills),
            "missing_skills_count": len(missing_skills),
            "extra_skills_count": len(extra_skills)
        }

    @classmethod
    def calculate_skills_resemblance_rate(cls, text_one: str, text_two: str) -> Tuple[float, Dict]:
        """
        Calculate the rate of resemblance between skills in two texts with detailed analysis.
        Returns both the resemblance rate and detailed skill analysis.
        """
        skills_one = set(cls.extract_skills(text_one))
        skills_two = set(cls.extract_skills(text_two))
        
        if not skills_one and not skills_two:
            return 1.0, {"matching_skills": [], "missing_skills": [], "extra_skills": []}
        if not skills_one or not skills_two:
            return 0.0, {"matching_skills": [], "missing_skills": [], "extra_skills": []}
            
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
    def get_skill_match_details(cls, job_text: str, candidate_text: str) -> Dict:
        """
        Get detailed skill matching information between job and candidate.
        Includes skill categories and match percentages.
        """
        analysis = cls.analyze_skills(job_text, candidate_text)
        
        # Calculate match percentages
        total_required = analysis["total_job_skills"]
        if total_required > 0:
            match_percentage = (analysis["matching_skills_count"] / total_required) * 100
        else:
            match_percentage = 0
            
        return {
            "match_percentage": round(match_percentage, 2),
            "skill_analysis": analysis,
            "summary": {
                "total_required_skills": total_required,
                "matching_skills_count": analysis["matching_skills_count"],
                "missing_skills_count": analysis["missing_skills_count"],
                "extra_skills_count": analysis["extra_skills_count"]
            }
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
    for skill in match_details['skill_analysis']['matching_skills']:
        print(f"✓ {skill}")
    print("\nMissing Skills:")
    for skill in match_details['skill_analysis']['missing_skills']:
        print(f"✗ {skill}")
    print("\nExtra Skills:")
    for skill in match_details['skill_analysis']['extra_skills']:
        print(f"+ {skill}")
    
    