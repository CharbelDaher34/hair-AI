# from services.llm.entities_models.candidate_pydantic import Candidate
# from services.llm.llm_agent import LLM
# import os

# system_prompt = """
# You are a skilled resume parser. Extract all relevant information from the provided resume 
# and structure it according to the Candidate schema. Follow these guidelines:

# """
# parser = LLM(api_key=os.environ.get("API_KEY"), system_prompt=system_prompt,result_type=Candidate)

# # Example with a PDF file
# # result = parser.parse("path/to/resume.pdf")

# # Example with text
# sample_resume = """
# John Doe
# Software Engineer
# john.doe@example.com | (555) 123-4567 | San Francisco, CA

# WORK EXPERIENCE
# Senior Software Engineer | ABC Tech | 2020-01 to Present
# - Led development of microservices architecture
# - Implemented CI/CD pipeline reducing deployment time by 40%

# Software Developer | XYZ Corp | 2017-06 to 2019-12
# - Developed RESTful APIs for customer-facing applications
# - Optimized database queries improving performance by 30%

# EDUCATION
# Master of Science in Computer Science | Stanford University | 2015-09 to 2017-05
# Bachelor of Science in Software Engineering | MIT | 2011-09 to 2015-05

# SKILLS
# Python, JavaScript, AWS, Docker, Kubernetes, SQL, React, TypeScript

# CERTIFICATIONS
# AWS Certified Solutions Architect | Amazon Web Services | 2019-07
# """

# # Parse the sample resume
# result = parser.parse(sample_resume)
# print(result)

import requests
from pydantic import BaseModel
import json
from enum import Enum
class Skills(BaseModel):
    name: str
    level: str

class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"

class Candidate(BaseModel):
    name: str
    email: str
    gender: Gender
    skills: list[Skills]

class Candidates(BaseModel):
    candidates: list[Candidate]

url = "http://84.16.230.94:8011/parser/parse"

schema_json = json.dumps(Candidate.model_json_schema())
system_prompt = (
    "You are a resume parser. Extract all relevant information from the provided resume and structure it according to the Candidate schema. Follow these guidelines:"
)

# resume_texts = [
#     "John Doe\nEmail: john@example.com\nSkills: Python, FastAPI, Machine Learning",
#     "Jane Smith\nEmail: jane@example.com\nSkills: Java, Docker, AWS"
# ]

# files = []
# try:
#     pdf_file = open("/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf", "rb")
#     files.append(("resume_files", ("sample_resume.pdf", pdf_file, "application/pdf")))
# except FileNotFoundError:
#     print("sample_resume.pdf not found.")
#     pdf_file = None

# image_path = "/storage/hussein/matching/ai/app/services/llm/images.jpeg"
# try:
#     img_file = open(image_path, "rb")
#     files.append(("resume_files", ("sample_resume.png", img_file, "image/png")))
# except FileNotFoundError:
#     print(f"{image_path} not found.")
#     img_file = None

# # Prepare multipart data for both lists and fields
# multipart_data = []
# for resume_text in resume_texts:
#     multipart_data.append(("resume_texts", resume_text))
# multipart_data.append(("schema", schema_json))
# multipart_data.append(("system_prompt", system_prompt))

# response = requests.post(url, data=multipart_data, files=files)
# import json

# # Print the parsed candidates
# print(json.dumps(response.json(), indent=2))

# # Parse single response as Pydantic model
# single_response_json = response.json()
# try:
#     if isinstance(single_response_json, list):
#         parsed_single = [Candidate(**item) if item is not None else None for item in single_response_json]
#     else:
#         parsed_single = Candidate(**single_response_json)
#     print("Parsed single response as Pydantic model(s):", parsed_single)
# except Exception as e:
#     print(f"Error parsing single response as Pydantic model: {e}")

# # Close files
# if pdf_file:
#     pdf_file.close()
# if 'img_file' in locals() and img_file:
#     img_file.close()

# print("Single parse response status:", response.status_code)
# print("Single parse response text:", response.text)


# --- Test for /batch_parse endpoint with files ---
print("\n--- Testing /batch_parse endpoint with files ---")
batch_url = "http://84.16.230.94:8011/parser/batch_parse"

candidate_schema_for_batch_json = Candidate.model_json_schema()

# Prepare file paths and open files
batch_file_paths = [
    ("alice_resume.pdf", "/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf", "application/pdf"),
    ("alice_cert.png", "/storage/hussein/matching/ai/app/services/llm/images.jpeg", "image/png"),
    ("bob_resume.pdf", "/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf", "application/pdf"),
]
opened_files = []
files = []
for fname, fpath, ftype in batch_file_paths:
    try:
        f = open(fpath, "rb")
        files.append(("resume_files", (fname, f, ftype)))
        opened_files.append(f)
    except FileNotFoundError:
        print(f"{fpath} not found. Skipping {fname}.")

batch_metadata = [
    {
        "resume_texts": [
            "Alice Wonderland\nEmail: alice@wonderland.ai\nSkills: Python, Curiouser, Potion Brewing"
        ],
        "resume_files": ["alice_resume.pdf", "alice_cert.png"],
        "schema": json.dumps(candidate_schema_for_batch_json),
        "system_prompt": "Extract candidate details for Alice."
    },
    {
        "resume_texts": None,
        "resume_files": ["bob_resume.pdf"],
        "schema": json.dumps(candidate_schema_for_batch_json),
        "system_prompt": "Extract candidate details for Bob."
    },
    {
        "resume_texts": [],
        "resume_files": [],
        "schema": json.dumps(candidate_schema_for_batch_json),
        "system_prompt": "This prompt will also be ignored."
    }
]

batch_data = {
    'batch_metadata': json.dumps(batch_metadata)
}

try:
    batch_response = requests.post(batch_url, data=batch_data, files=files)
    print("Batch parse response status:", batch_response.status_code)
    print("Batch parse response headers:", batch_response.headers.get('Content-Type'))
    batch_response_json = batch_response.json()
    print("Batch parse response JSON:", json.dumps(batch_response_json, indent=2))
    # Parse each batch result as Candidate
    parsed_batch = []
    for idx, item in enumerate(batch_response_json):
        if item is not None:
            try:
                parsed_item = Candidate(**item)
                parsed_batch.append(parsed_item)
            except Exception as e:
                print(f"Error parsing batch item {idx} as Candidate: {e}")
                parsed_batch.append(None)
        else:
            parsed_batch.append(None)
    print("Parsed batch response as Pydantic models:", parsed_batch)
except requests.exceptions.RequestException as e:
    print(f"Error during batch parse request: {e}")
finally:
    for f in opened_files:
        f.close()   