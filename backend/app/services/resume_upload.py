import os
import requests
import json
from pathlib import Path
from pydantic import BaseModel
from enum import Enum
from typing import List, Any, Dict, Optional
import time
import logging
from core.config import settings
logger = logging.getLogger(__name__)


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
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    return content_types.get(file_extension)


# Helper Pydantic model for batch items, not strictly necessary for AgentClient but good for structure
class BatchParseItemData(BaseModel):
    candidate_id: int  # To map results back
    resume_texts: Optional[List[str]] = None
    resume_files: Optional[
        List[str]
    ] = []  # List of filenames (basenames) associated with this candidate
    schema_definition: str
    system_prompt: Optional[str] = None


def _get_ai_service_url(ai_url_env: Optional[str] = None) -> str:
    if settings.AI_URL:
        return settings.AI_URL

    hosts = ["ai", "localhost"]
    port = settings.AI_PORT
    retries = 3
    for host in hosts:
        i = 0
        while i < retries:
            i += 1
            base_url = f"http://{host}:{port}"
            health_url = f"{base_url}/health"
            try:
                logger.info(f"Trying to connect to discovered AI URL: {health_url}")
                response = requests.get(health_url, timeout=5)
                response.raise_for_status()
                logger.info(f"✅ AI service is running at {base_url}")
                return base_url
            except requests.exceptions.RequestException as e:
                time.sleep(2)
                logger.error(f"❌ Could not connect to {health_url}: {e}")

    logger.error("❌ AI service is not running or not accessible.")
    return ""


AI_BASE_URL = _get_ai_service_url()


class AgentClient:
    def __init__(self):
        """
        Initializes the AgentClient.
        The base URL for the AI service is determined once when the module is loaded.
        """
        self.base_url = AI_BASE_URL

    def parse(self, system_prompt: str, schema: Any, inputs: List[Any]):
        """
        Parses a single resume item (can be text or file path, or list of these for one resume)
        by calling the AI service's /parser/parse endpoint.

        :param system_prompt: The system prompt string for the LLM.
        :param schema: The Pydantic model or JSON schema dict/string for the expected output.
        :param inputs: List of text strings or file paths for a single resume.
        """
        if self.base_url is None:
            logger.error("❌ AI service is not available - cannot parse resume")
            return None

        parser_url = f"{self.base_url}/parser/parse"

        if isinstance(schema, BaseModel):
            schema_str = json.dumps(schema.model_json_schema())
        elif isinstance(schema, dict):
            schema_str = json.dumps(schema)
        elif isinstance(schema, str):
            schema_str = schema
        else:
            raise ValueError("Schema must be a Pydantic model, dict, or JSON string.")

        form_data = {"schema": schema_str, "system_prompt": system_prompt}
        files_data = []
        opened_files = []
        for input_item in inputs:
            if isinstance(input_item, str) and (
                input_item.startswith("/") or "\\" in input_item
            ):
                file_path = Path(input_item)
                if not file_path.exists():
                    logger.warning(f"⚠️  File not found: {input_item}")
                    continue
                content_type = get_content_type(file_path.suffix.lower())
                if not content_type:
                    logger.warning(f"⚠️  Unsupported file type: {input_item}")
                    continue
                try:
                    file_obj = open(file_path, "rb")
                    opened_files.append(file_obj)
                    files_data.append(
                        ("inputs", (file_path.name, file_obj, content_type))
                    )
                    logger.info(f"✅ Added file: {file_path.name}")
                except Exception as e:
                    logger.error(f"❌ Error opening file {input_item}: {e}")
            else:
                files_data.append(("inputs", (None, input_item, "text/plain")))
                logger.info(f"✅ Added text input: {str(input_item)[:50]}...")
        if not files_data:
            logger.warning("❌ No valid inputs to process for single parse.")
            return None
        try:
            logger.info(
                f"\n🚀 Sending single parse request with {len(files_data)} inputs to {parser_url}..."
            )
            response = requests.post(parser_url, data=form_data, files=files_data)
            logger.info(f"Single Parse Status Code: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Single Parse Error: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Single Parse Request failed: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"❌ Single Parse Invalid JSON response: {response.text}")
            return None
        finally:
            for file_obj in opened_files:
                file_obj.close()

    def parse_batch(
        self, batch_metadata_payload: List[Dict[str, Any]], all_file_paths: List[str]
    ):
        """
        Parses a batch of resumes by calling the AI service's /parser/batch_parse endpoint.

        :param batch_metadata_payload: A list of dictionaries. Each dictionary is an item for
                                       the 'batch_metadata' form field. It should conform to what
                                       the AI's /batch_parse endpoint expects for each item,
                                       e.g., {"resume_texts": [], "resume_files": ["filename.pdf"],
                                              "schema": "...", "system_prompt": "..."}.
                                       The "resume_files" should contain basenames of files.
        :param all_file_paths: A list of absolute paths to all unique resume files that need to be uploaded.
                               The basenames of these paths should correspond to what's listed in
                               `resume_files` within `batch_metadata_payload` items.
        """
        if self.base_url is None:
            logger.error("❌ AI service is not available - cannot parse resume batch")
            return None

        batch_parser_url = f"{self.base_url}/parser/batch_parse"

        form_data = {"batch_metadata": json.dumps(batch_metadata_payload)}

        files_data = []
        opened_files = []

        # Deduplicate file paths to avoid opening/sending the same file multiple times
        # if it's referenced by multiple items in the batch, though AI endpoint expects flat list of unique files.
        # For simplicity here, we assume all_file_paths contains unique paths if needed,
        # or that the calling script manages this. The AI endpoint expects all files listed in batch_metadata
        # to be present in the 'resume_files' part of the form.

        unique_file_paths = sorted(list(set(all_file_paths)))

        for file_path_str in unique_file_paths:
            file_path_obj = Path(file_path_str)
            if not file_path_obj.exists():
                logger.warning(f"⚠️  File not found for batch: {file_path_str}")
                continue  # Or raise error, depending on desired strictness

            content_type = get_content_type(file_path_obj.suffix.lower())
            if not content_type:
                logger.warning(f"⚠️  Unsupported file type for batch: {file_path_str}")
                continue

            try:
                file_obj = open(file_path_obj, "rb")
                opened_files.append(file_obj)
                # The AI /batch_parse endpoint expects files under 'resume_files' key
                files_data.append(
                    ("resume_files", (file_path_obj.name, file_obj, content_type))
                )
                logger.info(f"✅ Added file for batch: {file_path_obj.name}")
            except Exception as e:
                logger.error(f"❌ Error opening file {file_path_str} for batch: {e}")

        if not batch_metadata_payload:
            logger.warning("❌ No batch metadata to process.")
            # Close any opened files if we're returning early
            for file_obj in opened_files:
                file_obj.close()
            return None

        # It's possible to have metadata but no files if all inputs are text-based
        # if not files_data and any(item.get("resume_files") for item in batch_metadata_payload):
        #     print("❌ Some batch items reference files, but no valid files could be prepared for upload.")
        #     for file_obj in opened_files:
        #         file_obj.close()
        #     return None

        try:
            logger.info(
                f"\n🚀 Sending batch parse request with {len(batch_metadata_payload)} items and {len(files_data)} files to {batch_parser_url}..."
            )
            response = requests.post(batch_parser_url, data=form_data, files=files_data)
            logger.info(f"Batch Parse Status Code: {response.status_code}")
            if response.status_code == 200:
                return response.json()  # Expected to be a list of results
            else:
                logger.error(f"❌ Batch Parse Error: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Batch Parse Request failed: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"❌ Batch Parse Invalid JSON response: {response.text}")
            return None
        finally:
            for file_obj in opened_files:
                file_obj.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing AgentClient...")
    if not True:
        logger.info("AI_BASE_URL not determined. Cannot run tests.")
    else:
        client = AgentClient()  # Initialize without specific task details

        # --- Test single parse (legacy behavior) ---
        logger.info("\n--- Testing single parse ---")
        single_system_prompt = "Extract structured information for a single resume."
        # Assuming Candidate schema is defined elsewhere or use a generic dict
        # from models.candidate_pydantic import CandidateResume # Example
        # single_schema = CandidateResume.model_json_schema()
        single_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
        }

        # Create dummy files for testing if they don't exist
        Path("dummy_resume.pdf").write_text("This is a dummy PDF content.")
        Path("dummy_image.jpeg").write_text("This is dummy image content.")

        single_inputs = [
            "John Doe\njohn.doe@email.com\nSkills: Test, Debug",
            "dummy_resume.pdf",
        ]
        try:
            single_result = client.parse(
                single_system_prompt, single_schema, single_inputs
            )
            if single_result:
                logger.info(
                    "✅ Single parse successful:", json.dumps(single_result, indent=2)
                )
            else:
                logger.info("❌ Single parse failed or returned None.")
        except Exception as e:
            logger.error(f"Error during single parse test: {e}")

        # --- Test batch parse ---
        logger.info("\n--- Testing batch parse ---")
        batch_meta_items = [
            {
                "candidate_id": 1,  # Custom field to help map results back
                "resume_texts": ["Text for resume 1: Jane Doe, jane@example.com"],
                "resume_files": ["dummy_resume.pdf"],  # Basename
                "schema": json.dumps(single_schema),  # Reusing schema for simplicity
                "system_prompt": "Parse Jane's resume.",
            },
            {
                "candidate_id": 2,
                "resume_texts": ["Text for resume 2: Peter Pan, peter@neverland.com"],
                "resume_files": ["dummy_image.jpeg"],  # Basename
                "schema": json.dumps(single_schema),
                "system_prompt": "Parse Peter's resume.",
            },
            {
                "candidate_id": 3,  # Text-only item
                "resume_texts": [
                    "Text for resume 3: Alice Wonderland, alice@rabbit_hole.com"
                ],
                "resume_files": [],
                "schema": json.dumps(single_schema),
                "system_prompt": "Parse Alice's resume.",
            },
        ]
        all_files_for_batch = [
            "dummy_resume.pdf",
            "dummy_image.jpeg",
        ]  # List of actual paths

        try:
            batch_results = client.parse_batch(batch_meta_items, all_files_for_batch)
            if batch_results:
                logger.info(
                    "✅ Batch parse successful:", json.dumps(batch_results, indent=2)
                )
                # Example: Map results back if candidate_id was part of the response or by order
                for i, result in enumerate(batch_results):
                    original_request = batch_meta_items[i]
                    logger.info(
                        f"Result for candidate_id {original_request.get('candidate_id')}: {result}"
                    )
            else:
                logger.info("❌ Batch parse failed or returned None.")
        except Exception as e:
            logger.error(f"Error during batch parse test: {e}")

        # Clean up dummy files
        Path("dummy_resume.pdf").unlink(missing_ok=True)
        Path("dummy_image.jpeg").unlink(missing_ok=True)

    # else:
