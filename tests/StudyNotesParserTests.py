## @package StudyNotesParserTests
## Unit tests for StudyNotesParser class.

import unittest
import tempfile
import pathlib
import shutil
from unittest.mock import patch, MagicMock

from StudyNotesParser import StudyNotesParser, StudyNote

## Test cases for StudyNotesParser class.
class StudyNotesParserTests(unittest.TestCase):
    ## Set up test environment.
    def setUp(self):
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = pathlib.Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir()
        
        # Create test BibleStudyNotes structure
        self.study_notes_dir = self.test_data_dir / "BibleStudyNotes"
        self.study_notes_dir.mkdir()
        
        # Create hierarchical structure
        books_dir = self.study_notes_dir / "Books"
        books_dir.mkdir()
        
        new_testament_dir = books_dir / "NewTestament"
        new_testament_dir.mkdir()
        
        revelation_dir = new_testament_dir / "Revelation"
        revelation_dir.mkdir()
        
        # Create test study note files
        self.test_file1 = revelation_dir / "1 - Revelation 1 - Introduction.txt"
        self.test_file1.write_text("This is a test study note about Revelation 1 introduction.")
        
        self.test_file2 = revelation_dir / "2 - Revelation 1_1-9 - Christian Identity.txt"
        self.test_file2.write_text("This is a test study note about Christian identity in Revelation.")
        
        # Initialize parser
        self.parser = StudyNotesParser(str(self.test_data_dir))
    
    ## Clean up test environment.
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    ## Test initialization of StudyNotesParser.
    def test_init(self):
        parser = StudyNotesParser("test_data")
        self.assertEqual(parser.DataDirectoryPath, pathlib.Path("test_data"))
        self.assertEqual(parser.StudyNotesPath, pathlib.Path("test_data") / "BibleStudyNotes")
        self.assertEqual(parser.StudyNotes, {})
        self.assertEqual(parser.AllStudyNotes, [])
    
    ## Test loading all study notes.
    def test_load_all_study_notes(self):
        self.parser.LoadAllStudyNotes()
        
        # Check that notes were loaded
        self.assertIn("Revelation", self.parser.StudyNotes)
        self.assertEqual(len(self.parser.StudyNotes["Revelation"]), 2)
        self.assertEqual(len(self.parser.AllStudyNotes), 2)
        
        # Check first note
        note1 = self.parser.StudyNotes["Revelation"][0]
        self.assertEqual(note1.book, "Revelation")
        self.assertEqual(note1.testament, "NewTestament")
        self.assertEqual(note1.chapter_topic, "Revelation 1 - Introduction")
        self.assertEqual(note1.content, "This is a test study note about Revelation 1 introduction.")
    
    ## Test loading study notes with missing directory.
    def test_load_all_study_notes_missing_directory(self):
        parser = StudyNotesParser("nonexistent")
        with self.assertRaises(FileNotFoundError):
            parser.LoadAllStudyNotes()
    
    ## Test loading study notes with no txt files.
    def test_load_all_study_notes_no_txt_files(self):
        # Create directory structure but no txt files
        empty_dir = tempfile.mkdtemp()
        empty_data_dir = pathlib.Path(empty_dir) / "data"
        empty_data_dir.mkdir()
        empty_study_dir = empty_data_dir / "BibleStudyNotes"
        empty_study_dir.mkdir()
        
        parser = StudyNotesParser(str(empty_data_dir))
        parser.LoadAllStudyNotes()  # Should not raise exception
        
        self.assertEqual(len(parser.AllStudyNotes), 0)
        shutil.rmtree(empty_dir)
    
    ## Test parsing single study note file.
    def test_parse_study_note_file(self):
        note = self.parser._ParseStudyNoteFile(self.test_file1)
        
        self.assertIsNotNone(note)
        if note is not None:  # Type guard for linter
            self.assertEqual(note.book, "Revelation")
            self.assertEqual(note.testament, "NewTestament")
            self.assertEqual(note.chapter_topic, "Revelation 1 - Introduction")
            self.assertEqual(note.content, "This is a test study note about Revelation 1 introduction.")
            self.assertEqual(note.filename, "1 - Revelation 1 - Introduction.txt")
    
    ## Test parsing non-existent file.
    def test_parse_study_note_file_nonexistent(self):
        nonexistent_file = self.test_data_dir / "nonexistent.txt"
        note = self.parser._ParseStudyNoteFile(nonexistent_file)
        self.assertIsNone(note)
    
    ## Test parsing empty file.
    def test_parse_study_note_file_empty(self):
        empty_file = self.test_data_dir / "empty.txt"
        empty_file.write_text("")
        
        note = self.parser._ParseStudyNoteFile(empty_file)
        self.assertIsNone(note)
        
        empty_file.unlink()
    
    ## Test extracting metadata from path.
    def test_extract_metadata_from_path(self):
        metadata = self.parser._ExtractMetadataFromPath(self.test_file1)
        
        self.assertIsNotNone(metadata)
        if metadata is not None:  # Type guard for linter
            self.assertEqual(metadata['book'], "Revelation")
            self.assertEqual(metadata['testament'], "NewTestament")
            self.assertEqual(metadata['chapter_topic'], "Revelation 1 - Introduction")
    
    ## Test extracting metadata from invalid path.
    def test_extract_metadata_from_path_invalid(self):
        invalid_file = self.test_data_dir / "invalid.txt"
        metadata = self.parser._ExtractMetadataFromPath(invalid_file)
        self.assertIsNone(metadata)
    
    ## Test extracting chapter topic from filename.
    def test_extract_chapter_topic_from_filename(self):
        # Test with numbered filename
        topic1 = self.parser._ExtractChapterTopicFromFilename("1 - Revelation 1 - Introduction.txt")
        self.assertEqual(topic1, "Revelation 1 - Introduction")
        
        # Test with complex filename
        topic2 = self.parser._ExtractChapterTopicFromFilename("2 - Revelation 1_1-9 - Christian Identity (Part 1) - Bond-Servants.txt")
        self.assertEqual(topic2, "Revelation 1_1-9 - Christian Identity (Part 1) - Bond-Servants")
        
        # Test with no number prefix
        topic3 = self.parser._ExtractChapterTopicFromFilename("Revelation 1 - Introduction.txt")
        self.assertEqual(topic3, "Revelation 1 - Introduction")
    
    ## Test searching study notes.
    def test_search_study_notes(self):
        self.parser.LoadAllStudyNotes()
        
        # Search for content
        results = self.parser.SearchStudyNotes("introduction")
        self.assertEqual(len(results), 1)
        self.assertIn("introduction", results[0].content.lower())
        
        # Search for chapter topic
        results = self.parser.SearchStudyNotes("Christian Identity")
        self.assertEqual(len(results), 1)
        self.assertIn("Christian Identity", results[0].chapter_topic)
        
        # Search with book filter
        results = self.parser.SearchStudyNotes("test", book_filter="Revelation")
        self.assertEqual(len(results), 2)
        
        # Search with non-matching book filter
        results = self.parser.SearchStudyNotes("test", book_filter="Genesis")
        self.assertEqual(len(results), 0)
    
    ## Test getting study notes for specific book.
    def test_get_study_notes_for_book(self):
        self.parser.LoadAllStudyNotes()
        
        notes = self.parser.GetStudyNotesForBook("Revelation")
        self.assertEqual(len(notes), 2)
        
        notes = self.parser.GetStudyNotesForBook("Genesis")
        self.assertEqual(len(notes), 0)
    
    ## Test getting available books.
    def test_get_available_books(self):
        self.parser.LoadAllStudyNotes()
        
        books = self.parser.GetAvailableBooks()
        self.assertEqual(books, ["Revelation"])
    
    ## Test getting study notes by testament.
    def test_get_study_notes_by_testament(self):
        self.parser.LoadAllStudyNotes()
        
        notes = self.parser.GetStudyNotesByTestament("NewTestament")
        self.assertEqual(len(notes), 2)
        
        notes = self.parser.GetStudyNotesByTestament("OldTestament")
        self.assertEqual(len(notes), 0)

if __name__ == '__main__':
    unittest.main() 