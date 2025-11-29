from app.services.rag_service import RAGService, MetadataService
from app.core.llm_client import LLMClient

llm_client = LLMClient()
rag_service = RAGService(
    llm_client = llm_client
)
metadata_service = MetadataService()
