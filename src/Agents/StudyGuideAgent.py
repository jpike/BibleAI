## @package StudyGuideAgent
## Agent for creating comprehensive Bible study guides.

from typing import Any, Optional

from BibleParser import BibleVerse, BibleParser
from LlmClient import LLMClient
from Agents.AgentResponse import AgentResponse
from Agents.TopicResearchAgent import TopicResearchAgent

# Agent Constants
DEFAULT_STUDY_GUIDE_MAX_VERSES = 30

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