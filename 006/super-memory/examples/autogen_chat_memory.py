import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core.memory import ListMemory, MemoryContent

from llms import model_client
from mem0_config import get_memory_client
async def main(task=None) -> None:
    client = await get_memory_client()
    result = client.search(query=task, user_id="danwen")
    list_results = result.get("results")
    memory = ListMemory(name="chat_history")
    for item in list_results:
        content = MemoryContent(content=item.get("memory"), mime_type="text/plain")
        await memory.add(content)

    agent = AssistantAgent(
                "assistant",
                model_client=model_client,
                model_client_stream=True,
                memory=[memory]

            )
    await Console(agent.run_stream(task=task))

asyncio.run(main(task="作者什么时间喜欢写程序"))