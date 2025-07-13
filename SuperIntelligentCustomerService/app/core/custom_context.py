"""
自定义ChatCompletionContext来解决AutoGen的memories属性问题
根据Microsoft AutoGen官方文档修复UnboundedChatCompletionContext缺少memories属性的问题
参考: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html
"""
import logging
from typing import List, Sequence, Any, Optional

try:
    from autogen_agentchat.messages import BaseMessage
    from autogen_core.model_context import UnboundedChatCompletionContext
    from autogen_core.models import LLMMessage
    from autogen_agentchat.agents import AssistantAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    class BaseMessage: pass
    class UnboundedChatCompletionContext: pass
    class LLMMessage: pass
    class AssistantAgent: pass

logger = logging.getLogger(__name__)


class MemoryResult:
    """模拟memories.results的结构"""
    def __init__(self, results: List[Any] = None):
        self.results = results or []


class MemoryContainer:
    """模拟memories属性的容器，符合AutoGen Memory协议"""
    def __init__(self):
        self.results = []
        self.items = []  # 兼容不同的访问方式
        
    def add_result(self, result: Any):
        """添加记忆结果"""
        self.results.append(result)
        self.items.append(result)
        
    def clear(self):
        """清空记忆"""
        self.results.clear()
        self.items.clear()


class FixedUnboundedChatCompletionContext(UnboundedChatCompletionContext):
    """
    修复了memories属性问题的UnboundedChatCompletionContext
    根据Microsoft AutoGen官方文档实现
    """
    
    def __init__(self, initial_messages: Optional[Sequence[LLMMessage]] = None):
        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen不可用，使用模拟实现")
            return
            
        super().__init__(initial_messages)
        # 添加缺失的memories属性
        self.memories = MemoryContainer()
        logger.debug("FixedUnboundedChatCompletionContext初始化完成，已添加memories属性")
    
    async def add_message(self, message: LLMMessage) -> None:
        """添加消息到上下文"""
        if not AUTOGEN_AVAILABLE:
            return
            
        await super().add_message(message)
        logger.debug(f"消息已添加到上下文: {type(message).__name__}")
    
    async def get_messages(self) -> List[LLMMessage]:
        """获取所有消息"""
        if not AUTOGEN_AVAILABLE:
            return []
            
        messages = await super().get_messages()
        logger.debug(f"获取到 {len(messages)} 条消息")
        return messages
    
    def add_memory_result(self, result: Any):
        """添加记忆结果到上下文"""
        if hasattr(self, 'memories'):
            self.memories.add_result(result)
            logger.debug("记忆结果已添加到上下文")


def create_fixed_assistant(name: str, model_client, system_message: str = None, 
                          tools: List = None, memory_adapters: List = None):
    """
    创建使用修复后的ChatCompletionContext的AssistantAgent
    根据Microsoft AutoGen官方文档实现
    """
    if not AUTOGEN_AVAILABLE:
        logger.warning("AutoGen不可用，无法创建智能体")
        return None
    
    try:
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
        
    except Exception as e:
        logger.error(f"创建修复后的助手失败: {e}")
        # 回退到标准创建方式
        try:
            assistant_params = {
                "name": name,
                "model_client": model_client,
                "reflect_on_tool_use": True,
                "model_client_stream": True,
            }
            
            if system_message:
                assistant_params["system_message"] = system_message
            
            if tools:
                assistant_params["tools"] = tools
            
            # 不使用memory参数，避免错误
            assistant = AssistantAgent(**assistant_params)
            logger.warning(f"使用回退方式创建助手: {name} (记忆功能已禁用)")
            return assistant
            
        except Exception as fallback_error:
            logger.error(f"回退创建助手也失败: {fallback_error}")
            return None


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
    if not adapter:
        return adapter
        
    # 保存原始的update_context方法
    if hasattr(adapter, 'update_context'):
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


def create_safe_assistant_with_memory(name: str, model_client, system_message: str = None, 
                                     tools: List = None, memory_adapters: List = None):
    """
    创建安全的带记忆功能的AssistantAgent
    自动应用memories属性修复和错误处理
    """
    if not AUTOGEN_AVAILABLE:
        logger.warning("AutoGen不可用，无法创建智能体")
        return None
    
    try:
        # 首先尝试使用修复后的context创建
        assistant = create_fixed_assistant(name, model_client, system_message, tools, memory_adapters)
        if assistant:
            return assistant
            
    except Exception as e:
        logger.warning(f"使用修复后的context创建失败: {e}")
    
    # 如果修复方式失败，尝试对memory_adapters应用补丁
    try:
        patched_adapters = []
        if memory_adapters:
            for adapter in memory_adapters:
                patched_adapter = patch_memory_adapter(adapter)
                patched_adapters.append(patched_adapter)
        
        # 使用标准方式创建，但使用补丁后的适配器
        assistant_params = {
            "name": name,
            "model_client": model_client,
            "reflect_on_tool_use": True,
            "model_client_stream": True,
        }
        
        if system_message:
            assistant_params["system_message"] = system_message
        
        if tools:
            assistant_params["tools"] = tools
        
        if patched_adapters:
            assistant_params["memory"] = patched_adapters
        
        assistant = AssistantAgent(**assistant_params)
        logger.info(f"使用补丁方式创建助手成功: {name}")
        return assistant
        
    except Exception as e:
        logger.error(f"使用补丁方式创建助手失败: {e}")
        
        # 最后的回退：不使用记忆功能
        try:
            assistant_params = {
                "name": name,
                "model_client": model_client,
                "reflect_on_tool_use": True,
                "model_client_stream": True,
            }
            
            if system_message:
                assistant_params["system_message"] = system_message
            
            if tools:
                assistant_params["tools"] = tools
            
            assistant = AssistantAgent(**assistant_params)
            logger.warning(f"使用无记忆回退方式创建助手: {name}")
            return assistant
            
        except Exception as final_error:
            logger.error(f"所有创建方式都失败: {final_error}")
            return None
