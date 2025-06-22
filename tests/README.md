# BibleAI Test Suite

This directory contains comprehensive unit tests for the BibleAI project. The tests are designed to protect against breaking changes and ensure code quality as the project evolves.

## Test Structure

The test files mirror the structure of the production code:

```
tests/
├── __init__.py
├── run_tests.py                 # Test runner script
├── README.md                    # This file
├── BibleVerseTests.py           # Tests for BibleVerse dataclass
├── BibleParserTests.py          # Tests for BibleParser class
├── LlmClientTests.py            # Tests for LLMClient class
├── MainTests.py                 # Tests for Main application
└── Agents/
    ├── __init__.py
    ├── AgentResponseTests.py    # Tests for AgentResponse dataclass
    ├── TopicResearchAgentTests.py    # Tests for TopicResearchAgent
    ├── CrossReferenceAgentTests.py   # Tests for CrossReferenceAgent
    └── StudyGuideAgentTests.py       # Tests for StudyGuideAgent
```

## Running Tests

### Run All Tests

To run the complete test suite:

```bash
python tests/run_tests.py
```

### Run Specific Tests

To run a specific test class:

```bash
python tests/run_tests.py --test BibleVerseTests
```

To run a specific test method:

```bash
python tests/run_tests.py --test BibleVerseTests.TestBasicInitialization
```

### List All Available Tests

To see all available tests:

```bash
python tests/run_tests.py --list
```

### Run Individual Test Files

You can also run individual test files directly:

```bash
python tests/BibleVerseTests.py
python tests/BibleParserTests.py
python tests/LlmClientTests.py
# etc.
```

## Test Coverage

The test suite covers:

### BibleVerseTests
- Basic initialization and data validation
- Text cleaning and normalization
- Dataclass equality and inequality
- Edge cases (empty text, whitespace-only text)
- Different translation codes and book names

### BibleParserTests
- XML file parsing and OSIS namespace handling
- Verse indexing and retrieval
- Search functionality (case-insensitive, max results)
- Topic keyword search
- Error handling (missing files, invalid XML)
- Multiple translation support

### LlmClientTests
- HTTP request handling and error management
- Connection testing
- Response generation with retry logic
- Request timeout handling
- JSON parsing and validation
- Custom parameters (temperature, max_tokens, etc.)

### AgentResponseTests
- Dataclass initialization and data access
- Complex metadata handling
- Bible verse integration
- Success/failure state management

### TopicResearchAgentTests
- Topic research workflow
- Keyword generation and extraction
- LLM integration with mocked responses
- Error handling and edge cases
- Verse formatting for analysis

### CrossReferenceAgentTests
- Bible reference parsing
- Cross-reference finding
- Key term extraction
- Related verse filtering
- Analysis generation

### StudyGuideAgentTests
- Study guide creation (comprehensive, devotional, theological)
- Topic research integration
- LLM prompt validation
- Guide type handling and defaults

### MainTests
- Application initialization
- Component dependency management
- Command parsing and handling
- User interaction simulation
- Error state management

## Test Dependencies

The tests use only Python standard library modules:
- `unittest` - Test framework
- `unittest.mock` - Mocking and patching
- `tempfile` - Temporary file/directory creation
- `shutil` - File operations
- `pathlib` - Path handling
- `xml.etree.ElementTree` - XML parsing
- `urllib.request` - HTTP requests
- `json` - JSON handling

## Mocking Strategy

The tests use extensive mocking to isolate units and avoid external dependencies:

- **LLMClient tests**: Mock `urllib.request.urlopen` to simulate HTTP responses
- **Agent tests**: Mock `LLMClient.GenerateResponse` and `BibleParser` methods
- **Main tests**: Mock all dependencies to test application logic in isolation
- **BibleParser tests**: Use temporary XML files for realistic testing

## Test Data

Test data is created dynamically:
- Temporary XML files with OSIS format Bible data
- Mock Bible verses with realistic content
- Simulated LLM responses
- Temporary directories that are cleaned up automatically

## Continuous Integration

The test suite is designed to run in CI/CD environments:
- No external dependencies required
- Fast execution (all tests should complete in under 30 seconds)
- Clear pass/fail reporting
- Detailed error messages for debugging

## Adding New Tests

When adding new functionality:

1. Create a test file following the naming convention: `{ClassName}Tests.py`
2. Place it in the appropriate directory structure
3. Add comprehensive test cases covering:
   - Happy path scenarios
   - Error conditions
   - Edge cases
   - Performance considerations
4. Update `tests/run_tests.py` to include the new test file
5. Ensure all tests pass before committing

## Test Best Practices

- **Isolation**: Each test should be independent and not rely on other tests
- **Descriptive names**: Test method names should clearly describe what is being tested
- **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
- **Mock external dependencies**: Don't rely on external services or files
- **Clean up**: Use `setUp()` and `tearDown()` methods for proper test isolation
- **Documentation**: Include clear comments explaining complex test scenarios

## Troubleshooting

### Import Errors
If you encounter import errors, ensure:
- You're running tests from the project root directory
- The `src` directory is in your Python path
- All `__init__.py` files are present

### Test Failures
For test failures:
- Check the detailed error output
- Verify that mocked dependencies are properly configured
- Ensure test data is correctly formatted
- Check that temporary files are being created and cleaned up properly

### Performance Issues
If tests are running slowly:
- Check for unnecessary file I/O operations
- Ensure mocks are being used instead of real HTTP requests
- Verify that temporary directories are being cleaned up efficiently 