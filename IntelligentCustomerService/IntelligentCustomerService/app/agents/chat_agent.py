"""
聊天智能体
负责处理用户对话，管理会话上下文，协调其他智能体
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime

from autogen_core import CancellationToken

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ChatAgent(BaseAgent):
    """
    聊天智能体
    
    主要职责：
    - 处理用户对话请求
    - 管理会话上下文和状态
    - 协调其他智能体的调用
    - 生成自然流畅的回复
    - 处理多轮对话逻辑
    """
    
    def __init__(
        self,
        name: str = "ChatAgent",
        system_message: str = None,
        model_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        初始化聊天智能体
        
        Args:
            name: 智能体名称
            system_message: 系统提示词
            model_config: 模型配置
            **kwargs: 其他配置参数
        """
        if system_message is None:
            system_message = self._get_default_system_message()
        
        super().__init__(
            name=name,
            system_message=system_message,
            model_config=model_config,
            **kwargs
        )
        
        # 聊天特定配置
        self.conversation_history = []
        self.max_history_length = model_config.get('max_history_length', 20) if model_config else 20
        self.temperature = model_config.get('temperature', 0.7) if model_config else 0.7
        self.max_tokens = model_config.get('max_tokens', 2048) if model_config else 2048
        
        # 协作智能体引用
        self.knowledge_agent = None
        self.tool_agent = None
        self.multimodal_agent = None
        
        logger.info(f"聊天智能体 {self.name} 初始化完成")
    
    def _get_default_system_message(self) -> str:
        """获取默认系统提示词"""
        return """你是一个专业、友好的智能客服助手。你的主要职责是：

1. 理解用户的问题和需求
2. 提供准确、有用的回答
3. 在需要时调用其他专业智能体协助
4. 保持对话的连贯性和上下文理解
5. 以友好、专业的语气与用户交流

请始终保持礼貌、耐心，并尽力帮助用户解决问题。如果遇到不确定的问题，请诚实说明并寻求帮助。"""
    
    def set_collaborator_agents(
        self,
        knowledge_agent=None,
        tool_agent=None,
        multimodal_agent=None
    ):
        """
        设置协作智能体
        
        Args:
            knowledge_agent: 知识检索智能体
            tool_agent: 工具调用智能体
            multimodal_agent: 多模态智能体
        """
        self.knowledge_agent = knowledge_agent
        self.tool_agent = tool_agent
        self.multimodal_agent = multimodal_agent
        
        logger.debug(f"为聊天智能体 {self.name} 设置协作智能体")
    
    async def _handle_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> str:
        """
        处理聊天消息的核心逻辑
        
        Args:
            message: 用户消息
            context: 上下文信息
            cancellation_token: 取消令牌
            
        Returns:
            聊天回复
        """
        try:
            # 分析消息意图
            intent = await self._analyze_intent(message, context)
            
            # 根据意图决定处理策略
            if intent.get('needs_knowledge_search'):
                # 需要知识检索
                response = await self._handle_with_knowledge(message, context, intent)
            elif intent.get('needs_tool_call'):
                # 需要工具调用
                response = await self._handle_with_tools(message, context, intent)
            elif intent.get('has_multimodal_content'):
                # 包含多模态内容
                response = await self._handle_multimodal(message, context, intent)
            else:
                # 普通对话
                response = await self._handle_normal_chat(message, context, intent)
            
            # 更新对话历史
            await self._update_conversation_history(message, response, context)
            
            return response
            
        except Exception as e:
            logger.error(f"聊天智能体处理消息失败: {str(e)}")
            return "抱歉，我在处理您的消息时遇到了问题，请稍后再试。"
    
    async def _analyze_intent(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析用户消息意图
        
        Args:
            message: 用户消息
            context: 上下文信息
            
        Returns:
            意图分析结果
        """
        intent = {
            'needs_knowledge_search': False,
            'needs_tool_call': False,
            'has_multimodal_content': False,
            'intent_type': 'general_chat',
            'confidence': 0.0,
            'entities': [],
            'keywords': []
        }
        
        # 简单的意图识别逻辑（可以后续用更复杂的NLP模型替换）
        message_lower = message.lower()
        
        # 检查是否需要知识搜索
        knowledge_keywords = ['什么是', '如何', '怎么', '为什么', '介绍', '说明', '解释']
        if any(keyword in message_lower for keyword in knowledge_keywords):
            intent['needs_knowledge_search'] = True
            intent['intent_type'] = 'knowledge_query'
            intent['confidence'] = 0.8
        
        # 检查是否需要工具调用
        tool_keywords = ['查询', '搜索', '订单', '商品', '购买', '支付', '退款']
        if any(keyword in message_lower for keyword in tool_keywords):
            intent['needs_tool_call'] = True
            intent['intent_type'] = 'tool_request'
            intent['confidence'] = 0.9
        
        # 检查是否包含多模态内容
        if context and (context.get('images') or context.get('files')):
            intent['has_multimodal_content'] = True
            intent['intent_type'] = 'multimodal_query'
            intent['confidence'] = 1.0
        
        logger.debug(f"意图分析结果: {intent}")
        return intent
    
    async def _handle_with_knowledge(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> str:
        """
        使用知识检索处理消息
        
        Args:
            message: 用户消息
            context: 上下文信息
            intent: 意图分析结果
            
        Returns:
            基于知识的回复
        """
        if not self.knowledge_agent:
            return await self._handle_normal_chat(message, context, intent)
        
        try:
            # 调用知识检索智能体
            knowledge_response = await self.knowledge_agent.process_message(
                message, context
            )
            
            # 基于检索结果生成回复
            if knowledge_response and knowledge_response.strip():
                return f"根据我的知识库，{knowledge_response}"
            else:
                return "抱歉，我没有找到相关的信息。您能提供更多详细信息吗？"
                
        except Exception as e:
            logger.error(f"知识检索处理失败: {str(e)}")
            return await self._handle_normal_chat(message, context, intent)
    
    async def _handle_with_tools(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> str:
        """
        使用工具调用处理消息
        
        Args:
            message: 用户消息
            context: 上下文信息
            intent: 意图分析结果
            
        Returns:
            基于工具调用的回复
        """
        if not self.tool_agent:
            return await self._handle_normal_chat(message, context, intent)
        
        try:
            # 调用工具智能体
            tool_response = await self.tool_agent.process_message(
                message, context
            )
            
            # 基于工具执行结果生成回复
            if tool_response and tool_response.strip():
                return tool_response
            else:
                return "抱歉，我无法执行您请求的操作。请检查您的请求是否正确。"
                
        except Exception as e:
            logger.error(f"工具调用处理失败: {str(e)}")
            return await self._handle_normal_chat(message, context, intent)
    
    async def _handle_multimodal(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> str:
        """
        处理多模态内容
        
        Args:
            message: 用户消息
            context: 上下文信息
            intent: 意图分析结果
            
        Returns:
            多模态处理回复
        """
        if not self.multimodal_agent:
            return "抱歉，我目前无法处理图片或文件内容。"
        
        try:
            # 调用多模态智能体
            multimodal_response = await self.multimodal_agent.process_message(
                message, context
            )
            
            return multimodal_response or "我已经查看了您提供的内容，但无法给出具体分析。"
            
        except Exception as e:
            logger.error(f"多模态处理失败: {str(e)}")
            return "抱歉，我在处理您提供的内容时遇到了问题。"
    
    async def _handle_normal_chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> str:
        """
        处理普通对话
        
        Args:
            message: 用户消息
            context: 上下文信息
            intent: 意图分析结果
            
        Returns:
            对话回复
        """
        try:
            # 构建对话上下文
            conversation_context = await self._build_conversation_context(context)
            
            # 调用模型服务生成回复
            if self.model_service:
                response = await self.model_service.chat_completion(
                    messages=conversation_context + [{"role": "user", "content": message}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response
            else:
                # 简单的回复逻辑（当模型服务不可用时）
                return self._generate_simple_response(message, intent)
                
        except Exception as e:
            logger.error(f"普通对话处理失败: {str(e)}")
            return "我理解您的问题，但目前无法给出详细回答。请稍后再试。"
    
    async def _build_conversation_context(
        self,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        构建对话上下文
        
        Args:
            context: 上下文信息
            
        Returns:
            对话历史列表
        """
        conversation_context = [{"role": "system", "content": self.system_message}]
        
        # 添加历史对话
        if self.conversation_history:
            # 只保留最近的对话历史
            recent_history = self.conversation_history[-self.max_history_length:]
            conversation_context.extend(recent_history)
        
        return conversation_context
    
    def _generate_simple_response(
        self,
        message: str,
        intent: Dict[str, Any]
    ) -> str:
        """
        生成简单回复（当模型服务不可用时）
        
        Args:
            message: 用户消息
            intent: 意图分析结果
            
        Returns:
            简单回复
        """
        message_lower = message.lower()
        
        # 问候语
        if any(greeting in message_lower for greeting in ['你好', 'hello', '您好']):
            return "您好！我是智能客服助手，很高兴为您服务。请问有什么可以帮助您的吗？"
        
        # 感谢
        if any(thanks in message_lower for thanks in ['谢谢', 'thank', '感谢']):
            return "不客气！如果您还有其他问题，随时可以问我。"
        
        # 再见
        if any(bye in message_lower for bye in ['再见', 'bye', '拜拜']):
            return "再见！祝您生活愉快，有问题随时联系我。"
        
        # 默认回复
        return "我理解您的问题，正在为您查找相关信息。请稍等片刻。"
    
    async def _update_conversation_history(
        self,
        user_message: str,
        assistant_response: str,
        context: Optional[Dict[str, Any]]
    ):
        """
        更新对话历史
        
        Args:
            user_message: 用户消息
            assistant_response: 助手回复
            context: 上下文信息
        """
        # 添加到内存对话历史
        self.conversation_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response}
        ])
        
        # 保持历史长度限制
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
        
        logger.debug(f"更新对话历史，当前长度: {len(self.conversation_history)}")
    
    async def stream_chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天接口
        
        Args:
            message: 用户消息
            context: 上下文信息
            
        Yields:
            流式响应片段
        """
        try:
            # 分析意图
            intent = await self._analyze_intent(message, context)
            
            # 构建对话上下文
            conversation_context = await self._build_conversation_context(context)
            
            # 流式生成回复
            if self.model_service:
                async for chunk in self.model_service.chat_completion_stream(
                    messages=conversation_context + [{"role": "user", "content": message}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                ):
                    yield chunk
            else:
                # 模拟流式输出
                response = await self._handle_message(message, context)
                for char in response:
                    yield char
                    await asyncio.sleep(0.01)  # 模拟打字效果
                    
        except Exception as e:
            logger.error(f"流式聊天失败: {str(e)}")
            yield "抱歉，我在处理您的消息时遇到了问题。"
    
    def clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info(f"清空聊天智能体 {self.name} 的对话历史")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        获取对话摘要
        
        Returns:
            对话摘要信息
        """
        return {
            'total_messages': len(self.conversation_history),
            'user_messages': len([msg for msg in self.conversation_history if msg['role'] == 'user']),
            'assistant_messages': len([msg for msg in self.conversation_history if msg['role'] == 'assistant']),
            'last_message_time': self.last_activity.isoformat() if self.last_activity else None,
            'conversation_length': sum(len(msg['content']) for msg in self.conversation_history)
        }
