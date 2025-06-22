"""
Milvus向量数据库服务
"""

import uuid
from typing import List, Dict, Any, Optional

from app.core.config import settings
from loguru import logger
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)

from app.core.exceptions import VectorDatabaseException


class MilvusService:
    """Milvus向量数据库服务类"""
    
    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.user = settings.MILVUS_USER
        self.password = settings.MILVUS_PASSWORD
        self.database = settings.MILVUS_DATABASE
        self.connection_alias = "default"
        self._connected = False
    
    async def connect(self):
        """连接到Milvus"""
        try:
            connections.connect(
                alias=self.connection_alias,
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db_name=self.database
            )
            self._connected = True
            logger.info(f"成功连接到Milvus: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"连接Milvus失败: {e}")
            raise VectorDatabaseException(f"连接Milvus失败: {e}")
    
    async def disconnect(self):
        """断开Milvus连接"""
        try:
            if self._connected:
                connections.disconnect(self.connection_alias)
                self._connected = False
                logger.info("已断开Milvus连接")
        except Exception as e:
            logger.error(f"断开Milvus连接失败: {e}")
    
    def _ensure_connected(self):
        """确保已连接"""
        if not self._connected:
            raise VectorDatabaseException("未连接到Milvus，请先调用connect()")
    
    async def create_collection(
        self, 
        collection_name: str, 
        dimension: int = 1024,
        description: str = ""
    ) -> bool:
        """创建向量集合"""
        try:
            self._ensure_connected()
            
            # 检查集合是否已存在
            if utility.has_collection(collection_name, using=self.connection_alias):
                logger.info(f"集合 {collection_name} 已存在")
                return True
            
            # 定义字段Schema
            fields = [
                FieldSchema(
                    name="id", 
                    dtype=DataType.VARCHAR, 
                    max_length=100,
                    is_primary=True, 
                    auto_id=False,
                    description="主键ID"
                ),
                FieldSchema(
                    name="vector", 
                    dtype=DataType.FLOAT_VECTOR, 
                    dim=dimension,
                    description="向量数据"
                ),
                FieldSchema(
                    name="knowledge_base_id", 
                    dtype=DataType.INT64,
                    description="知识库ID"
                ),
                FieldSchema(
                    name="document_id", 
                    dtype=DataType.INT64,
                    description="文档ID"
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
                    name="metadata", 
                    dtype=DataType.JSON,
                    description="元数据"
                )
            ]
            
            # 创建集合Schema
            schema = CollectionSchema(
                fields=fields, 
                description=description or f"知识库向量集合: {collection_name}"
            )
            
            # 创建集合
            collection = Collection(
                name=collection_name, 
                schema=schema, 
                using=self.connection_alias
            )
            
            # 创建索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "HNSW",
                "params": {"M": 16, "efConstruction": 200}
            }
            
            collection.create_index(
                field_name="vector",
                index_params=index_params
            )
            
            # 创建标量字段索引
            collection.create_index(field_name="knowledge_base_id")
            collection.create_index(field_name="document_id")
            
            logger.info(f"成功创建集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            raise VectorDatabaseException(f"创建集合失败: {e}")
    
    async def insert_vectors(
        self, 
        collection_name: str, 
        vectors: List[Dict[str, Any]]
    ) -> List[str]:
        """插入向量数据"""
        try:
            self._ensure_connected()
            
            if not vectors:
                return []
            
            # 获取集合
            collection = Collection(collection_name, using=self.connection_alias)
            
            # 准备数据
            ids = []
            vector_data = []
            knowledge_base_ids = []
            document_ids = []
            chunk_indices = []
            contents = []
            metadata_list = []
            
            for vector_item in vectors:
                # 生成ID
                vector_id = vector_item.get("id") or str(uuid.uuid4())
                ids.append(vector_id)
                
                vector_data.append(vector_item["vector"])
                knowledge_base_ids.append(vector_item["knowledge_base_id"])
                document_ids.append(vector_item["document_id"])
                chunk_indices.append(vector_item["chunk_index"])
                contents.append(vector_item["content"])
                metadata_list.append(vector_item.get("metadata", {}))
            
            # 插入数据
            data = [
                ids,
                vector_data,
                knowledge_base_ids,
                document_ids,
                chunk_indices,
                contents,
                metadata_list
            ]
            
            insert_result = collection.insert(data)
            
            # 刷新集合
            collection.flush()
            
            logger.info(f"成功插入 {len(vectors)} 条向量数据到集合 {collection_name}")
            return ids
            
        except Exception as e:
            logger.error(f"插入向量数据失败: {e}")
            raise VectorDatabaseException(f"插入向量数据失败: {e}")
    
    async def search_vectors(
        self,
        collection_name: str,
        query_vectors: List[List[float]],
        top_k: int = 10,
        knowledge_base_ids: Optional[List[int]] = None,
        score_threshold: Optional[float] = None,
        output_fields: Optional[List[str]] = None
    ) -> List[List[Dict[str, Any]]]:
        """搜索向量"""
        try:
            self._ensure_connected()
            
            # 获取集合
            collection = Collection(collection_name, using=self.connection_alias)
            
            # 加载集合到内存
            collection.load()
            
            # 构建搜索参数
            search_params = {
                "metric_type": "COSINE",
                "params": {"ef": 64}
            }
            
            # 构建过滤表达式
            expr = None
            if knowledge_base_ids:
                kb_ids_str = ",".join(map(str, knowledge_base_ids))
                expr = f"knowledge_base_id in [{kb_ids_str}]"
            
            # 设置输出字段
            if output_fields is None:
                output_fields = [
                    "id", "knowledge_base_id", "document_id", 
                    "chunk_index", "content", "metadata"
                ]
            
            # 执行搜索
            search_results = collection.search(
                data=query_vectors,
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=output_fields
            )
            
            # 处理搜索结果
            results = []
            for hits in search_results:
                hit_results = []
                for hit in hits:
                    # 应用分数阈值过滤
                    if score_threshold and hit.score < score_threshold:
                        continue
                    
                    result = {
                        "id": hit.id,
                        "score": hit.score,
                        "distance": hit.distance,
                    }
                    
                    # 添加输出字段
                    for field in output_fields:
                        if field != "id":
                            result[field] = hit.entity.get(field)
                    
                    hit_results.append(result)
                
                results.append(hit_results)
            
            logger.info(f"向量搜索完成，返回 {len(results)} 组结果")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise VectorDatabaseException(f"向量搜索失败: {e}")
    
    async def delete_vectors(
        self,
        collection_name: str,
        vector_ids: List[str] = None,
        knowledge_base_id: int = None,
        document_id: int = None
    ) -> bool:
        """删除向量数据"""
        try:
            self._ensure_connected()
            
            # 获取集合
            collection = Collection(collection_name, using=self.connection_alias)
            
            # 构建删除表达式
            expr_parts = []
            
            if vector_ids:
                ids_str = ",".join([f'"{vid}"' for vid in vector_ids])
                expr_parts.append(f"id in [{ids_str}]")
            
            if knowledge_base_id is not None:
                expr_parts.append(f"knowledge_base_id == {knowledge_base_id}")
            
            if document_id is not None:
                expr_parts.append(f"document_id == {document_id}")
            
            if not expr_parts:
                raise ValueError("必须指定删除条件")
            
            expr = " and ".join(expr_parts)
            
            # 执行删除
            collection.delete(expr)
            
            # 刷新集合
            collection.flush()
            
            logger.info(f"成功删除向量数据，条件: {expr}")
            return True
            
        except Exception as e:
            logger.error(f"删除向量数据失败: {e}")
            raise VectorDatabaseException(f"删除向量数据失败: {e}")
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            self._ensure_connected()
            
            # 检查集合是否存在
            if not utility.has_collection(collection_name, using=self.connection_alias):
                raise VectorDatabaseException(f"集合 {collection_name} 不存在")
            
            # 获取集合
            collection = Collection(collection_name, using=self.connection_alias)
            
            # 获取统计信息
            stats = {
                "name": collection_name,
                "num_entities": collection.num_entities,
                "description": collection.description,
                "schema": {
                    "fields": [
                        {
                            "name": field.name,
                            "type": str(field.dtype),
                            "description": field.description
                        }
                        for field in collection.schema.fields
                    ]
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            raise VectorDatabaseException(f"获取集合统计信息失败: {e}")
    
    async def list_collections(self) -> List[str]:
        """列出所有集合"""
        try:
            self._ensure_connected()
            
            collections = utility.list_collections(using=self.connection_alias)
            return collections
            
        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            raise VectorDatabaseException(f"列出集合失败: {e}")
    
    async def drop_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            self._ensure_connected()
            
            if utility.has_collection(collection_name, using=self.connection_alias):
                utility.drop_collection(collection_name, using=self.connection_alias)
                logger.info(f"成功删除集合: {collection_name}")
                return True
            else:
                logger.warning(f"集合 {collection_name} 不存在")
                return False
                
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            raise VectorDatabaseException(f"删除集合失败: {e}")


# 全局Milvus服务实例
milvus_service = MilvusService()
