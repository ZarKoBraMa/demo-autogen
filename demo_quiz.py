import os
from typing import List
from typing_extensions import Annotated

from autogen import ConversableAgent, GroupChat, GroupChatManager

from dotenv import load_dotenv

load_dotenv()

##### Setting up LLMs

config_list = [
    {
    "model": "gpt-4o-mini",
    "api_type": "azure",
    "api_key": os.getenv('AZURE_OPENAI_API_KEY'),
    "base_url": "https://oai-aiapplied-dev-swedencentral-001.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2023-03-15-preview",
    "api_version": "2024-02-01"
  },
]

##### Tool
scores = {
    "Bot": 0,
    "Human": 0
}

# Function to increment scores
def update_scores(names_list: Annotated[List[str], "list of participants who correctly answers question"]) -> int:
    for name in names_list:
        if name in scores:
            scores[name] += 1
        else:
            print(f"{name} not found in the dictionary.")
    return 1


quiz_master = ConversableAgent(
    name="Quiz_Master",
    system_message="You are an expert quizmaster. Your task is to generate medium-hard pub quiz questions. Each question should be intriguing but not too easy or obscure. Provide 4 possible answers, with only one correct answer. The topics can include general knowledge, science, history, sports, geography, and entertainment. Ensure the question and answers are concise. Randomize the position of the correct answer among the options. Do not log correct answer",
    llm_config={"config_list": config_list, "cache_seed": None},
)

quiz_participant_bot = ConversableAgent(
    name="Bot",
    system_message="You are a pub quiz participant with solid general knowledge and an 10% chance of answering correctly. Your goal is to select the correct answer from 4 options provided. Sometimes you may choose an incorrect answer to reflect the 10% accuracy. Review the question and options carefully, then respond with the letter (A, B, C, or D) that corresponds to your selected answer. Good luck!",
    llm_config={"config_list": config_list, "cache_seed": None},

)

quiz_participant_human = ConversableAgent(
    name="Human",
    system_message="You are a pub quiz participanta",
    llm_config=False,
    human_input_mode="ALWAYS"
)

quiz_participant_evaluator = ConversableAgent(
    name="quiz_participant_evaluator",
    system_message="quiz_referee will provide you answers from both quiz participants. Provide feedback to them are the answers correct or not.",
    llm_config={"config_list": config_list, "cache_seed": None},
    human_input_mode="NEVER"
)

quiz_participant_scorer = ConversableAgent(
    name="quiz_participant_scorer",
    system_message="Provide list of participants names who answered correctly on question.",
    llm_config={"config_list": config_list, "cache_seed": None},
    human_input_mode="NEVER"
)

quiz_participant_recorder = ConversableAgent(
    name="quiz_participant_recorder",
    llm_config=False,
    human_input_mode="NEVER"
)

quiz_participant_scorer.register_for_llm(name="update_scores", description="A tool for manage score of participants")(update_scores)
quiz_participant_recorder.register_for_execution(name="update_scores")(update_scores)

group_chat = GroupChat(
    agents=[quiz_participant_bot, quiz_participant_human, quiz_participant_evaluator, quiz_participant_scorer, quiz_participant_recorder],
    messages=[],
    max_round=6,
    speaker_selection_method="round_robin"
) 

quiz_referee = GroupChatManager(
    groupchat=group_chat,
    llm_config={"config_list": config_list, "cache_seed": None},
    system_message="After you receive answers from all quiz participants provide their answers to the quiz_participant_evaluator, so that he can evalute answers and send you list of participant names who answered correctly."
)

for X in range(3):
    print(f"Question number '{X + 1}'")
    question = quiz_master.generate_reply(messages=[{"content": "Create one question for pubquiz", "role": "user"}])
    result = quiz_master.initiate_chat(quiz_referee, message=question)

for name, score in scores.items():
    print(f"{name}: {score}")

name_with_max_score = max(scores, key=scores.get)

print(f"The person with the highest score and PubQuiz winner is: {name_with_max_score}")
