#!/usr/bin/env python3
"""
Test script for websearch.py functionality.
Allows interactive testing of the Firecrawl search tool.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.tools.websearch import firecrawl_search, run_firecrawl_search
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_basic_search():
    """Test basic search functionality without GPT summarization."""
    print("=" * 60)
    print("BASIC SEARCH TEST (No GPT Summarization)")
    print("=" * 60)
    
    while True:
        print("\n" + "-" * 40)
        query = input("Enter your search query (or 'quit' to exit): ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            print("Please enter a valid query.")
            continue
        
        try:
            print(f"\n🔍 Searching for: '{query}'")
            print("⏳ Please wait...")
            
            # Test basic search (returns raw results)
            results = firecrawl_search(query)
            
            print(f"\n✅ Found {len(results)} result(s):\n")
            
            for i, result in enumerate(results, 1):
                print(f"📄 Result {i}:")
                print(f"   Title: {result.get('title', 'N/A')}")
                print(f"   Description: {result.get('description', 'N/A')}")
                print(f"   URL: {result.get('url', 'N/A')}")
                print()
            
            # Pretty print JSON
            print("🔍 Raw JSON Output:")
            print(json.dumps(results, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"❌ Error during search: {e}")
            print(f"   Make sure your FIRECRAWL_API_KEY is set correctly.")


def test_full_search_with_summary():
    """Test full search functionality with GPT summarization."""
    print("=" * 60)
    print("FULL SEARCH TEST (With GPT Summarization)")
    print("=" * 60)
    
    while True:
        print("\n" + "-" * 40)
        query = input("Enter your search query (or 'quit' to exit): ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            print("Please enter a valid query.")
            continue
        
        try:
            print(f"\n🔍 Searching for: '{query}'")
            print("⏳ This will take ~15 seconds (includes wait time)...")
            
            # Test full search with GPT summarization
            summary = run_firecrawl_search(query)
            
            print(f"\n✅ Search completed!\n")
            print("📋 GPT Summary:")
            print("=" * 50)
            print(summary)
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error during search: {e}")
            print(f"   Check your API keys (FIRECRAWL_API_KEY and OpenAI config).")


def test_environment_setup():
    """Test if the environment is properly configured."""
    print("=" * 60)
    print("ENVIRONMENT SETUP TEST")
    print("=" * 60)
    
    # Check Firecrawl API Key
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    if firecrawl_key:
        print("✅ FIRECRAWL_API_KEY is set")
        print(f"   Key preview: {firecrawl_key[:10]}...{firecrawl_key[-4:]}")
    else:
        print("❌ FIRECRAWL_API_KEY is not set")
    
    # Check OpenAI configuration
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_api_version = os.getenv("OPENAI_API_VERSION")
    openai_deployment = os.getenv("OPENAI_DEPLOYMENT_NAME")
    
    print(f"\n🤖 OpenAI Configuration:")
    print(f"   Base URL: {'✅ Set' if openai_base_url else '❌ Not set'}")
    print(f"   API Key: {'✅ Set' if openai_api_key else '❌ Not set'}")
    print(f"   API Version: {'✅ Set' if openai_api_version else '❌ Not set'}")
    print(f"   Deployment Name: {'✅ Set' if openai_deployment else '❌ Not set'}")
    
    if openai_base_url:
        print(f"   Base URL: {openai_base_url}")
    if openai_deployment:
        print(f"   Deployment: {openai_deployment}")
    
    # Overall status
    print(f"\n🎯 Overall Status:")
    if firecrawl_key and openai_base_url and openai_api_key and openai_deployment:
        print("✅ Environment appears to be properly configured!")
        return True
    else:
        print("❌ Some environment variables are missing. Please check your .env file.")
        return False


def test_single_query():
    """Test a single predefined query for quick testing."""
    print("=" * 60)
    print("SINGLE QUERY TEST")
    print("=" * 60)
    
    test_query = "machine learning research papers 2024"
    
    print(f"🔍 Testing with query: '{test_query}'")
    
    try:
        # Test basic search first
        print("\n📋 Testing basic search...")
        results = firecrawl_search(test_query)
        print(f"✅ Basic search returned {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.get('title', 'No title')}")
        
        # Ask if user wants to test full search
        choice = input("\n🤖 Test with GPT summarization? (y/n): ").strip().lower()
        
        if choice in ['y', 'yes']:
            print("\n📋 Testing full search with GPT...")
            summary = run_firecrawl_search(test_query)
            print(f"\n✅ Full search completed!")
            print("\n📋 Summary:")
            print("=" * 50)
            print(summary)
            print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during test: {e}")


def main():
    """Main function to run the websearch tests."""
    print("🌐 WEBSEARCH.PY TESTING INTERFACE")
    print("=" * 60)
    
    while True:
        print("\nSelect a test option:")
        print("1. Test Environment Setup")
        print("2. Test Basic Search (No GPT)")
        print("3. Test Full Search (With GPT Summary)")
        print("4. Quick Single Query Test")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            test_environment_setup()
        elif choice == '2':
            if test_environment_setup():
                test_basic_search()
            else:
                print("❌ Environment not properly configured. Please fix and try again.")
        elif choice == '3':
            if test_environment_setup():
                test_full_search_with_summary()
            else:
                print("❌ Environment not properly configured. Please fix and try again.")
        elif choice == '4':
            if test_environment_setup():
                test_single_query()
            else:
                print("❌ Environment not properly configured. Please fix and try again.")
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Testing interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
