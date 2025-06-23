## @package BibleChatAgent
## Agent for interactive Bible chat with RAG capabilities.

from typing import List, Dict, Any, Optional
import json

from BibleParser import BibleParser, BibleVerse
from StudyNotesParser import StudyNotesParser, StudyNote
from EmbeddingsManager import EmbeddingsManager
from RetrievalEngine import RetrievalEngine
from LlmClient import LLMClient
from Agents.AgentResponse import AgentResponse

# Chat Agent Constants
DEFAULT_MAX_BIBLE_VERSES = 10
DEFAULT_MAX_STUDY_NOTES = 5
CHAT_SESSION_MAX_HISTORY = 10

## Agent for interactive Bible chat with RAG capabilities.
class BibleChatAgent:
    ## Initialize the Bible chat agent.
    ## @param[in] bible_parser - Initialized Bible parser instance.
    ## @param[in] study_notes_parser - Initialized study notes parser instance.
    ## @param[in] embeddings_manager - Initialized embeddings manager instance.
    ## @param[in] retrieval_engine - Initialized retrieval engine instance.
    ## @param[in] llm_client - Initialized LLM client instance.
    def __init__(self, bible_parser: 'BibleParser', study_notes_parser: 'StudyNotesParser',
                 embeddings_manager: 'EmbeddingsManager', retrieval_engine: 'RetrievalEngine',
                 llm_client: 'LLMClient'):
        ## Bible parser for accessing Bible data.
        self.BibleParser: "BibleParser" = bible_parser
        ## Study notes parser for accessing study notes.
        self.StudyNotesParser: "StudyNotesParser" = study_notes_parser
        ## Embeddings manager for semantic search.
        self.EmbeddingsManager: "EmbeddingsManager" = embeddings_manager
        ## Retrieval engine for content retrieval.
        self.RetrievalEngine: "RetrievalEngine" = retrieval_engine
        ## LLM client for AI interactions.
        self.LlmClient: "LLMClient" = llm_client
        ## Chat session history for context.
        self.ChatHistory: List[Dict[str, str]] = []
        
    ## Process a chat message and generate a response.
    ## @param[in] user_message - The user's message.
    ## @param[in] max_bible_verses - Maximum number of Bible verses to include.
    ## @param[in] max_study_notes - Maximum number of study notes to include.
    ## @return AgentResponse with chat response.
    def ProcessChatMessage(self, user_message: str, max_bible_verses: int = DEFAULT_MAX_BIBLE_VERSES,
                          max_study_notes: int = DEFAULT_MAX_STUDY_NOTES) -> AgentResponse:
        # Add user message to chat history
        self._AddToChatHistory("user", user_message)
        
        # Retrieve relevant content
        retrieved_content = self.RetrievalEngine.RetrieveContent(
            user_message, max_bible_verses, max_study_notes
        )
        
        # Generate response using LLM
        response = self._GenerateChatResponse(user_message, retrieved_content)
        
        # Add assistant response to chat history
        if response.success:
            self._AddToChatHistory("assistant", response.content)
        
        return response
    
    ## Generate a chat response using the LLM with retrieved content.
    ## @param[in] user_message - The user's message.
    ## @param[in] retrieved_content - Retrieved Bible verses and study notes.
    ## @return AgentResponse with generated response.
    def _GenerateChatResponse(self, user_message: str, retrieved_content: Dict[str, Any]) -> AgentResponse:
        # Format retrieved content for the LLM
        formatted_content = self._FormatRetrievedContent(retrieved_content)
        
        # Create the prompt for the LLM
        prompt = self._CreateChatPrompt(user_message, formatted_content)
        
        # Generate response from LLM
        llm_response = self.LlmClient.GenerateResponse([
            {"role": "user", "content": prompt}
        ])
        
        if not llm_response:
            return AgentResponse(
                success=False,
                content="I apologize, but I'm having trouble generating a response right now. Please try again.",
                verses_used=retrieved_content.get('bible_verses', []),
                metadata={
                    'query': user_message,
                    'retrieved_bible_count': len(retrieved_content.get('bible_verses', [])),
                    'retrieved_study_count': len(retrieved_content.get('study_notes', []))
                }
            )
        
        return AgentResponse(
            success=True,
            content=llm_response,
            verses_used=retrieved_content.get('bible_verses', []),
            metadata={
                'query': user_message,
                'retrieved_bible_count': len(retrieved_content.get('bible_verses', [])),
                'retrieved_study_count': len(retrieved_content.get('study_notes', [])),
                'study_notes_used': retrieved_content.get('study_notes', [])
            }
        )
    
    ## Format retrieved content for LLM consumption.
    ## @param[in] retrieved_content - Retrieved content from the retrieval engine.
    ## @return Formatted string of retrieved content.
    def _FormatRetrievedContent(self, retrieved_content: Dict[str, Any]) -> str:
        formatted_parts = []
        
        # Format Bible verses
        bible_verses = retrieved_content.get('bible_verses', [])
        if bible_verses:
            formatted_parts.append("BIBLE VERSES:")
            for i, verse in enumerate(bible_verses, 1):
                formatted_parts.append(f"{i}. {verse.book} {verse.chapter}:{verse.verse} ({verse.translation})")
                formatted_parts.append(f"   {verse.text}")
                formatted_parts.append("")
        
        # Format study notes
        study_notes = retrieved_content.get('study_notes', [])
        if study_notes:
            formatted_parts.append("BIBLE STUDY NOTES:")
            for i, note in enumerate(study_notes, 1):
                formatted_parts.append(f"{i}. {note.chapter_topic} (from {note.book})")
                # Include a preview of the study note content
                content_preview = note.content[:500] + "..." if len(note.content) > 500 else note.content
                formatted_parts.append(f"   {content_preview}")
                formatted_parts.append("")
        
        return "\n".join(formatted_parts)
    
    ## Create a prompt for the LLM with context and instructions.
    ## @param[in] user_message - The user's message.
    ## @param[in] formatted_content - Formatted retrieved content.
    ## @return Complete prompt for the LLM.
    def _CreateChatPrompt(self, user_message: str, formatted_content: str) -> str:
        # Create context from chat history
        context = self._CreateChatContext()
        
        prompt = f"""You are a helpful Bible study assistant. You can ONLY reference and quote from the Bible verses and study notes provided below. Do not use any external knowledge or sources.

IMPORTANT RULES:
1. ONLY reference the Bible verses and study notes provided below
2. Quote Bible verses in full when referencing them
3. Include translation information (YLT, KJV, WEB) when quoting verses
4. Reference study notes when they are relevant to the question
5. If the provided content doesn't address the question, say so clearly
6. Be respectful and helpful in your responses
7. Focus on biblical accuracy and clarity

{context}

AVAILABLE CONTENT:
{formatted_content}

USER QUESTION: {user_message}

Please provide a comprehensive response that directly addresses the user's question using ONLY the content provided above. Include relevant Bible verses in full and reference study notes when applicable."""

        return prompt
    
    ## Create context from chat history.
    ## @return Formatted chat context string.
    def _CreateChatContext(self) -> str:
        if not self.ChatHistory:
            return ""
        
        # Take the last few messages for context
        recent_history = self.ChatHistory[-CHAT_SESSION_MAX_HISTORY:]
        
        context_parts = ["RECENT CONVERSATION CONTEXT:"]
        for message in recent_history:
            role = message['role']
            content = message['content']
            # Truncate long messages for context
            if len(content) > 200:
                content = content[:200] + "..."
            context_parts.append(f"{role.upper()}: {content}")
        
        return "\n".join(context_parts) + "\n"
    
    ## Add a message to the chat history.
    ## @param[in] role - Role of the message sender ("user" or "assistant").
    ## @param[in] content - Content of the message.
    def _AddToChatHistory(self, role: str, content: str) -> None:
        self.ChatHistory.append({
            'role': role,
            'content': content
        })
        
        # Keep only the last N messages
        if len(self.ChatHistory) > CHAT_SESSION_MAX_HISTORY * 2:
            self.ChatHistory = self.ChatHistory[-CHAT_SESSION_MAX_HISTORY:]
    
    ## Clear the chat history.
    def ClearChatHistory(self) -> None:
        self.ChatHistory = []
    
    ## Get the current chat history.
    ## @return List of chat history messages.
    def GetChatHistory(self) -> List[Dict[str, str]]:
        return self.ChatHistory.copy()
    
    ## Get statistics about the chat session.
    ## @return Dictionary with chat statistics.
    def GetChatStats(self) -> Dict[str, Any]:
        user_messages = len([msg for msg in self.ChatHistory if msg['role'] == 'user'])
        assistant_messages = len([msg for msg in self.ChatHistory if msg['role'] == 'assistant'])
        
        return {
            'total_messages': len(self.ChatHistory),
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'session_active': len(self.ChatHistory) > 0
        } 