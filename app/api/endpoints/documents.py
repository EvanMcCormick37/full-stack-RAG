from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import DocumentList, DocumentMetadata, DeleteResponse
from app.services.rag_service import rag_service
from app.services.file_service import delete_file
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model = DocumentList)
async def list_documents()
    '''
    List all uploaded documents

    Returns:
        DocumentList
    '''
    try:
        return rag_service.list_documents()
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str):
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
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str):
    """Delete a document and remove it from the index"""
    try:
        # Get document info
        success = rag_service.delete_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )
        
        # Delete from vector store
        await rag_service.delete_document(document_id)
        
        # Delete file from disk
        file_path = rag_service.get_file_path(document_id)
        if file_path:
            FileService.delete_file(file_path)
        
        # Remove from metadata
        rag_service.delete_document(document_id)
        
        return DeleteResponse(
            document_id=document_id,
            message="Document deleted successfully",
            deleted=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))