# For ending the groupchar conversation

description = """
Acts as a proxy for the user, forwarding messages to the user agent. It does not have any tools or code execution capabilities. It should NEVER be called after any agent. It can only start the group chat. NEVER call this agent.
"""

system_message = """You are a user proxy agent. You forward messages to the user agent without any tools or code execution capabilities."""

user_proxy_agent = {
    "type": "user_proxy",
    "name": "user_proxy_agent",
    "system_message": system_message,
    "description": description,
    "human_input_mode": "ALWAYS",
    "code_execution_config": False,
}