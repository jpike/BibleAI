#!/usr/bin/env python3
## @package TestParser
## Test script for the Bible parser fix.

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.BibleParser import BibleParser

## Test the Bible parser with the namespace fix.
def test_parser():
    try:
        parser = BibleParser()
        result = parser.parse_translation('kjv.xml')
        
        # Print some statistics
        total_verses = sum(len(verses) for verses in result.values())
        print(f"Successfully parsed {total_verses} verses")
        print(f"Found {len(result)} books")
        
        # Show first few books and their verse counts
        for book_name, verses in list(result.items())[:5]:
            print(f"  {book_name}: {len(verses)} verses")
            
        # Show a sample verse
        if result and 'Gen' in result and result['Gen']:
            sample_verse = result['Gen'][0]
            print(f"\nSample verse: {sample_verse.osis_id}")
            print(f"Text: {sample_verse.text[:100]}...")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parser() 