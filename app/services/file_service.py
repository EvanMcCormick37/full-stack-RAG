import os
import hashlib
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import UploadFile
from typing import Dict, Any
from datetime import datetime
import logging
from app.config import settings
from app.core.exceptions import FileValidationError, FileOperationError


logger = logging.getLogger(__name__)

def validate_file(file: UploadFile) -> None:
    '''
    Params:
    file - The file being uploaded

    Validates the uploaded file against size limits and allowed extensions

    Raises: FileValidationError
    '''
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.allowed_extensions:
        raise FileValidationError(
            f"File type {file_ext} not allowed."
        )
    
    if hasattr(file,'size') and file.size>settings.max_file_size:
        raise FileValidationError(
            f"File size {file.size} too large. Maximum file size allowed for upload is {settings.max_file_size}"
        )
    

async def save_upload(
    file: UploadFile,
    document_id: str
) -> str:
    '''
    Params:
    file - The uploaded file
    document_id - Unique document identifier
    
    Save uploaded file to disk
    '''
    directory = settings.TEMP_DIR
    Path(directory).mkdir(parents=True, exist_ok=True)
    file_ext = Path(file.filename).suffix
    file_path = os.path.join(directory,f"{document_id}{file_ext}")

    with open(file_path, 'wb') as f:
        f.write(file.file.read())
    
    return file_path


def delete_file(file_path) -> bool:
    '''
    Params:
    file_path - Path to the file to delete

    Delete file from disk

    Returns:
    bool - True if deleted, False if file doesn't exist.
    '''
        
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    else:
        return False
    

def generate_document_id(filename: str) -> str:
    '''
    Params:
    filename - name of file to give unique id

    Generate a unique document ID for a file

    Returns:
    uuid: 16-char unique ID for file document
    '''
    timestamp = str(uuid.uuid4())
    return hashlib.md5(f"{filename}_{timestamp}".encode()).hexdigest()[:16]