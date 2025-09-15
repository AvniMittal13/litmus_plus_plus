#!/usr/bin/env python3
"""
Test script for db_search_and_scrape function
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import the function
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.tools.db_search_and_scrape import db_search_and_scrape, run_db_search_and_scrape

def test_db_search_and_scrape():
    """
    Test the db_search_and_scrape function
    """
    # Test query
    query = "python code generation benchmarks"
    
    # Path to one of the embedding files (adjust as needed)
    db_path = r"C:\Users\avnimittal\OneDrive - Microsoft\Desktop\tp\litmus_agent\all_final_csvs_finall\01_Code_Generation\combined_01_code_generation_embeddings.pkl"
    
    print("Testing db_search_and_scrape function...")
    print(f"Query: {query}")
    print(f"Database: {db_path}")
    print("="*50)
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("Please generate embeddings first using create_and_save_embeddings.py")
        return
    
    try:
        # Run the function
        result = db_search_and_scrape(query, db_path, top_k=2)
        
        print("✅ Function executed successfully!")
        print("\nResult:")
        print("="*50)
        print(result)
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()

def test_wrapper_function():
    """
    Test the wrapper function
    """
    print("\n" + "="*50)
    print("Testing wrapper function...")
    
    # Set environment variable for testing
    os.environ["DB_PATH"] = r"C:\Users\avnimittal\OneDrive - Microsoft\Desktop\tp\litmus_agent\all_final_csvs_finall\01_Code_Generation\combined_01_code_generation_embeddings.pkl"
    
    query = "multilingual code evaluation"
    
    try:
        result = run_db_search_and_scrape(query, top_k=1)
        print("✅ Wrapper function executed successfully!")
        print("\nResult:")
        print("="*50)
        print(result)
        
    except Exception as e:
        print(f"❌ Error during wrapper execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Testing DB Search and Scrape Tool")
    print("="*50)
    
    # Test main function
    test_db_search_and_scrape()
    
    # Test wrapper function
    test_wrapper_function()
    
    print("\n✅ Testing completed!")
