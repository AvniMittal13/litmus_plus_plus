
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
firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

# Path to scraped content JSON file
SCRAPED_CONTENT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scraped_content.json")

# Cache for scraped content
_scraped_content_cache = None

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

# Use relative path from project root for deployment compatibility
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "db", "all_embeddings_combined.pkl")
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

def db_search_and_scrape(query: str ) -> str:
    """
    Main function to:
    1. Create embedding for the query
    2. Search for similar embeddings in the database
    3. Extract URLs from top_k results
    4. Scrape each URL using Firecrawl
    5. Use scraped content to generate GPT response
    
    Args:
        query (str): The search query
    
    Returns:
        str: GPT-generated response based on scraped content
    """
    
    print(f"Starting db_search_and_scrape for query: '{query}'")
    global db_path
    global top_k
    print(f"Database path: {db_path}")
    
    # Step 1: Create embedding for the query
    print("Creating embedding for query...")
    query_embedding = get_embedding(query)
    if not query_embedding:
        return "Error: Could not generate embedding for the query."
    
    # Step 2: Load embeddings from the database
    print("Loading embeddings from database...")
    embeddings_data = load_embeddings_from_pkl(db_path)
    if not embeddings_data:
        return "Error: Could not load embeddings from the database."
    
    # Step 3: Find similar embeddings
    print(f"Searching for top {top_k} similar embeddings...")
    similar_results = search_similar_embeddings(query_embedding, embeddings_data, top_k)
    if not similar_results:
        return "No similar results found in the database."
    
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
        else:
            print(f"    ❌ Failed to scrape {url}: {scraped_content.get('error', 'Unknown error')}")
        
        # Add delay between requests to be respectful
        time.sleep(2)
    
    if not scraped_contents:
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
        
        return gpt_response + metadata
        
    except Exception as e:
        print(f"Error generating GPT response: {e}")
        return f"Error: Could not generate response. Scraped {len(scraped_contents)} papers successfully but failed to process with GPT."


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
    
    
    return db_search_and_scrape(query)

# Tool configuration for agent systems
db_search_and_scrape_tool = {
    "name": "db_search_and_scrape",
    "description": description,
    "run_function": run_db_search_and_scrape
}