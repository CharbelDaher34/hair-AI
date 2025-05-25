import requests
import json
from pathlib import Path


from pydantic import BaseModel
import json
from enum import Enum

class Skills(BaseModel):
    name: str
    level: str

class Gender(str,Enum):
    MALE = "Male"
    FEMALE = "Female"

class Candidate(BaseModel):
    name: str
    email: str
    gender: Gender
    skills: list[Skills]

class Candidates(BaseModel):
    candidates: list[Candidate]

def test_parse_resume():
    """Test parse resume endpoint with mixed text and file inputs"""
    url = "http://localhost:8011/parser/parse"
    
    # Resume schema
    resume_schema = json.dumps(Candidates.model_json_schema())
    
    form_data = {
        'schema': resume_schema,
        'system_prompt': "Extract structured information from resumes. Focus on contact details, skills, and work experience."
    }
    
    # Define your inputs in order - mix of text and file paths
    inputs = [
        "John Doe\njohn.doe@email.com\n(555) 123-4567\nSkills: Python, FastAPI, Machine Learning",
        "/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf",  # Update with your PDF path
        "Jane Smith\njane.smith@company.com\n(555) 987-6543\nSkills: React, Node.js, TypeScript",
        "/storage/hussein/matching/ai/app/services/llm/images.jpeg",  # Update with your image path
        "Alice Johnson\nalice@example.com\nExpertise: Java, Spring Boot, AWS"
    ]
    
    files_data = []
    opened_files = []
    
    for input_item in inputs:
        if input_item.startswith('/') or '\\' in input_item:  # File path
            file_path = Path(input_item)
            
            if not file_path.exists():
                print(f"⚠️  File not found: {input_item}")
                continue
                
            content_type = get_content_type(file_path.suffix.lower())
            if not content_type:
                print(f"⚠️  Unsupported file type: {input_item}")
                continue
                
            try:
                file_obj = open(file_path, 'rb')
                opened_files.append(file_obj)
                files_data.append(('inputs', (file_path.name, file_obj, content_type)))
                print(f"✅ Added file: {file_path.name}")
            except Exception as e:
                print(f"❌ Error opening file {input_item}: {e}")
        else:  # Text input
            files_data.append(('inputs', (None, input_item, 'text/plain')))
            print(f"✅ Added text input: {input_item[:50]}...")
    
    if not files_data:
        print("❌ No valid inputs to process")
        return
    
    try:
        print(f"\n🚀 Sending request with {len(files_data)} inputs...")
        response = requests.post(url, data=form_data, files=files_data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Parsed data:")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {response.text}")
    finally:
        for file_obj in opened_files:
            file_obj.close()

def get_content_type(file_extension):
    """Get content type based on file extension"""
    content_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff'
    }
    return content_types.get(file_extension)

if __name__ == "__main__":
    print("Testing Parse Resume Endpoint")
    print("=" * 40)
    test_parse_resume()