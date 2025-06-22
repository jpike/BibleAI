#!/usr/bin/env python3
## @package CrossReferenceAgentTests
## Unit tests for the CrossReferenceAgent class.

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.Agents.CrossReferenceAgent import CrossReferenceAgent
from src.Agents.AgentResponse import AgentResponse
from src.BibleVerse import BibleVerse

## Test cases for the CrossReferenceAgent class.
class CrossReferenceAgentTests(unittest.TestCase):
    ## Set up test environment before each test.
    def setUp(self):
        # Create mock dependencies
        self.mock_bible_parser = Mock()
        self.mock_llm_client = Mock()
        
        # Create agent instance
        self.agent = CrossReferenceAgent(self.mock_bible_parser, self.mock_llm_client)
    
    ## Test CrossReferenceAgent initialization.
    def test_Initialization(self):
        agent = CrossReferenceAgent(self.mock_bible_parser, self.mock_llm_client)
        
        self.assertEqual(agent.BibleParser, self.mock_bible_parser)
        self.assertEqual(agent.LlmClient, self.mock_llm_client)
    
    ## Test successful cross-reference finding.
    def test_SuccessfulCrossReferenceFinding(self):
        # Mock target verse
        target_verse = BibleVerse("KJV", "Joh", 3, 16, "For God so loved the world, that he gave his only begotten Son.", "Joh.3.16")
        self.mock_bible_parser.GetVerse.return_value = target_verse
        
        # Mock related verses
        related_verses = [
            BibleVerse("KJV", "1Jo", 4, 9, "In this was manifested the love of God toward us.", "1Jo.4.9"),
            BibleVerse("KJV", "Rom", 5, 8, "But God commendeth his love toward us.", "Rom.5.8")
        ]
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = related_verses
        
        # Mock LLM response for analysis
        self.mock_llm_client.GenerateResponse.return_value = "Cross-reference analysis..."
        
        # Test the cross-reference finding
        result = self.agent.FindCrossReferences("John 3:16", "KJV")
        
        # Verify the result
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Cross-reference analysis...")
        self.assertEqual(len(result.verses_used), 3)  # Target + 2 related
        self.assertEqual(result.metadata["reference"], "John 3:16")
        self.assertEqual(result.metadata["parsed"], ("John", 3, 16))
        self.assertEqual(result.metadata["related_count"], 2)
        
        # Verify method calls
        self.mock_bible_parser.GetVerse.assert_called_once_with("KJV", "John", 3, 16)
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_called_once()
        self.mock_llm_client.GenerateResponse.assert_called_once()
    
    ## Test cross-reference with unparseable reference.
    def test_UnparseableReference(self):
        # Test with invalid reference format
        result = self.agent.FindCrossReferences("Invalid Reference", "KJV")
        
        # Verify the result
        self.assertFalse(result.success)
        self.assertEqual(result.content, "Could not parse Bible reference: Invalid Reference")
        self.assertEqual(result.verses_used, [])
        self.assertEqual(result.metadata["reference"], "Invalid Reference")
        
        # Verify no Bible parser calls were made
        self.mock_bible_parser.GetVerse.assert_not_called()
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_not_called()
    
    ## Test cross-reference with verse not found.
    def test_VerseNotFound(self):
        # Mock Bible parser returning None for verse
        self.mock_bible_parser.GetVerse.return_value = None
        
        # Test the cross-reference finding
        result = self.agent.FindCrossReferences("John 999:999", "KJV")
        
        # Verify the result
        self.assertFalse(result.success)
        self.assertEqual(result.content, "Verse not found: John 999:999")
        self.assertEqual(result.verses_used, [])
        self.assertEqual(result.metadata["reference"], "John 999:999")
        self.assertEqual(result.metadata["parsed"], ("John", 999, 999))
        
        # Verify no further calls were made
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_not_called()
        self.mock_llm_client.GenerateResponse.assert_not_called()
    
    ## Test cross-reference with analysis failure.
    def test_AnalysisFailure(self):
        # Mock target verse
        target_verse = BibleVerse("KJV", "Joh", 3, 16, "For God so loved the world.", "Joh.3.16")
        self.mock_bible_parser.GetVerse.return_value = target_verse
        
        # Mock related verses
        related_verses = [
            BibleVerse("KJV", "1Jo", 4, 9, "In this was manifested the love of God.", "1Jo.4.9")
        ]
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = related_verses
        
        # Mock LLM failure
        self.mock_llm_client.GenerateResponse.return_value = None
        
        # Test the cross-reference finding
        result = self.agent.FindCrossReferences("John 3:16", "KJV")
        
        # Verify the result
        self.assertFalse(result.success)
        self.assertEqual(result.content, "Failed to analyze cross-references.")
        self.assertEqual(len(result.verses_used), 2)  # Target + 1 related
        self.assertEqual(result.metadata["reference"], "John 3:16")
    
    ## Test reference parsing with different formats.
    def test_ReferenceParsing(self):
        test_cases = [
            ("John 3:16", ("John", 3, 16)),
            ("Genesis 1:1", ("Genesis", 1, 1)),
            ("1 John 4:8", ("1 John", 4, 8)),
            ("2 Corinthians 13:14", ("2 Corinthians", 13, 14)),
            ("Psalm 23:1", ("Psalm", 23, 1)),
            ("Revelation 22:21", ("Revelation", 22, 21))
        ]
        
        for reference, expected in test_cases:
            with self.subTest(reference=reference):
                parsed = self.agent._ParseReference(reference)
                self.assertEqual(parsed, expected)
    
    ## Test reference parsing with invalid formats.
    def test_InvalidReferenceParsing(self):
        invalid_references = [
            "Invalid",
            "John",
            "3:16",
            "John 3",
            "John :16",
            "John 3:",
            "John 3:16:",
            "John 3:16:17"
        ]
        
        for reference in invalid_references:
            with self.subTest(reference=reference):
                parsed = self.agent._ParseReference(reference)
                self.assertIsNone(parsed)
    
    ## Test key term extraction.
    def test_KeyTermExtraction(self):
        test_cases = [
            ("For God so loved the world", ["world"]),
            ("In the beginning God created", ["beginning", "created"]),
            ("The Lord is my shepherd", ["shepherd"]),
            ("Blessed are the meek", ["Blessed", "meek"]),
            ("Love is patient and kind", ["patient", "kind"])
        ]
        
        for text, expected_terms in test_cases:
            with self.subTest(text=text):
                terms = self.agent._ExtractKeyTerms(text)
                # Check that all expected terms are present (order may vary)
                for term in expected_terms:
                    self.assertIn(term.lower(), [t.lower() for t in terms])
    
    ## Test key term extraction with common words filtering.
    def test_KeyTermExtractionWithCommonWords(self):
        text = "which that this with from they have were said unto them will shall"
        terms = self.agent._ExtractKeyTerms(text)
        
        # Should filter out common words
        common_words = {'which', 'that', 'this', 'with', 'from', 'they', 'have', 'were', 'said', 'unto', 'them', 'will', 'shall'}
        for word in common_words:
            self.assertNotIn(word, terms)
    
    ## Test key term extraction with short words.
    def test_KeyTermExtractionWithShortWords(self):
        text = "a an the in on at to for of with by"
        terms = self.agent._ExtractKeyTerms(text)
        
        # Should filter out short words (less than 4 characters)
        self.assertEqual(len(terms), 0)
    
    ## Test related verse finding.
    def test_RelatedVerseFinding(self):
        # Mock target verse
        target_verse = BibleVerse("KJV", "Joh", 3, 16, "For God so loved the world.", "Joh.3.16")
        
        # Mock related verses
        related_verses = [
            BibleVerse("KJV", "1Jo", 4, 9, "In this was manifested the love of God.", "1Jo.4.9"),
            BibleVerse("KJV", "Rom", 5, 8, "But God commendeth his love toward us.", "Rom.5.8")
        ]
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = related_verses
        
        # Test related verse finding
        result = self.agent._FindRelatedVerses(target_verse, "KJV", max_related=5)
        
        # Should return related verses (excluding target)
        self.assertEqual(len(result), 2)
        self.assertNotIn(target_verse, result)
        
        # Verify Bible parser was called with extracted terms
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_called_once()
        call_args = self.mock_bible_parser.GetVersesByTopicKeywords.call_args
        self.assertEqual(call_args[1]["translation"], "KJV")
        self.assertEqual(call_args[1]["max_results"], 10)  # 5 * 2
    
    ## Test related verse finding with target verse in results.
    def test_RelatedVerseFindingWithTargetInResults(self):
        # Mock target verse
        target_verse = BibleVerse("KJV", "Joh", 3, 16, "For God so loved the world.", "Joh.3.16")
        
        # Mock related verses including the target
        related_verses = [
            target_verse,  # Target verse included in results
            BibleVerse("KJV", "1Jo", 4, 9, "In this was manifested the love of God.", "1Jo.4.9")
        ]
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = related_verses
        
        # Test related verse finding
        result = self.agent._FindRelatedVerses(target_verse, "KJV", max_related=5)
        
        # Should filter out target verse
        self.assertEqual(len(result), 1)
        self.assertNotIn(target_verse, result)
    
    ## Test verse formatting for analysis.
    def test_VerseFormatting(self):
        # Create test verses
        verses = [
            BibleVerse("KJV", "Joh", 3, 16, "For God so loved the world.", "Joh.3.16"),
            BibleVerse("KJV", "1Jo", 4, 9, "In this was manifested the love of God.", "1Jo.4.9")
        ]
        
        # Test the formatting method
        formatted = self.agent._FormatVersesForAnalysis(verses)
        
        expected = (
            "Joh 3:16 - For God so loved the world.\n"
            "1Jo 4:9 - In this was manifested the love of God."
        )
        self.assertEqual(formatted, expected)
    
    ## Test empty verse list formatting.
    def test_EmptyVerseFormatting(self):
        # Test formatting empty list
        formatted = self.agent._FormatVersesForAnalysis([])
        self.assertEqual(formatted, "")
    
    ## Test cross-reference with no related verses.
    def test_NoRelatedVerses(self):
        # Mock target verse
        target_verse = BibleVerse("KJV", "Joh", 3, 16, "For God so loved the world.", "Joh.3.16")
        self.mock_bible_parser.GetVerse.return_value = target_verse
        
        # Mock no related verses
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = []
        
        # Mock LLM response for analysis
        self.mock_llm_client.GenerateResponse.return_value = "Analysis with no related verses..."
        
        # Test the cross-reference finding
        result = self.agent.FindCrossReferences("John 3:16", "KJV")
        
        # Should still succeed but with no related verses
        self.assertTrue(result.success)
        self.assertEqual(len(result.verses_used), 1)  # Only target verse
        self.assertEqual(result.metadata["related_count"], 0)
    
    ## Test cross-reference with different translations.
    def test_DifferentTranslations(self):
        # Mock target verse
        target_verse = BibleVerse("WEB", "Joh", 3, 16, "For God so loved the world.", "Joh.3.16")
        self.mock_bible_parser.GetVerse.return_value = target_verse
        
        # Mock related verses
        related_verses = [
            BibleVerse("WEB", "1Jo", 4, 9, "In this was manifested the love of God.", "1Jo.4.9")
        ]
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = related_verses
        
        # Mock LLM response for analysis
        self.mock_llm_client.GenerateResponse.return_value = "Analysis..."
        
        # Test with different translation
        result = self.agent.FindCrossReferences("John 3:16", "WEB")
        
        # Verify translation is passed correctly
        self.mock_bible_parser.GetVerse.assert_called_with("WEB", "John", 3, 16)
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_called_with(
            Mock(), translation="WEB", max_results=30
        )

if __name__ == '__main__':
    unittest.main() 