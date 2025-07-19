"""
向量数据库服务
基于006项目的CustomerVectorDB实现，适配SuperIntelligentCustomerService项目
"""
import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

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
from pathlib import Path
from ..utils.text_chunker import TextChunker, ChunkerConfig
from ..settings.file_types import FileProcessingMethod, get_processing_method

logger = logging.getLogger(__name__)


class VectorDBService:
    """向量数据库服务"""

    def __init__(self, remote_url: Optional[str] = None, remote_port: Optional[int] = None):
        """
        初始化向量数据库

        Args:
            remote_url: 可选的远程 ChromaDB URL
            remote_port: 可选的远程 ChromaDB 端口
        """
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB 不可用。向量数据库功能将被禁用。")
            self.chroma_client = None
            return

        # 使用默认嵌入函数（避免网络连接问题）
        try:
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            logger.info("正在使用 DefaultEmbeddingFunction。")
        except Exception as e:
            logger.error(f"初始化 DefaultEmbeddingFunction 失败: {e}")
            self.embedding_function = None

        # 初始化 ChromaDB 客户端
        if remote_url and remote_port:
            # 使用远程 ChromaDB
            try:
                self.chroma_client = chromadb.HttpClient(
                    host=remote_url,
                    port=remote_port,
                    settings=Settings(anonymized_telemetry=False)
                )
                self.chroma_client.heartbeat()
                logger.info(f"成功连接到远程 ChromaDB 于 {remote_url}:{remote_port}")
            except Exception as e:
                logger.error(f"连接到远程 ChromaDB 失败 {remote_url}:{remote_port}。错误: {e}")
                self.chroma_client = None
        else:
            # 使用本地 ChromaDB
            # 获取项目根目录
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent  # 从 app/services/vector_db.py 到项目根目录
            db_path = project_root / "vector_db_data"
            db_path.mkdir(parents=True, exist_ok=True)

            try:
                self.chroma_client = chromadb.PersistentClient(
                    path=str(db_path),
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info(f"正在使用本地 ChromaDB 于 {db_path}")
            except Exception as e:
                logger.error(f"初始化本地 ChromaDB 失败于 {db_path}。错误: {e}")
                self.chroma_client = None

    def _get_collection_name(self, knowledge_type: str, is_public: bool, owner_id: Optional[int]) -> str:
        """生成集合名称"""
        if not knowledge_type:
            raise ValueError("需要知识类型来确定集合名称。")

        if is_public:
            collection_name = f"{knowledge_type}_public_memory"
        else:
            if owner_id is None:
                raise ValueError("私有集合需要所有者 ID。")
            collection_name = f"{knowledge_type}_{owner_id}"

        # 清理集合名称
        collection_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', collection_name)
        collection_name = collection_name.strip('.')
        
        if not (3 <= len(collection_name) <= 63):
            raise ValueError(f"生成的集合名称 '{collection_name}' 无效。长度必须在 3 到 63 个字符之间。")
        
        if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', collection_name):
            raise ValueError(f"生成的集合名称 '{collection_name}' 类似于 IP 地址，这是无效的。")
        
        if collection_name.startswith(('_', '-')) or collection_name.endswith(('_', '-')):
            collection_name = f"col_{collection_name.strip('_-')}"[:63]

        return collection_name

    def get_or_create_collection(self, knowledge_base_id: int, knowledge_type: str, 
                               is_public: bool = False, owner_id: Optional[int] = None) -> Optional[Any]:
        """获取或创建 ChromaDB 集合"""
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法获取或创建集合。")
            return None

        try:
            collection_name = self._get_collection_name(knowledge_type, is_public, owner_id)
        except ValueError as ve:
            logger.error(f"生成有效的集合名称失败: {ve}")
            return None

        metadata_dict = {
            "knowledge_base_id": str(knowledge_base_id),
            "knowledge_type": knowledge_type,
            "is_public": str(is_public).lower(),
        }
        if owner_id is not None:
            metadata_dict["owner_id"] = str(owner_id)

        try:
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata=metadata_dict
            )
            logger.info(f"成功获取或创建集合: '{collection_name}'")
            return collection
        except Exception as e:
            logger.error(f"获取或创建 ChromaDB 集合 '{collection_name}' 失败: {e}")
            return None

    async def add_document(self, knowledge_base_id: int, file_id: int, content: str,
                          knowledge_type: str, is_public: bool = False,
                          owner_id: Optional[int] = None, chunk_size: int = 1024,
                          file_extension: str = '.txt') -> List[str]:
        """
        将文档添加到向量数据库
        
        Args:
            knowledge_base_id: 知识库ID
            file_id: 文件ID
            content: 文档内容
            knowledge_type: 知识库类型
            is_public: 是否公开
            owner_id: 所有者ID
            chunk_size: 分块大小
            
        Returns:
            添加的块ID列表
        """
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法添加文档。")
            return []

        # 获取集合
        collection = self.get_or_create_collection(
            knowledge_base_id=knowledge_base_id,
            knowledge_type=knowledge_type,
            is_public=is_public,
            owner_id=owner_id
        )

        if collection is None:
            logger.error("无法获取或创建集合。无法添加文档。")
            return []

        # 智能文本分块
        chunks = self._chunk_text(content, chunk_size, file_extension)
        
        if not chunks:
            logger.info(f"文件 {file_id} 未生成任何块。无需添加。")
            return []

        # 准备数据
        chunk_ids = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"file_{file_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            
            metadata = {
                "file_id": str(file_id),
                "knowledge_base_id": str(knowledge_base_id),
                "knowledge_type": knowledge_type,
                "is_public": is_public,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            
            if not is_public and owner_id is not None:
                metadata["owner_id"] = str(owner_id)

            metadatas.append(metadata)

        # 添加到集合
        try:
            collection.add(
                ids=chunk_ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"成功将文件 {file_id} 的 {len(chunks)} 个块添加到集合 '{collection.name}'")
            return chunk_ids
        except Exception as e:
            logger.error(f"将块添加到 ChromaDB 集合 '{collection.name}' 失败: {e}")
            return []

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

    async def search(self, knowledge_base_id: int, query: str, limit: int = 5,
                    knowledge_type: str = None, is_public: bool = None, 
                    owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """在向量数据库中搜索相关内容"""
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法搜索文档。")
            return []

        try:
            collection_name = self._get_collection_name(knowledge_type, is_public, owner_id)
        except ValueError as ve:
            logger.error(f"确定搜索集合名称失败: {ve}")
            return []

        try:
            collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            logger.warning(f"无法获取用于搜索的集合 '{collection_name}': {e}")
            return []

        try:
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                include=['metadatas', 'documents', 'distances']
            )
        except Exception as e:
            logger.error(f"ChromaDB 查询集合 '{collection.name}' 失败: {e}")
            return []

        # 格式化结果
        formatted_results = []
        if results and results.get("ids") and results["ids"] and results["ids"][0]:
            num_results = len(results["ids"][0])
            for i in range(num_results):
                try:
                    doc_id = results["ids"][0][i]
                    doc_content = results["documents"][0][i] if results.get("documents") and results["documents"][0] and len(results["documents"][0]) > i else None
                    metadata = results["metadatas"][0][i] if results.get("metadatas") and results["metadatas"][0] and len(results["metadatas"][0]) > i else {}
                    distance = results["distances"][0][i] if results.get("distances") and results["distances"][0] and len(results["distances"][0]) > i else None

                    formatted_results.append({
                        "id": doc_id,
                        "document": doc_content,
                        "metadata": metadata,
                        "distance": distance
                    })
                except (IndexError, Exception) as e:
                    logger.warning(f"处理搜索结果 {i} 时出错: {e}")

        return formatted_results

    async def delete_file(self, knowledge_base_id: int, file_id: int, knowledge_type: str,
                         is_public: bool = False, owner_id: Optional[int] = None) -> bool:
        """从向量数据库中删除文件"""
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法删除文件。")
            return False

        try:
            collection_name = self._get_collection_name(knowledge_type, is_public, owner_id)
        except ValueError as ve:
            logger.error(f"无法确定文件删除的集合名称: {ve}")
            return False

        try:
            collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            logger.warning(f"无法获取用于文件删除的集合 '{collection_name}': {e}")
            return True

        try:
            collection.delete(where={"file_id": str(file_id)})
            logger.info(f"尝试从集合 '{collection.name}' 中删除文件 {file_id} 的块。")
            return True
        except Exception as e:
            logger.error(f"从集合 '{collection.name}' 中删除文件 {file_id} 的块失败: {e}")
            return False

    async def delete_knowledge_base(self, knowledge_base_id: int, knowledge_type: str,
                                  is_public: bool = False, owner_id: Optional[int] = None) -> bool:
        """从向量数据库中删除知识库"""
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法删除知识库条目。")
            return False

        try:
            collection_name = self._get_collection_name(knowledge_type, is_public, owner_id)
        except ValueError as ve:
            logger.error(f"无法确定 KB 删除的集合名称: {ve}")
            return False

        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"找到用于删除 KB {knowledge_base_id} 文档的集合 '{collection_name}'。")
        except Exception as e:
            logger.warning(f"无法获取用于 KB {knowledge_base_id} 删除的集合 '{collection_name}'。它可能不存在: {e}")
            return True

        try:
            collection.delete(where={"knowledge_base_id": str(knowledge_base_id)})
            logger.info(f"尝试从集合 '{collection.name}' 中删除知识库 {knowledge_base_id} 的文档。")
            return True
        except Exception as e:
            logger.error(f"从集合 '{collection.name}' 中删除 KB {knowledge_base_id} 的文档失败: {e}")
            return False


# 单例模式
_vector_db_instance = None

def get_vector_db():
    """获取向量数据库单例实例"""
    global _vector_db_instance
    if _vector_db_instance is None:
        logger.info("正在初始化向量数据库单例实例")
        
        # 从环境变量或配置中获取设置
        remote_url = os.environ.get("CHROMA_URL")
        remote_port_str = os.environ.get("CHROMA_PORT", "8000")
        
        try:
            remote_port = int(remote_port_str)
        except ValueError:
            logger.error(f"无效的 CHROMA_PORT: '{remote_port_str}'。使用默认值 8000。")
            remote_port = 8000

        if remote_url:
            _vector_db_instance = VectorDBService(remote_url=remote_url, remote_port=remote_port)
        else:
            logger.info("未设置 CHROMA_URL，使用本地 ChromaDB 设置。")
            _vector_db_instance = VectorDBService()

        if _vector_db_instance.chroma_client is None:
            logger.critical("向量数据库初始化失败。向量数据库功能不可用。")

    return _vector_db_instance

# 创建全局实例
vector_db = get_vector_db()
