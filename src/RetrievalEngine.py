## @package RetrievalEngine
## Intelligent retrieval engine for Bible verses and study notes.

from typing import Dict, List, Optional, Tuple, Any
import re

from BibleParser import BibleParser, BibleVerse
from StudyNotesParser import StudyNotesParser, StudyNote
from EmbeddingsManager import EmbeddingsManager, EmbeddingItem
from LlmClient import LLMClient

# Retrieval Constants
DEFAULT_MAX_BIBLE_RESULTS = 15
DEFAULT_MAX_STUDY_RESULTS = 10
DEFAULT_SIMILARITY_THRESHOLD = 0.3
TRANSLATION_PRIORITY = ["YLT", "KJV", "WEB"]

## Intelligent retrieval engine for Bible content and study notes.
class RetrievalEngine:
    ## Initialize the retrieval engine.
    ## @param[in] bible_parser - Initialized Bible parser instance.
    ## @param[in] study_notes_parser - Initialized study notes parser instance.
    ## @param[in] embeddings_manager - Initialized embeddings manager instance.
    ## @param[in] llm_client - LLM client for generating embeddings.
    def __init__(self, bible_parser: 'BibleParser', study_notes_parser: 'StudyNotesParser', 
                 embeddings_manager: 'EmbeddingsManager', llm_client: 'LLMClient'):
        ## Bible parser for accessing Bible data.
        self.BibleParser: "BibleParser" = bible_parser
        ## Study notes parser for accessing study notes.
        self.StudyNotesParser: "StudyNotesParser" = study_notes_parser
        ## Embeddings manager for semantic search.
        self.EmbeddingsManager: "EmbeddingsManager" = embeddings_manager
        ## LLM client for generating embeddings.
        self.LlmClient: "LLMClient" = llm_client
        
    ## Retrieve relevant content for a query using both semantic and keyword search.
    ## @param[in] query - The search query.
    ## @param[in] max_bible_results - Maximum number of Bible verses to return.
    ## @param[in] max_study_results - Maximum number of study notes to return.
    ## @return Dictionary with retrieved content organized by type.
    def RetrieveContent(self, query: str, max_bible_results: int = DEFAULT_MAX_BIBLE_RESULTS,
                       max_study_results: int = DEFAULT_MAX_STUDY_RESULTS) -> Dict[str, Any]:
        # Generate embedding for the query
        query_embedding = self._GenerateEmbedding(query)
        
        # Retrieve content using semantic search
        semantic_bible_verses = self._RetrieveBibleVersesSemantic(query_embedding, max_bible_results)
        semantic_study_notes = self._RetrieveStudyNotesSemantic(query_embedding, max_study_results)
        
        # Retrieve content using keyword search as fallback
        keyword_bible_verses = self._RetrieveBibleVersesKeyword(query, max_bible_results)
        keyword_study_notes = self._RetrieveStudyNotesKeyword(query, max_study_results)
        
        # Combine and deduplicate results
        combined_bible_verses = self._CombineAndDeduplicateVerses(
            semantic_bible_verses, keyword_bible_verses, max_bible_results
        )
        combined_study_notes = self._CombineAndDeduplicateStudyNotes(
            semantic_study_notes, keyword_study_notes, max_study_results
        )
        
        return {
            'bible_verses': combined_bible_verses,
            'study_notes': combined_study_notes,
            'query': query,
            'total_bible_results': len(combined_bible_verses),
            'total_study_results': len(combined_study_notes)
        }
    
    ## Generate embedding for text using the LLM client.
    ## @param[in] text - Text to generate embedding for.
    ## @return List of floats representing the embedding.
    def _GenerateEmbedding(self, text: str) -> List[float]:
        # For now, we'll use a simple approach - in a full implementation,
        # this would call the LLM's embedding endpoint
        # This is a placeholder that returns a dummy embedding
        # In practice, you'd want to use the LLM's actual embedding API
        
        # Simple hash-based embedding for demonstration
        # In production, replace this with actual LLM embedding call
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to list of floats (simplified embedding)
        embedding = [float(b) / 255.0 for b in hash_bytes[:16]]  # Use first 16 bytes
        # Pad to reasonable embedding size
        while len(embedding) < 384:
            embedding.extend(embedding[:min(384 - len(embedding), len(embedding))])
        
        return embedding[:384]
    
    ## Retrieve Bible verses using semantic search.
    ## @param[in] query_embedding - Query embedding vector.
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of BibleVerse objects with similarity scores.
    def _RetrieveBibleVersesSemantic(self, query_embedding: List[float], 
                                   max_results: int) -> List[Tuple[BibleVerse, float]]:
        if not self.EmbeddingsManager.EmbeddingsLoaded:
            return []
            
        # Find similar Bible verse embeddings
        similar_items = self.EmbeddingsManager.FindSimilarContent(
            query_embedding, content_type_filter="bible_verse", max_results=max_results
        )
        
        # Convert to BibleVerse objects
        results = []
        for item, similarity in similar_items:
            if similarity >= DEFAULT_SIMILARITY_THRESHOLD:
                # Reconstruct BibleVerse from metadata
                metadata = item.metadata
                verse = BibleVerse(
                    translation=metadata['translation'],
                    book=metadata['book'],
                    chapter=metadata['chapter'],
                    verse=metadata['verse'],
                    text=item.content,
                    osis_id=metadata['osis_id']
                )
                results.append((verse, similarity))
        
        return results
    
    ## Retrieve study notes using semantic search.
    ## @param[in] query_embedding - Query embedding vector.
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of StudyNote objects with similarity scores.
    def _RetrieveStudyNotesSemantic(self, query_embedding: List[float], 
                                  max_results: int) -> List[Tuple[StudyNote, float]]:
        if not self.EmbeddingsManager.EmbeddingsLoaded:
            return []
            
        # Find similar study note embeddings
        similar_items = self.EmbeddingsManager.FindSimilarContent(
            query_embedding, content_type_filter="study_note", max_results=max_results
        )
        
        # Convert to StudyNote objects
        results = []
        for item, similarity in similar_items:
            if similarity >= DEFAULT_SIMILARITY_THRESHOLD:
                # Reconstruct StudyNote from metadata
                metadata = item.metadata
                note = StudyNote(
                    file_path=metadata['file_path'],
                    content=item.content,
                    book=metadata['book'],
                    testament=metadata['testament'],
                    chapter_topic=metadata['chapter_topic'],
                    filename=metadata['filename'],
                    line_count=metadata['line_count']
                )
                results.append((note, similarity))
        
        return results
    
    ## Retrieve Bible verses using keyword search.
    ## @param[in] query - Search query.
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of BibleVerse objects.
    def _RetrieveBibleVersesKeyword(self, query: str, max_results: int) -> List[BibleVerse]:
        # Extract keywords from query
        keywords = self._ExtractKeywords(query)
        
        # Search across all translations in priority order
        all_verses = []
        for translation in TRANSLATION_PRIORITY:
            verses = self.BibleParser.GetVersesByTopicKeywords(
                keywords, translation=translation, max_results=max_results
            )
            all_verses.extend(verses)
            
            if len(all_verses) >= max_results:
                break
        
        return all_verses[:max_results]
    
    ## Retrieve study notes using keyword search.
    ## @param[in] query - Search query.
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of StudyNote objects.
    def _RetrieveStudyNotesKeyword(self, query: str, max_results: int) -> List[StudyNote]:
        # Extract keywords from query
        keywords = self._ExtractKeywords(query)
        
        # Search study notes
        all_notes = []
        for keyword in keywords:
            notes = self.StudyNotesParser.SearchStudyNotes(keyword, max_results=max_results)
            all_notes.extend(notes)
            
            if len(all_notes) >= max_results:
                break
        
        return all_notes[:max_results]
    
    ## Extract keywords from a query.
    ## @param[in] query - The search query.
    ## @return List of keywords.
    def _ExtractKeywords(self, query: str) -> List[str]:
        # Simple keyword extraction - remove common words and split
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'what', 'when', 'where', 'why', 'how', 'who', 'which', 'that', 'this', 'these', 'those'}
        
        # Clean and split query
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out common words and short words
        keywords = [word for word in words if word not in common_words and len(word) > 2]
        
        return keywords[:10]  # Limit to 10 keywords
    
    ## Combine and deduplicate Bible verse results.
    ## @param[in] semantic_results - Results from semantic search.
    ## @param[in] keyword_results - Results from keyword search.
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of unique BibleVerse objects.
    def _CombineAndDeduplicateVerses(self, semantic_results: List[Tuple[BibleVerse, float]], 
                                   keyword_results: List[BibleVerse], 
                                   max_results: int) -> List[BibleVerse]:
        # Create a set to track seen verses
        seen_verses = set()
        combined_verses = []
        
        # Add semantic results first (they have similarity scores)
        for verse, similarity in semantic_results:
            verse_key = f"{verse.translation}:{verse.osis_id}"
            if verse_key not in seen_verses:
                seen_verses.add(verse_key)
                combined_verses.append(verse)
                
                if len(combined_verses) >= max_results:
                    return combined_verses
        
        # Add keyword results
        for verse in keyword_results:
            verse_key = f"{verse.translation}:{verse.osis_id}"
            if verse_key not in seen_verses:
                seen_verses.add(verse_key)
                combined_verses.append(verse)
                
                if len(combined_verses) >= max_results:
                    break
        
        return combined_verses
    
    ## Combine and deduplicate study note results.
    ## @param[in] semantic_results - Results from semantic search.
    ## @param[in] keyword_results - Results from keyword search.
    ## @param[in] max_results - Maximum number of results to return.
    ## @return List of unique StudyNote objects.
    def _CombineAndDeduplicateStudyNotes(self, semantic_results: List[Tuple[StudyNote, float]], 
                                       keyword_results: List[StudyNote], 
                                       max_results: int) -> List[StudyNote]:
        # Create a set to track seen notes
        seen_notes = set()
        combined_notes = []
        
        # Add semantic results first (they have similarity scores)
        for note, similarity in semantic_results:
            if note.file_path not in seen_notes:
                seen_notes.add(note.file_path)
                combined_notes.append(note)
                
                if len(combined_notes) >= max_results:
                    return combined_notes
        
        # Add keyword results
        for note in keyword_results:
            if note.file_path not in seen_notes:
                seen_notes.add(note.file_path)
                combined_notes.append(note)
                
                if len(combined_notes) >= max_results:
                    break
        
        return combined_notes 