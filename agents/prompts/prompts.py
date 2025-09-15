thought_agent_final_message_format = """
Final Response: {final_response}
---
Summary of Inner Conversation: {summary}
"""

thought_agent_starting_message = """
Answer the user query by following the thought process idea. 
Collect features and train a regression model if exact value cant be found via web search and crawl. DONOT give the code to me. Perform websearch to collect features and code generation and code execution to execute code. Use coder_agent after websearch_and_crawl. coder_agent writes code which gets executed and returns result. Collect all data for features required via web search then call coder_agent once all things are available.

User Query: {user_query}
---
Thought: {thought}
"""

response_analyzer_agent_message = """
Analyse the findings of different thought agents and provide detailed response:

User Query: {user_query}
---
Responses from Thought Agents: {responses}
"""

thought_analyzer_agent_message = """
Analyze the conversation with the user till now and the responses from thought agents to provide a comprehensive answer:

---
Last Responses from Thought Agents: {responses}
---
Conversation with the user till now: {conversation_history}
---
Expert knowledge on possible directions:
{expert_knowledge}
"""

thought_creator_agent_message = """
Generate thoughts and hypotheses based on the user query and the conversation history. Consider various angles and approaches to tackle the problem.
maximum number of thoughts to generate : 3

Conversation History: {conversation_history}
---
Expert Knowledge: {expert_knowledge}
"""

expert_knowledge_agent_message = """
Utilize expert knowledge to tell how to proceed approaching the user query and demands. Following are the messages user has shared till now:

---
user messages till now: {conversation_history_user}
"""