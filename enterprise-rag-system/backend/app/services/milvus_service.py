"""
Milvus向量数据库服务 - 支持混合检索
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from loguru import logger
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
    AnnSearchRequest,
    RRFRanker
)

from app.core import settings


class MilvusService:
    """Milvus向量数据库服务"""
    
    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.collection_name = "document_embeddings"
        self.dimension = settings.EMBEDDING_DIMENSION
        self.connection_alias = "default"
        self.collection = None
        self._connected = False
    
    async def connect(self):
        """连接到Milvus"""
        try:
            if self._connected:
                return
            
            # 连接到Milvus
            connections.connect(
                alias=self.connection_alias,
                host=self.host,
                port=self.port
            )
            
            # 创建或获取集合
            await self._ensure_collection()
            
            self._connected = True
            logger.info(f"成功连接到Milvus: {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"连接Milvus失败: {str(e)}")
            raise e
    
    async def _ensure_collection(self):
        """确保集合存在"""
        try:
            # 检查集合是否存在
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"使用现有集合: {self.collection_name}")
            else:
                # 创建新集合
                await self._create_collection()
                logger.info(f"创建新集合: {self.collection_name}")
            
            # 加载集合
            self.collection.load()
            
        except Exception as e:
            logger.error(f"确保集合存在失败: {str(e)}")
            raise e
    
    async def _create_collection(self):
        """创建集合"""
        try:
            # 定义字段
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=False,
                    description="文档分块ID"
                ),
                FieldSchema(
                    name="document_id",
                    dtype=DataType.INT64,
                    description="文档ID"
                ),
                FieldSchema(
                    name="knowledge_base_id",
                    dtype=DataType.INT64,
                    description="知识库ID"
                ),
                FieldSchema(
                    name="chunk_index",
                    dtype=DataType.INT64,
                    description="分块索引"
                ),
                FieldSchema(
                    name="content",
                    dtype=DataType.VARCHAR,
                    max_length=65535,
                    description="文本内容"
                ),
                FieldSchema(
                    name="vector",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.dimension,
                    description="向量嵌入"
                ),
                FieldSchema(
                    name="sparse_vector",
                    dtype=DataType.SPARSE_FLOAT_VECTOR,
                    description="稀疏向量（用于关键词检索）"
                ),
                FieldSchema(
                    name="keywords",
                    dtype=DataType.VARCHAR,
                    max_length=1000,
                    description="关键词（用于BM25检索）"
                )
            ]
            
            # 创建集合schema
            schema = CollectionSchema(
                fields=fields,
                description="文档向量嵌入集合"
            )
            
            # 创建集合
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            # 创建索引
            await self._create_index()
            
        except Exception as e:
            logger.error(f"创建集合失败: {str(e)}")
            raise e
    
    async def _create_index(self):
        """创建向量索引"""
        try:
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            
            self.collection.create_index(
                field_name="vector",
                index_params=index_params
            )
            
            logger.info("向量索引创建成功")
            
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            raise e
    
    async def insert_vectors(self, vector_data: List[Dict[str, Any]]):
        """插入向量数据"""
        try:
            if not self._connected:
                await self.connect()
            
            if not vector_data:
                return
            
            # 准备数据
            ids = [item["id"] for item in vector_data]
            document_ids = [item["document_id"] for item in vector_data]
            knowledge_base_ids = [item.get("knowledge_base_id", 0) for item in vector_data]
            chunk_indices = [item["chunk_index"] for item in vector_data]
            contents = [item["content"][:65535] for item in vector_data]  # 限制长度
            vectors = [item["vector"] for item in vector_data]
            
            # 插入数据
            entities = [
                ids,
                document_ids,
                knowledge_base_ids,
                chunk_indices,
                contents,
                vectors
            ]
            
            insert_result = self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"成功插入 {len(vector_data)} 条向量数据")
            return insert_result
            
        except Exception as e:
            logger.error(f"插入向量数据失败: {str(e)}")
            raise e
    
    async def search_vectors(
        self,
        vector: List[float],
        top_k: int = 10,
        score_threshold: float = 0.7,
        knowledge_base_ids: Optional[List[int]] = None,
        document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """搜索向量"""
        try:
            if not self._connected:
                await self.connect()
            
            # 构建搜索参数
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # 构建过滤表达式
            filter_expr = []
            if knowledge_base_ids:
                kb_filter = f"knowledge_base_id in {knowledge_base_ids}"
                filter_expr.append(kb_filter)
            
            if document_ids:
                doc_filter = f"document_id in {document_ids}"
                filter_expr.append(doc_filter)
            
            expr = " and ".join(filter_expr) if filter_expr else None
            
            # 执行搜索
            search_results = self.collection.search(
                data=[vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["id", "document_id", "knowledge_base_id", "chunk_index", "content"]
            )
            
            # 处理结果
            results = []
            for hits in search_results:
                for hit in hits:
                    if hit.score >= score_threshold:
                        result = {
                            "chunk_id": hit.entity.get("id"),
                            "document_id": hit.entity.get("document_id"),
                            "knowledge_base_id": hit.entity.get("knowledge_base_id"),
                            "chunk_index": hit.entity.get("chunk_index"),
                            "content": hit.entity.get("content"),
                            "score": float(hit.score),
                            "distance": float(hit.distance)
                        }
                        results.append(result)
            
            logger.info(f"向量搜索返回 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []

    async def hybrid_search(
        self,
        dense_vector: List[float],
        sparse_vector: Optional[Dict[int, float]] = None,
        keywords: Optional[str] = None,
        top_k: int = 10,
        score_threshold: float = 0.7,
        knowledge_base_ids: Optional[List[int]] = None,
        document_ids: Optional[List[int]] = None,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        混合检索：结合密集向量和稀疏向量检索

        Args:
            dense_vector: 密集向量
            sparse_vector: 稀疏向量
            keywords: 关键词
            top_k: 返回结果数量
            score_threshold: 分数阈值
            knowledge_base_ids: 知识库ID列表
            document_ids: 文档ID列表
            dense_weight: 密集向量权重
            sparse_weight: 稀疏向量权重
        """
        try:
            if not self._connected:
                await self.connect()

            # 构建过滤表达式
            filter_expr = []
            if knowledge_base_ids:
                kb_filter = f"knowledge_base_id in {knowledge_base_ids}"
                filter_expr.append(kb_filter)

            if document_ids:
                doc_filter = f"document_id in {document_ids}"
                filter_expr.append(doc_filter)

            expr = " and ".join(filter_expr) if filter_expr else None

            # 准备搜索请求
            search_requests = []

            # 密集向量搜索
            if dense_vector:
                dense_search_params = {
                    "metric_type": "COSINE",
                    "params": {"nprobe": 10}
                }

                dense_request = AnnSearchRequest(
                    data=[dense_vector],
                    anns_field="vector",
                    param=dense_search_params,
                    limit=top_k * 2,  # 获取更多结果用于重排序
                    expr=expr
                )
                search_requests.append(dense_request)

            # 稀疏向量搜索
            if sparse_vector:
                sparse_search_params = {
                    "metric_type": "IP",  # 内积
                    "params": {}
                }

                sparse_request = AnnSearchRequest(
                    data=[sparse_vector],
                    anns_field="sparse_vector",
                    param=sparse_search_params,
                    limit=top_k * 2,
                    expr=expr
                )
                search_requests.append(sparse_request)

            # 执行混合搜索
            if len(search_requests) > 1:
                # 使用RRF（Reciprocal Rank Fusion）进行结果融合
                ranker = RRFRanker()

                hybrid_results = self.collection.hybrid_search(
                    reqs=search_requests,
                    rerank=ranker,
                    limit=top_k,
                    output_fields=["id", "document_id", "knowledge_base_id", "chunk_index", "content", "keywords"]
                )
            else:
                # 单一搜索
                if search_requests:
                    hybrid_results = self.collection.search(
                        data=search_requests[0].data,
                        anns_field=search_requests[0].anns_field,
                        param=search_requests[0].param,
                        limit=top_k,
                        expr=expr,
                        output_fields=["id", "document_id", "knowledge_base_id", "chunk_index", "content", "keywords"]
                    )
                else:
                    return []

            # 处理结果
            results = []
            for hits in hybrid_results:
                for hit in hits:
                    if hit.score >= score_threshold:
                        result = {
                            "chunk_id": hit.entity.get("id"),
                            "document_id": hit.entity.get("document_id"),
                            "knowledge_base_id": hit.entity.get("knowledge_base_id"),
                            "chunk_index": hit.entity.get("chunk_index"),
                            "content": hit.entity.get("content"),
                            "keywords": hit.entity.get("keywords", ""),
                            "score": float(hit.score),
                            "distance": float(hit.distance),
                            "search_type": "hybrid"
                        }
                        results.append(result)

            logger.info(f"混合搜索返回 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}")
            # 降级到普通向量搜索
            if dense_vector:
                logger.info("降级到普通向量搜索")
                return await self.search_vectors(
                    dense_vector, top_k, score_threshold,
                    knowledge_base_ids, document_ids
                )
            return []
    
    async def delete_document_vectors(self, document_id: int):
        """删除文档的所有向量"""
        try:
            if not self._connected:
                await self.connect()
            
            # 删除指定文档的向量
            expr = f"document_id == {document_id}"
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"删除文档 {document_id} 的向量数据")
            
        except Exception as e:
            logger.error(f"删除文档向量失败: {str(e)}")
            raise e
    
    async def delete_knowledge_base_vectors(self, knowledge_base_id: int):
        """删除知识库的所有向量"""
        try:
            if not self._connected:
                await self.connect()
            
            # 删除指定知识库的向量
            expr = f"knowledge_base_id == {knowledge_base_id}"
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"删除知识库 {knowledge_base_id} 的向量数据")
            
        except Exception as e:
            logger.error(f"删除知识库向量失败: {str(e)}")
            raise e
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            if not self._connected:
                await self.connect()
            
            stats = self.collection.get_stats()
            return {
                "total_entities": stats.get("row_count", 0),
                "collection_name": self.collection_name,
                "dimension": self.dimension
            }
            
        except Exception as e:
            logger.error(f"获取集合统计失败: {str(e)}")
            return {}
    
    async def disconnect(self):
        """断开连接"""
        try:
            if self._connected:
                connections.disconnect(self.connection_alias)
                self._connected = False
                logger.info("已断开Milvus连接")
        except Exception as e:
            logger.error(f"断开Milvus连接失败: {str(e)}")


# 全局Milvus服务实例
milvus_service = MilvusService()
