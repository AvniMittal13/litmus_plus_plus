import sys
import os
import threading
import time
import json
import chromadb
from datetime import datetime
from typing import Optional, Dict, Any

# Add parent directory to path to import existing agents
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.thought_agent import ThoughtAgent
from agents.groupchat import GroupChat
from agents.agent import Agent

class ThoughtAgentService:
    """Service to integrate ThoughtAgent with web interface"""
    
    def __init__(self):
        self.active_conversations: Dict[str, dict] = {}
        self.agent_metadata = {
            'user_proxy_agent': {'color': '#007bff', 'display_name': 'User Proxy'},
            'research_planner_agent': {'color': '#28a745', 'display_name': 'Research Planner'},
            'expert_knowledge_agent': {'color': '#6f42c1', 'display_name': 'Expert Knowledge'},
            'websearch_and_crawl_agent': {'color': '#fd7e14', 'display_name': 'Web Search & Crawl'},
            'coder_agent': {'color': '#dc3545', 'display_name': 'Coder'},
            'code_executor_agent': {'color': '#17a2b8', 'display_name': 'Code Executor'},
            'send_user_msg_agent': {'color': '#6c757d', 'display_name': 'Response Formatter'}
        }
    
    def start_conversation(self, session_id: str, user_query: str, socketio_instance):
        """Start a new conversation with ThoughtAgent"""
        try:
            # Ensure ChromaDB is initialized
            self._ensure_chroma_db()
            
            # Extract thought agent ID from session_id for proper ThoughtAgent context
            thought_agent_id = None
            if '_thought_' in session_id:
                thought_agent_id = session_id.split('_thought_')[1]
                print(f"[AgentService] Backup - Extracted thought_agent_id: '{thought_agent_id}' from session: {session_id}")

            # Create enhanced ThoughtAgent with SocketIO integration
            agent = EnhancedThoughtAgent(
                session_id, 
                socketio_instance, 
                self.agent_metadata,
                parent_context='main_agent',
                thought_agent_id=thought_agent_id,
                parent_event_forwarder=None
            )
            
            # Store conversation info
            self.active_conversations[session_id] = {
                'agent': agent,
                'start_time': datetime.now(),
                'user_query': user_query,
                'status': 'running'
            }
            
            # Run conversation in background thread
            thread = threading.Thread(
                target=self._run_conversation,
                args=(session_id, agent, user_query, socketio_instance),
                daemon=True
            )
            thread.start()
            
            return thread
            
        except Exception as e:
            print(f"[AgentService] Error starting conversation: {e}")
            socketio_instance.emit('error', {
                'message': f'Failed to start conversation: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
    
    def _ensure_chroma_db(self):
        """Ensure ChromaDB collection exists for Expert Knowledge Agent"""
        try:
            from chromadb.utils import embedding_functions
            
            # Create embedding function
            openai_embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key="55qo1Eche8zYBdz8K15tLd5plNAslD5Yf9eLzqcTsR5hiuCHOkBSJQQJ99BCACHYHv6XJ3w3AAABACOGrHgz",
                model_name="text-embedding-ada-002",
                api_base="https://swarm-ws-openai-5.openai.azure.com",
                api_type="azure",
                api_version="2023-05-15",
                deployment_id="text-embedding-ada-002"
            )
            
            # Create persistent client - Use same path as original expert_knowledge_agent
            db_path = os.path.join(os.path.dirname(__file__), "..", "..", "tmp", "db")
            db_path = os.path.abspath(db_path)  # Convert to absolute path
            os.makedirs(db_path, exist_ok=True)
            client = chromadb.PersistentClient(path=db_path)
            
            print(f"[AgentService] Using ChromaDB path: {db_path}")
            
            collection_name = "expert_knowledge_new"
            
            try:
                # Try to get existing collection
                collection = client.get_collection(
                    name=collection_name,
                    embedding_function=openai_embedding_function
                )
                print(f"[AgentService] Found existing ChromaDB collection: {collection_name} (count: {collection.count()})")
                
            except Exception:
                print(f"[AgentService] Creating new ChromaDB collection: {collection_name}")
                
                # Create new collection
                collection = client.create_collection(
                    name=collection_name,
                    embedding_function=openai_embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
                
                # Load knowledge documents
                knowledge_file = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "knowledge.md")
                if os.path.exists(knowledge_file):
                    with open(knowledge_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Split content into chunks
                    chunks = content.split('\n\n')
                    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
                    
                    if chunks:
                        collection.add(
                            documents=chunks,
                            ids=[f"doc_{i}" for i in range(len(chunks))],
                            metadatas=[{"source": "knowledge.md", "chunk_id": i} for i in range(len(chunks))]
                        )
                        print(f"[AgentService] Added {len(chunks)} documents to ChromaDB collection")
                
        except Exception as e:
            print(f"[AgentService] Warning: Could not initialize ChromaDB: {e}")
            # Continue anyway - the conversation might still work without expert knowledge
    
    def _run_conversation(self, session_id: str, agent: 'EnhancedThoughtAgent', 
                         user_query: str, socketio_instance):
        """Run the actual conversation"""
        try:
            print(f"[AgentService] Starting conversation for session {session_id}")
            
            # Start the conversation
            final_response = agent.run(user_query)
            
            # Update conversation status
            if session_id in self.active_conversations:
                self.active_conversations[session_id]['status'] = 'completed'
                self.active_conversations[session_id]['final_response'] = final_response
                self.active_conversations[session_id]['end_time'] = datetime.now()
            
            # Emit final response
            socketio_instance.emit('conversation_completed', {
                'session_id': session_id,
                'final_response': final_response,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
            
            print(f"[AgentService] Conversation completed for session {session_id}")
            
        except Exception as e:
            print(f"[AgentService] Error in conversation: {e}")
            
            # Update conversation status
            if session_id in self.active_conversations:
                self.active_conversations[session_id]['status'] = 'error'
                self.active_conversations[session_id]['error'] = str(e)
            
            socketio_instance.emit('conversation_error', {
                'session_id': session_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
    
    def get_conversation_status(self, session_id: str) -> Optional[dict]:
        """Get conversation status"""
        return self.active_conversations.get(session_id)
    
    def stop_conversation(self, session_id: str):
        """Stop active conversation"""
        if session_id in self.active_conversations:
            self.active_conversations[session_id]['status'] = 'stopped'
            # Note: We can't easily stop the thread, but we mark it as stopped


class EnhancedThoughtAgent(ThoughtAgent):
    """ThoughtAgent enhanced with real-time web interface integration"""
    
    def __init__(self, session_id: str, socketio_instance, agent_metadata: dict):
        super().__init__()
        self.session_id = session_id
        self.socketio = socketio_instance
        self.agent_metadata = agent_metadata
        self.current_agent = None
        self.message_count = 0
        self._monitoring_active = False
        self.last_streamed_count = 0
        
        # Enhance the groupchat to emit real-time updates
        self._enhance_groupchat()
        
        # Hook into custom agents after groupchat is set up
        self._hook_custom_agents()
    
    def _enhance_groupchat(self):
        """Add real-time messaging to the groupchat and hook into custom agent internals"""
        original_continue = self.groupchat.continue_groupchat
        
        def enhanced_continue_groupchat(starting_msg):
            """Enhanced continue_groupchat with real-time message streaming"""
            try:
                self.socketio.emit('agent_conversation_started', {
                    'session_id': self.session_id,
                    'starting_message': starting_msg,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                
                # Hook into the autogen GroupChatManager to monitor messages
                groupchat_manager = self.groupchat.groupchat_manager
                
                # Store original message count to track new messages
                self.last_streamed_count = len(groupchat_manager.groupchat.messages)
                
                # Start monitoring in a separate thread for real-time updates
                self._monitoring_active = True
                monitor_thread = threading.Thread(
                    target=self._monitor_messages_real_time,
                    args=(groupchat_manager,),
                    daemon=True
                )
                monitor_thread.start()
                
                try:
                    # Run the original continue_groupchat method
                    messages, summary = original_continue(starting_msg)
                finally:
                    # Stop monitoring
                    self._monitoring_active = False
                
                # Final message sync - ensure all messages are streamed
                final_count = len(messages)
                if final_count > self.last_streamed_count:
                    for i in range(self.last_streamed_count, final_count):
                        if i < len(messages):
                            self._stream_single_message(messages[i], i)
                
                return messages, summary
                
            except Exception as e:
                print(f"[EnhancedThoughtAgent] Error in enhanced continue_groupchat: {e}")
                self._monitoring_active = False
                raise
        
        # Replace the continue_groupchat method
        self.groupchat.continue_groupchat = enhanced_continue_groupchat
    
    def _hook_custom_agents(self):
        """Hook into custom agents to capture their internal conversations"""
        try:
            print("[EnhancedThoughtAgent] Attempting to hook custom agents...")
            
            # Hook into Expert Knowledge Agent - access via self since we extend ThoughtAgent
            if hasattr(self, 'expert_knowledge_agent'):
                expert_agent = self.expert_knowledge_agent
                if hasattr(expert_agent, 'agent'):
                    self._hook_expert_knowledge_agent(expert_agent.agent)
                    print("[EnhancedThoughtAgent] Hooked Expert Knowledge Agent")
                else:
                    print("[EnhancedThoughtAgent] Expert Knowledge Agent has no 'agent' attribute")
            else:
                print("[EnhancedThoughtAgent] No expert_knowledge_agent found on self")
            
            # Hook into WebSearch and Crawl Agent - access via self since we extend ThoughtAgent  
            if hasattr(self, 'websearch_and_crawl_agent'):
                websearch_agent = self.websearch_and_crawl_agent
                if hasattr(websearch_agent, 'agent'):
                    self._hook_websearch_agent(websearch_agent.agent)
                    print("[EnhancedThoughtAgent] Hooked WebSearch and Crawl Agent")
                else:
                    print("[EnhancedThoughtAgent] WebSearch Agent has no 'agent' attribute")
            else:
                print("[EnhancedThoughtAgent] No websearch_and_crawl_agent found on self")
                
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error hooking custom agents: {e}")
            import traceback
            traceback.print_exc()
    
    def _hook_expert_knowledge_agent(self, agent):
        """Hook into the Expert Knowledge Agent's internal RAG conversation"""
        try:
            # Hook the generate_reply method which is what gets called by AutoGen
            if hasattr(agent, 'generate_reply'):
                original_generate_reply = agent.generate_reply
                
                def enhanced_generate_reply(messages=None, sender=None, config=None):
                    # Always emit that expert knowledge agent is processing
                    self.socketio.emit('agent_internal_conversation', {
                        'session_id': self.session_id,
                        'agent_name': 'expert_knowledge_agent',
                        'type': 'internal_start',
                        'content': 'Expert Knowledge Agent activated - searching knowledge base...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    
                    # Emit RAG process step
                    self.socketio.emit('agent_internal_conversation', {
                        'session_id': self.session_id,
                        'agent_name': 'expert_knowledge_agent',
                        'type': 'internal_message',
                        'internal_agent': 'RAG System',
                        'content': 'Using ChromaDB to find semantically similar knowledge from knowledge base...',
                        'role': 'system',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    
                    # Call the original method
                    try:
                        result = original_generate_reply(messages, sender, config)
                        
                        # Emit successful processing
                        self.socketio.emit('agent_internal_conversation', {
                            'session_id': self.session_id,
                            'agent_name': 'expert_knowledge_agent',
                            'type': 'internal_message',
                            'internal_agent': 'Knowledge Analyzer',
                            'content': 'Successfully retrieved relevant knowledge and generated response based on internal expertise.',
                            'role': 'assistant',
                            'timestamp': datetime.now().isoformat()
                        }, room=self.session_id)
                        
                        return result
                        
                    except Exception as e:
                        self.socketio.emit('agent_internal_conversation', {
                            'session_id': self.session_id,
                            'agent_name': 'expert_knowledge_agent',
                            'type': 'internal_error',
                            'content': f'Error in RAG processing: {str(e)}',
                            'timestamp': datetime.now().isoformat()
                        }, room=self.session_id)
                        raise
                
                agent.generate_reply = enhanced_generate_reply
                print("[EnhancedThoughtAgent] Successfully hooked Expert Knowledge Agent generate_reply")
            else:
                print("[EnhancedThoughtAgent] Expert Knowledge Agent has no generate_reply method")
                
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error hooking Expert Knowledge Agent: {e}")
            import traceback
            traceback.print_exc()
    
    def _hook_websearch_agent(self, agent):
        """Hook into the WebSearch Agent's internal conversation and tool calls"""
        try:
            # Hook the generate_reply method which is what gets called by AutoGen
            if hasattr(agent, 'generate_reply'):
                original_generate_reply = agent.generate_reply
                
                def enhanced_generate_reply(messages=None, sender=None, config=None):
                    # Always emit that websearch agent is processing
                    self.socketio.emit('agent_internal_conversation', {
                        'session_id': self.session_id,
                        'agent_name': 'websearch_and_crawl_agent',
                        'type': 'internal_start',
                        'content': 'WebSearch & Crawl Agent activated - planning search strategy...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    
                    # Emit tool preparation step
                    self.socketio.emit('agent_internal_conversation', {
                        'session_id': self.session_id,
                        'agent_name': 'websearch_and_crawl_agent',
                        'type': 'internal_message',
                        'internal_agent': 'Search Planner',
                        'content': 'Analyzing query to identify optimal search terms and determining Firecrawl search strategy...',
                        'role': 'system',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    
                    # Call the original method
                    try:
                        result = original_generate_reply(messages, sender, config)
                        
                        # Check if the result indicates tool usage or search attempts
                        result_str = str(result) if result else ""
                        
                        if 'tool_calls' in result_str.lower() or 'search' in result_str.lower():
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'tool_call',
                                'internal_agent': 'Firecrawl Search',
                                'content': 'Executing web search using Firecrawl API with optimized search parameters...',
                                'role': 'system',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        
                        if 'payment required' in result_str.lower() or 'insufficient credits' in result_str.lower():
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'internal_error',
                                'content': 'Search operation failed: Insufficient Firecrawl API credits. Please check your API quota.',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        else:
                            # Emit successful processing
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'internal_message',
                                'internal_agent': 'Search Results Processor',
                                'content': 'Search operation completed. Analyzing and formatting results for optimal response.',
                                'role': 'assistant',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        
                        return result
                        
                    except Exception as e:
                        error_msg = str(e)
                        if 'payment required' in error_msg.lower() or 'credits' in error_msg.lower():
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'internal_error',
                                'content': f'Web search failed due to API limitations: {error_msg}',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        else:
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'internal_error',
                                'content': f'Error in web search processing: {error_msg}',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        raise
                
                agent.generate_reply = enhanced_generate_reply
                print("[EnhancedThoughtAgent] Successfully hooked WebSearch Agent generate_reply")
            else:
                print("[EnhancedThoughtAgent] WebSearch Agent has no generate_reply method")
                
    def _hook_websearch_agent(self, agent):
        """Hook into the WebSearch Agent's internal conversation and tool calls"""
        try:
            # Hook the generate_reply method which is what gets called by AutoGen
            if hasattr(agent, 'generate_reply'):
                original_generate_reply = agent.generate_reply
                
                def enhanced_generate_reply(messages=None, sender=None, config=None):
                    # Always emit that websearch agent is processing
                    self.socketio.emit('agent_internal_conversation', {
                        'session_id': self.session_id,
                        'agent_name': 'websearch_and_crawl_agent',
                        'type': 'internal_start',
                        'content': 'WebSearch & Crawl Agent activated - planning search strategy...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    
                    # Emit tool preparation step
                    self.socketio.emit('agent_internal_conversation', {
                        'session_id': self.session_id,
                        'agent_name': 'websearch_and_crawl_agent',
                        'type': 'internal_message',
                        'internal_agent': 'Search Planner',
                        'content': 'Analyzing query to identify optimal search terms and determining Firecrawl search strategy...',
                        'role': 'system',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    
                    # Call the original method
                    try:
                        result = original_generate_reply(messages, sender, config)
                        
                        # Check if the result indicates tool usage or search attempts
                        result_str = str(result) if result else ""
                        
                        if 'tool_calls' in result_str.lower() or 'search' in result_str.lower():
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'tool_call',
                                'internal_agent': 'Firecrawl Search',
                                'content': 'Executing web search using Firecrawl API with optimized search parameters...',
                                'role': 'system',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        
                        if 'payment required' in result_str.lower() or 'insufficient credits' in result_str.lower():
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'internal_error',
                                'content': 'Search operation failed: Insufficient Firecrawl API credits. Please check your API quota.',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        else:
                            # Emit successful processing
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'internal_message',
                                'internal_agent': 'Search Results Processor',
                                'content': 'Search operation completed. Analyzing and formatting results for optimal response.',
                                'role': 'assistant',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        
                        return result
                        
                    except Exception as e:
                        error_msg = str(e)
                        if 'payment required' in error_msg.lower() or 'credits' in error_msg.lower():
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'internal_error',
                                'content': f'Web search failed due to API limitations: {error_msg}',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        else:
                            self.socketio.emit('agent_internal_conversation', {
                                'session_id': self.session_id,
                                'agent_name': 'websearch_and_crawl_agent',
                                'type': 'internal_error',
                                'content': f'Error in web search processing: {error_msg}',
                                'timestamp': datetime.now().isoformat()
                            }, room=self.session_id)
                        raise
                
                agent.generate_reply = enhanced_generate_reply
                print("[EnhancedThoughtAgent] Successfully hooked WebSearch Agent generate_reply")
            else:
                print("[EnhancedThoughtAgent] WebSearch Agent has no generate_reply method")
                
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error hooking WebSearch Agent: {e}")
            import traceback
            traceback.print_exc()
        #                             # Detect tool calls
        #                             content = msg.get('content', '')
        #                             if 'tool_calls' in msg or 'firecrawl_search' in content:
        #                                 self.socketio.emit('agent_internal_conversation', {
        #                                     'session_id': self.session_id,
        #                                     'agent_name': 'websearch_and_crawl_agent',
        #                                     'type': 'tool_call',
        #                                     'internal_agent': internal_agent_name,
        #                                     'content': content,
        #                                     'tool_calls': msg.get('tool_calls', []),
        #                                     'message_id': f"internal_{msg_idx}",
        #                                     'timestamp': datetime.now().isoformat()
        #                                 }, room=self.session_id)
        #                             else:
        #                                 self.socketio.emit('agent_internal_conversation', {
        #                                     'session_id': self.session_id,
        #                                     'agent_name': 'websearch_and_crawl_agent',
        #                                     'type': 'internal_message',
        #                                     'internal_agent': internal_agent_name,
        #                                     'content': content,
        #                                     'role': msg.get('role', 'assistant'),
        #                                     'message_id': f"internal_{msg_idx}",
        #                                     'timestamp': datetime.now().isoformat()
        #                                 }, room=self.session_id)
                    
        #             return result
                    
        #         except Exception as e:
        #             self.socketio.emit('agent_internal_conversation', {
        #                 'session_id': self.session_id,
        #                 'agent_name': 'websearch_and_crawl_agent',
        #                 'type': 'internal_error',
        #                 'content': f'Error in internal processing: {str(e)}',
        #                 'timestamp': datetime.now().isoformat()
        #             }, room=self.session_id)
        #             raise
            
        #     agent._reply_user = enhanced_reply_user
        #     print("[EnhancedThoughtAgent] Successfully hooked WebSearch and Crawl Agent")
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error hooking WebSearch Agent: {e}")
    
    def _monitor_messages_real_time(self, groupchat_manager):
        """Monitor for new messages and stream them in real-time"""
        while self._monitoring_active:
            try:
                current_messages = groupchat_manager.groupchat.messages
                current_count = len(current_messages)
                
                # Stream any new messages
                if current_count > self.last_streamed_count:
                    for i in range(self.last_streamed_count, current_count):
                        if i < len(current_messages) and self._monitoring_active:
                            self._stream_single_message(current_messages[i], i)
                    self.last_streamed_count = current_count
                
                # Small delay to prevent excessive polling
                time.sleep(0.2)
                
            except Exception as e:
                print(f"[EnhancedThoughtAgent] Error in real-time message monitoring: {e}")
                time.sleep(1)  # Longer delay on error
    
    def _stream_single_message(self, message, message_index):
        """Stream a single message to the frontend immediately as it's created"""
        try:
            # Handle both dict and autogen message object formats
            if hasattr(message, 'get'):
                agent_name = message.get('name', 'unknown')
                content = message.get('content', '')
                role = message.get('role', 'assistant')
            elif hasattr(message, 'name'):
                agent_name = getattr(message, 'name', 'unknown')
                content = getattr(message, 'content', '')
                role = getattr(message, 'role', 'assistant')
            else:
                print(f"[EnhancedThoughtAgent] Unknown message format: {type(message)}")
                return
            
            # Skip empty messages or system messages
            if not content.strip() or role == 'system':
                return
            
            # Detect agent changes and emit agent_started event
            if agent_name != self.current_agent:
                self.current_agent = agent_name
                self.socketio.emit('agent_started', {
                    'agent_name': agent_name,
                    'display_name': self.agent_metadata.get(agent_name, {}).get('display_name', agent_name),
                    'color': self.agent_metadata.get(agent_name, {}).get('color', '#6c757d'),
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
            
            # Emit the message in chronological order
            self.socketio.emit('agent_message', {
                'agent_name': agent_name,
                'display_name': self.agent_metadata.get(agent_name, {}).get('display_name', agent_name),
                'content': content,
                'message_id': message_index,
                'timestamp': datetime.now().isoformat(),
                'type': 'main_conversation'
            }, room=self.session_id)
            
            # Detect and emit custom agent thinking processes
            self._detect_and_emit_thinking_process(agent_name, content)
            
            print(f"[EnhancedThoughtAgent] Streamed message from {agent_name}: {content[:100]}...")
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error streaming single message: {e}")
    
    def _detect_and_emit_thinking_process(self, agent_name: str, content: str):
        """Detect custom agent internal activities and emit thinking processes"""
        try:
            # Enhanced detection for Expert Knowledge Agent
            if agent_name == 'expert_knowledge_agent':
                if any(keyword in content.lower() for keyword in ['searching', 'knowledge', 'database', 'retrieving']):
                    self.socketio.emit('custom_agent_thinking', {
                        'agent': 'expert_knowledge',
                        'phase': 'rag_search',
                        'content': 'Searching knowledge database for relevant information...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                elif any(keyword in content.lower() for keyword in ['found', 'retrieved', 'documents']):
                    self.socketio.emit('custom_agent_thinking', {
                        'agent': 'expert_knowledge',
                        'phase': 'rag_processing',
                        'content': 'Processing retrieved knowledge documents...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
            
            # Enhanced detection for Web Search Agent  
            elif agent_name == 'websearch_and_crawl_agent':
                if any(keyword in content.lower() for keyword in ['search', 'searching', 'google']):
                    self.socketio.emit('custom_agent_thinking', {
                        'agent': 'websearch_and_crawl',
                        'phase': 'web_search',
                        'content': 'Performing web search for relevant information...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                elif any(keyword in content.lower() for keyword in ['crawl', 'crawling', 'scraping']):
                    self.socketio.emit('custom_agent_thinking', {
                        'agent': 'websearch_and_crawl',
                        'phase': 'web_crawl',
                        'content': 'Crawling and extracting content from web pages...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
            
            # Enhanced detection for Coder Agent
            elif agent_name == 'coder_agent':
                if any(keyword in content.lower() for keyword in ['code', 'function', 'class', 'def ', 'import']):
                    self.socketio.emit('custom_agent_thinking', {
                        'agent': 'coder',
                        'phase': 'code_generation',
                        'content': 'Writing and structuring code solution...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
            
            # Enhanced detection for Code Executor
            elif agent_name == 'code_executor_agent':
                if any(keyword in content.lower() for keyword in ['executing', 'running', 'python']):
                    self.socketio.emit('custom_agent_thinking', {
                        'agent': 'code_executor',
                        'phase': 'code_execution',
                        'content': 'Executing generated code and capturing results...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                elif 'error' in content.lower() or 'exception' in content.lower():
                    self.socketio.emit('custom_agent_thinking', {
                        'agent': 'code_executor',
                        'phase': 'error_handling',
                        'content': 'Handling execution errors and debugging...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
            
            # Research Planner thinking phases
            elif agent_name == 'research_planner_agent':
                if any(keyword in content.lower() for keyword in ['plan', 'strategy', 'approach']):
                    self.socketio.emit('custom_agent_thinking', {
                        'agent': 'research_planner',
                        'phase': 'planning',
                        'content': 'Analyzing request and creating research strategy...',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
        
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error detecting thinking process: {e}")
    
    def run(self, starting_msg):
        """Override run method to add web interface integration with proper flow"""
        try:
            print(f"[EnhancedThoughtAgent] Starting run for session {self.session_id}")
            
            # Emit conversation start
            self.socketio.emit('thinking_process', {
                'type': 'conversation_started',
                'message': 'Initializing ThoughtAgent conversation...',
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            
            # Call parent run method - this will trigger our enhanced groupchat methods
            result = super().run(starting_msg)
            
            # Emit conversation completion with final response
            self.socketio.emit('main_conversation_completed', {
                'final_response': result,
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            
            print(f"[EnhancedThoughtAgent] Completed run for session {self.session_id}")
            return result
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error in run: {e}")
            self.socketio.emit('agent_error', {
                'error': str(e),
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            raise
