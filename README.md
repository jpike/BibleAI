# Agentic Bible Study Program

An AI-powered Bible study application that uses local LLMs to help with Bible research, cross-references, and study guide creation.

## Features

- **Topic Research**: Find relevant Bible verses for any topic
- **Cross-References**: Discover related passages and connections
- **Study Guides**: Generate comprehensive, devotional, or theological study guides
- **Multi-Translation Support**: Works with KJV, YLT, and WEB translations
- **Local LLM Integration**: Uses your local LM Studio setup
- **No External Dependencies**: Uses only Python built-in libraries

## Setup

### Prerequisites

1. **LM Studio**: Download and install [LM Studio](https://lmstudio.ai/)
2. **Python 3.8+**: Make sure Python is installed on your system
3. **Bible Data**: Place your OSIS XML Bible files in the `data/` directory

### Installation

1. Clone or download this project
2. No additional dependencies required - uses only Python built-in libraries!
3. Start LM Studio and load a model
4. Start the local server in LM Studio (usually runs on `http://localhost:1234`)

### Usage

Run the application:
```bash
python src/main.py
```

### Available Commands

- `research <topic>` - Research a Bible topic and find relevant verses
- `crossref <reference>` - Find cross-references for a specific verse
- `guide <topic> [type]` - Create a study guide (comprehensive, devotional, theological)
- `search <query>` - Search for specific words or phrases
- `help` - Show available commands
- `quit` - Exit the program

### Examples

```bash
# Research a topic
research love

# Find cross-references
crossref John 3:16

# Create a devotional guide
guide forgiveness devotional

# Search for specific terms
search grace
```

## Architecture

The application consists of several key components:

1. **BibleParser**: Parses OSIS XML files and provides search functionality
2. **LLMClient**: Connects to local LM Studio API
3. **Bible Agents**: Specialized agents for different Bible study tasks
   - TopicResearchAgent: Finds verses related to topics
   - CrossReferenceAgent: Discovers related passages
   - StudyGuideAgent: Creates comprehensive study guides

## Customization

You can customize the application by:

- Adding new Bible translations to the `data/` directory
- Modifying agent prompts in the agent classes
- Adjusting search parameters and result limits
- Adding new agent types for specialized tasks

## Troubleshooting

- **LLM Connection Failed**: Make sure LM Studio is running and the local server is started
- **No Bible Data**: Ensure XML files are in the `data/` directory
- **Slow Responses**: Try using a smaller/faster model in LM Studio

## License

This project is open source and available under the MIT License. 