from datetime import datetime
from agents.custom_agents.websearch_and_crawl import WebSearch_And_Crawl_Agent
from autogen import ConversableAgent, Agent
from agents.tools.webcrawl import firecrawl_search_tool
from utils.aoai_chat import model_config
import re

class EnhancedWebSearchCrawlAgent(WebSearch_And_Crawl_Agent):
    """
    Enhanced Web Search and Crawl Agent with internal conversation tracking.
    
    This agent extends the standard WebSearch_And_Crawl_Agent to capture and emit
    internal search process steps for visualization in the web interface.
    """
    
    def __init__(self, socketio=None, session_id=None, **kwargs):
        """
        Initialize the enhanced websearch agent with WebSocket communication.
        
        Args:
            socketio: SocketIO instance for real-time communication
            session_id: Session ID for WebSocket room management
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(**kwargs)
        self.socketio = socketio
        self.session_id = session_id
        self.internal_conversation = []
        
    def _emit_internal_message(self, message_type: str, content: str, metadata: dict = None):
        """
        Emit internal message for real-time monitoring of search process.
        
        Args:
            message_type: Type of search activity (search_prep, web_search, crawling, etc.)
            content: Human-readable description of the activity
            metadata: Additional data about the search process
        """
        try:
            message = {
                'type': message_type,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Store in internal conversation
            self.internal_conversation.append(message)
            
            # Emit via WebSocket if available
            if self.socketio and self.session_id:
                self.socketio.emit('agent_internal_conversation', {
                    'agent_name': 'websearch_and_crawl_agent',
                    'message': message
                }, room=self.session_id)
                
            print(f"[EnhancedWebSearchCrawlAgent] Internal: {message_type} - {content}")
            
        except Exception as e:
            print(f"[EnhancedWebSearchCrawlAgent] Error emitting internal message: {e}")
    
    def _monitor_search_conversation(self, messages, response):
        """
        Monitor the search conversation and capture key activities.
        
        Args:
            messages: Messages being processed
            response: Agent's response
        """
        try:
            if not response:
                return
                
            # Check for search preparation activities
            if any(keyword in response.lower() for keyword in ['search', 'query', 'looking']):
                self._emit_internal_message(
                    'search_preparation',
                    'Preparing search queries based on user request',
                    {'activity': 'query_formulation'}
                )
            
            # Check for web search execution
            if 'firecrawl_search' in response.lower() or any(keyword in response.lower() for keyword in ['searching', 'crawling']):
                self._emit_internal_message(
                    'web_search_execution', 
                    'Executing web search using Firecrawl tool',
                    {'activity': 'search_execution'}
                )
            
            # Check for content processing
            if any(keyword in response.lower() for keyword in ['found', 'results', 'sources']):
                self._emit_internal_message(
                    'content_processing',
                    'Processing and analyzing search results',
                    {'activity': 'content_analysis'}
                )
            
            # Check for synthesis
            if any(keyword in response.lower() for keyword in ['summary', 'conclusion', 'final']):
                self._emit_internal_message(
                    'final_synthesis',
                    'Synthesizing findings into structured response',
                    {'activity': 'result_synthesis'}
                )
                
        except Exception as e:
            print(f"[EnhancedWebSearchCrawlAgent] Error monitoring search conversation: {e}")
    
    def _capture_search_messages(self, chat_result):
        """
        Capture detailed search messages from the internal chat.
        
        Args:
            chat_result: Result from the internal search conversation
        """
        try:
            if not chat_result or not hasattr(chat_result, 'chat_history'):
                return
                
            # Extract search-specific messages
            for message in chat_result.chat_history:
                if message.get('role') == 'assistant':
                    content = message.get('content', '')
                    
                    # Capture tool calls
                    if 'firecrawl_search' in content:
                        self._emit_internal_message(
                            'tool_execution',
                            'Executing Firecrawl search tool',
                            {'tool': 'firecrawl_search', 'content_preview': content[:100]}
                        )
                    
                    # Capture search queries
                    if any(keyword in content.lower() for keyword in ['searching for', 'query:', 'looking up']):
                        self._emit_internal_message(
                            'search_query',
                            f'Search query: {content[:150]}...',
                            {'query_content': content}
                        )
                        
        except Exception as e:
            print(f"[EnhancedWebSearchCrawlAgent] Error capturing search messages: {e}")
    
    def _reply_user(self, messages=None, sender=None, config=None):
        """
        Enhanced reply method with internal conversation monitoring.
        """
        try:
            # Emit initial activity
            self._emit_internal_message(
                'search_started',
                'Web Search and Crawl Agent activated for information gathering',
                {'status': 'initialized'}
            )
            
            # Get the user question from messages
            if messages:
                user_question = messages[-1]["content"] if isinstance(messages, list) else messages
                self._emit_internal_message(
                    'search_preparation',
                    f'Analyzing user query and preparing search strategy: {user_question[:100]}...',
                    {'query_preview': user_question[:200] if user_question else ''}
                )
            
            # Call parent method to execute the search process
            success, response = super()._reply_user(messages, sender, config)
            
            # Monitor the search process by analyzing the response
            if response:
                self._analyze_search_response(response)
            
            # Emit completion
            self._emit_internal_message(
                'search_completed',
                'Web search and crawl process completed successfully',
                {'status': 'completed', 'response_length': len(response) if response else 0}
            )
            
            return success, response
            
        except Exception as e:
            print(f"[EnhancedWebSearchCrawlAgent] Error in enhanced reply: {e}")
            self._emit_internal_message(
                'search_error',
                f'Error during search process: {str(e)}',
                {'error': str(e)}
            )
            # Fallback to parent method
            return super()._reply_user(messages, sender, config)
    
    def _analyze_search_response(self, response):
        """
        Analyze the search response to identify different stages of the process.
        """
        try:
            if not response:
                return
                
            response_lower = response.lower()
            
            # Check for tool execution patterns
            if 'firecrawl_search' in response_lower or 'tool_calls' in response_lower:
                self._emit_internal_message(
                    'tool_execution',
                    'Executing Firecrawl search tool to gather web information',
                    {'tool': 'firecrawl_search'}
                )
            
            # Check for search query formulation
            if any(keyword in response_lower for keyword in ['searching for', 'query:', 'search query']):
                self._emit_internal_message(
                    'search_query',
                    'Formulating and executing targeted search queries',
                    {'activity': 'query_execution'}
                )
            
            # Check for content processing
            if any(keyword in response_lower for keyword in ['found', 'results', 'retrieved', 'extracted']):
                self._emit_internal_message(
                    'content_processing',
                    'Processing and analyzing retrieved web content',
                    {'activity': 'content_analysis'}
                )
            
            # Check for multiple searches
            if response_lower.count('search') > 2 or 'multiple' in response_lower:
                self._emit_internal_message(
                    'iterative_search',
                    'Conducting multiple searches for comprehensive coverage',
                    {'activity': 'multi_search'}
                )
            
            # Check for synthesis and final processing
            if any(keyword in response_lower for keyword in ['summary', 'conclusion', 'final', 'synthesizing']):
                self._emit_internal_message(
                    'final_synthesis',
                    'Synthesizing search findings into structured response',
                    {'activity': 'result_synthesis'}
                )
                
        except Exception as e:
            print(f"[EnhancedWebSearchCrawlAgent] Error analyzing search response: {e}")
