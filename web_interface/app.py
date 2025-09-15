from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import sys
import os
import uuid
import threading
import json
import time
from datetime import datetime

# Add parent directory to path to import existing agents
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.main_agent_service import MainAgentService
from services.session_manager import SessionManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thought-agent-web-interface-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize services
agent_service = MainAgentService()
session_manager = SessionManager()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    session_id = str(uuid.uuid4())
    join_room(session_id)
    session_manager.create_session(session_id, request.sid)
    
    emit('connected', {
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        'message': 'Connected to Thought Agent Interface'
    })
    
    print(f"[WebSocket] Client connected - Session ID: {session_id}")

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    session_id = session_manager.get_session_by_sid(request.sid)
    if session_id:
        session_manager.remove_session(session_id)
        leave_room(session_id)
        print(f"[WebSocket] Client disconnected - Session ID: {session_id}")

@socketio.on('start_conversation')
def handle_conversation(data):
    """Handle new user query and start MainAgent conversation"""
    try:
        session_id = data.get('session_id')
        user_query = data.get('query', '').strip()
        
        if not user_query:
            emit('error', {'message': 'Query cannot be empty'})
            return
        
        if not session_id or not session_manager.session_exists(session_id):
            emit('error', {'message': 'Invalid session'})
            return
        
        print(f"[Conversation] Starting MainAgent for session {session_id}: {user_query}")
        
        # Emit conversation started
        emit('conversation_started', {
            'session_id': session_id,
            'query': user_query,
            'timestamp': datetime.now().isoformat()
        }, room=session_id)
        
        # Start MainAgent conversation in background thread
        agent_service.start_conversation(session_id, user_query, socketio)
        
    except Exception as e:
        print(f"[Error] Failed to start conversation: {e}")
        emit('error', {'message': f'Failed to start conversation: {str(e)}'})

@socketio.on('join_session')
def handle_join_session(data):
    """Allow client to join specific session"""
    session_id = data.get('session_id')
    if session_id and session_manager.session_exists(session_id):
        join_room(session_id)
        emit('joined_session', {'session_id': session_id})
    else:
        emit('error', {'message': 'Invalid session ID'})

if __name__ == '__main__':
    print("Starting Main Agent Web Interface...")
    # Use Azure's PORT environment variable or default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    print(f"Access the application at: http://localhost:{port}")
    # Set debug=False for production deployment
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)
