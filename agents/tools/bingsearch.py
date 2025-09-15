import os
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.agents.azure._azure_ai_agent import AzureAIAgent
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import BingGroundingTool
import dotenv

dotenv.load_dotenv()

async def main():
    # Get Azure credentials and endpoint from environment
    credential = DefaultAzureCredential()
    azure_endpoint = os.getenv("AZURE_PROJECT_ENDPOINT", "")
    bing_connection_name = os.getenv("BING_CONNECTION_NAME", "")

    async with credential:
        async with AIProjectClient(credential=credential, endpoint=azure_endpoint) as project_client:
            # Get the Bing connection resource
            conn = await project_client.connections.get(name=bing_connection_name)

            # Create the Bing grounding tool instance
            bing_tool = BingGroundingTool(conn.id)

            # Create the AzureAIAgent with bing grounding
            agent = AzureAIAgent(
                name="bing_agent",
                description="An AI assistant with Bing grounding",
                project_client=project_client,
                deployment_name="YOUR_AZURE_MODEL_DEPLOYMENT_NAME",  # e.g. "gpt-4", or whatever your model is
                instructions="You are a helpful assistant. Use Bing for grounding and provide citations when you answer.",
                tools=bing_tool.definitions,
                metadata={"source": "AzureAIAgent_with_Bing"}
            )

            # Now send a user message and get a response
            result = await agent.on_messages(
                messages=[
                    TextMessage(
                        content="What is Microsoft's annual leave policy? Please provide citations using Bing.",
                        source="user",
                    )
                ],
                cancellation_token=CancellationToken(),
                message_limit=5,
            )

            print("Agent response:", result)

if __name__ == "__main__":
    asyncio.run(main())
