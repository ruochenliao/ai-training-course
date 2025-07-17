import asyncio
from dataclasses import dataclass

from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler
from pydantic import BaseModel


@dataclass
class MyMessageType:
    content: str

class MyMessage(BaseModel):
    content: str

class MyAgent(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @message_handler
    async def handle_my_message_type(self, message: MyMessageType, ctx: MessageContext) -> None:
        print(f"{self.id.type} received message: {message.content}")
        await self.send_message(MyMessage(content="我处理过了"), AgentId("my_agent2", "default"))

    @message_handler
    async def handle_my_message(self, message: MyMessage, ctx: MessageContext) -> None:
        print(f"{self.id.type} received message: {message.content}")

class MyAgent2(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @message_handler
    async def handle_my_message_type(self, message: MyMessageType, ctx: MessageContext) -> None:
        print(f"{self.id.type} received message: {message.content}")

    @message_handler
    async def handle_my_message(self, message: MyMessage, ctx: MessageContext) -> None:
        print(f"{self.id.type} received message: {message.content}")


from autogen_core import SingleThreadedAgentRuntime
async def main():
    # 创建一个运行时环境
    runtime = SingleThreadedAgentRuntime()
    await MyAgent.register(runtime, "my_agent", lambda: MyAgent("agent1"))
    await MyAgent2.register(runtime, "my_agent2", lambda: MyAgent2("agent2"))

    runtime.start()
    # 通过发消息的方式调用 MyAgent 智能体的代码，发消息的方式有两种：直接发消息和使用广播发消息

    # 直接发消息
    await runtime.send_message(MyMessageType("Hello, World!"), AgentId("my_agent", "default"))
    await runtime.send_message(MyMessage(content="Hello, World8888!"), AgentId("my_agent", "default"))

    await runtime.stop_when_idle()

asyncio.run(main())