from typing import Protocol, List
from abc import abstractmethod
from app.models.schemas import Source


class LLMClient(Protocol):
    @abstractmethod
    def answer(
        self,
        question: str,
        context_docs: List[Source]
    ) -> str:
        # Generate answer from context prompt
        ...


class MetadataService(Protocol):
    # Just here for some fun service validation
    ...