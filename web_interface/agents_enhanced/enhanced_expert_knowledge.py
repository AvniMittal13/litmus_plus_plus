import os
import sys
import threading
import time
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
import shutil

import re
import json
import pprint
import autogen
from autogen.coding import LocalCommandLineCodeExecutor
from autogen import Agent, AssistantAgent, ConversableAgent, UserProxyAgent
from autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent

from autogen import AssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
import chromadb
from chromadb.utils import embedding_functions

# Add parent directory to path to import existing utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.aoai_chat import model_config, get_embedding_function

load_dotenv()

openai_embedding_function = get_embedding_function()


class EnhancedExpertKnowledgeAgent(ConversableAgent):
    """
    Enhanced Expert Knowledge Agent with real-time WebSocket streaming capabilities.
    Inherits the core functionality of Expert_Knowledge_Agent but adds UI integration.
    """
    
    def __init__(self, session_id: str, socketio_instance, n_iters=2, **kwargs):
        """
        Initializes an Enhanced Expert Knowledge Agent instance.

        Parameters:
            - session_id (str): The WebSocket session ID for streaming
            - socketio_instance: SocketIO instance for real-time communication
            - n_iters (int, optional): The number of "improvement" iterations to run. Defaults to 2.
            - **kwargs: keyword arguments for the parent ConversableAgent.
        """
        super().__init__(**kwargs)
        self.session_id = session_id
        self.socketio = socketio_instance
        self.register_reply([Agent, None], reply_func=EnhancedExpertKnowledgeAgent._reply_user, position=0)
        self._n_iters = n_iters
        
        # Internal conversation tracking
        self.internal_conversation = []
        self.conversation_step = 0

    def _emit_internal_message(self, message_type: str, content: str, metadata: dict = None):
        """Emit internal conversation message to UI via WebSocket"""
        try:
            self.socketio.emit('agent_internal_conversation', {
                'agent_name': 'expert_knowledge_agent',
                'type': message_type,
                'content': content,
                'metadata': metadata or {},
                'step': self.conversation_step,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            
            # Store for later reference
            self.internal_conversation.append({
                'type': message_type,
                'content': content,
                'metadata': metadata or {},
                'step': self.conversation_step,
                'timestamp': datetime.now().isoformat()
            })
            
            self.conversation_step += 1
            print(f"[EnhancedExpertKnowledge] Emitted internal message: {message_type}")
            
        except Exception as e:
            print(f"[EnhancedExpertKnowledge] Error emitting internal message: {e}")

    def _create_enhanced_rag_proxy_agent(self, user_question: str):
        """Create RAG proxy agent with enhanced monitoring"""
        # Emit starting message
        self._emit_internal_message(
            "rag_initialization", 
            "Initializing knowledge retrieval system...",
            {"query": user_question}
        )
        
        ragproxyagent = RetrieveUserProxyAgent(
            name="ragproxyagent",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
            retrieve_config={
                "task": "default",
                "docs_path": [
                    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "knowledge_2.md")
                ],
                "custom_text_types": ["mdx"],
                "chunk_token_size": 1000,
                "vector_db": "chroma",
                "collection_name": "expert_knowledge_new2",
                "model": model_config["config_list"][0]["model"],
                "client": chromadb.PersistentClient(path="./tmp/db"),
                "embedding_function": openai_embedding_function,
                "embedding_model": "text-embedding-ada-002",
                "override": True,
                "get_or_create": True,
            },
            code_execution_config=False,
        )
        
        return ragproxyagent

    def _create_enhanced_assistant(self):
        """Create assistant agent with enhanced monitoring"""
        self._emit_internal_message(
            "assistant_initialization",
            "Setting up expert knowledge assistant...",
            {"role": "assistant"}
        )
        
        assistant = AssistantAgent(
            name="assistant",
            system_message="""
You are the Expert Knowledge Agent, providing guidance like an experienced PhD researcher in a multilingual domain.  

- You have access to a large corpus of expert knowledge about steps taken by expert researchers in multilingual nlp contexts. Based on the query and retreived results provide expert knowledge about what should be done next.
- Your results are used for planning an **effective research strategy**.
- Your role is to guide the next steps in a research project, including what data to collect, how to generate features, what features to collect in such a situation, how to structure it, and how to analyze it.
- If relevant expert information on how to proceed further cannot be found, clearly state that.
- Your response will be used to plan the next steps effectively.
- You only tell based on output of `ragproxyagent` which searches and gives you relevent piece of context. Use that as your source of groundtruth.
""",
            llm_config=model_config,
        )
        
        return assistant

    def _monitor_rag_conversation(self, ragproxyagent, assistant, user_question):
        """Monitor and stream the RAG conversation in real-time"""
        try:
            self._emit_internal_message(
                "rag_search_start",
                f"Starting knowledge search for query: '{user_question}'",
                {"query": user_question, "phase": "search_initiation"}
            )
            
            # Hook into the initiate_chat method to capture conversation
            original_initiate_chat = ragproxyagent.initiate_chat
            
            def enhanced_initiate_chat(*args, **kwargs):
                # Emit search start
                self._emit_internal_message(
                    "rag_retrieval_start",
                    "Searching knowledge database for relevant documents...",
                    {"phase": "document_retrieval"}
                )
                
                try:
                    result = original_initiate_chat(*args, **kwargs)
                    
                    # Capture and stream the conversation after it completes
                    self._capture_rag_messages(ragproxyagent, assistant)
                    
                    return result
                    
                except Exception as e:
                    self._emit_internal_message(
                        "rag_error",
                        f"Error during knowledge retrieval: {str(e)}",
                        {"error": str(e), "phase": "error"}
                    )
                    raise
            
            # Replace the method temporarily
            ragproxyagent.initiate_chat = enhanced_initiate_chat
            
            # Execute the enhanced chat
            ragproxyagent.initiate_chat(
                assistant, 
                message=ragproxyagent.message_generator, 
                problem=user_question
            )
            
            # Restore original method
            ragproxyagent.initiate_chat = original_initiate_chat
            
        except Exception as e:
            self._emit_internal_message(
                "monitoring_error",
                f"Error monitoring RAG conversation: {str(e)}",
                {"error": str(e)}
            )

    def _capture_rag_messages(self, ragproxyagent, assistant):
        """Capture and stream messages from the RAG conversation"""
        try:
            # Get messages from the conversation
            if hasattr(ragproxyagent, '_oai_messages') and assistant in ragproxyagent._oai_messages:
                messages = ragproxyagent._oai_messages[assistant]
                
                self._emit_internal_message(
                    "rag_processing",
                    f"Processing {len(messages)} conversation messages...",
                    {"message_count": len(messages), "phase": "message_processing"}
                )
                
                # Stream individual messages
                for i, message in enumerate(messages):
                    if isinstance(message, dict):
                        role = message.get('role', 'unknown')
                        content = message.get('content', '')
                        
                        if role == 'user':
                            self._emit_internal_message(
                                "rag_query",
                                f"RAG Query: {content}",  # Send full content
                                {"role": "user", "full_content": content, "message_index": i}
                            )
                        elif role == 'assistant':
                            self._emit_internal_message(
                                "rag_response",
                                f"RAG Response: {content}",  # Send full content  
                                {"role": "assistant", "full_content": content, "message_index": i}
                            )
                
                # Final processing message
                final_response = messages[-1].get('content', '') if messages else ''
                self._emit_internal_message(
                    "rag_completion",
                    "Knowledge retrieval and processing completed successfully",
                    {"final_response_preview": final_response[:200], "phase": "completion"}
                )
                
        except Exception as e:
            self._emit_internal_message(
                "capture_error",
                f"Error capturing RAG messages: {str(e)}",
                {"error": str(e)}
            )

    def _reply_user(self, messages=None, sender=None, config=None):
        """Enhanced reply method with real-time streaming"""
        print(f"[EnhancedExpertKnowledge] _reply_user called with messages={len(messages) if messages else 0}")
        
        if all((messages is None, sender is None)):
            error_msg = f"Either {messages=} or {sender=} must be provided."
            raise AssertionError(error_msg)
        if messages is None:
            messages = self._oai_messages[sender]

        user_question = messages[-1]["content"]
        print(f"[EnhancedExpertKnowledge] Processing question: {user_question[:100]}...")
        
        try:
            # Reset conversation tracking
            self.internal_conversation = []
            self.conversation_step = 0
            
            # Create enhanced agents
            assistant = self._create_enhanced_assistant()
            ragproxyagent = self._create_enhanced_rag_proxy_agent(user_question)
            
            # Monitor the RAG conversation with streaming
            self._monitor_rag_conversation(ragproxyagent, assistant, user_question)
            
            # Extract final response
            if hasattr(ragproxyagent, '_oai_messages') and assistant in ragproxyagent._oai_messages:
                response = ragproxyagent._oai_messages[assistant][-1]["content"]
                
                self._emit_internal_message(
                    "final_response",
                    "Generated final expert knowledge response",
                    {"response_length": len(response), "phase": "final"}
                )
            else:
                response = "No response generated from knowledge retrieval system."
                self._emit_internal_message(
                    "no_response",
                    "No response generated from knowledge retrieval system",
                    {"phase": "error"}
                )

            return True, response
            
        except Exception as e:
            self._emit_internal_message(
                "agent_error",
                f"Error in expert knowledge processing: {str(e)}",
                {"error": str(e), "phase": "critical_error"}
            )
            
            # Return a fallback response
            return True, f"Error processing expert knowledge request: {str(e)}"
