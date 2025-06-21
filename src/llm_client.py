"""
LLM Client for connecting to local LM Studio OpenAI-compatible API.
"""

import requests
import json
from typing import Dict, List, Any, Optional
import time


class LLMClient:
    """Client for interacting with local LLM via OpenAI-compatible API."""
    
    def __init__(self, base_url: str = "http://localhost:1234/v1", 
                 api_key: str = "not-needed", timeout: int = 30):
        """
        Initialize the LLM client.
        
        Args:
            base_url: Base URL for the LM Studio API.
            api_key: API key (usually not needed for local LM Studio).
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        # Set headers for OpenAI-compatible API
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        })
    
    def test_connection(self) -> bool:
        """
        Test the connection to the LLM API.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            response = self.session.get(f"{self.base_url}/models", timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def generate_response(self, messages: List[Dict[str, str]], 
                         model: str = "local-model",
                         temperature: float = 0.7,
                         max_tokens: int = 1000) -> Optional[str]:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            model: Model name to use.
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens to generate.
            
        Returns:
            Generated response text, or None if failed.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error generating response: {e}")
            return None
    
    def generate_with_retry(self, messages: List[Dict[str, str]], 
                           max_retries: int = 3,
                           **kwargs) -> Optional[str]:
        """
        Generate response with retry logic.
        
        Args:
            messages: List of message dictionaries.
            max_retries: Maximum number of retry attempts.
            **kwargs: Additional arguments for generate_response.
            
        Returns:
            Generated response text, or None if all retries failed.
        """
        for attempt in range(max_retries):
            response = self.generate_response(messages, **kwargs)
            if response is not None:
                return response
            
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                
        return None 