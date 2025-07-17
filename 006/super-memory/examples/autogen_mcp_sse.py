import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams, SseServerParams, SseMcpToolAdapter
from llms import model_client

async def main() -> None:
    server_params = SseServerParams(
        url="http://localhost:8765/mcp/autogen/sse/danwen",
        timeout=30,  # Connection timeout in seconds
    )
    adapter = await SseMcpToolAdapter.from_server_params(server_params, "search_memory")
    async with McpWorkbench(server_params) as mcp:
        agent = AssistantAgent(
            "assistant",
            system_message="只能调用工具回答问题",
            model_client=model_client,
            workbench=mcp,
            reflect_on_tool_use=True,
            model_client_stream=True,
        )
        await Console(agent.run_stream(task="点击Sign up and start coding没反应的问题时，怎么解决"))
asyncio.run(main())

