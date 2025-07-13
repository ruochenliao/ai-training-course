"""
向量数据库配置和模型管理器
支持ChromaDB向量数据库和嵌入模型管理
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    CrossEncoder = None


class VectorDBConfig:
    """向量数据库配置"""
    
    # ChromaDB配置
    CHROMA_PERSIST_DIRECTORY: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        str(Path.home() / ".chromadb_intelligent_customer_service")
    )

    # 模型缓存目录配置
    MODEL_CACHE_DIR: str = os.getenv(
        "MODEL_CACHE_DIR",
        str(Path(__file__).parent.parent.parent / "models")
    )

    # 通义千问模型路径配置
    QWEN_EMBEDDING_MODEL_PATH: str = os.getenv(
        "QWEN_EMBEDDING_MODEL_PATH",
        str(Path(__file__).parent.parent.parent / "models" / "embedding" / "Qwen3-8B")
    )
    QWEN_RERANKER_MODEL_PATH: str = os.getenv(
        "QWEN_RERANKER_MODEL_PATH",
        str(Path(__file__).parent.parent.parent / "models" / "reranker" / "Qwen3-Reranker-8B")
    )

    # 嵌入模型配置 - 强制使用通义千问模型
    USE_QWEN_EMBEDDING: bool = True  # 强制启用通义千问嵌入模型
    EMBEDDING_MODEL_NAME: str = "Qwen3-8B"  # 固定使用通义千问嵌入模型
    EMBEDDING_DIMENSION: int = 4096  # 通义千问嵌入模型维度
    USE_LOCAL_EMBEDDING: bool = True  # 强制使用本地模型

    # 重排模型配置 - 强制使用通义千问重排模型
    USE_QWEN_RERANKER: bool = True  # 强制启用通义千问重排模型
    RERANKER_MODEL_NAME: str = "Qwen3-Reranker-8B"  # 固定使用通义千问重排模型
    USE_RERANKER: bool = True  # 强制启用重排功能
    USE_LOCAL_RERANKER: bool = True  # 强制使用本地重排模型
    
    # 检索配置
    DEFAULT_RETRIEVAL_LIMIT: int = int(os.getenv("DEFAULT_RETRIEVAL_LIMIT", "5"))
    RETRIEVAL_MULTIPLIER: int = int(os.getenv("RETRIEVAL_MULTIPLIER", "3"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.1"))
    
    # 性能配置
    BATCH_SIZE: int = int(os.getenv("VECTOR_BATCH_SIZE", "32"))
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
    
    # 缓存配置
    ENABLE_MODEL_CACHE: bool = os.getenv("ENABLE_MODEL_CACHE", "true").lower() == "true"
    MODEL_CACHE_SIZE: int = int(os.getenv("MODEL_CACHE_SIZE", "100"))
    
    # 集合配置
    PRIVATE_MEMORY_COLLECTION_PREFIX: str = "private_memories"
    PUBLIC_MEMORY_COLLECTION_NAME: str = "public_knowledge_base"
    CHAT_MEMORY_COLLECTION_PREFIX: str = "chat_memories"
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "chroma_persist_directory": cls.CHROMA_PERSIST_DIRECTORY,
            "model_cache_dir": cls.MODEL_CACHE_DIR,
            "qwen_embedding_model_path": cls.QWEN_EMBEDDING_MODEL_PATH,
            "qwen_reranker_model_path": cls.QWEN_RERANKER_MODEL_PATH,
            "use_qwen_embedding": cls.USE_QWEN_EMBEDDING,
            "use_qwen_reranker": cls.USE_QWEN_RERANKER,
            "embedding_model_name": cls.EMBEDDING_MODEL_NAME,
            "embedding_dimension": cls.EMBEDDING_DIMENSION,
            "use_local_embedding": cls.USE_LOCAL_EMBEDDING,
            "reranker_model_name": cls.RERANKER_MODEL_NAME,
            "use_reranker": cls.USE_RERANKER,
            "use_local_reranker": cls.USE_LOCAL_RERANKER,
            "default_retrieval_limit": cls.DEFAULT_RETRIEVAL_LIMIT,
            "retrieval_multiplier": cls.RETRIEVAL_MULTIPLIER,
            "similarity_threshold": cls.SIMILARITY_THRESHOLD,
            "batch_size": cls.BATCH_SIZE,
            "max_workers": cls.MAX_WORKERS,
            "enable_model_cache": cls.ENABLE_MODEL_CACHE,
            "model_cache_size": cls.MODEL_CACHE_SIZE,
            "private_memory_collection_prefix": cls.PRIVATE_MEMORY_COLLECTION_PREFIX,
            "public_memory_collection_name": cls.PUBLIC_MEMORY_COLLECTION_NAME,
            "chat_memory_collection_prefix": cls.CHAT_MEMORY_COLLECTION_PREFIX,
        }
    
    @classmethod
    def get_chroma_settings(cls) -> Dict[str, Any]:
        """获取ChromaDB设置"""
        return {
            "anonymized_telemetry": False,
            "allow_reset": True,
            "is_persistent": True
        }


class ModelManager:
    """模型管理器 - 管理嵌入模型和重排模型"""
    
    def __init__(self):
        self._embedding_model = None
        self._reranker_model = None
        self.config = VectorDBConfig()
        
    def get_embedding_model(self):
        """获取嵌入模型"""
        if self._embedding_model is None:
            self._embedding_model = self._load_embedding_model()
        return self._embedding_model
    
    def get_reranker_model(self):
        """获取重排模型"""
        if not self.config.USE_RERANKER:
            return None
            
        if self._reranker_model is None:
            self._reranker_model = self._load_reranker_model()
        return self._reranker_model
    
    def _load_embedding_model(self):
        """加载嵌入模型 - 必须使用通义千问模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers不可用，请安装: pip install sentence-transformers")
            raise RuntimeError("sentence-transformers依赖缺失，无法加载嵌入模型")

        # 强制使用通义千问嵌入模型，不允许回退
        return self._load_qwen_embedding_model()

    def _load_qwen_embedding_model(self):
        """加载通义千问嵌入模型 - 必须成功，不允许回退"""
        model_path = self.config.QWEN_EMBEDDING_MODEL_PATH

        # 检查模型路径是否存在
        if not Path(model_path).exists():
            error_msg = f"通义千问嵌入模型路径不存在: {model_path}"
            logger.error(error_msg)
            logger.error("请运行 'python models/quick_download.py' 下载模型")
            raise FileNotFoundError(error_msg)

        try:
            logger.info(f"加载通义千问嵌入模型: {model_path}")

            # 加载本地通义千问模型
            model = SentenceTransformer(str(model_path), device='cpu')
            logger.info(f"通义千问嵌入模型加载成功: {model_path}")
            return model

        except Exception as e:
            error_msg = f"加载通义千问嵌入模型失败: {e}"
            logger.error(error_msg)
            logger.error("请检查模型文件完整性或重新下载模型")
            raise RuntimeError(error_msg)


    
    def _load_reranker_model(self):
        """加载重排模型 - 必须使用通义千问模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers不可用，请安装: pip install sentence-transformers")
            raise RuntimeError("sentence-transformers依赖缺失，无法加载重排模型")

        # 强制使用通义千问重排模型，不允许回退
        return self._load_qwen_reranker_model()

    def _load_qwen_reranker_model(self):
        """加载通义千问重排模型 - 必须成功，不允许回退"""
        model_path = self.config.QWEN_RERANKER_MODEL_PATH

        # 检查模型路径是否存在
        if not Path(model_path).exists():
            error_msg = f"通义千问重排模型路径不存在: {model_path}"
            logger.error(error_msg)
            logger.error("请运行 'python models/quick_download.py' 下载模型")
            raise FileNotFoundError(error_msg)

        try:
            logger.info(f"加载通义千问重排模型: {model_path}")

            # 加载本地通义千问重排模型
            model = CrossEncoder(str(model_path), device='cpu')
            logger.info(f"通义千问重排模型加载成功: {model_path}")
            return model

        except Exception as e:
            error_msg = f"加载通义千问重排模型失败: {e}"
            logger.error(error_msg)
            logger.error("请检查模型文件完整性或重新下载模型")
            raise RuntimeError(error_msg)


    



# 全局配置实例
vector_db_config = VectorDBConfig()

# 全局模型管理器实例
model_manager = ModelManager()
