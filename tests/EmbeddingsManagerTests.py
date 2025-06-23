## @package EmbeddingsManagerTests
## Unit tests for EmbeddingsManager class.

import unittest
import tempfile
import pathlib
import shutil
import pickle
from unittest.mock import patch, MagicMock

from EmbeddingsManager import EmbeddingsManager, EmbeddingItem
from BibleVerse import BibleVerse
from StudyNotesParser import StudyNote

## Test cases for EmbeddingsManager class.
class EmbeddingsManagerTests(unittest.TestCase):
    ## Set up test environment.
    def setUp(self):
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = pathlib.Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir()
        
        # Initialize embeddings manager
        self.embeddings_manager = EmbeddingsManager(str(self.test_data_dir))
        
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
        
        self.test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 77  # 385 dimensions
    
    ## Clean up test environment.
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    ## Test initialization of EmbeddingsManager.
    def test_init(self):
        manager = EmbeddingsManager("test_data")
        self.assertEqual(manager.DataDirectoryPath, pathlib.Path("test_data"))
        self.assertEqual(manager.EmbeddingsCachePath, pathlib.Path("test_data") / "embeddings_cache.pkl")
        self.assertEqual(manager.MetadataPath, pathlib.Path("test_data") / "embeddings_metadata.json")
        self.assertEqual(manager.Embeddings, {})
        self.assertFalse(manager.EmbeddingsLoaded)
    
    ## Test loading embeddings from non-existent file.
    def test_load_embeddings_nonexistent(self):
        self.embeddings_manager.LoadEmbeddings()
        self.assertEqual(len(self.embeddings_manager.Embeddings), 0)
        self.assertFalse(self.embeddings_manager.EmbeddingsLoaded)
    
    ## Test loading embeddings from existing file.
    def test_load_embeddings_existing(self):
        # Create test embeddings data
        test_embeddings_data = {
            "test_id": {
                'id': "test_id",
                'embedding': self.test_embedding,
                'content': "Test content",
                'content_type': "bible_verse",
                'metadata': {'test': 'data'}
            }
        }
        
        # Save test data
        with open(self.embeddings_manager.EmbeddingsCachePath, 'wb') as f:
            pickle.dump(test_embeddings_data, f)
        
        # Load embeddings
        self.embeddings_manager.LoadEmbeddings()
        
        self.assertEqual(len(self.embeddings_manager.Embeddings), 1)
        self.assertTrue(self.embeddings_manager.EmbeddingsLoaded)
        self.assertIn("test_id", self.embeddings_manager.Embeddings)
    
    ## Test loading embeddings with corrupted file.
    def test_load_embeddings_corrupted(self):
        # Create corrupted file
        with open(self.embeddings_manager.EmbeddingsCachePath, 'w') as f:
            f.write("corrupted data")
        
        # Load embeddings should handle error gracefully
        self.embeddings_manager.LoadEmbeddings()
        self.assertEqual(len(self.embeddings_manager.Embeddings), 0)
        self.assertFalse(self.embeddings_manager.EmbeddingsLoaded)
    
    ## Test saving embeddings.
    def test_save_embeddings(self):
        # Add test embedding
        test_item = EmbeddingItem(
            id="test_id",
            embedding=self.test_embedding,
            content="Test content",
            content_type="bible_verse",
            metadata={'test': 'data'}
        )
        self.embeddings_manager.Embeddings["test_id"] = test_item
        
        # Save embeddings
        self.embeddings_manager.SaveEmbeddings()
        
        # Verify file was created
        self.assertTrue(self.embeddings_manager.EmbeddingsCachePath.exists())
        
        # Load back and verify
        new_manager = EmbeddingsManager(str(self.test_data_dir))
        new_manager.LoadEmbeddings()
        self.assertEqual(len(new_manager.Embeddings), 1)
        self.assertIn("test_id", new_manager.Embeddings)
    
    ## Test adding Bible verse embeddings.
    def test_add_bible_verse_embeddings(self):
        verses = [self.test_verse]
        embeddings = [self.test_embedding]
        
        self.embeddings_manager.AddBibleVerseEmbeddings(verses, embeddings)
        
        expected_id = f"bible_{self.test_verse.translation}_{self.test_verse.osis_id}"
        self.assertIn(expected_id, self.embeddings_manager.Embeddings)
        
        item = self.embeddings_manager.Embeddings[expected_id]
        self.assertEqual(item.content_type, "bible_verse")
        self.assertEqual(item.content, self.test_verse.text)
        self.assertEqual(item.metadata['translation'], self.test_verse.translation)
        self.assertEqual(item.metadata['book'], self.test_verse.book)
    
    ## Test adding Bible verse embeddings with mismatched lengths.
    def test_add_bible_verse_embeddings_mismatched_lengths(self):
        verses = [self.test_verse]
        embeddings = [self.test_embedding, self.test_embedding]  # Extra embedding
        
        with self.assertRaises(ValueError):
            self.embeddings_manager.AddBibleVerseEmbeddings(verses, embeddings)
    
    ## Test adding study note embeddings.
    def test_add_study_note_embeddings(self):
        study_notes = [self.test_study_note]
        embeddings = [self.test_embedding]
        
        self.embeddings_manager.AddStudyNoteEmbeddings(study_notes, embeddings)
        
        expected_id = f"study_{self.test_study_note.book}_{self.test_study_note.filename}"
        self.assertIn(expected_id, self.embeddings_manager.Embeddings)
        
        item = self.embeddings_manager.Embeddings[expected_id]
        self.assertEqual(item.content_type, "study_note")
        self.assertEqual(item.content, self.test_study_note.content)
        self.assertEqual(item.metadata['book'], self.test_study_note.book)
        self.assertEqual(item.metadata['testament'], self.test_study_note.testament)
    
    ## Test finding similar content.
    def test_find_similar_content(self):
        # Add test embeddings
        test_item1 = EmbeddingItem(
            id="test1",
            embedding=[1.0, 0.0, 0.0, 0.0, 0.0] * 77,  # Similar to query
            content="Test content 1",
            content_type="bible_verse",
            metadata={'test': 'data1'}
        )
        test_item2 = EmbeddingItem(
            id="test2",
            embedding=[0.0, 1.0, 0.0, 0.0, 0.0] * 77,  # Less similar
            content="Test content 2",
            content_type="bible_verse",
            metadata={'test': 'data2'}
        )
        
        self.embeddings_manager.Embeddings["test1"] = test_item1
        self.embeddings_manager.Embeddings["test2"] = test_item2
        
        # Query embedding similar to test_item1
        query_embedding = [0.9, 0.1, 0.0, 0.0, 0.0] * 77
        
        results = self.embeddings_manager.FindSimilarContent(query_embedding, max_results=2)
        
        self.assertEqual(len(results), 2)
        # First result should be test_item1 (more similar)
        self.assertEqual(results[0][0].id, "test1")
        self.assertGreater(results[0][1], results[1][1])  # Higher similarity score
    
    ## Test finding similar content with content type filter.
    def test_find_similar_content_with_filter(self):
        # Add mixed content types
        bible_item = EmbeddingItem(
            id="bible_test",
            embedding=self.test_embedding,
            content="Bible content",
            content_type="bible_verse",
            metadata={'test': 'data'}
        )
        study_item = EmbeddingItem(
            id="study_test",
            embedding=self.test_embedding,
            content="Study content",
            content_type="study_note",
            metadata={'test': 'data'}
        )
        
        self.embeddings_manager.Embeddings["bible_test"] = bible_item
        self.embeddings_manager.Embeddings["study_test"] = study_item
        
        # Filter by bible_verse
        results = self.embeddings_manager.FindSimilarContent(
            self.test_embedding, 
            content_type_filter="bible_verse"
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0].content_type, "bible_verse")
    
    ## Test cosine similarity calculation.
    def test_cosine_similarity(self):
        # Test identical vectors
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]
        similarity = self.embeddings_manager._CosineSimilarity(vector1, vector2)
        self.assertAlmostEqual(similarity, 1.0, places=5)
        
        # Test orthogonal vectors
        vector1 = [1.0, 0.0, 0.0]
        vector2 = [0.0, 1.0, 0.0]
        similarity = self.embeddings_manager._CosineSimilarity(vector1, vector2)
        self.assertAlmostEqual(similarity, 0.0, places=5)
        
        # Test zero vectors
        vector1 = [0.0, 0.0, 0.0]
        vector2 = [1.0, 0.0, 0.0]
        similarity = self.embeddings_manager._CosineSimilarity(vector1, vector2)
        self.assertEqual(similarity, 0.0)
    
    ## Test getting embedding by ID.
    def test_get_embedding(self):
        test_item = EmbeddingItem(
            id="test_id",
            embedding=self.test_embedding,
            content="Test content",
            content_type="bible_verse",
            metadata={'test': 'data'}
        )
        self.embeddings_manager.Embeddings["test_id"] = test_item
        
        retrieved_item = self.embeddings_manager.GetEmbedding("test_id")
        self.assertEqual(retrieved_item, test_item)
        
        # Test non-existent ID
        retrieved_item = self.embeddings_manager.GetEmbedding("nonexistent")
        self.assertIsNone(retrieved_item)
    
    ## Test getting embeddings by type.
    def test_get_embeddings_by_type(self):
        # Add mixed content types
        bible_item = EmbeddingItem(
            id="bible_test",
            embedding=self.test_embedding,
            content="Bible content",
            content_type="bible_verse",
            metadata={'test': 'data'}
        )
        study_item = EmbeddingItem(
            id="study_test",
            embedding=self.test_embedding,
            content="Study content",
            content_type="study_note",
            metadata={'test': 'data'}
        )
        
        self.embeddings_manager.Embeddings["bible_test"] = bible_item
        self.embeddings_manager.Embeddings["study_test"] = study_item
        
        bible_embeddings = self.embeddings_manager.GetEmbeddingsByType("bible_verse")
        self.assertEqual(len(bible_embeddings), 1)
        self.assertEqual(bible_embeddings[0].content_type, "bible_verse")
        
        study_embeddings = self.embeddings_manager.GetEmbeddingsByType("study_note")
        self.assertEqual(len(study_embeddings), 1)
        self.assertEqual(study_embeddings[0].content_type, "study_note")
    
    ## Test getting embedding statistics.
    def test_get_embedding_stats(self):
        # Empty embeddings
        stats = self.embeddings_manager.GetEmbeddingStats()
        self.assertEqual(stats['total'], 0)
        self.assertEqual(stats['bible_verses'], 0)
        self.assertEqual(stats['study_notes'], 0)
        
        # Add mixed content
        bible_item = EmbeddingItem(
            id="bible_test",
            embedding=self.test_embedding,
            content="Bible content",
            content_type="bible_verse",
            metadata={'test': 'data'}
        )
        study_item = EmbeddingItem(
            id="study_test",
            embedding=self.test_embedding,
            content="Study content",
            content_type="study_note",
            metadata={'test': 'data'}
        )
        
        self.embeddings_manager.Embeddings["bible_test"] = bible_item
        self.embeddings_manager.Embeddings["study_test"] = study_item
        
        stats = self.embeddings_manager.GetEmbeddingStats()
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['bible_verses'], 1)
        self.assertEqual(stats['study_notes'], 1)
    
    ## Test clearing embeddings.
    def test_clear_embeddings(self):
        # Add test embedding
        test_item = EmbeddingItem(
            id="test_id",
            embedding=self.test_embedding,
            content="Test content",
            content_type="bible_verse",
            metadata={'test': 'data'}
        )
        self.embeddings_manager.Embeddings["test_id"] = test_item
        self.embeddings_manager.EmbeddingsLoaded = True
        
        # Save embeddings first
        self.embeddings_manager.SaveEmbeddings()
        
        # Clear embeddings
        self.embeddings_manager.ClearEmbeddings()
        
        self.assertEqual(len(self.embeddings_manager.Embeddings), 0)
        self.assertFalse(self.embeddings_manager.EmbeddingsLoaded)
        # Cache files should be removed
        self.assertFalse(self.embeddings_manager.EmbeddingsCachePath.exists())

if __name__ == '__main__':
    unittest.main() 