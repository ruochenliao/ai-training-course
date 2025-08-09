"""
# Copyright (c) 2025 左岚. All rights reserved.

基础智能体类

定义了所有智能体的基础接口和通用功能。
"""

# # Standard library imports
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Union

# # Third-party imports
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentMessage(BaseModel):
    """智能体消息模型"""
    id: str
    sender: str
    receiver: str
    content: str
    message_type: str = "text"
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()


class AgentConfig(BaseModel):
    """智能体配置模型"""
    name: str
    description: str
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4000
    system_prompt: str = ""
    tools: List[str] = []
    capabilities: List[str] = []


class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.description = config.description
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.system_prompt = config.system_prompt
        self.tools = config.tools
        self.capabilities = config.capabilities
        
        # 运行时状态
        self.is_active = False
        self.conversation_history: List[AgentMessage] = []
        self.context: Dict[str, Any] = {}
        
        logger.info(f"初始化智能体: {self.name}")
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """
        处理接收到的消息
        
        Args:
            message: 输入消息
            
        Returns:
            AgentMessage: 处理后的响应消息
        """
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        生成响应内容
        
        Args:
            prompt: 输入提示
            context: 上下文信息
            
        Returns:
            str: 生成的响应内容
        """
        pass
    
    async def send_message(self, receiver: str, content: str, message_type: str = "text") -> AgentMessage:
        """
        发送消息给其他智能体
        
        Args:
            receiver: 接收者名称
            content: 消息内容
            message_type: 消息类型
            
        Returns:
            AgentMessage: 发送的消息
        """
        message = AgentMessage(
            id=f"{self.name}_{datetime.now().timestamp()}",
            sender=self.name,
            receiver=receiver,
            content=content,
            message_type=message_type
        )
        
        # 添加到对话历史
        self.conversation_history.append(message)
        
        logger.info(f"{self.name} 发送消息给 {receiver}: {content[:100]}...")
        return message
    
    async def receive_message(self, message: AgentMessage) -> AgentMessage:
        """
        接收并处理消息
        
        Args:
            message: 接收到的消息
            
        Returns:
            AgentMessage: 处理后的响应消息
        """
        logger.info(f"{self.name} 接收到来自 {message.sender} 的消息")
        
        # 添加到对话历史
        self.conversation_history.append(message)
        
        # 处理消息
        response = await self.process_message(message)
        
        # 添加响应到历史
        self.conversation_history.append(response)
        
        return response
    
    def update_context(self, key: str, value: Any):
        """更新上下文信息"""
        self.context[key] = value
        logger.debug(f"{self.name} 更新上下文: {key}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文信息"""
        return self.context.get(key, default)
    
    def clear_context(self):
        """清空上下文"""
        self.context.clear()
        logger.debug(f"{self.name} 清空上下文")
    
    def get_conversation_history(self, limit: int = None) -> List[AgentMessage]:
        """获取对话历史"""
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history
    
    def clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
        logger.debug(f"{self.name} 清空对话历史")
    
    async def start(self):
        """启动智能体"""
        self.is_active = True
        logger.info(f"智能体 {self.name} 已启动")
    
    async def stop(self):
        """停止智能体"""
        self.is_active = False
        logger.info(f"智能体 {self.name} 已停止")
    
    def __str__(self) -> str:
        return f"Agent({self.name})"
    
    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', model='{self.model}', active={self.is_active})"


class AgentRegistry:
    """智能体注册表"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register(self, agent: BaseAgent):
        """注册智能体"""
        self._agents[agent.name] = agent
        logger.info(f"注册智能体: {agent.name}")
    
    def unregister(self, name: str):
        """注销智能体"""
        if name in self._agents:
            del self._agents[name]
            logger.info(f"注销智能体: {name}")
    
    def get(self, name: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self._agents.get(name)
    
    def list_agents(self) -> List[str]:
        """列出所有智能体名称"""
        return list(self._agents.keys())
    
    def get_active_agents(self) -> List[BaseAgent]:
        """获取所有活跃的智能体"""
        return [agent for agent in self._agents.values() if agent.is_active]


# 全局智能体注册表
agent_registry = AgentRegistry()
