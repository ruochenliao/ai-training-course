import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from chromadb.utils.embedding_functions.sentence_transformer_embedding_function import \
    SentenceTransformerEmbeddingFunction

import re # 导入正则表达式库，用于未来潜在的表格处理
from a_app.settings.config import settings
from a_app.utils.text_chunker import TextChunker, ChunkerConfig, LANGCHAIN_AVAILABLE
from a_app.settings.file_types import FileProcessingMethod, get_processing_method, is_supported_extension
from a_app.utils.text_chunker import get_byte_length

# 尝试导入 chromadb
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("未找到 ChromaDB 库。向量数据库功能将被禁用。")

import logging # 使用标准日志库进行演示
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 用于演示的虚拟 KnowledgeType
class KnowledgeType:
    CUSTOMER_SERVICE = "customer_service" # 定义客户服务知识类型常量


class CustomerVectorDB:
    """客户知识库的向量数据库"""

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

        # 使用 DefaultEmbeddingFunction 或指定您自己的 SentenceTransformer 模型
        # self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        # 示例：使用特定的 Sentence Transformer 模型 (需要 pip install sentence-transformers)
        try:
             # 尝试使用 all-MiniLM-L6-v2 模型初始化句子转换器嵌入函数
             # self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
             # logger.info("正在使用 SentenceTransformerEmbeddingFunction (all-MiniLM-L6-v2)。")

            self.embedding_function = SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-zh-v1.5")
            logger.info("正在使用 SentenceTransformerEmbeddingFunction (bge-small-zh-v1.5)。")
        except ImportError:
             logger.warning("未找到 sentence-transformers 库。回退到 DefaultEmbeddingFunction。")
             # 如果导入失败，回退到默认嵌入函数
             self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        except Exception as e:
             logger.error(f"初始化 SentenceTransformerEmbeddingFunction 失败: {e}。回退到 DefaultEmbeddingFunction。")
             # 如果出现其他异常，也回退到默认嵌入函数
             self.embedding_function = embedding_functions.DefaultEmbeddingFunction()


        # 初始化 ChromaDB 客户端（本地或远程）
        if remote_url and remote_port:
            # 使用远程 ChromaDB
            try:
                self.chroma_client = chromadb.HttpClient(
                    host=remote_url,
                    port=remote_port,
                    settings=Settings(anonymized_telemetry=False) # 禁用匿名遥测
                )
                # 验证连接（可选但推荐）
                self.chroma_client.heartbeat() # 发送心跳检查连接状态
                logger.info(f"成功连接到远程 ChromaDB 于 {remote_url}:{remote_port}")
            except Exception as e:
                logger.error(f"连接到远程 ChromaDB 失败 {remote_url}:{remote_port}。错误: {e}")
                self.chroma_client = None # 如果连接失败，确保客户端为 None
        else:
            # 使用本地 ChromaDB
            db_path = Path(settings.BASE_DIR) / "vector_db_data" # 数据库存储路径，稍微修改了文件夹名称
            db_path.mkdir(parents=True, exist_ok=True) # 创建数据库路径，如果父目录不存在也一并创建

            try:
                self.chroma_client = chromadb.PersistentClient(
                    path=str(db_path), # 指定本地存储路径
                    settings=Settings(anonymized_telemetry=False) # 禁用匿名遥测
                )
                logger.info(f"正在使用本地 ChromaDB 于 {db_path}")
            except Exception as e:
                logger.error(f"初始化本地 ChromaDB 失败于 {db_path}。错误: {e}")
                self.chroma_client = None # 初始化失败则将客户端设为 None

    def _get_collection_name(self, knowledge_type: str, is_public: bool, owner_id: Optional[int]) -> str:
         """辅助函数：用于一致地生成集合（Collection）名称。"""
         if not knowledge_type:
              # 知识类型是生成名称的必要条件
              raise ValueError("需要知识类型（Knowledge type）来确定集合名称。")

         if is_public:
            # 公共集合名称格式: {knowledge_type}_public_memory
            collection_name = f"{knowledge_type}_public_memory"
         else:
            # 私有集合名称格式: {knowledge_type}_private_{owner_id}
            if owner_id is None:
                # owner_id 对于私有集合至关重要
                raise ValueError("私有集合需要所有者 ID（Owner ID）。")
            collection_name = f"{knowledge_type}_{owner_id}"

         # 对集合名称进行基本清理（ChromaDB 有命名限制）
         # 替换无效字符（允许字母数字、下划线、连字符、句点）
         collection_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', collection_name)
         # 确保名称不以句点开头或结尾
         collection_name = collection_name.strip('.')
         # 确保持续时间约束（例如，3 到 63 个字符）
         if not (3 <= len(collection_name) <= 63):
              raise ValueError(f"生成的集合名称 '{collection_name}' 无效。长度必须在 3 到 63 个字符之间。")
         # 确保名称看起来不像 IP 地址
         if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', collection_name):
              raise ValueError(f"生成的集合名称 '{collection_name}' 类似于 IP 地址，这是无效的。")
         # 在可能的剥离后，再次确保它不以无效字符开头/结尾
         if collection_name.startswith(('_', '-')) or collection_name.endswith(('_', '-')):
             # 如果需要，添加前缀/后缀，简单示例：
             collection_name = f"col_{collection_name.strip('_-')}"[:63] # 重新检查长度


         return collection_name

    def get_or_create_collection(self, knowledge_base_id: int, knowledge_type: str = KnowledgeType.CUSTOMER_SERVICE, is_public: bool = False, owner_id: Optional[int] = None) -> Optional[Any]:
        """获取或创建带有验证的 ChromaDB 集合。"""
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法获取或创建集合。")
            return None

        try:
            # 使用辅助函数生成集合名称
            collection_name = self._get_collection_name(knowledge_type, is_public, owner_id)
        except ValueError as ve:
            logger.error(f"生成有效的集合名称失败: {ve}")
            return None

        # 确保元数据值适用于 ChromaDB（字符串、数字、布尔值）
        # 为了元数据安全，通常将 ID 和布尔值转换为字符串。
        metadata_dict = {
            "knowledge_base_id": str(knowledge_base_id), # 将知识库 ID 存储为字符串
            "knowledge_type": knowledge_type,            # 知识类型
            "is_public": str(is_public).lower(),         # 将布尔值转为 'true'/'false' 字符串
        }
        if owner_id is not None:
             metadata_dict["owner_id"] = str(owner_id)   # 将所有者 ID 存储为字符串

        try:
            # 获取或创建集合
            collection = self.chroma_client.get_or_create_collection(
                name=collection_name,                    # 集合名称
                embedding_function=self.embedding_function, # 指定嵌入函数
                metadata=metadata_dict                  # 传递验证过的元数据用于创建
            )
            logger.info(f"成功获取或创建集合: '{collection_name}'")
            return collection
        except Exception as e:
            # 捕获在创建/获取过程中可能出现的 ChromaDB 错误
            logger.error(f"获取或创建 ChromaDB 集合 '{collection_name}' 失败: {e}")
            return None

    async def add_document(self, knowledge_base_id: int, file_id: int, markdown_text: str, knowledge_type: str = None, is_public: bool = None, owner_id: int = None, chunk_index: int = None, file_extension: str = None, language: str = 'auto') -> List[str]:
        """
        使用优化的分块方法将文档添加到向量数据库。
        """
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法添加文档。")
            return []

        # --- 元数据获取逻辑（保持原样，但要确保其健壮性）---
        # 这部分很大程度上取决于您的应用程序结构（例如，使用 ORM）
        # 假设已正确获取必要的元数据（knowledge_type, is_public, owner_id）。
        # 如果获取失败，应引发错误或返回 []，因为添加到错误的集合中是不好的。
        # 示例占位符 - 用您实际的获取逻辑替换：
        if knowledge_type is None or is_public is None or (not is_public and owner_id is None):
             try:
                 # 占位符：从您的主数据库（例如 SQL）获取
                 # from a_app.models.knowledge import KnowledgeBase # 您的实际导入
                 # kb = await KnowledgeBase.get(id=knowledge_base_id)
                 # knowledge_type = knowledge_type or kb.knowledge_type
                 # is_public = is_public if is_public is not None else kb.is_public
                 # if not is_public:
                 #     owner_id = owner_id or kb.owner_id
                 # --- 用于演示的虚拟值 ---
                 logger.warning(f"未完全提供 KB {knowledge_base_id} 的元数据。使用虚拟值（私有）。")
                 knowledge_type = knowledge_type or KnowledgeType.CUSTOMER_SERVICE
                 is_public = is_public if is_public is not None else False # 默认为私有
                 if not is_public:
                     owner_id = owner_id or 999 # 虚拟所有者 ID
                 # --- 结束虚拟值 ---

             except Exception as e:
                 logger.error(f"检索 ID 为 {knowledge_base_id} 的 KnowledgeBase 信息失败: {e}")
                 # 如果无法可靠地确定元数据，则停止处理
                 # raise ValueError(f"未能检索知识库 {knowledge_base_id} 所需的元数据") from e
                 return [] # 返回空列表比使用错误的元数据继续处理更安全

        # --- 获取集合 ---
        collection = self.get_or_create_collection(
            knowledge_base_id=knowledge_base_id, # 传递 KB ID 用于元数据，虽然这里不直接用于集合名称
            knowledge_type=knowledge_type,
            is_public=is_public,
            owner_id=owner_id # 如果 is_public 为 True，则 owner_id 为 None
        )

        if collection is None:
            logger.error("无法获取或创建集合。无法添加文档。")
            return []

        # === 使用优化的分块方法 ===
        # 考虑使 max_chunk_size 可配置
        max_chunk_bytes = 1024 # 示例大小（字节）

        # 如果没有提供文件扩展名，尝试从元数据中推断
        if file_extension is None:
            try:
                # 尝试从数据库中获取文件信息
                # 这里只是一个占位符，实际实现可能需要使用 ORM 或其他方法
                logger.warning(f"没有提供文件扩展名。将使用默认的 Markdown 分块。")
                file_extension = ".md"  # 默认使用 Markdown
            except Exception as e:
                logger.error(f"获取文件扩展名失败: {e}")
                file_extension = ".md"  # 默认使用 Markdown

        # 确定处理方法
        try:
            processing_method = get_processing_method(file_extension)
        except ValueError:
            logger.warning(f"不支持的文件类型: {file_extension}。使用默认的 Markdown 分块。")
            processing_method = FileProcessingMethod.MARKDOWN  # 默认使用 Markdown

        # 根据文件类型选择合适的分块方法
        if processing_method == FileProcessingMethod.MARKDOWN:
            # 使用 Markdown 感知分块
            chunker_config = ChunkerConfig(
                chunk_size_bytes=max_chunk_bytes,
                overlap_ratio=0.1,  # 10% 的重叠
                respect_special_blocks=True,  # 保护代码块、表格等
                preserve_markdown_structure=True,  # 保持 Markdown 结构
                language=language  # 语言设置
            )
            chunks = TextChunker.chunk_markdown(markdown_text, config=chunker_config)
            logger.info(f"使用 Markdown 感知分块将文件 {file_id} 分割成 {len(chunks)} 个块")
        elif processing_method == FileProcessingMethod.TEXT:
            # 使用文本分块
            chunker_config = ChunkerConfig(
                chunk_size_bytes=max_chunk_bytes,
                overlap_ratio=0.1,  # 10% 的重叠
                respect_special_blocks=False,  # 纯文本不需要特殊块处理
                preserve_markdown_structure=False,  # 纯文本不需要 Markdown 结构
                language=language  # 语言设置
            )
            chunks = TextChunker.chunk_text(markdown_text, config=chunker_config)
            logger.info(f"使用文本分块将文件 {file_id} 分割成 {len(chunks)} 个块")
        else:  # PDF_CONVERTER 类型或其他
            # 对于 PDF 和其他复杂文档，使用 Markdown 分块
            chunker_config = ChunkerConfig(
                chunk_size_bytes=max_chunk_bytes,
                overlap_ratio=0.1,  # 10% 的重叠
                respect_special_blocks=True,  # 保护代码块、表格等
                preserve_markdown_structure=True,  # 保持 Markdown 结构
                language=language  # 语言设置
            )
            chunks = TextChunker.chunk_markdown(markdown_text, config=chunker_config)
            logger.info(f"使用默认分块将文件 {file_id} 分割成 {len(chunks)} 个块")
        # ====================================

        if not chunks:
             logger.info(f"文件 {file_id} 未生成任何块。无需添加。")
             return []

        # --- 准备用于 ChromaDB 的数据 ---
        chunk_ids = [] # 块 ID 列表
        metadatas = [] # 元数据列表
        documents = [] # 文档内容列表
        for i, chunk in enumerate(chunks):
            # 如果提供了 chunk_index，则使用它来生成 ID
            # 这允许在预先分块的情况下保持一致的 ID
            current_index = chunk_index + i if chunk_index is not None else i
            chunk_id = f"file_{file_id}_chunk_{current_index}" # 每个块的唯一 ID
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            # 准备元数据 - 确保值是 ChromaDB 兼容的类型（str, int, float, bool）
            metadata = {
                "file_id": str(file_id),                 # 将文件 ID 存储为字符串
                "knowledge_base_id": str(knowledge_base_id), # 将 KB ID 存储为字符串
                "knowledge_type": knowledge_type,       # 知识类型
                "is_public": is_public,                 # 存储为布尔值
                "chunk_index": current_index,           # 块索引
                "total_chunks": len(chunks),            # 总块数
                # 添加原始文档长度？可能有用。
                "source_doc_byte_length": get_byte_length(markdown_text), # 源文档字节长度
                "chunk_byte_length": get_byte_length(chunk) # 当前块字节长度
            }
            # 仅为私有知识库添加 owner_id
            if not is_public and owner_id is not None:
                metadata["owner_id"] = str(owner_id) # 将所有者 ID 存储为字符串

            metadatas.append(metadata)


        # --- 将块添加到集合 ---
        try:
            # 如果块数量非常大，为了性能考虑可以分批添加
            # 为简单起见，此处一次性添加所有块。
            collection.add(
                ids=chunk_ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"成功将文件 {file_id} 的 {len(chunks)} 个块添加到集合 '{collection.name}'")
        except Exception as e:
            logger.error(f"将块添加到 ChromaDB 集合 '{collection.name}' 失败: {e}")
            # 如果适用，考虑更具体的错误处理或重试逻辑
            return [] # 返回空列表表示失败


        return chunk_ids # 返回已添加块的 ID

    async def search(self, knowledge_base_id: int, query: str, limit: int = 5, knowledge_type: str = None, is_public: bool = None, owner_id: int = None, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """在向量数据库中搜索相关的块。"""
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法搜索文档。")
            return []

        # --- 元数据获取逻辑（类似于 add_document）---
        # 获取或确保所需的元数据（knowledge_type, is_public, owner_id）可用
        # 示例占位符：
        if knowledge_type is None or is_public is None or (not is_public and owner_id is None):
             try:
                 # 占位符获取
                 logger.warning(f"未完全提供在 KB {knowledge_base_id} 中搜索所需的元数据。使用虚拟值（私有）。")
                 knowledge_type = knowledge_type or KnowledgeType.CUSTOMER_SERVICE
                 is_public = is_public if is_public is not None else False # 默认为私有
                 if not is_public:
                     owner_id = owner_id or 999 # 虚拟所有者 ID
             except Exception as e:
                 logger.error(f"在搜索期间检索 ID 为 {knowledge_base_id} 的 KnowledgeBase 信息失败: {e}")
                 return []

        # --- 获取集合名称 ---
        try:
            collection_name = self._get_collection_name(knowledge_type, is_public, owner_id)
        except ValueError as ve:
             logger.error(f"确定搜索集合名称失败: {ve}")
             return []

        # --- 获取集合（对于搜索，它应该存在）---
        try:
             collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
             # 如果还没有添加任何文档，集合可能不存在
             logger.warning(f"无法获取用于搜索的集合 '{collection_name}' (它可能不存在或发生错误): {e}")
             return []

        # --- 构建 Where 过滤器（可选）---
        # 将基本过滤器与用户提供的过滤器结合起来
        where_filter = {}
        # 示例：如果您的集合结构允许多个 KB（在当前命名方式下不太可能），则始终按特定的知识库 ID 进行过滤
        # where_filter["knowledge_base_id"] = str(knowledge_base_id) # 如果需要，按 KB ID 过滤

        if filter_metadata:
            # 确保过滤器键与元数据键匹配，并且值是正确的类型（str, int, float, bool）
            # 示例基本合并（小心覆盖）：
             where_filter.update(filter_metadata)
             # 如果需要，在此处添加对 filter_metadata 内容的验证

        # --- 搜索集合 ---
        try:
            results = collection.query(
                query_texts=[query],                      # 查询文本列表
                n_results=limit,                         # 返回结果数量
                where=where_filter if where_filter else None, # 如果过滤器不为空则应用
                include=['metadatas', 'documents', 'distances'] # 明确包含所需字段
            )
        except Exception as e:
            logger.error(f"ChromaDB 查询集合 '{collection.name}' 失败: {e}")
            return []


        # --- 格式化结果 ---
        formatted_results = []
        # 检查 ChromaDB 结果结构（即使对于单个查询，它也为每个查询返回列表）
        if results and results.get("ids") and results["ids"] and results["ids"][0]:
             num_results = len(results["ids"][0]) # 获取结果数量
             for i in range(num_results):
                try:
                    doc_id = results["ids"][0][i]
                    # 在访问之前检查其他列表是否具有相同的长度
                    doc_content = results["documents"][0][i] if results.get("documents") and results["documents"][0] and len(results["documents"][0]) > i else None
                    metadata = results["metadatas"][0][i] if results.get("metadatas") and results["metadatas"][0] and len(results["metadatas"][0]) > i else {}
                    distance = results["distances"][0][i] if results.get("distances") and results["distances"][0] and len(results["distances"][0]) > i else None

                    formatted_results.append({
                        "id": doc_id,           # 块 ID
                        "document": doc_content,# 块内容
                        "metadata": metadata,   # 元数据
                        "distance": distance    # 距离（通常越低越相似）
                    })
                except IndexError:
                    logger.warning(f"处理查询 '{query}' 的结果 {i} 时出现索引错误。结果结构可能不一致。")
                except Exception as e:
                    logger.warning(f"格式化结果 {i} (ID: {doc_id}) 出错: {e}")
        else:
            logger.info(f"在集合 '{collection_name}' 中未找到查询 '{query}' 的结果。")


        return formatted_results

    async def delete_file(self, knowledge_base_id: int, file_id: int, knowledge_type: str = None, is_public: bool = None, owner_id: int = None) -> bool:
        """从适当的集合中删除与特定 file_id 关联的所有块。"""
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法删除文件。")
            return False

        # --- 元数据获取逻辑 ---
        # 获取或确保所需的元数据（knowledge_type, is_public, owner_id）可用
        # 示例占位符：
        if knowledge_type is None or is_public is None or (not is_public and owner_id is None):
             try:
                 # 占位符获取
                 logger.warning(f"未完全提供在 KB {knowledge_base_id} 中删除文件所需的元数据。使用虚拟值（私有）。")
                 knowledge_type = knowledge_type or KnowledgeType.CUSTOMER_SERVICE
                 is_public = is_public if is_public is not None else False # 默认为私有
                 if not is_public:
                     owner_id = owner_id or 999 # 虚拟所有者 ID
             except Exception as e:
                 logger.error(f"在文件删除期间检索 ID 为 {knowledge_base_id} 的 KnowledgeBase 信息失败: {e}")
                 return False


        # --- 获取集合名称 ---
        try:
            collection_name = self._get_collection_name(knowledge_type, is_public, owner_id)
        except ValueError as ve:
             logger.error(f"无法确定文件删除的集合名称: {ve}")
             return False

        # --- 获取集合（必须存在才能从中删除）---
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            logger.warning(f"无法获取用于文件删除的集合 '{collection_name}' (它可能不存在或发生错误): {e}")
            # 如果集合不存在，则文件反正不在那里
            return True # 或 False，取决于您是否将“未找到”视为失败


        # --- 按 file_id 元数据删除 ---
        try:
            # 我们将 file_id 作为字符串存储在元数据中，因此使用字符串进行过滤
            collection.delete(
                where={"file_id": str(file_id)}
            )
            logger.info(f"尝试从集合 '{collection.name}' 中删除文件 {file_id} 的块。")
            # 注意：如果找不到匹配的文档，ChromaDB delete 不会引发错误。
            return True # 表示已尝试删除
        except Exception as e:
             logger.error(f"从集合 '{collection.name}' 中删除文件 {file_id} 的块失败: {e}")
             return False

    async def delete_knowledge_base(self, knowledge_base_id: int, knowledge_type: str = None, is_public: bool = None, owner_id: int = None) -> bool:
        """从适当的集合中删除与特定 knowledge_base_id 关联的所有块。"""
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法删除知识库条目。")
            return False

        # --- 元数据获取逻辑 ---
        # 获取或确保所需的元数据（knowledge_type, is_public, owner_id）可用
        # 此处要小心：如果首先从主数据库中删除了 KB，您可能需要完全依赖传递的参数。
        # 示例占位符：
        if knowledge_type is None or is_public is None or (not is_public and owner_id is None):
             try:
                 # 占位符获取（处理潜在的“未找到”，如果主数据库条目已删除）
                 logger.warning(f"未完全提供 KB 删除 {knowledge_base_id} 所需的元数据。使用虚拟值（私有）。")
                 knowledge_type = knowledge_type or KnowledgeType.CUSTOMER_SERVICE
                 is_public = is_public if is_public is not None else False # 默认为私有
                 if not is_public:
                     owner_id = owner_id or 999 # 虚拟所有者 ID
             except Exception as e:
                 logger.error(f"在 KB 删除期间检索 ID 为 {knowledge_base_id} 的 KnowledgeBase 信息出错: {e}")
                 # 如果元数据至关重要且无法找到/推断，则删除失败
                 if knowledge_type is None or is_public is None or (not is_public and owner_id is None):
                     logger.error(f"无法删除 KB {knowledge_base_id} 向量数据：信息不足。")
                     return False


        # --- 确定集合名称 ---
        try:
            collection_name = self._get_collection_name(knowledge_type, is_public, owner_id)
        except ValueError as ve:
             logger.error(f"无法确定 KB 删除的集合名称: {ve}")
             return False

        # --- 获取集合 ---
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"找到用于删除 KB {knowledge_base_id} 文档的集合 '{collection_name}'。")
        except Exception as e:
             logger.warning(f"无法获取用于 KB {knowledge_base_id} 删除的集合 '{collection_name}'。它可能不存在: {e}")
             # 如果集合不存在，数据已经消失了。将此视为成功。
             return True


        # --- 按 knowledge_base_id 元数据删除 ---
        try:
            # 我们将 knowledge_base_id 作为字符串存储在元数据中
            collection.delete(
                where={"knowledge_base_id": str(knowledge_base_id)}
            )
            logger.info(f"尝试从集合 '{collection.name}' 中删除知识库 {knowledge_base_id} 的文档。")
            return True # 已尝试删除
        except Exception as e:
             logger.error(f"从集合 '{collection.name}' 中删除 KB {knowledge_base_id} 的文档失败: {e}")
             return False

    # 对此要非常小心，尤其是对于公共集合。
    def delete_entire_collection(self, knowledge_type: str, is_public: bool, owner_id: Optional[int]) -> bool:
        """删除整个 ChromaDB 集合。请极其谨慎使用。"""
        if not CHROMADB_AVAILABLE or self.chroma_client is None:
            logger.warning("ChromaDB 客户端不可用。无法删除集合。")
            return False

        if is_public:
             logger.error("尝试删除公共集合。为安全起见，此操作被阻止。")
             # 您可能需要特定的管理员权限来覆盖此设置。
             return False

        try:
            collection_name = self._get_collection_name(knowledge_type, is_public, owner_id)
            logger.warning(f"正在尝试删除整个集合: '{collection_name}'")
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"成功删除集合: '{collection_name}'")
            return True
        except ValueError as ve:
             logger.error(f"无法确定完全删除的集合名称: {ve}")
             return False
        except Exception as e:
            logger.error(f"删除集合 '{collection_name}' 失败: {e}")
            # 如果集合不存在，也可能失败，这在删除上下文中可以视为成功
            # 如果需要，检查特定的 ChromaDB 异常类型。
            return False # 暂时假设失败

# --- 单例模式 ---
_customer_vector_db_instance = None # 全局变量存储单例实例

def get_customer_vector_db():
    """获取 CustomerVectorDB 的单例实例"""
    global _customer_vector_db_instance
    if _customer_vector_db_instance is None:
        logger.info("正在初始化 CustomerVectorDB 单例实例")
        # 理想情况下，从设置或环境变量加载配置
        remote_url = os.environ.get("CHROMA_URL", "155.138.220.75") # 示例默认 URL
        remote_port_str = os.environ.get("CHROMA_PORT", "8000")     # 示例默认端口（字符串）
        try:
            remote_port = int(remote_port_str) # 尝试转换为整数
        except ValueError:
            logger.error(f"无效的 CHROMA_PORT: '{remote_port_str}'。使用默认值 8000。")
            remote_port = 8000 # 回退到默认端口

        # 根据配置决定是使用远程还是本地
        # 示例：如果设置了 CHROMA_URL，则使用远程，否则使用本地
        if "CHROMA_URL" in os.environ:
             _customer_vector_db_instance = CustomerVectorDB(remote_url=remote_url, remote_port=remote_port)
        else:
             logger.info("未设置 CHROMA_URL，使用本地 ChromaDB 设置。")
             _customer_vector_db_instance = CustomerVectorDB() # 使用本地默认设置

        # 检查初始化是否失败
        if _customer_vector_db_instance.chroma_client is None:
             logger.critical("CustomerVectorDB 初始化失败。向量数据库功能不可用。")
             # 根据您的应用程序，您可能想要引发错误或处理此状态
             # _customer_vector_db_instance = None # 如果失败，是否重置实例？

    return _customer_vector_db_instance

# 创建单例实例（在异步/多线程应用中考虑其影响）
customer_vector_db = get_customer_vector_db()

# --- 用法示例（用于测试）---
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG) # 测试时使用更详细的日志记录

    # --- 测试本地数据库 ---
    print("\n--- 测试本地数据库 ---")
    local_db = CustomerVectorDB() # 初始化本地数据库
    if local_db.chroma_client:
        # 示例 Markdown 文本
        markdown_example = """
# 文档标题

这是第一段。它介绍了主要主题。

## 第一节：引言

本节提供背景信息。
它包含多个句子。

这是一个列表：
* 项目 1
* 项目 2
* 项目 3

第一节中的另一段。

## 第二节：表格和代码

本节演示表格处理。

| 表头 1 | 表头 2 | 表头 3 |
|----------|----------|----------|
| 第 1 行，第 1 列 | 第 1 行，第 2 列 | 第 1 行，第 3 列 |
| 第 2 行，第 1 列 | 第 2 行，第 2 列 | 第 2 行，第 3 列 |
| 第 3 行，第 1 列 | 第 3 行，第 2 列 | 第 3 行，第 3 列 |
| 第 4 行，第 1 列 | 第 4 行，第 2 列 | 第 4 行，第 3 列 |
| 第 5 行，第 1 列 | 第 5 行，第 2 列 | 第 5 行，第 3 列 |

这个表格相对较小。

```python
def hello(name):
  print(f"你好, {name}!")

hello("世界")
        """