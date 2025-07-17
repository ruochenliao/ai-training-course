import asyncio
from dataclasses import dataclass

from autogen_core import (
    ClosureAgent,
    ClosureContext,
    DefaultSubscription,
    DefaultTopicId,
    MessageContext,
    SingleThreadedAgentRuntime, RoutedAgent, message_handler, type_subscription, TypeSubscription,
)
from pydantic import BaseModel
RESULT_COLLECTOR_TOPIC = "result_collector"

@dataclass
class FinalResult:
    value: str

class MyMessage(BaseModel):
    content: str

queue = asyncio.Queue[FinalResult]()

@type_subscription(topic_type="topic1")
class MyAgent(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @message_handler
    async def handle_my_message_type(self, message: MyMessage, ctx: MessageContext) -> None:
        print(f"{self.id.type} received message: {message.content}")
        # 处理复杂的业务逻辑
        result = FinalResult(value="处理结果：哈哈哈哈")
        await self.publish_message(result, topic_id=DefaultTopicId(type=RESULT_COLLECTOR_TOPIC))


# 接收智能体执行的结果
async def output_result(_agent: ClosureContext, message: FinalResult, ctx: MessageContext) -> None:
    # 接收到智能体执行的结果，可以返回到前端界面
    print(message)
    await queue.put(message)

async def main():
    runtime = SingleThreadedAgentRuntime()
    await MyAgent.register(runtime, "my_agent", lambda: MyAgent("agent1"))

    # 注册结果收集器智能体；指定接收结果的回调函数；订阅结果收集器智能体的结果
    await ClosureAgent.register_closure(
        runtime, "collector_agent", output_result, subscriptions=lambda: [
                TypeSubscription(
                    topic_type=RESULT_COLLECTOR_TOPIC,
                    agent_type="collector_agent"
                )
            ],
    )
    runtime.start()

    await runtime.publish_message(MyMessage(content="hello world"), topic_id=DefaultTopicId(type="topic1"))

    await runtime.stop_when_idle()

asyncio.run(main())