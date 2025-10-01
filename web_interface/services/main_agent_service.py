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
        """Start a new MainAgent conversation or continue existing one"""
        # Check if conversation already exists and is ready for continuation
        if session_id in self.active_conversations:
            conv = self.active_conversations[session_id]
            if conv['status'] == 'ready_for_continuation':
                print(f"[MainAgentService] Continuing existing conversation for session {session_id}")
                return self._continue_conversation(session_id, user_query, socketio)
            elif conv['status'] in ['starting', 'running']:
                print(f"[MainAgentService] Conversation already active for session {session_id}")
                return
        
        # Create new conversation thread
        thread = threading.Thread(
            target=self._run_conversation,
            args=(session_id, user_query, socketio, True),  # True = new conversation
            daemon=True
        )
        
        # Store conversation info
        self.active_conversations[session_id] = {
            'thread': thread,
            'start_time': datetime.now(),
            'user_query': user_query,
            'status': 'starting',
            'main_agent': None,  # Will store persistent agent
            'message_count': 0
        }
        
        # Start conversation
        thread.start()
        print(f"[MainAgentService] Started conversation thread for session {session_id}")
    
    def _run_conversation(self, session_id, user_query, socketio, is_new_conversation=True):
        """Run MainAgent conversation in background thread"""
        try:
            # Update conversation status
            if session_id in self.active_conversations:
                self.active_conversations[session_id]['status'] = 'running'
                self.active_conversations[session_id]['message_count'] += 1
            
            # Emit main agent started event
            socketio.emit('main_agent_started', {
                'session_id': session_id,
                'user_query': user_query,
                'is_continuation': not is_new_conversation,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            print(f"[MainAgentService] Running MainAgent for query: {user_query}")
            
            # Get or create EnhancedMainAgent
            if is_new_conversation or 'main_agent' not in self.active_conversations[session_id] or self.active_conversations[session_id]['main_agent'] is None:
                # Create new agent
                main_agent = EnhancedMainAgent(
                    session_id=session_id,
                    socketio_instance=socketio
                )
                self.active_conversations[session_id]['main_agent'] = main_agent
                print(f"[MainAgentService] Created new MainAgent for session {session_id}")
            else:
                # Reuse existing agent
                main_agent = self.active_conversations[session_id]['main_agent']
                print(f"[MainAgentService] Reusing existing MainAgent for session {session_id}")
            
            # Run with orchestration (proper MainAgent workflow)
            response = main_agent.run(user_query)
            
            # Emit response completed (not conversation completed)
            socketio.emit('response_completed', {
                'session_id': session_id,
                'final_response': response,
                'message_count': self.active_conversations[session_id]['message_count'],
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            print(f"[MainAgentService] Completed response for session {session_id}")
            
        except Exception as e:
            print(f"[MainAgentService] Error in conversation {session_id}: {e}")
            
            # Emit error event
            socketio.emit('conversation_error', {
                'session_id': session_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
        finally:
            # Mark as ready for continuation instead of completed
            if session_id in self.active_conversations:
                self.active_conversations[session_id]['status'] = 'ready_for_continuation'
                # Don't cleanup - keep agent alive for continuation
    
    def _continue_conversation(self, session_id, user_query, socketio):
        """Continue existing conversation with new query"""
        thread = threading.Thread(
            target=self._run_conversation,
            args=(session_id, user_query, socketio, False),  # False = continuation
            daemon=True
        )
        
        # Update conversation info
        self.active_conversations[session_id]['thread'] = thread
        self.active_conversations[session_id]['user_query'] = user_query
        
        # Start continuation
        thread.start()
        print(f"[MainAgentService] Continued conversation thread for session {session_id}")
    
    def end_conversation(self, session_id, socketio):
        """Explicitly end conversation and cleanup"""
        if session_id in self.active_conversations:
            print(f"[MainAgentService] Ending conversation for session {session_id}")
            
            # Emit conversation ended event
            socketio.emit('conversation_ended', {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            # Cleanup immediately
            self._cleanup_conversation(session_id)
            return True
        return False
    
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
