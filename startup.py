#!/usr/bin/env python3
"""
Startup script for local development and testing
For Azure App Service deployment, use app.py with gunicorn instead
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
    
    # Run the app (debug=False in production enables threaded mode for concurrent requests)
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)
