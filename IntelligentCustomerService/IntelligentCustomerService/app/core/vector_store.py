"""
Milvus向量数据库集成
提供高性能向量存储和检索功能，支持混合检索
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
import json
import uuid

from pymilvus import (
    connections, Collection, CollectionSchema, FieldSchema, DataType,
    utility, Index, SearchResult
)
import numpy as np

logger = logging.getLogger(__name__)


class MilvusConfig:
    """Milvus配置类"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        user: str = "",
        password: str = "",
        db_name: str = "default",
        alias: str = "default"
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.alias = alias


class VectorCollection:
    """向量集合封装类"""
    
    def __init__(
        self,
        collection_name: str,
        dimension: int,
        description: str = "",
        index_type: str = "HNSW",
        metric_type: str = "COSINE",
        index_params: Optional[Dict] = None
    ):
        self.collection_name = collection_name
        self.dimension = dimension
        self.description = description
        self.index_type = index_type
        self.metric_type = metric_type
        self.index_params = index_params or self._get_default_index_params()
        self.collection = None
        self.is_loaded = False
    
    def _get_default_index_params(self) -> Dict:
        """获取默认索引参数"""
        if self.index_type == "HNSW":
            return {"M": 16, "efConstruction": 200}
        elif self.index_type == "IVF_FLAT":
            return {"nlist": 1024}
        elif self.index_type == "IVF_SQ8":
            return {"nlist": 1024}
        else:
            return {}
    
    def create_schema(self) -> CollectionSchema:
        """创建集合Schema"""
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                max_length=64,
                is_primary=True,
                description="主键ID"
            ),
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.dimension,
                description="向量数据"
            ),
            FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=65535,
                description="原始文本"
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON,
                description="元数据"
            ),
            FieldSchema(
                name="timestamp",
                dtype=DataType.INT64,
                description="时间戳"
            ),
            FieldSchema(
                name="user_id",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="用户ID"
            ),
            FieldSchema(
                name="source",
                dtype=DataType.VARCHAR,
                max_length=256,
                description="数据源"
            )
        ]
        
        return CollectionSchema(
            fields=fields,
            description=self.description
        )
    
    async def create_collection(self):
        """创建集合"""
        try:
            schema = self.create_schema()
            self.collection = Collection(
                name=self.collection_name,
                schema=schema,
                using='default'
            )
            
            # 创建索引
            await self.create_index()
            
            logger.info(f"创建向量集合成功: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"创建向量集合失败: {str(e)}")
            raise
    
    async def create_index(self):
        """创建向量索引"""
        try:
            index_params = {
                "index_type": self.index_type,
                "metric_type": self.metric_type,
                "params": self.index_params
            }
            
            self.collection.create_index(
                field_name="vector",
                index_params=index_params
            )
            
            logger.info(f"创建向量索引成功: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"创建向量索引失败: {str(e)}")
            raise
    
    async def load_collection(self):
        """加载集合到内存"""
        try:
            if not self.is_loaded:
                self.collection.load()
                self.is_loaded = True
                logger.info(f"加载集合到内存: {self.collection_name}")
        except Exception as e:
            logger.error(f"加载集合失败: {str(e)}")
            raise


class MilvusVectorStore:
    """Milvus向量存储管理器"""
    
    def __init__(self, config: MilvusConfig):
        self.config = config
        self.collections: Dict[str, VectorCollection] = {}
        self.is_connected = False
        
        # 预定义集合配置
        self.collection_configs = {
            "documents": {
                "dimension": 1536,  # Qwen3-0.6B嵌入维度
                "description": "文档向量集合",
                "index_type": "HNSW",
                "metric_type": "COSINE"
            },
            "conversations": {
                "dimension": 1536,
                "description": "对话向量集合",
                "index_type": "IVF_FLAT",
                "metric_type": "IP"
            },
            "knowledge": {
                "dimension": 1536,
                "description": "知识库向量集合",
                "index_type": "HNSW",
                "metric_type": "COSINE"
            }
        }
    
    async def connect(self):
        """连接到Milvus"""
        try:
            connections.connect(
                alias=self.config.alias,
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                db_name=self.config.db_name
            )
            
            self.is_connected = True
            logger.info(f"连接Milvus成功: {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"连接Milvus失败: {str(e)}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        try:
            connections.disconnect(alias=self.config.alias)
            self.is_connected = False
            logger.info("断开Milvus连接")
        except Exception as e:
            logger.error(f"断开Milvus连接失败: {str(e)}")
    
    async def initialize_collections(self):
        """初始化所有集合"""
        if not self.is_connected:
            await self.connect()
        
        for name, config in self.collection_configs.items():
            await self.create_collection(name, **config)
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        description: str = "",
        index_type: str = "HNSW",
        metric_type: str = "COSINE",
        index_params: Optional[Dict] = None
    ):
        """创建向量集合"""
        try:
            # 检查集合是否已存在
            if utility.has_collection(collection_name):
                logger.info(f"集合 {collection_name} 已存在，跳过创建")
                collection = Collection(collection_name)
                vector_collection = VectorCollection(
                    collection_name, dimension, description, index_type, metric_type, index_params
                )
                vector_collection.collection = collection
                self.collections[collection_name] = vector_collection
                await vector_collection.load_collection()
                return
            
            # 创建新集合
            vector_collection = VectorCollection(
                collection_name, dimension, description, index_type, metric_type, index_params
            )
            
            await vector_collection.create_collection()
            await vector_collection.load_collection()
            
            self.collections[collection_name] = vector_collection
            
            logger.info(f"集合 {collection_name} 创建并初始化完成")
            
        except Exception as e:
            logger.error(f"创建集合 {collection_name} 失败: {str(e)}")
            raise
    
    async def insert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
        user_ids: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """插入向量数据"""
        try:
            if collection_name not in self.collections:
                raise ValueError(f"集合 {collection_name} 不存在")
            
            collection = self.collections[collection_name].collection
            
            # 准备数据
            num_entities = len(vectors)
            
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(num_entities)]
            
            if metadatas is None:
                metadatas = [{}] * num_entities
            
            if user_ids is None:
                user_ids = [""] * num_entities
            
            if sources is None:
                sources = [""] * num_entities
            
            # 构建插入数据
            entities = [
                ids,
                vectors,
                texts,
                metadatas,
                [int(datetime.now().timestamp() * 1000)] * num_entities,
                user_ids,
                sources
            ]
            
            # 插入数据
            insert_result = collection.insert(entities)
            
            # 刷新数据
            collection.flush()
            
            logger.info(f"向集合 {collection_name} 插入 {num_entities} 条向量数据")
            
            return ids
            
        except Exception as e:
            logger.error(f"插入向量数据失败: {str(e)}")
            raise
    
    async def search_vectors(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        top_k: int = 10,
        search_params: Optional[Dict] = None,
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None
    ) -> List[List[Dict]]:
        """搜索向量"""
        try:
            if collection_name not in self.collections:
                raise ValueError(f"集合 {collection_name} 不存在")
            
            collection = self.collections[collection_name].collection
            
            # 默认搜索参数
            if search_params is None:
                index_type = self.collections[collection_name].index_type
                if index_type == "HNSW":
                    search_params = {"ef": 64}
                elif index_type == "IVF_FLAT":
                    search_params = {"nprobe": 10}
                else:
                    search_params = {}
            
            # 默认输出字段
            if output_fields is None:
                output_fields = ["id", "text", "metadata", "timestamp", "user_id", "source"]
            
            # 执行搜索
            search_results = collection.search(
                data=query_vectors,
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=output_fields
            )
            
            # 格式化结果
            formatted_results = []
            for hits in search_results:
                hit_results = []
                for hit in hits:
                    result = {
                        "id": hit.id,
                        "score": hit.score,
                        "distance": hit.distance
                    }
                    
                    # 添加输出字段
                    for field in output_fields:
                        if hasattr(hit.entity, field):
                            result[field] = getattr(hit.entity, field)
                    
                    hit_results.append(result)
                
                formatted_results.append(hit_results)
            
            logger.debug(f"向量搜索完成: {collection_name}, 查询数量: {len(query_vectors)}, top_k: {top_k}")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            raise
    
    async def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_text: str,
        top_k: int = 10,
        vector_weight: float = 0.7,
        text_weight: float = 0.3,
        filter_expr: Optional[str] = None
    ) -> List[Dict]:
        """混合检索（向量+文本）"""
        try:
            # 向量检索
            vector_results = await self.search_vectors(
                collection_name=collection_name,
                query_vectors=[query_vector],
                top_k=top_k * 2,  # 获取更多候选
                filter_expr=filter_expr
            )
            
            if not vector_results or not vector_results[0]:
                return []
            
            # 文本相似度计算（简单的关键词匹配）
            results_with_scores = []
            for result in vector_results[0]:
                text = result.get("text", "")
                
                # 计算文本相似度（这里使用简单的关键词匹配，可以替换为更复杂的算法）
                text_similarity = self._calculate_text_similarity(query_text, text)
                
                # 计算综合分数
                vector_score = result["score"]
                combined_score = vector_weight * vector_score + text_weight * text_similarity
                
                result["text_similarity"] = text_similarity
                result["combined_score"] = combined_score
                results_with_scores.append(result)
            
            # 按综合分数排序
            results_with_scores.sort(key=lambda x: x["combined_score"], reverse=True)
            
            # 返回top_k结果
            return results_with_scores[:top_k]
            
        except Exception as e:
            logger.error(f"混合检索失败: {str(e)}")
            raise
    
    def _calculate_text_similarity(self, query: str, text: str) -> float:
        """计算文本相似度（简单实现）"""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words or not text_words:
            return 0.0
        
        intersection = query_words.intersection(text_words)
        union = query_words.union(text_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def delete_vectors(
        self,
        collection_name: str,
        ids: List[str]
    ) -> bool:
        """删除向量数据"""
        try:
            if collection_name not in self.collections:
                raise ValueError(f"集合 {collection_name} 不存在")
            
            collection = self.collections[collection_name].collection
            
            # 构建删除表达式
            id_list = "', '".join(ids)
            expr = f"id in ['{id_list}']"
            
            # 执行删除
            collection.delete(expr)
            collection.flush()
            
            logger.info(f"从集合 {collection_name} 删除 {len(ids)} 条向量数据")
            
            return True
            
        except Exception as e:
            logger.error(f"删除向量数据失败: {str(e)}")
            return False
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            if collection_name not in self.collections:
                raise ValueError(f"集合 {collection_name} 不存在")
            
            collection = self.collections[collection_name].collection
            
            # 获取统计信息
            stats = collection.get_stats()
            
            return {
                "collection_name": collection_name,
                "num_entities": collection.num_entities,
                "dimension": self.collections[collection_name].dimension,
                "index_type": self.collections[collection_name].index_type,
                "metric_type": self.collections[collection_name].metric_type,
                "is_loaded": self.collections[collection_name].is_loaded,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                "is_connected": self.is_connected,
                "collections": {},
                "total_collections": len(self.collections),
                "healthy_collections": 0
            }
            
            for name, collection in self.collections.items():
                try:
                    stats = await self.get_collection_stats(name)
                    health_status["collections"][name] = {
                        "is_healthy": True,
                        "is_loaded": collection.is_loaded,
                        "num_entities": stats.get("num_entities", 0)
                    }
                    health_status["healthy_collections"] += 1
                except Exception as e:
                    health_status["collections"][name] = {
                        "is_healthy": False,
                        "error": str(e)
                    }
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {"is_connected": False, "error": str(e)}


# 全局向量存储实例
vector_store: Optional[MilvusVectorStore] = None


async def get_vector_store() -> MilvusVectorStore:
    """获取向量存储实例"""
    global vector_store
    if vector_store is None:
        # 从配置加载
        config = MilvusConfig()  # 这里应该从配置文件加载
        vector_store = MilvusVectorStore(config)
        await vector_store.connect()
        await vector_store.initialize_collections()
    
    return vector_store
