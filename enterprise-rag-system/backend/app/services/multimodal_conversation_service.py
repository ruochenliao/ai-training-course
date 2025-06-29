"""
多模态对话服务 - 企业级RAG系统
严格按照技术栈要求：整合AutoGen智能体、deepseek-chat、qwen-vl-max多模态能力
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger

from app import autogen_service
from app import deepseek_llm_service
from app import milvus_service
from app import neo4j_service
from app import qwen_multimodal_service
from app.core import get_db_session
from app.models import Conversation, Message, MessageRole, ContentType


class MultimodalConversationService:
    """多模态对话服务"""
    
    def __init__(self):
        self.active_conversations = {}
        self.conversation_configs = {
            "max_history_length": 20,
            "max_image_size": 10 * 1024 * 1024,  # 10MB
            "supported_image_formats": {"jpg", "jpeg", "png", "bmp", "gif", "webp"},
            "enable_autogen": True,
            "enable_multimodal": True
        }
    
    async def create_conversation(
        self,
        user_id: int,
        knowledge_base_id: Optional[int] = None,
        agent_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建新对话"""
        try:
            conversation_id = str(uuid.uuid4())
            
            # 创建数据库记录
            async with get_db_session() as session:
                db_conversation = Conversation(
                    user_id=user_id,
                    knowledge_base_id=knowledge_base_id,
                    title="新对话",
                    agent_config=agent_config or {},
                    search_mode="auto"
                )
                session.add(db_conversation)
                await session.commit()
                await session.refresh(db_conversation)
                
                conversation_id = str(db_conversation.id)
            
            # 如果有知识库，创建AutoGen智能体群聊
            autogen_chat_id = None
            if knowledge_base_id and self.conversation_configs["enable_autogen"]:
                try:
                    autogen_chat_id = await autogen_service.create_group_chat(
                        conversation_id, knowledge_base_id
                    )
                except Exception as e:
                    logger.warning(f"创建AutoGen群聊失败: {e}")
            
            # 存储活跃对话信息
            self.active_conversations[conversation_id] = {
                "user_id": user_id,
                "knowledge_base_id": knowledge_base_id,
                "autogen_chat_id": autogen_chat_id,
                "agent_config": agent_config or {},
                "created_at": datetime.now(),
                "message_count": 0,
                "last_activity": datetime.now()
            }
            
            logger.info(f"对话创建成功: {conversation_id}")
            return {
                "success": True,
                "conversation_id": conversation_id,
                "autogen_enabled": autogen_chat_id is not None,
                "multimodal_enabled": self.conversation_configs["enable_multimodal"]
            }
            
        except Exception as e:
            logger.error(f"创建对话失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_message(
        self,
        conversation_id: str,
        content: str,
        content_type: ContentType = ContentType.TEXT,
        attachments: Optional[List[Dict[str, Any]]] = None,
        use_agents: bool = True
    ) -> Dict[str, Any]:
        """发送消息"""
        try:
            if conversation_id not in self.active_conversations:
                return {
                    "success": False,
                    "error": "对话不存在或已过期"
                }
            
            conv_info = self.active_conversations[conversation_id]
            start_time = datetime.now()
            
            # 保存用户消息
            await self._save_message(
                conversation_id, MessageRole.USER, content, content_type, attachments
            )
            
            # 处理多模态内容
            multimodal_context = None
            if attachments and content_type in [ContentType.IMAGE, ContentType.MIXED]:
                multimodal_context = await self._process_multimodal_content(
                    attachments, content
                )
            
            # 生成回复
            if use_agents and conv_info["autogen_chat_id"]:
                # 使用AutoGen智能体协作
                response = await self._generate_agent_response(
                    conv_info["autogen_chat_id"], content, multimodal_context
                )
            else:
                # 使用单一LLM
                response = await self._generate_llm_response(
                    conversation_id, content, multimodal_context
                )
            
            # 保存助手回复
            await self._save_message(
                conversation_id, MessageRole.ASSISTANT, response["content"],
                ContentType.TEXT, None, response.get("metadata")
            )
            
            # 更新对话信息
            conv_info["message_count"] += 2
            conv_info["last_activity"] = datetime.now()
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "response": response["content"],
                "processing_time_ms": processing_time,
                "agent_used": use_agents and conv_info["autogen_chat_id"] is not None,
                "multimodal_processed": multimodal_context is not None,
                "metadata": response.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "抱歉，处理您的消息时出现了错误。"
            }
    
    async def _process_multimodal_content(
        self,
        attachments: List[Dict[str, Any]],
        text_content: str
    ) -> Dict[str, Any]:
        """处理多模态内容"""
        try:
            multimodal_results = []
            
            for attachment in attachments:
                if attachment.get("type") == "image":
                    image_data = attachment.get("data")
                    filename = attachment.get("filename", "image")
                    
                    if image_data:
                        # 使用qwen-vl-max分析图像
                        if text_content and "?" in text_content:
                            # 图像问答
                            result = await qwen_multimodal_service.image_qa(
                                image_data, text_content, filename=filename
                            )
                        else:
                            # 图像描述
                            result = await qwen_multimodal_service.describe_image_for_search(
                                image_data, filename=filename
                            )
                        
                        if result["success"]:
                            multimodal_results.append({
                                "type": "image_analysis",
                                "filename": filename,
                                "content": result["content"],
                                "model": result["model"]
                            })
            
            return {
                "has_multimodal": len(multimodal_results) > 0,
                "results": multimodal_results,
                "processed_count": len(multimodal_results)
            }
            
        except Exception as e:
            logger.error(f"多模态内容处理失败: {e}")
            return {
                "has_multimodal": False,
                "results": [],
                "error": str(e)
            }
    
    async def _generate_agent_response(
        self,
        autogen_chat_id: str,
        query: str,
        multimodal_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用AutoGen智能体生成回复"""
        try:
            # 构建上下文
            context = {}
            if multimodal_context and multimodal_context["has_multimodal"]:
                context["multimodal_analysis"] = multimodal_context["results"]
            
            # 调用AutoGen智能体
            result = await autogen_service.process_query(
                autogen_chat_id, query, context
            )
            
            if result["success"]:
                return {
                    "content": result["answer"],
                    "metadata": {
                        "source": "autogen_agents",
                        "agents_involved": result.get("agents_involved", []),
                        "processing_time_ms": result.get("processing_time_ms", 0),
                        "message_count": result.get("message_count", 0)
                    }
                }
            else:
                # 如果智能体失败，回退到单一LLM
                logger.warning(f"AutoGen智能体处理失败，回退到LLM: {result.get('error')}")
                return await self._generate_llm_response_direct(query, multimodal_context)
                
        except Exception as e:
            logger.error(f"智能体回复生成失败: {e}")
            # 回退到单一LLM
            return await self._generate_llm_response_direct(query, multimodal_context)
    
    async def _generate_llm_response(
        self,
        conversation_id: str,
        query: str,
        multimodal_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用LLM生成回复"""
        try:
            # 获取对话历史
            history = await self._get_conversation_history(conversation_id)
            
            # 构建上下文
            context_parts = []
            if multimodal_context and multimodal_context["has_multimodal"]:
                for result in multimodal_context["results"]:
                    context_parts.append(f"图像分析结果: {result['content']}")
            
            # 添加对话历史
            for msg in history[-5:]:  # 最近5条消息
                role = "用户" if msg["role"] == "user" else "助手"
                context_parts.append(f"{role}: {msg['content']}")
            
            context = "\n".join(context_parts) if context_parts else None
            
            # 调用DeepSeek LLM
            result = await deepseek_llm_service.generate_response(
                prompt=query,
                context=context,
                system_message="你是一个专业的AI助手，请根据上下文信息回答用户问题。"
            )
            
            if result["success"]:
                return {
                    "content": result["content"],
                    "metadata": {
                        "source": "deepseek_llm",
                        "model": result.get("model"),
                        "usage": result.get("usage", {}),
                        "latency_ms": result.get("latency_ms", 0)
                    }
                }
            else:
                return {
                    "content": "抱歉，我无法处理您的请求。",
                    "metadata": {
                        "source": "error",
                        "error": result.get("error")
                    }
                }
                
        except Exception as e:
            logger.error(f"LLM回复生成失败: {e}")
            return {
                "content": "抱歉，处理您的请求时出现了错误。",
                "metadata": {
                    "source": "error",
                    "error": str(e)
                }
            }
    
    async def _generate_llm_response_direct(
        self,
        query: str,
        multimodal_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """直接使用LLM生成回复（无历史）"""
        try:
            context = None
            if multimodal_context and multimodal_context["has_multimodal"]:
                context_parts = []
                for result in multimodal_context["results"]:
                    context_parts.append(f"图像分析结果: {result['content']}")
                context = "\n".join(context_parts)
            
            result = await deepseek_llm_service.generate_response(
                prompt=query,
                context=context,
                system_message="你是一个专业的AI助手，请根据提供的信息回答用户问题。"
            )
            
            if result["success"]:
                return {
                    "content": result["content"],
                    "metadata": {
                        "source": "deepseek_llm_direct",
                        "model": result.get("model"),
                        "usage": result.get("usage", {}),
                        "latency_ms": result.get("latency_ms", 0)
                    }
                }
            else:
                return {
                    "content": "抱歉，我无法处理您的请求。",
                    "metadata": {
                        "source": "error",
                        "error": result.get("error")
                    }
                }
                
        except Exception as e:
            logger.error(f"直接LLM回复生成失败: {e}")
            return {
                "content": "抱歉，处理您的请求时出现了错误。",
                "metadata": {
                    "source": "error",
                    "error": str(e)
                }
            }
    
    async def _save_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        content_type: ContentType = ContentType.TEXT,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """保存消息到数据库"""
        try:
            async with get_db_session() as session:
                message = Message(
                    conversation_id=int(conversation_id),
                    role=role,
                    content=content,
                    content_type=content_type,
                    attachments=attachments,
                    agent_info=metadata
                )
                session.add(message)
                await session.commit()
                
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
    
    async def _get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取对话历史"""
        try:
            async with get_db_session() as session:
                # TODO: 实现数据库查询逻辑
                # 这里需要查询Message表获取对话历史
                return []
                
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []
    
    async def get_conversation_info(self, conversation_id: str) -> Dict[str, Any]:
        """获取对话信息"""
        if conversation_id in self.active_conversations:
            conv_info = self.active_conversations[conversation_id]
            return {
                "conversation_id": conversation_id,
                "user_id": conv_info["user_id"],
                "knowledge_base_id": conv_info["knowledge_base_id"],
                "autogen_enabled": conv_info["autogen_chat_id"] is not None,
                "message_count": conv_info["message_count"],
                "created_at": conv_info["created_at"].isoformat(),
                "last_activity": conv_info["last_activity"].isoformat()
            }
        else:
            return {"error": "对话不存在"}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查各个服务
            autogen_health = await autogen_service.health_check()
            deepseek_health = await deepseek_llm_service.health_check()
            qwen_health = await qwen_multimodal_service.health_check()
            
            return {
                "status": "healthy",
                "active_conversations": len(self.active_conversations),
                "services": {
                    "autogen": autogen_health,
                    "deepseek_llm": deepseek_health,
                    "qwen_multimodal": qwen_health
                },
                "capabilities": {
                    "text_chat": True,
                    "multimodal": self.conversation_configs["enable_multimodal"],
                    "agent_collaboration": self.conversation_configs["enable_autogen"]
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# 全局多模态对话服务实例
multimodal_conversation_service = MultimodalConversationService()


# 便捷函数
async def create_new_conversation(
    user_id: int,
    knowledge_base_id: Optional[int] = None
) -> Dict[str, Any]:
    """创建新对话的便捷函数"""
    return await multimodal_conversation_service.create_conversation(user_id, knowledge_base_id)


async def send_chat_message(
    conversation_id: str,
    content: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    use_agents: bool = True
) -> Dict[str, Any]:
    """发送聊天消息的便捷函数"""
    content_type = ContentType.MIXED if attachments else ContentType.TEXT
    return await multimodal_conversation_service.send_message(
        conversation_id, content, content_type, attachments, use_agents
    )
