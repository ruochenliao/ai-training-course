"""
自定义ChatCompletionContext来解决autogen 0.6.1的memories属性问题
"""
import logging
from typing import List, Sequence, Any, Optional

from autogen_agentchat.messages import BaseMessage
from autogen_core.model_context import UnboundedChatCompletionContext
from autogen_core.models import LLMMessage

logger = logging.getLogger(__name__)


class MemoryResult:
    """模拟memories.results的结构"""
    def __init__(self, results: List[Any] = None):
        self.results = results or []


class MemoryContainer:
    """模拟memories属性的容器"""
    def __init__(self):
        self.results = []


class FixedUnboundedChatCompletionContext(UnboundedChatCompletionContext):
    """
    修复了memories属性问题的UnboundedChatCompletionContext
    """
    
    def __init__(self, initial_messages: Optional[Sequence[LLMMessage]] = None):
        super().__init__(initial_messages)
        # 添加缺失的memories属性
        self.memories = MemoryContainer()
        logger.debug("FixedUnboundedChatCompletionContext初始化完成，已添加memories属性")
    
    async def add_message(self, message: LLMMessage) -> None:
        """添加消息到上下文"""
        await super().add_message(message)
        logger.debug(f"消息已添加到上下文: {type(message).__name__}")
    
    async def get_messages(self) -> List[LLMMessage]:
        """获取所有消息"""
        messages = await super().get_messages()
        logger.debug(f"获取到 {len(messages)} 条消息")
        return messages
    
    def clear(self) -> None:
        """清空上下文"""
        super().clear()
        # 重置memories
        self.memories = MemoryContainer()
        logger.debug("上下文已清空，memories已重置")


def create_fixed_assistant(name: str, model_client, system_message: str = None, 
                          tools: List = None, memory_adapters: List = None):
    """
    创建使用修复后的ChatCompletionContext的AssistantAgent
    """
    from autogen_agentchat.agents import AssistantAgent
    
    # 创建修复后的model_context
    model_context = FixedUnboundedChatCompletionContext()
    
    # 创建助手参数
    assistant_params = {
        "name": name,
        "model_client": model_client,
        "model_context": model_context,  # 使用我们修复后的context
        "reflect_on_tool_use": True,
        "model_client_stream": True,
    }
    
    if system_message:
        assistant_params["system_message"] = system_message
    
    if tools:
        assistant_params["tools"] = tools
    
    if memory_adapters:
        assistant_params["memory"] = memory_adapters
        logger.debug(f"记忆服务已启用，适配器数量: {len(memory_adapters)}")
    
    # 创建助手
    assistant = AssistantAgent(**assistant_params)
    
    logger.debug(f"修复后的助手创建成功: {name}")
    return assistant


class MemoryWorkaroundMixin:
    """
    为现有的内存适配器添加workaround功能的混入类
    """
    
    async def update_context_safe(self, messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
        """
        安全的上下文更新方法，避免memories属性错误
        """
        try:
            # 调用原始的update_context方法
            return await self.update_context(messages)
        except AttributeError as e:
            if "memories" in str(e):
                logger.warning(f"检测到memories属性错误，使用fallback方法: {e}")
                # 使用fallback方法：直接返回原始消息
                return messages
            else:
                # 其他AttributeError继续抛出
                raise
        except Exception as e:
            logger.error(f"上下文更新失败: {e}")
            # 返回原始消息，确保不中断流程
            return messages


def patch_memory_adapter(adapter):
    """
    为内存适配器添加workaround功能
    """
    # 保存原始的update_context方法
    original_update_context = adapter.update_context
    
    async def safe_update_context(messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
        try:
            return await original_update_context(messages)
        except AttributeError as e:
            if "memories" in str(e):
                logger.warning(f"检测到memories属性错误，跳过内存更新: {e}")
                return messages
            else:
                raise
        except Exception as e:
            logger.error(f"内存更新失败: {e}")
            return messages
    
    # 替换update_context方法
    adapter.update_context = safe_update_context
    logger.debug("内存适配器已应用workaround补丁")
    
    return adapter
