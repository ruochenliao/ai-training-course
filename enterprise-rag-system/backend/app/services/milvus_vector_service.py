"""
Milvus 2.3+ 向量数据库服务 - 企业级RAG系统
严格按照技术栈要求：Milvus 2.3+ 支持语义检索和混合检索，使用 HNSW 索引
"""
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.services.qwen_embedding_service import qwen_embedding_service
from loguru import logger
from pymilvus import (
    connections, Collection, CollectionSchema, FieldSchema, DataType,
    utility, SearchResult
)


class MilvusVectorService:
    """Milvus 向量数据库服务"""
    
    def __init__(self):
        self.connection_alias = "default"
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.embedding_dim = 1024  # Qwen2.5-7B-Instruct 嵌入维度
        self.collections = {}
        self._connected = False
        
        # HNSW 索引参数
        self.index_params = {
            "metric_type": "COSINE",  # 余弦相似度
            "index_type": "HNSW",
            "params": {
                "M": 16,              # HNSW 参数 M
                "efConstruction": 200  # 构建时的 ef 参数
            }
        }
        
        # 搜索参数
        self.search_params = {
            "metric_type": "COSINE",
            "params": {
                "ef": 64  # 搜索时的 ef 参数
            }
        }
    
    async def connect(self):
        """连接到Milvus数据库"""
        if self._connected:
            return
        
        try:
            # 在线程池中执行连接操作
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._connect_sync)
            
            self._connected = True
            logger.info(f"Milvus连接成功: {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Milvus连接失败: {e}")
            raise
    
    def _connect_sync(self):
        """同步连接Milvus"""
        connections.connect(
            alias=self.connection_alias,
            host=self.host,
            port=self.port,
            timeout=30
        )
    
    async def disconnect(self):
        """断开Milvus连接"""
        try:
            if self._connected:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, 
                    connections.disconnect, 
                    self.connection_alias
                )
                self._connected = False
                logger.info("Milvus连接已断开")
        except Exception as e:
            logger.error(f"断开Milvus连接失败: {e}")
    
    def _create_collection_schema(self, collection_name: str) -> CollectionSchema:
        """创建集合schema"""
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                max_length=100,
                is_primary=True,
                auto_id=False
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
                description="分块内容"
            ),
            FieldSchema(
                name="content_hash",
                dtype=DataType.VARCHAR,
                max_length=32,
                description="内容哈希"
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.embedding_dim,
                description="Qwen2.5嵌入向量"
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON,
                description="元数据"
            ),
            FieldSchema(
                name="created_at",
                dtype=DataType.INT64,
                description="创建时间戳"
            )
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description=f"知识库向量集合: {collection_name}",
            enable_dynamic_field=True
        )
        
        return schema
    
    async def create_collection(self, collection_name: str) -> bool:
        """创建向量集合"""
        try:
            await self.connect()
            
            # 检查集合是否已存在
            if await self.collection_exists(collection_name):
                logger.info(f"集合 {collection_name} 已存在")
                return True
            
            # 在线程池中创建集合
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                self._create_collection_sync, 
                collection_name
            )
            
            logger.info(f"集合 {collection_name} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            return False
    
    def _create_collection_sync(self, collection_name: str):
        """同步创建集合"""
        schema = self._create_collection_schema(collection_name)
        collection = Collection(
            name=collection_name,
            schema=schema,
            using=self.connection_alias
        )
        
        # 创建HNSW索引
        collection.create_index(
            field_name="embedding",
            index_params=self.index_params
        )
        
        # 加载集合到内存
        collection.load()
        
        self.collections[collection_name] = collection
    
    async def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        try:
            await self.connect()
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(
                None,
                utility.has_collection,
                collection_name,
                self.connection_alias
            )
            return exists
        except Exception as e:
            logger.error(f"检查集合存在性失败: {e}")
            return False
    
    async def get_collection(self, collection_name: str) -> Optional[Collection]:
        """获取集合对象"""
        try:
            await self.connect()
            
            if collection_name not in self.collections:
                if await self.collection_exists(collection_name):
                    loop = asyncio.get_event_loop()
                    collection = await loop.run_in_executor(
                        None,
                        Collection,
                        collection_name,
                        using=self.connection_alias
                    )
                    self.collections[collection_name] = collection
                else:
                    return None
            
            return self.collections[collection_name]
            
        except Exception as e:
            logger.error(f"获取集合失败: {e}")
            return None
    
    async def insert_vectors(
        self, 
        collection_name: str, 
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """批量插入向量"""
        try:
            collection = await self.get_collection(collection_name)
            if not collection:
                await self.create_collection(collection_name)
                collection = await self.get_collection(collection_name)
            
            # 准备数据
            ids = []
            document_ids = []
            chunk_indices = []
            contents = []
            content_hashes = []
            embeddings = []
            metadatas = []
            created_ats = []
            
            # 批量生成嵌入向量
            texts = [doc["content"] for doc in documents]
            vectors = await qwen_embedding_service.encode_batch(texts)
            
            for i, (doc, vector) in enumerate(zip(documents, vectors)):
                vector_id = str(uuid.uuid4())
                ids.append(vector_id)
                document_ids.append(doc["document_id"])
                chunk_indices.append(doc["chunk_index"])
                contents.append(doc["content"])
                content_hashes.append(doc["content_hash"])
                embeddings.append(vector.tolist())
                metadatas.append(doc.get("metadata", {}))
                created_ats.append(int(datetime.now().timestamp() * 1000))
            
            # 准备插入数据
            data = [
                ids,
                document_ids,
                chunk_indices,
                contents,
                content_hashes,
                embeddings,
                metadatas,
                created_ats
            ]
            
            # 在线程池中执行插入
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                collection.insert,
                data
            )
            
            # 刷新数据到磁盘
            await loop.run_in_executor(None, collection.flush)
            
            logger.info(f"成功插入 {len(ids)} 个向量到集合 {collection_name}")
            return ids
            
        except Exception as e:
            logger.error(f"插入向量失败: {e}")
            raise
    
    async def search_vectors(
        self,
        collection_name: str,
        query_text: str,
        top_k: int = 20,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """语义检索向量"""
        try:
            collection = await self.get_collection(collection_name)
            if not collection:
                logger.warning(f"集合 {collection_name} 不存在")
                return []
            
            # 生成查询向量
            query_vector = await qwen_embedding_service.encode_single(query_text)
            
            # 在线程池中执行搜索
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._search_sync,
                collection,
                [query_vector.tolist()],
                top_k,
                filter_expr
            )
            
            # 处理搜索结果
            search_results = []
            for hits in results:
                for hit in hits:
                    result = {
                        "id": hit.id,
                        "distance": float(hit.distance),
                        "score": 1.0 - float(hit.distance),  # 转换为相似度分数
                        "document_id": hit.entity.get("document_id"),
                        "chunk_index": hit.entity.get("chunk_index"),
                        "content": hit.entity.get("content"),
                        "content_hash": hit.entity.get("content_hash"),
                        "metadata": hit.entity.get("metadata", {}),
                        "created_at": hit.entity.get("created_at")
                    }
                    search_results.append(result)
            
            logger.info(f"语义检索完成，返回 {len(search_results)} 个结果")
            return search_results
            
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
    
    def _search_sync(
        self, 
        collection: Collection, 
        query_vectors: List[List[float]], 
        top_k: int,
        filter_expr: Optional[str] = None
    ) -> SearchResult:
        """同步执行向量搜索"""
        return collection.search(
            data=query_vectors,
            anns_field="embedding",
            param=self.search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=[
                "document_id", "chunk_index", "content", 
                "content_hash", "metadata", "created_at"
            ]
        )
    
    async def delete_vectors(
        self, 
        collection_name: str, 
        filter_expr: str
    ) -> bool:
        """删除向量"""
        try:
            collection = await self.get_collection(collection_name)
            if not collection:
                return False
            
            # 在线程池中执行删除
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                collection.delete,
                filter_expr
            )
            
            # 刷新数据
            await loop.run_in_executor(None, collection.flush)
            
            logger.info(f"删除向量完成: {filter_expr}")
            return True
            
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            return False
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            collection = await self.get_collection(collection_name)
            if not collection:
                return {}
            
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None,
                collection.get_stats
            )
            
            return {
                "collection_name": collection_name,
                "row_count": stats.row_count,
                "data_size": stats.data_size,
                "index_size": stats.index_size,
                "embedding_dimension": self.embedding_dim,
                "index_type": self.index_params["index_type"],
                "metric_type": self.index_params["metric_type"]
            }
            
        except Exception as e:
            logger.error(f"获取集合统计失败: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            await self.connect()
            
            # 测试连接
            loop = asyncio.get_event_loop()
            server_version = await loop.run_in_executor(
                None,
                utility.get_server_version,
                self.connection_alias
            )
            
            return {
                "status": "healthy",
                "server_version": server_version,
                "host": self.host,
                "port": self.port,
                "connected": self._connected,
                "embedding_dimension": self.embedding_dim
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "connected": False
            }
    
    async def create_knowledge_base_collection(self, knowledge_base_id: int) -> str:
        """为知识库创建专用集合"""
        collection_name = f"kb_{knowledge_base_id}"
        success = await self.create_collection(collection_name)
        
        if success:
            logger.info(f"知识库 {knowledge_base_id} 的向量集合创建成功")
            return collection_name
        else:
            raise Exception(f"创建知识库向量集合失败: {knowledge_base_id}")


# 全局Milvus服务实例
milvus_service = MilvusVectorService()


# 便捷函数
async def create_kb_collection(knowledge_base_id: int) -> str:
    """为知识库创建向量集合的便捷函数"""
    return await milvus_service.create_knowledge_base_collection(knowledge_base_id)


async def insert_document_vectors(
    knowledge_base_id: int, 
    chunks: List[Dict[str, Any]]
) -> List[str]:
    """插入文档向量的便捷函数"""
    collection_name = f"kb_{knowledge_base_id}"
    return await milvus_service.insert_vectors(collection_name, chunks)


async def search_similar_chunks(
    knowledge_base_id: int,
    query: str,
    top_k: int = 20,
    document_filter: Optional[int] = None
) -> List[Dict[str, Any]]:
    """搜索相似分块的便捷函数"""
    collection_name = f"kb_{knowledge_base_id}"
    
    # 构建过滤表达式
    filter_expr = None
    if document_filter:
        filter_expr = f"document_id == {document_filter}"
    
    return await milvus_service.search_vectors(
        collection_name, query, top_k, filter_expr
    )


async def delete_document_vectors(knowledge_base_id: int, document_id: int) -> bool:
    """删除文档向量的便捷函数"""
    collection_name = f"kb_{knowledge_base_id}"
    filter_expr = f"document_id == {document_id}"
    return await milvus_service.delete_vectors(collection_name, filter_expr)
