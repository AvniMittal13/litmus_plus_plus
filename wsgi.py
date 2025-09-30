#!/usr/bin/env python3
"""
WSGI entry point for Azure App Service production deployment
This file is used by Gunicorn to serve the Flask-SocketIO application
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

# Load environment variables
load_dotenv()

# Import the Flask app and SocketIO instance
from web_interface.app import app, socketio

# This is what Gunicorn will use
application = socketio

if __name__ == "__main__":
    # This won't be called in production, but useful for testing
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)