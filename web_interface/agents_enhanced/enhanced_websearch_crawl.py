import os
import sys
import threading
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
import shutil

import re
import json
import pprint
import autogen
from autogen.coding import LocalCommandLineCodeExecutor
from autogen import Agent, AssistantAgent, ConversableAgent, UserProxyAgent
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent

from autogen import AssistantAgent
import chromadb
from chromadb.utils import embedding_functions

# Add parent directory to path to import existing utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.aoai_chat import model_config

load_dotenv()


class EnhancedWebSearchCrawlAgent(ConversableAgent):
    """
    Enhanced Web Search and Crawl Agent with real-time WebSocket streaming capabilities.
    Inherits the core functionality of WebSearch_And_Crawl_Agent but adds UI integration.
    """
    
    def __init__(self, session_id: str, socketio_instance, n_iters=2, **kwargs):
        """
        Initializes an Enhanced Web Search and Crawl Agent instance.

        Parameters:
            - session_id (str): The WebSocket session ID for streaming
            - socketio_instance: SocketIO instance for real-time communication
            - n_iters (int, optional): The number of "improvement" iterations to run. Defaults to 2.
            - **kwargs: keyword arguments for the parent ConversableAgent.
        """
        super().__init__(**kwargs)
        self.session_id = session_id
        self.socketio = socketio_instance
        self.register_reply([Agent, None], reply_func=EnhancedWebSearchCrawlAgent._reply_user, position=0)
        self._n_iters = n_iters
        
        # Internal conversation tracking
        self.internal_conversation = []
        self.conversation_step = 0

    def _emit_internal_message(self, message_type: str, content: str, metadata: dict = None):
        """Emit internal conversation message to UI via WebSocket"""
        try:
            self.socketio.emit('agent_internal_conversation', {
                'agent_name': 'websearch_and_crawl_agent',
                'type': message_type,
                'content': content,
                'metadata': metadata or {},
                'step': self.conversation_step,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            
            # Store for later reference
            self.internal_conversation.append({
                'type': message_type,
                'content': content,
                'metadata': metadata or {},
                'step': self.conversation_step,
                'timestamp': datetime.now().isoformat()
            })
            
            self.conversation_step += 1
            print(f"[EnhancedWebSearchCrawl] Emitted internal message: {message_type}")
            
        except Exception as e:
            print(f"[EnhancedWebSearchCrawl] Error emitting internal message: {e}")

    def _reply_user(self, messages=None, sender=None, config=None):
        """Enhanced reply method with real-time streaming and actual web search functionality"""
        print(f"[EnhancedWebSearchCrawl] _reply_user called with messages={len(messages) if messages else 0}")
        
        if all((messages is None, sender is None)):
            error_msg = f"Either {messages=} or {sender=} must be provided."
            raise AssertionError(error_msg)
        if messages is None:
            messages = self._oai_messages[sender]

        user_question = messages[-1]["content"]
        print(f"[EnhancedWebSearchCrawl] Processing question: {user_question[:100]}...")
        
        try:
            # Reset conversation tracking
            self.internal_conversation = []
            self.conversation_step = 0
            
            # Start the search process
            self._emit_internal_message(
                "websearch_initialization",
                "Initializing web search and crawl process...",
                {"query": user_question, "agent_type": "websearch_crawl"}
            )
            
            # Import firecrawl tool
            try:
                # from agents.tools.webcrawl import db_search_and_scrape_tool
                from agents.tools.db_search_and_scrape import db_search_and_scrape_tool

            except ImportError as e:
                self._emit_internal_message(
                    "tool_import_error",
                    f"Failed to import firecrawl tool: {str(e)}",
                    {"error": str(e)}
                )
                return True, f"Error: Could not import web search tool: {str(e)}"
            
#             # Define the system message for web search
#             system_message = """
# **Role:**
# You are a **Web Search and Crawl Agent** with **expert knowledge in NLP for low-resource languages**.
# - You search and crawl the web using the **Firecrawl tool**.
# - Use Firecrawl **only** when up-to-date or external information is required and not already available.
# - Always consider **specific challenges and opportunities in low-resource NLP** and relate them to the user's query.

# ---

# ### Responsibilities

# 1. **Search Execution**
# - Call `firecrawl_search` with **precise and well-formed search instructions**.
# - Run **multiple, diverse queries** before finalizing results. This helps in gathering information from multiple sources and increases credibility.
# - If previous searches are given in input then DONOT repeat searching from them. Search for diverse **aspects** or papers for the topic.

# 2. **Result Quality**
# - Return only **accurate, and high-quality** results.
# - Ensure **diversity** in results. If a topic is already covered, expand to **related subtopics**.
# - Prioritize **usefulness over quantity**.

# 3. **Final Response Construction**
# - Provide results in a **structured format**. If numbers are found, present in detailed tables
# - Always **cite all sources** used.
# - Include summary of **additional insights** from web scraping for broader analysis.
# - Present **detailed numerical information in tables** (fill with actual numbers whenever found). DONOT create numbers on your own.
# - Provide a **brief insight/summary** of the tables.
# - If nothing found after multiple queries, provide a summary of the search results and insights gained.

# 4. **Iterative Search**
# - After each query, decide if **further searches** are needed.
# - Refine or expand queries accordingly.

# ---

# ### Termination Rule
# - Give Final answer only in the end after multiple searches. Once answer is given it CANNOT be changed. Contiuously call `firecrawl_search` until satisfied.
# - Once all searches and summaries are completed, output the final structured response.
# - End with `TERMINATE`.
# """

            system_message= """
**Role:**
You are a **Web Search and Crawl Agent** with **expert knowledge in NLP for low-resource languages**.
- You search and crawl the web using the **Firecrawl tool**.
- Use Firecrawl **only** when up-to-date or external information is required and not already available.
- Always consider **specific challenges and opportunities in low-resource NLP** and relate them to the user’s query.

---

### Responsibilities

1. **Search Execution**
- Call `db_search_and_scrape_tool` with **precise and well-formed search instructions**.
- Run **multiple, diverse queries** before finalizing results. This helps in gathering information from multiple sources and increases credibility.
- If previous searches are given in input then DONOT repeat searching from them. Search for diverse **aspects** or papers for the topic.

2. **Result Quality**
- Return only **accurate, and high-quality** results.
- Ensure **diversity** in results. If a topic is already covered, expand to **related subtopics**.
- Prioritize **usefulness over quantity**.

3. **Final Response Construction**
- Provide results in a **structured format**. If numbers are found, present in detailed tables
- Always **cite all sources** used.
- Include summary of **additional insights** from web scraping for broader analysis.
- Present **detailed numerical information in tables** (fill with actual numbers whenever found). DONOT create numbers on your own.
- Provide a **brief insight/summary** of the tables.
- If nothing found after multiple queries, provide a summary of the search results and insights gained.

4. **Iterative Search**
- After each query, decide if **further searches** are needed.
- Refine or expand queries accordingly.

---

### Termination Rule
- Give Final answer only in the end after multiple searches. Once answer is given it CANNOT be changed. Contiuously call `db_search_and_scrape_tool` until satisfied.
- Once all searches and summaries are completed, output the final structured response.
- End with `TERMINATE`.

"""


            self._emit_internal_message(
                "agent_setup",
                "Setting up assistant and user proxy agents for web search execution...",
                {"system_message_length": len(system_message)}
            )

            # Create assistant agent with web search capabilities
            assistant = ConversableAgent(
                name="Assistant",
                system_message=system_message,
                llm_config=model_config,
            )

            # Create user proxy agent for tool execution
            user_proxy = ConversableAgent(
                name="User",
                llm_config=False,
                is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
                human_input_mode="NEVER",
            )

            # Register the firecrawl search tool
            self._emit_internal_message(
                "tool_registration",
                "Registering db_search_and_scrape tool with agents...",
                {"tool_name": "firecrawl_search"}
            )

            assistant.register_for_llm(
                name=db_search_and_scrape_tool["name"], 
                description=db_search_and_scrape_tool["description"]
            )(db_search_and_scrape_tool["run_function"])

            user_proxy.register_for_execution(
                name=db_search_and_scrape_tool["name"]
            )(db_search_and_scrape_tool["run_function"])

            # Start the conversation
            self._emit_internal_message(
                "chat_initiation",
                "Initiating chat between assistant and user proxy for web search execution...",
                {"user_question_preview": user_question[:100]}
            )

            # Execute the chat
            chat_result = user_proxy.initiate_chat(assistant, message=user_question)
            
            # Extract and emit tool calls from the chat result
            self._extract_tool_calls_from_chat_result(chat_result)
            
            # Extract the response
            response = user_proxy._oai_messages[assistant][-1]["content"]
            
            self._emit_internal_message(
                "response_processing",
                "Processing and cleaning response from web search agents...",
                {"response_length": len(response)}
            )

            # Remove the TERMINATE keyword from response
            response = re.sub(r"TERMINATE", "", response)
            
            self._emit_internal_message(
                "websearch_completion",
                "Web search and crawl process completed successfully",
                {
                    "final_response_length": len(response),
                    "chat_result_available": chat_result is not None
                }
            )
            
            return True, response
            
        except Exception as e:
            self._emit_internal_message(
                "websearch_error",
                f"Error in web search and crawl process: {str(e)}",
                {"error": str(e), "step": "critical_error"}
            )
            
            # Return a fallback response
            return True, f"Error performing web search: {str(e)}"

    def _extract_tool_calls_from_chat_result(self, chat_result):
        """Extract and emit tool calls and responses from the chat conversation"""
        try:
            if not chat_result or not hasattr(chat_result, 'chat_history'):
                self._emit_internal_message(
                    "tool_extraction_info",
                    "No chat history available for tool call extraction",
                    {"chat_result_available": chat_result is not None}
                )
                return
            
            tool_call_sequence = 1
            
            self._emit_internal_message(
                "tool_extraction_start",
                f"Analyzing chat history for tool calls ({len(chat_result.chat_history)} messages)...",
                {"message_count": len(chat_result.chat_history)}
            )
            
            for i, message in enumerate(chat_result.chat_history):
                # Handle tool calls (when assistant wants to call a tool)
                if message.get('tool_calls'):
                    for tool_call in message['tool_calls']:
                        function_info = tool_call.get('function', {})
                        tool_name = function_info.get('name', 'unknown_tool')
                        tool_args_str = function_info.get('arguments', '{}')
                        
                        try:
                            import json
                            tool_args = json.loads(tool_args_str) if tool_args_str else {}
                        except json.JSONDecodeError:
                            tool_args = {"raw_arguments": tool_args_str}
                        
                        self._emit_internal_message(
                            "tool_call_execution",
                            f"Tool Call #{tool_call_sequence}: {tool_name}",
                            {
                                "tool_name": tool_name,
                                "tool_call_id": tool_call.get('id', f'call_{tool_call_sequence}'),
                                "tool_arguments": tool_args,
                                "call_sequence": tool_call_sequence,
                                "message_index": i
                            }
                        )
                        
                        # Emit detailed arguments
                        if tool_args and tool_args != {}:
                            # Send full arguments to frontend - let frontend handle truncation
                            self._emit_internal_message(
                                "tool_call_arguments",
                                f"Arguments for {tool_name}: {str(tool_args)}",  # Send full arguments
                                {
                                    "tool_name": tool_name,
                                    "full_arguments": tool_args,
                                    "call_sequence": tool_call_sequence
                                }
                            )
                        
                        tool_call_sequence += 1
                
                # Handle tool responses (results from tool execution)
                elif message.get('tool_responses'):
                    for tool_response in message['tool_responses']:
                        tool_call_id = tool_response.get('tool_call_id', 'unknown')
                        content = tool_response.get('content', 'No content')
                        
                        # Send full content to frontend - let frontend handle truncation
                        self._emit_internal_message(
                            "tool_call_response",
                            f"Tool Response: {content}",  # Send full content
                            {
                                "tool_call_id": tool_call_id,
                                "full_content": content,
                                "content_length": len(content),
                                "message_index": i
                            }
                        )
                
                # Handle regular content that might contain tool execution info
                elif message.get('content') and 'db_search_and_scrape' in message.get('content', ''):
                    content = message.get('content', '')
                    # Send full content to frontend - let frontend handle truncation
                    self._emit_internal_message(
                        "tool_content_detected",
                        f"Tool-related content detected: {content}",  # Send full content
                        {
                            "content_preview": content[:500],  # Keep preview in metadata for reference
                            "full_content": content,
                            "message_role": message.get('role', 'unknown'),
                            "message_index": i
                        }
                    )
            
            self._emit_internal_message(
                "tool_extraction_complete",
                f"Tool call extraction completed. Found {tool_call_sequence - 1} tool calls.",
                {"total_tool_calls": tool_call_sequence - 1}
            )
            
        except Exception as e:
            self._emit_internal_message(
                "tool_extraction_error",
                f"Error extracting tool calls: {str(e)}",
                {"error": str(e)}
            )
            print(f"[EnhancedWebSearchCrawl] Error extracting tool calls: {e}")
