from os import getenv
from dotenv import load_dotenv
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage  
from openai import AzureOpenAI  
import os
import re

load_dotenv()

# Auth mode: set USE_API_KEY=true in env for deployment (API key), otherwise uses Azure AD locally
USE_API_KEY = os.getenv("USE_API_KEY", "false").lower() == "true"

if USE_API_KEY:
    print("[Auth] Using API key authentication (deployment mode)")
    token_provider = None
    
    def get_embed_token():
        """Return API key for embedding calls in deployment mode"""
        return os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING") or os.getenv("OPENAI_API_KEY")
else:
    print("[Auth] Using Azure AD token authentication (local mode)")
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    _credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        _credential, "https://cognitiveservices.azure.com/.default"
    )
    
    def get_embed_token():
        """Get a fresh Azure AD token for embedding calls"""
        token = _credential.get_token("https://cognitiveservices.azure.com/.default")
        return token.token


def get_embedding_function():
    """Return the correct ChromaDB embedding function based on auth mode"""
    from chromadb.utils import embedding_functions
    if USE_API_KEY:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("AZURE_OPENAI_API_KEY_EMBEDDING"),
            model_name="text-embedding-ada-002",
            api_base=os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDING"),
            api_type="azure",
            api_version="2023-05-15",
            deployment_id="text-embedding-ada-002"
        )
    else:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=get_embed_token(),
            model_name="text-embedding-ada-002",
            api_base=os.getenv("AZURE_OPENAI_ENDPOINT_EMBEDDING"),
            api_type="azure",
            api_version="2023-05-15",
            deployment_id="text-embedding-ada-002"
        )

def get_env(key, opt=None):
    return getenv(key, opt)

def get_current_config():

    model = get_env("OPENAI_DEPLOYMENT_NAME")
    if "deepseek" in model.lower():
        t = {
            "model": get_env("OPENAI_DEPLOYMENT_NAME"),
            "api_key": get_env("OPENAI_API_KEY"),
            "base_url": get_env("OPENAI_BASE_URL"),
        }
        print(t)
        return t

    if USE_API_KEY:
        t = {
            "base_url": get_env('OPENAI_BASE_URL'),
            "api_version": get_env("OPENAI_API_VERSION"),
            "model": get_env("OPENAI_DEPLOYMENT_NAME"),
            "api_key": get_env("OPENAI_API_KEY"),
            "api_type": "azure",
        }
    else:
        t = {
            "base_url": get_env('OPENAI_BASE_URL'),
            "api_version": get_env("OPENAI_API_VERSION"),
            "model": get_env("OPENAI_DEPLOYMENT_NAME"),
            "azure_ad_token_provider": token_provider,
            "api_type": "azure",
        }

    print(t)
    return t



endpoint = os.getenv("OPENAI_BASE_URL")  
if USE_API_KEY:
    client = AzureOpenAI(  
        azure_endpoint=os.getenv("OPENAI_BASE_URL"),  
        api_key=os.getenv("OPENAI_API_KEY"),  
        api_version=os.getenv("OPENAI_API_VERSION")
    )
else:
    client = AzureOpenAI(  
        azure_endpoint=os.getenv("OPENAI_BASE_URL"),  
        azure_ad_token_provider=token_provider,  
        api_version=os.getenv("OPENAI_API_VERSION")
    )  
  

model_config = {"config_list": [get_current_config()], "cache_seed": None}

def extract_any_content_from_text(any_type, text):  
    text = str(text)  
    pattern = rf'```{any_type}\s*([\s\S]*)```'  
    match = re.search(pattern, text)  
    if match:  
        return match.group(1).strip()  
    return text  

def generate_message_general(system, user = None, output_dir=None, model_name=os.getenv("OPENAI_DEPLOYMENT_NAME"), read_csvs=False):  
    messages = []  
    if model_name == "o1-mini":  
        messages = [AssistantMessage(content=system)]  
        if user:  
            messages.append(UserMessage(content=user))  
    elif model_name in ["o4-mini", "gpt-4.1"]:  
        messages = [{  
            "role": "developer",  
            "content": [{"type": "text", "text": system}]  
        }]  
        if user:
            messages.append({"role": "user", "content": [{"type": "text", "text": user}]})
    else:  
        messages = [{"role": "system", "content": system}]  
        if user:  
            messages.append({"role": "user", "content": user})  
    
    return messages
  

def get_structured_response(prompt, structuredClass, model_name = os.getenv("OPENAI_DEPLOYMENT_NAME")):  
    try:  
        response = client.beta.chat.completions.parse(  
            model=model_name,  
            messages=[{"role": "user", "content": prompt}],  
            response_format=structuredClass,  
            timeout=600
        )  
        response = response.choices[0].message.content  
        return response  
    except Exception as e:  
        print(f"Error generating structured output: {str(e)}")  
        return None  
    
def get_chat_response(messages, model_name = os.getenv("OPENAI_DEPLOYMENT_NAME"), output_dir = None):  
    if output_dir:  
        model_name = os.getenv("OPENAI_DEPLOYMENT_NAME")  
    try:  
        response = client.chat.completions.create(  
            model=model_name,  
            messages=messages,  
        )  
        return response.choices[0].message.content  
    except Exception as e:  
        print(f"Error in get_chat_response: {e}")  
        return 1  
    
def get_gpt_output(system_msg, user_msg, extract_text = None):  
    messages = generate_message_general(str(system_msg), str(user_msg))  
    response = get_chat_response(messages)  
    if extract_text:  
        response = extract_any_content_from_text(extract_text, response)  
    return response  

