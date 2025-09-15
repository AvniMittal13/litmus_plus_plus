"""
Enhanced Main Agent - Full Orchestration Pattern
Implements proper MainAgent workflow with thought creation, multi-agent coordination, and response synthesis
"""

import sys
import os
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import original MainAgent components
from agents.agent import Agent
from agents.prompts.main_agent.user_proxy_agent import user_proxy_agent
from agents.prompts.main_agent.thought_creator_agent import thought_creator_agent
from agents.prompts.main_agent.response_analyzer_agent import response_analyzer_agent
from agents.prompts.main_agent.thought_analyzer_agent import thought_analyzer_agent
from agents.prompts.thought_agent.expert_knowledge_agent import expert_knowledge_agent
from agents.prompts.prompts import thought_agent_starting_message, response_analyzer_agent_message, thought_analyzer_agent_message, expert_knowledge_agent_message, thought_creator_agent_message


def extract_json_block(text):
    """Extract JSON block from text with ```json markers"""
    match = re.search(r"```json(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


class EnhancedMainAgent:
    """
    Enhanced MainAgent implementing proper orchestration workflow:
    1. Thought Creation - Generate multiple research paths
    2. Multi-Agent Coordination - Run multiple ThoughtAgents
    3. Response Synthesis - Combine and analyze results
    4. Iterative Refinement - Handle follow-up queries
    """
    
    def __init__(self, session_id: str, socketio_instance):
        self.session_id = session_id
        self.socketio = socketio_instance
        
        # Initialize MainAgent orchestration components
        self.user_proxy_agent = Agent(**user_proxy_agent)
        self.thought_creator_agent = Agent(**thought_creator_agent)
        self.response_analyzer_agent = Agent(**response_analyzer_agent)
        self.thought_analyzer_agent = Agent(**thought_analyzer_agent)
        self.expert_knowledge_agent = Agent(**expert_knowledge_agent)
        
        # Thought agent management
        self.thought_agents = {}
        self.completed_agents = {}
        self.discarded_agents = {}
        self.final_responses = {}
        
        # Conversation history
        self.messages = []
        
        print(f"[EnhancedMainAgent] Initialized orchestration for session: {session_id}")
    
    def run(self, user_query):
        """Public interface for running queries with full orchestration"""
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
        """
        Main orchestration workflow implementing proper MainAgent pattern:
        1. Expert knowledge gathering
        2. Thought creation or analysis  
        3. Multi-ThoughtAgent execution
        4. Response synthesis
        """
        try:
            print(f"[EnhancedMainAgent] Starting orchestration for: {user_query}")
            
            # Add user query to conversation history
            self.messages.append({"role": "user", "content": user_query})
            
            # Step 1: Gather expert knowledge context
            expert_knowledge = self._gather_expert_knowledge()
            
            # Step 2: Determine if this is initial query or follow-up
            if not self.thought_agents:
                # Initial query - create thought paths
                return self._handle_initial_query(user_query, expert_knowledge)
            else:
                # Follow-up query - analyze and refine existing thoughts
                return self._handle_followup_query(user_query, expert_knowledge)
                
        except Exception as e:
            print(f"[EnhancedMainAgent] Error in orchestration: {e}")
            import traceback
            print(f"[EnhancedMainAgent] Traceback: {traceback.format_exc()}")
            
            # Emit error with details
            self.socketio.emit('conversation_error', {
                'error': f'MainAgent orchestration failed: {str(e)}',
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat()
            }, room=self.session_id)
            
            return f"I apologize, but I encountered an error processing your request: {str(e)}"
    
    def _gather_expert_knowledge(self):
        """Gather expert knowledge context for the query"""
        print(f"[EnhancedMainAgent] Gathering expert knowledge...")
        
        self.socketio.emit('agent_started', {
            'agent_name': 'expert_knowledge_agent',
            'display_name': 'Expert Knowledge',
            'color': '#6f42c1',
            'timestamp': datetime.now().isoformat()
        }, room=self.session_id)
        
        try:
            self.user_proxy_agent.agent.send(
                recipient=self.expert_knowledge_agent.agent,
                message=expert_knowledge_agent_message.format(
                    conversation_history_user=json.dumps(self.extract_role_messages("user")),
                ),
                request_reply=True
            )
            expert_knowledge = self.user_proxy_agent.agent._oai_messages[self.expert_knowledge_agent.agent][-1]["content"]
            
            self.socketio.emit('agent_message', {
                'agent_name': 'expert_knowledge_agent',
                'display_name': 'Expert Knowledge',
                'content': expert_knowledge,
                'timestamp': datetime.now().isoformat(),
                'type': 'expert_analysis'
            }, room=self.session_id)
            
            return expert_knowledge
            
        except Exception as e:
            print(f"[EnhancedMainAgent] Error gathering expert knowledge: {e}")
            return "No expert knowledge available"
    
    def _handle_initial_query(self, user_query, expert_knowledge):
        """Handle initial query by creating thought paths and running ThoughtAgents"""
        print(f"[EnhancedMainAgent] Handling initial query - creating thought paths...")
        
        # Step 1: Create thought paths using thought_creator_agent
        thoughts = self._create_thought_paths(user_query, expert_knowledge)
        
        if not thoughts:
            # If no thoughts created, return direct response
            return "I need more information to provide a comprehensive analysis. Could you please provide more details about your query?"
        
        # Step 2: Create ThoughtAgents for each thought path
        self._create_thought_agents(thoughts)
        
        # Step 3: Run all ThoughtAgents
        responses = self._run_thought_agents(user_query)
        
        # Step 4: Store responses and synthesize final answer
        for agent_name in self.thought_agents:
            self.final_responses[agent_name] = responses.get(agent_name, None)
        
        # Step 5: Analyze and synthesize responses
        final_response = self._synthesize_responses(user_query)
        self.messages.append({"role": "assistant", "content": final_response})
        return final_response
    
    def _create_thought_paths(self, user_query, expert_knowledge):
        """Create thought paths using thought_creator_agent"""
        print(f"[EnhancedMainAgent] Creating thought paths...")
        
        self.socketio.emit('agent_started', {
            'agent_name': 'thought_creator_agent',
            'display_name': 'Thought Creator',
            'color': '#28a745',
            'timestamp': datetime.now().isoformat()
        }, room=self.session_id)
        
        try:
            self.user_proxy_agent.agent.send(
                recipient=self.thought_creator_agent.agent,
                message=thought_creator_agent_message.format(
                    conversation_history=json.dumps(self.messages),
                    expert_knowledge=json.dumps(expert_knowledge)
                ),
                request_reply=True
            )
            user_reply = self.user_proxy_agent.agent._oai_messages[self.thought_creator_agent.agent][-1]["content"]
            
            self.socketio.emit('agent_message', {
                'agent_name': 'thought_creator_agent',
                'display_name': 'Thought Creator',
                'content': user_reply,
                'timestamp': datetime.now().isoformat(),
                'type': 'thought_creation'
            }, room=self.session_id)
            
            # Extract JSON thought paths
            if "```json" in user_reply:
                try:
                    json_content = extract_json_block(user_reply)
                    if json_content:
                        json_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_content)
                        thoughts = json.loads(json_clean)["thought_paths"]
                        print(f"[EnhancedMainAgent] Created {len(thoughts)} thought paths")
                        return thoughts
                except json.JSONDecodeError as e:
                    print(f"[EnhancedMainAgent] JSON decode error: {e}")
                    return None
            else:
                # If no JSON, this is a clarification request
                return None
                
        except Exception as e:
            print(f"[EnhancedMainAgent] Error creating thought paths: {e}")
            return None
    
    def _create_thought_agents(self, thoughts):
        """Create EnhancedThoughtAgent instances for each thought path"""
        print(f"[EnhancedMainAgent] Creating ThoughtAgents for {len(thoughts)} thought paths...")
        
        from web_interface.services.agent_service import EnhancedThoughtAgent
        
        # Basic agent metadata
        agent_metadata = {
            'user_proxy_agent': {'color': '#007bff', 'display_name': 'User Proxy'},
            'research_planner_agent': {'color': '#28a745', 'display_name': 'Research Planner'},
            'expert_knowledge_agent': {'color': '#6f42c1', 'display_name': 'Expert Knowledge'},
            'websearch_and_crawl_agent': {'color': '#fd7e14', 'display_name': 'Web Search & Crawl'},
            'coder_agent': {'color': '#dc3545', 'display_name': 'Coder'},
            'code_executor_agent': {'color': '#17a2b8', 'display_name': 'Code Executor'},
            'send_user_msg_agent': {'color': '#6c757d', 'display_name': 'Response Formatter'}
        }
        
        for thought in thoughts:
            thought_name = thought["name"]
            print(f"[EnhancedMainAgent] Creating ThoughtAgent: {thought_name}")
            
            # Create unique session ID for this thought agent
            thought_session_id = f"{self.session_id}_thought_{thought_name}"
            
            # Create EnhancedThoughtAgent instance
            thought_agent = EnhancedThoughtAgent(
                session_id=thought_session_id,
                socketio_instance=self.socketio,
                agent_metadata=agent_metadata
            )
            
            self.thought_agents[thought_name] = {
                "agent": thought_agent,
                "thought": thought
            }
    
    def _run_thought_agents(self, user_query):
        """Run all ThoughtAgents sequentially and collect responses"""
        print(f"[EnhancedMainAgent] Running {len(self.thought_agents)} ThoughtAgents...")
        
        responses = {}
        for name, agent_info in self.thought_agents.items():
            try:
                print(f"[EnhancedMainAgent] Running ThoughtAgent: {name}")
                
                # Emit starting message for this thought agent
                self.socketio.emit('agent_started', {
                    'agent_name': f'thought_agent_{name}',
                    'display_name': f'Thought Agent: {name}',
                    'color': '#17a2b8',
                    'timestamp': datetime.now().isoformat()
                }, room=self.session_id)
                
                # Run the ThoughtAgent with the specific thought context
                starting_msg = thought_agent_starting_message.format(
                    thought=agent_info["thought"],
                    user_query=user_query
                )
                
                response = agent_info["agent"].run(starting_msg)
                responses[name] = response
                
                print(f"[EnhancedMainAgent] Completed ThoughtAgent: {name}")
                
            except Exception as exc:
                print(f"[EnhancedMainAgent] Error in ThoughtAgent {name}: {exc}")
                responses[name] = f"Error: {exc}"
                
        return responses
    
    def _synthesize_responses(self, user_query):
        """Synthesize responses from all ThoughtAgents using response_analyzer_agent"""
        print(f"[EnhancedMainAgent] Synthesizing responses from {len(self.final_responses)} ThoughtAgents...")
        
        self.socketio.emit('agent_started', {
            'agent_name': 'response_analyzer_agent',
            'display_name': 'Response Analyzer',
            'color': '#e83e8c',
            'timestamp': datetime.now().isoformat()
        }, room=self.session_id)
        
        try:
            self.user_proxy_agent.agent.send(
                recipient=self.response_analyzer_agent.agent,
                message=response_analyzer_agent_message.format(
                    user_query=user_query,
                    responses=json.dumps(self.final_responses)
                ),
                request_reply=True
            )
            final_response = self.user_proxy_agent.agent._oai_messages[self.response_analyzer_agent.agent][-1]["content"]
            
            self.socketio.emit('agent_message', {
                'agent_name': 'response_analyzer_agent',
                'display_name': 'Response Analyzer',
                'content': final_response,
                'timestamp': datetime.now().isoformat(),
                'type': 'final_synthesis'
            }, room=self.session_id)
            
            return final_response
            
        except Exception as e:
            print(f"[EnhancedMainAgent] Error synthesizing responses: {e}")
            return "I encountered an error while synthesizing the research results."
    
    def _handle_followup_query(self, user_query, expert_knowledge):
        """Handle follow-up queries by analyzing existing thoughts and potentially creating new ones"""
        print(f"[EnhancedMainAgent] Handling follow-up query...")
        
        self.socketio.emit('agent_started', {
            'agent_name': 'thought_analyzer_agent',
            'display_name': 'Thought Analyzer',
            'color': '#fd7e14',
            'timestamp': datetime.now().isoformat()
        }, room=self.session_id)
        
        try:
            # Analyze current state and determine next actions
            self.user_proxy_agent.agent.send(
                recipient=self.thought_analyzer_agent.agent,
                message=thought_analyzer_agent_message.format(
                    responses=json.dumps(self.final_responses),
                    conversation_history=json.dumps(self.messages),
                    expert_knowledge=json.dumps(expert_knowledge)
                ),
                request_reply=True
            )
            analysis_result = self.user_proxy_agent.agent._oai_messages[self.thought_analyzer_agent.agent][-1]["content"]
            
            self.socketio.emit('agent_message', {
                'agent_name': 'thought_analyzer_agent',
                'display_name': 'Thought Analyzer',
                'content': analysis_result,
                'timestamp': datetime.now().isoformat(),
                'type': 'thought_analysis'
            }, room=self.session_id)
            
            # Process the analysis result
            if "```json" in analysis_result:
                try:
                    json_content = extract_json_block(analysis_result)
                    if json_content:
                        json_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_content)
                        thought_updates = json.loads(json_clean)
                        
                        # Apply the updates
                        self._apply_thought_updates(thought_updates)
                        
                        # Re-run affected agents
                        responses = self._run_thought_agents(user_query)
                        
                        # Update responses
                        for agent_name in self.thought_agents:
                            self.final_responses[agent_name] = responses.get(agent_name, None)
                        
                        # Synthesize final response
                        final_response = self._synthesize_responses(user_query)
                        self.messages.append({"role": "assistant", "content": final_response})
                        return final_response
                        
                except json.JSONDecodeError as e:
                    print(f"[EnhancedMainAgent] JSON decode error in follow-up: {e}")
            
            # If no JSON analysis, return direct response
            self.messages.append({"role": "assistant", "content": analysis_result})
            return analysis_result
            
        except Exception as e:
            print(f"[EnhancedMainAgent] Error in follow-up analysis: {e}")
            return "I encountered an error while analyzing your follow-up query."
    
    def _apply_thought_updates(self, thought_updates):
        """Apply updates from thought_analyzer_agent"""
        print(f"[EnhancedMainAgent] Applying thought updates...")
        
        continue_agents = thought_updates.get("continue_agents", [])
        discard_agents = thought_updates.get("discard_agents", [])
        finalize_agents = thought_updates.get("final_response_agents", [])
        new_agents = thought_updates.get("new_agents", [])
        
        # Remove discarded agents
        for agent_name in discard_agents:
            if agent_name in self.thought_agents:
                self.discarded_agents[agent_name] = self.thought_agents.pop(agent_name)
                if agent_name in self.final_responses:
                    del self.final_responses[agent_name]
                print(f"[EnhancedMainAgent] Discarded ThoughtAgent: {agent_name}")
        
        # Move finalized agents to completed
        for agent_name in finalize_agents:
            if agent_name in self.thought_agents:
                self.completed_agents[agent_name] = self.thought_agents.pop(agent_name)
                print(f"[EnhancedMainAgent] Finalized ThoughtAgent: {agent_name}")
        
        # Add new agents
        if new_agents:
            self._create_thought_agents(new_agents)
            print(f"[EnhancedMainAgent] Created {len(new_agents)} new ThoughtAgents")
    
    def extract_role_messages(self, role):
        """Extract messages by role from conversation history"""
        return [msg for msg in self.messages if msg["role"] == role]
