from fastapi import APIRouter, HTTPException, UploadFile, File
from datetime import datetime
import traceback
from app.models.schemas import DocumentListResponse, DocumentMetadata, DeleteResponse, UploadResponse
from app.services import file_service, rag_service
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
    file: UploadFile = File(...)
):
    '''
    Upload and process a document

    Params:
        file - File to upload
    
    Returns:
        Document ID and processing status.
    '''
    try:
        file_service.validate_file(file)

        document_id = file_service.generate_document_id(file.filename)
        file_path = file_service.save_upload(file, document_id)
        upload_time = datetime.now()

        num_chunks = rag_service.process_document(
            document_id,
            file.filename,
            file.size,
            file_path,
            upload_time
        )

        file_service.delete_file(file_path)

        response = UploadResponse(
            document_metadata = DocumentMetadata(
                document_id = document_id,
                filename = file.filename,
                file_size = file.size,
                upload_time = upload_time,
                num_chunks = num_chunks
            )
        )

        return response
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model = DocumentListResponse)
def list_documents():
    '''
    List all uploaded documents

    Returns:
        DocumentList
    '''
    try:
        return rag_service.list_documents()
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentMetadata)
def get_document(document_id: str):
    """Get details of a specific document"""
    try:
        document = rag_service.get_document(document_id)
        
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


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str):
    """Delete a document and remove it from the index"""
    try:
        # Get document info
        success = rag_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        return DeleteResponse(
            deleted=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))