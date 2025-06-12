import os
import sys
import json
import asyncio
from pathlib import Path
from PIL import Image
from services.llm.llm_agent import LLM
import dotenv
from services.llm.entities_models.candidate_pydantic import Candidate

system_prompt = """
You are a resume parser. Extract all relevant information from the provided resume and structure it according to the Candidate schema. Follow these guidelines:
"""

dotenv.load_dotenv()
print(os.environ.get("API_KEY"))
# Sample resume text for testing
SAMPLE_RESUME = """
Sarah Johnson
Senior Data Scientist
sarah.johnson@example.com | (555) 987-6543 | New York, NY

WORK EXPERIENCE
Lead Data Scientist | Data Innovations Inc. | 2021-03 to Present
- Led a team of 5 data scientists on multiple ML projects
- Implemented advanced NLP algorithms for sentiment analysis
- Reduced prediction error by 25% using ensemble methods

Data Scientist | Tech Solutions Corp | 2018-09 to 2021-02
- Developed predictive models for customer churn
- Created data visualization dashboards using Tableau
- Collaborated with cross-functional teams on product improvements

EDUCATION
Ph.D. in Statistics | Cornell University | 2014-09 to 2018-08
Master of Science in Applied Mathematics | University of Michigan | 2012-09 to 2014-05
Bachelor of Science in Computer Science | University of California, Berkeley | 2008-09 to 2012-05

SKILLS
Python, R, TensorFlow, PyTorch, SQL, Big Data, Machine Learning, Deep Learning, Statistics

CERTIFICATIONS
Google Cloud Professional Data Engineer | Google | 2020-05
Microsoft Certified: Azure Data Scientist Associate | Microsoft | 2019-11
"""


input_data_list = [
    """
            Sarah Johnson
Senior Data Scientist
sarah.johnson@example.com | (555) 987-6543 | New York, NY

WORK EXPERIENCE
Lead Data Scientist | Data Innovations Inc. | 2021-03 to Present
- Led a team of 5 data scientists on multiple ML projects
- Implemented advanced NLP algorithms for sentiment analysis
- Reduced prediction error by 25% using ensemble methods

Data Scientist | Tech Solutions Corp | 2018-09 to 2021-02
- Developed predictive models for customer churn
- Created data visualization dashboards using Tableau
- Collaborated with cross-functional teams on product improvements""",
    """
EDUCATION
Ph.D. in Statistics | Cornell University | 2014-09 to 2018-08
Master of Science in Applied Mathematics | University of Michigan | 2012-09 to 2014-05
Bachelor of Science in Computer Science | University of California, Berkeley | 2008-09 to 2012-05

SKILLS
Python, R, TensorFlow, PyTorch, SQL, Big Data, Machine Learning, Deep Learning, Statistics

CERTIFICATIONS
Google Cloud Professional Data Engineer | Google | 2020-05
Microsoft Certified: Azure Data Scientist Associate | Microsoft | 2019-11
""",
]


async def test_parser(input_data=SAMPLE_RESUME):
    """Test the parsing functionality."""
    parser = LLM(
        api_key=os.environ.get("API_KEY"),
        result_type=Candidate,
        system_prompt=system_prompt,
    )
    # If input_data is a list of multiple resumes, use batch processing
    if isinstance(input_data, list) and len(input_data) > 1:
        results = await parser.parse_batch_async(input_data)
        type_data = "batch"
        for idx, result in enumerate(results):
            print(f"\n=== Testing Parser for Resume {idx + 1} in batch ===")
            print(f"Parsed Name: {result['candidate_name']}")
            print(
                f"Email: {result['email_addresses'][0] if result['email_addresses'] else 'Not found'}"
            )
            print("\nWork History:")
            for job in result["work_history"]:
                print(
                    f"- {job['job_title']} at {job['employer']} ({job['start_date']} to {job['end_date'] or 'Present'})"
                )
            print("\nEducation:")
            for edu in result["education"]:
                print(f"- {edu['level']} in {edu['subject']} from {edu['institution']}")
            print("\nSkills:")
            for skill in result["skills"]:
                print(f"- {skill['name']} ({skill['category']}, {skill['level']})")
            with open(f"./services/llm/parsed_resume_batch_{idx + 1}.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\nFull result saved to parsed_resume_batch_{idx + 1}.json")
    else:
        if isinstance(input_data, list):
            input_data = input_data[0]
        if isinstance(input_data, str) and input_data.endswith(".pdf"):
            type_data = "PDF"
        else:
            type_data = type(input_data)
        result = await parser.parse_async(input_data)
        print(f"\n=== Testing Parser with {type_data} ===")
        print(f"Parsed Name: {result['candidate_name']}")
        print(
            f"Email: {result['email_addresses'][0] if result['email_addresses'] else 'Not found'}"
        )
        print("\nWork History:")
        for job in result["work_history"]:
            print(
                f"- {job['job_title']} at {job['employer']} ({job['start_date']} to {job['end_date'] or 'Present'})"
            )
        print("\nEducation:")
        for edu in result["education"]:
            print(f"- {edu['level']} in {edu['subject']} from {edu['institution']}")
        print("\nSkills:")
        for skill in result["skills"]:
            print(f"- {skill['name']} ({skill['category']}, {skill['level']})")
        with open(f"./services/llm/parsed_resume_{type_data}.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nFull result saved to parsed_resume_{type_data}.json")


if __name__ == "__main__":
    pdf_path = "/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf"
    image_path = "/storage/hussein/matching/ai/app/services/llm/images.jpeg"

    async def run_tests():
        try:
            await test_parser(input_data=input_data_list)
            # with Image.open(image_path) as image:
            #     # Example: batch of resumes (text, pdf, image)
            #     input_batch = [SAMPLE_RESUME, pdf_path]  # Add image if needed: , image
            #     await test_parser(input_data=input_batch)
        except FileNotFoundError as e:
            print(f"Error: File not found - {e}")
        except Exception as e:
            print(f"Error occurred: {e}")

    asyncio.run(run_tests())
