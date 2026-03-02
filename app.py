#!/usr/bin/env python3
"""
WSGI entry point for Azure App Service deployment with gunicorn
This file provides the 'app' object that gunicorn expects
"""
import os
import sys
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

# Import the Flask app and SocketIO instance
from web_interface.app import app, socketio

# This is what gunicorn will look for
if __name__ == "__main__":
    # This won't be called when using gunicorn, but useful for local testing
    port = int(os.environ.get('PORT', 8000))

    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    # For production Azure deployment, allow unsafe werkzeug
    if os.environ.get('FLASK_ENV') == 'production':
        socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False, allow_unsafe_werkzeug=True)
    else:
        socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)

