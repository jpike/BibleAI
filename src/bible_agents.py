"""
Bible Study Agents for different types of analysis and tasks.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .bible_parser import BibleVerse, BibleParser
from .llm_client import LLMClient


@dataclass
class AgentResponse:
    """Response from a Bible study agent."""
    success: bool
    content: str
    verses_used: List[BibleVerse]
    metadata: Dict[str, Any]


class TopicResearchAgent:
    """Agent for researching Bible topics and finding relevant verses."""
    
    def __init__(self, bible_parser: BibleParser, llm_client: LLMClient):
        """
        Initialize the topic research agent.
        
        Args:
            bible_parser: Initialized Bible parser instance.
            llm_client: Initialized LLM client instance.
        """
        self.bible_parser = bible_parser
        self.llm_client = llm_client
        
    def research_topic(self, topic: str, translation: str = "KJV", 
                      max_verses: int = 20) -> AgentResponse:
        """
        Research a Bible topic and find relevant verses.
        
        Args:
            topic: The topic to research.
            translation: Bible translation to use.
            max_verses: Maximum number of verses to include.
            
        Returns:
            AgentResponse with research results.
        """
        # Generate keywords for the topic
        keyword_prompt = f"""
        Given the topic "{topic}", generate 5-10 relevant keywords that would help find Bible verses about this topic.
        Focus on biblical terms, concepts, and themes related to this topic.
        Return only the keywords, one per line, without numbering or extra text.
        """
        
        keywords_response = self.llm_client.generate_response([
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
        relevant_verses = self.bible_parser.get_verses_by_topic_keywords(
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
        {self._format_verses_for_analysis(relevant_verses[:max_verses])}
        
        Provide a well-structured response that would be helpful for Bible study.
        """
        
        analysis_response = self.llm_client.generate_response([
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
    
    def _format_verses_for_analysis(self, verses: List[BibleVerse]) -> str:
        """Format verses for LLM analysis."""
        formatted = []
        for verse in verses:
            formatted.append(f"{verse.book} {verse.chapter}:{verse.verse} ({verse.translation}) - {verse.text}")
        return "\n".join(formatted)


class CrossReferenceAgent:
    """Agent for finding cross-references and related passages."""
    
    def __init__(self, bible_parser: BibleParser, llm_client: LLMClient):
        """
        Initialize the cross-reference agent.
        
        Args:
            bible_parser: Initialized Bible parser instance.
            llm_client: Initialized LLM client instance.
        """
        self.bible_parser = bible_parser
        self.llm_client = llm_client
    
    def find_cross_references(self, reference: str, translation: str = "KJV") -> AgentResponse:
        """
        Find cross-references for a given Bible reference.
        
        Args:
            reference: Bible reference (e.g., "John 3:16").
            translation: Bible translation to use.
            
        Returns:
            AgentResponse with cross-reference analysis.
        """
        # Parse the reference
        parsed_ref = self._parse_reference(reference)
        if not parsed_ref:
            return AgentResponse(
                success=False,
                content=f"Could not parse Bible reference: {reference}",
                verses_used=[],
                metadata={"reference": reference}
            )
        
        book, chapter, verse = parsed_ref
        
        # Get the target verse
        target_verse = self.bible_parser.get_verse(translation, book, chapter, verse)
        if not target_verse:
            return AgentResponse(
                success=False,
                content=f"Verse not found: {reference}",
                verses_used=[],
                metadata={"reference": reference, "parsed": parsed_ref}
            )
        
        # Find related verses based on content
        related_verses = self._find_related_verses(target_verse, translation)
        
        # Analyze cross-references
        analysis_prompt = f"""
        Analyze this Bible verse and its cross-references:
        
        Main verse: {target_verse.book} {target_verse.chapter}:{target_verse.verse} - {target_verse.text}
        
        Related verses:
        {self._format_verses_for_analysis(related_verses)}
        
        Provide:
        1. Brief explanation of the main verse
        2. How the related verses connect to or expand on the main verse
        3. Key themes and theological connections
        4. Practical applications or insights
        
        Structure this as a helpful Bible study resource.
        """
        
        analysis_response = self.llm_client.generate_response([
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
    
    def _parse_reference(self, reference: str) -> Optional[tuple]:
        """Parse a Bible reference string."""
        import re
        
        # Pattern for "Book Chapter:Verse" format
        pattern = r'(\w+)\s+(\d+):(\d+)'
        match = re.search(pattern, reference)
        
        if match:
            book = match.group(1)
            chapter = int(match.group(2))
            verse = int(match.group(3))
            return (book, chapter, verse)
        
        return None
    
    def _find_related_verses(self, target_verse: BibleVerse, translation: str, 
                           max_related: int = 15) -> List[BibleVerse]:
        """Find verses related to the target verse."""
        # Extract key terms from the target verse
        key_terms = self._extract_key_terms(target_verse.text)
        
        # Search for verses with similar terms
        related_verses = []
        for term in key_terms:
            matches = self.bible_parser.search_verses(term, translation, max_results=10)
            for match in matches:
                if match.osis_id != target_verse.osis_id and match not in related_verses:
                    related_verses.append(match)
                    if len(related_verses) >= max_related:
                        break
            if len(related_verses) >= max_related:
                break
        
        return related_verses[:max_related]
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from verse text for cross-reference search."""
        # Simple approach: extract words longer than 4 characters
        words = text.split()
        key_terms = [word.lower() for word in words if len(word) > 4]
        
        # Remove common words
        common_words = {'which', 'that', 'this', 'with', 'from', 'they', 'have', 'were', 'said', 'unto', 'them', 'will', 'shall'}
        key_terms = [term for term in key_terms if term not in common_words]
        
        return key_terms[:5]  # Return top 5 terms
    
    def _format_verses_for_analysis(self, verses: List[BibleVerse]) -> str:
        """Format verses for LLM analysis."""
        formatted = []
        for verse in verses:
            formatted.append(f"{verse.book} {verse.chapter}:{verse.verse} - {verse.text}")
        return "\n".join(formatted)


class StudyGuideAgent:
    """Agent for creating comprehensive Bible study guides."""
    
    def __init__(self, bible_parser: BibleParser, llm_client: LLMClient):
        """
        Initialize the study guide agent.
        
        Args:
            bible_parser: Initialized Bible parser instance.
            llm_client: Initialized LLM client instance.
        """
        self.bible_parser = bible_parser
        self.llm_client = llm_client
    
    def create_study_guide(self, topic: str, translation: str = "KJV", 
                          guide_type: str = "comprehensive") -> AgentResponse:
        """
        Create a comprehensive Bible study guide.
        
        Args:
            topic: The topic for the study guide.
            translation: Bible translation to use.
            guide_type: Type of guide ("comprehensive", "devotional", "theological").
            
        Returns:
            AgentResponse with the study guide.
        """
        # First, research the topic to get relevant verses
        topic_agent = TopicResearchAgent(self.bible_parser, self.llm_client)
        topic_research = topic_agent.research_topic(topic, translation, max_verses=30)
        
        if not topic_research.success:
            return topic_research
        
        # Create the study guide based on type
        if guide_type == "comprehensive":
            return self._create_comprehensive_guide(topic, topic_research.verses_used)
        elif guide_type == "devotional":
            return self._create_devotional_guide(topic, topic_research.verses_used)
        elif guide_type == "theological":
            return self._create_theological_guide(topic, topic_research.verses_used)
        else:
            return self._create_comprehensive_guide(topic, topic_research.verses_used)
    
    def _create_comprehensive_guide(self, topic: str, verses: List[BibleVerse]) -> AgentResponse:
        """Create a comprehensive study guide."""
        guide_prompt = f"""
        Create a comprehensive Bible study guide on "{topic}" using these verses:
        
        {self._format_verses_for_analysis(verses)}
        
        Structure the guide with:
        1. Introduction and overview
        2. Key passages with explanations
        3. Main themes and principles
        4. Historical and cultural context
        5. Application questions
        6. Further study suggestions
        
        Make it suitable for group Bible study or personal study.
        """
        
        guide_content = self.llm_client.generate_response([
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
    
    def _create_devotional_guide(self, topic: str, verses: List[BibleVerse]) -> AgentResponse:
        """Create a devotional study guide."""
        guide_prompt = f"""
        Create a devotional Bible study guide on "{topic}" using these verses:
        
        {self._format_verses_for_analysis(verses)}
        
        Structure as a 7-day devotional with:
        - Daily scripture focus
        - Reflection questions
        - Prayer prompts
        - Personal application
        
        Make it encouraging and practical for daily spiritual growth.
        """
        
        guide_content = self.llm_client.generate_response([
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
    
    def _create_theological_guide(self, topic: str, verses: List[BibleVerse]) -> AgentResponse:
        """Create a theological study guide."""
        guide_prompt = f"""
        Create a theological Bible study guide on "{topic}" using these verses:
        
        {self._format_verses_for_analysis(verses)}
        
        Structure with:
        1. Biblical definition and scope
        2. Key theological concepts
        3. Systematic analysis of passages
        4. Historical development of the doctrine
        5. Contemporary implications
        6. Discussion questions for deeper study
        
        Focus on theological depth and academic rigor.
        """
        
        guide_content = self.llm_client.generate_response([
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
    
    def _format_verses_for_analysis(self, verses: List[BibleVerse]) -> str:
        """Format verses for LLM analysis."""
        formatted = []
        for verse in verses:
            formatted.append(f"{verse.book} {verse.chapter}:{verse.verse} - {verse.text}")
        return "\n".join(formatted) 