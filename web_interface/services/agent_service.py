import sys
import os
import threading
import time
import json
import chromadb
from datetime import datetime
from typing import Optional, Dict, Any

from utils.aoai_chat import model_config

# Add parent directory to path to import existing agents
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.thought_agent_db import ThoughtAgent
from agents.groupchat import GroupChat
from agents.agent import Agent

from web_interface.agents_enhanced.enhanced_expert_knowledge import EnhancedExpertKnowledgeAgent
from web_interface.agents_enhanced.enhanced_websearch_crawl import EnhancedWebSearchCrawlAgent


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
            # Session format: "main_session_id_thought_agent_name"
            thought_agent_id = None
            if '_thought_' in session_id:
                thought_agent_id = session_id.split('_thought_')[1]
                print(f"[AgentService] Extracted thought_agent_id: '{thought_agent_id}' from session: {session_id}")
            else:
                print(f"[AgentService] No thought agent context found in session: {session_id}")

            # Create enhanced ThoughtAgent with SocketIO integration and proper context
            agent = EnhancedThoughtAgent(
                session_id, 
                socketio_instance, 
                self.agent_metadata,
                parent_context='main_agent',  # Set context for proper event handling
                thought_agent_id=thought_agent_id,  # Pass extracted ThoughtAgent ID
                parent_event_forwarder=None  # Can be set for event forwarding if needed
            )            # Store conversation info
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
    
    def __init__(self, session_id: str, socketio_instance, agent_metadata: dict, 
                 parent_context: str = None, thought_agent_id: str = None, 
                 parent_event_forwarder=None):
        super().__init__()
        self.session_id = session_id
        self.socketio = socketio_instance
        self.agent_metadata = agent_metadata
        self.parent_context = parent_context  # NEW: 'main_agent' when called from MainAgent
        self.thought_agent_id = thought_agent_id  # NEW: ID for this ThoughtAgent instance
        self.parent_event_forwarder = parent_event_forwarder  # NEW: Event forwarding callback
        
        # Debug logging for thought agent context
        if thought_agent_id:
            print(f"[EnhancedThoughtAgent] Initialized with ThoughtAgent ID: '{thought_agent_id}'")
        else:
            print(f"[EnhancedThoughtAgent] Initialized without ThoughtAgent ID (main agent context)")
        print(f"[EnhancedThoughtAgent] Session ID: {session_id}")
        print(f"[EnhancedThoughtAgent] Parent context: {parent_context}")
        
        self.current_agent = None
        self.message_count = 0
        self._monitoring_active = False
        self.last_streamed_count = 0
        
        # Track enhanced agents
        self.enhanced_expert_knowledge_active = False
        self.enhanced_expert_agent_instance = None
        self.enhanced_websearch_crawl_active = False
        self.enhanced_websearch_agent_instance = None
        
        # Replace agents with enhanced versions
        self._replace_expert_knowledge_agent()
        self._replace_websearch_crawl_agent()
        
        self.groupchat = GroupChat(agents_list=[
                self.user_proxy_agent.agent,
                self.send_user_msg_agent.agent,
                self.research_planner_agent.agent,
                # self.firecrawl_websearch_agent.agent,
                # self.call_firecrawl_websearch_agent.agent,
                self.coder_agent.agent,
                self.code_executor_agent.agent,
                self.expert_knowledge_agent.agent,
                self.websearch_and_crawl_agent.agent
            ], 
            initiator_agent=self.user_proxy_agent.agent,
            last_message_agent=self.send_user_msg_agent.agent,
            custom_speaker_selection_func=self.custom_speaker_selection_func
        )


        # Enhance the groupchat to emit real-time updates
        self._enhance_groupchat()
    
    def _emit_and_forward(self, event_type, event_data):
        """Emit event to current session and forward to parent if available"""
        # Emit to current session (ThoughtAgent's own session)
        self.socketio.emit(event_type, event_data, room=self.session_id)
        print(f"[EnhancedThoughtAgent] Emitted {event_type} to session {self.session_id}")
        
        # Forward to parent session if forwarder is available
        if self.parent_event_forwarder:
            try:
                print(f"[EnhancedThoughtAgent] Forwarding {event_type} to parent...")
                self.parent_event_forwarder(event_type, event_data, self.session_id)
                print(f"[EnhancedThoughtAgent] Successfully forwarded {event_type} to parent")
            except Exception as e:
                print(f"[EnhancedThoughtAgent] Error forwarding event {event_type}: {e}")
        else:
            print(f"[EnhancedThoughtAgent] No parent forwarder available for {event_type}")
    
    def _get_main_session_id(self):
        """Extract main session ID from ThoughtAgent session ID for frontend communication"""
        if '_thought_' in self.session_id:
            main_session_id = self.session_id.split('_thought_')[0]
            print(f"[EnhancedThoughtAgent] Session extraction: ThoughtAgent={self.session_id} -> Main={main_session_id}")
            return main_session_id
        else:
            print(f"[EnhancedThoughtAgent] Using session ID as-is: {self.session_id}")
            return self.session_id
    
    def _replace_expert_knowledge_agent(self):
        """Replace the original expert knowledge agent with enhanced version"""
        if EnhancedExpertKnowledgeAgent is None:
            print("[EnhancedThoughtAgent] Enhanced expert knowledge agent not available, using original")
            return
            
        try:
            from agents.prompts.thought_agent.expert_knowledge_agent import expert_knowledge_agent
            
            # Create enhanced expert knowledge agent with WebSocket capabilities
            enhanced_expert_agent = EnhancedExpertKnowledgeAgent(
                session_id=self.session_id,
                socketio_instance=self.socketio,
                name = expert_knowledge_agent["name"],
                system_message = expert_knowledge_agent["system_message"],
                description = expert_knowledge_agent["description"],
                llm_config = model_config,
                human_input_mode = expert_knowledge_agent["human_input_mode"],
                code_execution_config = expert_knowledge_agent["code_execution_config"]
            )
            
            # Replace the agent in the instance
            self.expert_knowledge_agent.agent = enhanced_expert_agent            
 
            print("[EnhancedThoughtAgent] Successfully replaced expert knowledge agent with enhanced version")
            self.enhanced_expert_knowledge_active = True
            self.enhanced_expert_agent_instance = enhanced_expert_agent
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Warning: Could not replace expert knowledge agent: {e}")
            # Continue with original agent if replacement fails
    

    def _replace_websearch_crawl_agent(self):
        """Replace the original websearch and crawl agent with enhanced version"""
        if EnhancedWebSearchCrawlAgent is None:
            print("[EnhancedThoughtAgent] Enhanced websearch and crawl agent not available, using original")
            return
            
        try:
            from agents.prompts.thought_agent.websearch_and_crawl_agent import websearch_and_crawl
            # Create enhanced websearch and crawl agent with WebSocket capabilities
            enhanced_websearch_agent = EnhancedWebSearchCrawlAgent(
                session_id=self.session_id,
                socketio_instance=self.socketio,
                name = websearch_and_crawl["name"],
                system_message = websearch_and_crawl["system_message"],
                description = websearch_and_crawl["description"],
                llm_config = model_config,
                human_input_mode = websearch_and_crawl["human_input_mode"],
                code_execution_config = websearch_and_crawl["code_execution_config"]
            )
            
            # Replace the agent in the instance
            self.websearch_and_crawl_agent.agent = enhanced_websearch_agent

            print("[EnhancedThoughtAgent] Successfully replaced websearch and crawl agent with enhanced version")
            self.enhanced_websearch_crawl_active = True
            self.enhanced_websearch_agent_instance = enhanced_websearch_agent
            print(f"[EnhancedThoughtAgent] Enhanced websearch agent active: {self.enhanced_websearch_crawl_active}")

        except Exception as e:
            print(f"[EnhancedThoughtAgent] Warning: Could not replace websearch and crawl agent: {e}")
            # Continue with original agent if replacement fails
    

    def _enhance_groupchat(self):
        """Add real-time messaging to the groupchat"""
        
        original_continue = self.groupchat.continue_groupchat
        
        def enhanced_continue_groupchat(starting_msg):
            """Enhanced continue_groupchat with real-time message streaming"""
            try:
                conversation_started_data = {
                    'session_id': self.session_id,
                    'starting_message': starting_msg,
                    'timestamp': datetime.now().isoformat()
                }
                self._emit_and_forward('agent_conversation_started', conversation_started_data)
                
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
                
                # NEW: Post-processing hook - ensure enhanced agent summaries are emitted
                self._post_process_enhanced_agents()
                
                return messages, summary
                
            except Exception as e:
                print(f"[EnhancedThoughtAgent] Error in enhanced continue_groupchat: {e}")
                self._monitoring_active = False
                raise
        
        # Replace the continue_groupchat method
        self.groupchat.continue_groupchat = enhanced_continue_groupchat
    
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
            
            print(f"[EnhancedThoughtAgent] Processing message from agent: '{agent_name}' (enhanced_expert_active: {self.enhanced_expert_knowledge_active})")
            
            # Detect agent changes and emit agent_started event
            if agent_name != self.current_agent:
                self.current_agent = agent_name
                agent_started_data = {
                    'agent_name': agent_name,
                    'display_name': self.agent_metadata.get(agent_name, {}).get('display_name', agent_name),
                    'color': self.agent_metadata.get(agent_name, {}).get('color', '#6c757d'),
                    'timestamp': datetime.now().isoformat()
                }
                self._emit_and_forward('agent_started', agent_started_data)
            
            # Emit the message in chronological order
            agent_message_data = {
                'agent_name': agent_name,
                'display_name': self.agent_metadata.get(agent_name, {}).get('display_name', agent_name),
                'content': content,
                'message_id': message_index,
                'timestamp': datetime.now().isoformat(),
                'type': 'main_conversation'
            }
            self._emit_and_forward('agent_message', agent_message_data)
            
            # Detect and emit custom agent thinking processes
            self._detect_and_emit_thinking_process(agent_name, content)
            
            print(f"[EnhancedThoughtAgent] Streamed message from {agent_name}: {content[:100]}...")
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error streaming single message: {e}")
    
    def _detect_and_emit_thinking_process(self, agent_name: str, content: str):
        """Detect custom agent internal activities and emit thinking processes"""
        try:
            # FIXED: Handle both naming conventions for Expert Knowledge Agent
            # Backend can send either 'expert_knowledge' or 'expert_knowledge_agent'
            expert_knowledge_names = ['expert_knowledge_agent', 'expert_knowledge']
            websearch_crawl_names = ['websearch_and_crawl_agent', 'websearch_crawl', 'websearch_and_crawl']
            
            # Handle enhanced Expert Knowledge Agent - check for both naming conventions
            if agent_name in expert_knowledge_names and self.enhanced_expert_knowledge_active:
                print(f"[EnhancedThoughtAgent] Detected enhanced expert knowledge agent: {agent_name}")
                self._emit_enhanced_expert_summary()
                return
                
            # Enhanced detection for Expert Knowledge Agent (fallback for non-enhanced)
            if agent_name in expert_knowledge_names:
                if any(keyword in content.lower() for keyword in ['searching', 'knowledge', 'database', 'retrieving']):
                    self._emit_custom_thinking('expert_knowledge', 'rag_search', 
                                             'Searching knowledge database for relevant information...')
                elif any(keyword in content.lower() for keyword in ['found', 'retrieved', 'documents']):
                    self._emit_custom_thinking('expert_knowledge', 'rag_processing',
                                             'Processing retrieved knowledge documents...')
            
            # Handle enhanced Web Search and Crawl Agent - check for multiple naming conventions
            elif agent_name in websearch_crawl_names and self.enhanced_websearch_crawl_active:
                print(f"[EnhancedThoughtAgent] Detected enhanced websearch agent: {agent_name}")
                self._emit_enhanced_websearch_summary()
                return
                
            # Enhanced detection for Web Search Agent (fallback for non-enhanced)
            elif agent_name in websearch_crawl_names:
                print(f"[EnhancedThoughtAgent] Detected regular websearch agent activity: {content[:100]}")
                if any(keyword in content.lower() for keyword in ['search', 'searching', 'google']):
                    self._emit_custom_thinking('websearch_crawl', 'web_search',
                                             'Performing web search for relevant information...')
                elif any(keyword in content.lower() for keyword in ['crawl', 'crawling', 'scraping']):
                    self._emit_custom_thinking('websearch_crawl', 'web_crawl',
                                             'Crawling and extracting content from web pages...')
            
            # Enhanced detection for Coder Agent
            elif agent_name == 'coder_agent':
                if any(keyword in content.lower() for keyword in ['code', 'function', 'class', 'def ', 'import']):
                    self._emit_custom_thinking('coder', 'code_generation',
                                             'Writing and structuring code solution...')
            
            # Enhanced detection for Code Executor
            elif agent_name == 'code_executor_agent':
                if any(keyword in content.lower() for keyword in ['executing', 'running', 'python']):
                    self._emit_custom_thinking('code_executor', 'code_execution',
                                             'Executing generated code and capturing results...')
                elif 'error' in content.lower() or 'exception' in content.lower():
                    self._emit_custom_thinking('code_executor', 'error_handling',
                                             'Handling execution errors and debugging...')
            
            # Research Planner thinking phases
            elif agent_name == 'research_planner_agent':
                if any(keyword in content.lower() for keyword in ['plan', 'strategy', 'approach']):
                    self._emit_custom_thinking('research_planner', 'planning',
                                             'Analyzing request and creating research strategy...')
        
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error detecting thinking process: {e}")
    
    def _post_process_enhanced_agents(self):
        """Post-processing hook to ensure enhanced agent summaries are emitted after group chat completion"""
        try:
            print(f"[EnhancedThoughtAgent] Post-processing enhanced agents...")
            
            # Check if enhanced expert knowledge agent was active and has data
            if self.enhanced_expert_knowledge_active and self.enhanced_expert_agent_instance:
                if hasattr(self.enhanced_expert_agent_instance, 'internal_conversation'):
                    internal_messages = self.enhanced_expert_agent_instance.internal_conversation
                    if internal_messages and len(internal_messages) > 0:
                        print(f"[EnhancedThoughtAgent] Post-processing: Found {len(internal_messages)} expert knowledge messages")
                        self._emit_enhanced_expert_summary()
                    else:
                        print(f"[EnhancedThoughtAgent] Post-processing: No expert knowledge messages to process")
                else:
                    print(f"[EnhancedThoughtAgent] Post-processing: Expert agent has no internal_conversation attribute")
            
            # Check if enhanced websearch agent was active and has data  
            if self.enhanced_websearch_crawl_active and self.enhanced_websearch_agent_instance:
                if hasattr(self.enhanced_websearch_agent_instance, 'internal_conversation'):
                    internal_messages = self.enhanced_websearch_agent_instance.internal_conversation
                    if internal_messages and len(internal_messages) > 0:
                        print(f"[EnhancedThoughtAgent] Post-processing: Found {len(internal_messages)} websearch messages")
                        self._emit_enhanced_websearch_summary()
                    else:
                        print(f"[EnhancedThoughtAgent] Post-processing: No websearch messages to process")
                else:
                    print(f"[EnhancedThoughtAgent] Post-processing: Websearch agent has no internal_conversation attribute")
                    
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error in post-processing enhanced agents: {e}")
    
    def _emit_custom_thinking(self, agent: str, phase: str, content: str, step_id: str = None):
        """Helper method to emit custom agent thinking with context"""
        thinking_data = {
            'agent': agent,
            'phase': phase,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'step_id': step_id  # Optional step ID for enhanced agents
        }
        self._emit_and_forward('custom_agent_thinking', thinking_data)
    
    def _emit_enhanced_expert_summary(self):
        """Emit all internal conversation messages from enhanced expert agent for thinking panel"""
        try:
            print(f"[EnhancedThoughtAgent] _emit_enhanced_expert_summary called - checking enhanced agent instance")
            
            if not self.enhanced_expert_agent_instance:
                print(f"[EnhancedThoughtAgent] ERROR: Enhanced expert agent instance is None")
                return
                
            if not hasattr(self.enhanced_expert_agent_instance, 'internal_conversation'):
                print(f"[EnhancedThoughtAgent] ERROR: Enhanced agent instance does not have internal_conversation attribute")
                return
            
            internal_messages = self.enhanced_expert_agent_instance.internal_conversation
            print(f"[EnhancedThoughtAgent] Found {len(internal_messages) if internal_messages else 0} internal messages")
            
            if not internal_messages:
                print(f"[EnhancedThoughtAgent] WARNING: No internal messages available - agent may not have processed anything yet")
                return
            
            # Generate unique step ID for this expert knowledge agent call
            import uuid
            unique_step_id = f"expert_knowledge_{str(uuid.uuid4())[:8]}"
            
            print(f"[EnhancedThoughtAgent] Processing {len(internal_messages)} internal messages for step: {unique_step_id}")
            
            # Emit each internal message as a thinking phase (simplified approach)
            for i, message in enumerate(internal_messages):
                message_type = message.get('type', 'processing')
                content = message.get('content', 'Processing...')
                
                # Create a simple, clear summary for each step
                phase_content = f"Step {i+1}: {content}"
                
                self._emit_custom_thinking(
                    agent='expert_knowledge',
                    phase=self._map_internal_type_to_phase(message_type),
                    content=phase_content,
                    step_id=unique_step_id
                )
            
            print(f"[EnhancedThoughtAgent] About to emit store_internal_conversation with {len(internal_messages)} messages")
            print(f"[EnhancedThoughtAgent] ThoughtAgent ID: '{self.thought_agent_id}' (should not be None for nested agents)")
            
            # Extract main session ID from ThoughtAgent session ID
            # ThoughtAgent session format: "main_session_id_thought_agent_name"
            main_session_id = self._get_main_session_id()
            
            # Store the full internal conversation data for button click access with step ID
            self.socketio.emit('store_internal_conversation', {
                'step_id': unique_step_id,
                'agent_name': 'expert_knowledge',  # Use consistent backend naming
                'internal_conversation': internal_messages,
                'timestamp': datetime.now().isoformat(),
                'level': 'thought_agent',  # Indicate this is ThoughtAgent level
                'thought_agent_id': self.thought_agent_id,  # Include ThoughtAgent ID
                'parent_context': self.parent_context  # Include parent context
            }, room=main_session_id)  # Emit to main session, not ThoughtAgent session
            
            print(f"[EnhancedThoughtAgent] ✅ SUCCESSFULLY emitted store_internal_conversation for {len(internal_messages)} messages with step: {unique_step_id}")
            print(f"[EnhancedThoughtAgent] Emitted to main session {main_session_id} instead of ThoughtAgent session {self.session_id}")
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] ❌ ERROR in _emit_enhanced_expert_summary: {e}")
            import traceback
            print(f"[EnhancedThoughtAgent] Traceback: {traceback.format_exc()}")
    
    def _create_summary_content(self, message_type: str, message_data: dict) -> str:
        """Create summary content for thinking panel based on internal message type"""
        content_map = {
            'rag_initialization': 'Initializing knowledge retrieval system...',
            'assistant_initialization': 'Setting up expert knowledge assistant...',
            'rag_search_start': 'Searching knowledge database for relevant information...',
            'rag_retrieval_start': 'Retrieving relevant documents from knowledge base...',
            'rag_processing': 'Processing retrieved knowledge documents...',
            'rag_query': 'Analyzing query against expert knowledge...',
            'rag_response': 'Generating response from expert knowledge...',
            'rag_completion': 'Finalizing knowledge-based response...',
            'final_response': 'Expert knowledge analysis complete.',
            'rag_error': 'Handling knowledge retrieval issue...',
            'agent_error': 'Resolving expert knowledge processing error...'
        }
        
        return content_map.get(message_type, f"Processing expert knowledge: {message_type.replace('_', ' ').title()}...")
    
    def _map_internal_type_to_phase(self, message_type: str) -> str:
        """Map internal message types to thinking panel phases"""
        phase_map = {
            'rag_initialization': 'initialization',
            'assistant_initialization': 'setup',
            'rag_search_start': 'rag_search',
            'rag_retrieval_start': 'retrieval',
            'rag_processing': 'rag_processing',
            'rag_query': 'query_analysis',
            'rag_response': 'response_generation',
            'rag_completion': 'completion',
            'final_response': 'final',
            'rag_error': 'error_handling',
            'agent_error': 'error_handling'
        }
        
        return phase_map.get(message_type, 'processing')
    
    def _emit_enhanced_websearch_summary(self):
        """Emit all internal conversation messages from enhanced websearch agent for thinking panel"""
        try:
            if not self.enhanced_websearch_agent_instance or not hasattr(self.enhanced_websearch_agent_instance, 'internal_conversation'):
                print(f"[EnhancedThoughtAgent] Enhanced agent instance not available for summary")
                return

            internal_messages = self.enhanced_websearch_agent_instance.internal_conversation

            if not internal_messages:
                print(f"[EnhancedThoughtAgent] No internal messages available")
                return

            # Generate unique step ID for this websearch agent call
            import uuid
            unique_step_id = f"websearch_crawl_{str(uuid.uuid4())[:8]}"

            print(f"[EnhancedThoughtAgent] Processing {len(internal_messages)} internal messages for step: {unique_step_id}")
            
            # Emit each internal message as a thinking phase (simplified approach)
            for i, message in enumerate(internal_messages):
                message_type = message.get('type', 'processing')
                content = message.get('content', 'Processing...')
                
                # Create a simple, clear summary for each step
                phase_content = f"Step {i+1}: {content}"
                
                self._emit_custom_thinking(
                    agent='websearch_crawl',
                    phase=self._map_websearch_internal_type_to_phase(message_type),
                    content=phase_content,
                    step_id=unique_step_id
                )
            
            # Store the full internal conversation data for button click access with step ID
            print(f"[EnhancedThoughtAgent] About to emit websearch store_internal_conversation with {len(internal_messages)} messages")
            print(f"[EnhancedThoughtAgent] Websearch ThoughtAgent ID: '{self.thought_agent_id}' (should not be None for nested agents)")
            
            # Extract main session ID from ThoughtAgent session ID
            main_session_id = self._get_main_session_id()
            
            self.socketio.emit('store_internal_conversation', {
                'step_id': unique_step_id,
                'agent_name': 'websearch_crawl',  # Use consistent backend naming
                'internal_conversation': internal_messages,
                'timestamp': datetime.now().isoformat(),
                'level': 'thought_agent',  # Indicate this is ThoughtAgent level
                'thought_agent_id': self.thought_agent_id,  # Include ThoughtAgent ID
                'parent_context': self.parent_context  # Include parent context
            }, room=main_session_id)  # Emit to main session, not ThoughtAgent session
            
            print(f"[EnhancedThoughtAgent] ✅ SUCCESSFULLY emitted websearch store_internal_conversation for {len(internal_messages)} messages with step: {unique_step_id}")
            print(f"[EnhancedThoughtAgent] Emitted websearch to main session {main_session_id} instead of ThoughtAgent session {self.session_id}")
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] ❌ ERROR in _emit_enhanced_websearch_summary: {e}")
            import traceback
            print(f"[EnhancedThoughtAgent] Traceback: {traceback.format_exc()}")
    

    def ___emit_enhanced_websearch_summary(self):
        """Emit summary messages from enhanced websearch agent's internal conversation for thinking panel"""
        try:
            if not self.enhanced_websearch_agent_instance or not hasattr(self.enhanced_websearch_agent_instance, 'internal_conversation'):
                print(f"[EnhancedThoughtAgent] Enhanced websearch agent instance not available for summary")
                return
            
            internal_messages = self.enhanced_websearch_agent_instance.internal_conversation
            
            if not internal_messages:
                # Emit a default activity message if no internal messages yet
                self.socketio.emit('custom_agent_thinking', {
                    'agent': 'websearch_crawl',
                    'phase': 'active',
                    'content': 'Web Search and Crawl Agent is actively searching for information...',
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                return
            
            # Get the latest internal conversation step
            latest_message = internal_messages[-1]
            message_type = latest_message.get('type', 'processing')
            
            # Create appropriate summary based on the latest internal activity
            summary_content = self._create_websearch_summary_content(message_type, latest_message)
            
            # Generate unique step ID for this websearch agent call
            import uuid
            unique_step_id = f"websearch_crawl_{str(uuid.uuid4())[:8]}"
            
            # Emit summary message for thinking panel with unique step ID
            self._emit_custom_thinking(
                agent='websearch_crawl',
                phase=self._map_websearch_internal_type_to_phase(message_type),
                content=summary_content,
                step_id=unique_step_id
            )
            
            # Store the full internal conversation data for button click access with step ID
            # Extract main session ID from ThoughtAgent session ID
            main_session_id = self._get_main_session_id()
            
            self.socketio.emit('store_internal_conversation', {
                'step_id': unique_step_id,  # Use step ID instead of agent name
                'agent_name': 'websearch_crawl',  # Keep for display purposes
                'internal_conversation': internal_messages,
                'timestamp': datetime.now().isoformat(),
                'level': 'thought_agent',  # NEW: Indicate this is ThoughtAgent level
                'thought_agent_id': self.thought_agent_id,  # NEW: Include ThoughtAgent ID
                'parent_context': self.parent_context  # NEW: Include parent context
            }, room=main_session_id)  # Emit to main session, not ThoughtAgent session
            
            print(f"[EnhancedThoughtAgent] Emitted enhanced websearch summary: {message_type} with step ID: {unique_step_id}")
            print(f"[EnhancedThoughtAgent] Stored {len(internal_messages)} internal conversation messages for step: {unique_step_id}")
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error emitting enhanced websearch summary: {e}")
    
    def _create_websearch_summary_content(self, message_type: str, message_data: dict) -> str:
        """Create summary content for thinking panel based on websearch internal message type"""
        content_map = {
            'search_started': 'Initializing web search and crawl process...',
            'search_preparation': 'Preparing search queries and parameters...',
            'web_search_execution': 'Executing web search using Firecrawl tool...',
            'tool_execution': 'Running search tools and crawling web pages...',
            'search_query': 'Formulating and executing search queries...',
            'content_processing': 'Processing and analyzing search results...',
            'final_synthesis': 'Synthesizing findings into structured response...',
            'search_completed': 'Web search and crawl process completed.',
            'search_error': 'Handling web search issue...'
        }
        
        return content_map.get(message_type, f"Processing web search: {message_type.replace('_', ' ').title()}...")
    
    def _map_websearch_internal_type_to_phase(self, message_type: str) -> str:
        """Map websearch internal message types to thinking panel phases"""
        phase_map = {
            'search_started': 'initialization',
            'search_preparation': 'setup',
            'web_search_execution': 'search_execution',
            'tool_execution': 'tool_processing',
            'search_query': 'query_processing',
            'content_processing': 'content_analysis',
            'final_synthesis': 'result_synthesis',
            'search_completed': 'completion',
            'search_error': 'error_handling'
        }
        
        return phase_map.get(message_type, 'processing')
    
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
            completion_data = {
                'final_response': result,
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }
            self._emit_and_forward('main_conversation_completed', completion_data)
            
            print(f"[EnhancedThoughtAgent] Completed run for session {self.session_id}")
            return result
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error in run: {e}")
            error_data = {
                'error': str(e),
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }
            self._emit_and_forward('agent_error', error_data)
            raise
