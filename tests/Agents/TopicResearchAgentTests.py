#!/usr/bin/env python3
## @package TopicResearchAgentTests
## Unit tests for the TopicResearchAgent class.

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.Agents.TopicResearchAgent import TopicResearchAgent
from src.Agents.AgentResponse import AgentResponse
from src.BibleVerse import BibleVerse

## Test cases for the TopicResearchAgent class.
class TopicResearchAgentTests(unittest.TestCase):
    ## Set up test environment before each test.
    def setUp(self):
        # Create mock dependencies
        self.mock_bible_parser = Mock()
        self.mock_llm_client = Mock()
        
        # Create agent instance
        self.agent = TopicResearchAgent(self.mock_bible_parser, self.mock_llm_client)
    
    ## Test TopicResearchAgent initialization.
    def test_Initialization(self):
        agent = TopicResearchAgent(self.mock_bible_parser, self.mock_llm_client)
        
        self.assertEqual(agent.BibleParser, self.mock_bible_parser)
        self.assertEqual(agent.LlmClient, self.mock_llm_client)
    
    ## Test successful topic research.
    def test_SuccessfulTopicResearch(self):
        # Mock LLM response for keywords
        self.mock_llm_client.GenerateResponse.return_value = "love\ncharity\nkindness\nmercy\ncompassion"
        
        # Mock Bible parser response
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8"),
            BibleVerse("KJV", "1Co", 13, 4, "Charity suffereth long, and is kind.", "1Co.13.4")
        ]
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = mock_verses
        
        # Mock LLM response for analysis
        self.mock_llm_client.GenerateResponse.side_effect = [
            "love\ncharity\nkindness\nmercy\ncompassion",  # Keywords
            "Analysis of love in the Bible..."  # Analysis
        ]
        
        # Test the research
        result = self.agent.ResearchTopic("love", "KJV", max_verses=10)
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Analysis of love in the Bible...")
        self.assertEqual(len(result.verses_used), 2)
        self.assertEqual(result.metadata["topic"], "love")
        self.assertEqual(result.metadata["translation"], "KJV")
        self.assertEqual(result.metadata["verse_count"], 2)
        self.assertEqual(result.metadata["keywords"], ["love", "charity", "kindness", "mercy", "compassion"])
        
        # Verify method calls
        self.mock_llm_client.GenerateResponse.assert_called()
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_called_once()
    
    ## Test topic research with keyword generation failure.
    def test_KeywordGenerationFailure(self):
        # Mock LLM failure for keywords
        self.mock_llm_client.GenerateResponse.return_value = None
        
        # Test the research
        result = self.agent.ResearchTopic("love", "KJV")
        
        # Verify the result
        self.assertFalse(result.success)
        self.assertEqual(result.content, "Failed to generate keywords for topic research.")
        self.assertEqual(result.verses_used, [])
        self.assertEqual(result.metadata["topic"], "love")
        
        # Verify no Bible parser calls were made
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_not_called()
    
    ## Test topic research with no verses found.
    def test_NoVersesFound(self):
        # Mock LLM response for keywords
        self.mock_llm_client.GenerateResponse.return_value = "love\ncharity"
        
        # Mock Bible parser returning no verses
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = []
        
        # Test the research
        result = self.agent.ResearchTopic("nonexistent", "KJV")
        
        # Verify the result
        self.assertFalse(result.success)
        self.assertEqual(result.content, "No relevant verses found for topic: nonexistent")
        self.assertEqual(result.verses_used, [])
        self.assertEqual(result.metadata["topic"], "nonexistent")
        self.assertEqual(result.metadata["keywords"], ["love", "charity"])
    
    ## Test topic research with analysis failure.
    def test_AnalysisFailure(self):
        # Mock LLM responses
        self.mock_llm_client.GenerateResponse.side_effect = [
            "love\ncharity",  # Keywords
            None  # Analysis fails
        ]
        
        # Mock Bible parser response
        mock_verses = [
            BibleVerse("KJV", "1Jo", 4, 8, "He that loveth not knoweth not God; for God is love.", "1Jo.4.8")
        ]
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = mock_verses
        
        # Test the research
        result = self.agent.ResearchTopic("love", "KJV")
        
        # Verify the result
        self.assertFalse(result.success)
        self.assertEqual(result.content, "Failed to analyze verses for topic research.")
        self.assertEqual(len(result.verses_used), 1)
        self.assertEqual(result.metadata["topic"], "love")
        self.assertEqual(result.metadata["keywords"], ["love", "charity"])
    
    ## Test topic research with max verses limit.
    def test_MaxVersesLimit(self):
        # Mock LLM response for keywords
        self.mock_llm_client.GenerateResponse.return_value = "love\ncharity"
        
        # Mock Bible parser returning many verses
        mock_verses = []
        for i in range(50):
            verse = BibleVerse("KJV", "1Jo", 4, i+1, f"Love verse {i+1}", f"1Jo.4.{i+1}")
            mock_verses.append(verse)
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = mock_verses
        
        # Mock LLM response for analysis
        self.mock_llm_client.GenerateResponse.side_effect = [
            "love\ncharity",  # Keywords
            "Analysis..."  # Analysis
        ]
        
        # Test with max_verses limit
        result = self.agent.ResearchTopic("love", "KJV", max_verses=10)
        
        # Verify only max_verses are used
        self.assertEqual(len(result.verses_used), 10)
        self.assertEqual(result.metadata["verse_count"], 10)
    
    ## Test topic research with different translations.
    def test_DifferentTranslations(self):
        # Mock LLM response for keywords
        self.mock_llm_client.GenerateResponse.return_value = "love\ncharity"
        
        # Mock Bible parser response
        mock_verses = [
            BibleVerse("WEB", "1Jo", 4, 8, "He who doesn't love doesn't know God, for God is love.", "1Jo.4.8")
        ]
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = mock_verses
        
        # Mock LLM response for analysis
        self.mock_llm_client.GenerateResponse.side_effect = [
            "love\ncharity",  # Keywords
            "Analysis..."  # Analysis
        ]
        
        # Test with different translation
        result = self.agent.ResearchTopic("love", "WEB")
        
        # Verify translation is passed correctly
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_called_with(
            ["love", "charity"], translation="WEB", max_results=40
        )
        self.assertEqual(result.metadata["translation"], "WEB")
    
    ## Test keyword extraction from LLM response.
    def test_KeywordExtraction(self):
        # Test various keyword response formats
        test_cases = [
            "love\ncharity\nkindness",
            "love\n\ncharity\n\nkindness",
            "love\ncharity\nkindness\n",
            "\nlove\ncharity\nkindness\n",
            "love\ncharity\nkindness\n\n\n"
        ]
        
        for keywords_response in test_cases:
            with self.subTest(keywords_response=keywords_response):
                # Mock LLM response for keywords
                self.mock_llm_client.GenerateResponse.return_value = keywords_response
                
                # Mock Bible parser response
                mock_verses = [
                    BibleVerse("KJV", "1Jo", 4, 8, "Test verse", "1Jo.4.8")
                ]
                self.mock_bible_parser.GetVersesByTopicKeywords.return_value = mock_verses
                
                # Mock LLM response for analysis
                self.mock_llm_client.GenerateResponse.side_effect = [
                    keywords_response,  # Keywords
                    "Analysis..."  # Analysis
                ]
                
                # Test the research
                result = self.agent.ResearchTopic("love", "KJV")
                
                # Verify keywords are extracted correctly
                expected_keywords = ["love", "charity", "kindness"]
                self.assertEqual(result.metadata["keywords"], expected_keywords)
    
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
            "1Jo 4:8 (KJV) - He that loveth not knoweth not God; for God is love.\n"
            "1Co 13:4 (KJV) - Charity suffereth long, and is kind."
        )
        self.assertEqual(formatted, expected)
    
    ## Test empty verse list formatting.
    def test_EmptyVerseFormatting(self):
        # Test formatting empty list
        formatted = self.agent._FormatVersesForAnalysis([])
        self.assertEqual(formatted, "")
    
    ## Test topic research with empty keywords.
    def test_EmptyKeywords(self):
        # Mock LLM response with empty keywords
        self.mock_llm_client.GenerateResponse.return_value = ""
        
        # Test the research
        result = self.agent.ResearchTopic("love", "KJV")
        
        # Should still work with empty keywords
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_called_with([], translation="KJV", max_results=40)
    
    ## Test topic research with whitespace-only keywords.
    def test_WhitespaceOnlyKeywords(self):
        # Mock LLM response with whitespace-only keywords
        self.mock_llm_client.GenerateResponse.return_value = "   \n  \n  "
        
        # Test the research
        result = self.agent.ResearchTopic("love", "KJV")
        
        # Should work with whitespace-only keywords (empty list)
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_called_with([], translation="KJV", max_results=40)

if __name__ == '__main__':
    unittest.main() 