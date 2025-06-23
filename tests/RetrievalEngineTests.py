## @package RetrievalEngineTests
## Unit tests for RetrievalEngine class.

import unittest
import tempfile
import pathlib
import shutil
from unittest.mock import patch, MagicMock

from RetrievalEngine import RetrievalEngine
from BibleParser import BibleParser, BibleVerse
from StudyNotesParser import StudyNotesParser, StudyNote
from EmbeddingsManager import EmbeddingsManager
from LlmClient import LLMClient

## Test cases for RetrievalEngine class.
class RetrievalEngineTests(unittest.TestCase):
    ## Set up test environment.
    def setUp(self):
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = pathlib.Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir()
        
        # Create mock components
        self.mock_bible_parser = MagicMock(spec=BibleParser)
        self.mock_study_notes_parser = MagicMock(spec=StudyNotesParser)
        self.mock_embeddings_manager = MagicMock(spec=EmbeddingsManager)
        self.mock_llm_client = MagicMock(spec=LLMClient)
        
        # Set up mock embeddings manager
        self.mock_embeddings_manager.EmbeddingsLoaded = False
        
        # Initialize retrieval engine
        self.retrieval_engine = RetrievalEngine(
            self.mock_bible_parser,
            self.mock_study_notes_parser,
            self.mock_embeddings_manager,
            self.mock_llm_client
        )
        
        # Create test data
        self.test_verse = BibleVerse(
            translation="KJV",
            book="John",
            chapter=3,
            verse=16,
            text="For God so loved the world, that he gave his only begotten Son.",
            osis_id="John.3.16"
        )
        
        self.test_study_note = StudyNote(
            file_path="test/path.txt",
            content="This is a test study note about love.",
            book="John",
            testament="NewTestament",
            chapter_topic="John 3 - God's Love",
            filename="test_note.txt",
            line_count=5
        )
    
    ## Clean up test environment.
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    ## Test initialization of RetrievalEngine.
    def test_init(self):
        engine = RetrievalEngine(
            self.mock_bible_parser,
            self.mock_study_notes_parser,
            self.mock_embeddings_manager,
            self.mock_llm_client
        )
        
        self.assertEqual(engine.BibleParser, self.mock_bible_parser)
        self.assertEqual(engine.StudyNotesParser, self.mock_study_notes_parser)
        self.assertEqual(engine.EmbeddingsManager, self.mock_embeddings_manager)
        self.assertEqual(engine.LlmClient, self.mock_llm_client)
    
    ## Test retrieving content with keyword search only (no embeddings).
    def test_retrieve_content_keyword_only(self):
        # Set up mocks
        self.mock_embeddings_manager.EmbeddingsLoaded = False
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = [self.test_verse]
        self.mock_study_notes_parser.SearchStudyNotes.return_value = [self.test_study_note]
        
        # Test retrieval
        result = self.retrieval_engine.RetrieveContent("love")
        
        # Verify results
        self.assertEqual(len(result['bible_verses']), 1)
        self.assertEqual(len(result['study_notes']), 1)
        self.assertEqual(result['query'], "love")
        self.assertEqual(result['total_bible_results'], 1)
        self.assertEqual(result['total_study_results'], 1)
        
        # Verify method calls
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_called()
        self.mock_study_notes_parser.SearchStudyNotes.assert_called()
    
    ## Test retrieving content with semantic search.
    def test_retrieve_content_with_semantic_search(self):
        # Set up mocks for semantic search
        self.mock_embeddings_manager.EmbeddingsLoaded = True
        
        # Mock semantic search results
        semantic_bible_result = (self.test_verse, 0.8)
        semantic_study_result = (self.test_study_note, 0.7)
        
        self.mock_embeddings_manager.FindSimilarContent.side_effect = [
            [semantic_bible_result],  # Bible verses
            [semantic_study_result]   # Study notes
        ]
        
        # Mock keyword search results
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = []
        self.mock_study_notes_parser.SearchStudyNotes.return_value = []
        
        # Test retrieval
        result = self.retrieval_engine.RetrieveContent("love")
        
        # Verify results
        self.assertEqual(len(result['bible_verses']), 1)
        self.assertEqual(len(result['study_notes']), 1)
        
        # Verify semantic search was called
        self.assertEqual(self.mock_embeddings_manager.FindSimilarContent.call_count, 2)
    
    ## Test combining semantic and keyword results.
    def test_retrieve_content_combine_results(self):
        # Set up mocks
        self.mock_embeddings_manager.EmbeddingsLoaded = True
        
        # Mock semantic search results
        semantic_bible_result = (self.test_verse, 0.8)
        self.mock_embeddings_manager.FindSimilarContent.side_effect = [
            [semantic_bible_result],  # Bible verses
            []                        # Study notes
        ]
        
        # Mock keyword search results
        keyword_verse = BibleVerse(
            translation="WEB",
            book="John",
            chapter=3,
            verse=17,
            text="For God didn't send his Son into the world to judge the world.",
            osis_id="John.3.17"
        )
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = [keyword_verse]
        self.mock_study_notes_parser.SearchStudyNotes.return_value = [self.test_study_note]
        
        # Test retrieval
        result = self.retrieval_engine.RetrieveContent("love")
        
        # Verify results (should combine both)
        self.assertEqual(len(result['bible_verses']), 2)
        self.assertEqual(len(result['study_notes']), 1)
    
    ## Test deduplication of results.
    def test_retrieve_content_deduplication(self):
        # Set up mocks
        self.mock_embeddings_manager.EmbeddingsLoaded = True
        
        # Mock semantic search results
        semantic_bible_result = (self.test_verse, 0.8)
        self.mock_embeddings_manager.FindSimilarContent.side_effect = [
            [semantic_bible_result],  # Bible verses
            []                        # Study notes
        ]
        
        # Mock keyword search results (same verse)
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = [self.test_verse]
        self.mock_study_notes_parser.SearchStudyNotes.return_value = []
        
        # Test retrieval
        result = self.retrieval_engine.RetrieveContent("love")
        
        # Verify results (should deduplicate)
        self.assertEqual(len(result['bible_verses']), 1)
        self.assertEqual(len(result['study_notes']), 0)
    
    ## Test keyword extraction.
    def test_extract_keywords(self):
        # Test basic keyword extraction
        keywords = self.retrieval_engine._ExtractKeywords("What does the Bible say about love?")
        self.assertIn("bible", keywords)
        self.assertIn("love", keywords)
        self.assertNotIn("what", keywords)  # Common word should be filtered
        self.assertNotIn("the", keywords)   # Common word should be filtered
        
        # Test with short words
        keywords = self.retrieval_engine._ExtractKeywords("a b c d e f g")
        self.assertEqual(len(keywords), 0)  # All words too short
        
        # Test with mixed content
        keywords = self.retrieval_engine._ExtractKeywords("Jesus Christ salvation grace")
        self.assertIn("jesus", keywords)
        self.assertIn("christ", keywords)
        self.assertIn("salvation", keywords)
        self.assertIn("grace", keywords)
    
    ## Test Bible verse retrieval by keyword.
    def test_retrieve_bible_verses_keyword(self):
        # Set up mock
        self.mock_bible_parser.GetVersesByTopicKeywords.return_value = [self.test_verse]
        
        # Test retrieval
        results = self.retrieval_engine._RetrieveBibleVersesKeyword("love", 10)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.test_verse)
        
        # Verify method was called with correct parameters
        self.mock_bible_parser.GetVersesByTopicKeywords.assert_called()
        call_args = self.mock_bible_parser.GetVersesByTopicKeywords.call_args
        self.assertIn("love", call_args[0][0])  # First argument should contain keywords
    
    ## Test study notes retrieval by keyword.
    def test_retrieve_study_notes_keyword(self):
        # Set up mock
        self.mock_study_notes_parser.SearchStudyNotes.return_value = [self.test_study_note]
        
        # Test retrieval
        results = self.retrieval_engine._RetrieveStudyNotesKeyword("love", 10)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.test_study_note)
        
        # Verify method was called
        self.mock_study_notes_parser.SearchStudyNotes.assert_called()
    
    ## Test Bible verse retrieval by semantic search.
    def test_retrieve_bible_verses_semantic(self):
        # Set up mocks
        self.mock_embeddings_manager.EmbeddingsLoaded = True
        
        # Mock embedding item
        mock_embedding_item = MagicMock()
        mock_embedding_item.content = self.test_verse.text
        mock_embedding_item.metadata = {
            'translation': self.test_verse.translation,
            'book': self.test_verse.book,
            'chapter': self.test_verse.chapter,
            'verse': self.test_verse.verse,
            'osis_id': self.test_verse.osis_id
        }
        
        self.mock_embeddings_manager.FindSimilarContent.return_value = [
            (mock_embedding_item, 0.8)
        ]
        
        # Test retrieval
        results = self.retrieval_engine._RetrieveBibleVersesSemantic([0.1, 0.2, 0.3], 10)
        
        self.assertEqual(len(results), 1)
        verse, similarity = results[0]
        self.assertEqual(verse.translation, self.test_verse.translation)
        self.assertEqual(verse.book, self.test_verse.book)
        self.assertEqual(similarity, 0.8)
    
    ## Test study notes retrieval by semantic search.
    def test_retrieve_study_notes_semantic(self):
        # Set up mocks
        self.mock_embeddings_manager.EmbeddingsLoaded = True
        
        # Mock embedding item
        mock_embedding_item = MagicMock()
        mock_embedding_item.content = self.test_study_note.content
        mock_embedding_item.metadata = {
            'file_path': self.test_study_note.file_path,
            'book': self.test_study_note.book,
            'testament': self.test_study_note.testament,
            'chapter_topic': self.test_study_note.chapter_topic,
            'filename': self.test_study_note.filename,
            'line_count': self.test_study_note.line_count
        }
        
        self.mock_embeddings_manager.FindSimilarContent.return_value = [
            (mock_embedding_item, 0.7)
        ]
        
        # Test retrieval
        results = self.retrieval_engine._RetrieveStudyNotesSemantic([0.1, 0.2, 0.3], 10)
        
        self.assertEqual(len(results), 1)
        note, similarity = results[0]
        self.assertEqual(note.book, self.test_study_note.book)
        self.assertEqual(note.content, self.test_study_note.content)
        self.assertEqual(similarity, 0.7)
    
    ## Test combining and deduplicating Bible verses.
    def test_combine_and_deduplicate_verses(self):
        # Create test data
        semantic_results = [(self.test_verse, 0.8)]
        keyword_results = [self.test_verse]  # Same verse
        
        # Test deduplication
        combined = self.retrieval_engine._CombineAndDeduplicateVerses(
            semantic_results, keyword_results, 10
        )
        
        self.assertEqual(len(combined), 1)  # Should deduplicate
        
        # Test with different verses
        different_verse = BibleVerse(
            translation="WEB",
            book="John",
            chapter=3,
            verse=17,
            text="For God didn't send his Son into the world to judge the world.",
            osis_id="John.3.17"
        )
        keyword_results = [different_verse]
        
        combined = self.retrieval_engine._CombineAndDeduplicateVerses(
            semantic_results, keyword_results, 10
        )
        
        self.assertEqual(len(combined), 2)  # Should include both
    
    ## Test combining and deduplicating study notes.
    def test_combine_and_deduplicate_study_notes(self):
        # Create test data
        semantic_results = [(self.test_study_note, 0.7)]
        keyword_results = [self.test_study_note]  # Same note
        
        # Test deduplication
        combined = self.retrieval_engine._CombineAndDeduplicateStudyNotes(
            semantic_results, keyword_results, 10
        )
        
        self.assertEqual(len(combined), 1)  # Should deduplicate
        
        # Test with different notes
        different_note = StudyNote(
            file_path="different/path.txt",
            content="Different content",
            book="John",
            testament="NewTestament",
            chapter_topic="Different Topic",
            filename="different.txt",
            line_count=3
        )
        keyword_results = [different_note]
        
        combined = self.retrieval_engine._CombineAndDeduplicateStudyNotes(
            semantic_results, keyword_results, 10
        )
        
        self.assertEqual(len(combined), 2)  # Should include both
    
    ## Test embedding generation.
    def test_generate_embedding(self):
        # Test that embedding is generated
        embedding = self.retrieval_engine._GenerateEmbedding("test text")
        
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 384)  # Should be 384 dimensions
        self.assertTrue(all(isinstance(x, float) for x in embedding))
        
        # Test that different text produces different embedding
        embedding2 = self.retrieval_engine._GenerateEmbedding("different text")
        self.assertNotEqual(embedding, embedding2)
        
        # Test that same text produces same embedding
        embedding3 = self.retrieval_engine._GenerateEmbedding("test text")
        self.assertEqual(embedding, embedding3)

if __name__ == '__main__':
    unittest.main() 