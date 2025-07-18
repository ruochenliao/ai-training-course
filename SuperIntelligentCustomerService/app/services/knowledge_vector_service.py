"""
知识库向量服务
专门用于知识库的向量化存储和检索
基于ChromaDB实现
"""
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from autogen_core.memory import MemoryContent, MemoryMimeType
from autogen_ext.memory.chromadb import ChromaDBVectorMemory, PersistentChromaDBVectorMemoryConfig, \
    HttpChromaDBVectorMemoryConfig

from app.settings.config import settings
from app.log import logger
from app.models.knowledge import KnowledgeBase, KnowledgeFile


class KnowledgeVectorService:
    """知识库向量服务"""
    
    def __init__(self, knowledge_base_id: int):
        """
        初始化知识库向量服务
        
        Args:
            knowledge_base_id: 知识库ID
        """
        self.knowledge_base_id = knowledge_base_id
        self.collection_name = f"kb_{knowledge_base_id}"
        
        # 确保向量数据库目录存在
        self.vector_dir = os.path.join(settings.BASE_DIR, "data", "vector_db")
        os.makedirs(self.vector_dir, exist_ok=True)
        
        # 根据配置选择使用本地或HTTP连接
        if hasattr(settings, 'CHROMA_DB_HOST') and hasattr(settings, 'CHROMA_DB_PORT'):
            self.memory = self._get_memory_http()
        else:
            self.memory = self._get_memory()
            
        logger.info(f"初始化知识库向量服务，知识库ID: {knowledge_base_id}")

    def _get_memory(self) -> ChromaDBVectorMemory:
        """获取或创建本地向量记忆实例"""
        config = PersistentChromaDBVectorMemoryConfig(
            collection_name=self.collection_name,
            persistence_path=self.vector_dir,
            k=10,  # 返回最相关的10条记录
            score_threshold=0.3  # 最小相似度阈值
        )
        return ChromaDBVectorMemory(config=config)

    def _get_memory_http(self) -> ChromaDBVectorMemory:
        """获取或创建HTTP向量记忆实例"""
        config = HttpChromaDBVectorMemoryConfig(
            host=settings.CHROMA_DB_HOST,
            port=settings.CHROMA_DB_PORT,
            collection_name=self.collection_name,
            k=10,  # 返回最相关的10条记录
            score_threshold=0.3  # 最小相似度阈值
        )
        return ChromaDBVectorMemory(config=config)

    async def add_chunk(
        self, 
        content: str, 
        file_id: int,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        添加文本块到向量数据库
        
        Args:
            content: 文本内容
            file_id: 文件ID
            chunk_index: 块索引
            metadata: 额外的元数据
            
        Returns:
            向量ID
        """
        try:
            # 准备基础元数据
            base_metadata = {
                "knowledge_base_id": self.knowledge_base_id,
                "file_id": file_id,
                "chunk_index": chunk_index,
                "timestamp": datetime.now().isoformat(),
                "content_length": len(content)
            }
            
            # 合并自定义元数据
            if metadata:
                base_metadata.update(metadata)
            
            # 添加到向量数据库
            await self.memory.add(
                MemoryContent(
                    content=content,
                    mime_type=MemoryMimeType.TEXT,
                    metadata=base_metadata
                )
            )
            
            # 生成向量ID
            vector_id = f"kb_{self.knowledge_base_id}_file_{file_id}_chunk_{chunk_index}"
            logger.debug(f"添加文本块到向量数据库: {vector_id}")
            
            return vector_id
            
        except Exception as e:
            logger.error(f"添加文本块到向量数据库失败: {str(e)}")
            raise

    async def search(
        self, 
        query: str, 
        limit: int = 10,
        score_threshold: float = 0.3,
        file_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相关内容
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            score_threshold: 相似度阈值
            file_ids: 指定文件ID列表进行过滤
            
        Returns:
            搜索结果列表
        """
        try:
            # 执行向量搜索
            query_results = await self.memory.query(query)
            
            results = []
            for result in query_results.results:
                # 检查相似度阈值
                if hasattr(result, 'score') and result.score < score_threshold:
                    continue
                
                # 文件ID过滤
                if file_ids and result.metadata.get("file_id") not in file_ids:
                    continue
                
                result_dict = {
                    "content": result.content,
                    "score": getattr(result, 'score', 0.0),
                    "metadata": result.metadata,
                    "file_id": result.metadata.get("file_id"),
                    "chunk_index": result.metadata.get("chunk_index"),
                    "knowledge_base_id": result.metadata.get("knowledge_base_id")
                }
                results.append(result_dict)
                
                # 限制结果数量
                if len(results) >= limit:
                    break
            
            logger.info(f"向量搜索完成，查询: {query}, 结果数: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []

    async def delete_file_vectors(self, file_id: int) -> bool:
        """
        删除文件的所有向量
        
        Args:
            file_id: 文件ID
            
        Returns:
            是否删除成功
        """
        try:
            # ChromaDB的删除操作比较复杂，这里简化处理
            # 实际实现中可能需要根据metadata进行过滤删除
            logger.info(f"删除文件向量: file_id={file_id}")
            
            # 这里可以实现具体的删除逻辑
            # 由于ChromaDB的API限制，可能需要重新创建集合
            
            return True
            
        except Exception as e:
            logger.error(f"删除文件向量失败: {str(e)}")
            return False

    async def clear_all(self) -> bool:
        """
        清除知识库的所有向量数据
        
        Returns:
            是否清除成功
        """
        try:
            await self.memory.clear()
            logger.info(f"清除知识库向量数据: knowledge_base_id={self.knowledge_base_id}")
            return True
            
        except Exception as e:
            logger.error(f"清除向量数据失败: {str(e)}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取向量数据库统计信息
        
        Returns:
            统计信息
        """
        try:
            # 这里可以实现获取统计信息的逻辑
            # ChromaDB可能需要通过查询来获取统计信息
            
            stats = {
                "knowledge_base_id": self.knowledge_base_id,
                "collection_name": self.collection_name,
                "total_vectors": 0,  # 需要实际查询获取
                "last_updated": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取向量统计信息失败: {str(e)}")
            return {
                "knowledge_base_id": self.knowledge_base_id,
                "collection_name": self.collection_name,
                "total_vectors": 0,
                "error": str(e)
            }

    async def close(self):
        """关闭向量服务"""
        try:
            await self.memory.close()
            logger.info(f"关闭知识库向量服务: knowledge_base_id={self.knowledge_base_id}")
        except Exception as e:
            logger.error(f"关闭向量服务失败: {str(e)}")


class KnowledgeVectorManager:
    """知识库向量管理器"""
    
    def __init__(self):
        self._services: Dict[int, KnowledgeVectorService] = {}
    
    def get_service(self, knowledge_base_id: int) -> KnowledgeVectorService:
        """
        获取知识库向量服务
        
        Args:
            knowledge_base_id: 知识库ID
            
        Returns:
            向量服务实例
        """
        if knowledge_base_id not in self._services:
            self._services[knowledge_base_id] = KnowledgeVectorService(knowledge_base_id)
        
        return self._services[knowledge_base_id]
    
    async def remove_service(self, knowledge_base_id: int):
        """
        移除知识库向量服务
        
        Args:
            knowledge_base_id: 知识库ID
        """
        if knowledge_base_id in self._services:
            service = self._services[knowledge_base_id]
            await service.close()
            del self._services[knowledge_base_id]
    
    async def close_all(self):
        """关闭所有向量服务"""
        for service in self._services.values():
            await service.close()
        self._services.clear()


# 全局向量管理器实例
knowledge_vector_manager = KnowledgeVectorManager()


async def search_knowledge(
    knowledge_base_ids: List[int],
    query: str,
    limit: int = 10,
    score_threshold: float = 0.3
) -> List[Dict[str, Any]]:
    """
    跨知识库搜索
    
    Args:
        knowledge_base_ids: 知识库ID列表
        query: 搜索查询
        limit: 返回结果数量限制
        score_threshold: 相似度阈值
        
    Returns:
        搜索结果列表
    """
    all_results = []
    
    for kb_id in knowledge_base_ids:
        try:
            service = knowledge_vector_manager.get_service(kb_id)
            results = await service.search(
                query=query,
                limit=limit,
                score_threshold=score_threshold
            )
            all_results.extend(results)
        except Exception as e:
            logger.error(f"搜索知识库 {kb_id} 失败: {str(e)}")
    
    # 按相似度排序并限制结果数量
    all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return all_results[:limit]
