import re
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from gliner import GLiNER
import torch
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class skill_ner:
    # — spaCy + GLiNER setup — #
    _nlp = None
    try:
        _nlp = spacy.load("en_core_web_trf")
    except OSError:
        _nlp = spacy.load("en_core_web_lg")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    _gliner_model = GLiNER.from_pretrained("knowledgator/gliner-x-large",device=device)
    _VEC_CACHE: Dict[str, np.ndarray] = {}

    @classmethod
    def _clean(cls, phrase: str) -> str:
        try:
            if not phrase or phrase is None:
                return ""

            s = str(phrase).lower()
            s = re.sub(r"[,&\-\/]", " ", s)
            s = re.sub(r"\s+", " ", s).strip()

            # Process with spaCy safely
            doc = cls._nlp(s)
            cleaned_tokens = []
            for tok in doc:
                if tok.lemma_ and tok.lemma_.strip():
                    cleaned_tokens.append(tok.lemma_)

            return " ".join(cleaned_tokens) if cleaned_tokens else s
        except Exception as e:
            logger.warning(f"Error cleaning phrase '{phrase}': {e}")
            return str(phrase).lower().strip() if phrase else ""

    @classmethod
    def _vec(cls, phrase: str) -> np.ndarray:
        try:
            key = cls._clean(phrase)
            if not key or not key.strip():
                # Return a zero vector for empty phrases
                return np.zeros(cls._nlp.vocab.vectors_length)

            if key in cls._VEC_CACHE:
                return cls._VEC_CACHE[key]

            doc = cls._nlp(key)
            vec = doc.vector

            # Handle case where vector is all zeros or invalid
            if vec is None or not hasattr(vec, "shape") or vec.shape[0] == 0:
                vec = np.zeros(cls._nlp.vocab.vectors_length)

            norm = np.linalg.norm(vec) + 1e-9
            vec = vec / norm
            cls._VEC_CACHE[key] = vec
            return vec
        except Exception as e:
            logger.warning(f"Error creating vector for phrase '{phrase}': {e}")
            # Return a zero vector as fallback
            try:
                return np.zeros(cls._nlp.vocab.vectors_length)
            except:
                return np.zeros(300)  # Default vector size fallback

    @classmethod
    def extract_skills(cls, text: str) -> List[str]:
        try:
            if not text or not isinstance(text, str):
                return []

            labels = ["soft skills", "technical skills"]
            entities = cls._gliner_model.predict_entities(text, labels, threshold=0.5)
            
            if not entities:
                return []

            skills = set()
            for entity in entities:
                if entity and "text" in entity and entity["text"]:
                    skills.add(entity["text"].strip())

            return sorted(skills)
        except Exception as e:
            logger.error(f"Error extracting skills from text: {e}")
            return []

    @classmethod
    def match_skills(
        cls,
        job_skills: List[str],
        candidate_skills: List[str],
        threshold: float = 0.60,
    ) -> Dict[str, List]:
        try:
            # Safety checks for input parameters
            if not job_skills:
                job_skills = []
            if not candidate_skills:
                candidate_skills = []

            # Filter out None values and ensure all items are strings
            job_skills = [str(s) for s in job_skills if s is not None]
            candidate_skills = [str(s) for s in candidate_skills if s is not None]

            # If no job skills, return empty result
            if not job_skills:
                return {
                    "matching_skills": [],
                    "missing_skills": [],
                    "extra_skills": candidate_skills,
                }

            # normalize
            job_norm = [cls._clean(s) for s in job_skills]
            cand_norm = [cls._clean(s) for s in candidate_skills]

            matched, missing = [], []
            used_cand_idxs = set()

            # 1. Exact (cleaned) matches upfront
            for j_raw, j in zip(job_skills, job_norm):
                for idx, c in enumerate(cand_norm):
                    if j == c:
                        matched.append(
                            {
                                "job": j_raw,
                                "candidate": candidate_skills[idx],
                                "score": 1.0,
                            }
                        )
                        used_cand_idxs.add(idx)
                        break
                else:
                    missing.append((j_raw, j))  # keep cleaned form for next step

            # 2. Cosine similarity match for the still-missing ones
            true_missing = []
            for j_raw, j in missing:
                try:
                    v_j = cls._vec(j)
                    best = {"idx": None, "score": 0.0}
                    for idx, c in enumerate(cand_norm):
                        if idx in used_cand_idxs:
                            continue
                        try:
                            v_c = cls._vec(c)
                            sim = float(
                                cosine_similarity(
                                    v_j.reshape(1, -1), v_c.reshape(1, -1)
                                )[0, 0]
                            )
                            if sim > best["score"]:
                                best = {"idx": idx, "score": sim}
                        except Exception as e:
                            logger.warning(
                                f"Error computing similarity for '{j}' and '{c}': {e}"
                            )
                            continue

                    if best["idx"] is not None and best["score"] >= threshold:
                        matched.append(
                            {
                                "job": j_raw,
                                "candidate": candidate_skills[best["idx"]],
                                "score": round(best["score"], 2),
                            }
                        )
                        used_cand_idxs.add(best["idx"])
                    else:
                        true_missing.append(j_raw)
                except Exception as e:
                    logger.warning(f"Error processing skill '{j_raw}': {e}")
                    true_missing.append(j_raw)

            # 3. Extras = candidate skills NOT used and NOT required
            req_set = set(job_norm)
            extra = [
                cs
                for idx, cs in enumerate(candidate_skills)
                if idx not in used_cand_idxs and cls._clean(cs) not in req_set
            ]

            return {
                "matching_skills": matched,
                "missing_skills": true_missing,
                "extra_skills": extra,
            }
        except Exception as e:
            logger.error(f"Error in match_skills: {e}")
            return {
                "matching_skills": [],
                "missing_skills": job_skills or [],
                "extra_skills": candidate_skills or [],
            }

    @classmethod
    def analyze_skills(
        cls,
        job_text: str,
        candidate_text: str,
        candidate_skills: Optional[List[str]] = None,
    ) -> Dict:
        job = cls.extract_skills(job_text)
        resum = cls.extract_skills(candidate_text)
        all_cand = (candidate_skills or []) + resum
        res = cls.match_skills(job, all_cand)
        return {
            "matching_skills": res["matching_skills"],
            "missing_skills": res["missing_skills"],
            "extra_skills": res["extra_skills"],
            "total_job_skills": len(job),
            "total_candidate_skills": len(all_cand),
            "matching_skills_count": len(res["matching_skills"]),
            "missing_skills_count": len(res["missing_skills"]),
            "extra_skills_count": len(res["extra_skills"]),
        }

    @classmethod
    def calculate_skills_resemblance_rate(
        cls, text_one: str, text_two: str
    ) -> Tuple[float, Dict]:
        s1, s2 = set(cls.extract_skills(text_one)), set(cls.extract_skills(text_two))
        if not s1 and not s2:
            return 1.0, {
                "matching_skills": [],
                "missing_skills": [],
                "extra_skills": [],
            }
        if not s1 or not s2:
            return 0.0, {
                "matching_skills": [],
                "missing_skills": [],
                "extra_skills": [],
            }
        rate = len(s1 & s2) / len(s1 | s2)
        analysis = cls.analyze_skills(text_one, text_two)
        logger.info(f"Resemblance Rate: {rate:.2f}")
        return rate, analysis

    @classmethod
    def get_skill_match_details(
        cls,
        job_text: str,
        candidate_text: str,
        candidate_skills: Optional[List[str]] = None,
    ) -> Dict:
        analysis = cls.analyze_skills(job_text, candidate_text, candidate_skills)
        total = analysis["total_job_skills"]
        pct = (analysis["matching_skills_count"] / total * 100) if total else 0.0
        return {
            "match_percentage": round(pct, 2),
            "skill_analysis": analysis,
            "summary": {
                "total_required_skills": total,
                "matching_skills_count": analysis["matching_skills_count"],
                "missing_skills_count": analysis["missing_skills_count"],
                "extra_skills_count": analysis["extra_skills_count"],
            },
        }


if __name__ == "__main__":
    # Test with GLiNER-based skill extraction
    job_text = """
    We are looking for a Python developer with experience in Machine Learning and Deep Learning.
    The candidate should have strong communication skills and be able to work in a team environment.
    Cloud Computing experience with AWS and Data Engineering skills are required.
    """
    
    candidate_text = """
    I have 5 years of experience in python programming and machine learning.
    I've worked with deep learning frameworks and have excellent communication abilities.
    I'm experienced in team collaboration and have worked with AWS cloud services.
    I also have data engineer experience and additional skills in project management.
    """

    print("Job Skills:", skill_ner.extract_skills(job_text))
    print("Candidate Skills:", skill_ner.extract_skills(candidate_text))
    
    details = skill_ner.get_skill_match_details(job_text, candidate_text)
    print(f"\nMatch Percentage: {details['match_percentage']}%")
    print(f"Matching Skills: {len(details['skill_analysis']['matching_skills'])}")
    print(f"Missing Skills: {len(details['skill_analysis']['missing_skills'])}")
    print(f"Extra Skills: {len(details['skill_analysis']['extra_skills'])}")
