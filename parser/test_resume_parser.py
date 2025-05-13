import os
import sys
import json
import asyncio
from pathlib import Path
from PIL import Image

# Add parent directory to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from parser.resume_parser import ResumeParser
import dotenv

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

async def test_parser(input_data=SAMPLE_RESUME):
    """Test the parsing functionality."""
    parser = ResumeParser(api_key=os.environ.get("API_KEY"))
    
    type_data=type(input_data)
    if type_data==str and input_data.endswith(".pdf"):
        type_data="PDF"
   
    print(f"\n=== Testing Parser with {type_data} ===")
    result = await parser.parse_async(input_data)
    
    # Print basic information
    print(f"Parsed Name: {result['candidate_name']}")
    print(f"Email: {result['email_addresses'][0] if result['email_addresses'] else 'Not found'}")
    
    # Print work history summary
    print("\nWork History:")
    for job in result['work_history']:
        print(f"- {job['job_title']} at {job['employer']} ({job['start_date']} to {job['end_date'] or 'Present'})")
    
    # Print education summary
    print("\nEducation:")
    for edu in result['education']:
        print(f"- {edu['level']} in {edu['subject']} from {edu['institution']}")
    
    # Print skills summary
    print("\nSkills:")
    for skill in result['skills']:
        print(f"- {skill['name']} ({skill['category']}, {skill['level']})")
    
    # Optional: Save full result to JSON file
    with open(f"./parser/parsed_resume_{type_data}.json", "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nFull result saved to parsed_resume_{type_data}.json")
 
if __name__ == "__main__":
    pdf_path = "/storage/hussein/matching/parser/Charbel_Daher_Resume.pdf"
    image_path = "parser/images.jpeg"
    
    async def run_tests():
        try:
            # Open and process image
            with Image.open(image_path) as image:
                # Run tests concurrently
                await asyncio.gather(
                    test_parser(input_data=image),
                    test_parser(input_data=pdf_path),
                    test_parser(input_data=SAMPLE_RESUME)  # Also test with sample text
                )
                
        except FileNotFoundError as e:
            print(f"Error: File not found - {e}")
        except Exception as e:
            print(f"Error occurred: {e}")
    
    # Run the async function
    asyncio.run(run_tests())
    