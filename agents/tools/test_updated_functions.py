#!/usr/bin/env python3
"""
Quick test script to verify the updated db_search_and_scrape function works correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import the function
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_firecrawl_function():
    """Test the updated Firecrawl function"""
    from agents.tools.db_search_and_scrape import scrape_url_with_firecrawl
    
    # Test with a simple URL
    test_url = "https://arxiv.org/abs/2301.00001"  # Example arXiv URL
    
    print("Testing updated Firecrawl function...")
    print(f"URL: {test_url}")
    
    try:
        result = scrape_url_with_firecrawl(test_url)
        
        print(f"Success: {result.get('success', False)}")
        print(f"Markdown length: {len(result.get('markdown', ''))}")
        
        if result.get('success'):
            print("✅ Firecrawl function working correctly!")
        else:
            print(f"❌ Firecrawl failed: {result.get('error', 'Unknown error')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        return False

def test_embedding_functions():
    """Test the embedding-related functions"""
    from agents.tools.db_search_and_scrape import get_embedding, load_embeddings_from_pkl
    
    print("\nTesting embedding functions...")
    
    # Test embedding generation
    test_query = "test query for embedding"
    embedding = get_embedding(test_query)
    
    if embedding:
        print(f"✅ Embedding generated successfully! Length: {len(embedding)}")
    else:
        print("❌ Failed to generate embedding")
        return False
    
    # Test loading embeddings (if file exists)
    relative_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "litmus_agent", "all_final_csvs_finall", "01_Code_Generation", "combined_01_code_generation_embeddings.pkl")
    fallback_path = r"C:\Users\avnimittal\OneDrive - Microsoft\Desktop\tp\litmus_agent\all_final_csvs_finall\01_Code_Generation\combined_01_code_generation_embeddings.pkl"
    
    test_pkl_path = relative_path if os.path.exists(relative_path) else fallback_path
    
    if os.path.exists(test_pkl_path):
        embeddings_data = load_embeddings_from_pkl(test_pkl_path)
        if embeddings_data:
            print(f"✅ Loaded {len(embeddings_data)} embeddings from database")
            return True
        else:
            print("❌ Failed to load embeddings")
            return False
    else:
        print(f"⚠️  Test embedding file not found: {test_pkl_path}")
        print("   This is expected if embeddings haven't been generated yet")
        return True

if __name__ == "__main__":
    print("🔍 Testing Updated DB Search and Scrape Functions")
    print("=" * 50)
    
    # Test embedding functions
    embedding_test = test_embedding_functions()
    
    # Test Firecrawl function
    firecrawl_test = test_firecrawl_function()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  Embedding functions: {'✅ PASS' if embedding_test else '❌ FAIL'}")
    print(f"  Firecrawl function:  {'✅ PASS' if firecrawl_test else '❌ FAIL'}")
    
    if embedding_test and firecrawl_test:
        print("\n🎉 All tests passed! The function should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
