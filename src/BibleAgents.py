## @package BibleAgents
## AI Agents for Bible study tasks including topic research, cross-references, and study guides.

import dataclasses
from typing import Any, Optional

from BibleParser import BibleVerse, BibleParser
from LlmClient import LLMClient

# Agent Constants
DEFAULT_TOPIC_RESEARCH_MAX_VERSES = 20
DEFAULT_CROSS_REFERENCE_MAX_RELATED = 15
DEFAULT_STUDY_GUIDE_MAX_VERSES = 30
DEFAULT_KEYWORD_COUNT = 5
MIN_WORD_LENGTH_FOR_KEYWORDS = 4

## Response from a Bible study agent.
@dataclasses.dataclass
class AgentResponse:
    success: bool
    content: str
    verses_used: list[BibleVerse]
    metadata: dict[str, Any]


## Agent for researching Bible topics and finding relevant verses.
class TopicResearchAgent:
    ## Initialize the topic research agent.
    ## @param[in] bible_parser - Initialized Bible parser instance.
    ## @param[in] llm_client - Initialized LLM client instance.
    def __init__(self, bible_parser: 'BibleParser', llm_client: 'LLMClient'):
        ## Bible parser for accessing Bible data.
        self.BibleParser: "BibleParser" = bible_parser
        ## LLM client for AI interactions.
        self.LlmClient: "LLMClient" = llm_client
        
    ## Research a Bible topic and find relevant verses.
    ## @param[in] topic - The topic to research.
    ## @param[in] translation - Bible translation to use.
    ## @param[in] max_verses - Maximum number of verses to include.
    ## @return AgentResponse with research results.
    def ResearchTopic(self, topic: str, translation: str = "KJV", 
                      max_verses: int = DEFAULT_TOPIC_RESEARCH_MAX_VERSES) -> AgentResponse:
        # Generate keywords for the topic
        keyword_prompt = f"""
        Given the topic "{topic}", generate 5-10 relevant keywords that would help find Bible verses about this topic.
        Focus on biblical terms, concepts, and themes related to this topic.
        Return only the keywords, one per line, without numbering or extra text.
        """
        
        keywords_response = self.LlmClient.GenerateResponse([
            {"role": "user", "content": keyword_prompt}
        ])
        
        if not keywords_response:
            return AgentResponse(
                success=False,
                content="Failed to generate keywords for topic research.",
                verses_used=[],
                metadata={"topic": topic}
            )
        
        # Extract keywords
        keywords = [kw.strip() for kw in keywords_response.split('\n') if kw.strip()]
        
        # Search for relevant verses
        relevant_verses = self.BibleParser.GetVersesByTopicKeywords(
            keywords, translation=translation, max_results=max_verses * 2
        )
        
        if not relevant_verses:
            return AgentResponse(
                success=False,
                content=f"No relevant verses found for topic: {topic}",
                verses_used=[],
                metadata={"topic": topic, "keywords": keywords}
            )
        
        # Analyze and organize the verses
        analysis_prompt = f"""
        Analyze these Bible verses related to the topic "{topic}" and provide:
        
        1. A brief overview of what the Bible says about this topic
        2. Key themes and patterns
        3. Organized presentation of the verses with brief explanations
        
        Verses to analyze:
        {self._FormatVersesForAnalysis(relevant_verses[:max_verses])}
        
        Provide a well-structured response that would be helpful for Bible study.
        """
        
        analysis_response = self.LlmClient.GenerateResponse([
            {"role": "user", "content": analysis_prompt}
        ])
        
        if not analysis_response:
            return AgentResponse(
                success=False,
                content="Failed to analyze verses for topic research.",
                verses_used=relevant_verses[:max_verses],
                metadata={"topic": topic, "keywords": keywords}
            )
        
        return AgentResponse(
            success=True,
            content=analysis_response,
            verses_used=relevant_verses[:max_verses],
            metadata={
                "topic": topic,
                "keywords": keywords,
                "translation": translation,
                "verse_count": len(relevant_verses[:max_verses])
            }
        )
    
    ## Format verses for LLM analysis.
    ## @param[in] verses - List of Bible verses to format.
    ## @return Formatted string of verses.
    def _FormatVersesForAnalysis(self, verses: list[BibleVerse]) -> str:
        formatted = []
        for verse in verses:
            formatted.append(f"{verse.book} {verse.chapter}:{verse.verse} ({verse.translation}) - {verse.text}")
        return "\n".join(formatted)


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
        # Pattern for "Book Chapter:Verse" format
        pattern = r'(\w+)\s+(\d+):(\d+)'
        match = re.search(pattern, reference)
        
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
        # Simple approach: extract words longer than 4 characters
        words = text.split()
        key_terms = [word.lower() for word in words if len(word) > MIN_WORD_LENGTH_FOR_KEYWORDS]
        
        # Remove common words
        common_words = {'which', 'that', 'this', 'with', 'from', 'they', 'have', 'were', 'said', 'unto', 'them', 'will', 'shall'}
        key_terms = [term for term in key_terms if term not in common_words]
        
        return key_terms[:DEFAULT_KEYWORD_COUNT]  # Return top 5 terms
    
    ## Format verses for LLM analysis.
    ## @param[in] verses - List of Bible verses to format.
    ## @return Formatted string of verses.
    def _FormatVersesForAnalysis(self, verses: list[BibleVerse]) -> str:
        formatted = []
        for verse in verses:
            formatted.append(f"{verse.book} {verse.chapter}:{verse.verse} - {verse.text}")
        return "\n".join(formatted)


## Agent for creating comprehensive Bible study guides.
class StudyGuideAgent:
    ## Initialize the study guide agent.
    ## @param[in] bible_parser - Initialized Bible parser instance.
    ## @param[in] llm_client - Initialized LLM client instance.
    def __init__(self, bible_parser: BibleParser, llm_client: LLMClient):
        ## Bible parser for accessing Bible data.
        self.BibleParser: "BibleParser" = bible_parser
        ## LLM client for AI interactions.
        self.LlmClient: "LLMClient" = llm_client
    
    ## Create a comprehensive Bible study guide.
    ## @param[in] topic - The topic for the study guide.
    ## @param[in] translation - Bible translation to use.
    ## @param[in] guide_type - Type of guide ("comprehensive", "devotional", "theological").
    ## @return AgentResponse with the study guide.
    def CreateStudyGuide(self, topic: str, translation: str = "KJV", 
                          guide_type: str = "comprehensive") -> AgentResponse:
        # First, research the topic to get relevant verses
        topic_agent = TopicResearchAgent(self.BibleParser, self.LlmClient)
        topic_research = topic_agent.ResearchTopic(topic, translation, max_verses=DEFAULT_STUDY_GUIDE_MAX_VERSES)
        
        if not topic_research.success:
            return topic_research
        
        # Create the study guide based on type
        if guide_type == "comprehensive":
            return self._CreateComprehensiveGuide(topic, topic_research.verses_used)
        elif guide_type == "devotional":
            return self._CreateDevotionalGuide(topic, topic_research.verses_used)
        elif guide_type == "theological":
            return self._CreateTheologicalGuide(topic, topic_research.verses_used)
        else:
            return self._CreateComprehensiveGuide(topic, topic_research.verses_used)
    
    ## Create a comprehensive study guide.
    ## @param[in] topic - The topic for the study guide.
    ## @param[in] verses - List of Bible verses to use.
    ## @return AgentResponse with the comprehensive guide.
    def _CreateComprehensiveGuide(self, topic: str, verses: list[BibleVerse]) -> AgentResponse:
        guide_prompt = f"""
        Create a comprehensive Bible study guide on "{topic}" using these verses:
        
        {self._FormatVersesForAnalysis(verses)}
        
        Structure the guide with:
        1. Introduction and overview
        2. Key passages with explanations
        3. Main themes and principles
        4. Historical and cultural context
        5. Application questions
        6. Further study suggestions
        
        Make it suitable for group Bible study or personal study.
        """
        
        guide_content = self.LlmClient.GenerateResponse([
            {"role": "user", "content": guide_prompt}
        ])
        
        if not guide_content:
            return AgentResponse(
                success=False,
                content="Failed to create study guide.",
                verses_used=verses,
                metadata={"topic": topic, "guide_type": "comprehensive"}
            )
        
        return AgentResponse(
            success=True,
            content=guide_content,
            verses_used=verses,
            metadata={
                "topic": topic,
                "guide_type": "comprehensive",
                "verse_count": len(verses)
            }
        )
    
    ## Create a devotional study guide.
    ## @param[in] topic - The topic for the study guide.
    ## @param[in] verses - List of Bible verses to use.
    ## @return AgentResponse with the devotional guide.
    def _CreateDevotionalGuide(self, topic: str, verses: list[BibleVerse]) -> AgentResponse:
        guide_prompt = f"""
        Create a devotional Bible study guide on "{topic}" using these verses:
        
        {self._FormatVersesForAnalysis(verses)}
        
        Structure as a 7-day devotional with:
        - Daily scripture focus
        - Reflection questions
        - Prayer prompts
        - Personal application
        
        Make it encouraging and practical for daily spiritual growth.
        """
        
        guide_content = self.LlmClient.GenerateResponse([
            {"role": "user", "content": guide_prompt}
        ])
        
        if not guide_content:
            return AgentResponse(
                success=False,
                content="Failed to create devotional guide.",
                verses_used=verses,
                metadata={"topic": topic, "guide_type": "devotional"}
            )
        
        return AgentResponse(
            success=True,
            content=guide_content,
            verses_used=verses,
            metadata={
                "topic": topic,
                "guide_type": "devotional",
                "verse_count": len(verses)
            }
        )
    
    ## Create a theological study guide.
    ## @param[in] topic - The topic for the study guide.
    ## @param[in] verses - List of Bible verses to use.
    ## @return AgentResponse with the theological guide.
    def _CreateTheologicalGuide(self, topic: str, verses: list[BibleVerse]) -> AgentResponse:
        guide_prompt = f"""
        Create a theological Bible study guide on "{topic}" using these verses:
        
        {self._FormatVersesForAnalysis(verses)}
        
        Structure with:
        1. Biblical definition and scope
        2. Key theological concepts
        3. Systematic analysis of passages
        4. Historical development of the doctrine
        5. Contemporary implications
        6. Discussion questions for deeper study
        
        Focus on theological depth and academic rigor.
        """
        
        guide_content = self.LlmClient.GenerateResponse([
            {"role": "user", "content": guide_prompt}
        ])
        
        if not guide_content:
            return AgentResponse(
                success=False,
                content="Failed to create theological guide.",
                verses_used=verses,
                metadata={"topic": topic, "guide_type": "theological"}
            )
        
        return AgentResponse(
            success=True,
            content=guide_content,
            verses_used=verses,
            metadata={
                "topic": topic,
                "guide_type": "theological",
                "verse_count": len(verses)
            }
        )
    
    ## Format verses for LLM analysis.
    ## @param[in] verses - List of Bible verses to format.
    ## @return Formatted string of verses.
    def _FormatVersesForAnalysis(self, verses: list[BibleVerse]) -> str:
        formatted = []
        for verse in verses:
            formatted.append(f"{verse.book} {verse.chapter}:{verse.verse} - {verse.text}")
        return "\n".join(formatted) 