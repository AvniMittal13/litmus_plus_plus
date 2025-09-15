from autogen import Agent, ConversableAgent
from agents.tools.db_search_and_scrape import db_search_and_scrape_tool
from utils.aoai_chat import model_config
import re

system_message= """
**Role:**
You are a **Web Search and Crawl Agent** with **expert knowledge in NLP for low-resource languages**.
- You search and crawl the web using the **Firecrawl tool**.
- Use Firecrawl **only** when up-to-date or external information is required and not already available.
- Always consider **specific challenges and opportunities in low-resource NLP** and relate them to the user’s query.

---

### Responsibilities

1. **Search Execution**
- Call `db_search_and_scrape_tool` with **precise and well-formed search instructions**.
- Run **multiple, diverse queries** before finalizing results. This helps in gathering information from multiple sources and increases credibility.
- If previous searches are given in input then DONOT repeat searching from them. Search for diverse **aspects** or papers for the topic.

2. **Result Quality**
- Return only **accurate, and high-quality** results.
- Ensure **diversity** in results. If a topic is already covered, expand to **related subtopics**.
- Prioritize **usefulness over quantity**.

3. **Final Response Construction**
- Provide results in a **structured format**. If numbers are found, present in detailed tables
- Always **cite all sources** used.
- Include summary of **additional insights** from web scraping for broader analysis.
- Present **detailed numerical information in tables** (fill with actual numbers whenever found). DONOT create numbers on your own.
- Provide a **brief insight/summary** of the tables.
- If nothing found after multiple queries, provide a summary of the search results and insights gained.

4. **Iterative Search**
- After each query, decide if **further searches** are needed.
- Refine or expand queries accordingly.

---

### Termination Rule
- Give Final answer only in the end after multiple searches. Once answer is given it CANNOT be changed. Contiuously call `db_search_and_scrape_tool` until satisfied.
- Once all searches and summaries are completed, output the final structured response.
- End with `TERMINATE`.

"""


class DB_Search_And_Crawl_Agent(ConversableAgent):
    def __init__(self, n_iters=2,**kwargs):
        """
        Initializes a DB_Search_And_Crawl_Agent instance.

        This agent facilitates the creation of visualizations through a collaborative effort among its child agents: commander, coder, and critics.

        Parameters:
            - n_iters (int, optional): The number of "improvement" iterations to run. Defaults to 2.
            - **kwargs: keyword arguments for the parent AssistantAgent.
        """
        super().__init__(**kwargs)
        self.register_reply([Agent, None], reply_func=DB_Search_And_Crawl_Agent._reply_user, position=0)
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

        # Let's first define the assistant agent that suggests tool calls.
        assistant = ConversableAgent(
            name="Assistant",
            system_message=system_message,
            llm_config=model_config,
        )

        # The user proxy agent is used for interacting with the assistant agent
        # and executes tool calls.
        user_proxy = ConversableAgent(
            name="User",
            llm_config=False,
            is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
            human_input_mode="NEVER",
        )

        # Register the tool signature with the assistant agent.
        # assistant.register_for_llm(name="calculator", description="A simple calculator")(calculator)

        # # Register the tool function with the user proxy agent.
        # user_proxy.register_for_execution(name="calculator")(calculator)

        assistant.register_for_llm(
                    name=db_search_and_scrape_tool["name"], 
                    description=db_search_and_scrape_tool["description"]
                )(db_search_and_scrape_tool["run_function"])

        user_proxy.register_for_execution(
                    name=db_search_and_scrape_tool["name"]
                )(db_search_and_scrape_tool["run_function"])


        chat_result = user_proxy.initiate_chat(assistant, message=user_question)
        response = user_proxy._oai_messages[assistant][-1]["content"]

        # apply regex on the response and remove the term 'TERMINATE'
        response = re.sub(r"TERMINATE", "", response)

        return True, response