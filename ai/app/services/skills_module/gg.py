# https://github.com/AnasAito/SkillNER?tab=readme-ov-file
#%%
import sys
from pathlib import Path
# Add parent directory to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import spacy
from spacy.matcher import PhraseMatcher
# spacy.download("./skillsNer/en_core_web_lg")
import os
os.system("cd ./skillsNer && python -m spacy download en_core_web_lg")
# load default skills data base
from skillNer.general_params import SKILL_DB
# import skill extractor
from skillNer.skill_extractor_class import SkillExtractor

# init params of skill extractor
nlp = spacy.load("en_core_web_lg")
# init skill extractor
skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

# extract skills from job_description
job_description = """
You are a Python developer with a solid experience in web development
and can manage projects. You quickly adapt to new environments
and speak fluently English and French

python is a must
fastapi expertise is much needed
"""

annotations = skill_extractor.annotate(job_description)
#%%
import pprint
pprint.pprint(annotations)

