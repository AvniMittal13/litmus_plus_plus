#!/usr/bin/env python3
"""
Startup script for Azure Web App deployment
This ensures proper module path resolution for the Flask app
"""
import os
import sys
from dotenv import load_dotenv

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
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)
