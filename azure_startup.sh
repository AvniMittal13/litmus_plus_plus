#!/bin/bash
# Azure App Service startup script for SQLite compatibility

# Set environment variables for ChromaDB
export CHROMA_SERVER_HOST="0.0.0.0"
export CHROMA_SERVER_HTTP_PORT=${PORT:-5000}

# Install and configure pysqlite3 if needed
python -c "
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
    print('SQLite3 module replaced with pysqlite3')
except ImportError:
    print('pysqlite3 not available, using system sqlite3')

import sqlite3
print(f'Using SQLite version: {sqlite3.sqlite_version}')
"

# Start the application
python startup.py
