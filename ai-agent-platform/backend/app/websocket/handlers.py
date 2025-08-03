"""
WebSocket消息处理器

处理不同类型的WebSocket消息和事件。
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .manager import ConnectionManager, WebSocketConnection
from .events import *
from ..agents.base import agent_registry
from ..agents.workflow import workflow_manager
from ..rag.rag_agent import RAGAgent

logger = logging.getLogger(__name__)


class BaseHandler:
    """基础处理器"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def handle_message(self, connection: WebSocketConnection, message: Dict[str, Any]):
        """处理消息"""
        try:
            event_type = message.get("type")
            data = message.get("data", {})
            
            handler_method = getattr(self, f"handle_{event_type}", None)
            if handler_method:
                await handler_method(connection, data)
            else:
                await self.handle_unknown_message(connection, message)
                
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
            await connection.send_error(f"消息处理失败: {str(e)}")
    
    async def handle_unknown_message(self, connection: WebSocketConnection, message: Dict[str, Any]):
        """处理未知消息"""
        await connection.send_error("未知的消息类型", "UNKNOWN_MESSAGE_TYPE")


class ChatHandler(BaseHandler):
    """聊天处理器"""
    
    def __init__(self, connection_manager: ConnectionManager):
        super().__init__(connection_manager)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def handle_chat_message(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """处理聊天消息"""
        try:
            # 解析消息
            content = data.get("content", "")
            agent_type = data.get("agent_type", "customer_service")
            session_id = data.get("session_id", f"session_{connection.user_id}")
            
            if not content.strip():
                await connection.send_error("消息内容不能为空", "EMPTY_MESSAGE")
                return
            
            # 创建聊天消息
            message = ChatMessage(
                message_id=f"msg_{datetime.now().timestamp()}",
                content=content,
                sender="user",
                metadata=data.get("metadata", {})
            )
            
            # 发送消息确认
            await connection.send_message(create_chat_message_event(
                message, connection.user_id, session_id
            ).to_dict())
            
            # 显示智能体思考状态
            await self._send_agent_thinking(connection, agent_type)
            
            # 获取智能体响应
            response = await self._get_agent_response(
                agent_type, content, connection.user_id, session_id, data.get("metadata", {})
            )
            
            # 发送响应
            await connection.send_message(create_chat_response_event(
                response, connection.user_id, session_id
            ).to_dict())
            
        except Exception as e:
            logger.error(f"聊天消息处理失败: {e}")
            await connection.send_error(f"聊天处理失败: {str(e)}")
    
    async def handle_agent_select(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """处理智能体选择"""
        try:
            agent_type = data.get("agent_type")
            session_id = data.get("session_id", f"session_{connection.user_id}")
            
            # 验证智能体类型
            if agent_type not in ["customer_service", "text2sql", "knowledge_qa", "content_creation"]:
                await connection.send_error("无效的智能体类型", "INVALID_AGENT_TYPE")
                return
            
            # 更新会话信息
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {}
            self.active_sessions[session_id]["agent_type"] = agent_type
            self.active_sessions[session_id]["user_id"] = connection.user_id
            
            # 发送确认
            await connection.send_message({
                "type": "agent_selected",
                "data": {
                    "agent_type": agent_type,
                    "session_id": session_id,
                    "message": f"已选择{self._get_agent_name(agent_type)}智能体"
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"智能体选择处理失败: {e}")
            await connection.send_error(f"智能体选择失败: {str(e)}")
    
    async def handle_chat_history(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """处理聊天历史请求"""
        try:
            session_id = data.get("session_id", f"session_{connection.user_id}")
            limit = data.get("limit", 50)
            
            # 这里应该从数据库获取聊天历史
            # 暂时返回空历史
            history = []
            
            await connection.send_message({
                "type": "chat_history",
                "data": {
                    "session_id": session_id,
                    "messages": history,
                    "total": len(history)
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"聊天历史处理失败: {e}")
            await connection.send_error(f"获取聊天历史失败: {str(e)}")
    
    async def _send_agent_thinking(self, connection: WebSocketConnection, agent_type: str):
        """发送智能体思考状态"""
        await connection.send_message({
            "type": "agent_thinking",
            "data": {
                "agent_type": agent_type,
                "message": f"{self._get_agent_name(agent_type)}正在思考中..."
            },
            "timestamp": datetime.now().isoformat()
        })
    
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
        # 这里应该调用实际的客服智能体
        return f"感谢您的咨询：{content}。我们的客服团队会尽快为您处理。如果您有紧急问题，请拨打客服热线。"
    
    async def _get_text2sql_response(self, content: str, metadata: Dict[str, Any]) -> str:
        """获取Text2SQL智能体响应"""
        # 这里应该调用实际的Text2SQL智能体
        return f"您的查询：{content}\n\n生成的SQL：\n```sql\nSELECT * FROM users WHERE name LIKE '%{content}%';\n```\n\n请注意，这是一个示例SQL，实际使用时请根据您的数据库结构调整。"
    
    async def _get_knowledge_qa_response(self, content: str, metadata: Dict[str, Any]) -> str:
        """获取知识库问答智能体响应"""
        # 这里应该调用实际的知识库问答智能体
        return f"根据知识库搜索，关于\"{content}\"的信息如下：\n\n这是一个示例回答。实际使用时，系统会从知识库中检索相关信息并生成准确的答案。\n\n如果您需要更详细的信息，请提供更具体的问题。"
    
    async def _get_content_creation_response(self, content: str, metadata: Dict[str, Any]) -> str:
        """获取内容创作智能体响应"""
        # 这里应该调用实际的内容创作智能体
        return f"基于您的需求"{content}"，我为您创作了以下内容：\n\n这是一个示例创作内容。实际使用时，系统会根据您的具体要求生成高质量的文案、文章或其他类型的内容。\n\n如果您需要调整风格或内容，请告诉我具体的要求。"
    
    def _get_agent_name(self, agent_type: str) -> str:
        """获取智能体名称"""
        names = {
            "customer_service": "客服",
            "text2sql": "数据分析",
            "knowledge_qa": "知识问答",
            "content_creation": "内容创作"
        }
        return names.get(agent_type, "智能")


class WorkflowHandler(BaseHandler):
    """工作流处理器"""
    
    async def handle_workflow_start(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """处理工作流启动"""
        try:
            user_request = data.get("user_request", "")
            context = data.get("context", {})
            
            if not user_request.strip():
                await connection.send_error("请求内容不能为空", "EMPTY_REQUEST")
                return
            
            # 创建工作流
            workflow_id = f"workflow_{datetime.now().timestamp()}"
            
            # 发送工作流启动事件
            await connection.send_message({
                "type": "workflow_started",
                "data": {
                    "workflow_id": workflow_id,
                    "user_request": user_request,
                    "status": "started"
                },
                "timestamp": datetime.now().isoformat()
            })
            
            # 模拟工作流进度更新
            await self._simulate_workflow_progress(connection, workflow_id)
            
        except Exception as e:
            logger.error(f"工作流启动失败: {e}")
            await connection.send_error(f"工作流启动失败: {str(e)}")
    
    async def handle_workflow_status(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """处理工作流状态查询"""
        try:
            workflow_id = data.get("workflow_id")
            
            if not workflow_id:
                await connection.send_error("工作流ID不能为空", "MISSING_WORKFLOW_ID")
                return
            
            # 这里应该查询实际的工作流状态
            progress = WorkflowProgress(
                workflow_id=workflow_id,
                status="running",
                current_step="数据分析",
                completed_steps=2,
                total_steps=5,
                progress_percentage=40.0,
                estimated_remaining_time=300
            )
            
            await connection.send_message(create_workflow_progress_event(
                progress, connection.user_id
            ).to_dict())
            
        except Exception as e:
            logger.error(f"工作流状态查询失败: {e}")
            await connection.send_error(f"工作流状态查询失败: {str(e)}")
    
    async def _simulate_workflow_progress(self, connection: WebSocketConnection, workflow_id: str):
        """模拟工作流进度"""
        steps = [
            "分析请求",
            "制定计划", 
            "执行任务",
            "生成结果",
            "完成"
        ]
        
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
            
            await connection.send_message(create_workflow_progress_event(
                progress, connection.user_id
            ).to_dict())
        
        # 发送完成事件
        await connection.send_message({
            "type": "workflow_completed",
            "data": {
                "workflow_id": workflow_id,
                "result": "工作流执行完成，所有任务已成功处理。",
                "execution_time": len(steps) * 2
            },
            "timestamp": datetime.now().isoformat()
        })
