"""
Enhanced Main Agent - Exact Replication of main_agent.py Logic with Event Forwarding
Maintains conversation state, handles clarifications, and forwards ThoughtAgent events
"""

import sys
import os
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.prompts.main_agent.user_proxy_agent import user_proxy_agent
from agents.prompts.main_agent.thought_creator_agent import thought_creator_agent
from agents.prompts.main_agent.response_analyzer_agent import response_analyzer_agent
from agents.prompts.main_agent.thought_analyzer_agent import thought_analyzer_agent
from agents.agent import Agent
from agents.prompts.prompts import thought_agent_starting_message, response_analyzer_agent_message, thought_analyzer_agent_message, expert_knowledge_agent_message, thought_creator_agent_message
from agents.prompts.thought_agent.expert_knowledge_agent import expert_knowledge_agent


def extract_json_block(text):
    """Extract JSON block from text with ```json markers"""
    match = re.search(r"```json(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


class EnhancedMainAgent:
    """
    Enhanced MainAgent that exactly replicates main_agent.py logic with event forwarding.
    Handles conversation state, clarifications, and forwards ThoughtAgent events to UI.
    """
    
    def __init__(self, session_id: str, socketio_instance):
        self.session_id = session_id
        self.socketio = socketio_instance
        
        # Initialize agents exactly as in main_agent.py
        self.user_proxy_agent = Agent(**user_proxy_agent)
        self.thought_creator_agent = Agent(**thought_creator_agent)
        self.response_analyzer_agent = Agent(**response_analyzer_agent)
        self.thought_analyzer_agent = Agent(**thought_analyzer_agent)
        self.expert_knowledge_agent = Agent(**expert_knowledge_agent)

        # State management exactly as in main_agent.py
        self.thought_agents = {}
        self.completed_agents = {}
        self.discarded_agents = {}
        self.final_responses = {}
        self.messages = []
        
        print(f"[EnhancedMainAgent] Initialized for session: {session_id}")
    
    def run(self, user_query):
        """
        Main run method - exactly replicates main_agent.py logic
        Handles both initial queries and follow-ups with conversation state
        """
        try:
            return self._run_with_orchestration(user_query)
        except Exception as e:
            print(f"[EnhancedMainAgent] Error running query: {e}")
            self.socketio.emit('conversation_error', {
                'error': str(e),
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            raise
    
    def _run_with_orchestration(self, user_query):
        """Wrapper method for MainAgentService compatibility"""
        # Add user query to conversation history (exactly as main_agent.py)
        self.messages.append({"role": "user", "content": user_query})
        
        # Emit user message to UI
        self._emit_agent_message('user', 'User', user_query, '#007bff', 'user_query')
        
        # Get expert knowledge (exactly as main_agent.py)
        expert_knowledge = self._get_expert_knowledge()
        
        # Branch based on whether thought_agents exist (exactly as main_agent.py)
        if not self.thought_agents:
            # Initial query path
            return self._handle_initial_query(user_query, expert_knowledge)
        else:
            # Follow-up query path
            return self._handle_followup_query(user_query, expert_knowledge)
    
    def _get_expert_knowledge(self):
        """Get expert knowledge - exactly as main_agent.py"""
        self._emit_agent_started('expert_knowledge_agent', 'Expert Knowledge', '#6f42c1')
        
        self.user_proxy_agent.agent.send(
            recipient=self.expert_knowledge_agent.agent,
            message=expert_knowledge_agent_message.format(
                conversation_history_user=json.dumps(self.extract_role_messages("user")),
            ),
            request_reply=True
        )
        expert_knowledge = self.user_proxy_agent.agent._oai_messages[self.expert_knowledge_agent.agent][-1]["content"]
        
        self._emit_agent_message('expert_knowledge_agent', 'Expert Knowledge', expert_knowledge, '#6f42c1', 'expert_analysis')
        return expert_knowledge
    
    def _handle_initial_query(self, user_query, expert_knowledge):
        """Handle initial query - exactly as main_agent.py"""
        # Use thought_creator_agent to create thoughts
        self._emit_agent_started('thought_creator_agent', 'Thought Creator', '#28a745')
        
        self.user_proxy_agent.agent.send(
            recipient=self.thought_creator_agent.agent,
            message=thought_creator_agent_message.format(
                conversation_history=json.dumps(self.messages),
                expert_knowledge=json.dumps(expert_knowledge)
            ),
            request_reply=True
        )
        user_reply = self.user_proxy_agent.agent._oai_messages[self.thought_creator_agent.agent][-1]["content"]
        
        self._emit_agent_message('thought_creator_agent', 'Thought Creator', user_reply, '#28a745', 'thought_creation')
        
        # Check if user reply contains ```json or not (exactly as main_agent.py)
        if "```json" in user_reply:
            try:
                json_content = extract_json_block(user_reply)
                if json_content:
                    json_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_content)
                    thoughts = json.loads(json_clean)["thought_paths"]
                    print(f"[EnhancedMainAgent] Extracted thoughts: {thoughts}")
                else:
                    user_reply = "Could not extract JSON block."
                    self.messages.append({"role": "assistant", "content": user_reply})
                    return user_reply
            except json.JSONDecodeError:
                user_reply = "Invalid JSON format in user reply."
                self.messages.append({"role": "assistant", "content": user_reply})
                return user_reply
        else:
            # No JSON means clarification needed - return directly to user (exactly as main_agent.py)
            self.messages.append({"role": "assistant", "content": user_reply})
            self._emit_agent_message('system', 'System', user_reply, '#6c757d', 'clarification_request')
            return user_reply
        
        # Create thought agents for each thought (exactly as main_agent.py)
        if thoughts:
            for thought in thoughts:
                print(f"[EnhancedMainAgent] Creating thought agent for: {thought['name']}")
                thought_agent = self._create_enhanced_thought_agent(thought['name'])
                self.thought_agents[thought["name"]] = {
                    "agent": thought_agent,
                    "thought": thought
                }
            
            # Run thought agents (exactly as main_agent.py)
            responses = self.run_thought_agents(user_query)
            
            # Store responses (exactly as main_agent.py)
            for agent_name in self.thought_agents:
                self.final_responses[agent_name] = responses.get(agent_name, None)
            
            # Call response analyzer agent (exactly as main_agent.py)
            user_reply = self.call_response_analyzer_agent(user_query)
            self.messages.append({"role": "assistant", "content": user_reply})
            return user_reply
        
        return "No valid thoughts were generated."
    
    def _handle_followup_query(self, user_query, expert_knowledge):
        """Handle follow-up query - exactly as main_agent.py"""
        # Use thought_analyzer_agent for follow-ups
        self._emit_agent_started('thought_analyzer_agent', 'Thought Analyzer', '#fd7e14')
        
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
        
        self._emit_agent_message('thought_analyzer_agent', 'Thought Analyzer', user_reply, '#fd7e14', 'thought_analysis')
        
        # Process analysis result (exactly as main_agent.py)
        if "```json" in user_reply:
            try:
                json_content = extract_json_block(user_reply)
                if json_content:
                    json_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_content)
                    thought_agent_updates = json.loads(json_clean)
                    continue_agents = thought_agent_updates.get("continue_agents", [])
                    discard_agents = thought_agent_updates.get("discard_agents", [])
                    finalize_agents = thought_agent_updates.get("final_response_agents", [])
                    new_agents = thought_agent_updates.get("new_agents", [])

                    # Update agent states exactly as main_agent.py
                    for agent_name in discard_agents:
                        if agent_name in self.thought_agents:
                            self.discarded_agents[agent_name] = self.thought_agents.pop(agent_name)
                            if agent_name in self.final_responses:
                                del self.final_responses[agent_name]

                    for agent_name in finalize_agents:
                        if agent_name in self.thought_agents:
                            self.completed_agents[agent_name] = self.thought_agents.pop(agent_name)

                    # Add new agents
                    for thought in new_agents:
                        thought_agent = self._create_enhanced_thought_agent(thought['name'])
                        self.thought_agents[thought["name"]] = {
                            "agent": thought_agent,
                            "thought": thought
                        }

            except Exception as e:
                print(f"[EnhancedMainAgent] Error processing follow-up JSON: {e}")
                user_reply = "Invalid JSON format in user reply."
        
        # Run thought agents and synthesize response (exactly as main_agent.py)
        responses = self.run_thought_agents(user_query)
        
        for agent_name in self.thought_agents:
            self.final_responses[agent_name] = responses.get(agent_name, None)
        
        user_reply = self.call_response_analyzer_agent(user_query)
        self.messages.append({"role": "assistant", "content": user_reply})
        return user_reply
    
    def _create_enhanced_thought_agent(self, thought_name):
        """Create an EnhancedThoughtAgent for a specific thought with event forwarding"""
        from web_interface.services.agent_service import EnhancedThoughtAgent
        
        agent_metadata = {
            'user_proxy_agent': {'color': '#007bff', 'display_name': 'User Proxy'},
            'research_planner_agent': {'color': '#28a745', 'display_name': 'Research Planner'},
            'expert_knowledge_agent': {'color': '#6f42c1', 'display_name': 'Expert Knowledge'},
            'websearch_and_crawl_agent': {'color': '#fd7e14', 'display_name': 'Web Search & Crawl'},
            'coder_agent': {'color': '#dc3545', 'display_name': 'Coder'},
            'code_executor_agent': {'color': '#17a2b8', 'display_name': 'Code Executor'},
            'send_user_msg_agent': {'color': '#6c757d', 'display_name': 'Response Formatter'}
        }
        
        # Keep separate session ID for isolation but create event forwarding
        thought_session_id = f"{self.session_id}_thought_{thought_name}"
        
        # Create event forwarding callback
        def event_forwarder(event_type, event_data):
            """Forward ThoughtAgent events to MainAgent session with proper metadata"""
            self._forward_thought_agent_event(event_type, event_data, thought_name)
        
        return EnhancedThoughtAgent(
            session_id=thought_session_id,
            socketio_instance=self.socketio,
            agent_metadata=agent_metadata,
            event_forwarder=event_forwarder  # NEW: Pass forwarding callback
        )
    
    def _forward_thought_agent_event(self, event_type, event_data, thought_name):
        """
        Forward ThoughtAgent events to MainAgent session with proper metadata
        This ensures ThoughtAgent internal events reach the UI
        """
        # Add hierarchical metadata for proper frontend routing
        forwarded_data = event_data.copy()
        forwarded_data.update({
            'level': 'thought_agent',
            'thought_agent_id': thought_name,
            'parent_context': 'main_agent'
        })
        
        print(f"[EnhancedMainAgent] Forwarding {event_type} from ThoughtAgent: {thought_name}")
        
        # Emit to main session for UI display
        self.socketio.emit(event_type, forwarded_data, room=self.session_id)
    
    def extract_role_messages(self, role):
        """Extract messages by role - exactly as main_agent.py"""
        return [msg for msg in self.messages if msg["role"] == role]
    
    def call_response_analyzer_agent(self, user_query):
        """Call response analyzer agent - exactly as main_agent.py"""
        self._emit_agent_started('response_analyzer_agent', 'Response Analyzer', '#e83e8c')
        
        self.user_proxy_agent.agent.send(
            recipient=self.response_analyzer_agent.agent,
            message=response_analyzer_agent_message.format(
                user_query=user_query,
                responses=json.dumps(self.final_responses)
            ),
            request_reply=True
        )
        user_reply = self.user_proxy_agent.agent._oai_messages[self.response_analyzer_agent.agent][-1]["content"]
        
        self._emit_agent_message('response_analyzer_agent', 'Response Analyzer', user_reply, '#e83e8c', 'final_synthesis')
        return user_reply
    
    def run_thought_agents(self, user_query):
        """Run thought agents sequentially - exactly as main_agent.py"""
        responses = {}
        for name, agent_info in self.thought_agents.items():
            try:
                print(f"[EnhancedMainAgent] Running ThoughtAgent: {name}")
                
                # Emit ThoughtAgent container creation
                self._emit_thought_agent_lifecycle('create', name, agent_info["thought"])
                self._emit_thought_agent_lifecycle('start', name, agent_info["thought"])
                
                response = agent_info["agent"].run(
                    starting_msg=thought_agent_starting_message.format(
                        thought=agent_info["thought"],
                        user_query=user_query
                    )
                )
                responses[name] = response
                
                # Emit ThoughtAgent completion
                self._emit_thought_agent_lifecycle('complete', name, agent_info["thought"], response)
                
            except Exception as exc:
                print(f"[EnhancedMainAgent] Error in ThoughtAgent {name}: {exc}")
                responses[name] = f"Error: {exc}"
                self._emit_thought_agent_lifecycle('error', name, agent_info["thought"], None, str(exc))
        
        return responses
    
    def _emit_thought_agent_lifecycle(self, action, thought_name, thought_data, response=None, error=None):
        """Emit ThoughtAgent lifecycle events for UI container management"""
        lifecycle_data = {
            'action': action,
            'thought_agent_id': thought_name,
            'thought_data': thought_data,
            'timestamp': datetime.now().isoformat()
        }
        
        if response:
            lifecycle_data['response'] = response
        if error:
            lifecycle_data['error'] = error
            
        self.socketio.emit('thought_agent_lifecycle', lifecycle_data, room=self.session_id)
    
    def _emit_agent_started(self, agent_name, display_name, color):
        """Emit agent started event"""
        self.socketio.emit('agent_started', {
            'agent_name': agent_name,
            'display_name': display_name,
            'color': color,
            'timestamp': datetime.now().isoformat()
        }, room=self.session_id)
    
    def _emit_agent_message(self, agent_name, display_name, content, color, message_type):
        """Emit agent message event"""
        self.socketio.emit('agent_message', {
            'agent_name': agent_name,
            'display_name': display_name,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'type': message_type
        }, room=self.session_id)
