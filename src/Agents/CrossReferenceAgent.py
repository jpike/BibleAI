## @package CrossReferenceAgent
## Agent for finding cross-references and related passages.

from typing import Any, Optional

from BibleParser import BibleVerse, BibleParser
from LlmClient import LLMClient
from Agents.AgentResponse import AgentResponse

# Agent Constants
DEFAULT_CROSS_REFERENCE_MAX_RELATED = 15
DEFAULT_KEYWORD_COUNT = 5
MIN_WORD_LENGTH_FOR_KEYWORDS = 4

## Agent for finding cross-references and related passages.
class CrossReferenceAgent:
    ## Initialize the cross-reference agent.
    ## @param[in] bible_parser - Initialized Bible parser instance.
    ## @param[in] llm_client - Initialized LLM client instance.
    def __init__(self, bible_parser: BibleParser, llm_client: LLMClient):
        ## Bible parser for accessing Bible data.
        self.BibleParser: "BibleParser" = bible_parser
        ## LLM client for AI interactions.
        self.LlmClient: "LLMClient" = llm_client
    
    ## Find cross-references for a given Bible reference.
    ## @param[in] reference - Bible reference (e.g., "John 3:16").
    ## @param[in] translation - Bible translation to use.
    ## @return AgentResponse with cross-reference analysis.
    def FindCrossReferences(self, reference: str, translation: str = "KJV") -> AgentResponse:
        # Parse the reference
        parsed_ref = self._ParseReference(reference)
        if not parsed_ref:
            return AgentResponse(
                success=False,
                content=f"Could not parse Bible reference: {reference}",
                verses_used=[],
                metadata={"reference": reference}
            )
        
        book, chapter, verse = parsed_ref
        
        # Get the target verse
        target_verse = self.BibleParser.GetVerse(translation, book, chapter, verse)
        if not target_verse:
            return AgentResponse(
                success=False,
                content=f"Verse not found: {reference}",
                verses_used=[],
                metadata={"reference": reference, "parsed": parsed_ref}
            )
        
        # Find related verses based on content
        related_verses = self._FindRelatedVerses(target_verse, translation)
        
        # Analyze cross-references
        analysis_prompt = f"""
        Analyze this Bible verse and its cross-references:
        
        Main verse: {target_verse.book} {target_verse.chapter}:{target_verse.verse} - {target_verse.text}
        
        Related verses:
        {self._FormatVersesForAnalysis(related_verses)}
        
        Provide:
        1. Brief explanation of the main verse
        2. How the related verses connect to or expand on the main verse
        3. Key themes and theological connections
        4. Practical applications or insights
        
        Structure this as a helpful Bible study resource.
        """
        
        analysis_response = self.LlmClient.GenerateResponse([
            {"role": "user", "content": analysis_prompt}
        ])
        
        if not analysis_response:
            return AgentResponse(
                success=False,
                content="Failed to analyze cross-references.",
                verses_used=[target_verse] + related_verses,
                metadata={"reference": reference, "parsed": parsed_ref}
            )
        
        return AgentResponse(
            success=True,
            content=analysis_response,
            verses_used=[target_verse] + related_verses,
            metadata={
                "reference": reference,
                "parsed": parsed_ref,
                "related_count": len(related_verses)
            }
        )
    
    ## Parse a Bible reference string.
    ## @param[in] reference - Bible reference string to parse.
    ## @return Tuple of (book, chapter, verse) if successful, None otherwise.
    def _ParseReference(self, reference: str) -> Optional[tuple]:
        import re
        
        # Regex group indices for Bible reference parsing
        BOOK_GROUP_INDEX = 1
        CHAPTER_GROUP_INDEX = 2
        VERSE_GROUP_INDEX = 3
        
        # Simple parsing for common formats like "John 3:16"
        # Pattern for "Book Chapter:Verse" format - handles numbered books and multi-word book names
        # Must end with verse number, not followed by additional content
        pattern = r'(\d*\s*\w+(?:\s+\w+)*)\s+(\d+):(\d+)$'
        match = re.search(pattern, reference.strip())
        
        if match:
            book = match.group(BOOK_GROUP_INDEX)
            chapter = int(match.group(CHAPTER_GROUP_INDEX))
            verse = int(match.group(VERSE_GROUP_INDEX))
            return (book, chapter, verse)        
        return None
    
    ## Find verses related to the target verse.
    ## @param[in] target_verse - The verse to find related verses for.
    ## @param[in] translation - Bible translation to use.
    ## @param[in] max_related - Maximum number of related verses to find.
    ## @return List of related Bible verses.
    def _FindRelatedVerses(self, target_verse: BibleVerse, translation: str, 
                           max_related: int = DEFAULT_CROSS_REFERENCE_MAX_RELATED) -> list[BibleVerse]:
        # Extract key terms from the target verse
        key_terms = self._ExtractKeyTerms(target_verse.text)
        
        if not key_terms:
            return []
        
        # Search for verses containing these terms
        related_verses = self.BibleParser.GetVersesByTopicKeywords(
            key_terms, translation=translation, max_results=max_related * 2
        )
        
        # Filter out the target verse itself
        related_verses = [v for v in related_verses if v.osis_id != target_verse.osis_id]
        
        return related_verses[:max_related]
    
    ## Extract key terms from verse text for cross-reference search.
    ## @param[in] text - Verse text to extract terms from.
    ## @return List of key terms.
    def _ExtractKeyTerms(self, text: str) -> list[str]:
        import re
        
        # Remove punctuation and split into words
        clean_text = re.sub(r'[^\w\s]', ' ', text)
        words = clean_text.split()
        
        # Extract words with length greater than or equal to 4 characters
        key_terms = [word.lower() for word in words if len(word) >= MIN_WORD_LENGTH_FOR_KEYWORDS]
        
        # Remove common words
        common_words = {'which', 'that', 'this', 'with', 'from', 'they', 'have', 'were', 'said', 'unto', 'them', 'will', 'shall'}
        key_terms = [term for term in key_terms if term not in common_words]
        
        # Return all terms to ensure we don't miss any important ones
        return key_terms
    
    ## Format verses for LLM analysis.
    ## @param[in] verses - List of Bible verses to format.
    ## @return Formatted string of verses.
    def _FormatVersesForAnalysis(self, verses: list[BibleVerse]) -> str:
        formatted = []
        for verse in verses:
            formatted.append(f"{verse.book} {verse.chapter}:{verse.verse} - {verse.text}")
        return "\n".join(formatted) 