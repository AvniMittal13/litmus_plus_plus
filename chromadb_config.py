"""
ChromaDB SQLite compatibility configuration for Azure deployment
"""
import sys
import os

def configure_sqlite_for_chromadb():
    """Configure SQLite for ChromaDB compatibility on Azure"""
    try:
        # Try to use pysqlite3-binary if available
        import pysqlite3
        
        # Replace the default sqlite3 module with pysqlite3
        sys.modules['sqlite3'] = pysqlite3
        print("✅ SQLite3 module replaced with pysqlite3-binary for ChromaDB compatibility")
        
        # Verify the version
        import sqlite3
        print(f"✅ Using SQLite version: {sqlite3.sqlite_version}")
        
        return True
    except ImportError:
        print("⚠️  pysqlite3-binary not available, using system sqlite3")
        try:
            import sqlite3
            version_parts = [int(x) for x in sqlite3.sqlite_version.split('.')]
            required_version = [3, 35, 0]
            
            if version_parts >= required_version:
                print(f"✅ System SQLite version {sqlite3.sqlite_version} is compatible")
                return True
            else:
                print(f"❌ System SQLite version {sqlite3.sqlite_version} is too old (requires >= 3.35.0)")
                return False
        except Exception as e:
            print(f"❌ Error checking SQLite version: {e}")
            return False

def get_chromadb_client(db_path="./tmp/db"):
    """Get ChromaDB client with proper SQLite configuration"""
    
    # Ensure SQLite is properly configured
    if not configure_sqlite_for_chromadb():
        raise RuntimeError("SQLite version is incompatible with ChromaDB")
    
    # Import ChromaDB after SQLite configuration
    import chromadb
    
    # Ensure the database directory exists
    os.makedirs(db_path, exist_ok=True)
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        print(f"✅ ChromaDB client initialized successfully at {db_path}")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize ChromaDB client: {e}")
        raise

# Configure SQLite when this module is imported
configure_sqlite_for_chromadb()
