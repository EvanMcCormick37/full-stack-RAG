from typing import Protocol, List
from abc import abstractmethod


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