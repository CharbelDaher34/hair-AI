import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from core.config import RESUME_STORAGE_DIR
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def ensure_resume_directory() -> None:
    """Ensure the resume storage directory exists."""
    os.makedirs(RESUME_STORAGE_DIR, exist_ok=True)


def save_resume_file(temp_file_path: str, candidate_id: int) -> str:
    """
    Save a resume file permanently with candidate ID as filename.

    Args:
        temp_file_path: Path to the temporary file
        candidate_id: ID of the candidate

    Returns:
        Path to the saved resume file

    Raises:
        Exception: If file saving fails
    """
    ensure_resume_directory()

    permanent_resume_path = os.path.join(RESUME_STORAGE_DIR, f"{candidate_id}.pdf")
    shutil.copy2(temp_file_path, permanent_resume_path)

    return permanent_resume_path


def get_resume_file_path(candidate_id: int) -> Optional[str]:
    """
    Get the path to a candidate's resume file.

    Args:
        candidate_id: ID of the candidate

    Returns:
        Path to the resume file if it exists, None otherwise
    """
    resume_path = os.path.join(RESUME_STORAGE_DIR, f"{candidate_id}.pdf")
    print(f"[File Utils] Resume path: {resume_path}")
    return resume_path if os.path.exists(resume_path) else None


def delete_resume_file(candidate_id: int) -> bool:
    """
    Delete a candidate's resume file.

    Args:
        candidate_id: ID of the candidate

    Returns:
        True if file was deleted or didn't exist, False if deletion failed
    """
    resume_path = os.path.join(RESUME_STORAGE_DIR, f"{candidate_id}.pdf")

    if os.path.exists(resume_path):
        try:
            os.remove(resume_path)
            return True
        except Exception:
            return False

    return True  # File didn't exist, so "deletion" was successful


def get_resume_file_size(candidate_id: int) -> Optional[int]:
    """
    Get the size of a candidate's resume file in bytes.

    Args:
        candidate_id: ID of the candidate

    Returns:
        File size in bytes if file exists, None otherwise
    """
    resume_path = get_resume_file_path(candidate_id)

    if resume_path:
        try:
            return os.path.getsize(resume_path)
        except Exception:
            return None

    return None


def create_temp_text_file(content: str, filename_prefix: str, extension: str = 'txt') -> Optional[str]:
    """
    Create a temporary text file with the given content.

    Args:
        content: Text content to write to the file
        filename_prefix: Prefix for the temporary filename
        extension: File extension (without dot)

    Returns:
        Path to the temporary file if successful, None otherwise
    """
    try:
        # Create a temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix=f'.{extension}', prefix=f'{filename_prefix}_')
        
        # Write content to the temporary file
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
            temp_file.write(content)
        
        print(f"[File Utils] Created temp file: {temp_path}")
        return temp_path
        
    except Exception as e:
        print(f"[File Utils] Failed to create temp file: {str(e)}")
        return None


def create_temp_pdf_file(content: str, filename_prefix: str, title: str = "Document") -> Optional[str]:
    """
    Create a temporary PDF file with the given content.

    Args:
        content: Text content to write to the PDF
        filename_prefix: Prefix for the temporary filename
        title: Title for the PDF document

    Returns:
        Path to the temporary PDF file if successful, None otherwise
    """
    try:
        # Create a temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix=f'{filename_prefix}_')
        os.close(temp_fd)  # Close the file descriptor since we'll use the path
        
        # Create PDF document
        doc = SimpleDocTemplate(temp_path, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Build content
        story = []
        
        # Add title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Split content into paragraphs and add to story
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Replace newlines within paragraphs with <br/> tags
                formatted_para = para.replace('\n', '<br/>')
                story.append(Paragraph(formatted_para, styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        
        print(f"[File Utils] Created temp PDF file: {temp_path}")
        return temp_path
        
    except Exception as e:
        print(f"[File Utils] Failed to create temp PDF file: {str(e)}")
        return None


def cleanup_temp_file(file_path: str) -> bool:
    """
    Clean up a temporary file.

    Args:
        file_path: Path to the file to delete

    Returns:
        True if file was deleted successfully, False otherwise
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"[File Utils] Cleaned up temp file: {file_path}")
            return True
        return True  # File didn't exist, so cleanup was successful
    except Exception as e:
        print(f"[File Utils] Failed to cleanup temp file {file_path}: {str(e)}")
        return False
