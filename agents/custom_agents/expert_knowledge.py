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
from utils.aoai_chat import model_config, get_embedding_function
from dotenv import load_dotenv
load_dotenv()

from chromadb.utils import embedding_functions

# Lazy-init: don't call get_embedding_function() at import time (causes crash on Azure if env vars aren't ready)
_openai_embedding_function = None

def _get_openai_embedding_function():
    global _openai_embedding_function
    if _openai_embedding_function is None:
        _openai_embedding_function = get_embedding_function()
    return _openai_embedding_function

# Keep backward compat reference (but now lazy)
openai_embedding_function = None


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
            system_message= """
You are the Expert Knowledge Agent, acting as a senior multilingual NLP researcher guiding another researcher through complex performance prediction or multilingual modeling challenges.

You have access to a corpus of expert research practices, experimental strategies, and multilingual NLP analysis guides via a RAG system. Based on retrieved passages from that knowledge base, your job is to translate the content into **clear, actionable next steps**.

### Your task:
- **Extract expert insights** from the retrieved content and **explain exactly how to proceed** in the current research scenario.
- Provide **step-by-step, structured guidance** covering:
  - What data to gather (e.g., benchmarks, features, corpora)
  - What features to compute (e.g., tokenizer metrics, typological distance, vocabulary overlap)
  - How to structure and organize the data for modeling
  - What modeling strategies are appropriate (e.g., regression, ranking, multi-task learning)
  - How to analyze and interpret the results (e.g., performance validation, feature importance)
- Where relevant, **highlight trade-offs, risks, and fallback options**.

### Response requirements:
- Your answer **must be detailed, specific, and logically structured**.
- DO NOT repeat retrieved passages — instead, synthesize them into **explicit research guidance**.
- If the retrieved results are not sufficient to recommend next steps, **clearly state that and explain why**.
- DONOT give code in your response
- Give instructions for reiterations.

Your goal is to **bridge expert knowledge with practical next actions**, so the researcher can confidently move forward with their experiment or modeling strategy.
Tell all details and best practices in a concise structured manner. Tell these according to the user query.
"""
       
            
            
            
#             """
# You are the Expert Knowledge Agent, providing guidance like an experienced PhD researcher in a multilingual domain.  

# - You have access to a large corpus of expert knowledge about steps taken by expert researchers in multilingual nlp contexts. Based on the query and retreived results provide expert knowledge about what should be done next.
# - Your results are used for planning an **effective research strategy**.
# - Your role is to guide the next steps in a research project, including what data to collect, how to generate features, what features to collect in such a situation, how to structure it, and how to analyze it.
# - If relevant expert information on how to proceed further cannot be found, clearly state that.
# - Your response will be used to plan the next steps effectively.
# - You only tell based on output of `ragproxyagent` which searches and gives you relevent piece of context. Use that as your source of groundtruth.
# """
,
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
                    # "C:\\Users\\avnimittal\\OneDrive - Microsoft\\Desktop\\tp\\litmus_agent\\knowledge\\knowledge.md",
                    # "C:\\Users\\avnimittal\\OneDrive - Microsoft\\Desktop\\tp\\litmus_agent\\knowledge\\knowledge_2.md"
                     os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "knowledge_2.md")
                    # os.path.join(os.path.abspath(""), "..", "website", "docs"),
                ],
                "custom_text_types": ["mdx"],
                "chunk_token_size": 1000,
                "vector_db": "chroma",
                "collection_name": "expert_knowledge_new2",
                "model": model_config["config_list"][0]["model"],
                # "model": os.getenv("OPENAI_EMBEDDING_MODEL"),
                "client": chromadb.PersistentClient(path="./tmp/db"),
                # "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL"),
                "embedding_function": _get_openai_embedding_function(),
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