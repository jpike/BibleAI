#!/usr/bin/env python3
## @package LlmClientTests
## Unit tests for the LLMClient class.

import unittest
import sys
import os
import json
import urllib.request
import urllib.error
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.LlmClient import LLMClient

## Test cases for the LLMClient class.
class LlmClientTests(unittest.TestCase):
    ## Set up test environment before each test.
    def setUp(self):
        self.client = LLMClient("http://localhost:1234/v1", "test-key", 30)
    
    ## Test LLMClient initialization.
    def test_Initialization(self):
        client = LLMClient("http://localhost:1234/v1", "test-key", 30)
        self.assertEqual(client.BaseUrl, "http://localhost:1234/v1")
        self.assertEqual(client.ApiKey, "test-key")
        self.assertEqual(client.Timeout, 30)
        self.assertEqual(client.Headers["Content-Type"], "application/json")
        self.assertEqual(client.Headers["Authorization"], "Bearer test-key")
    
    ## Test initialization with default parameters.
    def test_DefaultInitialization(self):
        client = LLMClient()
        self.assertEqual(client.BaseUrl, "http://localhost:1234/v1")
        self.assertEqual(client.ApiKey, "not-needed")
        self.assertEqual(client.Timeout, 600)
    
    ## Test URL normalization (removing trailing slash).
    def test_UrlNormalization(self):
        client = LLMClient("http://localhost:1234/v1/", "test-key")
        self.assertEqual(client.BaseUrl, "http://localhost:1234/v1")
    
    ## Test successful connection test.
    @patch('urllib.request.urlopen')
    def test_SuccessfulConnectionTest(self, mock_urlopen):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"models": []}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.client.TestConnection()
        self.assertTrue(result)
    
    ## Test failed connection test.
    @patch('urllib.request.urlopen')
    def test_FailedConnectionTest(self, mock_urlopen):
        # Mock connection error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        result = self.client.TestConnection()
        self.assertFalse(result)
    
    ## Test successful response generation.
    @patch('urllib.request.urlopen')
    def test_SuccessfulResponseGeneration(self, mock_urlopen):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Test response"}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateResponse(messages)
        
        self.assertEqual(result, "Test response")
    
    ## Test failed response generation.
    @patch('urllib.request.urlopen')
    def test_FailedResponseGeneration(self, mock_urlopen):
        # Mock failed response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"error": "Invalid request"}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateResponse(messages)
        
        self.assertIsNone(result)
    
    ## Test HTTP error handling.
    @patch('urllib.request.urlopen')
    def test_HttpErrorHandling(self, mock_urlopen):
        # Mock HTTP error with a simple exception
        mock_urlopen.side_effect = Exception("HTTP Error")
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateResponse(messages)
        
        self.assertIsNone(result)
    
    ## Test URL error handling.
    @patch('urllib.request.urlopen')
    def test_UrlErrorHandling(self, mock_urlopen):
        # Mock URL error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateResponse(messages)
        
        self.assertIsNone(result)
    
    ## Test JSON decode error handling.
    @patch('urllib.request.urlopen')
    def test_JsonDecodeErrorHandling(self, mock_urlopen):
        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.read.return_value = b"Invalid JSON"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateResponse(messages)
        
        self.assertIsNone(result)
    
    ## Test successful retry logic.
    @patch('urllib.request.urlopen')
    def test_SuccessfulRetryLogic(self, mock_urlopen):
        # Mock first failure, then success
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Test response"}}]
        }).encode('utf-8')
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_response
        
        # First call fails, second call succeeds with a valid HTTP response
        def side_effect(*args, **kwargs):
            if side_effect.counter == 0:
                side_effect.counter += 1
                raise urllib.error.URLError("Connection refused")
            else:
                return mock_context_manager
        side_effect.counter = 0
        mock_urlopen.side_effect = side_effect
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateWithRetry(messages, max_retries=2)
        self.assertEqual(result, "Test response")
        self.assertEqual(mock_urlopen.call_count, 2)
    
    ## Test retry logic with all failures.
    @patch('urllib.request.urlopen')
    def test_RetryLogicAllFailures(self, mock_urlopen):
        # Mock all calls failing
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateWithRetry(messages, max_retries=3)
        
        self.assertIsNone(result)
        self.assertEqual(mock_urlopen.call_count, 3)
    
    ## Test retry logic with immediate success.
    @patch('urllib.request.urlopen')
    def test_RetryLogicImmediateSuccess(self, mock_urlopen):
        # Mock immediate success
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Test response"}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateWithRetry(messages, max_retries=3)
        
        self.assertEqual(result, "Test response")
        self.assertEqual(mock_urlopen.call_count, 1)
    
    ## Test response generation with custom parameters.
    @patch('urllib.request.urlopen')
    def test_ResponseGenerationWithCustomParameters(self, mock_urlopen):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Test response"}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateResponse(
            messages, 
            model="custom-model", 
            temperature=0.5, 
            max_tokens=500
        )
        
        self.assertEqual(result, "Test response")
        
        # Verify the request payload
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.get_full_url(), "http://localhost:1234/v1/chat/completions")
        
        # Parse the request data to verify parameters
        request_data = json.loads(request.data.decode('utf-8'))
        self.assertEqual(request_data["model"], "custom-model")
        self.assertEqual(request_data["temperature"], 0.5)
        self.assertEqual(request_data["max_tokens"], 500)
        self.assertEqual(request_data["messages"], messages)
    
    ## Test request timeout handling.
    @patch('urllib.request.urlopen')
    def test_RequestTimeout(self, mock_urlopen):
        # Mock timeout error
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        
        messages = [{"role": "user", "content": "Hello"}]
        result = self.client.GenerateResponse(messages)
        
        self.assertIsNone(result)
    
    ## Test models endpoint request.
    @patch('urllib.request.urlopen')
    def test_ModelsEndpointRequest(self, mock_urlopen):
        # Mock successful models response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"models": ["model1", "model2"]}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        result = self.client.TestConnection()
        
        self.assertTrue(result)
        
        # Verify the request
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.get_full_url(), "http://localhost:1234/v1/models")
    
    ## Test request headers.
    @patch('urllib.request.Request')
    @patch('urllib.request.urlopen')
    def test_RequestHeaders(self, mock_urlopen, mock_request):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Test response"}}]
        }).encode('utf-8')
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context_manager
        messages = [{"role": "user", "content": "Hello"}]
        self.client.GenerateResponse(messages)
        # Verify headers passed to Request
        call_args = mock_request.call_args
        headers = call_args[1]["headers"]
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Authorization"], "Bearer test-key")
    
    ## Test empty messages list.
    @patch('urllib.request.urlopen')
    def test_EmptyMessagesList(self, mock_urlopen):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Test response"}}]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        messages = []
        result = self.client.GenerateResponse(messages)
        
        self.assertEqual(result, "Test response")
        
        # Verify empty messages list was sent
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        request_data = json.loads(request.data.decode('utf-8'))
        self.assertEqual(request_data["messages"], [])

if __name__ == '__main__':
    unittest.main() 