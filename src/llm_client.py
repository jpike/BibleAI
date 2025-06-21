"""
LLM Client for connecting to local LM Studio OpenAI-compatible API.
"""

import urllib.request
import urllib.parse
import urllib.error
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
        
        # Set headers for OpenAI-compatible API
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    def _make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make an HTTP request using urllib.
        
        Args:
            url: The URL to request.
            method: HTTP method (GET or POST).
            data: Data to send with POST request.
            
        Returns:
            Response data as dictionary, or None if failed.
        """
        try:
            # Prepare the request
            if data:
                data_bytes = json.dumps(data).encode('utf-8')
            else:
                data_bytes = None
            
            # Create request object
            req = urllib.request.Request(url, data=data_bytes, headers=self.headers, method=method)
            
            # Make the request with timeout
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read()
                return json.loads(response_data.decode('utf-8'))
                
        except urllib.error.HTTPError as e:
            print(f"HTTP Error {e.code}: {e.reason}")
            if hasattr(e, 'read'):
                error_body = e.read().decode('utf-8')
                print(f"Error body: {error_body}")
            return None
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test the connection to the LLM API.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            response_data = self._make_request(f"{self.base_url}/models")
            return response_data is not None
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
        
        response_data = self._make_request(
            f"{self.base_url}/chat/completions",
            method="POST",
            data=payload
        )
        
        if response_data and 'choices' in response_data:
            return response_data['choices'][0]['message']['content']
        else:
            print(f"Failed to generate response: {response_data}")
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