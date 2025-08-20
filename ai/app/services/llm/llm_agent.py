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

from services.llm.agent_dir.agent import agent
import dotenv

dotenv.load_dotenv()


class LLM:
    def __init__(
        self,
        output_type: BaseModel,
        system_prompt: str,
        model_settings: dict = None,
        api_key: str = None,
        model: str = "gemini-2.0-flash",
    ):
        """
        Initialize the LLM with the specified AI model.

        Args:
            model: Name of the LLM model to use
            api_key: API key for the model provider (if not provided, will use environment variable)
            model_settings: Additional settings for the model
        """
        self.api_key = api_key or os.environ.get("API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided either in constructor or as API_KEY environment variable"
            )

        # Default model settings if none provided
        self.model_settings = model_settings or {"temperature": 0.2, "top_p": 0.95}

        self.output_type = output_type
        # Initialize the agent with Candidate as the result type
        self.llm_agent = agent(
            model=model,
            output_type=self.output_type,
            system_prompt=system_prompt,
            api_key=self.api_key,
            model_settings=self.model_settings,
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
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2)
                )  # 2x scaling for better resolution
                img_bytes = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_bytes))
                images.append(pil_image)

            doc.close()
            return images
        except Exception as e:
            print(f"Error rendering PDF pages as images: {e}")
            return []

    # def parse(self, input_data: list[Union[str, Image.Image, List[Any]]]) -> BaseModel:
    #     """
    #     Parse resume data synchronously from various input types.

    #     Args:
    #         input_data: Can be one of:
    #             - Path to a PDF file
    #             - Raw text string
    #             - PIL Image object
    #             - List containing text and/or images

    #     Returns:
    #         BaseModel: Parsed data as a Pydantic model
    #     """
    #     if not isinstance(input_data, list):
    #         input_data = [input_data]

    #     payload = []

    #     for item in input_data:
    #         # Handle different input types
    #         if isinstance(item, str):
    #             # Check if it's a path to a PDF file
    #             if item.lower().endswith('.pdf'):
    #                 # For PDFs, convert each page to an image
    #                 page_images = self._render_pdf_pages_as_images(item)
    #                 payload.extend(page_images)
    #             else:
    #                 # For raw text, send as is
    #                 payload.append(item)

    #         elif isinstance(item, Image.Image):
    #             # Single image input
    #             payload.append(item)

    #         elif isinstance(item, list):
    #             # List of mixed inputs
    #             payload.extend(item)

    #         else:
    #             continue
    #             # raise ValueError("Unsupported input type. Must be a string, PIL Image, or list.")

    #     if len(payload) == 0:
    #         raise ValueError("No valid input data provided.")

    #     # Process the payload synchronously
    #     try:
    #         result = self.llm_agent.run_sync(payload)
    #         return result
    #     except Exception as e:
    #         print(f"Error parsing resume: {e}")
    #         print(traceback.format_exc())
    #         raise

    async def parse_async(
        self, input_data: list[Union[str, Image.Image, List[Any]]]
    ) -> BaseModel:
        """
        Parse resume data asynchronously from various input types.

        Args:
            input_data: Can be one of:
                - Path to a PDF file
                - Raw text string
                - PIL Image object
                - List containing text and/or images

        Returns:
            BaseModel: Parsed data as a Pydantic model
        """
        if not isinstance(input_data, list):
            input_data = [input_data]

        payload = []
        MIN_TEXT_LENGTH_FOR_PDF = 100 # Heuristic: if extracted text is less than this, consider it poor.

        for item in input_data:
            if isinstance(item, str) and item.lower().endswith(".pdf"):
                pdf_text = self._extract_text_from_pdf(item)
                if pdf_text and len(pdf_text) >= MIN_TEXT_LENGTH_FOR_PDF:
                    print(f"Successfully extracted text from PDF: {item}, length: {len(pdf_text)}")
                    payload.append(pdf_text)
                else:
                    print(f"Falling back to image rendering for PDF: {item} (text length: {len(pdf_text or '')})")
                    page_images = self._render_pdf_pages_as_images(item)
                    if page_images: # Ensure fallback actually produced images
                        payload.extend(page_images)
                    else:
                        print(f"Warning: PDF image rendering also failed for {item}. Skipping this item.")
                        # Optionally, append a placeholder or raise an error if no content can be processed
            elif isinstance(item, str): # Regular text
                payload.append(item)
            elif isinstance(item, Image.Image): # Image
                payload.append(item)
            elif isinstance(item, list): # List of items (recursive call or nested structure not explicitly handled here, assuming flat list of basic types)
                # This case might need clarification if lists can contain PDFs/images themselves.
                # For now, assuming it's a list of text or pre-processed items.
                payload.extend(item)
            else:
                # Skip unsupported types or raise ValueError
                print(f"Unsupported item type: {type(item)}. Skipping.")
                continue

        if not payload: # Check if payload is empty after processing all inputs
            # raise ValueError("No valid input data provided or processed.")
            # Instead of raising an error, let the agent handle an empty payload if it can,
            # or return a default value (e.g. None or empty dict) if that's more appropriate.
            # For now, let's assume the agent might return an empty result or handle it.
            # If an error is preferred:
            print("Warning: No processable content found in input_data for parse_async.")
            # Depending on how llm_agent.run handles empty list, this might be fine or might need to return early.
            # To be safe, if strict parsing is required and empty payload is an error:
            # return self.output_type() # Return default empty model or handle as error
            # For now, let it pass to agent.run to see its behavior.

        # Process the payload asynchronously
        try:
            # Ensure payload is not empty before calling agent if agent can't handle empty list
            if not payload:
                 # Return default model instance or specific error response
                print("parse_async: No data to send to LLM agent after processing inputs.")
                # This should ideally return what the API expects for an empty/failed parse.
                # For instance, if output_type is a Pydantic model:
                try:
                    return self.output_type() # Return a default-initialized Pydantic model
                except Exception as model_init_e:
                    print(f"Error initializing default output_type: {model_init_e}")
                    return {} # Fallback to empty dict

            result = await self.llm_agent.run(payload)
            return result
        except Exception as e:
            print(f"Error parsing resume asynchronously: {e}")
            print(traceback.format_exc())
            raise

    async def parse_batch_async(self, list_of_inputs: list) -> list:
        """
        Parse a batch of resumes asynchronously. Each input is processed as a separate resume.
        Args:
            list_of_inputs: List of inputs (each can be a string, image, or PDF path for a single resume)
                            Each element in list_of_inputs corresponds to one resume.
        Returns:
            List of parsed results (one per input resume)
        """
        batch_payloads_for_agent = []
        MIN_TEXT_LENGTH_FOR_PDF = 100 # Heuristic

        for single_resume_input_data in list_of_inputs:
            current_resume_payload = []
            # Ensure single_resume_input_data is a list for uniform processing
            if not isinstance(single_resume_input_data, list):
                processed_input_data = [single_resume_input_data]
            else:
                processed_input_data = single_resume_input_data

            for item in processed_input_data:
                if isinstance(item, str) and item.lower().endswith(".pdf"):
                    pdf_text = self._extract_text_from_pdf(item)
                    if pdf_text and len(pdf_text) >= MIN_TEXT_LENGTH_FOR_PDF:
                        print(f"Batch: Successfully extracted text from PDF: {item}, length: {len(pdf_text)}")
                        current_resume_payload.append(pdf_text)
                    else:
                        print(f"Batch: Falling back to image rendering for PDF: {item} (text length: {len(pdf_text or '')})")
                        page_images = self._render_pdf_pages_as_images(item)
                        if page_images:
                            current_resume_payload.extend(page_images)
                        else:
                             print(f"Batch: Warning: PDF image rendering also failed for {item}. This resume part might be empty.")
                elif isinstance(item, str): # Regular text
                    current_resume_payload.append(item)
                elif isinstance(item, Image.Image): # Image
                    current_resume_payload.append(item)
                # Note: Assuming 'list' type items within single_resume_input_data are pre-flattened or simple text lists.
                # If a list item itself could be a path to a PDF, the logic might need more nesting.
                # For now, this handles a flat list of components for one resume.
                elif isinstance(item, list):
                    current_resume_payload.extend(item)
                else:
                    print(f"Batch: Unsupported item type: {type(item)} in resume data. Skipping.")

            # Add the processed payload for this resume and its expected output_type to the batch
            # If current_resume_payload is empty, the agent will receive an empty list for this item.
            # The agent's batch method should handle empty payloads for individual items gracefully.
            if not current_resume_payload:
                print(f"Batch: Warning: No processable content for one of the resume inputs. Sending empty payload for this item.")
            batch_payloads_for_agent.append((current_resume_payload, self.output_type))

        if not batch_payloads_for_agent:
            print("Warning: No valid inputs to process in batch.")
            return []

        results = await self.llm_agent.batch(batch_payloads_for_agent)
        return results
