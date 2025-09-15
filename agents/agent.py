import autogen
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent

from utils.aoai_chat import model_config
from agents.custom_agents.expert_knowledge import Expert_Knowledge_Agent
from agents.custom_agents.websearch_and_crawl import WebSearch_And_Crawl_Agent
from agents.custom_agents.db_search_and_crawl import DB_Search_And_Crawl_Agent

class Agent:
    def __init__(self, type, name, description, system_message, human_input_mode="NEVER", code_execution_config = False, llm_config=True, retrieve_config = False):
        
        self.type = type
        self.name = name
        self.description = description
        self.system_message = system_message
        self.human_input_mode = human_input_mode
        self.code_execution_config = code_execution_config
        self.llm_config = llm_config
        if self.llm_config:
            self.llm_config = model_config
        
        if retrieve_config:
            self.retrieve_config = retrieve_config
            
        self.agent = self.create_agent()

    def create_agent(self):
        if self.type == "user_proxy":
            return autogen.UserProxyAgent(
                name=self.name,
                llm_config=False,
                description=self.description,
                human_input_mode="ALWAYS",  # Does not require human input.
                code_execution_config=False
            )
        elif self.type == "conversable":
            return autogen.ConversableAgent(
                name=self.name,
                system_message=self.system_message,
                llm_config=self.llm_config,
                description=self.description,
                human_input_mode=self.human_input_mode,
                code_execution_config=self.code_execution_config
            )
        elif self.type == "assistant":
            return autogen.AssistantAgent(
                name=self.name,
                system_message=self.system_message,
                llm_config=self.llm_config,
                description=self.description,
                human_input_mode=self.human_input_mode,
                code_execution_config=self.code_execution_config
            )
        elif self.type == "retriever":
            return RetrieveUserProxyAgent(
                name=self.name,
                system_message=self.system_message,
                llm_config=self.llm_config,
                description=self.description,
                human_input_mode=self.human_input_mode,
                code_execution_config=self.code_execution_config,
                retrieve_config=self.retrieve_config
            )
        
        elif self.type == "expert_knowledge":
            return Expert_Knowledge_Agent(
                n_iters=2,
                name=self.name,
                system_message=self.system_message,
                llm_config=self.llm_config,
                description=self.description,
                human_input_mode=self.human_input_mode,
                code_execution_config=self.code_execution_config
            )
        elif self.type == "websearch_and_crawl":
            return WebSearch_And_Crawl_Agent(
                # n_iters=10,
                name=self.name,
                system_message=self.system_message,
                llm_config=self.llm_config,
                description=self.description,
                human_input_mode=self.human_input_mode,
                code_execution_config=self.code_execution_config
            )
        elif self.type == "db_search_and_crawl":
            return DB_Search_And_Crawl_Agent(
                # n_iters=10,
                name=self.name,
                system_message=self.system_message,
                llm_config=self.llm_config,
                description=self.description,
                human_input_mode=self.human_input_mode,
                code_execution_config=self.code_execution_config
            )
        
