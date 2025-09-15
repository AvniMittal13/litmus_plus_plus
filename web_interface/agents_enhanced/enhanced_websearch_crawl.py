import os
import sys
import threading
import time
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
        
        # Register webcrawl tool if available
        try:
            from agents.tools.webcrawl import firecrawl_search_tool
            
            # Register tool for LLM use
            self.register_for_llm(
                name=firecrawl_search_tool["name"], 
                description=firecrawl_search_tool["description"]
            )(firecrawl_search_tool["run_function"])
            
            # Register tool for execution
            self.register_for_execution(
                name=firecrawl_search_tool["name"]
            )(firecrawl_search_tool["run_function"])
            
            print("[EnhancedWebSearchCrawlAgent] Successfully registered firecrawl search tool")
            
        except Exception as e:
            print(f"[EnhancedWebSearchCrawlAgent] Warning: Could not register firecrawl tool: {e}")

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

    def _analyze_user_request(self, user_query: str):
        """Analyze user request to plan search strategy"""
        self._emit_internal_message(
            "search_planning", 
            f"Analyzing user request to plan search strategy: '{user_query}'",
            {"query": user_query, "step": "planning"}
        )
        
        # Extract search keywords and intent
        search_keywords = []
        search_intent = "general_search"
        
        # Simple keyword extraction (could be enhanced with NLP)
        keywords = re.findall(r'\b\w+\b', user_query.lower())
        search_keywords = [word for word in keywords if len(word) > 2]
        
        # Determine search intent
        if any(word in user_query.lower() for word in ['latest', 'recent', 'new', 'current']):
            search_intent = "recent_information"
        elif any(word in user_query.lower() for word in ['how', 'tutorial', 'guide', 'steps']):
            search_intent = "instructional"
        elif any(word in user_query.lower() for word in ['compare', 'versus', 'difference']):
            search_intent = "comparative"
        
        self._emit_internal_message(
            "search_strategy",
            f"Search strategy determined: {search_intent} with keywords: {', '.join(search_keywords[:5])}",
            {
                "keywords": search_keywords,
                "intent": search_intent,
                "keyword_count": len(search_keywords)
            }
        )
        
        return search_keywords, search_intent

    def _execute_search(self, search_query: str):
        """Execute web search using available tools"""
        self._emit_internal_message(
            "search_execution_start",
            f"Executing web search for: '{search_query}'",
            {"search_query": search_query, "tool": "firecrawl"}
        )
        
        try:
            # This would be replaced with actual tool execution in the real implementation
            # For now, we'll simulate the search process
            
            self._emit_internal_message(
                "web_crawling",
                "Crawling web pages and extracting relevant content...",
                {"status": "in_progress", "crawl_type": "targeted"}
            )
            
            # Simulate processing time
            time.sleep(0.5)
            
            self._emit_internal_message(
                "content_extraction",
                "Extracting and processing content from crawled pages...",
                {"status": "processing", "content_type": "structured"}
            )
            
            self._emit_internal_message(
                "search_results_analysis",
                "Analyzing search results and filtering relevant information...",
                {"status": "analyzing", "filter_criteria": "relevance_score"}
            )
            
            return f"Search completed for query: {search_query}"
            
        except Exception as e:
            self._emit_internal_message(
                "search_error",
                f"Error during web search execution: {str(e)}",
                {"error": str(e), "status": "error"}
            )
            raise

    def _synthesize_results(self, search_results: str, user_query: str):
        """Synthesize search results into a coherent response"""
        self._emit_internal_message(
            "result_synthesis_start",
            "Synthesizing search results into coherent response...",
            {"input_length": len(search_results), "synthesis_type": "comprehensive"}
        )
        
        # Analyze relevance
        self._emit_internal_message(
            "relevance_analysis",
            "Analyzing relevance of found information to user query...",
            {"query": user_query, "analysis_type": "semantic_matching"}
        )
        
        # Structure response
        self._emit_internal_message(
            "response_structuring",
            "Structuring response with citations and source references...",
            {"structure_type": "cited_response", "source_count": "multiple"}
        )
        
        return search_results

    def _reply_user(self, messages=None, sender=None, config=None):
        """Enhanced reply method with real-time streaming"""
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
            
            # Analyze user request
            search_keywords, search_intent = self._analyze_user_request(user_question)
            
            # Execute search
            search_results = self._execute_search(user_question)
            
            # Synthesize results
            final_response = self._synthesize_results(search_results, user_question)
            
            self._emit_internal_message(
                "websearch_completion",
                "Web search and crawl process completed successfully",
                {
                    "response_length": len(final_response),
                    "search_intent": search_intent,
                    "keywords_used": len(search_keywords)
                }
            )
            
            return True, final_response
            
        except Exception as e:
            self._emit_internal_message(
                "websearch_error",
                f"Error in web search and crawl process: {str(e)}",
                {"error": str(e), "step": "critical_error"}
            )
            
            # Return a fallback response
            return True, f"Error performing web search: {str(e)}"
