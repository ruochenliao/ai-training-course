"""
向量存储

负责向量的存储、检索和管理，支持多种向量数据库。
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import uuid
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class Document:
    """文档对象"""
    
    def __init__(self, id: str, content: str, metadata: Dict[str, Any] = None,
                 embedding: List[float] = None):
        self.id = id
        self.content = content
        self.metadata = metadata or {}
        self.embedding = embedding
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """从字典创建文档"""
        doc = cls(
            id=data["id"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding")
        )
        if "created_at" in data:
            doc.created_at = datetime.fromisoformat(data["created_at"])
        return doc


class SearchResult:
    """搜索结果"""
    
    def __init__(self, document: Document, score: float, rank: int = 0):
        self.document = document
        self.score = score
        self.rank = rank
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "rank": self.rank
        }


class BaseVectorStore(ABC):
    """向量存储基类"""
    
    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档"""
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], top_k: int = 10,
                    filters: Dict[str, Any] = None) -> List[SearchResult]:
        """搜索相似文档"""
        pass
    
    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        pass
    
    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        pass
    
    @abstractmethod
    async def update_document(self, doc_id: str, document: Document) -> bool:
        """更新文档"""
        pass
    
    @abstractmethod
    async def count_documents(self, filters: Dict[str, Any] = None) -> int:
        """统计文档数量"""
        pass


class MilvusVectorStore(BaseVectorStore):
    """Milvus向量存储"""
    
    def __init__(self, host: str = "localhost", port: int = 19530,
                 collection_name: str = "documents", dimension: int = 1536):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.dimension = dimension
        self.collection = None
        
        try:
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
            self.connections = connections
            self.Collection = Collection
            self.FieldSchema = FieldSchema
            self.CollectionSchema = CollectionSchema
            self.DataType = DataType
        except ImportError:
            raise ImportError("需要安装pymilvus: pip install pymilvus")
    
    async def connect(self):
        """连接到Milvus"""
        try:
            self.connections.connect("default", host=self.host, port=self.port)
            await self._create_collection()
            logger.info(f"连接到Milvus: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"连接Milvus失败: {e}")
            raise
    
    async def _create_collection(self):
        """创建集合"""
        try:
            # 定义字段
            fields = [
                self.FieldSchema(name="id", dtype=self.DataType.VARCHAR, max_length=100, is_primary=True),
                self.FieldSchema(name="content", dtype=self.DataType.VARCHAR, max_length=65535),
                self.FieldSchema(name="metadata", dtype=self.DataType.VARCHAR, max_length=65535),
                self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=self.dimension),
                self.FieldSchema(name="created_at", dtype=self.DataType.VARCHAR, max_length=50)
            ]
            
            # 创建集合模式
            schema = self.CollectionSchema(fields, description="文档向量存储")
            
            # 创建集合
            if not self.connections.has_collection(self.collection_name):
                self.collection = self.Collection(self.collection_name, schema)
                
                # 创建索引
                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                self.collection.create_index("embedding", index_params)
                logger.info(f"创建Milvus集合: {self.collection_name}")
            else:
                self.collection = self.Collection(self.collection_name)
            
            # 加载集合
            self.collection.load()
            
        except Exception as e:
            logger.error(f"创建Milvus集合失败: {e}")
            raise
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档"""
        try:
            if not self.collection:
                await self.connect()
            
            # 准备数据
            ids = []
            contents = []
            metadatas = []
            embeddings = []
            created_ats = []
            
            for doc in documents:
                if not doc.embedding:
                    raise ValueError(f"文档 {doc.id} 缺少嵌入向量")
                
                ids.append(doc.id)
                contents.append(doc.content)
                metadatas.append(json.dumps(doc.metadata, ensure_ascii=False))
                embeddings.append(doc.embedding)
                created_ats.append(doc.created_at.isoformat())
            
            # 插入数据
            entities = [ids, contents, metadatas, embeddings, created_ats]
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"添加 {len(documents)} 个文档到Milvus")
            return ids
            
        except Exception as e:
            logger.error(f"添加文档到Milvus失败: {e}")
            raise
    
    async def search(self, query_embedding: List[float], top_k: int = 10,
                    filters: Dict[str, Any] = None) -> List[SearchResult]:
        """搜索相似文档"""
        try:
            if not self.collection:
                await self.connect()
            
            # 搜索参数
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            # 执行搜索
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["id", "content", "metadata", "created_at"]
            )
            
            # 处理结果
            search_results = []
            for i, hit in enumerate(results[0]):
                metadata = json.loads(hit.entity.get("metadata", "{}"))
                
                document = Document(
                    id=hit.entity.get("id"),
                    content=hit.entity.get("content"),
                    metadata=metadata
                )
                
                if hit.entity.get("created_at"):
                    document.created_at = datetime.fromisoformat(hit.entity.get("created_at"))
                
                search_result = SearchResult(
                    document=document,
                    score=float(hit.score),
                    rank=i + 1
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Milvus搜索失败: {e}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        try:
            if not self.collection:
                await self.connect()
            
            # 查询文档
            expr = f'id == "{doc_id}"'
            results = self.collection.query(
                expr=expr,
                output_fields=["id", "content", "metadata", "created_at"]
            )
            
            if not results:
                return None
            
            result = results[0]
            metadata = json.loads(result.get("metadata", "{}"))
            
            document = Document(
                id=result.get("id"),
                content=result.get("content"),
                metadata=metadata
            )
            
            if result.get("created_at"):
                document.created_at = datetime.fromisoformat(result.get("created_at"))
            
            return document
            
        except Exception as e:
            logger.error(f"获取Milvus文档失败: {e}")
            return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            if not self.collection:
                await self.connect()
            
            expr = f'id == "{doc_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"删除Milvus文档: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除Milvus文档失败: {e}")
            return False
    
    async def update_document(self, doc_id: str, document: Document) -> bool:
        """更新文档"""
        try:
            # Milvus不支持直接更新，需要先删除再插入
            await self.delete_document(doc_id)
            document.id = doc_id
            await self.add_documents([document])
            return True
        except Exception as e:
            logger.error(f"更新Milvus文档失败: {e}")
            return False
    
    async def count_documents(self, filters: Dict[str, Any] = None) -> int:
        """统计文档数量"""
        try:
            if not self.collection:
                await self.connect()
            
            return self.collection.num_entities
        except Exception as e:
            logger.error(f"统计Milvus文档数量失败: {e}")
            return 0


class InMemoryVectorStore(BaseVectorStore):
    """内存向量存储（用于测试和开发）"""
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档"""
        ids = []
        for doc in documents:
            self.documents[doc.id] = doc
            ids.append(doc.id)
        
        logger.info(f"添加 {len(documents)} 个文档到内存存储")
        return ids
    
    async def search(self, query_embedding: List[float], top_k: int = 10,
                    filters: Dict[str, Any] = None) -> List[SearchResult]:
        """搜索相似文档"""
        import numpy as np
        
        results = []
        query_vec = np.array(query_embedding)
        
        for doc in self.documents.values():
            if not doc.embedding:
                continue
            
            # 应用过滤器
            if filters:
                match = True
                for key, value in filters.items():
                    if key not in doc.metadata or doc.metadata[key] != value:
                        match = False
                        break
                if not match:
                    continue
            
            # 计算余弦相似度
            doc_vec = np.array(doc.embedding)
            similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
            
            results.append(SearchResult(doc, float(similarity)))
        
        # 按相似度排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 设置排名并返回top_k
        for i, result in enumerate(results[:top_k]):
            result.rank = i + 1
        
        return results[:top_k]
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return self.documents.get(doc_id)
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False
    
    async def update_document(self, doc_id: str, document: Document) -> bool:
        """更新文档"""
        if doc_id in self.documents:
            document.id = doc_id
            self.documents[doc_id] = document
            return True
        return False
    
    async def count_documents(self, filters: Dict[str, Any] = None) -> int:
        """统计文档数量"""
        if not filters:
            return len(self.documents)
        
        count = 0
        for doc in self.documents.values():
            match = True
            for key, value in filters.items():
                if key not in doc.metadata or doc.metadata[key] != value:
                    match = False
                    break
            if match:
                count += 1
        
        return count


class VectorStore:
    """向量存储管理器"""
    
    def __init__(self, store_type: str = "memory", **kwargs):
        self.store_type = store_type
        
        if store_type == "milvus":
            self.store = MilvusVectorStore(**kwargs)
        elif store_type == "memory":
            self.store = InMemoryVectorStore()
        else:
            raise ValueError(f"不支持的存储类型: {store_type}")
    
    async def initialize(self):
        """初始化存储"""
        if hasattr(self.store, 'connect'):
            await self.store.connect()
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档"""
        return await self.store.add_documents(documents)
    
    async def search(self, query_embedding: List[float], top_k: int = 10,
                    filters: Dict[str, Any] = None) -> List[SearchResult]:
        """搜索相似文档"""
        return await self.store.search(query_embedding, top_k, filters)
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return await self.store.get_document(doc_id)
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        return await self.store.delete_document(doc_id)
    
    async def update_document(self, doc_id: str, document: Document) -> bool:
        """更新文档"""
        return await self.store.update_document(doc_id, document)
    
    async def count_documents(self, filters: Dict[str, Any] = None) -> int:
        """统计文档数量"""
        return await self.store.count_documents(filters)
