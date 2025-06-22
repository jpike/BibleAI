## @package TopicResearchAgent
## Agent for researching Bible topics and finding relevant verses.

from typing import Any, Optional

from BibleParser import BibleVerse, BibleParser
from LlmClient import LLMClient
from Agents.AgentResponse import AgentResponse

# Agent Constants
DEFAULT_TOPIC_RESEARCH_MAX_VERSES = 20

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