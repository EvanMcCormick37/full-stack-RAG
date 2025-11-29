from app.services.rag_service import RAGService, MetadataService
from app.core.llm_client import LLMClient

# Initialize singleton service instances for import
llm_client = LLMClient()
metadata_service = MetadataService()

# Initialize last as this imports the other service singletons
rag_service = RAGService()