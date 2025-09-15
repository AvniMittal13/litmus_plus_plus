import autogen
from utils.aoai_chat import model_config


def create_groupchat(agents_list, custom_speaker_selection_func):
    investigation_crew_group = agents_list

    # group chat intorduction -- Each agent know about each other
    group_chat_with_introductions = autogen.GroupChat(
        agents=investigation_crew_group,
        messages=[],
        max_round=50,
        send_introductions=True,
        speaker_selection_method=custom_speaker_selection_func,
    )

    manager = autogen.GroupChatManager(
        groupchat=group_chat_with_introductions, llm_config=model_config
    )

    return manager