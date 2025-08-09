# Copyright (c) 2025 左岚. All rights reserved.
"""
SSE消息处理器

处理不同类型的SSE消息和事件。
"""

# # Standard library imports
import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, Optional

# # Local folder imports
from .events import *
from .manager import SSEConnection, SSEManager

logger = logging.getLogger(__name__)


class BaseHandler:
    """基础处理器"""
    
    def __init__(self, sse_manager: SSEManager):
        self.sse_manager = sse_manager
    
    async def handle_request(self, connection: SSEConnection, data: Dict[str, Any]):
        """处理请求"""
        try:
            request_type = data.get("type")
            request_data = data.get("data", {})
            
            handler_method = getattr(self, f"handle_{request_type}", None)
            if handler_method:
                await handler_method(connection, request_data)
            else:
                await self.handle_unknown_request(connection, data)
                
        except Exception as e:
            logger.error(f"请求处理失败: {e}")
            await connection.send_error(f"请求处理失败: {str(e)}")
    
    async def handle_unknown_request(self, connection: SSEConnection, data: Dict[str, Any]):
        """处理未知请求"""
        await connection.send_error("未知的请求类型", "UNKNOWN_REQUEST_TYPE")


class ChatHandler(BaseHandler):
    """聊天处理器"""
    
    def __init__(self, sse_manager: SSEManager):
        super().__init__(sse_manager)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def handle_chat_message(self, user_id: str, content: str, agent_type: str = "customer_service", 
                                 session_id: str = None, metadata: Dict[str, Any] = None):
        """处理聊天消息"""
        try:
            if not session_id:
                session_id = f"session_{user_id}"
            
            if not content.strip():
                error_event = create_error_event("消息内容不能为空", "EMPTY_MESSAGE", user_id, session_id)
                await self.sse_manager.send_to_user(user_id, error_event)
                return
            
            # 创建聊天消息
            message = ChatMessage(
                message_id=f"msg_{datetime.now().timestamp()}",
                content=content,
                sender="user",
                metadata=metadata or {}
            )
            
            # 发送消息确认
            message_event = chat_message_event(message, user_id, session_id)
            await self.sse_manager.send_to_user(user_id, message_event)

            # 显示智能体思考状态
            thinking_event = agent_thinking_event(agent_type, user_id, session_id)
            await self.sse_manager.send_to_user(user_id, thinking_event)
            
            # 获取智能体响应
            response = await self._get_agent_response(
                agent_type, content, user_id, session_id, metadata or {}
            )
            
            # 发送响应
            response_event = chat_response_event(response, user_id, session_id)
            await self.sse_manager.send_to_user(user_id, response_event)
            
        except Exception as e:
            logger.error(f"聊天消息处理失败: {e}")
            error_event = error_event(f"聊天处理失败: {str(e)}", "CHAT_ERROR", user_id, session_id)
            await self.sse_manager.send_to_user(user_id, error_event)
    
    async def handle_agent_select(self, user_id: str, agent_type: str, session_id: str = None):
        """处理智能体选择"""
        try:
            if not session_id:
                session_id = f"session_{user_id}"
            
            # 验证智能体类型
            if agent_type not in ["customer_service", "text2sql", "knowledge_qa", "content_creation"]:
                error_event = create_error_event("无效的智能体类型", "INVALID_AGENT_TYPE", user_id, session_id)
                await self.sse_manager.send_to_user(user_id, error_event)
                return
            
            # 更新会话信息
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {}
            self.active_sessions[session_id]["agent_type"] = agent_type
            self.active_sessions[session_id]["user_id"] = user_id
            
            # 发送确认事件
            select_event = SSEEvent(
                event_type="agent_selected",
                data={
                    "agent_type": agent_type,
                    "session_id": session_id,
                    "message": f"已选择{get_agent_name(agent_type)}智能体"
                },
                user_id=user_id,
                session_id=session_id
            )
            await self.sse_manager.send_to_user(user_id, select_event)
            
        except Exception as e:
            logger.error(f"智能体选择处理失败: {e}")
            error_event = create_error_event(f"智能体选择失败: {str(e)}", "AGENT_SELECT_ERROR", user_id, session_id)
            await self.sse_manager.send_to_user(user_id, error_event)
    
    async def _get_agent_response(self, agent_type: str, content: str, user_id: str, 
                                session_id: str, metadata: Dict[str, Any]) -> ChatResponse:
        """获取智能体响应"""
        try:
            # 根据智能体类型获取响应
            if agent_type == "customer_service":
                response_content = await self._get_customer_service_response(content, metadata)
            elif agent_type == "text2sql":
                response_content = await self._get_text2sql_response(content, metadata)
            elif agent_type == "knowledge_qa":
                response_content = await self._get_knowledge_qa_response(content, metadata)
            elif agent_type == "content_creation":
                response_content = await self._get_content_creation_response(content, metadata)
            else:
                response_content = "抱歉，暂不支持该类型的智能体。"
            
            return ChatResponse(
                message_id=f"resp_{datetime.now().timestamp()}",
                response_to=f"msg_{datetime.now().timestamp()}",
                content=response_content,
                agent_type=agent_type,
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"获取智能体响应失败: {e}")
            return ChatResponse(
                message_id=f"resp_{datetime.now().timestamp()}",
                response_to="",
                content=f"抱歉，处理您的请求时出现错误: {str(e)}",
                agent_type=agent_type,
                confidence=0.0
            )
    
    async def _get_customer_service_response(self, content: str, metadata: Dict[str, Any]) -> str:
        """获取客服智能体响应"""
        # 模拟处理时间
        await asyncio.sleep(1)
        return f"感谢您的咨询：{content}。我们的客服团队会尽快为您处理。如果您有紧急问题，请拨打客服热线。"
    
    async def _get_text2sql_response(self, content: str, metadata: Dict[str, Any]) -> str:
        """获取Text2SQL智能体响应"""
        await asyncio.sleep(2)
        return f"您的查询：{content}\n\n生成的SQL：\n```sql\nSELECT * FROM users WHERE name LIKE '%{content}%';\n```\n\n请注意，这是一个示例SQL，实际使用时请根据您的数据库结构调整。"
    
    async def _get_knowledge_qa_response(self, content: str, metadata: Dict[str, Any]) -> str:
        """获取知识库问答智能体响应"""
        await asyncio.sleep(1.5)
        return f"根据知识库搜索，关于\"{content}\"的信息如下：\n\n这是一个示例回答。实际使用时，系统会从知识库中检索相关信息并生成准确的答案。\n\n如果您需要更详细的信息，请提供更具体的问题。"
    
    async def _get_content_creation_response(self, content: str, metadata: Dict[str, Any]) -> str:
        """获取内容创作智能体响应"""
        await asyncio.sleep(2.5)
        return f"基于您的需求\"{content}\"，我为您创作了以下内容：\n\n这是一个示例创作内容。实际使用时，系统会根据您的具体要求生成高质量的文案、文章或其他类型的内容。\n\n如果您需要调整风格或内容，请告诉我具体的要求。"


class WorkflowHandler(BaseHandler):
    """工作流处理器"""
    
    async def handle_workflow_start(self, user_id: str, user_request: str, context: Dict[str, Any] = None):
        """处理工作流启动"""
        try:
            if not user_request.strip():
                error_event = create_error_event("请求内容不能为空", "EMPTY_REQUEST", user_id)
                await self.sse_manager.send_to_user(user_id, error_event)
                return
            
            # 创建工作流
            workflow_id = f"workflow_{datetime.now().timestamp()}"
            
            # 发送工作流启动事件
            start_event = SSEEvent(
                event_type="workflow_started",
                data={
                    "workflow_id": workflow_id,
                    "user_request": user_request,
                    "status": "started"
                },
                user_id=user_id
            )
            await self.sse_manager.send_to_user(user_id, start_event)
            
            # 模拟工作流进度更新
            await self._simulate_workflow_progress(user_id, workflow_id)
            
        except Exception as e:
            logger.error(f"工作流启动失败: {e}")
            error_event = create_error_event(f"工作流启动失败: {str(e)}", "WORKFLOW_ERROR", user_id)
            await self.sse_manager.send_to_user(user_id, error_event)
    
    async def _simulate_workflow_progress(self, user_id: str, workflow_id: str):
        """模拟工作流进度"""
        steps = ["分析请求", "制定计划", "执行任务", "生成结果", "完成"]
        
        for i, step in enumerate(steps):
            await asyncio.sleep(2)  # 模拟处理时间
            
            progress = WorkflowProgress(
                workflow_id=workflow_id,
                status="running" if i < len(steps) - 1 else "completed",
                current_step=step,
                completed_steps=i + 1,
                total_steps=len(steps),
                progress_percentage=(i + 1) / len(steps) * 100,
                estimated_remaining_time=(len(steps) - i - 1) * 2
            )
            
            progress_event = create_workflow_progress_event(progress, user_id)
            await self.sse_manager.send_to_user(user_id, progress_event)
        
        # 发送完成事件
        complete_event = SSEEvent(
            event_type="workflow_completed",
            data={
                "workflow_id": workflow_id,
                "result": "工作流执行完成，所有任务已成功处理。",
                "execution_time": len(steps) * 2
            },
            user_id=user_id
        )
        await self.sse_manager.send_to_user(user_id, complete_event)
