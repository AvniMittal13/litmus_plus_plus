import os
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
import os
import chromadb
from utils.aoai_chat import model_config
from dotenv import load_dotenv
load_dotenv()

from chromadb.utils import embedding_functions


openai_embedding_function = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING"),
    model_name="text-embedding-ada-002",
    api_base=os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDING"),
    api_type="azure",
    api_version="2023-05-15",
    deployment_id="text-embedding-ada-002"
)


class Expert_Knowledge_Agent(ConversableAgent):
    def __init__(self, n_iters=2,**kwargs):
        """
        Initializes a Expert_Knowledge_Agent instance.

        This agent facilitates the creation of visualizations through a collaborative effort among its child agents: commander, coder, and critics.

        Parameters:
            - n_iters (int, optional): The number of "improvement" iterations to run. Defaults to 2.
            - **kwargs: keyword arguments for the parent AssistantAgent.
        """
        super().__init__(**kwargs)
        self.register_reply([Agent, None], reply_func=Expert_Knowledge_Agent._reply_user, position=0)
        self._n_iters = n_iters
        # self.img_name = img_name

    def _reply_user(self, messages=None, sender=None, config=None):
        if all((messages is None, sender is None)):
            error_msg = f"Either {messages=} or {sender=} must be provided."
            # logger.error(error_msg)  # noqa: F821
            raise AssertionError(error_msg)
        if messages is None:
            messages = self._oai_messages[sender]


        user_question = messages[-1]["content"]



        return True, response