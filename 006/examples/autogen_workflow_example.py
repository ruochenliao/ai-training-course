import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Create an OpenAI model client
# client = OpenAIChatCompletionClient(model="gpt-4.1-nano")
from llms import model_client as client
# Create the writer agent
writer = AssistantAgent("writer", model_client=client, system_message="擅长编写古诗")

# Create the reviewer agent
reviewer = AssistantAgent("reviewer", model_client=client, system_message="对古诗提出修改建议")

# Build the graph
builder = DiGraphBuilder()
builder.add_node(writer).add_node(reviewer)
builder.add_edge(writer, reviewer)

# Build and validate the graph
graph = builder.build()

# Create the flow
flow = GraphFlow([writer, reviewer], graph=graph)
# Use `asyncio.run(...)` and wrap the below in a async function when running in a script.
async def main():
    stream = flow.run_stream(task="写一首关于夏天的诗")
    async for event in stream:  # type: ignore
        print(event)
# Use Console(flow.run_stream(...)) for better formatting in console.

asyncio.run(main())