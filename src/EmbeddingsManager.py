## @package EmbeddingsManager
## Manager for local file-based embeddings storage and retrieval.

import json
import pathlib
import pickle
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

from BibleVerse import BibleVerse
from StudyNotesParser import StudyNote

# Embeddings Constants
EMBEDDINGS_FILE_NAME = "embeddings_cache.pkl"
METADATA_FILE_NAME = "embeddings_metadata.json"
DEFAULT_EMBEDDING_DIMENSION = 384  # Using a reasonable default dimension

## Represents an embedding with metadata for storage and retrieval.
@dataclass
class EmbeddingItem:
    ## Unique identifier for the embedding.
    id: str
    ## The embedding vector.
    embedding: List[float]
    ## The original text content.
    content: str
    ## Type of content ("bible_verse" or "study_note").
    content_type: str
    ## Metadata for the content.
    metadata: Dict[str, Any]

## Manager for local file-based embeddings storage and retrieval.
class EmbeddingsManager:
    ## Initialize the embeddings manager.
    ## @param[in] data_directory_path - Path to directory for storing embeddings.
    def __init__(self, data_directory_path: str = "data"):
        ## Path to the directory for storing embeddings.
        self.DataDirectoryPath: pathlib.Path = pathlib.Path(data_directory_path)
        ## Path to the embeddings cache file.
        self.EmbeddingsCachePath: pathlib.Path = self.DataDirectoryPath / EMBEDDINGS_FILE_NAME
        ## Path to the embeddings metadata file.
        self.MetadataPath: pathlib.Path = self.DataDirectoryPath / METADATA_FILE_NAME
        ## Dictionary storing all embeddings by ID.
        self.Embeddings: Dict[str, EmbeddingItem] = {}
        ## Flag indicating if embeddings are loaded.
        self.EmbeddingsLoaded: bool = False
        
    ## Load embeddings from local storage.
    def LoadEmbeddings(self) -> None:
        embeddings_file_exists = self.EmbeddingsCachePath.exists()
        if not embeddings_file_exists:
            print("No existing embeddings found. Will create new embeddings when needed.")
            return
            
        try:
            with open(self.EmbeddingsCachePath, 'rb') as f:
                embeddings_data = pickle.load(f)
                
            # Convert back to EmbeddingItem objects
            for item_id, item_data in embeddings_data.items():
                self.Embeddings[item_id] = EmbeddingItem(
                    id=item_data['id'],
                    embedding=item_data['embedding'],
                    content=item_data['content'],
                    content_type=item_data['content_type'],
                    metadata=item_data['metadata']
                )
                
            self.EmbeddingsLoaded = True
            print(f"Loaded {len(self.Embeddings)} embeddings from cache")
            
        except Exception as e:
            print(f"Error loading embeddings: {e}")
            self.Embeddings = {}
    
    ## Save embeddings to local storage.
    def SaveEmbeddings(self) -> None:
        try:
            # Convert EmbeddingItem objects to serializable format
            embeddings_data = {}
            for item_id, item in self.Embeddings.items():
                embeddings_data[item_id] = {
                    'id': item.id,
                    'embedding': item.embedding,
                    'content': item.content,
                    'content_type': item.content_type,
                    'metadata': item.metadata
                }
                
            with open(self.EmbeddingsCachePath, 'wb') as f:
                pickle.dump(embeddings_data, f)
                
            print(f"Saved {len(self.Embeddings)} embeddings to cache")
            
        except Exception as e:
            print(f"Error saving embeddings: {e}")
    
    ## Add Bible verse embeddings.
    ## @param[in] verses - List of BibleVerse objects to add embeddings for.
    ## @param[in] embeddings - List of embedding vectors corresponding to verses.
    def AddBibleVerseEmbeddings(self, verses: List[BibleVerse], embeddings: List[List[float]]) -> None:
        if len(verses) != len(embeddings):
            raise ValueError("Number of verses must match number of embeddings")
            
        for verse, embedding in zip(verses, embeddings):
            item_id = f"bible_{verse.translation}_{verse.osis_id}"
            
            self.Embeddings[item_id] = EmbeddingItem(
                id=item_id,
                embedding=embedding,
                content=verse.text,
                content_type="bible_verse",
                metadata={
                    'translation': verse.translation,
                    'book': verse.book,
                    'chapter': verse.chapter,
                    'verse': verse.verse,
                    'osis_id': verse.osis_id
                }
            )
    
    ## Add study note embeddings.
    ## @param[in] study_notes - List of StudyNote objects to add embeddings for.
    ## @param[in] embeddings - List of embedding vectors corresponding to study notes.
    def AddStudyNoteEmbeddings(self, study_notes: List[StudyNote], embeddings: List[List[float]]) -> None:
        if len(study_notes) != len(embeddings):
            raise ValueError("Number of study notes must match number of embeddings")
            
        for note, embedding in zip(study_notes, embeddings):
            item_id = f"study_{note.book}_{note.filename}"
            
            self.Embeddings[item_id] = EmbeddingItem(
                id=item_id,
                embedding=embedding,
                content=note.content,
                content_type="study_note",
                metadata={
                    'book': note.book,
                    'testament': note.testament,
                    'chapter_topic': note.chapter_topic,
                    'filename': note.filename,
                    'file_path': note.file_path,
                    'line_count': note.line_count
                }
            )
    
    ## Find similar content using cosine similarity.
    ## @param[in] query_embedding - Query embedding vector.
    ## @param[in] content_type_filter - Optional filter for content type.
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of tuples (EmbeddingItem, similarity_score) sorted by similarity.
    def FindSimilarContent(self, query_embedding: List[float], 
                          content_type_filter: Optional[str] = None,
                          max_results: int = 10) -> List[Tuple[EmbeddingItem, float]]:
        if not self.Embeddings:
            return []
            
        query_vector = np.array(query_embedding)
        similarities = []
        
        for item in self.Embeddings.values():
            # Apply content type filter if specified
            if content_type_filter and item.content_type != content_type_filter:
                continue
                
            # Calculate cosine similarity
            item_vector = np.array(item.embedding)
            similarity = self._CosineSimilarity(query_vector, item_vector)
            similarities.append((item, similarity))
        
        # Sort by similarity (highest first) and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:max_results]
    
    ## Calculate cosine similarity between two vectors.
    ## @param[in] vector_a - First vector.
    ## @param[in] vector_b - Second vector.
    ## @return Cosine similarity score.
    def _CosineSimilarity(self, vector_a: np.ndarray, vector_b: np.ndarray) -> float:
        dot_product = np.dot(vector_a, vector_b)
        norm_a = np.linalg.norm(vector_a)
        norm_b = np.linalg.norm(vector_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)
    
    ## Get embedding for a specific item by ID.
    ## @param[in] item_id - ID of the item to retrieve.
    ## @return EmbeddingItem if found, None otherwise.
    def GetEmbedding(self, item_id: str) -> Optional[EmbeddingItem]:
        return self.Embeddings.get(item_id)
    
    ## Get all embeddings of a specific content type.
    ## @param[in] content_type - Type of content to filter by.
    ## @return List of EmbeddingItem objects of the specified type.
    def GetEmbeddingsByType(self, content_type: str) -> List[EmbeddingItem]:
        return [item for item in self.Embeddings.values() if item.content_type == content_type]
    
    ## Get statistics about stored embeddings.
    ## @return Dictionary with embedding statistics.
    def GetEmbeddingStats(self) -> Dict[str, Any]:
        if not self.Embeddings:
            return {'total': 0, 'bible_verses': 0, 'study_notes': 0}
            
        bible_count = len([item for item in self.Embeddings.values() if item.content_type == "bible_verse"])
        study_count = len([item for item in self.Embeddings.values() if item.content_type == "study_note"])
        
        return {
            'total': len(self.Embeddings),
            'bible_verses': bible_count,
            'study_notes': study_count
        }
    
    ## Clear all embeddings from memory and storage.
    def ClearEmbeddings(self) -> None:
        self.Embeddings = {}
        self.EmbeddingsLoaded = False
        
        # Remove cache files if they exist
        if self.EmbeddingsCachePath.exists():
            self.EmbeddingsCachePath.unlink()
        if self.MetadataPath.exists():
            self.MetadataPath.unlink()
            
        print("Cleared all embeddings") 