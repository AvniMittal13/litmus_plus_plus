import sys
import os
import threading
import time
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path to import existing agents
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.main_agent import MainAgent, extract_json_block
from agents.thought_agent import ThoughtAgent
from agents.prompts.prompts import thought_agent_starting_message, response_analyzer_agent_message, thought_analyzer_agent_message, expert_knowledge_agent_message, thought_creator_agent_message

# Import the existing EnhancedThoughtAgent for reuse
from web_interface.services.agent_service import EnhancedThoughtAgent


class EnhancedMainAgent(MainAgent):
    """
    MainAgent enhanced with real-time web interface integration.
    Orchestrates multiple ThoughtAgents and streams the process to the UI.
    """
    
    def __init__(self, session_id: str, socketio_instance):
        super().__init__()
        self.session_id = session_id
        self.socketio = socketio_instance
        self.enhanced_thought_agents = {}  # Track enhanced ThoughtAgent instances
        self.current_agent = None
        self.main_agent_metadata = {
            'thought_creator_agent': {'color': '#9c27b0', 'display_name': 'Thought Creator', 'icon': 'fa-lightbulb'},
            'response_analyzer_agent': {'color': '#ff5722', 'display_name': 'Response Analyzer', 'icon': 'fa-analyze'},
            'thought_analyzer_agent': {'color': '#795548', 'display_name': 'Thought Analyzer', 'icon': 'fa-search-plus'},
            'expert_knowledge_agent': {'color': '#6f42c1', 'display_name': 'Expert Knowledge (Main)', 'icon': 'fa-brain'},
            'user_proxy_agent': {'color': '#007bff', 'display_name': 'User Proxy (Main)', 'icon': 'fa-user'}
        }
        
        # Metadata for ThoughtAgent instances (for nested display)
        self.thought_agent_metadata = {
            'user_proxy_agent': {'color': '#007bff', 'display_name': 'User Proxy', 'icon': 'fa-user'},
            'research_planner_agent': {'color': '#28a745', 'display_name': 'Research Planner', 'icon': 'fa-search'},
            'expert_knowledge_agent': {'color': '#6f42c1', 'display_name': 'Expert Knowledge', 'icon': 'fa-brain'},
            'websearch_and_crawl_agent': {'color': '#fd7e14', 'display_name': 'Web Search & Crawl', 'icon': 'fa-globe'},
            'coder_agent': {'color': '#dc3545', 'display_name': 'Coder', 'icon': 'fa-code'},
            'code_executor_agent': {'color': '#17a2b8', 'display_name': 'Code Executor', 'icon': 'fa-play'},
            'send_user_msg_agent': {'color': '#6c757d', 'display_name': 'Response Formatter', 'icon': 'fa-comment'}
        }
    
    def run(self, user_query):
        """Override run method to add web interface integration"""
        try:
            print(f"[EnhancedMainAgent] Starting main agent run for session {self.session_id}")
            
            # Emit main agent started
            self.socketio.emit('main_agent_started', {
                'session_id': self.session_id,
                'user_query': user_query,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            
            # Start main agent process with streaming
            return self._run_with_streaming(user_query)
            
        except Exception as e:
            print(f"[EnhancedMainAgent] Error in run: {e}")
            self.socketio.emit('main_agent_error', {
                'error': str(e),
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            raise
    
    def _run_with_streaming(self, user_query):
        """Run MainAgent with streaming to web interface"""
        
        # Add user query to messages
        self.messages.append({"role": "user", "content": user_query})
        
        # Stream Expert Knowledge Agent (MainAgent level) activity
        self._stream_agent_activity('expert_knowledge_agent', 'Querying expert knowledge for initial context...')
        
        # Call expert knowledge agent
        self.user_proxy_agent.agent.send(
            recipient=self.expert_knowledge_agent.agent,
            message=expert_knowledge_agent_message.format(
                conversation_history_user=json.dumps(self.extract_role_messages("user")),
            ),
            request_reply=True
        )
        expert_knowledge = self.user_proxy_agent.agent._oai_messages[self.expert_knowledge_agent.agent][-1]["content"]
        
        # Stream expert knowledge completion
        self._stream_agent_message('expert_knowledge_agent', expert_knowledge)
        
        # Initial thought creation or analysis
        if not self.thought_agents:
            return self._handle_initial_thought_creation(user_query, expert_knowledge)
        else:
            return self._handle_thought_analysis(user_query, expert_knowledge)
    
    def _handle_initial_thought_creation(self, user_query, expert_knowledge):
        """Handle initial thought creation with streaming"""
        
        # Stream Thought Creator Agent activity
        self._stream_agent_activity('thought_creator_agent', 'Creating initial thought paths and research strategies...')
        
        # Call thought creator agent
        self.user_proxy_agent.agent.send(
            recipient=self.thought_creator_agent.agent,
            message=thought_creator_agent_message.format(
                conversation_history=json.dumps(self.messages),
                expert_knowledge=json.dumps(expert_knowledge)
            ),
            request_reply=True
        )
        user_reply = self.user_proxy_agent.agent._oai_messages[self.thought_creator_agent.agent][-1]["content"]
        
        # Stream thought creator response
        self._stream_agent_message('thought_creator_agent', user_reply)
        
        # Parse JSON response
        if "```json" in user_reply:
            try:
                json_content = extract_json_block(user_reply)
                if json_content:
                    json_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_content)
                    thoughts = json.loads(json_clean)["thought_paths"]
                else:
                    return "Could not extract JSON block."
            except json.JSONDecodeError:
                return "Invalid JSON format in user reply."
        else:
            self.messages.append({"role": "assistant", "content": user_reply})
            return user_reply
        
        # Create ThoughtAgents if thoughts exist
        if thoughts:
            return self._create_and_run_thought_agents(user_query, thoughts)
        
        return user_reply
    
    def _handle_thought_analysis(self, user_query, expert_knowledge):
        """Handle thought analysis for existing ThoughtAgents"""
        
        # Stream Thought Analyzer Agent activity
        self._stream_agent_activity('thought_analyzer_agent', 'Analyzing existing thought paths and responses...')
        
        # Call thought analyzer agent
        self.user_proxy_agent.agent.send(
            recipient=self.thought_analyzer_agent.agent,
            message=thought_analyzer_agent_message.format(
                responses=json.dumps(self.final_responses),
                conversation_history=json.dumps(self.messages),
                expert_knowledge=json.dumps(expert_knowledge)
            ),
            request_reply=True
        )
        user_reply = self.user_proxy_agent.agent._oai_messages[self.thought_analyzer_agent.agent][-1]["content"]
        
        # Stream thought analyzer response
        self._stream_agent_message('thought_analyzer_agent', user_reply)
        
        # Parse and handle thought agent updates
        if "```json" in user_reply:
            try:
                json_content = extract_json_block(user_reply)
                if json_content:
                    json_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_content)
                    thought_agent_updates = json.loads(json_clean)
                    self._handle_thought_agent_updates(thought_agent_updates)
            except:
                user_reply = "Invalid JSON format in user reply."
        
        # Run updated thought agents
        responses = self._run_all_thought_agents(user_query)
        
        # Update responses
        for agent_name in self.thought_agents:
            self.final_responses[agent_name] = responses.get(agent_name, None)
        
        # Generate final response
        return self._generate_final_response(user_query)
    
    def _create_and_run_thought_agents(self, user_query, thoughts):
        """Create and run ThoughtAgents with streaming"""
        
        for thought in thoughts:
            thought_name = thought["name"]
            print(f"[EnhancedMainAgent] Creating thought agent: {thought_name}")
            
            # Create EnhancedThoughtAgent instead of regular ThoughtAgent
            enhanced_thought_agent = EnhancedThoughtAgent(
                session_id=self.session_id,
                socketio_instance=self.socketio,
                agent_metadata=self.thought_agent_metadata,
                parent_context='main_agent',
                thought_agent_id=thought_name
            )
            
            # Store the enhanced agent
            self.thought_agents[thought_name] = {
                "agent": enhanced_thought_agent,
                "thought": thought
            }
            self.enhanced_thought_agents[thought_name] = enhanced_thought_agent
            
            # Emit ThoughtAgent created event
            self.socketio.emit('thought_agent_lifecycle', {
                'action': 'created',
                'thought_agent_id': thought_name,
                'thought_data': thought,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
        
        # Run all ThoughtAgents
        responses = self._run_all_thought_agents(user_query)
        
        # Store responses
        for agent_name in self.thought_agents:
            self.final_responses[agent_name] = responses.get(agent_name, None)
        
        # Generate final response
        return self._generate_final_response(user_query)
    
    def _run_all_thought_agents(self, user_query):
        """Run all active ThoughtAgents with lifecycle streaming"""
        responses = {}
        
        for name, agent_info in self.thought_agents.items():
            try:
                # Emit ThoughtAgent started
                self.socketio.emit('thought_agent_lifecycle', {
                    'action': 'started',
                    'thought_agent_id': name,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                
                # Run the enhanced ThoughtAgent
                response = agent_info["agent"].run(
                    starting_msg=thought_agent_starting_message.format(
                        thought=agent_info["thought"],
                        user_query=user_query
                    )
                )
                responses[name] = response
                
                # Emit ThoughtAgent completed
                self.socketio.emit('thought_agent_lifecycle', {
                    'action': 'completed',
                    'thought_agent_id': name,
                    'response': response,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                
            except Exception as exc:
                responses[name] = f"Error: {exc}"
                
                # Emit ThoughtAgent error
                self.socketio.emit('thought_agent_lifecycle', {
                    'action': 'error',
                    'thought_agent_id': name,
                    'error': str(exc),
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
        
        return responses
    
    def _handle_thought_agent_updates(self, thought_agent_updates):
        """Handle updates to ThoughtAgent states with streaming"""
        
        continue_agents = thought_agent_updates.get("continue_agents", [])
        discard_agents = thought_agent_updates.get("discard_agents", [])
        finalize_agents = thought_agent_updates.get("final_response_agents", [])
        new_agents = thought_agent_updates.get("new_agents", [])
        
        # Handle discarded agents
        for agent_name in discard_agents:
            if agent_name in self.thought_agents:
                self.discarded_agents[agent_name] = self.thought_agents.pop(agent_name)
                if agent_name in self.final_responses:
                    del self.final_responses[agent_name]
                
                # Emit discarded event
                self.socketio.emit('thought_agent_lifecycle', {
                    'action': 'discarded',
                    'thought_agent_id': agent_name,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
        
        # Handle finalized agents
        for agent_name in finalize_agents:
            if agent_name in self.thought_agents:
                self.completed_agents[agent_name] = self.thought_agents.pop(agent_name)
                
                # Emit finalized event
                self.socketio.emit('thought_agent_lifecycle', {
                    'action': 'finalized',
                    'thought_agent_id': agent_name,
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
        
        # Handle new agents
        for thought in new_agents:
            thought_name = thought["name"]
            
            # Create new EnhancedThoughtAgent
            enhanced_thought_agent = EnhancedThoughtAgent(
                session_id=self.session_id,
                socketio_instance=self.socketio,
                agent_metadata=self.thought_agent_metadata,
                parent_context='main_agent',
                thought_agent_id=thought_name
            )
            
            self.thought_agents[thought_name] = {
                "agent": enhanced_thought_agent,
                "thought": thought
            }
            self.enhanced_thought_agents[thought_name] = enhanced_thought_agent
            
            # Emit new agent created
            self.socketio.emit('thought_agent_lifecycle', {
                'action': 'created',
                'thought_agent_id': thought_name,
                'thought_data': thought,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
    
    def _generate_final_response(self, user_query):
        """Generate final response with streaming"""
        
        # Stream Response Analyzer Agent activity
        self._stream_agent_activity('response_analyzer_agent', 'Analyzing and synthesizing all thought responses...')
        
        # Call response analyzer
        self.user_proxy_agent.agent.send(
            recipient=self.response_analyzer_agent.agent,
            message=response_analyzer_agent_message.format(
                user_query=user_query,
                responses=json.dumps(self.final_responses)
            ),
            request_reply=True
        )
        user_reply = self.user_proxy_agent.agent._oai_messages[self.response_analyzer_agent.agent][-1]["content"]
        
        # Stream final response
        self._stream_agent_message('response_analyzer_agent', user_reply)
        
        self.messages.append({"role": "assistant", "content": user_reply})
        return user_reply
    
    def _stream_agent_activity(self, agent_name: str, activity_message: str):
        """Stream agent activity/thinking phase"""
        metadata = self.main_agent_metadata.get(agent_name, {
            'color': '#6c757d', 
            'display_name': agent_name, 
            'icon': 'fa-robot'
        })
        
        self.socketio.emit('main_agent_thinking', {
            'agent': agent_name,
            'display_name': metadata['display_name'],
            'color': metadata['color'],
            'phase': 'processing',
            'content': activity_message,
            'timestamp': datetime.now().isoformat(),
            'level': 'main'
        }, room=self.session_id)
    
    def _stream_agent_message(self, agent_name: str, content: str):
        """Stream agent message content"""
        metadata = self.main_agent_metadata.get(agent_name, {
            'color': '#6c757d', 
            'display_name': agent_name, 
            'icon': 'fa-robot'
        })
        
        self.socketio.emit('main_agent_message', {
            'agent_name': agent_name,
            'display_name': metadata['display_name'],
            'color': metadata['color'],
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'level': 'main'
        }, room=self.session_id)
