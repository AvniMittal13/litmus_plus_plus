"""
Enhanced Main Agent - Simplified Delegation Pattern
Delegates to EnhancedThoughtAgent for proven functionality
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class EnhancedMainAgent:
    """
    Simplified MainAgent that delegates to proven EnhancedThoughtAgent.
    This ensures immediate functionality while maintaining future extensibility.
    """
    
    def __init__(self, session_id: str, socketio_instance):
        self.session_id = session_id
        self.socketio = socketio_instance
        print(f"[EnhancedMainAgent] Initialized for session: {session_id}")
    
    def run(self, user_query):
        """Public interface for running queries"""
        try:
            return self._run_with_streaming(user_query)
        except Exception as e:
            print(f"[EnhancedMainAgent] Error running query: {e}")
            self.socketio.emit('conversation_error', {
                'error': str(e),
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            raise
    
    def _run_with_streaming(self, user_query):
        """
        Simplified streaming implementation using delegation to EnhancedThoughtAgent.
        This ensures we reuse the proven working functionality.
        """
        try:
            print(f"[EnhancedMainAgent] Starting delegation to EnhancedThoughtAgent for: {user_query}")
            
            # Import EnhancedThoughtAgent (proven working component)
            from web_interface.services.agent_service import EnhancedThoughtAgent
            
            # Create basic agent metadata (from backup working version)
            agent_metadata = {
                'user_proxy_agent': {'color': '#007bff', 'display_name': 'User Proxy'},
                'research_planner_agent': {'color': '#28a745', 'display_name': 'Research Planner'},
                'expert_knowledge_agent': {'color': '#6f42c1', 'display_name': 'Expert Knowledge'},
                'websearch_and_crawl_agent': {'color': '#fd7e14', 'display_name': 'Web Search & Crawl'},
                'coder_agent': {'color': '#dc3545', 'display_name': 'Coder'},
                'code_executor_agent': {'color': '#17a2b8', 'display_name': 'Code Executor'},
                'send_user_msg_agent': {'color': '#6c757d', 'display_name': 'Response Formatter'}
            }
            
            # Create EnhancedThoughtAgent (the proven working component)
            thought_agent = EnhancedThoughtAgent(
                session_id=self.session_id,
                socketio_instance=self.socketio,
                agent_metadata=agent_metadata
            )
            
            print(f"[EnhancedMainAgent] Created EnhancedThoughtAgent, running query...")
            
            # Delegate to the proven working component
            response = thought_agent.run(user_query)
            
            print(f"[EnhancedMainAgent] Completed delegation, received response")
            return response
            
        except Exception as e:
            print(f"[EnhancedMainAgent] Error in delegation: {e}")
            import traceback
            print(f"[EnhancedMainAgent] Traceback: {traceback.format_exc()}")
            
            # Emit error with details
            self.socketio.emit('conversation_error', {
                'error': f'MainAgent delegation failed: {str(e)}',
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            
            # Return simple error response
            return f"I apologize, but I encountered an error processing your request: {str(e)}"
