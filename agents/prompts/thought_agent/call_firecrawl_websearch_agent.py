# has access to tool for web search. actually performs the web search

# system_message="""
# You have access to a tool that searches the web using Firecrawl. Use it to fetch relevant info when needed.
# """

system_message = """
You are the Firecrawl Websearch Executor.  
You have access to a tool that performs web searches using Firecrawl.  
Your role is to execute searches when requested and return the results clearly.  
Only perform searches when explicitly triggered, and ensure outputs are passed back in a clean and useful format.
"""

description="""
Executes web searches using Firecrawl and returns results from the `firecrawl_websearch` agent. Only and only triggered after `firecrawl_websearch` agent requests execution.
"""


call_firecrawl_websearch_agent = {
    "type": "conversable",
    "name": "firecrawl_websearch_execution_agent",
    "description": description,
    "system_message": system_message,
    "human_input_mode": "NEVER",
    "code_execution_config": False,
    "llm_config": False
}