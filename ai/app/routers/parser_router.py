from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from pydantic import BaseModel
from services.llm.llm_agent import LLM
from services.llm.entities_models.candidate_pydantic import Candidate
from utils import create_model_from_schema
import os
import json
from typing import List, Optional, Any, Dict, Union
import aiofiles
import tempfile
import shutil

router = APIRouter()

# This model is for the items in the JSON payload of the /batch_parse endpoint
class BatchParseItem(BaseModel):
    resume_texts: Optional[List[str]] = None
    resume_files: Optional[Any] = None  # Client sends null/None for this in tests.
                                        # Actual file content would need different handling (e.g., base64).
    schema_str: str # Expects a JSON string for the schema
    system_prompt: Optional[str] = None

    class Config:
        # If client sends "schema" and "system_prompt" as keys in JSON:
        # This allows Pydantic to map "schema_str" to JSON key "schema" if needed,
        # but let's assume client sends "schema_str" and "system_prompt" or we adjust client.
        # For now, let's assume the client will send keys matching these field names,
        # or the test client needs to be updated. The test sends "schema" and "system_prompt".
        # So, let's rename fields to match the test client.
        pass

# Re-defining BatchParseItem to match keys used in test_parser_endpoint.py for batch_payload
class CleanBatchParseItem(BaseModel):
    resume_texts: Optional[List[str]] = None
    resume_files: Optional[Any] = None 
    schema: str  # This will be the JSON string for the schema, matching "schema" key in client
    system_prompt: Optional[str] = None # Matches "system_prompt" key in client


# Helper function to process uploaded files asynchronously
async def process_uploaded_files(resume_files: List[UploadFile]) -> tuple[List[str], str]:
    temp_dir = tempfile.mkdtemp()
    processed_file_paths = []
    for file in resume_files:
        safe_filename = os.path.basename(file.filename) 
        temp_file_path = os.path.join(temp_dir, safe_filename)
        
        try:
            async with aiofiles.open(temp_file_path, "wb") as f:
                content = await file.read() 
                await f.write(content)
            processed_file_paths.append(temp_file_path)
        except Exception as e:
            shutil.rmtree(temp_dir)
            raise HTTPException(status_code=500, detail=f"Error processing file {file.filename}: {e}")

    return processed_file_paths, temp_dir

# @router.post("/parse")
# async def parse_resume(
#     resume_texts: Optional[List[str]] = Form(default=None),
#     resume_files: Optional[List[UploadFile]] = File(default=None),
#     schema: str = Form(...), # Schema is a required form field (JSON string)
#     system_prompt: Optional[str] = Form(default=None) # System prompt is an optional form field
# ):
#     """
#     Parse resumes from text, PDF, or image files and return structured candidate data.
#     """
#     if not resume_texts and not resume_files:
#         raise HTTPException(status_code=400, detail="Either resume_texts or resume_files must be provided.")
    
#     api_key = os.environ.get("API_KEY")
#     if not api_key:
#         raise HTTPException(status_code=500, detail="API_KEY not configured.")

#     # 'schema' is already a string from Form(...)
#     try:
#         schema_dict = json.loads(schema)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Schema is not valid JSON: {e}")
    
#     schema_model = create_model_from_schema(schema_dict, globals_dict=globals())
#     if not issubclass(schema_model, BaseModel): # create_model_from_schema should ideally raise or return None on failure
#         raise HTTPException(status_code=400, detail="Schema must be a valid Pydantic model.")
#     print(f"Schema model created: {schema_model.__name__}")
#     print(f"Schema model JSON schema: {schema_model.model_json_schema()}")
#     llm_parser = LLM(
#         api_key=api_key,
#         system_prompt=system_prompt, # Use the system_prompt parameter
#         result_type=schema_model,
#     )

#     input_data = []
#     if resume_texts:
#         input_data.extend(resume_texts)

#     temp_dir_to_clean = None
#     try:
#         if resume_files:
#             # Pass resume_files (List[UploadFile]) directly to process_uploaded_files
#             processed_file_paths, temp_dir_to_clean = await process_uploaded_files(resume_files)
#             input_data.extend(processed_file_paths)
        
#         if not input_data: 
#              raise HTTPException(status_code=400, detail="No data to parse.")

#         result = await llm_parser.parse_async(input_data)
#         return result
#     finally:
#         if temp_dir_to_clean and os.path.exists(temp_dir_to_clean):
#             shutil.rmtree(temp_dir_to_clean)

@router.post("/parse")
async def parse_resume(
    inputs: List[Union[str, UploadFile]] = Form(...),
    schema: str = Form(...),
    system_prompt: Optional[str] = Form(default=None)
):
    """
    Parse resumes from ordered list of text strings or files (PDF/images) and return structured candidate data.
    """
    if not inputs:
        raise HTTPException(status_code=400, detail="inputs must be provided.")
    
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API_KEY not configured.")

    try:
        schema_dict = json.loads(schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Schema is not valid JSON: {e}")
    
    schema_model = create_model_from_schema(schema_dict, globals_dict=globals())
    if not issubclass(schema_model, BaseModel):
        raise HTTPException(status_code=400, detail="Schema must be a valid Pydantic model.")
    
    
    
    llm_parser = LLM(
        api_key=api_key,
        system_prompt=system_prompt,
        result_type=schema_model,
    )

    processed_inputs = []
    files_to_process = []
    temp_dir_to_clean = None
    
    try:
        for input_item in inputs:
            if isinstance(input_item, str):
                processed_inputs.append(input_item)
            elif isinstance(input_item, UploadFile):
                files_to_process.append(input_item)
                processed_inputs.append(None)  # Placeholder to maintain order
        
        if files_to_process:
            processed_file_paths, temp_dir_to_clean = await process_uploaded_files(files_to_process)
            
            # Replace placeholders with actual file paths in order
            file_index = 0
            for i, item in enumerate(processed_inputs):
                if item is None:
                    processed_inputs[i] = processed_file_paths[file_index]
                    file_index += 1
        
        result = await llm_parser.parse_async(processed_inputs)
        return result
    finally:
        if temp_dir_to_clean and os.path.exists(temp_dir_to_clean):
            shutil.rmtree(temp_dir_to_clean)


@router.post("/batch_parse")
async def batch_parse_resume(
    batch_metadata: str = Form(...),
    resume_files: Optional[List[UploadFile]] = File(None)
):
    """
    Parse a batch of resumes, supporting both text and file uploads per batch item.
    batch_metadata: JSON string describing each batch item, including which files belong to which item (by filename).
    resume_files: All files for all batch items, flat list.
    """
    try:
        batch_requests = json.loads(batch_metadata)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"batch_metadata is not valid JSON: {e}")

    if not batch_requests:
        raise HTTPException(status_code=400, detail="No requests provided for batch parsing.")

    first_request = batch_requests[0]

    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API_KEY not configured.")

    if not first_request.get("schema"):
        raise HTTPException(status_code=400, detail="Schema must be provided in the first request for batch processing.")
    
    try:
        schema_dict = json.loads(first_request["schema"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Schema in the first request is not valid JSON: {e}")
    
    schema_model = create_model_from_schema(schema_dict, globals_dict=globals())
    if not issubclass(schema_model, BaseModel):
        raise HTTPException(
            status_code=400,
            detail="Schema in the first request must define a valid Pydantic model."
        )
    print(f"Batch processing with schema model: {schema_model.__name__} and system prompt: '{first_request.get('system_prompt')}'")
    print(json.dumps(schema_model.model_json_schema(), indent=2))
    llm_parser = LLM(
        api_key=api_key,
        system_prompt=first_request.get("system_prompt"),
        result_type=schema_model,
    )

    # Map filename to UploadFile for quick lookup
    file_map: Dict[str, UploadFile] = {}
    if resume_files:
        for f in resume_files:
            file_map[f.filename] = f

    payloads_for_llm_markers = []
    temp_dirs_to_clean = []

    try:
        for req_idx, request_item in enumerate(batch_requests):
            current_input_data = []
            # Texts
            if request_item.get("resume_texts"):
                current_input_data.extend(request_item["resume_texts"])
            # Files
            item_file_names = request_item.get("resume_files") or []
            item_files = [file_map[name] for name in item_file_names if name in file_map]
            if item_files:
                processed_file_paths, temp_dir = await process_uploaded_files(item_files)
                current_input_data.extend(processed_file_paths)
                if temp_dir:
                    temp_dirs_to_clean.append(temp_dir)
            if not current_input_data:
                print(f"Info: Request at index {req_idx} in batch has no input data. A None will be placed in the results for this item.")
                payloads_for_llm_markers.append(None)
            else:
                payloads_for_llm_markers.append(current_input_data)

        actual_llm_payloads = [p for p in payloads_for_llm_markers if p is not None]
        processed_llm_results_iter = iter([])
        if actual_llm_payloads:
            raw_results_from_llm = await llm_parser.parse_batch_async(actual_llm_payloads)
            processed_llm_results_iter = iter(raw_results_from_llm)
        final_results = []
        for marker in payloads_for_llm_markers:
            if marker is None:
                final_results.append(None)
            else:
                try:
                    final_results.append(next(processed_llm_results_iter))
                except StopIteration:
                    print(f"ERROR: LLM result iteration exhausted prematurely. Appending None as fallback.")
                    final_results.append(None)
        return final_results
    finally:
        for temp_dir in temp_dirs_to_clean:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

# Example usage comment block can remain as is or be removed if not current.
# from services.llm.entities_models.candidate_pydantic import Candidate
# @router.post("/parse_candidate_json_schema")
# async def parse_candidate_json_schema(
#     resume_texts: Optional[List[str]] = Form(None),
#     resume_files: Optional[List[UploadFile]] = File(None),
#     system_prompt: str = Form(None),
# ):
#     candidate_schema = json.dumps(Candidate.model_json_schema())
#     return await parse_resume(
#         resume_texts=resume_texts,
#         resume_files=resume_files,
#         schema=candidate_schema,
#         system_prompt=system_prompt,
#     )
