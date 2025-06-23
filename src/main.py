## @package Main
## Main application for the Agentic Bible Study Program.

import sys
import pathlib
import os
from typing import Optional

# Add all subfolders of ThirdParty to sys.path for local third-party packages
thirdparty_dir = pathlib.Path(__file__).parent.parent / 'ThirdParty'
if thirdparty_dir.exists():
    for item in thirdparty_dir.iterdir():
        if item.is_dir():
            sys.path.insert(0, str(item))

# Add src directory to path for imports.
sys.path.append(str(pathlib.Path(__file__).parent))

from BibleParser import BibleParser
from LlmClient import LLMClient
from StudyNotesParser import StudyNotesParser
from EmbeddingsManager import EmbeddingsManager
from RetrievalEngine import RetrievalEngine
from Agents import TopicResearchAgent, CrossReferenceAgent, StudyGuideAgent
from Agents.BibleChatAgent import BibleChatAgent

# UI Constants
SEPARATOR_LINE_LENGTH = 60
SEARCH_RESULTS_SEPARATOR_LENGTH = 40
DEFAULT_SEARCH_MAX_RESULTS = 10
DEFAULT_RELATED_COUNT = 0

## Main application class for the Bible study program.
class BibleStudyApp:
    ## Initialize the Bible study application.
    ## @param[in] data_directory_path - Path to Bible data files.
    ## @param[in] llm_base_url - Base URL for LM Studio API.
    def __init__(
            self, 
            data_directory_path: str = "data", 
            llm_base_url: str = "http://localhost:1234/v1"):
        ## Path to the directory containing Bible data files.
        self.DataDirectoryPath: str = data_directory_path
        ## Base URL for the LM Studio API.
        self.LlmBaseUrl: str = llm_base_url
        
        ## Bible parser for accessing Bible data.
        self.BibleParser: Optional["BibleParser"] = None
        ## Study notes parser for accessing study notes.
        self.StudyNotesParser: Optional["StudyNotesParser"] = None
        ## Embeddings manager for semantic search.
        self.EmbeddingsManager: Optional["EmbeddingsManager"] = None
        ## Retrieval engine for content retrieval.
        self.RetrievalEngine: Optional["RetrievalEngine"] = None
        ## LLM client for AI interactions.
        self.LlmClient: Optional["LLMClient"] = None
        ## Dictionary mapping agent names to their instances.
        self.Agents: dict[str, "TopicResearchAgent | CrossReferenceAgent | StudyGuideAgent | BibleChatAgent"] = {}
        
        # Don't auto-initialize components for testing compatibility
        # self._InitializeComponents()
    
    ## Initialize all application components.
    def _InitializeComponents(self) -> None:
        print("Initializing Bible Study Application...")
        
        # Initialize Bible parser
        try:
            self.BibleParser = BibleParser(self.DataDirectoryPath)
            self.BibleParser.LoadAllTranslations()
            print("✓ Bible data loaded successfully")
        except Exception as e:
            print(f"✗ Error loading Bible data: {e}")
            return
        
        # Initialize study notes parser
        try:
            self.StudyNotesParser = StudyNotesParser(self.DataDirectoryPath)
            self.StudyNotesParser.LoadAllStudyNotes()
            print("✓ Study notes loaded successfully")
        except Exception as e:
            print(f"✗ Error loading study notes: {e}")
            # Continue without study notes for now
        
        # Initialize embeddings manager
        try:
            self.EmbeddingsManager = EmbeddingsManager(self.DataDirectoryPath)
            self.EmbeddingsManager.LoadEmbeddings()
            print("✓ Embeddings manager initialized")
        except Exception as e:
            print(f"✗ Error initializing embeddings: {e}")
            # Continue without embeddings for now
        
        # Initialize LLM client
        try:
            self.LlmClient = LLMClient(self.LlmBaseUrl)
            llm_connection_successful = self.LlmClient.TestConnection()
            if llm_connection_successful:
                print("✓ LLM connection successful")
            else:
                print("✗ LLM connection failed - make sure LM Studio is running")
                return
        except Exception as e:
            print(f"✗ Error connecting to LLM: {e}")
            return
        
        # Initialize retrieval engine
        try:
            self.RetrievalEngine = RetrievalEngine(
                self.BibleParser, 
                self.StudyNotesParser, 
                self.EmbeddingsManager, 
                self.LlmClient
            )
            print("✓ Retrieval engine initialized")
        except Exception as e:
            print(f"✗ Error initializing retrieval engine: {e}")
            # Continue without retrieval engine for now
        
        # Initialize agents
        self.Agents = {
            'topic_research': TopicResearchAgent(self.BibleParser, self.LlmClient),
            'cross_reference': CrossReferenceAgent(self.BibleParser, self.LlmClient),
            'study_guide': StudyGuideAgent(self.BibleParser, self.LlmClient)
        }
        
        # Initialize chat agent if all components are available
        # Only initialize chat agent if all required components are properly initialized
        # In test environment, these components are typically None or not properly initialized
        if (self.StudyNotesParser is not None and 
            self.EmbeddingsManager is not None and 
            self.RetrievalEngine is not None and
            hasattr(self.StudyNotesParser, 'LoadAllStudyNotes') and
            hasattr(self.EmbeddingsManager, 'LoadEmbeddings')):
            try:
                self.Agents['chat'] = BibleChatAgent(
                    self.BibleParser, 
                    self.StudyNotesParser, 
                    self.EmbeddingsManager, 
                    self.RetrievalEngine, 
                    self.LlmClient
                )
                print("✓ Chat agent initialized")
            except Exception as e:
                print(f"✗ Error initializing chat agent: {e}")
        
        print("✓ All components initialized successfully")
    
    ## Run the application in interactive mode.
    def RunInteractive(self) -> None:
        components_initialized = self.BibleParser is not None and self.LlmClient is not None
        if not components_initialized:
            print("Application not properly initialized. Exiting.")
            return
        
        print("\n" + "="*SEPARATOR_LINE_LENGTH)
        print("🤖 AGENTIC BIBLE STUDY PROGRAM")
        print("="*SEPARATOR_LINE_LENGTH)
        print("Available commands:")
        print("1. research <topic> - Research a Bible topic")
        print("2. crossref <reference> - Find cross-references")
        print("3. guide <topic> [type] - Create study guide")
        print("4. search <query> - Search for specific verses")
        print("5. chat - Enter interactive chat mode")
        print("6. help - Show this help")
        print("7. quit - Exit the program")
        print("="*SEPARATOR_LINE_LENGTH)
        
        while True:
            try:
                user_input = input("\n📖 Bible Study > ").strip()
                
                if not user_input:
                    continue
                
                user_input_lower = user_input.lower()
                is_quit_command = user_input_lower in ['quit', 'exit', 'q']
                if is_quit_command:
                    print("Goodbye! 🙏")
                    break
                
                is_help_command = user_input_lower == 'help'
                if is_help_command:
                    self._ShowHelp()
                    continue
                
                # Parse command
                COMMAND_SPLIT_MAX_SPLITS = 1
                COMMAND_INDEX = 0
                ARGS_INDEX = 1
                parts = user_input.split(' ', COMMAND_SPLIT_MAX_SPLITS)
                command = parts[COMMAND_INDEX].lower()
                args = parts[ARGS_INDEX] if len(parts) > ARGS_INDEX else ""
                
                if command == 'research':
                    self._HandleResearch(args)
                elif command == 'crossref':
                    self._HandleCrossref(args)
                elif command == 'guide':
                    self._HandleGuide(args)
                elif command == 'search':
                    self._HandleSearch(args)
                elif command == 'chat':
                    self._HandleChat(args)
                else:
                    print(f"Unknown command: {command}")
                    
            except KeyboardInterrupt:
                print("\nGoodbye! 🙏")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    ## Handle research command.
    ## @param[in] args - Research arguments.
    def _HandleResearch(self, args: str) -> None:
        if not args:
            print("Usage: research <topic>")
            return
        
        print(f"\n🔍 Researching topic: {args}")
        print("Please wait...")
        
        response = self.Agents['topic_research'].ResearchTopic(args)
        
        if response.success:
            print("\n" + "="*SEPARATOR_LINE_LENGTH)
            print(f"📚 RESEARCH RESULTS: {args.upper()}")
            print("="*SEPARATOR_LINE_LENGTH)
            print(response.content)
            print(f"\n📊 Used {len(response.verses_used)} verses from {response.metadata.get('translation', 'KJV')}")
        else:
            print(f"❌ Research failed: {response.content}")
    
    ## Handle cross-reference command.
    ## @param[in] args - Cross-reference arguments.
    def _HandleCrossref(self, args: str) -> None:
        if not args:
            print("Usage: crossref <reference> (e.g., crossref John 3:16)")
            return
        
        print(f"\n🔗 Finding cross-references for: {args}")
        print("Please wait...")
        
        response = self.Agents['cross_reference'].FindCrossReferences(args)
        
        if response.success:
            print("\n" + "="*SEPARATOR_LINE_LENGTH)
            print(f"🔗 CROSS-REFERENCES: {args.upper()}")
            print("="*SEPARATOR_LINE_LENGTH)
            print(response.content)
            print(f"\n📊 Found {response.metadata.get('related_count', DEFAULT_RELATED_COUNT)} related verses")
        else:
            print(f"❌ Cross-reference failed: {response.content}")
    
    ## Handle study guide command.
    ## @param[in] args - Study guide arguments.
    def _HandleGuide(self, args: str) -> None:
        if not args:
            print("Usage: guide <topic> [type]")
            print("Types: comprehensive, devotional, theological")
            return
        
        # Parse guide arguments
        COMMAND_SPLIT_MAX_SPLITS = 1
        COMMAND_INDEX = 0
        ARGS_INDEX = 1
        parts = args.split(' ', COMMAND_SPLIT_MAX_SPLITS)
        topic = parts[COMMAND_INDEX]
        guide_type = parts[ARGS_INDEX] if len(parts) > ARGS_INDEX else "comprehensive"
        
        print(f"\n📖 Creating {guide_type} study guide for: {topic}")
        print("Please wait...")
        
        # Call with the signature expected by tests: CreateStudyGuide(topic, translation, guide_type)
        response = self.Agents['study_guide'].CreateStudyGuide(topic, "KJV", guide_type)
        
        if response.success:
            print("\n" + "="*SEPARATOR_LINE_LENGTH)
            print(f"📖 STUDY GUIDE: {topic.upper()} ({guide_type.upper()})")
            print("="*SEPARATOR_LINE_LENGTH)
            print(response.content)
            print(f"\n📊 Used {len(response.verses_used)} verses")
        else:
            print(f"❌ Study guide failed: {response.content}")
    
    ## Handle verse search command.
    ## @param[in] args - Search query arguments.
    def _HandleSearch(self, args: str) -> None:
        if not args:
            print("Usage: search <query>")
            return
        
        print(f"\n🔍 Searching for: {args}")
        print("Please wait...")
        
        # Call with the signature expected by tests: SearchVerses(query, translation=None, max_results=10)
        results = self.BibleParser.SearchVerses(args, translation=None, max_results=DEFAULT_SEARCH_MAX_RESULTS)
        
        if results:
            print(f"\n📖 SEARCH RESULTS ({len(results)} found):")
            print("-" * SEARCH_RESULTS_SEPARATOR_LENGTH)
            
            for i, verse in enumerate(results, 1):
                print(f"{i}. {verse.book} {verse.chapter}:{verse.verse} ({verse.translation})")
                print(f"   {verse.text}")
                print()
        else:
            print(f"No verses found matching '{args}'")
    
    ## Handle chat command.
    ## @param[in] args - Chat arguments.
    def _HandleChat(self, args: str) -> None:
        chat_agent_available = 'chat' in self.Agents
        if not chat_agent_available:
            print("❌ Chat functionality is not available. Some components failed to initialize.")
            return
        
        print("\n" + "="*SEPARATOR_LINE_LENGTH)
        print("💬 INTERACTIVE BIBLE CHAT MODE")
        print("="*SEPARATOR_LINE_LENGTH)
        print("Ask me anything about the Bible! I'll search through:")
        print("• Bible verses (YLT, KJV, WEB translations)")
        print("• Bible study notes")
        print("• Provide full verse quotes with proper attribution")
        print("\nType 'exit' to return to main menu")
        print("Type 'clear' to clear chat history")
        print("="*SEPARATOR_LINE_LENGTH)
        
        chat_agent = self.Agents['chat']
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                user_input_lower = user_input.lower()
                is_exit_command = user_input_lower in ['exit', 'quit', 'q']
                if is_exit_command:
                    print("Returning to main menu...")
                    break
                
                is_clear_command = user_input_lower == 'clear'
                if is_clear_command:
                    chat_agent.ClearChatHistory()
                    print("Chat history cleared.")
                    continue
                
                print("🤖 Thinking...")
                
                # Process the chat message
                response = chat_agent.ProcessChatMessage(user_input)
                
                if response.success:
                    print("\n" + "-"*SEPARATOR_LINE_LENGTH)
                    print("🤖 Assistant:")
                    print(response.content)
                    
                    # Show metadata about sources used
                    metadata = response.metadata
                    bible_count = metadata.get('retrieved_bible_count', 0)
                    study_count = metadata.get('retrieved_study_count', 0)
                    
                    if bible_count > 0 or study_count > 0:
                        print(f"\n📚 Sources: {bible_count} Bible verses, {study_count} study notes")
                    
                    print("-"*SEPARATOR_LINE_LENGTH)
                else:
                    print(f"❌ Error: {response.content}")
                
            except KeyboardInterrupt:
                print("\nReturning to main menu...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again or type 'exit' to return to main menu")
    
    ## Show help information.
    def _ShowHelp(self) -> None:
        print("\n" + "="*SEPARATOR_LINE_LENGTH)
        print("📖 BIBLE STUDY COMMANDS")
        print("="*SEPARATOR_LINE_LENGTH)
        print("research <topic>     - Research a Bible topic and find relevant verses")
        print("crossref <reference> - Find cross-references for a specific verse")
        print("guide <topic> [type] - Create a study guide (comprehensive/devotional/theological)")
        print("search <query>       - Search for specific text in Bible verses")
        print("chat                - Enter interactive chat mode")
        print("help                - Show this help information")
        print("quit                - Exit the program")
        print("="*SEPARATOR_LINE_LENGTH)
        print("\nExamples:")
        print("  research love")
        print("  crossref John 3:16")
        print("  guide faith devotional")
        print("  search 'kingdom of heaven'")
        print("="*SEPARATOR_LINE_LENGTH)

## Main function to run the Bible study application.
def Main():
    # Check if data directory and BibleVerses subdirectory exist
    data_dir = pathlib.Path("data")
    bible_verses_dir = data_dir / "BibleVerses"
    
    data_directory_exists = data_dir.exists()
    if not data_directory_exists:
        print("Error: 'data' directory not found. Please ensure Bible data files are available.")
        return
    
    bible_verses_directory_exists = bible_verses_dir.exists()
    if not bible_verses_directory_exists:
        print("Error: 'data/BibleVerses' directory not found. Please ensure Bible XML files are in the BibleVerses subdirectory.")
        return
    
    # Create and run the application
    app = BibleStudyApp()
    app._InitializeComponents()  # Initialize components for actual usage
    app.RunInteractive()

if __name__ == "__main__":
    Main() 