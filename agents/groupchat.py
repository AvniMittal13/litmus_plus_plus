import autogen
from utils.aoai_chat import model_config
import uuid
import os
import json


class GroupChat:
    def __init__(self, agents_list, initiator_agent, last_message_agent, custom_speaker_selection_func = None):
        self.agents_list = agents_list
        self.initiator_agent = initiator_agent
        self.last_message_agent = last_message_agent
        if custom_speaker_selection_func:
            self.custom_speaker_selection_func = custom_speaker_selection_func
        else:
            self.custom_speaker_selection_func = "auto"

        self.groupchat_manager = self.create_groupchat()

        # Generate a random filename for logging this groupchat session
        self.log_filename = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "agent_outputs",
            f"groupchat_log_{uuid.uuid4().hex}.json"
        )


    def run(self, starting_msg = "No starting msg, end the conversation."):
        messages, summary = self.continue_groupchat(starting_msg)
        final_response = self.get_last_message_by_name(messages, self.last_message_agent.name)

        # Log all messages to the random log file
        try:
            os.makedirs(os.path.dirname(self.log_filename), exist_ok=True)
            with open(self.log_filename, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[GroupChat] Failed to write log file: {e}")

        return final_response, messages, summary

    def create_groupchat(self, ):
        investigation_crew_group = self.agents_list

        # group chat intorduction -- Each agent know about each other
        group_chat_with_introductions = autogen.GroupChat(
            agents=investigation_crew_group,
            messages=[],
            max_round=50,
            send_introductions=True,
            speaker_selection_method=self.custom_speaker_selection_func,
        )

        manager = autogen.GroupChatManager(
            groupchat=group_chat_with_introductions, llm_config=model_config
        )

        return manager

    def continue_groupchat(self, starting_msg):
        chat_result = self.initiator_agent.initiate_chat(
            self.groupchat_manager,
            message=starting_msg,
            summary_method="reflection_with_llm",
            clear_history=False
        )

        return self.groupchat_manager.groupchat.messages, chat_result.summary

    def get_last_message_by_name(self, messages, target_name, before_last_user_msg=True):
        for message in reversed(messages):
            if message.get('name') == target_name:
                return message.get('content')
            if message.get('name') == "user_proxy" and before_last_user_msg:
                break
        return f"No message by {target_name}"