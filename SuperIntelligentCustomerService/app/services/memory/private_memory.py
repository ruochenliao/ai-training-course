"""
私有记忆服务
用户个人知识库，使用ChromaDB向量数据库存储用户偏好、历史行为等个性化信息
基于AutoGen的ChromaDBVectorMemory实现模式，继承BaseMemoryService抽象基类
"""
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    SentenceTransformer = None

    class MockChromaDB:
        """ChromaDB不可用时的占位符"""
        pass

from .base import BaseMemoryService, MemoryItem, MemoryType, QueryResult, ServiceStatus

logger = logging.getLogger(__name__)


class PrivateMemoryService(BaseMemoryService):
    """
    用户私有知识库服务
    基于ChromaDB向量数据库实现，继承BaseMemoryService抽象基类
    """

    def __init__(self, user_id: str):
        """
        初始化私有记忆服务

        Args:
            user_id: 用户ID
        """
        # 调用父类初始化
        service_id = f"private_memory_{user_id}"
        super().__init__(service_id, MemoryType.PRIVATE)

        self.user_id = user_id

        if not CHROMADB_AVAILABLE:
            self._handle_error(ImportError("ChromaDB不可用，请安装: pip install chromadb sentence-transformers"))
            raise ImportError("ChromaDB不可用，请安装: pip install chromadb sentence-transformers")

        try:
            self._init_vector_db()
            self._set_ready()
        except Exception as e:
            self._handle_error(e)
            raise

    def _init_vector_db(self):
        """初始化向量数据库"""
        try:
            # 设置ChromaDB持久化路径
            self.chroma_path = os.path.join(
                str(Path.home()),
                ".chromadb_intelligent_customer_service",
                f"private_memory_{self.user_id}"
            )
            os.makedirs(self.chroma_path, exist_ok=True)

            # 初始化ChromaDB客户端
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # 创建或获取集合
            self.collection_name = f"private_memories_{self.user_id}"
            try:
                self.collection = self.chroma_client.get_collection(self.collection_name)
            except Exception:  # 捕获所有异常，包括NotFoundError
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"user_id": self.user_id, "type": "private_memory"}
                )

            # 初始化嵌入模型 - 使用全局模型管理器
            from ...config.vector_db_config import model_manager
            self.embedding_model = model_manager.get_embedding_model()

            logger.info(f"私有记忆向量数据库初始化成功: {self.chroma_path}")

        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            raise
    
    async def add_memory(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加私有记忆"""
        memory_id = f"private_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        return await self._add_memory_vector(memory_id, content, metadata)

    async def _add_memory_vector(self, memory_id: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """使用向量数据库添加记忆"""
        try:
            # 生成嵌入向量
            embedding = self.embedding_model.encode(content).tolist()

            # 准备元数据
            doc_metadata = {
                "user_id": self.user_id,
                "content_type": metadata.get("content_type", "text") if metadata else "text",
                "category": metadata.get("category", "general") if metadata else "general",
                "tags": json.dumps(metadata.get("tags", [])) if metadata else "[]",
                "created_at": datetime.now().isoformat(),
                **(metadata or {})
            }

            # 添加到ChromaDB
            self.collection.add(
                ids=[memory_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[doc_metadata]
            )

            logger.debug(f"向量记忆添加成功: {memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"向量记忆添加失败: {e}")
            raise


    
    async def retrieve_memories(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """检索相关私有记忆"""
        return await self._retrieve_memories_vector(query, limit)

    async def _retrieve_memories_vector(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """使用向量数据库检索记忆"""
        try:
            # 生成查询嵌入
            query_embedding = self.embedding_model.encode(query).tolist()

            # 从ChromaDB检索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(limit, 10),  # 获取更多结果用于重排
                include=["documents", "metadatas", "distances"]
            )

            memories = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    try:
                        content = results["documents"][0][i]
                        metadata = results["metadatas"][0][i]
                        distance = results["distances"][0][i]

                        # 转换距离为相似度分数 (ChromaDB使用欧几里得距离)
                        similarity_score = 1.0 / (1.0 + distance)

                        # 解析标签
                        if "tags" in metadata:
                            try:
                                metadata["tags"] = json.loads(metadata["tags"])
                            except (json.JSONDecodeError, TypeError):
                                metadata["tags"] = []

                        metadata["relevance_score"] = similarity_score
                        metadata["distance"] = distance

                        memory = MemoryItem(
                            id=doc_id,
                            content=content,
                            metadata=metadata,
                            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                            updated_at=datetime.now()
                        )
                        memories.append(memory)

                    except Exception as e:
                        logger.warning(f"Failed to process vector memory result: {e}")
                        continue

            # 按相关性排序并返回前N个
            memories.sort(key=lambda x: x.metadata.get("relevance_score", 0), reverse=True)
            return memories[:limit]

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []


    
    async def add_user_preference(self, preference_type: str, preference_value: str, context: str = "") -> str:
        """添加用户偏好"""
        content = f"用户偏好 - {preference_type}: {preference_value}"
        if context:
            content += f" (上下文: {context})"

        metadata = {
            "content_type": "user_preference",
            "category": "preference",
            "preference_type": preference_type,
            "preference_value": preference_value,
            "context": context,
            "tags": ["偏好", preference_type]
        }

        return await self.add_memory(content, metadata)

    async def add_user_history(self, action: str, details: Dict[str, Any]) -> str:
        """添加用户行为历史"""
        content = f"用户行为 - {action}: {json.dumps(details, ensure_ascii=False)}"

        metadata = {
            "content_type": "user_history",
            "category": "history",
            "action": action,
            "details": details,
            "tags": ["历史", action]
        }

        return await self.add_memory(content, metadata)
    
    async def get_user_preferences(self, preference_type: str = None) -> List[MemoryItem]:
        """获取用户偏好"""
        try:
            # 构建查询条件
            where_conditions = {"user_id": self.user_id, "content_type": "user_preference"}
            if preference_type:
                where_conditions["preference_type"] = preference_type

            # 从ChromaDB检索偏好记录
            results = self.collection.get(
                where=where_conditions,
                include=["documents", "metadatas"]
            )

            memories = []
            if results["ids"]:
                for i, doc_id in enumerate(results["ids"]):
                    try:
                        content = results["documents"][i]
                        metadata = results["metadatas"][i]

                        # 解析标签
                        if "tags" in metadata:
                            try:
                                metadata["tags"] = json.loads(metadata["tags"])
                            except (json.JSONDecodeError, TypeError):
                                metadata["tags"] = []

                        memory = MemoryItem(
                            id=doc_id,
                            content=content,
                            metadata=metadata,
                            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                            updated_at=datetime.now()
                        )
                        memories.append(memory)

                    except Exception as e:
                        logger.warning(f"Failed to parse preference memory: {e}")
                        continue

            # 按创建时间排序
            memories.sort(key=lambda x: x.created_at, reverse=True)
            return memories

        except Exception as e:
            logger.error(f"获取用户偏好失败: {e}")
            return []
    
    def _generate_summary(self, content: str, max_length: int = 100) -> str:
        """生成内容摘要"""
        if len(content) <= max_length:
            return content
        
        # 简单的摘要生成：取前N个字符
        summary = content[:max_length].strip()
        if summary != content:
            summary += "..."
        
        return summary
    
    async def update_memory(self, memory_id: str, content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """更新私有记忆"""
        try:
            # ChromaDB不支持直接更新，需要删除后重新添加
            if content is not None:
                # 删除旧记录
                self.collection.delete(ids=[memory_id])

                # 重新添加更新后的记录
                await self._add_memory_vector(memory_id, content, metadata)
                return True
            return False
        except Exception as e:
            logger.error(f"更新私有记忆失败: {e}")
            return False
    
    # 实现BaseMemoryService抽象方法
    async def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加记忆内容（实现基类接口）

        Args:
            content: 记忆内容
            metadata: 元数据

        Returns:
            记忆项ID
        """
        try:
            self._update_access_time()
            return await self.add_memory(content, metadata)
        except Exception as e:
            self._handle_error(e)
            raise

    async def query(self, query: str, limit: int = 5, **kwargs) -> QueryResult:
        """
        查询记忆内容（实现基类接口）

        Args:
            query: 查询内容
            limit: 返回数量限制
            **kwargs: 其他查询参数

        Returns:
            查询结果
        """
        try:
            start_time = time.time()
            self._update_access_time()

            memories = await self.retrieve_memories(query, limit)
            query_time = time.time() - start_time

            return QueryResult(
                items=memories,
                total_count=len(memories),
                query_time=query_time,
                metadata={
                    "query_type": "vector_search",
                    "user_id": self.user_id,
                    "collection_name": self.collection_name
                }
            )
        except Exception as e:
            self._handle_error(e)
            raise

    async def clear(self, **kwargs) -> bool:
        """
        清空记忆内容（实现基类接口）

        Args:
            **kwargs: 清空参数

        Returns:
            是否成功
        """
        try:
            self._update_access_time()

            # 删除集合中的所有数据
            self.collection.delete()
            logger.info(f"已清空用户 {self.user_id} 的所有私有记忆")
            return True
        except Exception as e:
            self._handle_error(e)
            raise

    async def close(self) -> None:
        """
        关闭服务，释放资源（实现基类接口）
        """
        try:
            # ChromaDB客户端会自动处理连接关闭
            self.status = ServiceStatus.CLOSED
            logger.info(f"私有记忆服务 {self.service_id} 已关闭")
        except Exception as e:
            logger.error(f"关闭私有记忆服务时发生错误: {e}")

    # 保持向后兼容的方法
    async def delete_memory(self, memory_id: str) -> bool:
        """删除私有记忆（向后兼容）"""
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            logger.error(f"向量记忆删除失败: {e}")
            return False
