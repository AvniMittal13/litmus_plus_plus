from agents.prompts.main_agent.user_proxy_agent import user_proxy_agent
from agents.prompts.main_agent.thought_creator_agent import thought_creator_agent
from agents.prompts.main_agent.response_analyzer_agent import response_analyzer_agent
from agents.prompts.main_agent.thought_analyzer_agent import thought_analyzer_agent

from agents.agent import Agent
from agents.thought_agent import ThoughtAgent
from agents.prompts.prompts import thought_agent_starting_message, response_analyzer_agent_message, thought_analyzer_agent_message, expert_knowledge_agent_message, thought_creator_agent_message
from agents.prompts.thought_agent.expert_knowledge_agent import expert_knowledge_agent

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


def extract_json_block(text):
    match = re.search(r"```json(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

class MainAgent:
    def __init__(self):
        self.user_proxy_agent = Agent(**user_proxy_agent)
        self.thought_creator_agent = Agent(**thought_creator_agent)
        self.response_analyzer_agent = Agent(**response_analyzer_agent)
        self.thought_analyzer_agent = Agent(**thought_analyzer_agent)
        self.expert_knowledge_agent = Agent(**expert_knowledge_agent)

        self.thought_agents = {}
        self.completed_agents = {}
        self.discarded_agents = {}
        self.final_responses = {}

        self.messages = []

    def run(self, user_query):

        '''
        user proxy agent --> to simulate user
        send_user_msg_agent --> to send messages to user, needed here also as final msg goes to user - needs to be summary or clarifications required

        thought_creator_agent --> to create thoughts and plan research. Think of different hypothesis or thought paths to search
        # give entire thought paths to the agent. path, as in try to think in this manner
        this is for creating new agents, adding new ones, disregarding old  ones 
            or merging --> need to see how to implement merging of chats/conversations.
            - to ensure all search information is not lost

        '''

        # first get any clarifications and generate initial thoughts
        # user proxy agent, send user msg agent and thought creator agent.

        # if self.thought_agents is empty dictionary then do
        self.messages.append({"role": "user", "content": user_query})

        self.user_proxy_agent.agent.send(
            recipient=self.expert_knowledge_agent.agent,
            message=expert_knowledge_agent_message.format(
                conversation_history_user=json.dumps(self.extract_role_messages("user")),
                
            ),
            request_reply=True
        )
        expert_knowledge = self.user_proxy_agent.agent._oai_messages[self.expert_knowledge_agent.agent][-1]["content"]

        if not self.thought_agents:
            self.user_proxy_agent.agent.send(
                recipient=self.thought_creator_agent.agent,
                message=thought_creator_agent_message.format(
                    conversation_history=json.dumps(self.messages),
                    expert_knowledge=json.dumps(expert_knowledge)
                ),
                request_reply=True
            )
            user_reply = self.user_proxy_agent.agent._oai_messages[self.thought_creator_agent.agent][-1]["content"]

            # check if user reply contains ```json or not. If yes then extract json content and use it. if no then return user_reply as is
            if "```json" in user_reply:
                try:
                    json_content = extract_json_block(user_reply)
                    if json_content:
                        json_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_content)
                        thoughts = json.loads(json_clean)["thought_paths"]

                        print(f"Extracted thoughts: {thoughts}")
                    else:
                        user_reply = "Could not extract JSON block."
                except json.JSONDecodeError:
                    user_reply = "Invalid JSON format in user reply."
            else:
                self.messages.append({"role":"assistant", "content": user_reply})
                return user_reply
            
            # if thoughts is not empty then create a new thought agent for each thought
            if thoughts:
                for thought in thoughts:
                    print(thought)
                    print(f"Creating thought agent for: {thought['name']}")
                    thought_agent = ThoughtAgent()
                    self.thought_agents[thought["name"]] = {
                        "agent": thought_agent,
                        "thought": thought
                    }

                responses = self.run_thought_agents(user_query)

                for agent_name in self.thought_agents:
                    self.final_responses[agent_name] = responses.get(agent_name, None)

                user_reply =  self.call_response_analyzer_agent(user_query)
                self.messages.append({"role":"assistant", "content": user_reply})
                return user_reply

        else:
            # if thoughts already exist, then send the user query to the thought analyzer agent
            self.user_proxy_agent.agent.send(
                recipient=self.thought_analyzer_agent.agent,
                message=thought_analyzer_agent_message.format(
                    responses = json.dumps(self.final_responses),
                    conversation_history = json.dumps(self.messages),
                    expert_knowledge = json.dumps(expert_knowledge)
                ),
                request_reply=True
            )
            user_reply = self.user_proxy_agent.agent._oai_messages[self.thought_analyzer_agent.agent][-1]["content"]

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


                        # Update agent states after response
                        # Remove discarded agents from thought_agents and add to discarded_agents
                        for agent_name in discard_agents:
                            if agent_name in self.thought_agents:
                                self.discarded_agents[agent_name] = self.thought_agents.pop(agent_name)
                                if agent_name in self.final_responses:
                                    del self.final_responses[agent_name]


                        # Remove finalized agents from thought_agents and add to completed_agents
                        for agent_name in finalize_agents:
                            if agent_name in self.thought_agents:
                                self.completed_agents[agent_name] = self.thought_agents.pop(agent_name)

                        # Add new agents to thought_agents
                        for thought in new_agents:
                            thought_agent = ThoughtAgent()
                            self.thought_agents[thought["name"]] = {
                                "agent": thought_agent,
                                "thought": thought
                            }

                except:
                    user_reply = "Invalid JSON format in user reply." 

        responses = self.run_thought_agents(user_query)

        # Update responses for all current thought agents
        for agent_name in self.thought_agents:
            self.final_responses[agent_name] = responses.get(agent_name, None)

        # summarize all responses, response analyzer agent
        user_reply = self.call_response_analyzer_agent(user_query)
        self.messages.append({"role":"assistant", "content": user_reply})
        return user_reply

    def extract_role_messages(self, role):
        return [msg for msg in self.messages if msg["role"] == role]

    def call_response_analyzer_agent(self, user_query):
        # Call the response analyzer agent to analyze the responses from thought agents
        self.user_proxy_agent.agent.send(
            recipient=self.response_analyzer_agent.agent,
            message=response_analyzer_agent_message.format(
                user_query=user_query,
                responses=json.dumps(self.final_responses)
            ),
            request_reply=True
        )
        user_reply = self.user_proxy_agent.agent._oai_messages[self.response_analyzer_agent.agent][-1]["content"]
        return user_reply

    def _run_thought_agents(self, user_query):
        # Run all thought agents in parallel and collect their responses
        responses = {}
        with ThreadPoolExecutor() as executor:
            future_to_name = {
                executor.submit(
                    agent_info["agent"].run,
                    starting_msg=thought_agent_starting_message.format(
                        thought=agent_info["thought"],
                        user_query=user_query
                    )
                ): name for name, agent_info in self.thought_agents.items()
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    responses[name] = future.result()
                except Exception as exc:
                    responses[name] = f"Error: {exc}"
        return responses

    def run_thought_agents(self, user_query):
        # Run all thought agents sequentially and collect their responses
        responses = {}
        for name, agent_info in self.thought_agents.items():
            try:
                response = agent_info["agent"].run(
                    starting_msg=thought_agent_starting_message.format(
                        thought=agent_info["thought"],
                        user_query=user_query
                    )
                )
                responses[name] = response
            except Exception as exc:
                responses[name] = f"Error: {exc}"
        return responses