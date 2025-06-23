## @package BibleChatAgentTests
## Unit tests for BibleChatAgent class.

import unittest
import tempfile
import pathlib
import shutil
from unittest.mock import patch, MagicMock

from Agents.BibleChatAgent import BibleChatAgent
from BibleParser import BibleParser, BibleVerse
from StudyNotesParser import StudyNotesParser, StudyNote
from EmbeddingsManager import EmbeddingsManager
from RetrievalEngine import RetrievalEngine
from LlmClient import LLMClient
from Agents.AgentResponse import AgentResponse

## Test cases for BibleChatAgent class.
class BibleChatAgentTests(unittest.TestCase):
    ## Set up test environment.
    def setUp(self):
        # Create mock components
        self.mock_bible_parser = MagicMock(spec=BibleParser)
        self.mock_study_notes_parser = MagicMock(spec=StudyNotesParser)
        self.mock_embeddings_manager = MagicMock(spec=EmbeddingsManager)
        self.mock_retrieval_engine = MagicMock(spec=RetrievalEngine)
        self.mock_llm_client = MagicMock(spec=LLMClient)
        
        # Initialize chat agent
        self.chat_agent = BibleChatAgent(
            self.mock_bible_parser,
            self.mock_study_notes_parser,
            self.mock_embeddings_manager,
            self.mock_retrieval_engine,
            self.mock_llm_client
        )
        
        # Create test data
        self.test_verse = BibleVerse(
            translation="KJV",
            book="John",
            chapter=3,
            verse=16,
            text="For God so loved the world, that he gave his only begotten Son.",
            osis_id="John.3.16"
        )
        
        self.test_study_note = StudyNote(
            file_path="test/path.txt",
            content="This is a test study note about love.",
            book="John",
            testament="NewTestament",
            chapter_topic="John 3 - God's Love",
            filename="test_note.txt",
            line_count=5
        )
    
    ## Test initialization of BibleChatAgent.
    def test_init(self):
        agent = BibleChatAgent(
            self.mock_bible_parser,
            self.mock_study_notes_parser,
            self.mock_embeddings_manager,
            self.mock_retrieval_engine,
            self.mock_llm_client
        )
        
        self.assertEqual(agent.BibleParser, self.mock_bible_parser)
        self.assertEqual(agent.StudyNotesParser, self.mock_study_notes_parser)
        self.assertEqual(agent.EmbeddingsManager, self.mock_embeddings_manager)
        self.assertEqual(agent.RetrievalEngine, self.mock_retrieval_engine)
        self.assertEqual(agent.LlmClient, self.mock_llm_client)
        self.assertEqual(agent.ChatHistory, [])
    
    ## Test processing chat message successfully.
    def test_process_chat_message_success(self):
        # Set up mocks
        retrieved_content = {
            'bible_verses': [self.test_verse],
            'study_notes': [self.test_study_note],
            'query': 'What does the Bible say about love?',
            'total_bible_results': 1,
            'total_study_results': 1
        }
        
        self.mock_retrieval_engine.RetrieveContent.return_value = retrieved_content
        self.mock_llm_client.GenerateResponse.return_value = "The Bible teaches about love in John 3:16..."
        
        # Test processing
        response = self.chat_agent.ProcessChatMessage("What does the Bible say about love?")
        
        # Verify response
        self.assertTrue(response.success)
        self.assertIn("love", response.content.lower())
        self.assertEqual(len(response.verses_used), 1)
        self.assertEqual(response.metadata['query'], "What does the Bible say about love?")
        self.assertEqual(response.metadata['retrieved_bible_count'], 1)
        self.assertEqual(response.metadata['retrieved_study_count'], 1)
        
        # Verify method calls
        self.mock_retrieval_engine.RetrieveContent.assert_called_once()
        self.mock_llm_client.GenerateResponse.assert_called_once()
        
        # Verify chat history was updated
        self.assertEqual(len(self.chat_agent.ChatHistory), 2)  # User message + assistant response
        self.assertEqual(self.chat_agent.ChatHistory[0]['role'], 'user')
        self.assertEqual(self.chat_agent.ChatHistory[1]['role'], 'assistant')
    
    ## Test processing chat message with LLM failure.
    def test_process_chat_message_llm_failure(self):
        # Set up mocks
        retrieved_content = {
            'bible_verses': [self.test_verse],
            'study_notes': [],
            'query': 'What does the Bible say about love?',
            'total_bible_results': 1,
            'total_study_results': 0
        }
        
        self.mock_retrieval_engine.RetrieveContent.return_value = retrieved_content
        self.mock_llm_client.GenerateResponse.return_value = None  # LLM failure
        
        # Test processing
        response = self.chat_agent.ProcessChatMessage("What does the Bible say about love?")
        
        # Verify response
        self.assertFalse(response.success)
        self.assertIn("trouble generating", response.content.lower())
        self.assertEqual(len(response.verses_used), 1)
        
        # Verify chat history was not updated for assistant response
        self.assertEqual(len(self.chat_agent.ChatHistory), 1)  # Only user message
        self.assertEqual(self.chat_agent.ChatHistory[0]['role'], 'user')
    
    ## Test formatting retrieved content.
    def test_format_retrieved_content(self):
        retrieved_content = {
            'bible_verses': [self.test_verse],
            'study_notes': [self.test_study_note]
        }
        
        formatted = self.chat_agent._FormatRetrievedContent(retrieved_content)
        
        # Verify Bible verses are formatted
        self.assertIn("BIBLE VERSES:", formatted)
        self.assertIn("John 3:16 (KJV)", formatted)
        self.assertIn(self.test_verse.text, formatted)
        
        # Verify study notes are formatted
        self.assertIn("BIBLE STUDY NOTES:", formatted)
        self.assertIn("John 3 - God's Love (from John)", formatted)
        self.assertIn(self.test_study_note.content, formatted)
    
    ## Test formatting retrieved content with empty results.
    def test_format_retrieved_content_empty(self):
        retrieved_content = {
            'bible_verses': [],
            'study_notes': []
        }
        
        formatted = self.chat_agent._FormatRetrievedContent(retrieved_content)
        
        # Should not contain section headers for empty results
        self.assertNotIn("BIBLE VERSES:", formatted)
        self.assertNotIn("BIBLE STUDY NOTES:", formatted)
        self.assertEqual(formatted.strip(), "")
    
    ## Test creating chat prompt.
    def test_create_chat_prompt(self):
        user_message = "What does the Bible say about love?"
        formatted_content = "BIBLE VERSES:\n1. John 3:16 (KJV) - For God so loved..."
        
        prompt = self.chat_agent._CreateChatPrompt(user_message, formatted_content)
        
        # Verify prompt structure
        self.assertIn("You are a helpful Bible study assistant", prompt)
        self.assertIn("ONLY reference the Bible verses and study notes provided below", prompt)
        self.assertIn("Quote Bible verses in full when referencing them", prompt)
        self.assertIn(user_message, prompt)
        self.assertIn(formatted_content, prompt)
    
    ## Test creating chat prompt with context.
    def test_create_chat_prompt_with_context(self):
        # Add some chat history
        self.chat_agent.ChatHistory = [
            {'role': 'user', 'content': 'Tell me about love'},
            {'role': 'assistant', 'content': 'Love is mentioned in John 3:16...'}
        ]
        
        user_message = "Tell me more about that"
        formatted_content = "BIBLE VERSES:\n1. John 3:16 (KJV) - For God so loved..."
        
        prompt = self.chat_agent._CreateChatPrompt(user_message, formatted_content)
        
        # Verify context is included
        self.assertIn("RECENT CONVERSATION CONTEXT:", prompt)
        self.assertIn("USER: Tell me about love", prompt)
        self.assertIn("ASSISTANT: Love is mentioned in John 3:16...", prompt)
    
    ## Test creating chat context.
    def test_create_chat_context(self):
        # Empty history
        context = self.chat_agent._CreateChatContext()
        self.assertEqual(context, "")
        
        # Add some history
        self.chat_agent.ChatHistory = [
            {'role': 'user', 'content': 'Tell me about love'},
            {'role': 'assistant', 'content': 'Love is mentioned in John 3:16...'}
        ]
        
        context = self.chat_agent._CreateChatContext()
        self.assertIn("RECENT CONVERSATION CONTEXT:", context)
        self.assertIn("USER: Tell me about love", context)
        self.assertIn("ASSISTANT: Love is mentioned in John 3:16...", context)
    
    ## Test creating chat context with long messages.
    def test_create_chat_context_long_messages(self):
        # Add a long message
        long_message = "This is a very long message that should be truncated when used as context " * 10
        self.chat_agent.ChatHistory = [
            {'role': 'user', 'content': long_message}
        ]
        
        context = self.chat_agent._CreateChatContext()
        self.assertIn("USER:", context)
        # Should be truncated
        self.assertLess(len(context), len(long_message) + 100)
    
    ## Test adding to chat history.
    def test_add_to_chat_history(self):
        # Test adding user message
        self.chat_agent._AddToChatHistory("user", "Hello")
        self.assertEqual(len(self.chat_agent.ChatHistory), 1)
        self.assertEqual(self.chat_agent.ChatHistory[0]['role'], 'user')
        self.assertEqual(self.chat_agent.ChatHistory[0]['content'], 'Hello')
        
        # Test adding assistant message
        self.chat_agent._AddToChatHistory("assistant", "Hi there!")
        self.assertEqual(len(self.chat_agent.ChatHistory), 2)
        self.assertEqual(self.chat_agent.ChatHistory[1]['role'], 'assistant')
        self.assertEqual(self.chat_agent.ChatHistory[1]['content'], 'Hi there!')
    
    ## Test chat history limit.
    def test_chat_history_limit(self):
        # Add more messages than the limit
        for i in range(25):  # More than CHAT_SESSION_MAX_HISTORY * 2
            self.chat_agent._AddToChatHistory("user", f"Message {i}")
        
        # Should be limited to CHAT_SESSION_MAX_HISTORY
        self.assertLessEqual(len(self.chat_agent.ChatHistory), 20)  # CHAT_SESSION_MAX_HISTORY * 2
    
    ## Test clearing chat history.
    def test_clear_chat_history(self):
        # Add some history
        self.chat_agent.ChatHistory = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi'}
        ]
        
        # Clear history
        self.chat_agent.ClearChatHistory()
        self.assertEqual(self.chat_agent.ChatHistory, [])
    
    ## Test getting chat history.
    def test_get_chat_history(self):
        # Add some history
        test_history = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi'}
        ]
        self.chat_agent.ChatHistory = test_history.copy()
        
        # Get history
        retrieved_history = self.chat_agent.GetChatHistory()
        self.assertEqual(retrieved_history, test_history)
        
        # Verify it's a copy, not a reference
        retrieved_history.append({'role': 'user', 'content': 'Test'})
        self.assertEqual(len(self.chat_agent.ChatHistory), 2)  # Original unchanged
    
    ## Test getting chat statistics.
    def test_get_chat_stats(self):
        # Empty history
        stats = self.chat_agent.GetChatStats()
        self.assertEqual(stats['total_messages'], 0)
        self.assertEqual(stats['user_messages'], 0)
        self.assertEqual(stats['assistant_messages'], 0)
        self.assertFalse(stats['session_active'])
        
        # Add some history
        self.chat_agent.ChatHistory = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi'},
            {'role': 'user', 'content': 'How are you?'}
        ]
        
        stats = self.chat_agent.GetChatStats()
        self.assertEqual(stats['total_messages'], 3)
        self.assertEqual(stats['user_messages'], 2)
        self.assertEqual(stats['assistant_messages'], 1)
        self.assertTrue(stats['session_active'])
    
    ## Test processing chat message with custom limits.
    def test_process_chat_message_custom_limits(self):
        # Set up mocks
        retrieved_content = {
            'bible_verses': [self.test_verse],
            'study_notes': [self.test_study_note],
            'query': 'What does the Bible say about love?',
            'total_bible_results': 1,
            'total_study_results': 1
        }
        
        self.mock_retrieval_engine.RetrieveContent.return_value = retrieved_content
        self.mock_llm_client.GenerateResponse.return_value = "The Bible teaches about love..."
        
        # Test with custom limits
        response = self.chat_agent.ProcessChatMessage(
            "What does the Bible say about love?",
            max_bible_verses=5,
            max_study_notes=3
        )
        
        # Verify custom limits were passed to retrieval engine
        self.mock_retrieval_engine.RetrieveContent.assert_called_with(
            "What does the Bible say about love?",
            max_bible_results=5,
            max_study_results=3
        )
        
        self.assertTrue(response.success)

if __name__ == '__main__':
    unittest.main() 