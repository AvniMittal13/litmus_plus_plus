
import os
import pickle
import json
import numpy as np
from typing import List, Dict
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from sklearn.metrics.pairwise import cosine_similarity
from openai import AzureOpenAI
from utils.aoai_chat import get_gpt_output
import time

load_dotenv()

# Initialize Azure OpenAI client for embeddings
client_embedding = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDING"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING"),
    api_version="2025-01-01-preview"
)

# Initialize Firecrawl
firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY36"))

# Path to scraped content JSON file
SCRAPED_CONTENT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scraped_content.json")

# Path to query cache database
QUERY_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "query_cache.pkl")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "db", "all_embeddings_combined.pkl")

# Cache for scraped content
_scraped_content_cache = None

# Cache for query responses
_query_cache = None

def load_scraped_content() -> Dict:
    """
    Load scraped content from JSON file with caching.
    """
    global _scraped_content_cache
    
    if _scraped_content_cache is not None:
        return _scraped_content_cache
    
    try:
        if os.path.exists(SCRAPED_CONTENT_PATH):
            with open(SCRAPED_CONTENT_PATH, 'r', encoding='utf-8') as f:
                _scraped_content_cache = json.load(f)
            print(f"Loaded scraped content for {len(_scraped_content_cache)} URLs from cache")
            return _scraped_content_cache
        else:
            print(f"Scraped content file not found at {SCRAPED_CONTENT_PATH}")
            return {}
    except Exception as e:
        print(f"Error loading scraped content: {e}")
        return {}

def load_query_cache() -> List[Dict]:
    """
    Load query cache from pickle file.
    Returns list of dicts with keys: 'query', 'embedding', 'response'
    """
    global _query_cache
    
    if _query_cache is not None:
        return _query_cache
    
    try:
        if os.path.exists(QUERY_CACHE_PATH):
            with open(QUERY_CACHE_PATH, 'rb') as f:
                _query_cache = pickle.load(f)
            print(f"Loaded query cache with {len(_query_cache)} entries")
            return _query_cache
        else:
            print(f"Query cache file not found, creating new cache")
            _query_cache = []
            return _query_cache
    except Exception as e:
        print(f"Error loading query cache: {e}")
        _query_cache = []
        return _query_cache

def save_query_cache(new_entries: List[Dict]):
    """
    Save query cache to pickle file by appending new entries.
    Always loads existing cache first to prevent data loss.
    """
    global _query_cache
    try:
        # Always load the latest cache from disk first
        existing_cache = []
        if os.path.exists(QUERY_CACHE_PATH):
            try:
                with open(QUERY_CACHE_PATH, 'rb') as f:
                    existing_cache = pickle.load(f)
                print(f"Loaded {len(existing_cache)} existing cache entries")
            except Exception as e:
                print(f"Warning: Could not load existing cache: {e}")
                existing_cache = []
        
        # Create a set of existing query texts to avoid duplicates
        existing_queries = {entry['query'].strip().lower() for entry in existing_cache if 'query' in entry}
        
        # Add only new entries that don't already exist
        added_count = 0
        for entry in new_entries:
            query_text = entry.get('query', '').strip().lower()
            if query_text and query_text not in existing_queries:
                existing_cache.append(entry)
                existing_queries.add(query_text)
                added_count += 1
        
        # Save merged cache
        with open(QUERY_CACHE_PATH, 'wb') as f:
            pickle.dump(existing_cache, f)
        
        _query_cache = existing_cache
        print(f"Saved query cache: {added_count} new entries added, total {len(existing_cache)} entries")
    except Exception as e:
        print(f"Error saving query cache: {e}")

def search_cached_query(query_embedding: List[float], threshold: float = 0.90) -> str:
    """
    Search for similar query in cache. If similarity > threshold, return cached response.
    Returns None if no similar query found.
    """
    query_cache = load_query_cache()
    
    if not query_cache:
        return None
    
    best_match = None
    best_similarity = 0.0
    
    for cached_item in query_cache:
        if cached_item.get('embedding') is not None:
            similarity = cosine_similarity(
                [query_embedding], 
                [cached_item['embedding']]
            )[0][0]
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = cached_item
    
    if best_similarity >= threshold:
        print(f"Found cached query with {best_similarity:.4f} similarity: '{best_match['query']}'")
        return best_match['response']
    
    return None

# db_path = os.getenv("DB_PATH", "")
top_k: int = 1

def get_embedding(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    """
    Retrieve the OpenAI embedding for a single piece of text.
    """
    try:
        resp = client_embedding.embeddings.create(input=[text], model=model)
        return resp.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def load_embeddings_from_pkl(pkl_path: str) -> List[Dict]:
    """
    Load embeddings from a pickle file.
    """
    try:
        with open(pkl_path, 'rb') as f:
            embeddings_data = pickle.load(f)
        print(f"Loaded {len(embeddings_data)} embeddings from {pkl_path}")
        return embeddings_data
    except Exception as e:
        print(f"Error loading embeddings from {pkl_path}: {e}")
        return []

def search_similar_embeddings(query_embedding: List[float], embeddings_data: List[Dict], top_k: int = 3) -> List[Dict]:
    """
    Find the top_k most similar embeddings to the query embedding.
    """
    if not embeddings_data or not query_embedding:
        return []
    
    similarities = []
    for i, item in enumerate(embeddings_data):
        if item.get('embedding') is not None:
            similarity = cosine_similarity(
                [query_embedding], 
                [item['embedding']]
            )[0][0]
            similarities.append((i, similarity, item))
    
    # Sort by similarity and get top_k
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    results = []
    for i, (idx, sim_score, item) in enumerate(similarities[:top_k]):
        result = {
            'rank': i + 1,
            'similarity_score': sim_score,
            'url': item.get('url', ''),
            'task': item.get('task', ''),
            'languages': item.get('languages', ''),
            'models': item.get('models', ''),
            'description': item.get('description', ''),
            'source_file': item.get('source_file', ''),
            'row_index': item.get('row_index', '')
        }
        results.append(result)
    
    return results

def scrape_url_with_firecrawl(url: str) -> Dict:
    """
    Get scraped content for a URL from the scraped_content.json file.
    Falls back to actual Firecrawl scraping if URL not found in cache.
    """
    # First, try to get content from the scraped content cache
    scraped_content = load_scraped_content()
    
    if url in scraped_content:
        cached_data = scraped_content[url]
        if cached_data.get('success', False):
            return {
                'url': url,
                'markdown': cached_data.get('content', ''),
                'success': True
            }
        else:
            return {
                'url': url,
                'markdown': '',
                'success': False,
                'error': cached_data.get('error', 'Content not available in cache')
            }
    
    # Fallback to actual Firecrawl scraping if URL not found in cache
    print(f"URL {url} not found in scraped content cache, falling back to Firecrawl...")
    try:
        # Use cached data if it's less than 1 hour old (3600000 ms)
        time.sleep(15)
        scrape_result = firecrawl.scrape_url(
            url, 
            formats=['markdown'],
            max_age=3600000  # 1 hour in milliseconds
        )

        # Check if scrape was successful and has markdown content
        if hasattr(scrape_result, 'markdown') and scrape_result.markdown:
            return {
                'url': url,
                'markdown': scrape_result.markdown,
                'success': True
            }
        else:
            return {
                'url': url,
                'markdown': '',
                'success': False,
                'error': 'No markdown content returned'
            }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {
            'url': url,
            'markdown': '',
            'success': False,
            'error': str(e)
        }

def db_search_and_scrape(query: str, return_intermediates: bool = False):
    """
    Main function to:
    1. Create embedding for the query
    2. Check if similar query exists in cache (>95% similarity)
    3. If cached, return cached response
    4. Otherwise, search for similar embeddings in the database
    5. Extract URLs from top_k results
    6. Scrape each URL using Firecrawl
    7. Use scraped content to generate GPT response
    8. Save query and response to cache
    
    Args:
        query (str): The search query
        return_intermediates (bool): If True, returns (response, intermediates_dict)
    
    Returns:
        str or tuple: GPT-generated response, or (response, intermediates) if return_intermediates=True
    """
    
    from datetime import datetime
    
    # Initialize intermediates tracking
    intermediates = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "cache_hit": False,
        "embedding_generation": {},
        "database_search": {},
        "scraping_results": [],
        "gpt_analysis": {},
        "final_response_length": 0
    }
    
    print(f"Starting db_search_and_scrape for query: '{query}'")
    global db_path
    global top_k
    print(f"Database path: {db_path}")
    
    # Step 1: Create embedding for the query
    print("Creating embedding for query...")
    query_embedding = get_embedding(query)
    if not query_embedding:
        intermediates["embedding_generation"]["success"] = False
        intermediates["embedding_generation"]["error"] = "Could not generate embedding"
        if return_intermediates:
            return "Error: Could not generate embedding for the query.", intermediates
        return "Error: Could not generate embedding for the query."
    
    intermediates["embedding_generation"]["success"] = True
    intermediates["embedding_generation"]["embedding_dim"] = len(query_embedding)
    
    # Step 2: Check cache for similar query
    print("Checking query cache...")
    cached_response = search_cached_query(query_embedding)
    if cached_response:
        print("✅ Returning cached response")
        intermediates["cache_hit"] = True
        intermediates["final_response_length"] = len(cached_response)
        if return_intermediates:
            return cached_response, intermediates
        return cached_response
    
    print("No cached response found, proceeding with full search...")
    
    # Step 3: Load embeddings from the database
    print("Loading embeddings from database...")
    embeddings_data = load_embeddings_from_pkl(db_path)
    if not embeddings_data:
        intermediates["database_search"]["error"] = "Could not load embeddings"
        if return_intermediates:
            return "Error: Could not load embeddings from the database.", intermediates
        return "Error: Could not load embeddings from the database."
    
    # Step 4: Find similar embeddings
    print(f"Searching for top {top_k} similar embeddings...")
    similar_results = search_similar_embeddings(query_embedding, embeddings_data, top_k)
    if not similar_results:
        intermediates["database_search"]["similar_results"] = []
        if return_intermediates:
            return "No similar results found in the database.", intermediates
        return "No similar results found in the database."
    
    # Store search results in intermediates
    intermediates["database_search"] = {
        "db_path": db_path,
        "top_k": top_k,
        "similar_results": similar_results
    }
    
    # Print similarity results
    print("\nTop matching results:")
    for result in similar_results:
        print(f"  Rank {result['rank']}: {result['url']} (Similarity: {result['similarity_score']:.4f})")
    
    # Step 4: Extract URLs and scrape content
    print(f"\nScraping {len(similar_results)} URLs...")
    scraped_contents = []
    
    for i, result in enumerate(similar_results):
        url = result['url']
        if not url:
            print(f"  Skipping result {i+1}: No URL found")
            continue
        
        print(f"  Scraping {i+1}/{len(similar_results)}: {url}")
        scraped_content = scrape_url_with_firecrawl(url)
        
        if scraped_content.get('success', False) and scraped_content.get('markdown'):
            scraped_contents.append({
                'rank': result['rank'],
                'similarity_score': result['similarity_score'],
                'url': url,
                'title': result.get('task', 'Research Paper'),  # Use task as title fallback
                'content': scraped_content['markdown'],
                'task': result['task'],
                'languages': result['languages'],
                'models': result['models'],
                'description': result.get('description', '')  # Use original description from embedding
            })
            print(f"    ✅ Successfully scraped {url}")
            
            # Store scraping result in intermediates
            intermediates["scraping_results"].append({
                "url": url,
                "success": True,
                "content_length": len(scraped_content['markdown']),
                "scrape_method": "cached" if url in load_scraped_content() else "firecrawl"
            })
        else:
            print(f"    ❌ Failed to scrape {url}: {scraped_content.get('error', 'Unknown error')}")
            
            # Store failed scraping in intermediates
            intermediates["scraping_results"].append({
                "url": url,
                "success": False,
                "error": scraped_content.get('error', 'Unknown error'),
                "scrape_method": "failed"
            })
        
        # Add delay between requests to be respectful
        time.sleep(2)
    
    if not scraped_contents:
        intermediates["gpt_analysis"]["error"] = "Could not scrape any URLs"
        if return_intermediates:
            return "Error: Could not scrape any of the URLs from the search results.", intermediates
        return "Error: Could not scrape any of the URLs from the search results."
    
    # Step 5: Prepare content for GPT
    print(f"\nPreparing content for GPT analysis...")
    
    # Format scraped content for GPT input
    formatted_content = ""
    for i, content in enumerate(scraped_contents):
        formatted_content += f"\n--- Research Paper {i+1} (Similarity: {content['similarity_score']:.4f}) ---\n"
        formatted_content += f"URL: {content['url']}\n"
        formatted_content += f"Title: {content['title']}\n"
        formatted_content += f"Task: {content['task']}\n"
        formatted_content += f"Languages: {content['languages']}\n"
        formatted_content += f"Models: {content['models']}\n"
        formatted_content += f"Description: {content['description']}\n"
        formatted_content += f"Content:\n{content['content']}\n"
        formatted_content += "\n" + "="*80 + "\n"
    
    # System message for GPT
    system_message = """
You are an expert research analyst. You have been provided with research papers that are most similar to a user's query. 

Your task is to:
1. Analyze the provided research papers thoroughly
2. Extract key findings, methodologies, and results that are relevant to the user's query
3. Provide a comprehensive summary that directly addresses the user's question
4. Include specific details, numbers, and findings from the papers
5. Cite sources clearly with URLs
6. Present information in a structured, easy-to-read format
7. Use tables where appropriate for numerical results
8. Highlight key insights and takeaways
9. Only use information from the provided research papers - do not make assumptions or add external information

Format your response with clear sections and make it informative and actionable.
"""
    
    # User message with query and scraped content
    user_message = f"""
Please analyze the following research papers to answer this query: "{query}"

Here are the most relevant research papers found:

{formatted_content}

Please provide a comprehensive analysis that directly addresses the query, including:
- Key findings from each paper
- Relevant methodologies and approaches
- Important results and metrics
- How these findings relate to the query
- Practical insights and takeaways
- Clear citations with URLs

Focus on information that directly helps answer the user's query while providing additional valuable insights from the research.
"""
    
    # Store GPT analysis info in intermediates
    intermediates["gpt_analysis"] = {
        "system_message": system_message[:200] + "...",  # Preview only
        "user_message_preview": user_message[:500] + "...",
        "formatted_content_length": len(formatted_content),
        "papers_analyzed": len(scraped_contents)
    }
    
    # Step 6: Generate GPT response
    print("Generating GPT response...")
    try:
        gpt_response = get_gpt_output(system_message, user_message)
        
        # Add metadata about the search
        metadata = f"\n\n--- Search Metadata ---\n"
        metadata += f"Query: {query}\n"
        metadata += f"Database searched: {db_path}\n"
        metadata += f"Total papers analyzed: {len(scraped_contents)}\n"
        metadata += f"Papers found:\n"
        for content in scraped_contents:
            metadata += f"  • {content['title']} (Similarity: {content['similarity_score']:.4f})\n    {content['url']}\n"
        
        final_response = gpt_response + metadata
        
        # Store final response length in intermediates
        intermediates["final_response_length"] = len(final_response)
        
        # Step 7: Save to query cache (append only)
        print("Saving query and response to cache...")
        new_entry = {
            'query': query,
            'embedding': query_embedding,
            'response': final_response
        }
        save_query_cache([new_entry])
        
        if return_intermediates:
            return final_response, intermediates
        return final_response
        
    except Exception as e:
        print(f"Error generating GPT response: {e}")
        intermediates["gpt_analysis"]["error"] = str(e)
        error_msg = f"Error: Could not generate response. Scraped {len(scraped_contents)} papers successfully but failed to process with GPT."
        if return_intermediates:
            return error_msg, intermediates
        return error_msg


# Tool description for integration with agent systems
description = """
Web searcher and crawler tool. It takes natural language query as input, searches the web, research papers, scrapes them and returns the results. It can take one natural language query at a time.

The tool requires:
- query: Natural language search query

Returns a detailed analysis based on the most relevant research papers found.
"""

def run_db_search_and_scrape(query: str):
    """
    Wrapper function for tool integration
    """
    global db_path
    if not db_path:
        db_path = os.environ.get("DB_PATH", "")
        if not db_path:
            return "Error: No database path provided. Please specify db_path parameter or set DB_PATH environment variable."
    
    final_response = db_search_and_scrape(query)
    return final_response

# Tool configuration for agent systems
db_search_and_scrape_tool = {
    "name": "db_search_and_scrape",
    "description": description,
    "run_function": run_db_search_and_scrape
}