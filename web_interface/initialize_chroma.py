"""
ChromaDB Initialization Script
Initializes the expert knowledge collection for the web interface
"""

import os
import sys
import chromadb
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from chromadb.utils import embedding_functions
from utils.aoai_chat import model_config

load_dotenv()

def initialize_chroma_db():
    """Initialize ChromaDB with expert knowledge collection"""
    try:
        print("Initializing ChromaDB for Expert Knowledge Agent...")
        
        # Create embedding function
        openai_embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING"),
            model_name="text-embedding-ada-002",
            api_base=os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDING"),
            api_type="azure",
            api_version="2023-05-15",
            deployment_id="text-embedding-ada-002"
        )
        
        # Create persistent client
        db_path = "./tmp/db"
        os.makedirs(db_path, exist_ok=True)
        client = chromadb.PersistentClient(path=db_path)
        
        # Get or create collection
        collection_name = "expert_knowledge_new"
        
        try:
            # Try to get existing collection
            collection = client.get_collection(
                name=collection_name,
                embedding_function=openai_embedding_function
            )
            print(f"Found existing collection: {collection_name}")
            print(f"Collection count: {collection.count()}")
            
        except Exception as e:
            print(f"Collection doesn't exist, creating new one: {e}")
            
            # Create new collection
            collection = client.create_collection(
                name=collection_name,
                embedding_function=openai_embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Load and add knowledge documents if collection is empty
            knowledge_file = os.path.join(os.path.dirname(__file__), "..", "knowledge", "knowledge.md")
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split content into chunks
                chunks = content.split('\n\n')  # Simple chunking by paragraphs
                chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
                
                if chunks:
                    print(f"Adding {len(chunks)} chunks to collection...")
                    
                    # Add documents to collection
                    collection.add(
                        documents=chunks,
                        ids=[f"doc_{i}" for i in range(len(chunks))],
                        metadatas=[{"source": "knowledge.md", "chunk_id": i} for i in range(len(chunks))]
                    )
                    
                    print(f"Successfully added {len(chunks)} documents to collection")
                else:
                    print("No content found in knowledge.md")
            else:
                print(f"Knowledge file not found: {knowledge_file}")
        
        print("ChromaDB initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing ChromaDB: {e}")
        return False

if __name__ == "__main__":
    success = initialize_chroma_db()
    if success:
        print("✅ ChromaDB ready for Expert Knowledge Agent")
    else:
        print("❌ Failed to initialize ChromaDB")
        sys.exit(1)
