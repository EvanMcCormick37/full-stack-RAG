from typing import Protocol, List
from abc import abstractmethod
from app.models.schemas import PromptStyle, Source


class LLMClient(Protocol):
    @abstractmethod
    def answer(
        self,
        question: str,
        context_docs: List[Source],
        style: PromptStyle
    ) -> str:
        # Generate answer from context prompt
        ...