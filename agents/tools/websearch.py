import os
import time
from dotenv import load_dotenv
from firecrawl import FirecrawlApp  # or whatever the correct import is
from utils.aoai_chat import get_gpt_output

load_dotenv()

def firecrawl_search(query: str):
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    response = app.search(
        query=query,
        limit=3
        # No scrape_options here => search only
    )

    response_data = response.data

    print("response form firecrawl: ", response_data)
    filtered_data = []
    for item in response_data:
        filtered_item = {
            'title': item.get('title', ''),
            'description': item.get('description', ''),
            'url': item.get('url', '')
            # no markdown or scraped content fields since we're not scraping
        }
        filtered_data.append(filtered_item)

    return filtered_data

system_message = """
Summarize the results of the websearched research paper.

- Cite the source clearly.  
- Present information in a structured and easy-to-read format.  
- Include tables wherever numerical results are given, using only actual numbers from the source.  
- Do not create or assume information. Only use information from the web search results.
- Provide explanations of all findings in detail.  
- Add a short summary/insight after each table.  
- Always highlight key findings to answer user query. Provide other details and insights from the results as well.
"""

user_message = """Summarize the following search results in detail, highlight key findings which help in answering the query with other findings.

Query: {query}

Search Output: {search_output}"""

def run_firecrawl_search(query: str):
    # maybe remove or reduce sleep if not needed
    time.sleep(15)
    search_output = firecrawl_search(query)
    output_summary = get_gpt_output(
        system_message,
        user_message.format(query=query, search_output=search_output)
    )
    return output_summary

firecrawl_search_tool = {
    "name": "firecrawl_search",
    "description": "Web search tool using Firecrawl; returns search results only (title, description, url).",
    "run_function": run_firecrawl_search
}
