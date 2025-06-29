"""
高级搜索服务
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List

from loguru import logger

from app import embedding_service
from app import graph_service
from app import milvus_service
from app import reranker_service
from app.core import SearchException


class SearchType(Enum):
    """搜索类型枚举"""
    VECTOR = "vector"
    GRAPH = "graph"
    HYBRID = "hybrid"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    FUZZY = "fuzzy"


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    source: str  # vector, graph, keyword
    chunk_index: int = 0
    document_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
            "source": self.source,
            "chunk_index": self.chunk_index,
            "document_id": self.document_id
        }


@dataclass
class SearchConfig:
    """搜索配置"""
    search_type: SearchType = SearchType.HYBRID
    top_k: int = 10
    score_threshold: float = 0.0
    enable_rerank: bool = True
    rerank_top_k: int = 20
    vector_weight: float = 0.7
    graph_weight: float = 0.3
    keyword_weight: float = 0.2
    enable_expansion: bool = True
    expansion_terms: int = 3
    filters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


class AdvancedSearchService:
    """高级搜索服务类"""
    
    def __init__(self):
        """初始化搜索服务"""
        self.max_concurrent_searches = 5
        self.search_timeout = 30
        logger.info("高级搜索服务初始化完成")
    
    async def search(
        self,
        query: str,
        knowledge_base_id: int,
        config: SearchConfig = None
    ) -> List[SearchResult]:
        """
        执行高级搜索
        
        Args:
            query: 搜索查询
            knowledge_base_id: 知识库ID
            config: 搜索配置
            
        Returns:
            搜索结果列表
        """
        config = config or SearchConfig()
        
        try:
            if config.search_type == SearchType.VECTOR:
                return await self._vector_search(query, knowledge_base_id, config)
            elif config.search_type == SearchType.GRAPH:
                return await self._graph_search(query, knowledge_base_id, config)
            elif config.search_type == SearchType.HYBRID:
                return await self._hybrid_search(query, knowledge_base_id, config)
            elif config.search_type == SearchType.SEMANTIC:
                return await self._semantic_search(query, knowledge_base_id, config)
            elif config.search_type == SearchType.KEYWORD:
                return await self._keyword_search(query, knowledge_base_id, config)
            elif config.search_type == SearchType.FUZZY:
                return await self._fuzzy_search(query, knowledge_base_id, config)
            else:
                raise SearchException(f"不支持的搜索类型: {config.search_type}")
                
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise SearchException(f"搜索失败: {e}")
    
    async def _vector_search(
        self,
        query: str,
        knowledge_base_id: int,
        config: SearchConfig
    ) -> List[SearchResult]:
        """向量搜索"""
        try:
            # 生成查询向量
            query_vector = await embedding_service.embed_text(query)
            
            # 构建过滤条件
            filters = {"knowledge_base_id": knowledge_base_id}
            filters.update(config.filters)
            
            # 执行向量搜索
            results = await milvus_service.search(
                collection_name=f"kb_{knowledge_base_id}",
                query_vectors=[query_vector],
                top_k=config.rerank_top_k if config.enable_rerank else config.top_k,
                filters=filters
            )
            
            # 转换结果格式
            search_results = []
            for result in results:
                search_result = SearchResult(
                    id=result["id"],
                    content=result["content"],
                    score=result["score"],
                    metadata=result.get("metadata", {}),
                    source="vector",
                    chunk_index=result.get("chunk_index", 0),
                    document_id=result.get("document_id", "")
                )
                search_results.append(search_result)
            
            # 重排序
            if config.enable_rerank and len(search_results) > config.top_k:
                search_results = await self._rerank_results(query, search_results, config.top_k)
            
            return search_results[:config.top_k]
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    async def _graph_search(
        self,
        query: str,
        knowledge_base_id: int,
        config: SearchConfig
    ) -> List[SearchResult]:
        """图搜索"""
        try:
            # 实体识别
            entities = await self._extract_entities_from_query(query)
            
            if not entities:
                logger.warning("查询中未识别到实体，返回空结果")
                return []
            
            # 图搜索
            graph_results = []
            for entity in entities:
                # 查找相关实体和关系
                neighbors = await graph_service.get_entity_neighbors(
                    entity_id=entity,
                    max_depth=2,
                    limit=config.top_k
                )
                
                for neighbor in neighbors.get("neighbors", []):
                    search_result = SearchResult(
                        id=neighbor["entity"]["id"],
                        content=neighbor["entity"].get("description", neighbor["entity"]["name"]),
                        score=0.8,  # 图搜索的默认分数
                        metadata=neighbor["entity"],
                        source="graph",
                        document_id=neighbor["entity"].get("document_id", "")
                    )
                    graph_results.append(search_result)
            
            # 去重和排序
            unique_results = self._deduplicate_results(graph_results)
            return unique_results[:config.top_k]
            
        except Exception as e:
            logger.error(f"图搜索失败: {e}")
            return []
    
    async def _hybrid_search(
        self,
        query: str,
        knowledge_base_id: int,
        config: SearchConfig
    ) -> List[SearchResult]:
        """混合搜索"""
        try:
            # 并行执行多种搜索
            tasks = []
            
            # 向量搜索
            vector_config = SearchConfig(
                search_type=SearchType.VECTOR,
                top_k=config.rerank_top_k,
                enable_rerank=False,
                filters=config.filters
            )
            tasks.append(self._vector_search(query, knowledge_base_id, vector_config))
            
            # 图搜索
            graph_config = SearchConfig(
                search_type=SearchType.GRAPH,
                top_k=config.top_k,
                filters=config.filters
            )
            tasks.append(self._graph_search(query, knowledge_base_id, graph_config))
            
            # 关键词搜索
            keyword_config = SearchConfig(
                search_type=SearchType.KEYWORD,
                top_k=config.top_k,
                filters=config.filters
            )
            tasks.append(self._keyword_search(query, knowledge_base_id, keyword_config))
            
            # 等待所有搜索完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并结果
            all_results = []
            weights = [config.vector_weight, config.graph_weight, config.keyword_weight]
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"搜索任务 {i} 失败: {result}")
                    continue
                
                # 应用权重
                for search_result in result:
                    search_result.score *= weights[i]
                    all_results.append(search_result)
            
            # 去重和排序
            unique_results = self._deduplicate_results(all_results)
            unique_results.sort(key=lambda x: x.score, reverse=True)
            
            # 重排序
            if config.enable_rerank and len(unique_results) > config.top_k:
                unique_results = await self._rerank_results(query, unique_results, config.top_k)
            
            return unique_results[:config.top_k]
            
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return []
    
    async def _semantic_search(
        self,
        query: str,
        knowledge_base_id: int,
        config: SearchConfig
    ) -> List[SearchResult]:
        """语义搜索（增强版向量搜索）"""
        try:
            # 查询扩展
            expanded_queries = [query]
            if config.enable_expansion:
                expanded_queries.extend(await self._expand_query(query, config.expansion_terms))
            
            # 多查询搜索
            all_results = []
            for expanded_query in expanded_queries:
                results = await self._vector_search(expanded_query, knowledge_base_id, config)
                all_results.extend(results)
            
            # 去重和重新评分
            unique_results = self._deduplicate_results(all_results)
            
            # 语义相似度重新评分
            for result in unique_results:
                semantic_score = await self._calculate_semantic_similarity(query, result.content)
                result.score = (result.score + semantic_score) / 2
            
            unique_results.sort(key=lambda x: x.score, reverse=True)
            return unique_results[:config.top_k]
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []
    
    async def _keyword_search(
        self,
        query: str,
        knowledge_base_id: int,
        config: SearchConfig
    ) -> List[SearchResult]:
        """关键词搜索"""
        try:
            # 这里应该调用全文搜索引擎（如Elasticsearch）
            # 目前使用简单的模拟实现
            
            # 提取关键词
            keywords = self._extract_keywords(query)
            
            # 模拟关键词搜索结果
            results = []
            for i, keyword in enumerate(keywords[:config.top_k]):
                search_result = SearchResult(
                    id=f"keyword_{i}",
                    content=f"包含关键词 '{keyword}' 的内容...",
                    score=0.6 - i * 0.1,
                    metadata={"keyword": keyword},
                    source="keyword"
                )
                results.append(search_result)
            
            return results
            
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return []
    
    async def _fuzzy_search(
        self,
        query: str,
        knowledge_base_id: int,
        config: SearchConfig
    ) -> List[SearchResult]:
        """模糊搜索"""
        try:
            # 生成模糊查询变体
            fuzzy_queries = self._generate_fuzzy_queries(query)
            
            # 对每个变体执行搜索
            all_results = []
            for fuzzy_query in fuzzy_queries:
                results = await self._vector_search(fuzzy_query, knowledge_base_id, config)
                all_results.extend(results)
            
            # 去重和排序
            unique_results = self._deduplicate_results(all_results)
            unique_results.sort(key=lambda x: x.score, reverse=True)
            
            return unique_results[:config.top_k]
            
        except Exception as e:
            logger.error(f"模糊搜索失败: {e}")
            return []
    
    async def _rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """重排序结果"""
        try:
            if not results:
                return results
            
            # 准备重排序数据
            texts = [result.content for result in results]
            
            # 调用重排序服务
            reranked_scores = await reranker_service.rerank(query, texts)
            
            # 更新分数
            for i, result in enumerate(results):
                if i < len(reranked_scores):
                    result.score = reranked_scores[i]
            
            # 排序并返回top_k
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.warning(f"重排序失败，使用原始排序: {e}")
            return results[:top_k]
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重结果"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                unique_results.append(result)
            else:
                # 如果ID重复，保留分数更高的
                for i, existing in enumerate(unique_results):
                    if existing.id == result.id and result.score > existing.score:
                        unique_results[i] = result
                        break
        
        return unique_results
    
    async def _extract_entities_from_query(self, query: str) -> List[str]:
        """从查询中提取实体"""
        # 这里应该调用NER服务
        # 目前使用简单的实现
        words = query.split()
        return [word for word in words if len(word) > 1]
    
    async def _expand_query(self, query: str, num_terms: int) -> List[str]:
        """查询扩展"""
        # 这里可以使用同义词词典、词向量相似度等方法
        # 目前使用简单的实现
        return [f"{query} 相关", f"{query} 类似", f"{query} 相似"][:num_terms]
    
    async def _calculate_semantic_similarity(self, query: str, text: str) -> float:
        """计算语义相似度"""
        try:
            query_vector = await embedding_service.embed_text(query)
            text_vector = await embedding_service.embed_text(text)
            
            # 计算余弦相似度
            import numpy as np
            similarity = np.dot(query_vector, text_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(text_vector)
            )
            return float(similarity)
            
        except Exception as e:
            logger.warning(f"语义相似度计算失败: {e}")
            return 0.5
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        import re
        words = re.findall(r'\w+', query.lower())
        return [word for word in words if len(word) > 2]
    
    def _generate_fuzzy_queries(self, query: str) -> List[str]:
        """生成模糊查询变体"""
        # 简单的模糊查询生成
        variants = [query]
        
        # 添加部分匹配
        words = query.split()
        if len(words) > 1:
            for i in range(len(words)):
                variant = " ".join(words[:i] + words[i+1:])
                if variant:
                    variants.append(variant)
        
        return variants


# 全局高级搜索服务实例
advanced_search_service = AdvancedSearchService()
