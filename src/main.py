## @package Main
## Main application for the Agentic Bible Study Program.

import sys
import pathlib
from typing import Optional

# Add src directory to path for imports.
sys.path.append(str(pathlib.Path(__file__).parent))

from BibleParser import BibleParser
from LlmClient import LLMClient
from BibleAgents import TopicResearchAgent, CrossReferenceAgent, StudyGuideAgent

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
        ## LLM client for AI interactions.
        self.LlmClient: Optional["LLMClient"] = None
        ## Dictionary mapping agent names to their instances.
        self.Agents: dict[str, "TopicResearchAgent | CrossReferenceAgent | StudyGuideAgent"] = {}
        
        self._InitializeComponents()
    
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
        
        # Initialize agents
        self.Agents = {
            'topic_research': TopicResearchAgent(self.BibleParser, self.LlmClient),
            'cross_reference': CrossReferenceAgent(self.BibleParser, self.LlmClient),
            'study_guide': StudyGuideAgent(self.BibleParser, self.LlmClient)
        }
        
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
        print("5. help - Show this help")
        print("6. quit - Exit the program")
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
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\nGoodbye! 🙏")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    ## Handle topic research command.
    ## @param[in] args - Research topic arguments.
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
        
        response = self.Agents['study_guide'].CreateStudyGuide(topic, guide_type=guide_type)
        
        if response.success:
            print("\n" + "="*SEPARATOR_LINE_LENGTH)
            print(f"📖 STUDY GUIDE: {topic.upper()} ({guide_type.upper()})")
            print("="*SEPARATOR_LINE_LENGTH)
            print(response.content)
            print(f"\n📊 Based on {len(response.verses_used)} verses")
        else:
            print(f"❌ Study guide creation failed: {response.content}")
    
    ## Handle verse search command.
    ## @param[in] args - Search query arguments.
    def _HandleSearch(self, args: str) -> None:
        if not args:
            print("Usage: search <query>")
            return
        
        bible_parser_available = self.BibleParser is not None
        if not bible_parser_available:
            print("❌ Bible parser not initialized.")
            return
        
        print(f"\n🔍 Searching for: {args}")
        
        verses = self.BibleParser.SearchVerses(args, max_results=DEFAULT_SEARCH_MAX_RESULTS)
        
        if verses:
            print(f"\n📖 Found {len(verses)} verses:")
            print("-" * SEARCH_RESULTS_SEPARATOR_LENGTH)
            ENUMERATION_START = 1
            for i, verse in enumerate(verses, ENUMERATION_START):
                print(f"{i}. {verse.book} {verse.chapter}:{verse.verse} ({verse.translation})")
                print(f"   {verse.text}")
                print()
        else:
            print("❌ No verses found matching your search.")
    
    ## Show help information.
    def _ShowHelp(self) -> None:
        print("\n" + "="*SEPARATOR_LINE_LENGTH)
        print("📖 BIBLE STUDY COMMANDS")
        print("="*SEPARATOR_LINE_LENGTH)
        print("research <topic>")
        print("  Research a Bible topic and find relevant verses")
        print("  Example: research love")
        print()
        print("crossref <reference>")
        print("  Find cross-references for a specific verse")
        print("  Example: crossref John 3:16")
        print()
        print("guide <topic> [type]")
        print("  Create a study guide (comprehensive, devotional, theological)")
        print("  Example: guide forgiveness devotional")
        print()
        print("search <query>")
        print("  Search for specific words or phrases in the Bible")
        print("  Example: search grace")
        print()
        print("help - Show this help")
        print("quit - Exit the program")
        print("="*SEPARATOR_LINE_LENGTH)


## Main entry point.
def Main():
    # Check if data directory exists
    data_directory_path = "data"
    data_directory_exists = pathlib.Path(data_directory_path).exists()
    if not data_directory_exists:
        print(f"Error: Data directory '{data_directory_path}' not found.")
        print("Make sure you have Bible XML files in the data directory.")
        return
    
    # Create and run the application
    app = BibleStudyApp(data_directory_path)
    app.RunInteractive()

if __name__ == "__main__":
    Main() 