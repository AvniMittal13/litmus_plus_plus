# SQLite fix for ChromaDB on Azure (must run before ANY chromadb import)
import sys
import os
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

from flask import Flask, render_template, request, send_from_directory, abort
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import threading
import json
import time
from datetime import datetime

# import eventlet
# eventlet.monkey_patch()

# Add parent directory to path to import existing agents
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from web_interface.services.main_agent_service import MainAgentService
from web_interface.services.session_manager import SessionManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thought-agent-web-interface-key'
# socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

environment = os.getenv("FLASK_ENV", "development")
if environment == "production":
    socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")
else:
    socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Initialize services
agent_service = MainAgentService()
session_manager = SessionManager()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/agent_outputs/<path:filename>')
def serve_agent_output(filename):
    """Serve generated files (images, etc.) from agent_outputs directory"""
    # Resolve agent_outputs relative to project root (one level up from web_interface)
    agent_outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'agent_outputs'))
    # Security: ensure the resolved path stays within agent_outputs
    requested_path = os.path.abspath(os.path.join(agent_outputs_dir, filename))
    if not requested_path.startswith(agent_outputs_dir):
        abort(403)
    return send_from_directory(agent_outputs_dir, filename)

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

#         user_query = f"""
#         Run the following Question without asking any clarifications. Assume answers/responses to the questions and continue
# Use coder agent to generate code for performing predictive analysis by training intelligent regressors wherever required.

# Question: {user_query}
# """
        
        
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

@socketio.on('end_conversation')
def handle_end_conversation(data):
    """Handle conversation end (clear chat)"""
    try:
        session_id = data.get('session_id')
        
        if not session_id or not session_manager.session_exists(session_id):
            emit('error', {'message': 'Invalid session'})
            return
        
        print(f"[WebSocket] Ending conversation for session {session_id}")
        
        # End conversation via agent service
        success = agent_service.end_conversation(session_id, socketio)
        
        if success:
            print(f"[WebSocket] Successfully ended conversation for session {session_id}")
        else:
            print(f"[WebSocket] No active conversation found for session {session_id}")
            # Still emit ended event for frontend cleanup
            emit('conversation_ended', {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
        
    except Exception as e:
        print(f"[Error] Failed to end conversation: {e}")
        emit('error', {'message': f'Failed to end conversation: {str(e)}'})

if __name__ == '__main__':
    print("Starting Main Agent Web Interface...")
    # Use Azure's PORT environment variable or default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    print(f"Access the application at: http://localhost:{port}")
    # Set debug=False for production deployment
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    # For production Azure deployment, allow unsafe werkzeug
    if os.environ.get('FLASK_ENV') == 'production':
        socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False, allow_unsafe_werkzeug=True)
    else:
        socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)
