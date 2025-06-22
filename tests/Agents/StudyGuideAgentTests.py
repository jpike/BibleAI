#!/usr/bin/env python3
## @package StudyGuideAgentTests
## Unit tests for the StudyGuideAgent class.

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.Agents.StudyGuideAgent import StudyGuideAgent
from src.Agents.AgentResponse import AgentResponse
from src.BibleVerse import BibleVerse

## Test cases for the StudyGuideAgent class.
class StudyGuideAgentTests(unittest.TestCase):
    ## Set up test environment before each test.
    def setUp(self):
        # Create mock dependencies
        self.mock_bible_parser = Mock()
        self.mock_llm_client = Mock()
        
        # Create agent instance
        self.agent = StudyGuideAgent(self.mock_bible_parser, self.mock_llm_client)
    
    ## Test StudyGuideAgent initialization.
    def test_Initialization(self):
        agent = StudyGuideAgent(self.mock_bible_parser, self.mock_llm_client)
        
        self.assertEqual(agent.BibleParser, self.mock_bible_parser)
        self.assertEqual(agent.LlmClient, self.mock_llm_client)
    
    ## Test successful comprehensive study guide creation.
    def test_SuccessfulComprehensiveGuide(self):
        # Mock topic research response
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8"),
            BibleVerse("KJV", "1Co", 13, 4, "Charity suffereth long, and is kind.", "1Co.13.4")
        ]
        
        # Mock LLM response for study guide
        self.mock_llm_client.GenerateResponse.return_value = "Comprehensive study guide content..."
        
        # Test the study guide creation
        result = self.agent.CreateStudyGuide("love", "KJV", "comprehensive")
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Comprehensive study guide content...")
        self.assertEqual(len(result.verses_used), 2)
        self.assertEqual(result.metadata["topic"], "love")
        self.assertEqual(result.metadata["guide_type"], "comprehensive")
        self.assertEqual(result.metadata["verse_count"], 2)
        
        # Verify LLM was called with comprehensive guide prompt
        self.mock_llm_client.GenerateResponse.assert_called_once()
        call_args = self.mock_llm_client.GenerateResponse.call_args
        prompt = call_args[0][0][0]["content"]
        self.assertIn("comprehensive Bible study guide", prompt)
        self.assertIn("love", prompt)
    
    ## Test successful devotional study guide creation.
    def test_SuccessfulDevotionalGuide(self):
        # Mock topic research response
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8")
        ]
        
        # Mock LLM response for devotional guide
        self.mock_llm_client.GenerateResponse.return_value = "Devotional study guide content..."
        
        # Test the study guide creation
        result = self.agent.CreateStudyGuide("love", "KJV", "devotional")
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Devotional study guide content...")
        self.assertEqual(result.metadata["guide_type"], "devotional")
        
        # Verify LLM was called with devotional guide prompt
        self.mock_llm_client.GenerateResponse.assert_called_once()
        call_args = self.mock_llm_client.GenerateResponse.call_args
        prompt = call_args[0][0][0]["content"]
        self.assertIn("devotional Bible study guide", prompt)
        self.assertIn("7-day devotional", prompt)
    
    ## Test successful theological study guide creation.
    def test_SuccessfulTheologicalGuide(self):
        # Mock topic research response
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8")
        ]
        
        # Mock LLM response for theological guide
        self.mock_llm_client.GenerateResponse.return_value = "Theological study guide content..."
        
        # Test the study guide creation
        result = self.agent.CreateStudyGuide("love", "KJV", "theological")
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Theological study guide content...")
        self.assertEqual(result.metadata["guide_type"], "theological")
        
        # Verify LLM was called with theological guide prompt
        self.mock_llm_client.GenerateResponse.assert_called_once()
        call_args = self.mock_llm_client.GenerateResponse.call_args
        prompt = call_args[0][0][0]["content"]
        self.assertIn("theological Bible study guide", prompt)
        self.assertIn("theological depth", prompt)
    
    ## Test study guide creation with default type.
    def test_DefaultGuideType(self):
        # Mock topic research response
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8")
        ]
        
        # Mock LLM response
        self.mock_llm_client.GenerateResponse.return_value = "Default guide content..."
        
        # Test without specifying guide type (should default to comprehensive)
        result = self.agent.CreateStudyGuide("love", "KJV")
        
        # Verify default type is used
        self.assertEqual(result.metadata["guide_type"], "comprehensive")
    
    ## Test study guide creation with unknown type.
    def test_UnknownGuideType(self):
        # Mock topic research response
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8")
        ]
        
        # Mock LLM response
        self.mock_llm_client.GenerateResponse.return_value = "Default guide content..."
        
        # Test with unknown guide type
        result = self.agent.CreateStudyGuide("love", "KJV", "unknown_type")
        
        # Should default to comprehensive
        self.assertEqual(result.metadata["guide_type"], "comprehensive")
    
    ## Test study guide creation with topic research failure.
    @patch('src.Agents.StudyGuideAgent.TopicResearchAgent')
    def test_TopicResearchFailure(self, mock_topic_agent_class):
        # Mock topic research agent
        mock_topic_agent = Mock()
        mock_topic_agent_class.return_value = mock_topic_agent
        
        # Mock failed topic research
        failed_response = AgentResponse(
            success=False,
            content="Topic research failed",
            verses_used=[],
            metadata={"topic": "love"}
        )
        mock_topic_agent.ResearchTopic.return_value = failed_response
        
        # Test the study guide creation
        result = self.agent.CreateStudyGuide("love", "KJV", "comprehensive")
        
        # Should return the failed response
        self.assertFalse(result.success)
        self.assertEqual(result.content, "Topic research failed")
        self.assertEqual(result.verses_used, [])
        
        # Verify topic research was called
        mock_topic_agent.ResearchTopic.assert_called_once_with("love", "KJV", max_verses=30)
    
    ## Test study guide creation with LLM failure.
    @patch('src.Agents.StudyGuideAgent.TopicResearchAgent')
    def test_LlmFailure(self, mock_topic_agent_class):
        # Mock topic research agent
        mock_topic_agent = Mock()
        mock_topic_agent_class.return_value = mock_topic_agent
        
        # Mock successful topic research
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8")
        ]
        successful_response = AgentResponse(
            success=True,
            content="Topic research successful",
            verses_used=mock_verses,
            metadata={"topic": "love"}
        )
        mock_topic_agent.ResearchTopic.return_value = successful_response
        
        # Mock LLM failure
        self.mock_llm_client.GenerateResponse.return_value = None
        
        # Test the study guide creation
        result = self.agent.CreateStudyGuide("love", "KJV", "comprehensive")
        
        # Should return failure response
        self.assertFalse(result.success)
        self.assertEqual(result.content, "Failed to create study guide.")
        self.assertEqual(len(result.verses_used), 1)
        self.assertEqual(result.metadata["guide_type"], "comprehensive")
    
    ## Test comprehensive guide creation method.
    def test_ComprehensiveGuideMethod(self):
        # Mock verses
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8")
        ]
        
        # Mock LLM response
        self.mock_llm_client.GenerateResponse.return_value = "Comprehensive guide content..."
        
        # Test the method directly
        result = self.agent._CreateComprehensiveGuide("love", mock_verses)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Comprehensive guide content...")
        self.assertEqual(result.metadata["topic"], "love")
        self.assertEqual(result.metadata["guide_type"], "comprehensive")
        
        # Verify prompt contains comprehensive guide elements
        call_args = self.mock_llm_client.GenerateResponse.call_args
        prompt = call_args[0][0][0]["content"]
        self.assertIn("comprehensive Bible study guide", prompt)
        self.assertIn("Introduction and overview", prompt)
        self.assertIn("Key passages with explanations", prompt)
        self.assertIn("Main themes and principles", prompt)
        self.assertIn("Historical and cultural context", prompt)
        self.assertIn("Application questions", prompt)
        self.assertIn("Further study suggestions", prompt)
    
    ## Test devotional guide creation method.
    def test_DevotionalGuideMethod(self):
        # Mock verses
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8")
        ]
        
        # Mock LLM response
        self.mock_llm_client.GenerateResponse.return_value = "Devotional guide content..."
        
        # Test the method directly
        result = self.agent._CreateDevotionalGuide("love", mock_verses)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Devotional guide content...")
        self.assertEqual(result.metadata["topic"], "love")
        self.assertEqual(result.metadata["guide_type"], "devotional")
        
        # Verify prompt contains devotional guide elements
        call_args = self.mock_llm_client.GenerateResponse.call_args
        prompt = call_args[0][0][0]["content"]
        self.assertIn("devotional Bible study guide", prompt)
        self.assertIn("7-day devotional", prompt)
        self.assertIn("Daily scripture focus", prompt)
        self.assertIn("Reflection questions", prompt)
        self.assertIn("Prayer prompts", prompt)
        self.assertIn("Personal application", prompt)
    
    ## Test theological guide creation method.
    def test_TheologicalGuideMethod(self):
        # Mock verses
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8")
        ]
        
        # Mock LLM response
        self.mock_llm_client.GenerateResponse.return_value = "Theological guide content..."
        
        # Test the method directly
        result = self.agent._CreateTheologicalGuide("love", mock_verses)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Theological guide content...")
        self.assertEqual(result.metadata["topic"], "love")
        self.assertEqual(result.metadata["guide_type"], "theological")
        
        # Verify prompt contains theological guide elements
        call_args = self.mock_llm_client.GenerateResponse.call_args
        prompt = call_args[0][0][0]["content"]
        self.assertIn("theological Bible study guide", prompt)
        self.assertIn("Biblical definition and scope", prompt)
        self.assertIn("Key theological concepts", prompt)
        self.assertIn("Systematic analysis of passages", prompt)
        self.assertIn("Historical development of the doctrine", prompt)
        self.assertIn("Contemporary implications", prompt)
        self.assertIn("Discussion questions for deeper study", prompt)
    
    ## Test verse formatting for analysis.
    def test_VerseFormatting(self):
        # Create test verses
        verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8"),
            BibleVerse("KJV", "1Co", 13, 4, "Charity suffereth long, and is kind.", "1Co.13.4")
        ]
        
        # Test the formatting method
        formatted = self.agent._FormatVersesForAnalysis(verses)
        
        expected = (
            "1Jo 4:8 - He that loveth not knoweth not God; for God is love.\n"
            "1Co 13:4 - Charity suffereth long, and is kind."
        )
        self.assertEqual(formatted, expected)
    
    ## Test empty verse list formatting.
    def test_EmptyVerseFormatting(self):
        # Test formatting empty list
        formatted = self.agent._FormatVersesForAnalysis([])
        self.assertEqual(formatted, "")
    
    ## Test study guide creation with different translations.
    @patch('src.Agents.StudyGuideAgent.TopicResearchAgent')
    def test_DifferentTranslations(self, mock_topic_agent_class):
        # Mock topic research agent
        mock_topic_agent = Mock()
        mock_topic_agent_class.return_value = mock_topic_agent
        
        # Mock successful topic research
        mock_verses = [
            BibleVerse("WEB", "1Jo", 4, 8, "He who doesn't love doesn't know God, for God is love.", "1Jo.4.8")
        ]
        successful_response = AgentResponse(
            success=True,
            content="Topic research successful",
            verses_used=mock_verses,
            metadata={"topic": "love"}
        )
        mock_topic_agent.ResearchTopic.return_value = successful_response
        
        # Mock LLM response
        self.mock_llm_client.GenerateResponse.return_value = "Guide content..."
        
        # Test with different translation
        result = self.agent.CreateStudyGuide("love", "WEB", "comprehensive")
        
        # Verify translation is passed correctly
        mock_topic_agent.ResearchTopic.assert_called_with("love", "WEB", max_verses=30)
        self.assertTrue(result.success)
    
    ## Test study guide creation with large verse list.
    @patch('src.Agents.StudyGuideAgent.TopicResearchAgent')
    def test_LargeVerseList(self, mock_topic_agent_class):
        # Mock topic research agent
        mock_topic_agent = Mock()
        mock_topic_agent_class.return_value = mock_topic_agent
        
        # Mock successful topic research with many verses
        mock_verses = []
        for i in range(50):
            verse = BibleVerse("KJV", "1Jo", 4, i+1, f"Love verse {i+1}", f"1Jo.4.{i+1}")
            mock_verses.append(verse)
        
        successful_response = AgentResponse(
            success=True,
            content="Topic research successful",
            verses_used=mock_verses,
            metadata={"topic": "love"}
        )
        mock_topic_agent.ResearchTopic.return_value = successful_response
        
        # Mock LLM response
        self.mock_llm_client.GenerateResponse.return_value = "Guide content..."
        
        # Test with large verse list
        result = self.agent.CreateStudyGuide("love", "KJV", "comprehensive")
        
        # Should handle large verse list
        self.assertTrue(result.success)
        self.assertEqual(len(result.verses_used), 50)
        self.assertEqual(result.metadata["verse_count"], 50)

if __name__ == '__main__':
    unittest.main() 