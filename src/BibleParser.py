## @package BibleParser
## Bible Data Parser for OSIS XML format.
## Handles parsing and indexing Bible verses from multiple translations.

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass
from pathlib import Path


## Represents a single Bible verse with metadata.
@dataclass
class BibleVerse:
    translation: str
    book: str
    chapter: int
    verse: int
    text: str
    osis_id: str
    
    ## Validate and clean the verse data.
    def __post_init__(self):
        self.text = self.text.strip()
        # Remove extra whitespace and normalize
        self.text = re.sub(r'\s+', ' ', self.text)


## Parser for OSIS XML Bible data files.
class BibleParser:
    ## Initialize the Bible parser.
    ## @param[in] data_directory_path - Path to directory containing OSIS XML files.
    def __init__(self, data_directory_path: str = "data"):
        ## Path to the directory containing OSIS XML files.
        self.DataDirectoryPath: Path = Path(data_directory_path)
        ## Dictionary storing parsed Bible data organized by translation.
        self.Translations: dict[str, dict[str, list["BibleVerse"]]] = {}
        ## Index for fast verse lookup by translation and OSIS ID.
        self.VerseIndex: dict[str, "BibleVerse"] = {}
        
    ## Parse a single Bible translation file.
    ## @param[in] translation_name - Name of the translation file (e.g., 'kjv.xml').
    ## @return Dictionary mapping book names to lists of verses.
    def ParseTranslation(self, translation_name: str) -> Dict[str, List[BibleVerse]]:
        file_path = self.DataDirectoryPath / translation_name
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
            self.VerseIndex[index_key] = bible_verse
            
            verse_count += 1
            
        print(f"Parsed {verse_count} verses from {translation_name}")
        return verses_by_book
    
    ## Load all available Bible translations from the data directory.
    def LoadAllTranslations(self) -> None:
        xml_files = list(self.DataDirectoryPath.glob("*.xml"))
        
        if not xml_files:
            raise FileNotFoundError(f"No XML files found in {self.DataDirectoryPath}")
            
        for xml_file in xml_files:
            translation_name = xml_file.name
            try:
                verses_by_book = self.ParseTranslation(translation_name)
                self.Translations[translation_name] = verses_by_book
            except Exception as e:
                print(f"Error parsing {translation_name}: {e}")
                
        print(f"Successfully loaded {len(self.Translations)} translations")
    
    ## Get a specific verse by reference.
    ## @param[in] translation - Translation code (e.g., 'KJV').
    ## @param[in] book - Book name (e.g., 'Gen').
    ## @param[in] chapter - Chapter number.
    ## @param[in] verse - Verse number.
    ## @return BibleVerse object if found, None otherwise.
    def GetVerse(self, translation: str, book: str, chapter: int, verse: int) -> Optional[BibleVerse]:
        osis_id = f"{book}.{chapter}.{verse}"
        index_key = f"{translation}:{osis_id}"
        return self.VerseIndex.get(index_key)
    
    ## Search for verses containing the query text.
    ## @param[in] query - Search query (case-insensitive).
    ## @param[in] translation - Specific translation to search (None for all).
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of matching BibleVerse objects.
    def SearchVerses(self, query: str, translation: Optional[str] = None, 
                     max_results: int = 50) -> List[BibleVerse]:
        query_lower = query.lower()
        results = []
        
        translations_to_search = [translation] if translation else self.Translations.keys()
        
        for trans_name in translations_to_search:
            if trans_name not in self.Translations:
                continue
                
            for book_verses in self.Translations[trans_name].values():
                for verse in book_verses:
                    if query_lower in verse.text.lower():
                        results.append(verse)
                        if len(results) >= max_results:
                            return results
                            
        return results
    
    ## Find verses that contain any of the specified keywords.
    ## @param[in] keywords - List of keywords to search for.
    ## @param[in] translation - Specific translation to search (None for all).
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of matching BibleVerse objects.
    def GetVersesByTopicKeywords(self, keywords: List[str], 
                                   translation: Optional[str] = None,
                                   max_results: int = 50) -> List[BibleVerse]:
        keywords_lower = [kw.lower() for kw in keywords]
        results = []
        
        translations_to_search = [translation] if translation else self.Translations.keys()
        
        for trans_name in translations_to_search:
            # Handle both filename format ('kjv.xml') and code format ('KJV')
            if trans_name.endswith('.xml'):
                translation_filename = trans_name  # Already in filename format
            else:
                translation_filename = trans_name.lower() + '.xml'  # Convert code to filename

            if translation_filename not in self.Translations:
                continue

            for book_verses in self.Translations[translation_filename].values():
                for verse in book_verses:
                    verse_text_lower = verse.text.lower()
                    if any(keyword in verse_text_lower for keyword in keywords_lower):
                        results.append(verse)
                        if len(results) >= max_results:
                            return results
                                
        return results 