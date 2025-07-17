import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams
from llms import model_client
import asyncio
from pathlib import Path
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken


async def main_tools() -> None:
    # Setup server params for local filesystem access
    desktop = str(Path.home() / "Desktop")
    server_params = StdioServerParams(
        command="npx.cmd", args=["-y", "@modelcontextprotocol/server-filesystem", desktop]
    )

    # Get all available tools from the server
    tools = await mcp_server_tools(server_params)

    # Create an agent that can use all the tools
    agent = AssistantAgent(
        name="file_manager",
        model_client=model_client,
        tools=tools,  # type: ignore
    )

    # The agent can now use any of the filesystem tools
    await agent.run(task="Create a file called test.txt with some content", cancellation_token=CancellationToken())



async def main_workbench() -> None:
    server_params = StdioServerParams(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            r"C:\Users\86134\Desktop\workspace\production\super-memory",
        ]
    )
    async with McpWorkbench(server_params) as mcp:
        agent = AssistantAgent(
            "assistant",
            model_client=model_client,
            workbench=mcp,
            reflect_on_tool_use=False,
            model_client_stream=True,
        )
        await Console(agent.run_stream(task="在当前目录下新建一个文件夹：666666"))
asyncio.run(main())

