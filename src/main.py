## @package main
## Main application for the Agentic Bible Study Program.

import sys
import os
from pathlib import Path
from typing import Optional

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent))

from bible_parser import BibleParser
from llm_client import LLMClient
from bible_agents import TopicResearchAgent, CrossReferenceAgent, StudyGuideAgent


## Main application class for the Bible study program.
class BibleStudyApp:
    ## Initialize the Bible study application.
    ## @param[in] data_directory - Path to Bible data files.
    ## @param[in] llm_base_url - Base URL for LM Studio API.
    def __init__(self, data_directory: str = "data", 
                 llm_base_url: str = "http://localhost:1234/v1"):
        self.data_directory = data_directory
        self.llm_base_url = llm_base_url
        
        # Initialize components
        self.bible_parser = None
        self.llm_client = None
        self.agents = {}
        
        self._initialize_components()
    
    ## Initialize all application components.
    def _initialize_components(self) -> None:
        print("Initializing Bible Study Application...")
        
        # Initialize Bible parser
        try:
            self.bible_parser = BibleParser(self.data_directory)
            self.bible_parser.load_all_translations()
            print("✓ Bible data loaded successfully")
        except Exception as e:
            print(f"✗ Error loading Bible data: {e}")
            return
        
        # Initialize LLM client
        try:
            self.llm_client = LLMClient(self.llm_base_url)
            if self.llm_client.test_connection():
                print("✓ LLM connection successful")
            else:
                print("✗ LLM connection failed - make sure LM Studio is running")
                return
        except Exception as e:
            print(f"✗ Error connecting to LLM: {e}")
            return
        
        # Initialize agents
        self.agents = {
            'topic_research': TopicResearchAgent(self.bible_parser, self.llm_client),
            'cross_reference': CrossReferenceAgent(self.bible_parser, self.llm_client),
            'study_guide': StudyGuideAgent(self.bible_parser, self.llm_client)
        }
        
        print("✓ All components initialized successfully")
    
    ## Run the application in interactive mode.
    def run_interactive(self) -> None:
        if not self.bible_parser or not self.llm_client:
            print("Application not properly initialized. Exiting.")
            return
        
        print("\n" + "="*60)
        print("🤖 AGENTIC BIBLE STUDY PROGRAM")
        print("="*60)
        print("Available commands:")
        print("1. research <topic> - Research a Bible topic")
        print("2. crossref <reference> - Find cross-references")
        print("3. guide <topic> [type] - Create study guide")
        print("4. search <query> - Search for specific verses")
        print("5. help - Show this help")
        print("6. quit - Exit the program")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n📖 Bible Study > ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye! 🙏")
                    break
                
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                # Parse command
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == 'research':
                    self._handle_research(args)
                elif command == 'crossref':
                    self._handle_crossref(args)
                elif command == 'guide':
                    self._handle_guide(args)
                elif command == 'search':
                    self._handle_search(args)
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
    def _handle_research(self, args: str) -> None:
        if not args:
            print("Usage: research <topic>")
            return
        
        print(f"\n🔍 Researching topic: {args}")
        print("Please wait...")
        
        response = self.agents['topic_research'].research_topic(args)
        
        if response.success:
            print("\n" + "="*60)
            print(f"📚 RESEARCH RESULTS: {args.upper()}")
            print("="*60)
            print(response.content)
            print(f"\n📊 Used {len(response.verses_used)} verses from {response.metadata.get('translation', 'KJV')}")
        else:
            print(f"❌ Research failed: {response.content}")
    
    ## Handle cross-reference command.
    ## @param[in] args - Cross-reference arguments.
    def _handle_crossref(self, args: str) -> None:
        if not args:
            print("Usage: crossref <reference> (e.g., crossref John 3:16)")
            return
        
        print(f"\n🔗 Finding cross-references for: {args}")
        print("Please wait...")
        
        response = self.agents['cross_reference'].find_cross_references(args)
        
        if response.success:
            print("\n" + "="*60)
            print(f"🔗 CROSS-REFERENCES: {args.upper()}")
            print("="*60)
            print(response.content)
            print(f"\n📊 Found {response.metadata.get('related_count', 0)} related verses")
        else:
            print(f"❌ Cross-reference failed: {response.content}")
    
    ## Handle study guide command.
    ## @param[in] args - Study guide arguments.
    def _handle_guide(self, args: str) -> None:
        if not args:
            print("Usage: guide <topic> [type]")
            print("Types: comprehensive, devotional, theological")
            return
        
        parts = args.split(' ', 1)
        topic = parts[0]
        guide_type = parts[1] if len(parts) > 1 else "comprehensive"
        
        print(f"\n📖 Creating {guide_type} study guide for: {topic}")
        print("Please wait...")
        
        response = self.agents['study_guide'].create_study_guide(topic, guide_type=guide_type)
        
        if response.success:
            print("\n" + "="*60)
            print(f"📖 STUDY GUIDE: {topic.upper()} ({guide_type.upper()})")
            print("="*60)
            print(response.content)
            print(f"\n📊 Based on {len(response.verses_used)} verses")
        else:
            print(f"❌ Study guide creation failed: {response.content}")
    
    ## Handle verse search command.
    ## @param[in] args - Search query arguments.
    def _handle_search(self, args: str) -> None:
        if not args:
            print("Usage: search <query>")
            return
        
        print(f"\n🔍 Searching for: {args}")
        
        verses = self.bible_parser.search_verses(args, max_results=10)
        
        if verses:
            print(f"\n📖 Found {len(verses)} verses:")
            print("-" * 40)
            for i, verse in enumerate(verses, 1):
                print(f"{i}. {verse.book} {verse.chapter}:{verse.verse} ({verse.translation})")
                print(f"   {verse.text}")
                print()
        else:
            print("❌ No verses found matching your search.")
    
    ## Show help information.
    def _show_help(self) -> None:
        print("\n" + "="*60)
        print("📖 BIBLE STUDY COMMANDS")
        print("="*60)
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
        print("="*60)


## Main entry point.
def main():
    # Check if data directory exists
    data_dir = "data"
    if not Path(data_dir).exists():
        print(f"Error: Data directory '{data_dir}' not found.")
        print("Make sure you have Bible XML files in the data directory.")
        return
    
    # Create and run the application
    app = BibleStudyApp(data_dir)
    app.run_interactive()


if __name__ == "__main__":
    main() 