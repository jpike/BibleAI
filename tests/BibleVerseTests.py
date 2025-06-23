#!/usr/bin/env python3
## @package BibleVerseTests
## Unit tests for the BibleVerse dataclass.

import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BibleVerse import BibleVerse

## Test cases for the BibleVerse dataclass.
class BibleVerseTests(unittest.TestCase):
    ## Test basic BibleVerse initialization.
    def test_BasicInitialization(self):
        verse = BibleVerse(
            translation="KJV",
            book="Gen",
            chapter=1,
            verse=1,
            text="In the beginning God created the heaven and the earth.",
            osis_id="Gen.1.1"
        )
        
        self.assertEqual(verse.translation, "KJV")
        self.assertEqual(verse.book, "Gen")
        self.assertEqual(verse.chapter, 1)
        self.assertEqual(verse.verse, 1)
        self.assertEqual(verse.text, "In the beginning God created the heaven and the earth.")
        self.assertEqual(verse.osis_id, "Gen.1.1")
    
    ## Test text cleaning functionality.
    def test_TextCleaning(self):
        # Test with extra whitespace
        verse = BibleVerse(
            translation="KJV",
            book="Gen",
            chapter=1,
            verse=1,
            text="  In the beginning   God created   the heaven and the earth.  ",
            osis_id="Gen.1.1"
        )
        
        # Text should be cleaned of extra whitespace
        expected_text = "In the beginning God created the heaven and the earth."
        self.assertEqual(verse.text, expected_text)
    
    ## Test text normalization with multiple spaces and tabs.
    def test_TextNormalization(self):
        verse = BibleVerse(
            translation="KJV",
            book="Gen",
            chapter=1,
            verse=1,
            text="In\tthe\t\tbeginning\nGod\tcreated\tthe\theaven\tand\tthe\tearth.",
            osis_id="Gen.1.1"
        )
        
        # Text should be normalized to single spaces
        expected_text = "In the beginning God created the heaven and the earth."
        self.assertEqual(verse.text, expected_text)
    
    ## Test with empty text.
    def test_EmptyText(self):
        verse = BibleVerse(
            translation="KJV",
            book="Gen",
            chapter=1,
            verse=1,
            text="",
            osis_id="Gen.1.1"
        )
        
        # Empty text should remain empty after cleaning
        self.assertEqual(verse.text, "")
    
    ## Test with whitespace-only text.
    def test_WhitespaceOnlyText(self):
        verse = BibleVerse(
            translation="KJV",
            book="Gen",
            chapter=1,
            verse=1,
            text="   \t\n   ",
            osis_id="Gen.1.1"
        )
        
        # Whitespace-only text should become empty
        self.assertEqual(verse.text, "")
    
    ## Test with special characters in text.
    def test_SpecialCharacters(self):
        verse = BibleVerse(
            translation="KJV",
            book="Gen",
            chapter=1,
            verse=1,
            text="In the beginning God created the heaven & earth.",
            osis_id="Gen.1.1"
        )
        
        # Special characters should be preserved
        self.assertEqual(verse.text, "In the beginning God created the heaven & earth.")
    
    ## Test with different translation codes.
    def test_DifferentTranslations(self):
        translations = ["KJV", "WEB", "YLT", "NIV", "ESV"]
        
        for translation in translations:
            verse = BibleVerse(
                translation=translation,
                book="Gen",
                chapter=1,
                verse=1,
                text="Test verse.",
                osis_id="Gen.1.1"
            )
            self.assertEqual(verse.translation, translation)
    
    ## Test with different book names.
    def test_DifferentBooks(self):
        books = ["Gen", "Exo", "Lev", "Num", "Deu", "Mat", "Mar", "Luk", "Joh"]
        
        for book in books:
            verse = BibleVerse(
                translation="KJV",
                book=book,
                chapter=1,
                verse=1,
                text="Test verse.",
                osis_id=f"{book}.1.1"
            )
            self.assertEqual(verse.book, book)
    
    ## Test with large chapter and verse numbers.
    def test_LargeNumbers(self):
        verse = BibleVerse(
            translation="KJV",
            book="Psa",
            chapter=119,
            verse=176,
            text="Test verse.",
            osis_id="Psa.119.176"
        )
        
        self.assertEqual(verse.chapter, 119)
        self.assertEqual(verse.verse, 176)
    
    ## Test dataclass equality.
    def test_Equality(self):
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
            verse=1,
            text="In the beginning God created the heaven and the earth.",
            osis_id="Gen.1.1"
        )
        
        self.assertEqual(verse1, verse2)
    
    ## Test dataclass inequality.
    def test_Inequality(self):
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
        
        self.assertNotEqual(verse1, verse2)

if __name__ == '__main__':
    unittest.main() 