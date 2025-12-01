from app.services import document_processing_service, file_service
from app.services.rag_service import RAGService
from app.services.metadata_service import MetadataService
from app.services.llm_client_service import LLMClient

llm_client = LLMClient()
metadata_service = MetadataService()
rag_service = RAGService(
    llm_client = llm_client,
    metadata_service = metadata_service
)

__all__ = [
    'file_service',
    'document_processing_service',
    'llm_client',
    'metadata_service',
    'rag_service',
]