from typing import Any, List, Dict, Optional
import google.generativeai as genai
import time
import random

class LLMClient:
    def __init__(
            self,
            api_key: str,
            model_name: str,
            max_retries: int,
            max_delay: int,
            ):
        
        self._api_key = api_key
        self._model_name = model_name
        self._model = self.initialize_model()
        self._max_retries = max_retries
        self._delay = max_delay


    def initialize_model(self):
        """
        Initialize the Gemini model with safety settings.
        
        Returns:
            Configured GenerativeModel instance
        """
        genai.configure(api_key = self._api_key)
        return genai.GenerativeModel(self._model_name)


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

        for attempt in range(self._max_retries):
            try:
                response = self._model.generate_content(prompt)
                return response.text
            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise e
                sleep_time = self._delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)


    def query(
            self,
            prompt: str,
            ) -> str:
        self._validate_prompt(prompt)
        response_text = self._call_with_exponential_backoff(prompt)
        return response_text