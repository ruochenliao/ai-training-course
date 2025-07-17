import asyncio
import logging
from typing import List, Dict

from c_app.schemas.customer import ChatMessage
from c_app.services.memory_service import (
    MemoryServiceFactory,
    ChatMemoryService,
    PrivateMemoryService,
    PublicMemoryService
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def example_chat_memory_service(user_id: str):
    """聊天历史记忆服务示例"""
    logger.info("=== 聊天历史记忆服务示例 ===")
    
    # 创建聊天历史记忆服务
    chat_memory = ChatMemoryService(user_id)
    
    # 添加一些聊天消息
    await chat_memory.add(ChatMessage(role="user", content="你好，AI助手！"))
    await chat_memory.add(ChatMessage(role="assistant", content="你好！我是AI助手，有什么可以帮助你的吗？"))
    await chat_memory.add(ChatMessage(role="user", content="我想了解一下记忆服务的功能"))
    
    # 添加一些文本
    await chat_memory.add("这是一条普通文本记录", {"tag": "note"})
    
    # 查询聊天历史
    results = await chat_memory.query("AI助手")
    logger.info(f"查询结果数量: {len(results)}")
    for i, result in enumerate(results):
        logger.info(f"结果 {i+1}: {result['content']}")
    
    # 获取所有消息
    all_messages = await chat_memory.get_all_messages()
    logger.info(f"所有消息数量: {len(all_messages)}")
    
    # 清理资源
    await chat_memory.close()


async def example_private_memory_service(user_id: str):
    """私有记忆服务示例"""
    logger.info("=== 私有记忆服务示例 ===")
    
    # 创建私有记忆服务
    private_memory = PrivateMemoryService(user_id)
    
    # 添加一些内容
    await private_memory.add("这是用户的私有笔记", {"tag": "note"})
    await private_memory.add("用户的个人信息：姓名、年龄、职业等", {"tag": "personal_info"})
    await private_memory.add(ChatMessage(role="user", content="这是一条私有消息"))
    
    # 查询私有记忆
    results = await private_memory.query("私有")
    logger.info(f"查询结果数量: {len(results)}")
    for i, result in enumerate(results):
        logger.info(f"结果 {i+1}: {result['content']}")
    
    # 清理资源
    await private_memory.close()


async def example_public_memory_service():
    """公共记忆服务示例"""
    logger.info("=== 公共记忆服务示例 ===")
    
    # 创建公共记忆服务
    public_memory = PublicMemoryService()
    
    # 添加一些内容
    await public_memory.add("这是一条公共知识：地球是圆的", {"tag": "knowledge"})
    await public_memory.add("公共FAQ：如何使用记忆服务？", {"tag": "faq"})
    await public_memory.add(ChatMessage(role="assistant", content="这是一条公共回复模板"))
    
    # 查询公共记忆
    results = await public_memory.query("公共")
    logger.info(f"查询结果数量: {len(results)}")
    for i, result in enumerate(results):
        logger.info(f"结果 {i+1}: {result['content']}")
    
    # 清理资源
    await public_memory.close()


async def example_memory_service_factory():
    """记忆服务工厂示例"""
    logger.info("=== 记忆服务工厂示例 ===")
    
    # 创建记忆服务工厂
    factory = MemoryServiceFactory()
    
    # 获取不同用户的聊天记忆服务
    user1_chat = factory.get_chat_memory_service("user1")
    user2_chat = factory.get_chat_memory_service("user2")
    
    # 获取不同用户的私有记忆服务
    user1_private = factory.get_private_memory_service("user1")
    user2_private = factory.get_private_memory_service("user2")
    
    # 获取公共记忆服务
    public_memory = factory.get_public_memory_service()
    
    # 添加一些内容
    await user1_chat.add(ChatMessage(role="user", content="用户1的消息"))
    await user2_chat.add(ChatMessage(role="user", content="用户2的消息"))
    
    await user1_private.add("用户1的私有数据")
    await user2_private.add("用户2的私有数据")
    
    await public_memory.add("所有用户共享的公共数据")
    
    # 关闭所有服务
    await factory.close_all()


async def main():
    """主函数"""
    user_id = "test_user"
    
    # 运行示例
    await example_chat_memory_service(user_id)
    await example_private_memory_service(user_id)
    await example_public_memory_service()
    await example_memory_service_factory()


if __name__ == "__main__":
    asyncio.run(main())
