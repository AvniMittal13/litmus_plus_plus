import os
import pickle
from dotenv import load_dotenv, dotenv_values
import shutil
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import AzureOpenAI

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

# Cache setup for expert knowledge responses
EXPERT_KNOWLEDGE_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "expert_knowledge_cache.pkl")
_expert_knowledge_cache = None

# Embedding client for cache
_embedding_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDING"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING"),
    api_version="2023-05-15"
)

def _get_query_embedding(text: str) -> list:
    """Get embedding for a query text."""
    try:
        resp = _embedding_client.embeddings.create(input=[text], model="text-embedding-ada-002")
        return resp.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def _load_expert_knowledge_cache() -> list:
    """Load cache from pickle file."""
    global _expert_knowledge_cache
    if _expert_knowledge_cache is not None:
        return _expert_knowledge_cache
    try:
        if os.path.exists(EXPERT_KNOWLEDGE_CACHE_PATH):
            with open(EXPERT_KNOWLEDGE_CACHE_PATH, 'rb') as f:
                _expert_knowledge_cache = pickle.load(f)
            print(f"Loaded expert knowledge cache with {len(_expert_knowledge_cache)} entries")
            return _expert_knowledge_cache
        else:
            _expert_knowledge_cache = []
            return _expert_knowledge_cache
    except Exception as e:
        print(f"Error loading expert knowledge cache: {e}")
        _expert_knowledge_cache = []
        return _expert_knowledge_cache

def _save_expert_knowledge_cache(query: str, embedding: list, response: str):
    """Save a new entry to the cache. Always loads from disk first to prevent data loss."""
    global _expert_knowledge_cache
    try:
        # Always load the latest cache from disk first (not in-memory) to prevent data loss
        existing_cache = []
        if os.path.exists(EXPERT_KNOWLEDGE_CACHE_PATH):
            try:
                with open(EXPERT_KNOWLEDGE_CACHE_PATH, 'rb') as f:
                    existing_cache = pickle.load(f)
                print(f"Loaded {len(existing_cache)} existing expert knowledge cache entries from disk")
            except Exception as e:
                print(f"Warning: Could not load existing expert knowledge cache: {e}")
                existing_cache = []

        # Deduplicate: skip if a similar query already exists
        existing_queries = {entry['query'].strip().lower() for entry in existing_cache if 'query' in entry}
        query_normalized = query.strip().lower()
        if query_normalized in existing_queries:
            print(f"Expert knowledge cache: query already exists, skipping duplicate")
            _expert_knowledge_cache = existing_cache
            return

        existing_cache.append({'query': query, 'embedding': embedding, 'response': response})
        with open(EXPERT_KNOWLEDGE_CACHE_PATH, 'wb') as f:
            pickle.dump(existing_cache, f)
        _expert_knowledge_cache = existing_cache
        print(f"Saved to expert knowledge cache: 1 new entry added, total {len(existing_cache)} entries")
    except Exception as e:
        print(f"Error saving to cache: {e}")

def _search_expert_knowledge_cache(query_embedding: list, threshold: float = 0.90) -> str:
    """Search cache for similar query. Returns cached response if similarity >= threshold."""
    cache = _load_expert_knowledge_cache()
    if not cache or query_embedding is None:
        return None
    
    best_similarity = 0.0
    best_response = None
    
    for item in cache:
        if item.get('embedding') is not None:
            sim = cosine_similarity([query_embedding], [item['embedding']])[0][0]
            if sim > best_similarity:
                best_similarity = sim
                best_response = item['response']
    
    if best_similarity >= threshold:
        print(f"Cache hit! Similarity: {best_similarity:.4f}")
        return best_response
    
    print(f"Cache miss. Best similarity: {best_similarity:.4f} (threshold: {threshold})")
    return None


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

        # Check cache first
        query_embedding = _get_query_embedding(user_question)
        cached_response = _search_expert_knowledge_cache(query_embedding, threshold=0.90)
        if cached_response:
            print("Returning cached expert knowledge response")
            return True, cached_response

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
                    "C:\\Users\\avnimittal\\OneDrive - Microsoft\\Desktop\\tp\\litmus_agent\\knowledge\\knowledge_2.md"
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

        # Save to cache
        if query_embedding is not None:
            _save_expert_knowledge_cache(user_question, query_embedding, response)

        return True, response