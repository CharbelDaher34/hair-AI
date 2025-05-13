import os
import sys
from pathlib import Path
from typing import Union, List, Any, Optional
import io
import traceback

from pydantic import BaseModel
from PIL import Image
# import fitz  # PyMuPDF for PDF handling
import pymupdf as fitz
import asyncio

# Add parent directory to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from parser.entities_models.candidate_pydantic import Candidate
from parser.agent_dir.agent import agent

class ResumeParser:
    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
        model_settings: Optional[dict] = None
    ):
        """
        Initialize the resume parser with the specified AI model.
        
        Args:
            model: Name of the LLM model to use
            api_key: API key for the model provider (if not provided, will use environment variable)
            model_settings: Additional settings for the model
        """
        self.api_key = api_key or os.environ.get("API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided either in constructor or as API_KEY environment variable")
        
        # Default model settings if none provided
        self.model_settings = model_settings or {
            "temperature": 0.2,
            "top_p": 0.95
        }
        
        # Initialize the agent with Candidate as the result type
        self.parser_agent = agent(
            model=model,
            result_type=Candidate,
            system_prompt="""
            You are a skilled resume parser. Extract all relevant information from the provided resume 
            and structure it according to the Candidate schema. Follow these guidelines:
            
            1. Extract contact information: name, email, phone, address
            2. Extract work history with dates, job titles, employers, and responsibilities
            3. Extract education history with degree types, institutions, and dates
            4. Extract skills and categorize them appropriately
            5. Extract certifications with issuing organizations and dates
            
            Be precise with dates and leave fields empty if information is not available.
            For ambiguous information, make reasonable inferences but do not fabricate data.
            Format all dates as YYYY-MM-DD and ensure data types match the schema requirements.
            """,
            api_key=self.api_key,
            model_settings=self.model_settings
        )
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file."""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def _extract_images_from_pdf(self, pdf_path: str) -> List[Image.Image]:
        """Extract images from a PDF file."""
        images = []
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    images.append(pil_image)
            
            doc.close()
            return images
        except Exception as e:
            print(f"Error extracting images from PDF: {e}")
            return []
    
    def _render_pdf_pages_as_images(self, pdf_path: str) -> List[Image.Image]:
        """Render each page of the PDF as an image."""
        images = []
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scaling for better resolution
                img_bytes = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_bytes))
                images.append(pil_image)
            
            doc.close()
            return images
        except Exception as e:
            print(f"Error rendering PDF pages as images: {e}")
            return []
    
    def parse(self, input_data: Union[str, Image.Image, List[Any]]) -> Candidate:
        """
        Parse resume data synchronously from various input types.
        
        Args:
            input_data: Can be one of:
                - Path to a PDF file
                - Raw text string
                - PIL Image object
                - List containing text and/or images
                
        Returns:
            Candidate: Parsed candidate data as a Pydantic model
        """
        payload = []
        
        # Handle different input types
        if isinstance(input_data, str):
            # Check if it's a path to a PDF file
            if input_data.lower().endswith('.pdf'):
                # For PDFs, convert each page to an image
                page_images = self._render_pdf_pages_as_images(input_data)
                payload.extend(page_images)
            else:
                # For raw text, send as is
                payload.append(input_data)
        
        elif isinstance(input_data, Image.Image):
            # Single image input
            payload.append(input_data)
        
        elif isinstance(input_data, list):
            # List of mixed inputs
            payload = input_data
        
        else:
            raise ValueError("Unsupported input type. Must be a string, PIL Image, or list.")
        
        # Process the payload synchronously
        try:
            result = self.parser_agent.run_sync(payload)
            return result
        except Exception as e:
            print(f"Error parsing resume: {e}")
            print(traceback.format_exc())
            raise
    
    async def parse_async(self, input_data: Union[str, Image.Image, List[Any]]) -> Candidate:
        """
        Parse resume data asynchronously from various input types.
        
        Args:
            input_data: Can be one of:
                - Path to a PDF file
                - Raw text string
                - PIL Image object
                - List containing text and/or images
                
        Returns:
            Candidate: Parsed candidate data as a Pydantic model
        """
        payload = []
        
        # Handle different input types (same as sync version)
        if isinstance(input_data, str):
            if input_data.lower().endswith('.pdf'):
                # For PDFs, convert each page to an image
                page_images = self._render_pdf_pages_as_images(input_data)
                payload.extend(page_images)
            else:
                # For raw text, send as is
                payload.append(input_data)
        
        elif isinstance(input_data, Image.Image):
            payload.append(input_data)
        
        elif isinstance(input_data, list):
            payload = input_data
        
        else:
            raise ValueError("Unsupported input type. Must be a string, PIL Image, or list.")
        
        # Process the payload asynchronously
        try:
            result = await self.parser_agent.run(payload)
            return result
        except Exception as e:
            print(f"Error parsing resume asynchronously: {e}")
            print(traceback.format_exc())
            raise

# Usage example
if __name__ == "__main__":
    parser = ResumeParser(api_key=os.environ.get("API_KEY"))
    
    # Example with a PDF file
    # result = parser.parse("path/to/resume.pdf")
    
    # Example with text
    sample_resume = """
    John Doe
    Software Engineer
    john.doe@example.com | (555) 123-4567 | San Francisco, CA
    
    WORK EXPERIENCE
    Senior Software Engineer | ABC Tech | 2020-01 to Present
    - Led development of microservices architecture
    - Implemented CI/CD pipeline reducing deployment time by 40%
    
    Software Developer | XYZ Corp | 2017-06 to 2019-12
    - Developed RESTful APIs for customer-facing applications
    - Optimized database queries improving performance by 30%
    
    EDUCATION
    Master of Science in Computer Science | Stanford University | 2015-09 to 2017-05
    Bachelor of Science in Software Engineering | MIT | 2011-09 to 2015-05
    
    SKILLS
    Python, JavaScript, AWS, Docker, Kubernetes, SQL, React, TypeScript
    
    CERTIFICATIONS
    AWS Certified Solutions Architect | Amazon Web Services | 2019-07
    """
    
    # Parse the sample resume
    result = parser.parse(sample_resume)
    print(result)
