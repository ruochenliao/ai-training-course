import asyncio

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination, SourceMatchTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from llms import model_client
# Create an OpenAI model client.


# Create the primary agent.
primary_agent = AssistantAgent(
    "primary",
    model_client=model_client,
    system_message="You are a helpful AI assistant.",
)

# Create the critic agent.
critic_agent = AssistantAgent(
    "critic",
    model_client=model_client,
    system_message="Provide constructive feedback. Respond with 'APPROVE' to when your feedbacks are addressed.",
)


user_proxy = UserProxyAgent("user_proxy", input_func=input)

# Define a termination condition that stops the task if the critic approves.
text_termination = TextMentionTermination("APPROVE")
source_termination = SourceMatchTermination(["critic"])

# Create a team with the primary and critic agents.
team = RoundRobinGroupChat([primary_agent, user_proxy], termination_condition=text_termination)

# Use `asyncio.run(...)` when running in a script.
async def main():
    stream = team.run_stream(task="编写一首夏天的诗")
    async for msg in stream:
      print(msg)

asyncio.run(main())

