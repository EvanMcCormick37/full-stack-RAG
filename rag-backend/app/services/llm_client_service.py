from typing import List
import hashlib
from collections import OrderedDict
import google.generativeai as genai
import time
import random
from app.config import settings
from app.models.schemas import Source
from app.core.prompts import PROMPT_STYLES, ROUTING_PROMPT, AnswerStyle


class LLMClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self._cache: OrderedDict[str, str] = OrderedDict()


    def _validate_prompt(self, prompt: str) -> None:
        """Validate the input prompt."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if len(prompt) > 900_000:
            raise ValueError("Prompt exceeds maximum length")


    def _call_with_exponential_backoff(self, prompt: str) -> str:
        """Call the Gemini API with exponential backoff on rate limit errors."""
        delay = 1
        for attempt in range(settings.LLM_MAX_RETRIES):
            try:
                response = self._model.generate_content(prompt)
                return response.text
            except Exception as e:
                if attempt == settings.LLM_MAX_RETRIES - 1:
                    raise e
                sleep_time = delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)


    def _route_prompt(self, question: str, context: str) -> AnswerStyle:
        """Determine the best prompt style for the given question and context."""
        routing_prompt = ROUTING_PROMPT.format(question=question, context=context)
        response = self._call_with_exponential_backoff(routing_prompt).strip().upper()
        
        # Map routing response to AnswerStyle
        routing_map = {
            "ANSWER": AnswerStyle.ANSWER,
            "ANALOGIZE": AnswerStyle.ANALOGIZE,
            "UNRELATED": AnswerStyle.DISTRACT,
        }
        return routing_map.get(response, AnswerStyle.DISTRACT)  # Default to ANSWER


    def answer(self, question: str, sources: List[Source]) -> str:
        """
        Answer a user's question with the given sources using prompt-routing.

        Params:
            - question: The user's question
            - sources: Text chunks from the database to provide context

        Returns:
            The LLM's answer to the context prompt.
        """
        context = ",\n".join([f"{src.chunk_text} (src. {src.document_id})" for src in sources])
        
        # Check cache
        prompt_hash = hashlib.sha256(",".join([question,context]).encode('utf-8')).hexdigest()
        if prompt_hash in self._cache:
            answer = self._cache[prompt_hash]
            return answer, AnswerStyle.CACHED
        # Route to determine best prompt style
        prompt_style = self._route_prompt(question, context)
        
        # Build final prompt with selected style
        prompt = PROMPT_STYLES[prompt_style].format(context=context, question=question)
        self._validate_prompt(prompt)

        # Generate answer
        answer = self._call_with_exponential_backoff(prompt)

        # Update cache
        if len(self._cache) >= settings.MAX_CACHE_SIZE:
            self._cache.popitem(last=False)
        self._cache[prompt_hash] = answer

        return answer, prompt_style