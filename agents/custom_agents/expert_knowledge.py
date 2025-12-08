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

# print("expert knowledge: ", os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING"), os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDING"))
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


        assistant = AssistantAgent(
            name="assistant",
            system_message="""
You are the Expert Knowledge Agent, providing guidance like an experienced PhD researcher in a multilingual domain.  

- You have access to a large corpus of expert knowledge about steps taken by expert researchers in multilingual nlp contexts. Based on the query and retreived results provide expert knowledge about what should be done next.
- Your results are used for planning an **effective research strategy**.
- Your role is to guide the next steps in a research project, including what data to collect, how to generate features, what features to collect in such a situation, how to structure it, and how to analyze it.
- If relevant expert information on how to proceed further cannot be found, clearly state that.
- Your response will be used to plan the next steps effectively.
- You only tell based on output of `ragproxyagent` which searches and gives you relevent piece of context. Use that as your source of groundtruth.
""",
            llm_config=model_config,
        )
        ragproxyagent = RetrieveUserProxyAgent(
            name="ragproxyagent",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
            retrieve_config={
                "task": "default",
                "docs_path": [
                    # "https://raw.githubusercontent.com/microsoft/FLAML/main/website/docs/Examples/Integrate%20-%20Spark.md",
                    # "https://raw.githubusercontent.com/microsoft/FLAML/main/website/docs/Research.md",
                    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "knowledge.md")
                    # os.path.join(os.path.abspath(""), "..", "website", "docs"),
                ],
                "custom_text_types": ["mdx"],
                "chunk_token_size": 1000,
                "vector_db": "chroma",
                "collection_name": "expert_knowledge_new",
                "model": model_config["config_list"][0]["model"],
                # "model": os.getenv("OPENAI_EMBEDDING_MODEL"),
                "client": chromadb.PersistentClient(path="./tmp/db"),
                # "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL"),
                "embedding_function": openai_embedding_function,
                "embedding_model": "text-embedding-ada-002",
                "override": True,
                "get_or_create": True,  # set to False if you don't want to reuse an existing collection, but you'll need to remove the collection manually
            },
            code_execution_config=False,  # set to False if you don't want to execute the code
        )

        # code_problem = "What to do when no dataset available for a language?"
        ragproxyagent.initiate_chat(
            assistant, message=ragproxyagent.message_generator, problem=user_question,
            #   search_string="spark"
        )  


        print("RAG Proxy Agent Messages:", ragproxyagent._oai_messages)
        response = ragproxyagent._oai_messages[assistant][-1]["content"]


        return True, response