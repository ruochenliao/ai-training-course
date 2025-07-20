import logging
from typing import Dict, Any, Optional

from fastapi import HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.services.memory_service import MemoryServiceFactory, KnowledgeType


class MemoryQueryRequest(BaseModel):
    """记忆查询请求模型"""
    query: str
    knowledge_type: str = KnowledgeType.CUSTOMER_SERVICE
    limit: Optional[int] = 5


class MemoryAddRequest(BaseModel):
    """记忆添加请求模型"""
    content: str
    knowledge_type: str = KnowledgeType.CUSTOMER_SERVICE
    metadata: Optional[Dict[str, Any]] = None


class MemoryController:
    """记忆服务控制器"""

    def __init__(self):
        self.memory_factory = MemoryServiceFactory()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def upload_file_to_knowledge_base(
        self,
        user_id: str,
        file: UploadFile = File(...),
        knowledge_type: str = Form(KnowledgeType.CUSTOMER_SERVICE),
        is_public: bool = Form(False)
    ) -> Dict[str, Any]:
        """上传文件到知识库

        Args:
            user_id: 用户ID
            file: 上传的文件
            knowledge_type: 知识库类型
            is_public: 是否为公共知识库

        Returns:
            文件处理结果
        """
        try:
            if is_public:
                memory_service = self.memory_factory.get_public_memory_service(knowledge_type)
            else:
                memory_service = self.memory_factory.get_private_memory_service(user_id, knowledge_type)

            result = await memory_service.add_file(file)
            self.logger.info(f"文件上传成功: {result}")
            return {
                "success": True,
                "message": "文件上传并处理成功",
                "data": result
            }
        except Exception as e:
            self.logger.error(f"文件上传失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    async def query_memory(
        self,
        user_id: str,
        request: MemoryQueryRequest,
        include_public: bool = True
    ) -> Dict[str, Any]:
        """查询记忆内容

        Args:
            user_id: 用户ID
            request: 查询请求
            include_public: 是否包含公共记忆

        Returns:
            查询结果
        """
        try:
            results = []

            # 查询私有记忆
            private_service = self.memory_factory.get_private_memory_service(user_id, request.knowledge_type)
            private_results = await private_service.query(request.query, limit=request.limit)
            results.extend(private_results)

            # 查询公共记忆
            if include_public:
                public_service = self.memory_factory.get_public_memory_service(request.knowledge_type)
                public_results = await public_service.query(request.query, limit=request.limit)
                results.extend(public_results)

            # 限制总结果数量
            if request.limit:
                results = results[:request.limit]

            return {
                "success": True,
                "message": "查询成功",
                "data": {
                    "query": request.query,
                    "results": results,
                    "total": len(results)
                }
            }
        except Exception as e:
            self.logger.error(f"记忆查询失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"记忆查询失败: {str(e)}")

    async def add_text_to_memory(
        self,
        user_id: str,
        request: MemoryAddRequest,
        is_public: bool = False
    ) -> Dict[str, Any]:
        """添加文本到记忆

        Args:
            user_id: 用户ID
            request: 添加请求
            is_public: 是否为公共记忆

        Returns:
            添加结果
        """
        try:
            if is_public:
                memory_service = self.memory_factory.get_public_memory_service(request.knowledge_type)
            else:
                memory_service = self.memory_factory.get_private_memory_service(user_id, request.knowledge_type)

            await memory_service.add(request.content, request.metadata)

            return {
                "success": True,
                "message": "文本添加成功",
                "data": {
                    "content_preview": request.content[:100] + "..." if len(request.content) > 100 else request.content,
                    "knowledge_type": request.knowledge_type,
                    "is_public": is_public
                }
            }
        except Exception as e:
            self.logger.error(f"文本添加失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文本添加失败: {str(e)}")

    async def clear_user_memory(
        self,
        user_id: str,
        knowledge_type: str = KnowledgeType.CUSTOMER_SERVICE,
        memory_type: str = "all"  # "chat", "private", "all"
    ) -> Dict[str, Any]:
        """清除用户记忆

        Args:
            user_id: 用户ID
            knowledge_type: 知识库类型
            memory_type: 记忆类型 ("chat", "private", "all")

        Returns:
            清除结果
        """
        try:
            cleared_types = []

            if memory_type in ["chat", "all"]:
                chat_service = self.memory_factory.get_chat_memory_service(user_id)
                await chat_service.clear()
                cleared_types.append("chat")

            if memory_type in ["private", "all"]:
                private_service = self.memory_factory.get_private_memory_service(user_id, knowledge_type)
                await private_service.clear()
                cleared_types.append("private")

            return {
                "success": True,
                "message": f"成功清除 {', '.join(cleared_types)} 记忆",
                "data": {
                    "user_id": user_id,
                    "cleared_types": cleared_types,
                    "knowledge_type": knowledge_type
                }
            }
        except Exception as e:
            self.logger.error(f"清除记忆失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"清除记忆失败: {str(e)}")

    async def get_chat_history(self, user_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """获取用户聊天历史

        Args:
            user_id: 用户ID
            limit: 限制返回数量

        Returns:
            聊天历史
        """
        try:
            chat_service = self.memory_factory.get_chat_memory_service(user_id)
            messages = await chat_service.get_all_messages()

            if limit:
                messages = messages[-limit:]  # 获取最近的消息

            return {
                "success": True,
                "message": "获取聊天历史成功",
                "data": {
                    "user_id": user_id,
                    "messages": messages,
                    "total": len(messages)
                }
            }
        except Exception as e:
            self.logger.error(f"获取聊天历史失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取聊天历史失败: {str(e)}")

    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户记忆统计信息

        Args:
            user_id: 用户ID

        Returns:
            记忆统计信息
        """
        try:
            stats = {
                "user_id": user_id,
                "chat_messages": 0,
                "private_knowledge": {},
                "public_knowledge": {}
            }

            # 获取聊天历史统计
            chat_service = self.memory_factory.get_chat_memory_service(user_id)
            chat_messages = await chat_service.get_all_messages()
            stats["chat_messages"] = len(chat_messages)

            # 这里可以添加更多统计信息的获取逻辑

            return {
                "success": True,
                "message": "获取记忆统计成功",
                "data": stats
            }
        except Exception as e:
            self.logger.error(f"获取记忆统计失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取记忆统计失败: {str(e)}")
