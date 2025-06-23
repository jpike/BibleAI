## @package StudyNotesParser
## Parser for Bible study notes from hierarchical folder structure.

import pathlib
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

# Study Notes Constants
DEFAULT_SEARCH_MAX_RESULTS = 20

## Represents a parsed study note with metadata.
@dataclass
class StudyNote:
    ## File path to the study note.
    file_path: str
    ## Content of the study note.
    content: str
    ## Book name (e.g., "Revelation").
    book: str
    ## Testament (e.g., "NewTestament").
    testament: str
    ## Chapter/topic information extracted from filename.
    chapter_topic: str
    ## Full filename for reference.
    filename: str
    ## Line count for content analysis.
    line_count: int

## Parser for Bible study notes from hierarchical folder structure.
class StudyNotesParser:
    ## Initialize the study notes parser.
    ## @param[in] data_directory_path - Path to directory containing BibleStudyNotes.
    def __init__(self, data_directory_path: str = "data"):
        ## Path to the directory containing Bible study notes.
        self.DataDirectoryPath: pathlib.Path = pathlib.Path(data_directory_path)
        ## Path to the BibleStudyNotes subdirectory.
        self.StudyNotesPath: pathlib.Path = self.DataDirectoryPath / "BibleStudyNotes"
        ## Dictionary storing parsed study notes organized by book.
        self.StudyNotes: Dict[str, List[StudyNote]] = {}
        ## List of all study notes for searching.
        self.AllStudyNotes: List[StudyNote] = []
        
    ## Load all study notes from the hierarchical directory structure.
    def LoadAllStudyNotes(self) -> None:
        study_notes_directory_exists = self.StudyNotesPath.exists()
        if not study_notes_directory_exists:
            raise FileNotFoundError(f"BibleStudyNotes directory not found: {self.StudyNotesPath}")
            
        print("Loading Bible study notes...")
        
        # Find all .txt files in the hierarchical structure
        txt_files = list(self.StudyNotesPath.rglob("*.txt"))
        
        if not txt_files:
            print("No .txt files found in BibleStudyNotes directory")
            return
            
        for txt_file in txt_files:
            try:
                study_note = self._ParseStudyNoteFile(txt_file)
                if study_note:
                    # Organize by book
                    if study_note.book not in self.StudyNotes:
                        self.StudyNotes[study_note.book] = []
                    self.StudyNotes[study_note.book].append(study_note)
                    self.AllStudyNotes.append(study_note)
            except Exception as e:
                print(f"Error parsing {txt_file}: {e}")
                
        print(f"Successfully loaded {len(self.AllStudyNotes)} study notes from {len(self.StudyNotes)} books")
    
    ## Parse a single study note file.
    ## @param[in] file_path - Path to the .txt file to parse.
    ## @return StudyNote object if successful, None otherwise.
    def _ParseStudyNoteFile(self, file_path: pathlib.Path) -> Optional[StudyNote]:
        file_exists = file_path.exists()
        if not file_exists:
            return None
            
        # Extract metadata from file path
        metadata = self._ExtractMetadataFromPath(file_path)
        if not metadata:
            return None
            
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
            
        # Skip empty files
        if not content:
            return None
            
        # Count lines for content analysis
        line_count = len(content.split('\n'))
        
        return StudyNote(
            file_path=str(file_path),
            content=content,
            book=metadata['book'],
            testament=metadata['testament'],
            chapter_topic=metadata['chapter_topic'],
            filename=file_path.name,
            line_count=line_count
        )
    
    ## Extract metadata from file path structure.
    ## @param[in] file_path - Path to extract metadata from.
    ## @return Dictionary with book, testament, and chapter_topic information.
    def _ExtractMetadataFromPath(self, file_path: pathlib.Path) -> Optional[Dict[str, str]]:
        # Expected structure: data/BibleStudyNotes/Books/NewTestament/Revelation/filename.txt
        parts = file_path.parts
        
        # Find the relevant parts in the path
        try:
            # Look for "Books" directory
            books_index = parts.index("Books")
            if books_index + 3 >= len(parts):  # Need at least testament, book, filename
                return None
                
            testament = parts[books_index + 1]  # e.g., "NewTestament"
            book = parts[books_index + 2]       # e.g., "Revelation"
            
            # Extract chapter/topic from filename
            filename = parts[-1]  # e.g., "1 - Revelation 1 - Introduction.txt"
            chapter_topic = self._ExtractChapterTopicFromFilename(filename)
            
            return {
                'book': book,
                'testament': testament,
                'chapter_topic': chapter_topic
            }
        except (ValueError, IndexError):
            return None
    
    ## Extract chapter/topic information from filename.
    ## @param[in] filename - Filename to extract information from.
    ## @return Chapter/topic string.
    def _ExtractChapterTopicFromFilename(self, filename: str) -> str:
        # Remove .txt extension
        name_without_ext = filename.replace('.txt', '')
        
        # Try to extract meaningful information
        # Examples: "1 - Revelation 1 - Introduction" -> "Revelation 1 - Introduction"
        #          "2 - Revelation 1_1-9 - Christian Identity (Part 1) - Bond-Servants" -> "Revelation 1_1-9 - Christian Identity"
        
        # Remove leading number and dash if present
        if re.match(r'^\d+\s*-\s*', name_without_ext):
            name_without_ext = re.sub(r'^\d+\s*-\s*', '', name_without_ext)
        
        return name_without_ext
    
    ## Search study notes for content containing the query.
    ## @param[in] query - Search query (case-insensitive).
    ## @param[in] book_filter - Optional book name to filter by.
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of matching StudyNote objects.
    def SearchStudyNotes(self, query: str, book_filter: Optional[str] = None, 
                        max_results: int = DEFAULT_SEARCH_MAX_RESULTS) -> List[StudyNote]:
        query_lower = query.lower()
        results = []
        
        notes_to_search = self.AllStudyNotes
        if book_filter:
            book_filter_lower = book_filter.lower()
            notes_to_search = [note for note in self.AllStudyNotes 
                             if book_filter_lower in note.book.lower()]
        
        for note in notes_to_search:
            # Search in content
            if query_lower in note.content.lower():
                results.append(note)
                if len(results) >= max_results:
                    break
                    
            # Search in chapter_topic
            elif query_lower in note.chapter_topic.lower():
                results.append(note)
                if len(results) >= max_results:
                    break
        
        return results
    
    ## Get study notes for a specific book.
    ## @param[in] book_name - Name of the book to get notes for.
    ## @return List of StudyNote objects for the book.
    def GetStudyNotesForBook(self, book_name: str) -> List[StudyNote]:
        return self.StudyNotes.get(book_name, [])
    
    ## Get all available book names.
    ## @return List of book names that have study notes.
    def GetAvailableBooks(self) -> List[str]:
        return list(self.StudyNotes.keys())
    
    ## Get study notes by testament.
    ## @param[in] testament - Testament name (e.g., "NewTestament").
    ## @return List of StudyNote objects for the testament.
    def GetStudyNotesByTestament(self, testament: str) -> List[StudyNote]:
        testament_lower = testament.lower()
        return [note for note in self.AllStudyNotes 
                if testament_lower in note.testament.lower()] 