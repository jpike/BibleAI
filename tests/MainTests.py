#!/usr/bin/env python3
## @package MainTests
## Unit tests for the Main application class.

import unittest
import sys
import os
import tempfile
import shutil
import pathlib
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.Main import BibleStudyApp

## Test cases for the BibleStudyApp class.
class MainTests(unittest.TestCase):
    ## Set up test environment before each test.
    def setUp(self):
        # Create a temporary directory for test data
        self.test_data_dir = pathlib.Path("test_data")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Create BibleVerses subdirectory to match new structure
        self.test_bible_verses_dir = self.test_data_dir / "BibleVerses"
        self.test_bible_verses_dir.mkdir(exist_ok=True)
        
        # Create test XML file
        self._CreateTestXmlFile()
        
        # Initialize app
        self.app = BibleStudyApp(str(self.test_data_dir), "http://localhost:1234/v1")
    
    ## Clean up test environment after each test.
    def tearDown(self):
        # Remove temporary directory
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
    
    ## Create test XML file for testing.
    def _CreateTestXmlFile(self):
        test_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
    <osisText>
        <div type="book" osisID="Gen">
            <chapter osisID="Gen.1">
                <verse osisID="Gen.1.1">In the beginning God created the heaven and the earth.</verse>
                <verse osisID="Gen.1.2">And the earth was without form, and void.</verse>
            </chapter>
        </div>
    </osisText>
</osis>'''
        
        test_file_path = self.test_bible_verses_dir / "kjv.xml"
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_xml_content)
    
    ## Test BibleStudyApp initialization.
    def test_Initialization(self):
        app = BibleStudyApp("test_data", "http://localhost:1234/v1")
        
        self.assertEqual(app.DataDirectoryPath, "test_data")
        self.assertEqual(app.LlmBaseUrl, "http://localhost:1234/v1")
        self.assertIsNone(app.BibleParser)
        self.assertIsNone(app.LlmClient)
        self.assertEqual(app.Agents, {})
    
    ## Test successful component initialization.
    @patch('src.Main.LLMClient')
    @patch('src.Main.BibleParser')
    def test_SuccessfulComponentInitialization(self, mock_bible_parser_class, mock_llm_client_class):
        # Mock Bible parser
        mock_bible_parser = Mock()
        mock_bible_parser_class.return_value = mock_bible_parser
        
        # Mock LLM client
        mock_llm_client = Mock()
        mock_llm_client.TestConnection.return_value = True
        mock_llm_client_class.return_value = mock_llm_client
        
        # Create app and initialize components
        app = BibleStudyApp(str(self.test_data_dir), "http://localhost:1234/v1")
        app._InitializeComponents()
        
        # Verify components were initialized
        self.assertIsNotNone(app.BibleParser)
        self.assertIsNotNone(app.LlmClient)
        self.assertEqual(len(app.Agents), 4)  # topic_research, cross_reference, study_guide, chat
        self.assertIn('topic_research', app.Agents)
        self.assertIn('cross_reference', app.Agents)
        self.assertIn('study_guide', app.Agents)
        self.assertIn('chat', app.Agents)
        
        # Verify method calls
        mock_bible_parser.LoadAllTranslations.assert_called_once()
        mock_llm_client.TestConnection.assert_called_once()
    
    ## Test component initialization with Bible parser failure.
    @patch('src.Main.LLMClient')
    @patch('src.Main.BibleParser')
    def test_BibleParserInitializationFailure(self, mock_bible_parser_class, mock_llm_client_class):
        # Mock Bible parser failure
        mock_bible_parser_class.side_effect = Exception("Bible parser error")
        
        # Mock LLM client
        mock_llm_client = Mock()
        mock_llm_client_class.return_value = mock_llm_client
        
        # Create app and initialize components
        app = BibleStudyApp(str(self.test_data_dir), "http://localhost:1234/v1")
        app._InitializeComponents()
        
        # Verify components were not initialized
        self.assertIsNone(app.BibleParser)
        self.assertIsNone(app.LlmClient)
        self.assertEqual(app.Agents, {})
    
    ## Test component initialization with LLM connection failure.
    @patch('src.Main.LLMClient')
    @patch('src.Main.BibleParser')
    def test_LlmConnectionFailure(self, mock_bible_parser_class, mock_llm_client_class):
        # Mock Bible parser
        mock_bible_parser = Mock()
        mock_bible_parser_class.return_value = mock_bible_parser
        
        # Mock LLM client with connection failure
        mock_llm_client = Mock()
        mock_llm_client.TestConnection.return_value = False
        mock_llm_client_class.return_value = mock_llm_client
        
        # Create app and initialize components
        app = BibleStudyApp(str(self.test_data_dir), "http://localhost:1234/v1")
        app._InitializeComponents()
        
        # Verify components were not fully initialized due to LLM connection failure
        # BibleParser should be initialized but LLMClient should not be properly connected
        self.assertIsNotNone(app.BibleParser)
        self.assertIsNotNone(app.LlmClient)  # LLMClient is created but connection fails
        self.assertEqual(app.Agents, {})  # No agents should be initialized when LLM connection fails
    
    ## Test research command handling.
    def test_HandleResearch(self):
        # Mock agents
        mock_topic_agent = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "Research results"
        mock_response.verses_used = []
        mock_response.metadata = {"translation": "KJV"}
        mock_topic_agent.ResearchTopic.return_value = mock_response
        
        self.app.Agents = {'topic_research': mock_topic_agent}
        
        # Test research command
        with patch('builtins.print') as mock_print:
            self.app._HandleResearch("love")
            
            # Verify agent was called
            mock_topic_agent.ResearchTopic.assert_called_once_with("love")
            
            # Verify output was printed
            mock_print.assert_called()
    
    ## Test research command with no arguments.
    def test_HandleResearchNoArgs(self):
        with patch('builtins.print') as mock_print:
            self.app._HandleResearch("")
            
            # Verify usage message was printed
            mock_print.assert_called_with("Usage: research <topic>")
    
    ## Test cross-reference command handling.
    def test_HandleCrossref(self):
        # Mock agents
        mock_crossref_agent = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "Cross-reference results"
        mock_response.verses_used = []
        mock_response.metadata = {"related_count": 5}
        mock_crossref_agent.FindCrossReferences.return_value = mock_response
        
        self.app.Agents = {'cross_reference': mock_crossref_agent}
        
        # Test cross-reference command
        with patch('builtins.print') as mock_print:
            self.app._HandleCrossref("John 3:16")
            
            # Verify agent was called
            mock_crossref_agent.FindCrossReferences.assert_called_once_with("John 3:16")
            
            # Verify output was printed
            mock_print.assert_called()
    
    ## Test cross-reference command with no arguments.
    def test_HandleCrossrefNoArgs(self):
        with patch('builtins.print') as mock_print:
            self.app._HandleCrossref("")
            
            # Verify usage message was printed
            mock_print.assert_called_with("Usage: crossref <reference> (e.g., crossref John 3:16)")
    
    ## Test study guide command handling.
    def test_HandleGuide(self):
        # Mock agents
        mock_study_agent = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "Study guide content"
        mock_response.verses_used = []
        mock_response.metadata = {"guide_type": "comprehensive"}
        mock_study_agent.CreateStudyGuide.return_value = mock_response
        
        self.app.Agents = {'study_guide': mock_study_agent}
        
        # Test study guide command
        with patch('builtins.print') as mock_print:
            self.app._HandleGuide("love comprehensive")
            
            # Verify agent was called
            mock_study_agent.CreateStudyGuide.assert_called_once_with("love", "KJV", "comprehensive")
            
            # Verify output was printed
            mock_print.assert_called()
    
    ## Test study guide command with no arguments.
    def test_HandleGuideNoArgs(self):
        with patch('builtins.print') as mock_print:
            self.app._HandleGuide("")
            
            # Verify usage message was printed
            calls = mock_print.call_args_list
            self.assertIn("Usage: guide <topic> [type]", str(calls))
            self.assertIn("Types: comprehensive, devotional, theological", str(calls))
    
    ## Test study guide command with default type.
    def test_HandleGuideDefaultType(self):
        # Mock agents
        mock_study_agent = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.content = "Study guide content"
        mock_response.verses_used = []
        mock_response.metadata = {"guide_type": "comprehensive"}
        mock_study_agent.CreateStudyGuide.return_value = mock_response
        
        self.app.Agents = {'study_guide': mock_study_agent}
        
        # Test study guide command without type (should default to comprehensive)
        with patch('builtins.print'):
            self.app._HandleGuide("love")
            
            # Verify agent was called with default type
            mock_study_agent.CreateStudyGuide.assert_called_once_with("love", "KJV", "comprehensive")
    
    ## Test search command handling.
    def test_HandleSearch(self):
        # Mock Bible parser
        mock_parser = Mock()
        mock_verses = [
            Mock(book="Gen", chapter=1, verse=1, text="In the beginning God created"),
            Mock(book="Gen", chapter=1, verse=2, text="And the earth was without form")
        ]
        mock_parser.SearchVerses.return_value = mock_verses
        self.app.BibleParser = mock_parser
        
        # Test search command
        with patch('builtins.print') as mock_print:
            self.app._HandleSearch("God")
            
            # Verify parser was called
            mock_parser.SearchVerses.assert_called_once_with("God", translation=None, max_results=10)
            
            # Verify output was printed
            mock_print.assert_called()
    
    ## Test search command with no arguments.
    def test_HandleSearchNoArgs(self):
        with patch('builtins.print') as mock_print:
            self.app._HandleSearch("")
            
            # Verify usage message was printed
            mock_print.assert_called_with("Usage: search <query>")
    
    ## Test help command.
    def test_ShowHelp(self):
        with patch('builtins.print') as mock_print:
            self.app._ShowHelp()
            
            # Verify help was printed
            mock_print.assert_called()
            calls = mock_print.call_args_list
            help_text = str(calls)
            self.assertIn("research", help_text)
            self.assertIn("crossref", help_text)
            self.assertIn("guide", help_text)
            self.assertIn("search", help_text)
    
    ## Test command parsing.
    def test_CommandParsing(self):
        # Test various command formats
        test_cases = [
            ("research love", ("research", "love")),
            ("crossref John 3:16", ("crossref", "John 3:16")),
            ("guide love comprehensive", ("guide", "love comprehensive")),
            ("search God", ("search", "God")),
            ("help", ("help", "")),
            ("quit", ("quit", ""))
        ]
        
        for command_input, expected in test_cases:
            with self.subTest(command_input=command_input):
                parts = command_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                self.assertEqual((command, args), expected)
    
    ## Test quit commands.
    def test_QuitCommands(self):
        quit_commands = ['quit', 'exit', 'q']
        
        for command in quit_commands:
            with self.subTest(command=command):
                self.assertTrue(command in ['quit', 'exit', 'q'])
    
    ## Test failed research response.
    def test_FailedResearchResponse(self):
        # Mock agents
        mock_topic_agent = Mock()
        mock_response = Mock()
        mock_response.success = False
        mock_response.content = "Research failed"
        mock_response.verses_used = []
        mock_response.metadata = {"translation": "KJV"}
        mock_topic_agent.ResearchTopic.return_value = mock_response
        
        self.app.Agents = {'topic_research': mock_topic_agent}
        
        # Test research command
        with patch('builtins.print') as mock_print:
            self.app._HandleResearch("love")
            
            # Verify error message was printed
            mock_print.assert_called_with("❌ Research failed: Research failed")
    
    ## Test failed cross-reference response.
    def test_FailedCrossrefResponse(self):
        # Mock agents
        mock_crossref_agent = Mock()
        mock_response = Mock()
        mock_response.success = False
        mock_response.content = "Cross-reference failed"
        mock_response.verses_used = []
        mock_response.metadata = {"related_count": 0}
        mock_crossref_agent.FindCrossReferences.return_value = mock_response
        
        self.app.Agents = {'cross_reference': mock_crossref_agent}
        
        # Test cross-reference command
        with patch('builtins.print') as mock_print:
            self.app._HandleCrossref("John 3:16")
            
            # Verify error message was printed
            mock_print.assert_called_with("❌ Cross-reference failed: Cross-reference failed")
    
    ## Test failed study guide response.
    def test_FailedGuideResponse(self):
        # Mock agents
        mock_study_agent = Mock()
        mock_response = Mock()
        mock_response.success = False
        mock_response.content = "Study guide failed"
        mock_response.verses_used = []
        mock_response.metadata = {"guide_type": "comprehensive"}
        mock_study_agent.CreateStudyGuide.return_value = mock_response
        
        self.app.Agents = {'study_guide': mock_study_agent}
        
        # Test study guide command
        with patch('builtins.print') as mock_print:
            self.app._HandleGuide("love comprehensive")
            
            # Verify error message was printed
            mock_print.assert_called_with("❌ Study guide failed: Study guide failed")
    
    ## Test search with no results.
    def test_SearchNoResults(self):
        # Mock Bible parser
        mock_parser = Mock()
        mock_parser.SearchVerses.return_value = []
        self.app.BibleParser = mock_parser
        
        # Test search command
        with patch('builtins.print') as mock_print:
            self.app._HandleSearch("nonexistent")
            
            # Verify no results message was printed
            mock_print.assert_called_with("No verses found matching 'nonexistent'")

if __name__ == '__main__':
    unittest.main() 