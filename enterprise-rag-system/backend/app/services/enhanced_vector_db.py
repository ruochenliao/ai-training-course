"""
增强版Milvus向量数据库服务
支持混合检索、分区管理、批量操作、性能优化
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.services.vector_db import MilvusService
from loguru import logger
from pymilvus import (
    Collection, utility
)

from app.core.exceptions import VectorDatabaseException


@dataclass
class SearchConfig:
    """搜索配置"""
    metric_type: str = "COSINE"
    index_type: str = "HNSW"
    search_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.search_params is None:
            self.search_params = {"ef": 64}


@dataclass
class HybridSearchResult:
    """混合搜索结果"""
    vector_results: List[Dict[str, Any]]
    keyword_results: List[Dict[str, Any]]
    combined_results: List[Dict[str, Any]]
    search_time: float
    total_results: int


class EnhancedVectorDBService:
    """增强版Milvus向量数据库服务"""
    
    def __init__(self):
        self.base_service = MilvusService()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 缓存配置
        self.cache_enabled = True
        self.search_cache = {}
        self.cache_ttl = 300  # 5分钟
        
        # 性能统计
        self.stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'avg_search_time': 0.0,
            'total_search_time': 0.0
        }
        
        logger.info("增强版向量数据库服务初始化完成")
    
    async def initialize(self):
        """初始化服务"""
        await self.base_service.connect()
        
        # 创建默认集合
        default_collection = settings.MILVUS_COLLECTION_NAME
        await self.ensure_collection_exists(
            default_collection,
            dimension=settings.EMBEDDING_DIMENSION,
            description="默认知识库向量集合"
        )
    
    async def ensure_collection_exists(
        self,
        collection_name: str,
        dimension: int = None,
        description: str = "",
        partition_names: List[str] = None
    ) -> bool:
        """确保集合存在，不存在则创建"""
        try:
            if dimension is None:
                dimension = settings.EMBEDDING_DIMENSION
            
            # 检查集合是否存在
            if not utility.has_collection(collection_name, using=self.base_service.connection_alias):
                await self.base_service.create_collection(collection_name, dimension, description)
                
                # 创建分区
                if partition_names:
                    await self.create_partitions(collection_name, partition_names)
            
            return True
            
        except Exception as e:
            logger.error(f"确保集合存在失败: {e}")
            raise VectorDatabaseException(f"确保集合存在失败: {e}")
    
    async def create_partitions(self, collection_name: str, partition_names: List[str]) -> bool:
        """创建分区"""
        try:
            collection = Collection(collection_name, using=self.base_service.connection_alias)
            
            for partition_name in partition_names:
                if not collection.has_partition(partition_name):
                    collection.create_partition(partition_name)
                    logger.info(f"创建分区: {collection_name}.{partition_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"创建分区失败: {e}")
            raise VectorDatabaseException(f"创建分区失败: {e}")
    
    async def batch_insert_vectors(
        self,
        collection_name: str,
        vectors: List[Dict[str, Any]],
        batch_size: int = 1000,
        partition_name: str = None
    ) -> List[str]:
        """批量插入向量数据"""
        try:
            if not vectors:
                return []
            
            all_ids = []
            
            # 分批处理
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                # 如果指定了分区，添加分区信息
                if partition_name:
                    for vector_item in batch:
                        vector_item['partition'] = partition_name
                
                batch_ids = await self.base_service.insert_vectors(collection_name, batch)
                all_ids.extend(batch_ids)
                
                logger.info(f"批量插入进度: {min(i + batch_size, len(vectors))}/{len(vectors)}")
            
            logger.info(f"批量插入完成，共插入 {len(all_ids)} 条向量数据")
            return all_ids
            
        except Exception as e:
            logger.error(f"批量插入向量数据失败: {e}")
            raise VectorDatabaseException(f"批量插入向量数据失败: {e}")
    
    async def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_text: str = "",
        top_k: int = 10,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        knowledge_base_ids: Optional[List[int]] = None,
        search_config: SearchConfig = None
    ) -> HybridSearchResult:
        """混合检索：向量检索 + 关键词检索"""
        start_time = time.time()
        
        try:
            if search_config is None:
                search_config = SearchConfig()
            
            # 并行执行向量检索和关键词检索
            vector_task = self._vector_search(
                collection_name, [query_vector], top_k * 2, 
                knowledge_base_ids, search_config
            )
            
            keyword_task = self._keyword_search(
                collection_name, query_text, top_k * 2, knowledge_base_ids
            ) if query_text else asyncio.create_task(asyncio.sleep(0))
            
            vector_results, keyword_results = await asyncio.gather(
                vector_task, keyword_task, return_exceptions=True
            )
            
            # 处理异常
            if isinstance(vector_results, Exception):
                logger.error(f"向量检索失败: {vector_results}")
                vector_results = []
            else:
                vector_results = vector_results[0] if vector_results else []
            
            if isinstance(keyword_results, Exception):
                logger.error(f"关键词检索失败: {keyword_results}")
                keyword_results = []
            elif keyword_results is None:
                keyword_results = []
            
            # 融合结果
            combined_results = self._combine_search_results(
                vector_results, keyword_results, vector_weight, keyword_weight, top_k
            )
            
            search_time = time.time() - start_time
            
            # 更新统计
            self._update_search_stats(search_time)
            
            return HybridSearchResult(
                vector_results=vector_results,
                keyword_results=keyword_results,
                combined_results=combined_results,
                search_time=search_time,
                total_results=len(combined_results)
            )
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            raise VectorDatabaseException(f"混合检索失败: {e}")
    
    async def _vector_search(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        top_k: int,
        knowledge_base_ids: Optional[List[int]],
        search_config: SearchConfig
    ) -> List[List[Dict[str, Any]]]:
        """向量检索"""
        return await self.base_service.search_vectors(
            collection_name=collection_name,
            query_vectors=query_vectors,
            top_k=top_k,
            knowledge_base_ids=knowledge_base_ids,
            score_threshold=settings.DEFAULT_SCORE_THRESHOLD
        )
    
    async def _keyword_search(
        self,
        collection_name: str,
        query_text: str,
        top_k: int,
        knowledge_base_ids: Optional[List[int]]
    ) -> List[Dict[str, Any]]:
        """关键词检索"""
        try:
            collection = Collection(collection_name, using=self.base_service.connection_alias)
            collection.load()
            
            # 构建关键词搜索表达式
            keywords = query_text.split()
            keyword_exprs = []
            
            for keyword in keywords:
                keyword_exprs.append(f'content like "%{keyword}%"')
            
            if not keyword_exprs:
                return []
            
            # 构建完整的搜索表达式
            expr_parts = [f"({' or '.join(keyword_exprs)})"]
            
            if knowledge_base_ids:
                kb_ids_str = ",".join(map(str, knowledge_base_ids))
                expr_parts.append(f"knowledge_base_id in [{kb_ids_str}]")
            
            expr = " and ".join(expr_parts)
            
            # 执行查询
            results = collection.query(
                expr=expr,
                output_fields=["id", "content", "metadata", "knowledge_base_id", "document_id"],
                limit=top_k
            )
            
            # 计算关键词匹配分数
            scored_results = []
            for result in results:
                content = result.get('content', '')
                score = self._calculate_keyword_score(content, keywords)
                
                scored_results.append({
                    'id': result['id'],
                    'content': content,
                    'metadata': result.get('metadata', {}),
                    'knowledge_base_id': result.get('knowledge_base_id'),
                    'document_id': result.get('document_id'),
                    'score': score,
                    'search_type': 'keyword'
                })
            
            # 按分数排序
            scored_results.sort(key=lambda x: x['score'], reverse=True)
            
            return scored_results[:top_k]
            
        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []
    
    def _calculate_keyword_score(self, content: str, keywords: List[str]) -> float:
        """计算关键词匹配分数"""
        if not content or not keywords:
            return 0.0
        
        content_lower = content.lower()
        total_score = 0.0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = content_lower.count(keyword_lower)
            
            if count > 0:
                # 基于词频和词长度的评分
                score = count * (len(keyword) / len(content))
                total_score += score
        
        return min(total_score, 1.0)
    
    def _combine_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        vector_weight: float,
        keyword_weight: float,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """融合搜索结果"""
        combined = {}
        
        # 处理向量检索结果
        for result in vector_results:
            doc_id = result.get('id')
            if doc_id:
                combined[doc_id] = {
                    **result,
                    'vector_score': result.get('score', 0.0),
                    'keyword_score': 0.0,
                    'combined_score': result.get('score', 0.0) * vector_weight,
                    'search_types': ['vector']
                }
        
        # 处理关键词检索结果
        for result in keyword_results:
            doc_id = result.get('id')
            if doc_id:
                if doc_id in combined:
                    # 更新已存在的结果
                    combined[doc_id]['keyword_score'] = result.get('score', 0.0)
                    combined[doc_id]['combined_score'] = (
                        combined[doc_id]['vector_score'] * vector_weight +
                        result.get('score', 0.0) * keyword_weight
                    )
                    combined[doc_id]['search_types'].append('keyword')
                else:
                    # 添加新结果
                    combined[doc_id] = {
                        **result,
                        'vector_score': 0.0,
                        'keyword_score': result.get('score', 0.0),
                        'combined_score': result.get('score', 0.0) * keyword_weight,
                        'search_types': ['keyword']
                    }
        
        # 排序并返回top_k结果
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        return sorted_results[:top_k]
    
    async def semantic_search_with_rerank(
        self,
        collection_name: str,
        query_vector: List[float],
        query_text: str,
        top_k: int = 10,
        rerank_top_k: int = 20,
        knowledge_base_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """语义检索 + 重排"""
        try:
            # 先进行向量检索，获取更多候选
            vector_results = await self.base_service.search_vectors(
                collection_name=collection_name,
                query_vectors=[query_vector],
                top_k=rerank_top_k,
                knowledge_base_ids=knowledge_base_ids
            )
            
            if not vector_results or not vector_results[0]:
                return []
            
            candidates = vector_results[0]
            
            # 使用重排模型重新排序
            from app.services.reranker_service import reranker_service
            
            documents = [result.get('content', '') for result in candidates]
            rerank_result = await reranker_service.rerank(
                query=query_text,
                documents=documents,
                top_k=top_k
            )
            
            # 重新组织结果
            reranked_results = []
            for i, (idx, score) in enumerate(zip(rerank_result["indices"], rerank_result["scores"])):
                if idx < len(candidates):
                    result = candidates[idx].copy()
                    result['rerank_score'] = score
                    result['rerank_position'] = i + 1
                    result['original_position'] = idx + 1
                    reranked_results.append(result)
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"语义检索重排失败: {e}")
            raise VectorDatabaseException(f"语义检索重排失败: {e}")
    
    def _update_search_stats(self, search_time: float):
        """更新搜索统计"""
        self.stats['total_searches'] += 1
        self.stats['total_search_time'] += search_time
        self.stats['avg_search_time'] = (
            self.stats['total_search_time'] / self.stats['total_searches']
        )
    
    async def get_collection_health(self, collection_name: str) -> Dict[str, Any]:
        """获取集合健康状态"""
        try:
            stats = await self.base_service.get_collection_stats(collection_name)
            
            # 添加健康检查
            health_info = {
                **stats,
                'health_status': 'healthy',
                'issues': [],
                'recommendations': []
            }
            
            # 检查实体数量
            if stats['num_entities'] == 0:
                health_info['issues'].append('集合为空')
                health_info['recommendations'].append('添加向量数据')
            
            # 检查索引状态
            collection = Collection(collection_name, using=self.base_service.connection_alias)
            indexes = collection.indexes
            
            if not indexes:
                health_info['issues'].append('缺少索引')
                health_info['recommendations'].append('创建向量索引以提高搜索性能')
                health_info['health_status'] = 'warning'
            
            return health_info
            
        except Exception as e:
            logger.error(f"获取集合健康状态失败: {e}")
            return {
                'health_status': 'error',
                'error': str(e)
            }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            **self.stats,
            'cache_hit_rate': (
                self.stats['cache_hits'] / max(self.stats['total_searches'], 1)
            ),
            'cache_enabled': self.cache_enabled
        }


# 全局增强版向量数据库服务实例
enhanced_vector_db_service = EnhancedVectorDBService()
