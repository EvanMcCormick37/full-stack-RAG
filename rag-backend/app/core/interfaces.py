from typing import Protocol, List, Optional
from datetime import datetime
from abc import abstractmethod
from app.models.schemas import Source, DocumentMetadata, DocumentListResponse


class LLMClient(Protocol):
    @abstractmethod
    async def answer(
        self,
        question: str,
        context_docs: List[Source]
    ) -> str:
        # Generate answer from context prompt
        ...

class MetadataService(Protocol):
    async def create_document(
        self,
        document_id: str,
        filename: str,
        upload_time: datetime,
        session_id: str,
        num_chunks: int,
        status: str = "completed"
    ) -> DocumentMetadata:
        ...
    
    async def get_document(
        self, 
        document_id: str
    ) -> Optional[DocumentMetadata]:
        ...
    
    async def get_all_documents(
        self, 
        session_id: Optional[str] = None
    ) -> List[DocumentMetadata]:
        ...
    
    async def get_documents_by_session(
        self, 
        session_id: str
    ) -> List[DocumentMetadata]:
        ...
    
    async def update_last_accessed(
        self, 
        document_id: str
    ) -> bool:
        ...
    
    async def update_status(
        self, 
        document_id: str, 
        status: str
    ) -> bool:
        ...
    
    async def delete_document(
        self, 
        document_id: str
    ) -> None:
        ...
    
    async def delete_all_documents(self) -> None:
        ...
    
    async def get_most_stale_document(self) -> Optional[DocumentMetadata]:
        ...
    
    async def count_documents(self) -> int:
        ...
    
    async def list_documents(
        self, 
        session_id: Optional[str]
    ) -> DocumentListResponse:
        ...