import uuid
import time
from typing import Dict, Optional

class SessionManager:
    """Manages user sessions and their associated data"""
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
        self.sid_to_session: Dict[str, str] = {}  # Map socket ID to session ID
    
    def create_session(self, session_id: str, socket_id: str) -> dict:
        """Create a new session"""
        session_data = {
            'session_id': session_id,
            'socket_id': socket_id,
            'created_at': time.time(),
            'last_activity': time.time(),
            'messages': [],
            'agent_states': {},
            'conversation_active': False
        }
        
        self.sessions[session_id] = session_data
        self.sid_to_session[socket_id] = session_id
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data by session ID"""
        return self.sessions.get(session_id)
    
    def get_session_by_sid(self, socket_id: str) -> Optional[str]:
        """Get session ID by socket ID"""
        return self.sid_to_session.get(socket_id)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return session_id in self.sessions
    
    def update_session_activity(self, session_id: str):
        """Update last activity timestamp"""
        if session_id in self.sessions:
            self.sessions[session_id]['last_activity'] = time.time()
    
    def add_message(self, session_id: str, message: dict):
        """Add message to session history"""
        if session_id in self.sessions:
            self.sessions[session_id]['messages'].append(message)
            self.update_session_activity(session_id)
    
    def set_conversation_status(self, session_id: str, active: bool):
        """Set conversation active status"""
        if session_id in self.sessions:
            self.sessions[session_id]['conversation_active'] = active
            self.update_session_activity(session_id)
    
    def update_agent_state(self, session_id: str, agent_name: str, state: dict):
        """Update agent state for session"""
        if session_id in self.sessions:
            if 'agent_states' not in self.sessions[session_id]:
                self.sessions[session_id]['agent_states'] = {}
            self.sessions[session_id]['agent_states'][agent_name] = state
            self.update_session_activity(session_id)
    
    def remove_session(self, session_id: str):
        """Remove session and cleanup"""
        if session_id in self.sessions:
            socket_id = self.sessions[session_id].get('socket_id')
            if socket_id and socket_id in self.sid_to_session:
                del self.sid_to_session[socket_id]
            del self.sessions[session_id]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove old inactive sessions"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        sessions_to_remove = []
        for session_id, session_data in self.sessions.items():
            if current_time - session_data['last_activity'] > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.remove_session(session_id)
        
        return len(sessions_to_remove)
    
    def get_active_sessions(self) -> list:
        """Get list of all active sessions"""
        return list(self.sessions.keys())
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self.sessions)
