## @package LlmClient
## LLM Client for connecting to local LM Studio OpenAI-compatible API.

import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Dict, List, Any, Optional
import time


## Client for interacting with local LLM via OpenAI-compatible API.
class LLMClient:
    ## Initialize the LLM client.
    ## @param[in] base_url - Base URL for the LM Studio API.
    ## @param[in] api_key - API key (usually not needed for local LM Studio).
    ## @param[in] timeout - Request timeout in seconds.
    def __init__(self, base_url: str = "http://localhost:1234/v1", 
                 api_key: str = "not-needed", timeout: int = 30):
        ## Base URL for the LM Studio API.
        self.BaseUrl: str = base_url.rstrip('/')
        ## API key for authentication (usually not needed for local LM Studio).
        self.ApiKey: str = api_key
        ## Request timeout in seconds.
        self.Timeout: int = timeout
        
        ## HTTP headers for API requests.
        self.Headers: dict[str, str] = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    ## Make an HTTP request using urllib.
    ## @param[in] url - The URL to request.
    ## @param[in] method - HTTP method (GET or POST).
    ## @param[in] data - Data to send with POST request.
    ## @return Response data as dictionary, or None if failed.
    def _MakeRequest(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:  
        try:
            # Prepare the request
            if data:
                data_bytes = json.dumps(data).encode('utf-8')
            else:
                data_bytes = None
            
            # Create request object
            req = urllib.request.Request(url, data=data_bytes, headers=self.Headers, method=method)
            
            # Make the request with timeout
            with urllib.request.urlopen(req, timeout=self.Timeout) as response:
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

    ## Test the connection to the LLM API.
    ## @return True if connection successful, False otherwise.
    def TestConnection(self) -> bool:
        try:
            response_data = self._MakeRequest(f"{self.BaseUrl}/models")
            return response_data is not None
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    ## Generate a response from the LLM.
    ## @param[in] messages - List of message dictionaries with 'role' and 'content'.
    ## @param[in] model - Model name to use.
    ## @param[in] temperature - Sampling temperature (0.0 to 2.0).
    ## @param[in] max_tokens - Maximum tokens to generate.
    ## @return Generated response text, or None if failed.
    def GenerateResponse(self, messages: List[Dict[str, str]], 
                         model: str = "local-model",
                         temperature: float = 0.7,
                         max_tokens: int = 1000) -> Optional[str]:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        response_data = self._MakeRequest(
            f"{self.BaseUrl}/chat/completions",
            method="POST",
            data=payload
        )
        
        if response_data and 'choices' in response_data:
            return response_data['choices'][0]['message']['content']
        else:
            print(f"Failed to generate response: {response_data}")
            return None
    
    ## Generate response with retry logic.
    ## @param[in] messages - List of message dictionaries.
    ## @param[in] max_retries - Maximum number of retry attempts.
    ## @param[in] **kwargs - Additional arguments for GenerateResponse.
    ## @return Generated response text, or None if all retries failed.
    def GenerateWithRetry(self, messages: List[Dict[str, str]], 
                           max_retries: int = 3,
                           **kwargs) -> Optional[str]:
        for attempt in range(max_retries):
            response = self.GenerateResponse(messages, **kwargs)
            if response is not None:
                return response
            
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                
        return None 