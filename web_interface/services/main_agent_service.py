"""
Main Agent Service for Web Interface
Handles MainAgent orchestration with WebSocket streaming
"""

import threading
import uuid
import time
from datetime import datetime
import sys
import os

# Add parent directory to import enhanced agents
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from web_interface.agents_enhanced.enhanced_main_agent import EnhancedMainAgent
from web_interface.services.session_manager import SessionManager

class MainAgentService:
    """Service for managing MainAgent conversations with WebSocket support"""
    
    def __init__(self):
        self.active_conversations = {}
        self.session_manager = SessionManager()
        
    def start_conversation(self, session_id, user_query, socketio):
        """Start a new MainAgent conversation"""
        if session_id in self.active_conversations:
            print(f"[MainAgentService] Conversation already active for session {session_id}")
            return
        
        # Create conversation thread
        thread = threading.Thread(
            target=self._run_conversation,
            args=(session_id, user_query, socketio),
            daemon=True
        )
        
        # Store conversation info
        self.active_conversations[session_id] = {
            'thread': thread,
            'start_time': datetime.now(),
            'user_query': user_query,
            'status': 'starting'
        }
        
        # Start conversation
        thread.start()
        print(f"[MainAgentService] Started conversation thread for session {session_id}")
    
    def _run_conversation(self, session_id, user_query, socketio):
        """Run MainAgent conversation in background thread"""
        try:
            # Update conversation status
            if session_id in self.active_conversations:
                self.active_conversations[session_id]['status'] = 'running'
            
            # Emit main agent started event
            socketio.emit('main_agent_started', {
                'session_id': session_id,
                'user_query': user_query,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            print(f"[MainAgentService] Running MainAgent for query: {user_query}")
            
            # Create and run EnhancedMainAgent
            main_agent = EnhancedMainAgent(
                session_id=session_id,
                socketio_instance=socketio
            )
            
            # Run with orchestration (proper MainAgent workflow)
            response = main_agent.run(user_query)
            
            # Emit final response for main chat
            socketio.emit('conversation_completed', {
                'session_id': session_id,
                'final_response': response,  # Changed from 'response' to 'final_response'
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            print(f"[MainAgentService] Completed conversation for session {session_id}")
            
        except Exception as e:
            print(f"[MainAgentService] Error in conversation {session_id}: {e}")
            
            # Emit error event
            socketio.emit('conversation_error', {
                'session_id': session_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
        finally:
            # Clean up conversation
            if session_id in self.active_conversations:
                self.active_conversations[session_id]['status'] = 'completed'
                # Remove after a delay to allow for final events
                threading.Timer(30.0, lambda: self._cleanup_conversation(session_id)).start()
    
    def _cleanup_conversation(self, session_id):
        """Clean up completed conversation"""
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
            print(f"[MainAgentService] Cleaned up conversation for session {session_id}")
    
    def get_conversation_status(self, session_id):
        """Get status of conversation"""
        if session_id in self.active_conversations:
            conv = self.active_conversations[session_id]
            return {
                'status': conv['status'],
                'start_time': conv['start_time'].isoformat(),
                'user_query': conv['user_query']
            }
        return None
    
    def stop_conversation(self, session_id):
        """Stop an active conversation"""
        if session_id in self.active_conversations:
            conv = self.active_conversations[session_id]
            if conv['status'] == 'running':
                # Note: Graceful stopping would need to be implemented in the agent
                conv['status'] = 'stopped'
                print(f"[MainAgentService] Marked conversation {session_id} for stopping")
                return True
        return False
    
    def list_active_conversations(self):
        """List all active conversations"""
        return {
            sid: {
                'status': conv['status'],
                'start_time': conv['start_time'].isoformat(),
                'user_query': conv['user_query']
            }
            for sid, conv in self.active_conversations.items()
        }
