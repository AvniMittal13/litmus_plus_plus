# initialise a class named ThoughtAgent which is an autogen groupchat. it has functions of run, create_groupchat, continue groupchat and so on
import autogen

from agents.groupchat import GroupChat
from agents.agent import Agent
from agents.prompts.thought_agent.research_planner_agent import research_planner_agent

# from agents.prompts.thought_agent.research_planner_agent_fire import research_planner_agent
# from agents.prompts.thought_agent.firecrawl_websearch_agent import firecrawl_websearch_agent
from agents.prompts.thought_agent.send_user_msg_agent import send_user_msg_agent
# from agents.prompts.thought_agent.call_firecrawl_websearch_agent import call_firecrawl_websearch_agent
from agents.prompts.thought_agent.user_proxy_agent import user_proxy_agent
from agents.prompts.thought_agent.coder_agent import coder_agent
from agents.prompts.thought_agent.code_executor_agent import code_executor_agent

from agents.prompts.thought_agent.expert_knowledge_agent import expert_knowledge_agent
from agents.prompts.thought_agent.db_search_and_crawl_agent import db_search_and_crawl_agent

from agents.tools.webcrawl import firecrawl_search_tool
from agents.prompts.prompts import thought_agent_final_message_format

print("res planner: ", research_planner_agent["description"])

class ThoughtAgent():
    def __init__(self):
        super().__init__()

        # Initialise agents using parameter dictionaries from prompts
        self.user_proxy_agent = Agent(**user_proxy_agent)
        self.send_user_msg_agent = Agent(**send_user_msg_agent)
        self.research_planner_agent = Agent(**research_planner_agent)
        # self.firecrawl_websearch_agent = Agent(**firecrawl_websearch_agent)
        # self.call_firecrawl_websearch_agent = Agent(**call_firecrawl_websearch_agent)
        self.coder_agent = Agent(**coder_agent)
        self.code_executor_agent = Agent(**code_executor_agent)
        self.expert_knowledge_agent = Agent(**expert_knowledge_agent)
        self.websearch_and_crawl_agent = Agent(**db_search_and_crawl_agent)


        # register any tools required by the agents
        # self.firecrawl_websearch_agent.agent.register_for_llm(
        #     name=firecrawl_search_tool["name"], 
        #     description=firecrawl_search_tool["description"]
        # )(firecrawl_search_tool["run_function"])

        # self.call_firecrawl_websearch_agent.agent.register_for_execution(
        #     name=firecrawl_search_tool["name"]
        # )(firecrawl_search_tool["run_function"])

        # Create a group chat with the agents
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


    def run(self, starting_msg):
        final_response, messages, summary = self.groupchat.run(starting_msg)
        return thought_agent_final_message_format.format(
            final_response=final_response,
            summary=summary
        )
    def create_groupchat(self):
        pass
    
    def continue_groupchat(self):
        pass

    def custom_speaker_selection_func(self, last_speaker, groupchat):
        if last_speaker == self.send_user_msg_agent.agent:
            return None
        if last_speaker == self.user_proxy_agent.agent:
            return self.research_planner_agent.agent
        # if last_speaker == self.firecrawl_websearch_agent.agent:
            # return self.call_firecrawl_websearch_agent.agent
        if last_speaker == self.coder_agent.agent:
            return self.code_executor_agent.agent
        return "auto"
