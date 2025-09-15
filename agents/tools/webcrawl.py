import os
import asyncio
from dotenv import load_dotenv
from firecrawl import AsyncFirecrawlApp, FirecrawlApp, ScrapeOptions
from utils.aoai_chat import get_gpt_output
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


system_message = """
Summarize the results of the webscraped research paper.

- Cite the source clearly.  
- Present information in a structured and easy-to-read format.  
- Include tables wherever numerical results are given, using only actual numbers from the source.  
- Do not create or assume information. Only use information from the webscraped results.
- Provide explanations of all findings in detail.  
- Add a short summary/insight after each table.  
- Always Highlight key findings to answer user query. Provide other details and insights from the results as well
"""


user_message = """Summarize the following search results in detail, highlight key findings which help in answering the query with other findings.

Query: {query}

Search Output: {search_output}"""

def run_firecrawl_search(query: str):
    # Since firecrawl_search is not async, we don't need asyncio
    time.sleep(15)
    search_output = firecrawl_search(query)
    output_summary = get_gpt_output(
        system_message,
        user_message.format(query=query, search_output=search_output)
    )
    return output_summary

description = """
Web searcher and crawler tool. It takes natural language query as input, searches the web, research papers, scrapes them and returns the results. It can take one natural language query at a time.
"""

firecrawl_search_tool = {
    "name": "firecrawl_search",
    "description": description,
    "run_function": run_firecrawl_search
}