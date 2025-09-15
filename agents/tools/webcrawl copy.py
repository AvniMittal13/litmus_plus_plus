import os
import asyncio
from dotenv import load_dotenv
from firecrawl import AsyncFirecrawlApp, FirecrawlApp, ScrapeOptions
import time
load_dotenv()

def firecrawl_search(query: str):
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    response = app.search(
        query=query,
        limit=1,
        scrape_options=ScrapeOptions(formats=["markdown"])
    )
    
    response_data = response.data
    filtered_data = []
    for item in response_data:
        filtered_item = {
            'title': item.get('title', ''),
            'description': item.get('description', ''),
            'url': item.get('url', ''),
            'markdown': item.get('markdown', '')
        }
        filtered_data.append(filtered_item)

    return filtered_data

def run_firecrawl_search(query: str):
    # Since firecrawl_search is not async, we don't need asyncio
    time.sleep(5)
    return firecrawl_search(query)

description = """
Web searcher and crawler tool. It takes natural language query as input, searches the web, research papers, scrapes them and returns the results. It can take one natural language query at a time.
"""

firecrawl_search_tool = {
    "name": "firecrawl_search",
    "description": description,
    "run_function": run_firecrawl_search
}