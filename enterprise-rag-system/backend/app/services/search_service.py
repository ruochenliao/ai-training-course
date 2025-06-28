"""
搜索服务
提供向量搜索、图谱搜索、混合搜索等功能
作为AdvancedSearchService的适配器，保持向后兼容性
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple

from loguru import logger

from app.core.config import settings
from app.services.advanced_search_service import AdvancedSearchService, SearchConfig, SearchType


class SearchService:
    """搜索服务 - AdvancedSearchService的适配器"""
    
    def __init__(self):
        self.vector_weight = 0.7  # 向量搜索权重
        self.graph_weight = 0.3   # 图谱搜索权重
        self.advanced_search = AdvancedSearchService()
    
    async def vector_search(
        self,
        query: str,
        knowledge_base_ids: Optional[List[int]] = None,
        top_k: int = 10,
        score_threshold: float = 0.7,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        向量搜索
        """
        start_time = time.time()
        
        try:
            logger.info(f"执行向量搜索: {query}")
            
            # 使用第一个知识库ID，如果没有提供则使用默认值
            knowledge_base_id = knowledge_base_ids[0] if knowledge_base_ids else 1
            
            # 配置向量搜索
            config = SearchConfig(
                search_type=SearchType.VECTOR,
                top_k=top_k,
                score_threshold=score_threshold
            )
            
            # 执行搜索
            search_results = await self.advanced_search.search(query, knowledge_base_id, config)
            
            # 转换结果格式
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "content": result.content,
                    "score": result.score,
                    "metadata": result.metadata,
                    "source_type": result.metadata.get("source_type", "document"),
                    "document_id": result.metadata.get("document_id")
                })
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "query": query,
                "results": results,
                "total": len(results),
                "search_type": "vector",
                "processing_time": round(processing_time, 2),
                "parameters": {
                    "top_k": top_k,
                    "score_threshold": score_threshold,
                    "knowledge_base_ids": knowledge_base_ids
                }
            }
            
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return {
                "query": query,
                "results": [],
                "total": 0,
                "search_type": "vector",
                "processing_time": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def graph_search(
        self,
        query: str,
        knowledge_base_ids: Optional[List[int]] = None,
        top_k: int = 10,
        score_threshold: float = 0.7,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        图谱搜索
        """
        start_time = time.time()
        
        try:
            logger.info(f"执行图谱搜索: {query}")
            
            # 使用第一个知识库ID，如果没有提供则使用默认值
            knowledge_base_id = knowledge_base_ids[0] if knowledge_base_ids else 1
            
            # 配置图谱搜索
            config = SearchConfig(
                search_type=SearchType.GRAPH,
                top_k=top_k,
                score_threshold=score_threshold
            )
            
            # 执行搜索
            search_results = await self.advanced_search.search(query, knowledge_base_id, config)
            
            # 转换结果格式
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "content": result.content,
                    "score": result.score,
                    "metadata": result.metadata,
                    "source_type": result.metadata.get("source_type", "graph"),
                    "document_id": result.metadata.get("document_id")
                })
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "query": query,
                "results": results,
                "total": len(results),
                "search_type": "graph",
                "processing_time": round(processing_time, 2),
                "parameters": {
                    "top_k": top_k,
                    "score_threshold": score_threshold,
                    "knowledge_base_ids": knowledge_base_ids
                }
            }
            
        except Exception as e:
            logger.error(f"图谱搜索失败: {str(e)}")
            return {
                "query": query,
                "results": [],
                "total": 0,
                "search_type": "graph",
                "processing_time": (time.time() - start_time) * 1000,
                "error": str(e)
            }
    
    async def hybrid_search(
        self,
        query: str,
        knowledge_base_ids: Optional[List[int]] = None,
        top_k: int = 10,
        score_threshold: float = 0.7,
        user_id: Optional[int] = None,
        vector_weight: float = 0.7,
        graph_weight: float = 0.3
    ) -> Dict[str, Any]:
        """
        混合搜索（向量搜索 + 图谱搜索）
        """
        start_time = time.time()
        
        try:
            logger.info(f"执行混合搜索: {query}")
            
            # 使用第一个知识库ID，如果没有提供则使用默认值
            knowledge_base_id = knowledge_base_ids[0] if knowledge_base_ids else 1
            
            # 配置混合搜索
            config = SearchConfig(
                search_type=SearchType.HYBRID,
                top_k=top_k,
                score_threshold=score_threshold,
                vector_weight=vector_weight,
                graph_weight=graph_weight
            )
            
            # 执行搜索
            search_results = await self.advanced_search.search(query, knowledge_base_id, config)
            
            # 转换结果格式
            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "content": result.content,
                    "score": result.score,
                    "metadata": result.metadata,
                    "source_type": result.metadata.get("source_type", "hybrid"),
                    "document_id": result.metadata.get("document_id")
                })
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "query": query,
                "results": results,
                "total": len(results),
                "search_type": "hybrid",
                "processing_time": round(processing_time, 2),
                "parameters": {
                    "top_k": top_k,
                    "score_threshold": score_threshold,
                    "knowledge_base_ids": knowledge_base_ids,
                    "vector_weight": vector_weight,
                    "graph_weight": graph_weight
                }
            }
            
        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}")
            return {
                "query": query,
                "results": [],
                "total": 0,
                "search_type": "hybrid",
                "processing_time": (time.time() - start_time) * 1000,
                "error": str(e)
            }


# 创建全局实例
search_service = SearchService()
