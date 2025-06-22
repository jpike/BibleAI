#!/usr/bin/env python3
## @package AgentResponseTests
## Unit tests for the AgentResponse dataclass.

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.Agents.AgentResponse import AgentResponse
from src.BibleVerse import BibleVerse

## Test cases for the AgentResponse dataclass.
class AgentResponseTests(unittest.TestCase):
    ## Test basic AgentResponse initialization.
    def test_BasicInitialization(self):
        response = AgentResponse(
            success=True,
            content="Test response content",
            verses_used=[],
            metadata={"key": "value"}
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Test response content")
        self.assertEqual(response.verses_used, [])
        self.assertEqual(response.metadata, {"key": "value"})
    
    ## Test AgentResponse with Bible verses.
    def test_WithBibleVerses(self):
        verse1 = BibleVerse(
            translation="KJV",
            book="Gen",
            chapter=1,
            verse=1,
            text="In the beginning God created the heaven and the earth.",
            osis_id="Gen.1.1"
        )
        
        verse2 = BibleVerse(
            translation="KJV",
            book="Gen",
            chapter=1,
            verse=2,
            text="And the earth was without form, and void.",
            osis_id="Gen.1.2"
        )
        
        response = AgentResponse(
            success=True,
            content="Research results",
            verses_used=[verse1, verse2],
            metadata={"topic": "creation", "verse_count": 2}
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Research results")
        self.assertEqual(len(response.verses_used), 2)
        self.assertEqual(response.verses_used[0].osis_id, "Gen.1.1")
        self.assertEqual(response.verses_used[1].osis_id, "Gen.1.2")
        self.assertEqual(response.metadata["topic"], "creation")
        self.assertEqual(response.metadata["verse_count"], 2)
    
    ## Test failed response.
    def test_FailedResponse(self):
        response = AgentResponse(
            success=False,
            content="Error: Could not find relevant verses",
            verses_used=[],
            metadata={"error": "no_results"}
        )
        
        self.assertFalse(response.success)
        self.assertEqual(response.content, "Error: Could not find relevant verses")
        self.assertEqual(response.verses_used, [])
        self.assertEqual(response.metadata["error"], "no_results")
    
    ## Test empty content.
    def test_EmptyContent(self):
        response = AgentResponse(
            success=True,
            content="",
            verses_used=[],
            metadata={}
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.content, "")
        self.assertEqual(response.verses_used, [])
        self.assertEqual(response.metadata, {})
    
    ## Test complex metadata.
    def test_ComplexMetadata(self):
        metadata = {
            "topic": "love",
            "translation": "KJV",
            "keywords": ["love", "charity", "kindness"],
            "search_time": 1.5,
            "results_count": 15,
            "nested": {
                "level1": {
                    "level2": "value"
                }
            }
        }
        
        response = AgentResponse(
            success=True,
            content="Complex response",
            verses_used=[],
            metadata=metadata
        )
        
        self.assertEqual(response.metadata["topic"], "love")
        self.assertEqual(response.metadata["keywords"], ["love", "charity", "kindness"])
        self.assertEqual(response.metadata["search_time"], 1.5)
        self.assertEqual(response.metadata["nested"]["level1"]["level2"], "value")
    
    ## Test dataclass equality.
    def test_Equality(self):
        response1 = AgentResponse(
            success=True,
            content="Test content",
            verses_used=[],
            metadata={"key": "value"}
        )
        
        response2 = AgentResponse(
            success=True,
            content="Test content",
            verses_used=[],
            metadata={"key": "value"}
        )
        
        self.assertEqual(response1, response2)
    
    ## Test dataclass inequality.
    def test_Inequality(self):
        response1 = AgentResponse(
            success=True,
            content="Test content",
            verses_used=[],
            metadata={"key": "value"}
        )
        
        response2 = AgentResponse(
            success=False,
            content="Different content",
            verses_used=[],
            metadata={"key": "value"}
        )
        
        self.assertNotEqual(response1, response2)
    
    ## Test with large number of verses.
    def test_LargeVerseList(self):
        verses = []
        for i in range(100):
            verse = BibleVerse(
                translation="KJV",
                book="Gen",
                chapter=1,
                verse=i + 1,
                text=f"Verse {i + 1}",
                osis_id=f"Gen.1.{i + 1}"
            )
            verses.append(verse)
        
        response = AgentResponse(
            success=True,
            content="Large response",
            verses_used=verses,
            metadata={"verse_count": 100}
        )
        
        self.assertEqual(len(response.verses_used), 100)
        self.assertEqual(response.metadata["verse_count"], 100)
    
    ## Test metadata access patterns.
    def test_MetadataAccessPatterns(self):
        response = AgentResponse(
            success=True,
            content="Test",
            verses_used=[],
            metadata={
                "string_value": "test",
                "int_value": 42,
                "float_value": 3.14,
                "bool_value": True,
                "list_value": [1, 2, 3],
                "dict_value": {"nested": "value"}
            }
        )
        
        # Test different data types in metadata
        self.assertEqual(response.metadata["string_value"], "test")
        self.assertEqual(response.metadata["int_value"], 42)
        self.assertEqual(response.metadata["float_value"], 3.14)
        self.assertTrue(response.metadata["bool_value"])
        self.assertEqual(response.metadata["list_value"], [1, 2, 3])
        self.assertEqual(response.metadata["dict_value"]["nested"], "value")

if __name__ == '__main__':
    unittest.main() 