import os
import shutil
from pathlib import Path
from typing import Optional
from core.config import RESUME_STORAGE_DIR


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