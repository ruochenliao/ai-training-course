"""
基础智能体类
所有智能体的基类，提供通用功能和接口
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from autogen_agentchat import ConversableAgent
from autogen_core import CancellationToken

logger = logging.getLogger(__name__)


class BaseAgent(ConversableAgent, ABC):
    """
    基础智能体类
    
    提供所有智能体的通用功能：
    - 消息处理
    - 状态管理
    - 错误处理
    - 日志记录
    - 性能监控
    """
    
    def __init__(
        self,
        name: str,
        system_message: str,
        model_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        初始化基础智能体
        
        Args:
            name: 智能体名称
            system_message: 系统提示词
            model_config: 模型配置
            **kwargs: 其他配置参数
        """
        super().__init__(
            name=name,
            system_message=system_message,
            **kwargs
        )
        
        self.model_config = model_config or {}
        self.agent_type = self.__class__.__name__
        self.created_at = datetime.now()
        self.message_count = 0
        self.error_count = 0
        self.last_activity = datetime.now()
        
        # 服务依赖注入
        self.memory_service = None
        self.tool_service = None
        self.knowledge_service = None
        self.model_service = None
        
        logger.info(f"初始化智能体: {self.name} ({self.agent_type})")
    
    def inject_services(
        self,
        memory_service=None,
        tool_service=None,
        knowledge_service=None,
        model_service=None
    ):
        """
        注入服务依赖
        
        Args:
            memory_service: 记忆服务
            tool_service: 工具服务
            knowledge_service: 知识库服务
            model_service: 模型服务
        """
        self.memory_service = memory_service
        self.tool_service = tool_service
        self.knowledge_service = knowledge_service
        self.model_service = model_service
        
        logger.debug(f"为智能体 {self.name} 注入服务依赖")
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> str:
        """
        处理消息的主要入口
        
        Args:
            message: 输入消息
            context: 上下文信息
            cancellation_token: 取消令牌
            
        Returns:
            处理后的响应消息
        """
        try:
            self.message_count += 1
            self.last_activity = datetime.now()
            
            logger.debug(f"智能体 {self.name} 开始处理消息: {message[:100]}...")
            
            # 预处理
            processed_message = await self._preprocess_message(message, context)
            
            # 核心处理逻辑（由子类实现）
            response = await self._handle_message(processed_message, context, cancellation_token)
            
            # 后处理
            final_response = await self._postprocess_response(response, context)
            
            logger.debug(f"智能体 {self.name} 完成消息处理")
            return final_response
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"智能体 {self.name} 处理消息时发生错误: {str(e)}")
            return await self._handle_error(e, message, context)
    
    @abstractmethod
    async def _handle_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> str:
        """
        核心消息处理逻辑（由子类实现）
        
        Args:
            message: 预处理后的消息
            context: 上下文信息
            cancellation_token: 取消令牌
            
        Returns:
            处理结果
        """
        pass
    
    async def _preprocess_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        消息预处理
        
        Args:
            message: 原始消息
            context: 上下文信息
            
        Returns:
            预处理后的消息
        """
        # 基础预处理：去除多余空格、格式化等
        processed = message.strip()
        
        # 记录到记忆服务
        if self.memory_service and context:
            await self.memory_service.add_message(
                user_id=context.get('user_id'),
                role='user',
                content=processed,
                metadata={'agent': self.name, 'timestamp': datetime.now().isoformat()}
            )
        
        return processed
    
    async def _postprocess_response(
        self,
        response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        响应后处理
        
        Args:
            response: 原始响应
            context: 上下文信息
            
        Returns:
            后处理后的响应
        """
        # 基础后处理：格式化、添加元信息等
        processed = response.strip()
        
        # 记录到记忆服务
        if self.memory_service and context:
            await self.memory_service.add_message(
                user_id=context.get('user_id'),
                role='assistant',
                content=processed,
                metadata={'agent': self.name, 'timestamp': datetime.now().isoformat()}
            )
        
        return processed
    
    async def _handle_error(
        self,
        error: Exception,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        错误处理
        
        Args:
            error: 异常对象
            message: 原始消息
            context: 上下文信息
            
        Returns:
            错误响应消息
        """
        error_msg = f"抱歉，我在处理您的请求时遇到了问题。错误类型：{type(error).__name__}"
        
        # 记录错误日志
        logger.error(
            f"智能体 {self.name} 错误处理",
            extra={
                'agent_name': self.name,
                'agent_type': self.agent_type,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'input_message': message,
                'context': context
            }
        )
        
        return error_msg
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取智能体状态信息
        
        Returns:
            状态信息字典
        """
        return {
            'name': self.name,
            'type': self.agent_type,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'message_count': self.message_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.message_count, 1),
            'is_healthy': self.error_count / max(self.message_count, 1) < 0.1
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.message_count = 0
        self.error_count = 0
        self.last_activity = datetime.now()
        logger.info(f"重置智能体 {self.name} 的统计信息")
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            健康状态
        """
        try:
            # 基础健康检查
            if self.error_count / max(self.message_count, 1) > 0.5:
                return False
            
            # 检查服务依赖
            if self.memory_service:
                # 可以添加记忆服务健康检查
                pass
            
            if self.model_service:
                # 可以添加模型服务健康检查
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"智能体 {self.name} 健康检查失败: {str(e)}")
            return False
    
    def __str__(self) -> str:
        return f"{self.agent_type}(name={self.name})"
    
    def __repr__(self) -> str:
        return (
            f"{self.agent_type}("
            f"name={self.name}, "
            f"messages={self.message_count}, "
            f"errors={self.error_count})"
        )
