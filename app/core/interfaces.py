from typing import Protocol, List
from abc import abstractmethod

class DocumentProcessor(Protocol):
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        # Extract text from a document
        ...
    
    @abstractmethod
    def chunk_text(self, text: str) -> str:
        # Chunk text
        ...


class LLMClient(Protocol):
    @abstractmethod
    def answer(
        self,
        question: str,
        context_docs: List[str],
        style: str
    ) -> str:
        # Generate answer from context prompt
        ...