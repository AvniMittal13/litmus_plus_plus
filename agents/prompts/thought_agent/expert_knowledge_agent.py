from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
load_dotenv()

openai_embedding_function = embedding_functions.OpenAIEmbeddingFunction(api_key = os.getenv("OPENAI_API_KEY"), model_name=os.getenv("OPENAI_EMBEDDING_MODEL"))
text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n", "\n", "\r", "\t"])

# description = """
# It has expert knowledge on how an actual researcher approaches the problem statement, what data they collect, how they structure the data, and how they analyze the data. It can be used to get expert knowledge on a topic and information about how to proceed to the next step in a research project.
# """

description = """
Provides expert-level knowledge on research topics and guidance on next steps, simulating the approach of an experienced PhD researcher in a multilingual domain. Always invoked first for new queries or when the path forward is unclear and any clarifications are needed. Its output informs the `research_planner_agent` on how to plan and proceed with the research.
"""

# system_message = """
# You are an expert knowledge agent. You have access to a large corpus of knowledge and can provide expert knowledge on a wide range of topics. You can also provide information about how to proceed to the next step in a research project. Based on the user query, you can provide expert knowledge on the topic and information about how to proceed to the next step in a research project.
# If you can't find relevant information then tell so.
# """

system_message = """
You are the Expert Knowledge Agent, providing guidance like an experienced PhD researcher in a multilingual domain.  

- You have access to a large corpus of knowledge and can provide expert insights on a wide range of topics.  
- Your role is to guide the next steps in a research project, including what data to collect, how to structure it, and how to analyze it.  
- If relevant information cannot be found, clearly state that.  
- Your response will be used by the `research_planner_agent` to plan the next steps effectively.  
"""

expert_knowledge_agent = {
    "type": "expert_knowledge",
    "name": "expert_knowledge_agent",
    "system_message": system_message,
    "description": description,
    "human_input_mode": "NEVER",
    "code_execution_config":False
}

# expert_knowledge_agent = {
#     "type": "retriever",
#     "name": "expert_knowledge_agent",
#     "system_message": system_message,
#     "description": description,
#     "human_input_mode": "NEVER",
#     "code_execution_config":False,

#     "retrieve_config":{
#         "task": "qa",        
#         "docs_path": "knowledge/expert_knowledge.pdf",
#         "chunk_token_size": 1000,
#         "collection_name": "groupchat",
#         "get_or_create": True,
#         "embedding_function": openai_embedding_function,
#         "custom_text_split_function": text_splitter.split_text,
#     },
# }