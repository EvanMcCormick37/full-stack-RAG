from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from datetime import datetime
from typing import Optional
import traceback
from app.models.schemas import DocumentListResponse, DocumentMetadata, DeleteResponse, UploadResponse
from app.services import file_service, rag_service, metadata_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def documents_health():
    '''
    Check if documents service is online
    '''
    return {"status": "operational", "endpoint":"documents"}


@router.post("/", response_model = UploadResponse)
def upload_document(
    file: UploadFile,
    session_id: Optional[str] = None
):
    '''
    Upload and process a document

    Params:
        - file - File to upload
        - x_session_id - Session ID header (optional, defaults to "default")
    
    Returns:
        Document ID and processing status.
    '''
    try:
        file_service.validate_file(file)

        document_id = file_service.generate_document_id(file.filename)
        file_path = file_service.save_upload(file, document_id)
        upload_time = datetime.now()

        rag_service.process_document(
            document_id,
            file.filename,
            file_path,
            upload_time,
            session_id
        )

        file_service.delete_file(file_path)

        response = UploadResponse(
            document_metadata = metadata_service.get_document(document_id)
        )

        return response
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model = DocumentListResponse)
def list_documents(session_id: Optional[str] = None):
    '''
    List all uploaded documents

    Returns:
        DocumentList
    '''
    try:
        return metadata_service.list_documents(session_id)
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentMetadata)
def get_document(document_id: str):
    """
    Get details of a specific document
    
    Params:
        document_id - the ID of the document to get

    Returns:
        DocumentMetadata for the matching document if it exists.
    """
    try:
        document = metadata_service.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/", response_model=DeleteResponse)
def delete_documents(session_id: Optional[str] = None):
    """
    Delete all documents from the vector database
    
    Returns:
        bool indicating whether deletion was successful
    """
    try:
        rag_service.delete_all_documents(session_id)
        return DeleteResponse(deleted=True)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting all documents: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str, session_id: Optional[str] = None):
    """
    Delete a document and remove it from the index

    Params:
        document_id - the ID of the document to delete
    
    Returns:
        bool indicating whether deletion was successful (deleting a nonexistent document returns 'true')
    """
    try:
        # Get document info
        rag_service.delete_document(document_id, session_id)
        return DeleteResponse(deleted=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))