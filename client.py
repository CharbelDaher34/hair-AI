import requests
import json
from pathlib import Path
from pydantic import BaseModel
from enum import Enum
from typing import List, Any

# --- Define schema models (or import if available) ---
class Skills(BaseModel):
    name: str
    level: str

class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"

class Candidate(BaseModel):
    name: str
    email: str
    gender: Gender
    skills: list[Skills]

class Candidates(BaseModel):
    candidates: list[Candidate]


def get_content_type(file_extension):
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

class ResumeParserClient:
    def __init__(self, system_prompt: str, schema: Any, inputs: List[Any], url: str = "http://localhost:8011/parser/parse"):
        """
        :param system_prompt: The system prompt string for the LLM
        :param schema: The Pydantic model or JSON schema dict/string
        :param inputs: List of text strings or file paths
        :param url: Endpoint URL
        """
        self.system_prompt = system_prompt
        # Accept either a Pydantic model, dict, or JSON string for schema
        if isinstance(schema, BaseModel):
            self.schema = json.dumps(schema.model_json_schema())
        elif isinstance(schema, dict):
            self.schema = json.dumps(schema)
        elif isinstance(schema, str):
            self.schema = schema
        else:
            raise ValueError("Schema must be a Pydantic model, dict, or JSON string.")
        self.inputs = inputs
        self.url = url

    def parse(self):
        form_data = {
            'schema': self.schema,
            'system_prompt': self.system_prompt
        }
        files_data = []
        opened_files = []
        for input_item in self.inputs:
            if isinstance(input_item, str) and (input_item.startswith('/') or '\\' in input_item):
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
            else:
                files_data.append(('inputs', (None, input_item, 'text/plain')))
                print(f"✅ Added text input: {str(input_item)[:50]}...")
        if not files_data:
            print("❌ No valid inputs to process")
            return None
        try:
            print(f"\n🚀 Sending request with {len(files_data)} inputs...")
            response = requests.post(self.url, data=form_data, files=files_data)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("✅ Success! Parsed data:")
                # print(json.dumps(result, indent=2))
                return result
            else:
                print(f"❌ Error: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            return None
        finally:
            for file_obj in opened_files:
                file_obj.close()

if __name__ == "__main__":
    print("Testing ResumeParserClient")
    print("=" * 40)
    # Example usage
    system_prompt = "Extract structured information from resumes. Focus on contact details, skills, and work experience."
    schema = Candidates
    inputs = [
        # "Charbel daher/ charbeldaher34@gmail.com: Skills: Python, FastAPI, Machine Learning\n\n"
        # "John Doe\njohn.doe@email.com\n(555) 123-4567",
        "/storage/hussein/matching/ai/app/services/llm/Charbel_Daher_Resume.pdf",
        # "Jane Smith\njane.smith@company.com\n(555) 987-6543\nSkills: React, Node.js, TypeScript",
        "/storage/hussein/matching/ai/app/services/llm/images.jpeg",
        # "Alice Johnson\nalice@example.com\nExpertise: Java, Spring Boot, AWS"
    ]
    client = ResumeParserClient(system_prompt, schema.model_json_schema(), inputs)
    client.parse()
