#!/usr/bin/env python3
"""
Startup script for both local development and Azure App Service deployment
Usage: python startup.py
"""
import os
import sys

# Eventlet monkey-patching MUST happen before any other imports
# Required for production (FLASK_ENV=production) where SocketIO uses eventlet
if os.environ.get('FLASK_ENV') == 'production':
    import eventlet
    eventlet.monkey_patch()

from dotenv import load_dotenv

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configure SQLite for ChromaDB BEFORE any other imports
try:
    from chromadb_config import configure_sqlite_for_chromadb
    configure_sqlite_for_chromadb()
    print("✅ ChromaDB SQLite configuration applied")
except Exception as e:
    print(f"⚠️  ChromaDB SQLite configuration failed: {e}")

# Load environment variables from .env file if it exists
load_dotenv()

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import and run the Flask app
if __name__ == '__main__':
    from web_interface.app import app, socketio
    
    print("Starting Main Agent Web Interface via startup script...")
    # Use Azure's PORT environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    print(f"Application will be accessible on port: {port}")
    
    # Set production configuration
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    # In production with eventlet, don't pass allow_unsafe_werkzeug (eventlet has its own WSGI server)
    # In development with threading mode, allow_unsafe_werkzeug is needed for Werkzeug
    if os.environ.get('FLASK_ENV') == 'production':
        socketio.run(app, debug=False, host='0.0.0.0', port=port, use_reloader=False)
    else:
        socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False, allow_unsafe_werkzeug=True)
