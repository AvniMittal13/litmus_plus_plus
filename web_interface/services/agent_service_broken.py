from flask_socketio import SocketIO
from datetime import datetime
import threading
import time
import os
import sys

# Add the parent directory to Python path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.thought_agent import ThoughtAgent
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction


class ThoughtAgentService:
    def __init__(self):
        # Initialize without socketio and session_id - they'll be provided per request
        self._active_sessions = {}
        
    def start_conversation(self, session_id: str, query: str, socketio: SocketIO):
        """Start a conversation for a specific session"""
        # Create or get agent for this session
        if session_id not in self._active_sessions:
            # Extract thought agent ID
            thought_agent_id = session_id.split('_thought_')[1] if '_thought_' in session_id else None
            
            self._active_sessions[session_id] = {
                'agent': EnhancedThoughtAgent(
                    session_id=session_id, 
                    socketio_instance=socketio,
                    agent_metadata={},
                    parent_context='main_agent',
                    thought_agent_id=thought_agent_id
                ),
                'processing': False
            }
        
        session = self._active_sessions[session_id]
        
        if session['processing']:
            socketio.emit('error', {
                'message': 'Agent is currently busy processing another request. Please wait.',
                'session_id': session_id
            }, room=session_id)
            return
            
        # Start processing in a background thread
        import threading
        
        def process_conversation():
            session['processing'] = True
            try:
                # Emit processing start
                socketio.emit('thinking_process', {
                    'session_id': session_id,
                    'type': 'start',
                    'content': 'Starting to process your request...',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
                # Process the query using the enhanced agent
                response = session['agent'].run(query)
                
                # Emit final response
                socketio.emit('conversation_response', {
                    'session_id': session_id,
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
                # Emit processing completion
                socketio.emit('thinking_process', {
                    'session_id': session_id,
                    'type': 'complete',
                    'content': 'Processing completed successfully!',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
            except Exception as e:
                # Emit error
                socketio.emit('error', {
                    'session_id': session_id,
                    'message': f'Error processing query: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
                
            finally:
                session['processing'] = False
        
        # Start the background thread
        thread = threading.Thread(target=process_conversation)
        thread.daemon = True
        thread.start()
        
    def process_query(self, query: str) -> str:
        """Process a user query through the thought agent - for compatibility with test scripts"""
        # This is used by test scripts - create a minimal mock
        if not hasattr(self, 'socketio') or not hasattr(self, 'session_id'):
            raise RuntimeError("This method requires socketio and session_id to be set")
        
        # Use the active session or create one
        if self.session_id not in self._active_sessions:
            # Extract thought agent ID
            thought_agent_id = self.session_id.split('_thought_')[1] if '_thought_' in self.session_id else None
            
            self._active_sessions[self.session_id] = {
                'agent': EnhancedThoughtAgent(
                    session_id=self.session_id,
                    socketio_instance=self.socketio,
                    agent_metadata={},
                    parent_context='main_agent',
                    thought_agent_id=thought_agent_id
                ),
                'processing': False
            }
        
        agent = self._active_sessions[self.session_id]['agent']
        return agent.run(query)


class EnhancedThoughtAgent(ThoughtAgent):
    """Enhanced ThoughtAgent with real-time web interface integration"""
    
    def __init__(self, socketio: SocketIO, session_id: str):
        # Initialize the parent ThoughtAgent
        super().__init__()
        
        self.socketio = socketio
        self.session_id = session_id
        self._monitoring_active = False
        
        # Hook into custom agents after initialization
        self._hook_custom_agents()
        
        # Hook into the groupchat continue method to monitor conversation
        # self._hook_groupchat_monitoring()  # Disabled for now
    
    def _hook_groupchat_monitoring(self):
        """Hook into the GroupChat continue method to monitor all agent interactions"""
        try:
            original_continue_groupchat = self.groupchat.continue_groupchat
            
            def enhanced_continue_groupchat(messages, agents, continue_groupchat):
                self._monitoring_active = True
                
                # Emit groupchat step start
                self.socketio.emit('thinking_process', {
                    'session_id': self.session_id,
                    'type': 'groupchat_step',
                    'content': f'Group discussion in progress with {len(agents)} agents...',
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                
                try:
                    result = original_continue_groupchat(messages, agents, continue_groupchat)
                    return result
                except Exception as e:
                    self.socketio.emit('thinking_process', {
                        'session_id': self.session_id,
                        'type': 'error',
                        'content': f'Error in group discussion: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }, room=self.session_id)
                    self._monitoring_active = False
                    raise
        
            # Replace the continue_groupchat method
            self.groupchat.continue_groupchat = enhanced_continue_groupchat
            
        except Exception as e:
            print(f"[EnhancedThoughtAgent] Error hooking groupchat monitoring: {e}")
    
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
                
                def enhanced_generate_reply(messages=None, sender=None, **kwargs):
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
                        result = original_generate_reply(messages=messages, sender=sender, **kwargs)
                        
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
                
                def enhanced_generate_reply(messages=None, sender=None, **kwargs):
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
                        result = original_generate_reply(messages=messages, sender=sender, **kwargs)
                        
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
