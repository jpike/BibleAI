#!/usr/bin/env python3
## @package run_tests
## Test runner script for the BibleAI project.

import unittest
import sys
import os
import pathlib
import time

# Add the project root to the Python path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / 'src'))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def RunAllTests():
    """Run all unit tests in the project."""
    print("🧪 BIBLEAI UNIT TEST SUITE")
    print("=" * 50)
    
    # Start timing
    start_time = time.time()
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    
    # Test files to run (in order of dependency)
    test_files = [
        'BibleVerseTests',
        'BibleParserTests', 
        'LlmClientTests',
        'Agents.AgentResponseTests',
        'Agents.TopicResearchAgentTests',
        'Agents.CrossReferenceAgentTests',
        'Agents.StudyGuideAgentTests',
        'MainTests'
    ]
    
    all_tests = unittest.TestSuite()
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_file in test_files:
        try:
            # Import the test module
            test_module = __import__(f'tests.{test_file}', fromlist=['*'])
            
            # Load tests from the module
            suite = loader.loadTestsFromModule(test_module)
            all_tests.addTest(suite)
            
            # Count tests in this module
            test_count = suite.countTestCases()
            total_tests += test_count
            
            print(f"📋 Loaded {test_count} tests from {test_file}")
            
        except ImportError as e:
            print(f"❌ Failed to import {test_file}: {e}")
            total_errors += 1
        except Exception as e:
            print(f"❌ Error loading {test_file}: {e}")
            total_errors += 1
    
    print(f"\n🚀 Running {total_tests} tests...")
    print("-" * 50)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(all_tests)
    
    # Calculate timing
    end_time = time.time()
    duration = end_time - start_time
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total tests run: {total_tests}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Duration: {duration:.2f} seconds")
    
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            error_msg = (
                traceback.split('AssertionError:')[-1].strip()
                if 'AssertionError:' in traceback
                else traceback.split('\n')[-1].strip()
            )
            print(f"  • {test}: {error_msg}")

    if result.errors:
        print(f"\n💥 ERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            error_msg = (
                traceback.split('Exception:')[-1].strip()
                if 'Exception:' in traceback
                else traceback.split('\n')[-1].strip()
            )
            print(f"  • {test}: {error_msg}")    
    if result.wasSuccessful():
        print(f"\n✅ ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} TESTS FAILED")
        return 1
    # Parse test name (e.g., "BibleVerseTests.TestBasicInitialization")
    parts = test_name.split('.')
    
    if len(parts) == 1:
        # Just the test class
        suite = unittest.TestLoader().loadTestsFromName(f"tests.{parts[0]}")
    elif len(parts) == 2:
        # Test class and method, or module.class
        if parts[0] in ['Agents']:  # Handle submodules
            suite = unittest.TestLoader().loadTestsFromName(f"tests.{test_name}")
        else:
            suite = unittest.TestLoader().loadTestsFromName(f"tests.{parts[0]}.{parts[1]}")
    elif len(parts) == 3:
        # Module.class.method
        suite = unittest.TestLoader().loadTestsFromName(f"tests.{test_name}")
    else:
        print(f"❌ Invalid test name format: {test_name}")
        print("Use format: TestClass, TestClass.TestMethod, or Module.TestClass.TestMethod")
        return 1
    
    # Run the specific test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

def ListAllTests():
    """List all available tests."""
    print("📋 AVAILABLE TESTS")
    print("=" * 50)
    
    test_files = [
        'BibleVerseTests',
        'BibleParserTests', 
        'LlmClientTests',
        'Agents.AgentResponseTests',
        'Agents.TopicResearchAgentTests',
        'Agents.CrossReferenceAgentTests',
        'Agents.StudyGuideAgentTests',
        'MainTests'
    ]
    
    for test_file in test_files:
        try:
            test_module = __import__(f'tests.{test_file}', fromlist=['*'])
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            
            print(f"\n📁 {test_file}:")
            for test in suite:
                test_name = str(test)
                if 'testMethod=' in test_name:
                    # Extract method name
                    method_name = test_name.split('testMethod=')[1].split(')')[0]
                    print(f"  • {method_name}")
                else:
                    print(f"  • {test_name}")
                    
        except ImportError as e:
            print(f"❌ {test_file}: Import error - {e}")
        except Exception as e:
            print(f"❌ {test_file}: Error - {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run BibleAI unit tests')
    parser.add_argument('--test', '-t', help='Run a specific test (e.g., BibleVerseTests.TestBasicInitialization)')
    parser.add_argument('--list', '-l', action='store_true', help='List all available tests')
    
    args = parser.parse_args()
    
    if args.list:
        ListAllTests()
    elif args.test:
        exit_code = RunSpecificTest(args.test)
        sys.exit(exit_code)
    else:
        exit_code = RunAllTests()
        sys.exit(exit_code) 