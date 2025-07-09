"""
基于ChromaDB的向量数据库管理系统
支持本地和远程连接，使用BAAI/bge-small-zh-v1.5中文嵌入模型
提供完整的文档操作、集合管理和元数据处理功能
"""
import asyncio
import hashlib
import logging
import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.models.Collection import Collection
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    SentenceTransformer = None
    Collection = None

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """连接类型枚举"""
    LOCAL = "local"
    REMOTE = "remote"


class CollectionType(Enum):
    """集合类型枚举"""
    PUBLIC = "public"
    PRIVATE = "private"


@dataclass
class ChromaConfig:
    """ChromaDB配置"""
    connection_type: ConnectionType = ConnectionType.LOCAL
    persist_directory: str = field(default_factory=lambda: str(Path.home() / ".chromadb_intelligent_customer_service"))
    host: Optional[str] = None
    port: Optional[int] = None
    ssl: bool = False
    headers: Optional[Dict[str, str]] = None
    
    # 嵌入模型配置
    embedding_model_name: str = "BAAI/bge-small-zh-v1.5"
    embedding_dimension: int = 512
    device: str = "cpu"
    
    # 性能配置
    batch_size: int = 100
    max_workers: int = 4
    connection_timeout: int = 30
    
    # 集合配置
    default_distance_function: str = "cosine"
    enable_hnsw_index: bool = True
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保持久化目录存在
        if self.connection_type == ConnectionType.LOCAL:
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)


@dataclass
class DocumentMetadata:
    """文档元数据结构"""
    # 文件级元数据
    file_id: str
    knowledge_base_id: str
    file_type: str
    file_name: str
    file_size: int
    file_hash: str
    
    # 块级元数据
    chunk_index: int
    total_chunks: int
    byte_length: int
    chunk_hash: str
    
    # 权限元数据
    is_public: bool
    owner_id: str
    knowledge_type: str
    
    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 扩展元数据
    extra_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "file_id": self.file_id,
            "knowledge_base_id": self.knowledge_base_id,
            "file_type": self.file_type,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "byte_length": self.byte_length,
            "chunk_hash": self.chunk_hash,
            "is_public": self.is_public,
            "owner_id": self.owner_id,
            "knowledge_type": self.knowledge_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            **self.extra_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentMetadata':
        """从字典创建元数据对象"""
        extra_metadata = {k: v for k, v in data.items() if k not in {
            'file_id', 'knowledge_base_id', 'file_type', 'file_name', 'file_size', 'file_hash',
            'chunk_index', 'total_chunks', 'byte_length', 'chunk_hash',
            'is_public', 'owner_id', 'knowledge_type', 'created_at', 'updated_at'
        }}
        
        return cls(
            file_id=data.get("file_id", ""),
            knowledge_base_id=data.get("knowledge_base_id", ""),
            file_type=data.get("file_type", ""),
            file_name=data.get("file_name", ""),
            file_size=data.get("file_size", 0),
            file_hash=data.get("file_hash", ""),
            chunk_index=data.get("chunk_index", 0),
            total_chunks=data.get("total_chunks", 1),
            byte_length=data.get("byte_length", 0),
            chunk_hash=data.get("chunk_hash", ""),
            is_public=data.get("is_public", False),
            owner_id=data.get("owner_id", ""),
            knowledge_type=data.get("knowledge_type", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            extra_metadata=extra_metadata
        )


@dataclass
class SearchResult:
    """搜索结果数据结构"""
    id: str
    content: str
    metadata: DocumentMetadata
    distance: float
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "distance": self.distance,
            "score": self.score
        }


class CollectionNamingStrategy:
    """集合命名策略管理"""
    
    @staticmethod
    def get_collection_name(knowledge_type: str, collection_type: CollectionType, user_id: str = None) -> str:
        """
        获取集合名称
        
        Args:
            knowledge_type: 知识类型
            collection_type: 集合类型
            user_id: 用户ID（私有集合需要）
            
        Returns:
            集合名称
        """
        # 清理知识类型名称
        clean_knowledge_type = CollectionNamingStrategy._clean_name(knowledge_type)
        
        if collection_type == CollectionType.PUBLIC:
            return f"{clean_knowledge_type}_public_memory"
        elif collection_type == CollectionType.PRIVATE:
            if not user_id:
                raise ValueError("私有集合需要提供用户ID")
            clean_user_id = CollectionNamingStrategy._clean_name(user_id)
            return f"{clean_knowledge_type}_{clean_user_id}"
        else:
            raise ValueError(f"不支持的集合类型: {collection_type}")
    
    @staticmethod
    def _clean_name(name: str) -> str:
        """
        清理名称，确保符合ChromaDB命名规范
        
        Args:
            name: 原始名称
            
        Returns:
            清理后的名称
        """
        # 转换为小写
        name = name.lower()
        
        # 替换特殊字符为下划线
        name = re.sub(r'[^a-z0-9_]', '_', name)
        
        # 移除连续的下划线
        name = re.sub(r'_+', '_', name)
        
        # 移除开头和结尾的下划线
        name = name.strip('_')
        
        # 确保名称不为空且不超过63个字符（ChromaDB限制）
        if not name:
            name = "default"
        if len(name) > 63:
            name = name[:63]
        
        return name
    
    @staticmethod
    def validate_collection_name(name: str) -> bool:
        """
        验证集合名称是否有效
        
        Args:
            name: 集合名称
            
        Returns:
            是否有效
        """
        if not name or len(name) > 63:
            return False
        
        # 检查是否只包含小写字母、数字和下划线
        if not re.match(r'^[a-z0-9_]+$', name):
            return False
        
        # 不能以下划线开头或结尾
        if name.startswith('_') or name.endswith('_'):
            return False
        
        return True


class MetadataManager:
    """元数据管理器"""
    
    @staticmethod
    def create_file_metadata(
        file_id: str,
        knowledge_base_id: str,
        file_type: str,
        file_name: str,
        file_size: int,
        file_content: str,
        is_public: bool,
        owner_id: str,
        knowledge_type: str,
        extra_metadata: Dict[str, Any] = None
    ) -> str:
        """
        创建文件元数据
        
        Returns:
            文件哈希值
        """
        # 计算文件哈希
        file_hash = hashlib.sha256(file_content.encode('utf-8')).hexdigest()
        
        return file_hash
    
    @staticmethod
    def create_chunk_metadata(
        file_id: str,
        knowledge_base_id: str,
        file_type: str,
        file_name: str,
        file_size: int,
        file_hash: str,
        chunk_content: str,
        chunk_index: int,
        total_chunks: int,
        is_public: bool,
        owner_id: str,
        knowledge_type: str,
        extra_metadata: Dict[str, Any] = None
    ) -> DocumentMetadata:
        """
        创建块级元数据
        
        Returns:
            文档元数据对象
        """
        # 计算块哈希
        chunk_hash = hashlib.sha256(chunk_content.encode('utf-8')).hexdigest()
        
        return DocumentMetadata(
            file_id=file_id,
            knowledge_base_id=knowledge_base_id,
            file_type=file_type,
            file_name=file_name,
            file_size=file_size,
            file_hash=file_hash,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            byte_length=len(chunk_content.encode('utf-8')),
            chunk_hash=chunk_hash,
            is_public=is_public,
            owner_id=owner_id,
            knowledge_type=knowledge_type,
            extra_metadata=extra_metadata or {}
        )
    
    @staticmethod
    def build_search_filter(
        knowledge_base_id: str = None,
        file_id: str = None,
        owner_id: str = None,
        is_public: bool = None,
        knowledge_type: str = None,
        file_type: str = None,
        custom_filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        构建搜索过滤条件
        
        Returns:
            过滤条件字典
        """
        filters = {}
        
        if knowledge_base_id is not None:
            filters["knowledge_base_id"] = knowledge_base_id
        if file_id is not None:
            filters["file_id"] = file_id
        if owner_id is not None:
            filters["owner_id"] = owner_id
        if is_public is not None:
            filters["is_public"] = is_public
        if knowledge_type is not None:
            filters["knowledge_type"] = knowledge_type
        if file_type is not None:
            filters["file_type"] = file_type
        
        if custom_filters:
            filters.update(custom_filters)
        
        return filters


class ChromaVectorDBManager:
    """
    ChromaDB向量数据库管理器
    支持本地和远程连接，提供完整的文档操作和集合管理功能
    """

    def __init__(self, config: ChromaConfig = None):
        """
        初始化ChromaDB管理器

        Args:
            config: ChromaDB配置
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB不可用，请安装: pip install chromadb sentence-transformers")

        self.config = config or ChromaConfig()
        self.client = None
        self.embedding_model = None
        self.collections_cache = {}

        # 统计信息
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "total_documents": 0,
            "total_collections": 0,
            "last_health_check": None,
            "connection_status": "disconnected"
        }

        logger.info(f"ChromaDB管理器初始化完成，连接类型: {self.config.connection_type.value}")

    async def initialize(self) -> bool:
        """
        初始化连接和嵌入模型

        Returns:
            是否初始化成功
        """
        try:
            # 初始化ChromaDB客户端
            await self._initialize_client()

            # 初始化嵌入模型
            await self._initialize_embedding_model()

            # 执行健康检查
            health_status = await self.health_check()
            if health_status["status"] == "healthy":
                self.stats["connection_status"] = "connected"
                logger.info("ChromaDB管理器初始化成功")
                return True
            else:
                logger.error(f"ChromaDB健康检查失败: {health_status}")
                return False

        except Exception as e:
            logger.error(f"ChromaDB管理器初始化失败: {e}")
            self.stats["connection_status"] = "error"
            return False

    async def _initialize_client(self) -> None:
        """初始化ChromaDB客户端"""
        try:
            if self.config.connection_type == ConnectionType.LOCAL:
                # 本地持久化客户端
                self.client = chromadb.PersistentClient(
                    path=self.config.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True,
                        is_persistent=True
                    )
                )
                logger.info(f"本地ChromaDB客户端初始化成功: {self.config.persist_directory}")

            elif self.config.connection_type == ConnectionType.REMOTE:
                # 远程HTTP客户端
                if not self.config.host or not self.config.port:
                    raise ValueError("远程连接需要提供host和port")

                self.client = chromadb.HttpClient(
                    host=self.config.host,
                    port=self.config.port,
                    ssl=self.config.ssl,
                    headers=self.config.headers or {}
                )
                logger.info(f"远程ChromaDB客户端初始化成功: {self.config.host}:{self.config.port}")

            else:
                raise ValueError(f"不支持的连接类型: {self.config.connection_type}")

        except Exception as e:
            logger.error(f"ChromaDB客户端初始化失败: {e}")
            raise

    async def _initialize_embedding_model(self) -> None:
        """初始化嵌入模型"""
        try:
            # 使用BAAI/bge-small-zh-v1.5中文嵌入模型
            self.embedding_model = SentenceTransformer(
                self.config.embedding_model_name,
                device=self.config.device
            )

            # 验证模型维度
            test_embedding = self.embedding_model.encode(["测试文本"])
            actual_dimension = len(test_embedding[0])

            if actual_dimension != self.config.embedding_dimension:
                logger.warning(f"嵌入维度不匹配，期望: {self.config.embedding_dimension}, 实际: {actual_dimension}")
                self.config.embedding_dimension = actual_dimension

            logger.info(f"嵌入模型初始化成功: {self.config.embedding_model_name}, 维度: {actual_dimension}")

        except Exception as e:
            logger.error(f"嵌入模型初始化失败: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        执行健康检查

        Returns:
            健康状态信息
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "client_status": "connected" if self.client else "disconnected",
                "embedding_model_status": "loaded" if self.embedding_model else "not_loaded",
                "collections_count": 0,
                "total_documents": 0,
                "config": {
                    "connection_type": self.config.connection_type.value,
                    "embedding_model": self.config.embedding_model_name,
                    "embedding_dimension": self.config.embedding_dimension
                }
            }

            if self.client:
                try:
                    # 获取所有集合
                    collections = self.client.list_collections()
                    health_status["collections_count"] = len(collections)

                    # 统计文档数量
                    total_docs = 0
                    for collection in collections:
                        try:
                            count = collection.count()
                            total_docs += count
                        except Exception:
                            pass

                    health_status["total_documents"] = total_docs

                except Exception as e:
                    health_status["status"] = "degraded"
                    health_status["error"] = str(e)
            else:
                health_status["status"] = "error"
                health_status["error"] = "客户端未初始化"

            # 更新统计信息
            self.stats["last_health_check"] = health_status["timestamp"]
            self.stats["total_collections"] = health_status["collections_count"]
            self.stats["total_documents"] = health_status["total_documents"]

            return health_status

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def create_collection(
        self,
        knowledge_type: str,
        collection_type: CollectionType,
        user_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        创建集合

        Args:
            knowledge_type: 知识类型
            collection_type: 集合类型
            user_id: 用户ID（私有集合需要）
            metadata: 集合元数据

        Returns:
            集合名称
        """
        try:
            self.stats["total_operations"] += 1

            # 生成集合名称
            collection_name = CollectionNamingStrategy.get_collection_name(
                knowledge_type, collection_type, user_id
            )

            # 验证集合名称
            if not CollectionNamingStrategy.validate_collection_name(collection_name):
                raise ValueError(f"无效的集合名称: {collection_name}")

            # 检查集合是否已存在
            try:
                existing_collection = self.client.get_collection(collection_name)
                logger.info(f"集合已存在: {collection_name}")
                self.collections_cache[collection_name] = existing_collection
                return collection_name
            except Exception:
                # 集合不存在，继续创建
                pass

            # 创建集合元数据
            collection_metadata = {
                "knowledge_type": knowledge_type,
                "collection_type": collection_type.value,
                "created_at": datetime.now().isoformat(),
                "embedding_model": self.config.embedding_model_name,
                "embedding_dimension": self.config.embedding_dimension
            }

            if user_id:
                collection_metadata["user_id"] = user_id

            if metadata:
                collection_metadata.update(metadata)

            # 创建集合
            collection = self.client.create_collection(
                name=collection_name,
                metadata=collection_metadata,
                embedding_function=None  # 我们使用自定义嵌入
            )

            # 缓存集合
            self.collections_cache[collection_name] = collection

            self.stats["successful_operations"] += 1
            logger.info(f"集合创建成功: {collection_name}")

            return collection_name

        except Exception as e:
            self.stats["failed_operations"] += 1
            logger.error(f"创建集合失败: {e}")
            raise

    async def get_collection(self, collection_name: str) -> Collection:
        """
        获取集合

        Args:
            collection_name: 集合名称

        Returns:
            集合对象
        """
        try:
            # 先从缓存获取
            if collection_name in self.collections_cache:
                return self.collections_cache[collection_name]

            # 从数据库获取
            collection = self.client.get_collection(collection_name)
            self.collections_cache[collection_name] = collection

            return collection

        except Exception as e:
            logger.error(f"获取集合失败: {collection_name}, 错误: {e}")
            raise

    async def delete_collection(self, collection_name: str) -> bool:
        """
        删除集合

        Args:
            collection_name: 集合名称

        Returns:
            是否删除成功
        """
        try:
            self.stats["total_operations"] += 1

            # 删除集合
            self.client.delete_collection(collection_name)

            # 从缓存中移除
            if collection_name in self.collections_cache:
                del self.collections_cache[collection_name]

            self.stats["successful_operations"] += 1
            logger.info(f"集合删除成功: {collection_name}")

            return True

        except Exception as e:
            self.stats["failed_operations"] += 1
            logger.error(f"删除集合失败: {collection_name}, 错误: {e}")
            return False

    async def add_document(
        self,
        collection_name: str,
        content: str,
        metadata: DocumentMetadata,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """
        添加文档，支持智能分块和元数据存储

        Args:
            collection_name: 集合名称
            content: 文档内容
            metadata: 文档元数据
            chunk_size: 分块大小
            chunk_overlap: 分块重叠

        Returns:
            文档块ID列表
        """
        try:
            self.stats["total_operations"] += 1

            # 获取集合
            collection = await self.get_collection(collection_name)

            # 智能分块
            chunks = await self._intelligent_chunk_text(content, chunk_size, chunk_overlap)

            # 准备批量插入数据
            chunk_ids = []
            chunk_contents = []
            chunk_embeddings = []
            chunk_metadatas = []

            total_chunks = len(chunks)

            for i, chunk_content in enumerate(chunks):
                # 生成块ID
                chunk_id = f"{metadata.file_id}_chunk_{i}_{uuid.uuid4().hex[:8]}"

                # 创建块元数据
                chunk_metadata = MetadataManager.create_chunk_metadata(
                    file_id=metadata.file_id,
                    knowledge_base_id=metadata.knowledge_base_id,
                    file_type=metadata.file_type,
                    file_name=metadata.file_name,
                    file_size=metadata.file_size,
                    file_hash=metadata.file_hash,
                    chunk_content=chunk_content,
                    chunk_index=i,
                    total_chunks=total_chunks,
                    is_public=metadata.is_public,
                    owner_id=metadata.owner_id,
                    knowledge_type=metadata.knowledge_type,
                    extra_metadata=metadata.extra_metadata
                )

                # 生成嵌入向量
                embedding = await self._create_embedding(chunk_content)

                chunk_ids.append(chunk_id)
                chunk_contents.append(chunk_content)
                chunk_embeddings.append(embedding)
                chunk_metadatas.append(chunk_metadata.to_dict())

            # 批量插入
            collection.add(
                ids=chunk_ids,
                documents=chunk_contents,
                embeddings=chunk_embeddings,
                metadatas=chunk_metadatas
            )

            self.stats["successful_operations"] += 1
            self.stats["total_documents"] += len(chunk_ids)

            logger.info(f"文档添加成功: {metadata.file_id}, 分块数: {len(chunk_ids)}")

            return chunk_ids

        except Exception as e:
            self.stats["failed_operations"] += 1
            logger.error(f"添加文档失败: {e}")
            raise

    async def _intelligent_chunk_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[str]:
        """
        智能文本分块

        Args:
            text: 文本内容
            chunk_size: 分块大小
            chunk_overlap: 分块重叠

        Returns:
            分块列表
        """
        try:
            # 预处理文本
            text = text.strip()
            if not text:
                return []

            # 使用递归字符分割器进行分块
            separators = [
                "\n\n",  # 段落分隔符
                "\n",    # 行分隔符
                "。",    # 中文句号
                "！",    # 中文感叹号
                "？",    # 中文问号
                ".",     # 英文句号
                "!",     # 英文感叹号
                "?",     # 英文问号
                ";",     # 分号
                ",",     # 逗号
                " ",     # 空格
                ""       # 字符级别
            ]

            chunks = []
            current_chunk = ""

            # 按段落分割
            paragraphs = text.split("\n\n")

            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    continue

                # 如果当前块加上新段落不超过限制，则合并
                if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # 保存当前块
                    if current_chunk:
                        chunks.append(current_chunk)

                    # 如果单个段落过长，需要进一步分割
                    if len(paragraph) > chunk_size:
                        sub_chunks = self._split_long_text(paragraph, chunk_size, chunk_overlap, separators)
                        chunks.extend(sub_chunks)
                        current_chunk = ""
                    else:
                        current_chunk = paragraph

            # 添加最后一个块
            if current_chunk:
                chunks.append(current_chunk)

            # 处理重叠
            if chunk_overlap > 0 and len(chunks) > 1:
                chunks = self._add_chunk_overlap(chunks, chunk_overlap)

            return chunks

        except Exception as e:
            logger.error(f"智能分块失败: {e}")
            # 降级到简单分块
            return self._simple_chunk_text(text, chunk_size)

    def _split_long_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        separators: List[str]
    ) -> List[str]:
        """分割长文本"""
        if len(text) <= chunk_size:
            return [text]

        # 尝试使用分隔符分割
        for separator in separators:
            if separator in text:
                parts = text.split(separator)
                chunks = []
                current_chunk = ""

                for part in parts:
                    if len(current_chunk) + len(part) + len(separator) <= chunk_size:
                        if current_chunk:
                            current_chunk += separator + part
                        else:
                            current_chunk = part
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)

                        if len(part) > chunk_size:
                            # 递归分割
                            sub_chunks = self._split_long_text(part, chunk_size, chunk_overlap, separators[1:])
                            chunks.extend(sub_chunks)
                            current_chunk = ""
                        else:
                            current_chunk = part

                if current_chunk:
                    chunks.append(current_chunk)

                return chunks

        # 如果所有分隔符都无效，按字符分割
        return self._simple_chunk_text(text, chunk_size)

    def _simple_chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """简单文本分块"""
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks

    def _add_chunk_overlap(self, chunks: List[str], overlap: int) -> List[str]:
        """添加分块重叠"""
        if len(chunks) <= 1 or overlap <= 0:
            return chunks

        overlapped_chunks = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]

            # 从前一个块的末尾取重叠部分
            if len(prev_chunk) > overlap:
                overlap_text = prev_chunk[-overlap:]
                overlapped_chunk = overlap_text + " " + current_chunk
            else:
                overlapped_chunk = prev_chunk + " " + current_chunk

            overlapped_chunks.append(overlapped_chunk)

        return overlapped_chunks

    async def _create_embedding(self, text: str) -> List[float]:
        """
        创建文本嵌入向量

        Args:
            text: 文本内容

        Returns:
            嵌入向量
        """
        try:
            # 预处理文本
            text = text.strip()
            if not text:
                # 返回零向量
                return [0.0] * self.config.embedding_dimension

            # 生成嵌入向量
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)

            return embedding.tolist()

        except Exception as e:
            logger.error(f"创建嵌入向量失败: {e}")
            # 返回零向量
            return [0.0] * self.config.embedding_dimension

    async def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 10,
        where: Dict[str, Any] = None,
        where_document: Dict[str, Any] = None,
        include_distances: bool = True
    ) -> List[SearchResult]:
        """
        向量相似度搜索，支持元数据过滤

        Args:
            collection_name: 集合名称
            query: 查询文本
            n_results: 返回结果数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件
            include_distances: 是否包含距离信息

        Returns:
            搜索结果列表
        """
        try:
            self.stats["total_operations"] += 1

            # 获取集合
            collection = await self.get_collection(collection_name)

            # 生成查询向量
            query_embedding = await self._create_embedding(query)

            # 执行搜索
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"] if include_distances else ["documents", "metadatas"]
            )

            # 处理搜索结果
            search_results = []

            if results["ids"] and len(results["ids"]) > 0:
                ids = results["ids"][0]
                documents = results["documents"][0] if "documents" in results else []
                metadatas = results["metadatas"][0] if "metadatas" in results else []
                distances = results["distances"][0] if "distances" in results else []

                for i in range(len(ids)):
                    # 计算相似度分数 (1 - distance)
                    distance = distances[i] if i < len(distances) else 1.0
                    score = max(0.0, 1.0 - distance)

                    # 创建元数据对象
                    metadata_dict = metadatas[i] if i < len(metadatas) else {}
                    metadata = DocumentMetadata.from_dict(metadata_dict)

                    # 创建搜索结果
                    search_result = SearchResult(
                        id=ids[i],
                        content=documents[i] if i < len(documents) else "",
                        metadata=metadata,
                        distance=distance,
                        score=score
                    )

                    search_results.append(search_result)

            self.stats["successful_operations"] += 1
            logger.info(f"搜索完成: {collection_name}, 查询: '{query}', 结果数: {len(search_results)}")

            return search_results

        except Exception as e:
            self.stats["failed_operations"] += 1
            logger.error(f"搜索失败: {e}")
            raise

    async def delete_file(self, collection_name: str, file_id: str) -> bool:
        """
        按文件ID删除相关块

        Args:
            collection_name: 集合名称
            file_id: 文件ID

        Returns:
            是否删除成功
        """
        try:
            self.stats["total_operations"] += 1

            # 获取集合
            collection = await self.get_collection(collection_name)

            # 查询要删除的文档
            results = collection.get(
                where={"file_id": file_id},
                include=["documents", "metadatas"]
            )

            if not results["ids"]:
                logger.warning(f"未找到文件相关的文档块: {file_id}")
                return True

            # 删除文档
            collection.delete(where={"file_id": file_id})

            deleted_count = len(results["ids"])
            self.stats["successful_operations"] += 1
            self.stats["total_documents"] -= deleted_count

            logger.info(f"文件删除成功: {file_id}, 删除块数: {deleted_count}")

            return True

        except Exception as e:
            self.stats["failed_operations"] += 1
            logger.error(f"删除文件失败: {file_id}, 错误: {e}")
            return False

    async def delete_knowledge_base(self, collection_name: str, knowledge_base_id: str) -> bool:
        """
        按知识库ID批量删除

        Args:
            collection_name: 集合名称
            knowledge_base_id: 知识库ID

        Returns:
            是否删除成功
        """
        try:
            self.stats["total_operations"] += 1

            # 获取集合
            collection = await self.get_collection(collection_name)

            # 查询要删除的文档
            results = collection.get(
                where={"knowledge_base_id": knowledge_base_id},
                include=["documents", "metadatas"]
            )

            if not results["ids"]:
                logger.warning(f"未找到知识库相关的文档: {knowledge_base_id}")
                return True

            # 删除文档
            collection.delete(where={"knowledge_base_id": knowledge_base_id})

            deleted_count = len(results["ids"])
            self.stats["successful_operations"] += 1
            self.stats["total_documents"] -= deleted_count

            logger.info(f"知识库删除成功: {knowledge_base_id}, 删除块数: {deleted_count}")

            return True

        except Exception as e:
            self.stats["failed_operations"] += 1
            logger.error(f"删除知识库失败: {knowledge_base_id}, 错误: {e}")
            return False

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合统计信息

        Args:
            collection_name: 集合名称

        Returns:
            统计信息
        """
        try:
            collection = await self.get_collection(collection_name)

            # 获取基本统计
            total_count = collection.count()

            # 获取集合元数据
            collection_metadata = collection.metadata or {}

            # 统计不同文件类型的数量
            file_type_stats = {}
            knowledge_base_stats = {}

            # 分批获取所有文档的元数据
            batch_size = 1000
            offset = 0

            while True:
                results = collection.get(
                    include=["metadatas"],
                    limit=batch_size,
                    offset=offset
                )

                if not results["metadatas"]:
                    break

                for metadata in results["metadatas"]:
                    # 统计文件类型
                    file_type = metadata.get("file_type", "unknown")
                    file_type_stats[file_type] = file_type_stats.get(file_type, 0) + 1

                    # 统计知识库
                    kb_id = metadata.get("knowledge_base_id", "unknown")
                    knowledge_base_stats[kb_id] = knowledge_base_stats.get(kb_id, 0) + 1

                if len(results["metadatas"]) < batch_size:
                    break

                offset += batch_size

            return {
                "collection_name": collection_name,
                "total_documents": total_count,
                "collection_metadata": collection_metadata,
                "file_type_distribution": file_type_stats,
                "knowledge_base_distribution": knowledge_base_stats,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"获取集合统计失败: {collection_name}, 错误: {e}")
            return {
                "collection_name": collection_name,
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }

    async def list_collections(self) -> List[Dict[str, Any]]:
        """
        列出所有集合

        Returns:
            集合信息列表
        """
        try:
            collections = self.client.list_collections()

            collection_info = []
            for collection in collections:
                info = {
                    "name": collection.name,
                    "metadata": collection.metadata or {},
                    "count": collection.count()
                }
                collection_info.append(info)

            return collection_info

        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []

    async def close(self) -> None:
        """关闭连接，释放资源"""
        try:
            # 清理缓存
            self.collections_cache.clear()

            # 重置统计
            self.stats["connection_status"] = "disconnected"

            logger.info("ChromaDB管理器已关闭")

        except Exception as e:
            logger.error(f"关闭ChromaDB管理器失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取管理器统计信息

        Returns:
            统计信息
        """
        return {
            **self.stats,
            "config": {
                "connection_type": self.config.connection_type.value,
                "embedding_model": self.config.embedding_model_name,
                "embedding_dimension": self.config.embedding_dimension,
                "batch_size": self.config.batch_size
            },
            "cached_collections": list(self.collections_cache.keys())
        }
