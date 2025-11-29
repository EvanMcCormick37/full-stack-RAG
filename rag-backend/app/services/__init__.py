from app.services.rag_service import RAGService
from app.services.metadata_service import MetadataService
from app.core.llm_client import LLMClient

llm_client = LLMClient()
metadata_service = MetadataService()
rag_service = RAGService(
    llm_client = llm_client,
    metadata_service = metadata_service
)
