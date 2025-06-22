"""
Bible Data Parser for OSIS XML format.
Handles parsing and indexing Bible verses from multiple translations.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BibleVerse:
    """Represents a single Bible verse with metadata."""
    translation: str
    book: str
    chapter: int
    verse: int
    text: str
    osis_id: str
    
    def __post_init__(self):
        """Validate and clean the verse data."""
        self.text = self.text.strip()
        # Remove extra whitespace and normalize
        self.text = re.sub(r'\s+', ' ', self.text)


class BibleParser:
    """Parser for OSIS XML Bible data files."""
    
    def __init__(self, data_directory: str = "data"):
        """
        Initialize the Bible parser.
        
        Args:
            data_directory: Path to directory containing OSIS XML files.
        """
        self.data_directory = Path(data_directory)
        self.translations = {}  # Store parsed data by translation
        self.verse_index = {}   # Index for fast verse lookup
        
    def parse_translation(self, translation_name: str) -> Dict[str, List[BibleVerse]]:
        """
        Parse a single Bible translation file.
        
        Args:
            translation_name: Name of the translation file (e.g., 'kjv.xml').
            
        Returns:
            Dictionary mapping book names to lists of verses.
        """
        file_path = self.data_directory / translation_name
        if not file_path.exists():
            raise FileNotFoundError(f"Translation file not found: {file_path}")
            
        print(f"Parsing {translation_name}...")
        
        # Parse XML file
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Define the OSIS namespace
        osis_namespace = {'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace'}
        
        # Extract translation name from filename
        translation_code = translation_name.replace('.xml', '').upper()
        
        verses_by_book = {}
        verse_count = 0
        
        # Find all verse elements using the correct namespace and recursive search
        for verse_elem in root.findall('.//osis:verse', osis_namespace):
            osis_id = verse_elem.get('osisID', '')
            text = verse_elem.text or ''
            
            if not osis_id or not text.strip():
                continue
                
            # Parse OSIS ID (e.g., 'Gen.1.1')
            parts = osis_id.split('.')
            if len(parts) != 3:
                continue
                
            book, chapter_str, verse_str = parts
            
            try:
                chapter = int(chapter_str)
                verse = int(verse_str)
            except ValueError:
                continue
                
            # Create BibleVerse object
            bible_verse = BibleVerse(
                translation=translation_code,
                book=book,
                chapter=chapter,
                verse=verse,
                text=text,
                osis_id=osis_id
            )
            
            # Store by book
            if book not in verses_by_book:
                verses_by_book[book] = []
            verses_by_book[book].append(bible_verse)
            
            # Add to global index
            index_key = f"{translation_code}:{osis_id}"
            self.verse_index[index_key] = bible_verse
            
            verse_count += 1
            
        print(f"Parsed {verse_count} verses from {translation_name}")
        return verses_by_book
    
    def load_all_translations(self) -> None:
        """Load all available Bible translations from the data directory."""
        xml_files = list(self.data_directory.glob("*.xml"))
        
        if not xml_files:
            raise FileNotFoundError(f"No XML files found in {self.data_directory}")
            
        for xml_file in xml_files:
            translation_name = xml_file.name
            try:
                verses_by_book = self.parse_translation(translation_name)
                self.translations[translation_name] = verses_by_book
            except Exception as e:
                print(f"Error parsing {translation_name}: {e}")
                
        print(f"Successfully loaded {len(self.translations)} translations")
    
    def get_verse(self, translation: str, book: str, chapter: int, verse: int) -> Optional[BibleVerse]:
        """
        Get a specific verse by reference.
        
        Args:
            translation: Translation code (e.g., 'KJV').
            book: Book name (e.g., 'Gen').
            chapter: Chapter number.
            verse: Verse number.
            
        Returns:
            BibleVerse object if found, None otherwise.
        """
        osis_id = f"{book}.{chapter}.{verse}"
        index_key = f"{translation}:{osis_id}"
        return self.verse_index.get(index_key)
    
    def search_verses(self, query: str, translation: Optional[str] = None, 
                     max_results: int = 50) -> List[BibleVerse]:
        """
        Search for verses containing the query text.
        
        Args:
            query: Search query (case-insensitive).
            translation: Specific translation to search (None for all).
            max_results: Maximum number of results to return.
            
        Returns:
            List of matching BibleVerse objects.
        """
        query_lower = query.lower()
        results = []
        
        translations_to_search = [translation] if translation else self.translations.keys()
        
        for trans_name in translations_to_search:
            if trans_name not in self.translations:
                continue
                
            for book_verses in self.translations[trans_name].values():
                for verse in book_verses:
                    if query_lower in verse.text.lower():
                        results.append(verse)
                        if len(results) >= max_results:
                            return results
                            
        return results
    
    def get_verses_by_topic_keywords(self, keywords: List[str], 
                                   translation: Optional[str] = None,
                                   max_results: int = 50) -> List[BibleVerse]:
        """
        Find verses that contain any of the specified keywords.
        
        Args:
            keywords: List of keywords to search for.
            translation: Specific translation to search (None for all).
            max_results: Maximum number of results to return.
            
        Returns:
            List of matching BibleVerse objects.
        """
        keywords_lower = [kw.lower() for kw in keywords]
        results = []
        
        translations_to_search = [translation] if translation else self.translations.keys()
        
        for trans_name in translations_to_search:
            translation_filename = trans_name.lower() + '.xml'
            if translation_filename not in self.translations:
                continue
                
            for book_verses in self.translations[translation_filename].values():
                for verse in book_verses:
                    verse_text_lower = verse.text.lower()
                    if any(keyword in verse_text_lower for keyword in keywords_lower):
                        results.append(verse)
                        if len(results) >= max_results:
                            return results
                            
        return results 