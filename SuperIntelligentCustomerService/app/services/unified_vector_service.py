"""
统一向量数据库服务
整合所有现有的向量数据库功能，提供统一的接口
支持ChromaDB作为底层存储，提供多种使用场景
"""
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

# 尝试导入 chromadb
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    from chromadb.utils.embedding_functions.sentence_transformer_embedding_function import \
        SentenceTransformerEmbeddingFunction
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("未找到 ChromaDB 库。向量数据库功能将被禁用。")

import logging
from ..settings.config import settings
from ..utils.text_chunker import TextChunker, ChunkerConfig
from ..settings.file_types import FileProcessingMethod, get_processing_method

logger = logging.getLogger(__name__)


class VectorCollectionType(Enum):
    """向量集合类型"""
    KNOWLEDGE_BASE = "knowledge_base"  # 知识库
    CHAT_MEMORY = "chat_memory"       # 聊天记忆
    PRIVATE_MEMORY = "private_memory"  # 私有记忆
    PUBLIC_MEMORY = "public_memory"    # 公共记忆
    CUSTOMER_SERVICE = "customer_service"  # 客服知识


@dataclass
class VectorSearchConfig:
    """向量搜索配置"""
    limit: int = 10
    score_threshold: float = 0.3
    include_metadata: bool = True
    include_documents: bool = True
    include_distances: bool = True


@dataclass
class VectorDocument:
    """向量文档"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    id: str
    content: str
    score: float
    distance: float
    metadata: Dict[str, Any]


class UnifiedVectorService:
    """统一向量数据库服务"""
    
    def __init__(self, 
                 remote_url: Optional[str] = None, 
                 remote_port: Optional[int] = None,
                 base_path: Optional[str] = None):
        """
        初始化统一向量数据库服务
        
        Args:
            remote_url: 远程ChromaDB URL
            remote_port: 远程ChromaDB端口
            base_path: 本地存储基础路径
        """
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB 不可用。向量数据库功能将被禁用。")
            self.chroma_client = None
            return
        
        self.base_path = base_path or self._get_default_base_path()
        self.remote_url = remote_url
        self.remote_port = remote_port
        
        # 初始化嵌入函数
        self.embedding_function = self._init_embedding_function()
        
        # 初始化ChromaDB客户端
        self.chroma_client = self._init_chroma_client()
        
        # 集合缓存
        self._collections_cache = {}
        
        logger.info(f"统一向量数据库服务初始化完成，存储路径: {self.base_path}")
    
    def _get_default_base_path(self) -> str:
        """获取默认存储路径"""
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        return str(project_root / "data" / "unified_vector_db")
    
    def _init_embedding_function(self):
        """初始化嵌入函数"""
        try:
            # 优先使用BGE模型
            if hasattr(settings, 'BGE_EMBEDDING_MODEL_PATH'):
                return SentenceTransformerEmbeddingFunction(
                    model_name="BAAI/bge-small-zh-v1.5",
                    device="cpu"
                )
            else:
                return embedding_functions.DefaultEmbeddingFunction()
        except Exception as e:
            logger.error(f"初始化嵌入函数失败: {e}")
            return embedding_functions.DefaultEmbeddingFunction()
    
    def _init_chroma_client(self):
        """初始化ChromaDB客户端"""
        if self.remote_url and self.remote_port:
            # 远程连接
            try:
                client = chromadb.HttpClient(
                    host=self.remote_url,
                    port=self.remote_port,
                    settings=Settings(anonymized_telemetry=False)
                )
                client.heartbeat()
                logger.info(f"成功连接到远程ChromaDB: {self.remote_url}:{self.remote_port}")
                return client
            except Exception as e:
                logger.error(f"连接远程ChromaDB失败: {e}")
                return None
        else:
            # 本地连接
            try:
                os.makedirs(self.base_path, exist_ok=True)
                client = chromadb.PersistentClient(
                    path=self.base_path,
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info(f"使用本地ChromaDB: {self.base_path}")
                return client
            except Exception as e:
                logger.error(f"初始化本地ChromaDB失败: {e}")
                return None
    
    def _generate_collection_name(self, 
                                collection_type: VectorCollectionType,
                                identifier: Optional[str] = None,
                                is_public: bool = False,
                                owner_id: Optional[int] = None) -> str:
        """
        生成集合名称
        
        Args:
            collection_type: 集合类型
            identifier: 标识符（如知识库ID、用户ID等）
            is_public: 是否公开
            owner_id: 所有者ID
        """
        base_name = collection_type.value
        
        if collection_type == VectorCollectionType.KNOWLEDGE_BASE:
            if identifier:
                return f"kb_{identifier}"
            else:
                return "kb_default"
        elif collection_type == VectorCollectionType.CHAT_MEMORY:
            if identifier:
                return f"chat_{identifier}"
            else:
                return "chat_default"
        elif collection_type == VectorCollectionType.PRIVATE_MEMORY:
            if identifier and owner_id:
                return f"private_{identifier}_{owner_id}"
            elif identifier:
                return f"private_{identifier}"
            else:
                return "private_default"
        elif collection_type == VectorCollectionType.PUBLIC_MEMORY:
            return f"public_{identifier}" if identifier else "public_memory"
        elif collection_type == VectorCollectionType.CUSTOMER_SERVICE:
            if is_public:
                return f"{base_name}_public"
            elif owner_id:
                return f"{base_name}_{owner_id}"
            else:
                return f"{base_name}_default"
        
        # 清理集合名称
        collection_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base_name)
        collection_name = collection_name.strip('.')
        
        if not (3 <= len(collection_name) <= 63):
            collection_name = f"col_{collection_name}"[:63]
        
        return collection_name
    
    def get_or_create_collection(self, 
                               collection_type: VectorCollectionType,
                               identifier: Optional[str] = None,
                               is_public: bool = False,
                               owner_id: Optional[int] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """获取或创建集合"""
        if not self.chroma_client:
            logger.warning("ChromaDB客户端不可用")
            return None
        
        collection_name = self._generate_collection_name(
            collection_type, identifier, is_public, owner_id
        )
        
        # 检查缓存
        if collection_name in self._collections_cache:
            return self._collections_cache[collection_name]
        
        # 准备元数据
        collection_metadata = {
            "collection_type": collection_type.value,
            "is_public": str(is_public).lower(),
            "created_at": datetime.now().isoformat()
        }
        
        if identifier:
            collection_metadata["identifier"] = identifier
        if owner_id:
            collection_metadata["owner_id"] = str(owner_id)
        if metadata:
            collection_metadata.update(metadata)
        
        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata=collection_metadata
            )
            
            # 缓存集合
            self._collections_cache[collection_name] = collection
            
            logger.info(f"成功获取或创建集合: {collection_name}")
            return collection
            
        except Exception as e:
            logger.error(f"获取或创建集合失败: {e}")
            return None

    async def add_documents(self,
                          collection_type: VectorCollectionType,
                          documents: List[VectorDocument],
                          identifier: Optional[str] = None,
                          is_public: bool = False,
                          owner_id: Optional[int] = None) -> List[str]:
        """
        添加文档到向量数据库

        Args:
            collection_type: 集合类型
            documents: 文档列表
            identifier: 标识符
            is_public: 是否公开
            owner_id: 所有者ID

        Returns:
            添加的文档ID列表
        """
        if not self.chroma_client:
            logger.warning("ChromaDB客户端不可用")
            return []

        collection = self.get_or_create_collection(
            collection_type, identifier, is_public, owner_id
        )

        if not collection:
            logger.error("无法获取或创建集合")
            return []

        try:
            # 准备数据
            ids = [doc.id for doc in documents]
            contents = [doc.content for doc in documents]
            metadatas = []

            for doc in documents:
                metadata = doc.metadata.copy()
                metadata.update({
                    "collection_type": collection_type.value,
                    "is_public": is_public,
                    "added_at": datetime.now().isoformat(),
                    "content_length": len(doc.content)
                })

                if identifier:
                    metadata["identifier"] = identifier
                if owner_id:
                    metadata["owner_id"] = str(owner_id)

                metadatas.append(metadata)

            # 添加到集合
            collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas
            )

            logger.info(f"成功添加 {len(documents)} 个文档到集合 {collection.name}")
            return ids

        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return []

    async def add_document_chunks(self,
                                collection_type: VectorCollectionType,
                                content: str,
                                file_id: int,
                                identifier: Optional[str] = None,
                                is_public: bool = False,
                                owner_id: Optional[int] = None,
                                chunk_size: int = 1024,
                                file_extension: str = '.txt',
                                metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        将文档分块并添加到向量数据库

        Args:
            collection_type: 集合类型
            content: 文档内容
            file_id: 文件ID
            identifier: 标识符
            is_public: 是否公开
            owner_id: 所有者ID
            chunk_size: 分块大小
            file_extension: 文件扩展名
            metadata: 额外元数据

        Returns:
            添加的块ID列表
        """
        if not content:
            return []

        # 智能文本分块
        chunks = self._chunk_text(content, chunk_size, file_extension)

        if not chunks:
            logger.info(f"文件 {file_id} 未生成任何块")
            return []

        # 创建文档对象
        documents = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"file_{file_id}_chunk_{i}"

            chunk_metadata = {
                "file_id": str(file_id),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk)
            }

            if metadata:
                chunk_metadata.update(metadata)

            documents.append(VectorDocument(
                id=chunk_id,
                content=chunk,
                metadata=chunk_metadata
            ))

        return await self.add_documents(
            collection_type, documents, identifier, is_public, owner_id
        )

    def _chunk_text(self, text: str, chunk_size: int = 1024, file_extension: str = '.txt') -> List[str]:
        """智能文本分块"""
        if not text:
            return []

        try:
            # 根据文件类型选择分块方法
            processing_method = get_processing_method(file_extension)
        except ValueError:
            processing_method = FileProcessingMethod.TEXT

        # 配置分块参数
        config = ChunkerConfig(
            chunk_size_bytes=chunk_size,
            overlap_ratio=0.1,
            respect_special_blocks=True,
            preserve_markdown_structure=(processing_method == FileProcessingMethod.MARKDOWN),
            language='auto'
        )

        # 根据处理方法选择分块策略
        if processing_method == FileProcessingMethod.MARKDOWN:
            chunks = TextChunker.chunk_markdown(text, config)
        else:
            chunks = TextChunker.chunk_text(text, config)

        return chunks

    async def search(self,
                   collection_type: VectorCollectionType,
                   query: str,
                   config: Optional[VectorSearchConfig] = None,
                   identifier: Optional[str] = None,
                   is_public: Optional[bool] = None,
                   owner_id: Optional[int] = None,
                   filters: Optional[Dict[str, Any]] = None) -> List[VectorSearchResult]:
        """
        在向量数据库中搜索

        Args:
            collection_type: 集合类型
            query: 搜索查询
            config: 搜索配置
            identifier: 标识符
            is_public: 是否公开
            owner_id: 所有者ID
            filters: 额外过滤条件

        Returns:
            搜索结果列表
        """
        if not self.chroma_client:
            logger.warning("ChromaDB客户端不可用")
            return []

        if config is None:
            config = VectorSearchConfig()

        # 确定集合名称
        if identifier or is_public is not None or owner_id:
            collection_name = self._generate_collection_name(
                collection_type, identifier, is_public or False, owner_id
            )

            try:
                collection = self.chroma_client.get_collection(name=collection_name)
            except Exception as e:
                logger.warning(f"无法获取集合 {collection_name}: {e}")
                return []
        else:
            # 搜索所有相关集合
            return await self._search_multiple_collections(
                collection_type, query, config, filters
            )

        try:
            # 构建查询参数
            include_params = []
            if config.include_metadata:
                include_params.append('metadatas')
            if config.include_documents:
                include_params.append('documents')
            if config.include_distances:
                include_params.append('distances')

            # 构建where条件
            where_conditions = {}
            if filters:
                where_conditions.update(filters)

            # 执行搜索
            results = collection.query(
                query_texts=[query],
                n_results=config.limit,
                include=include_params,
                where=where_conditions if where_conditions else None
            )

            # 格式化结果
            return self._format_search_results(results, config.score_threshold)

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def _search_multiple_collections(self,
                                         collection_type: VectorCollectionType,
                                         query: str,
                                         config: VectorSearchConfig,
                                         filters: Optional[Dict[str, Any]] = None) -> List[VectorSearchResult]:
        """在多个集合中搜索"""
        all_results = []

        try:
            # 获取所有集合
            collections = self.chroma_client.list_collections()

            # 过滤相关集合
            relevant_collections = [
                col for col in collections
                if col.name.startswith(collection_type.value) or
                   (col.metadata and col.metadata.get("collection_type") == collection_type.value)
            ]

            # 在每个集合中搜索
            for collection in relevant_collections:
                try:
                    include_params = []
                    if config.include_metadata:
                        include_params.append('metadatas')
                    if config.include_documents:
                        include_params.append('documents')
                    if config.include_distances:
                        include_params.append('distances')

                    where_conditions = {}
                    if filters:
                        where_conditions.update(filters)

                    results = collection.query(
                        query_texts=[query],
                        n_results=config.limit,
                        include=include_params,
                        where=where_conditions if where_conditions else None
                    )

                    collection_results = self._format_search_results(results, config.score_threshold)
                    all_results.extend(collection_results)

                except Exception as e:
                    logger.warning(f"搜索集合 {collection.name} 失败: {e}")
                    continue

            # 按分数排序并限制结果数量
            all_results.sort(key=lambda x: x.score, reverse=True)
            return all_results[:config.limit]

        except Exception as e:
            logger.error(f"多集合搜索失败: {e}")
            return []

    def _format_search_results(self, results: Dict[str, Any], score_threshold: float = 0.0) -> List[VectorSearchResult]:
        """格式化搜索结果"""
        formatted_results = []

        if not results or not results.get("ids") or not results["ids"][0]:
            return formatted_results

        num_results = len(results["ids"][0])

        for i in range(num_results):
            try:
                doc_id = results["ids"][0][i]
                content = results["documents"][0][i] if results.get("documents") and results["documents"][0] else ""
                metadata = results["metadatas"][0][i] if results.get("metadatas") and results["metadatas"][0] else {}
                distance = results["distances"][0][i] if results.get("distances") and results["distances"][0] else 0.0

                # 转换距离为相似度分数
                score = 1.0 - distance

                # 应用分数阈值
                if score < score_threshold:
                    continue

                formatted_results.append(VectorSearchResult(
                    id=doc_id,
                    content=content,
                    score=score,
                    distance=distance,
                    metadata=metadata
                ))

            except (IndexError, Exception) as e:
                logger.warning(f"处理搜索结果 {i} 时出错: {e}")
                continue

        return formatted_results

    async def delete_documents(self,
                             collection_type: VectorCollectionType,
                             document_ids: Optional[List[str]] = None,
                             identifier: Optional[str] = None,
                             is_public: bool = False,
                             owner_id: Optional[int] = None,
                             filters: Optional[Dict[str, Any]] = None) -> bool:
        """
        删除文档

        Args:
            collection_type: 集合类型
            document_ids: 要删除的文档ID列表
            identifier: 标识符
            is_public: 是否公开
            owner_id: 所有者ID
            filters: 过滤条件

        Returns:
            是否删除成功
        """
        if not self.chroma_client:
            logger.warning("ChromaDB客户端不可用")
            return False

        collection_name = self._generate_collection_name(
            collection_type, identifier, is_public, owner_id
        )

        try:
            collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            logger.warning(f"无法获取集合 {collection_name}: {e}")
            return True  # 集合不存在，认为删除成功

        try:
            if document_ids:
                # 删除指定文档
                collection.delete(ids=document_ids)
                logger.info(f"删除了 {len(document_ids)} 个文档")
            elif filters:
                # 根据条件删除
                collection.delete(where=filters)
                logger.info(f"根据条件删除文档: {filters}")
            else:
                logger.warning("未指定删除条件")
                return False

            return True

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    async def delete_file_documents(self,
                                  collection_type: VectorCollectionType,
                                  file_id: int,
                                  identifier: Optional[str] = None,
                                  is_public: bool = False,
                                  owner_id: Optional[int] = None) -> bool:
        """删除文件的所有文档"""
        return await self.delete_documents(
            collection_type=collection_type,
            identifier=identifier,
            is_public=is_public,
            owner_id=owner_id,
            filters={"file_id": str(file_id)}
        )

    async def delete_collection(self,
                              collection_type: VectorCollectionType,
                              identifier: Optional[str] = None,
                              is_public: bool = False,
                              owner_id: Optional[int] = None) -> bool:
        """
        删除整个集合

        Args:
            collection_type: 集合类型
            identifier: 标识符
            is_public: 是否公开
            owner_id: 所有者ID

        Returns:
            是否删除成功
        """
        if not self.chroma_client:
            logger.warning("ChromaDB客户端不可用")
            return False

        collection_name = self._generate_collection_name(
            collection_type, identifier, is_public, owner_id
        )

        try:
            self.chroma_client.delete_collection(name=collection_name)

            # 从缓存中移除
            if collection_name in self._collections_cache:
                del self._collections_cache[collection_name]

            logger.info(f"成功删除集合: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False

    async def get_collection_stats(self,
                                 collection_type: VectorCollectionType,
                                 identifier: Optional[str] = None,
                                 is_public: bool = False,
                                 owner_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取集合统计信息

        Args:
            collection_type: 集合类型
            identifier: 标识符
            is_public: 是否公开
            owner_id: 所有者ID

        Returns:
            统计信息
        """
        if not self.chroma_client:
            return {"error": "ChromaDB客户端不可用"}

        collection_name = self._generate_collection_name(
            collection_type, identifier, is_public, owner_id
        )

        try:
            collection = self.chroma_client.get_collection(name=collection_name)

            # 获取文档数量
            count = collection.count()

            # 获取集合元数据
            metadata = collection.metadata or {}

            stats = {
                "collection_name": collection_name,
                "collection_type": collection_type.value,
                "document_count": count,
                "metadata": metadata,
                "identifier": identifier,
                "is_public": is_public,
                "owner_id": owner_id,
                "last_updated": datetime.now().isoformat()
            }

            return stats

        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {
                "collection_name": collection_name,
                "error": str(e)
            }

    async def list_collections(self, collection_type: Optional[VectorCollectionType] = None) -> List[Dict[str, Any]]:
        """
        列出所有集合

        Args:
            collection_type: 可选的集合类型过滤

        Returns:
            集合信息列表
        """
        if not self.chroma_client:
            return []

        try:
            collections = self.chroma_client.list_collections()

            result = []
            for collection in collections:
                # 过滤集合类型
                if collection_type:
                    if not (collection.name.startswith(collection_type.value) or
                           (collection.metadata and collection.metadata.get("collection_type") == collection_type.value)):
                        continue

                collection_info = {
                    "name": collection.name,
                    "metadata": collection.metadata or {},
                    "document_count": collection.count()
                }

                result.append(collection_info)

            return result

        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []


# 单例模式
_unified_vector_service_instance = None


def get_unified_vector_service() -> UnifiedVectorService:
    """获取统一向量数据库服务单例实例"""
    global _unified_vector_service_instance

    if _unified_vector_service_instance is None:
        logger.info("正在初始化统一向量数据库服务单例实例")

        # 从环境变量或配置中获取设置
        remote_url = os.environ.get("CHROMA_URL")
        remote_port_str = os.environ.get("CHROMA_PORT", "8000")

        try:
            remote_port = int(remote_port_str)
        except ValueError:
            logger.error(f"无效的 CHROMA_PORT: '{remote_port_str}'。使用默认值 8000。")
            remote_port = 8000

        if remote_url:
            _unified_vector_service_instance = UnifiedVectorService(
                remote_url=remote_url,
                remote_port=remote_port
            )
        else:
            logger.info("未设置 CHROMA_URL，使用本地 ChromaDB 设置。")
            _unified_vector_service_instance = UnifiedVectorService()

        if _unified_vector_service_instance.chroma_client is None:
            logger.critical("统一向量数据库初始化失败。向量数据库功能不可用。")

    return _unified_vector_service_instance


# 便捷函数
async def add_knowledge_base_document(knowledge_base_id: int,
                                    file_id: int,
                                    content: str,
                                    chunk_size: int = 1024,
                                    file_extension: str = '.txt',
                                    metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """添加知识库文档的便捷函数"""
    service = get_unified_vector_service()
    return await service.add_document_chunks(
        collection_type=VectorCollectionType.KNOWLEDGE_BASE,
        content=content,
        file_id=file_id,
        identifier=str(knowledge_base_id),
        chunk_size=chunk_size,
        file_extension=file_extension,
        metadata=metadata
    )


async def search_knowledge_base(knowledge_base_id: int,
                              query: str,
                              limit: int = 10,
                              score_threshold: float = 0.3) -> List[VectorSearchResult]:
    """搜索知识库的便捷函数"""
    service = get_unified_vector_service()
    config = VectorSearchConfig(
        limit=limit,
        score_threshold=score_threshold
    )
    return await service.search(
        collection_type=VectorCollectionType.KNOWLEDGE_BASE,
        query=query,
        config=config,
        identifier=str(knowledge_base_id)
    )


async def search_multiple_knowledge_bases(knowledge_base_ids: List[int],
                                        query: str,
                                        limit: int = 10,
                                        score_threshold: float = 0.3) -> List[VectorSearchResult]:
    """跨多个知识库搜索的便捷函数"""
    service = get_unified_vector_service()
    all_results = []

    for kb_id in knowledge_base_ids:
        try:
            results = await search_knowledge_base(kb_id, query, limit, score_threshold)
            all_results.extend(results)
        except Exception as e:
            logger.error(f"搜索知识库 {kb_id} 失败: {str(e)}")

    # 按相似度排序并限制结果数量
    all_results.sort(key=lambda x: x.score, reverse=True)
    return all_results[:limit]


async def delete_knowledge_base_file(knowledge_base_id: int, file_id: int) -> bool:
    """删除知识库文件的便捷函数"""
    service = get_unified_vector_service()
    return await service.delete_file_documents(
        collection_type=VectorCollectionType.KNOWLEDGE_BASE,
        file_id=file_id,
        identifier=str(knowledge_base_id)
    )


async def add_chat_memory(user_id: str,
                        content: str,
                        metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """添加聊天记忆的便捷函数"""
    service = get_unified_vector_service()

    document = VectorDocument(
        id=f"chat_{user_id}_{datetime.now().timestamp()}",
        content=content,
        metadata=metadata or {}
    )

    return await service.add_documents(
        collection_type=VectorCollectionType.CHAT_MEMORY,
        documents=[document],
        identifier=user_id
    )


async def search_chat_memory(user_id: str,
                           query: str,
                           limit: int = 5,
                           score_threshold: float = 0.4) -> List[VectorSearchResult]:
    """搜索聊天记忆的便捷函数"""
    service = get_unified_vector_service()
    config = VectorSearchConfig(
        limit=limit,
        score_threshold=score_threshold
    )
    return await service.search(
        collection_type=VectorCollectionType.CHAT_MEMORY,
        query=query,
        config=config,
        identifier=user_id
    )


async def add_private_memory(user_id: int,
                           content: str,
                           memory_type: str = "general",
                           metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """添加私有记忆的便捷函数"""
    service = get_unified_vector_service()

    document = VectorDocument(
        id=f"private_{user_id}_{memory_type}_{datetime.now().timestamp()}",
        content=content,
        metadata=metadata or {}
    )

    return await service.add_documents(
        collection_type=VectorCollectionType.PRIVATE_MEMORY,
        documents=[document],
        identifier=memory_type,
        owner_id=user_id
    )


async def add_public_memory(content: str,
                          memory_type: str = "general",
                          metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """添加公共记忆的便捷函数"""
    service = get_unified_vector_service()

    document = VectorDocument(
        id=f"public_{memory_type}_{datetime.now().timestamp()}",
        content=content,
        metadata=metadata or {}
    )

    return await service.add_documents(
        collection_type=VectorCollectionType.PUBLIC_MEMORY,
        documents=[document],
        identifier=memory_type,
        is_public=True
    )


# 创建全局实例
unified_vector_service = get_unified_vector_service()
