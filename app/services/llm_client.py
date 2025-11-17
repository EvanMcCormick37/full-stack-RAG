from typing import Any, List, Dict, Optional
import hashlib
from collections import OrderedDict
import google.generativeai as genai
import time
import random
from app.config import settings
from app.models.schemas import PromptStyle

class LLMClient:
    def __init__(self):
        genai.configure(api_key = settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self._cache: OrderedDict[str, str] = OrderedDict()


    def _validate_prompt(self, prompt: str) -> None:
        """
        Validate the input prompt.
        
        Args:
            prompt: User's prompt text
            
        Raises:
            ValueError: If prompt is invalid
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        if len(prompt) > 900_000:  # Gemini's approximate token limit
            raise ValueError("Prompt exceeds maximum length")
        

    def _call_with_exponential_backoff(self, prompt: str) -> str:
        """
        Call the Gemini API with exponential backoff on rate limit errors.
        
        Args:
            prompt: User's prompt text
            
        Returns:
            Model's response text
        """
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


    def answer(
            self,
            prompt: str,
            context: List[str],
            style: PromptStyle
            ) -> str:
        '''
        Answer a user's question with the given context and prompt style.

        Params:
            Question - The user's question
            Context - Text chunks from the database to provide context to the user's question
            Style - The style in which the LLM should answer. There are multiple 'style' options, each tied to a context prompt template designed to elicit a particular conversational style from the LLM.
        '''
        self._validate_prompt(prompt)

        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        if prompt_hash in self._cache:
            return self._cache[prompt_hash]
        
        response_text = self._call_with_exponential_backoff(prompt)

        if len(self._cache) >= settings.MAX_CACHE_SIZE:
            self._cache.popitem(last=False)
        self._cache[prompt_hash] = response_text
        
        return response_text