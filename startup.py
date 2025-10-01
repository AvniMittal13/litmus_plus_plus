#!/usr/bin/env python3
"""
Startup script for Azure App Service and local development
This script handles both Azure production deployment and local testing
"""
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# For Azure App Service, the working directory is /home/site/wwwroot
if os.path.exists('/home/site/wwwroot'):
    os.chdir('/home/site/wwwroot')
    sys.path.insert(0, '/home/site/wwwroot')

# Configure SQLite for ChromaDB BEFORE any other imports
try:
    from chromadb_config import configure_sqlite_for_chromadb
    configure_sqlite_for_chromadb()
    print("✅ ChromaDB SQLite configuration applied")
except Exception as e:
    print(f"⚠️  ChromaDB SQLite configuration failed: {e}")

# Load environment variables from .env file if it exists
load_dotenv()

# Import and run the Flask app
if __name__ == '__main__':
    # Check if we're in Azure App Service environment
    is_azure = os.environ.get('WEBSITE_SITE_NAME') is not None
    
    if is_azure:
        print("Starting in Azure App Service environment...")
        # In Azure, we should use Gunicorn instead of the development server
        # But if startup.py is called directly, we'll start with allow_unsafe_werkzeug
        from web_interface.app import app, socketio
        port = int(os.environ.get('PORT', 8000))
        print(f"Azure App Service - Application will be accessible on port: {port}")
        socketio.run(app, debug=False, host='0.0.0.0', port=port, use_reloader=False, allow_unsafe_werkzeug=True)
    else:
        print("Starting in local development environment...")
        from web_interface.app import app, socketio
        port = int(os.environ.get('PORT', 5000))
        print(f"Local development - Application will be accessible on port: {port}")
        debug_mode = os.environ.get('FLASK_ENV') != 'production'
        socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)
