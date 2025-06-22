#!/usr/bin/env python3
## @package BibleParserTests
## Unit tests for the BibleParser class.

import unittest
import sys
import os
import tempfile
import shutil
import pathlib
import xml.etree.ElementTree as ET
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.BibleParser import BibleParser
from src.BibleVerse import BibleVerse

## Test cases for the BibleParser class.
class BibleParserTests(unittest.TestCase):
    ## Set up test environment before each test.
    def setUp(self):
        # Create a temporary directory for test data
        self.test_data_dir = pathlib.Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Create BibleVerses subdirectory to match new structure
        self.test_bible_verses_dir = self.test_data_dir / "BibleVerses"
        self.test_bible_verses_dir.mkdir(exist_ok=True)
        
        # Create test XML files
        self._CreateTestXmlFiles()
        
        # Initialize parser
        self.parser = BibleParser(str(self.test_data_dir))
    
    ## Clean up test environment after each test.
    def tearDown(self):
        # Remove temporary directory
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
    
    ## Create test XML files for testing.
    def _CreateTestXmlFiles(self):
        # Create a simple test XML file
        test_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
    <osisText>
        <div type="book" osisID="Gen">
            <chapter osisID="Gen.1">
                <verse osisID="Gen.1.1">In the beginning God created the heaven and the earth.</verse>
                <verse osisID="Gen.1.2">And the earth was without form, and void.</verse>
                <verse osisID="Gen.1.3">And God said, Let there be light: and there was light.</verse>
            </chapter>
            <chapter osisID="Gen.2">
                <verse osisID="Gen.2.1">Thus the heavens and the earth were finished.</verse>
                <verse osisID="Gen.2.2">And on the seventh day God ended his work.</verse>
            </chapter>
        </div>
        <div type="book" osisID="Exo">
            <chapter osisID="Exo.1">
                <verse osisID="Exo.1.1">Now these are the names of the children of Israel.</verse>
                <verse osisID="Exo.1.2">Reuben, Simeon, Levi, and Judah.</verse>
            </chapter>
        </div>
    </osisText>
</osis>'''
        
        # Write test XML file
        test_file_path = self.test_bible_verses_dir / "test.xml"
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_xml_content)
        
        # Create another test file with different content
        test2_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
    <osisText>
        <div type="book" osisID="Mat">
            <chapter osisID="Mat.1">
                <verse osisID="Mat.1.1">The book of the generation of Jesus Christ.</verse>
                <verse osisID="Mat.1.2">Abraham begat Isaac; and Isaac begat Jacob.</verse>
            </chapter>
        </div>
    </osisText>
</osis>'''
        
        test2_file_path = self.test_bible_verses_dir / "test2.xml"
        with open(test2_file_path, 'w', encoding='utf-8') as f:
            f.write(test2_xml_content)
    
    ## Test BibleParser initialization.
    def test_Initialization(self):
        parser = BibleParser("test_data")
        self.assertEqual(parser.DataDirectoryPath, pathlib.Path("test_data"))
        self.assertEqual(parser.Translations, {})
        self.assertEqual(parser.VerseIndex, {})
    
    ## Test parsing a single translation file.
    def test_ParseTranslation(self):
        result = self.parser.ParseTranslation("test.xml")
        
        # Check that we got the expected books
        self.assertIn("Gen", result)
        self.assertIn("Exo", result)
        
        # Check verse counts
        self.assertEqual(len(result["Gen"]), 5)  # 3 from Gen.1 + 2 from Gen.2
        self.assertEqual(len(result["Exo"]), 2)
        
        # Check first verse details
        first_verse = result["Gen"][0]
        self.assertEqual(first_verse.translation, "TEST")
        self.assertEqual(first_verse.book, "Gen")
        self.assertEqual(first_verse.chapter, 1)
        self.assertEqual(first_verse.verse, 1)
        self.assertEqual(first_verse.text, "In the beginning God created the heaven and the earth.")
        self.assertEqual(first_verse.osis_id, "Gen.1.1")
    
    ## Test parsing non-existent file.
    def test_ParseNonExistentFile(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.ParseTranslation("nonexistent.xml")
    
    ## Test loading all translations.
    def test_LoadAllTranslations(self):
        self.parser.LoadAllTranslations()
        
        # Should have loaded both test files
        self.assertIn("test.xml", self.parser.Translations)
        self.assertIn("test2.xml", self.parser.Translations)
        
        # Check total verses loaded
        total_verses = sum(len(verses) for verses in self.parser.Translations.values())
        self.assertEqual(total_verses, 7)  # 5 from test.xml + 2 from test2.xml
    
    ## Test getting a specific verse.
    def test_GetVerse(self):
        # First load the translation
        self.parser.ParseTranslation("test.xml")
        
        # Test getting existing verse
        verse = self.parser.GetVerse("TEST", "Gen", 1, 1)
        self.assertIsNotNone(verse)
        if verse is not None:  # Add null check for linter
            self.assertEqual(verse.text, "In the beginning God created the heaven and the earth.")
        
        # Test getting non-existent verse
        verse = self.parser.GetVerse("TEST", "Gen", 1, 999)
        self.assertIsNone(verse)
    
    ## Test searching for verses.
    def test_SearchVerses(self):
        # First load the translation
        self.parser.ParseTranslation("test.xml")
        
        # Search for "God"
        results = self.parser.SearchVerses("God", translation="test.xml")
        self.assertGreater(len(results), 0)
        
        # All results should contain "God"
        for verse in results:
            self.assertIn("God", verse.text)
        
        # Search for non-existent text
        results = self.parser.SearchVerses("nonexistent", translation="test.xml")
        self.assertEqual(len(results), 0)
    
    ## Test searching with max results limit.
    def test_SearchWithMaxResults(self):
        # First load the translation
        self.parser.ParseTranslation("test.xml")
        
        # Search with max results limit
        results = self.parser.SearchVerses("the", translation="test.xml", max_results=2)
        self.assertLessEqual(len(results), 2)
    
    ## Test getting verses by topic keywords.
    def test_GetVersesByTopicKeywords(self):
        # First load the translation
        self.parser.ParseTranslation("test.xml")
        
        # Search for verses containing keywords
        keywords = ["God", "earth"]
        results = self.parser.GetVersesByTopicKeywords(keywords, translation="test.xml")
        self.assertGreater(len(results), 0)
        
        # All results should contain at least one keyword
        for verse in results:
            verse_text_lower = verse.text.lower()
            has_keyword = any(keyword.lower() in verse_text_lower for keyword in keywords)
            self.assertTrue(has_keyword)
    
    ## Test getting verses by topic keywords with translation code.
    def test_GetVersesByTopicKeywordsWithCode(self):
        # First load the translation
        self.parser.ParseTranslation("test.xml")
        
        # Search using translation code instead of filename
        keywords = ["God"]
        results = self.parser.GetVersesByTopicKeywords(keywords, translation="TEST")
        self.assertGreater(len(results), 0)
    
    ## Test verse index functionality.
    def test_VerseIndex(self):
        # First load the translation
        self.parser.ParseTranslation("test.xml")
        
        # Check that verses are indexed
        self.assertGreater(len(self.parser.VerseIndex), 0)
        
        # Check specific index entry
        index_key = "TEST:Gen.1.1"
        self.assertIn(index_key, self.parser.VerseIndex)
        
        verse = self.parser.VerseIndex[index_key]
        self.assertEqual(verse.text, "In the beginning God created the heaven and the earth.")
    
    ## Test case-insensitive search.
    def test_CaseInsensitiveSearch(self):
        # First load the translation
        self.parser.ParseTranslation("test.xml")
        
        # Search with different cases
        results1 = self.parser.SearchVerses("GOD", translation="test.xml")
        results2 = self.parser.SearchVerses("god", translation="test.xml")
        results3 = self.parser.SearchVerses("God", translation="test.xml")
        
        # All should return the same results
        self.assertEqual(len(results1), len(results2))
        self.assertEqual(len(results2), len(results3))
    
    ## Test search across multiple translations.
    def test_SearchMultipleTranslations(self):
        # Load both translations
        self.parser.LoadAllTranslations()
        
        # Search across all translations
        results = self.parser.SearchVerses("the")
        self.assertGreater(len(results), 0)
        
        # Results should come from different translations
        translations_found = set(verse.translation for verse in results)
        self.assertGreater(len(translations_found), 1)
    
    ## Test invalid OSIS ID handling.
    def test_InvalidOsisId(self):
        # Create XML with invalid OSIS ID
        invalid_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
    <osisText>
        <div type="book" osisID="Gen">
            <chapter osisID="Gen.1">
                <verse osisID="invalid">Invalid verse</verse>
                <verse osisID="Gen.1.1">Valid verse</verse>
            </chapter>
        </div>
    </osisText>
</osis>'''
        
        invalid_file_path = self.test_bible_verses_dir / "invalid.xml"
        with open(invalid_file_path, 'w', encoding='utf-8') as f:
            f.write(invalid_xml_content)
        
        # Parse should handle invalid OSIS ID gracefully
        result = self.parser.ParseTranslation("invalid.xml")
        self.assertIn("Gen", result)
        self.assertEqual(len(result["Gen"]), 1)  # Only the valid verse should be included
    
    ## Test empty verse text handling.
    def test_EmptyVerseText(self):
        # Create XML with empty verse text
        empty_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
    <osisText>
        <div type="book" osisID="Gen">
            <chapter osisID="Gen.1">
                <verse osisID="Gen.1.1"></verse>
                <verse osisID="Gen.1.2">Valid verse</verse>
            </chapter>
        </div>
    </osisText>
</osis>'''
        
        empty_file_path = self.test_bible_verses_dir / "empty.xml"
        with open(empty_file_path, 'w', encoding='utf-8') as f:
            f.write(empty_xml_content)
        
        # Parse should handle empty text gracefully
        result = self.parser.ParseTranslation("empty.xml")
        self.assertIn("Gen", result)
        self.assertEqual(len(result["Gen"]), 1)  # Only the valid verse should be included

if __name__ == '__main__':
    unittest.main() 