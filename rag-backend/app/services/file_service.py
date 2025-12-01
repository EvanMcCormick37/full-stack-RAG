"""
Async File Service

Handles file validation, upload, and cleanup with async I/O.
"""
import os
import hashlib
import uuid
from pathlib import Path
import logging
import aiofiles
import aiofiles.os

from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import FileValidationError

logger = logging.getLogger(__name__)


async def validate_file(file: UploadFile) -> None:
    """
    Validate the uploaded file against size limits and allowed extensions.
    
    Params:
        file: The uploaded file
    
    Raises:
        FileValidationError if validation fails
    """
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"File type {file_ext} not allowed. "
            f"Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Check file size if available
    if hasattr(file, 'size') and file.size:
        if file.size > settings.MAX_FILE_SIZE:
            raise FileValidationError(
                f"File size {file.size:,} bytes exceeds maximum "
                f"allowed size of {settings.MAX_FILE_SIZE:,} bytes"
            )


async def save_upload(file: UploadFile, document_id: str) -> str:
    """
    Save uploaded file to disk asynchronously.
    
    Params:
        file: The uploaded file
        document_id: Unique document identifier
    
    Returns:
        Path to the saved file
    """
    directory = Path(settings.TEMP_DIR)
    
    # Create directory if needed
    await aiofiles.os.makedirs(directory, exist_ok=True)
    
    file_ext = Path(file.filename).suffix
    file_path = directory / f"{document_id}{file_ext}"
    
    # Read content from SpooledTemporaryFile
    # FastAPI's UploadFile uses SpooledTemporaryFile which isn't async
    # but we can read it in chunks and write asynchronously
    content = await file.read()
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Reset file position for potential re-reads
    await file.seek(0)
    
    logger.debug(f"Saved upload to {file_path}")
    return str(file_path)


async def delete_file(file_path: str) -> bool:
    """
    Delete a file from disk asynchronously.
    
    Params:
        file_path: Path to the file to delete
    
    Returns:
        True if deleted, False if file doesn't exist
    """
    try:
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
            logger.debug(f"Deleted file: {file_path}")
            return True
        return False
    except OSError as e:
        logger.warning(f"Failed to delete {file_path}: {e}")
        return False


def generate_document_id(filename: str) -> str:
    """
    Generate a unique document ID for a file.
    
    This is CPU-light and doesn't need to be async.
    
    Params:
        filename: Name of the file
    
    Returns:
        16-character unique ID
    """
    timestamp = str(uuid.uuid4())
    return hashlib.md5(f"{filename}_{timestamp}".encode()).hexdigest()[:16]


async def ensure_directories() -> None:
    """
    Ensure required directories exist.
    
    Call during application startup.
    """
    for directory in [settings.UPLOAD_DIR, settings.TEMP_DIR]:
        await aiofiles.os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")


def clean_up() -> None:
    """
    Clean up temp and upload directories
    """
    temp_dir = Path(settings.TEMP_DIR)
    upload_dir = Path(settings.UPLOAD_DIR)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)
    if os.path.exists(upload_dir):
        os.rmdir(upload_dir)