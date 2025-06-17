"""
向量数据库配置
"""
import os
from typing import Dict, Any
from pathlib import Path


class VectorDBConfig:
    """向量数据库配置"""
    
    # ChromaDB配置
    CHROMA_PERSIST_DIRECTORY: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY", 
        str(Path.home() / ".chromadb_intelligent_customer_service")
    )
    
    # 嵌入模型配置
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # 重排模型配置
    RERANKER_MODEL_NAME: str = os.getenv("RERANKER_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    USE_RERANKER: bool = os.getenv("USE_RERANKER", "true").lower() == "true"
    
    # 检索配置
    DEFAULT_RETRIEVAL_LIMIT: int = int(os.getenv("DEFAULT_RETRIEVAL_LIMIT", "5"))
    RETRIEVAL_MULTIPLIER: int = int(os.getenv("RETRIEVAL_MULTIPLIER", "3"))  # 检索候选数量倍数
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
    
    # 高级配置
    ENABLE_HYBRID_SEARCH: bool = os.getenv("ENABLE_HYBRID_SEARCH", "true").lower() == "true"
    HYBRID_SEARCH_ALPHA: float = float(os.getenv("HYBRID_SEARCH_ALPHA", "0.7"))  # 向量搜索权重
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "chroma_persist_directory": cls.CHROMA_PERSIST_DIRECTORY,
            "embedding_model_name": cls.EMBEDDING_MODEL_NAME,
            "embedding_dimension": cls.EMBEDDING_DIMENSION,
            "reranker_model_name": cls.RERANKER_MODEL_NAME,
            "use_reranker": cls.USE_RERANKER,
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
            "enable_hybrid_search": cls.ENABLE_HYBRID_SEARCH,
            "hybrid_search_alpha": cls.HYBRID_SEARCH_ALPHA
        }
    
    @classmethod
    def get_chroma_settings(cls) -> Dict[str, Any]:
        """获取ChromaDB设置"""
        return {
            "anonymized_telemetry": False,
            "allow_reset": True,
            "is_persistent": True
        }
    
    @classmethod
    def get_embedding_model_config(cls) -> Dict[str, Any]:
        """获取嵌入模型配置"""
        return {
            "model_name": cls.EMBEDDING_MODEL_NAME,
            "device": "cpu",  # 可以设置为 "cuda" 如果有GPU
            "normalize_embeddings": True,
            "encode_kwargs": {
                "batch_size": cls.BATCH_SIZE,
                "show_progress_bar": False
            }
        }
    
    @classmethod
    def get_reranker_config(cls) -> Dict[str, Any]:
        """获取重排模型配置"""
        return {
            "model_name": cls.RERANKER_MODEL_NAME,
            "device": "cpu",  # 可以设置为 "cuda" 如果有GPU
            "max_length": 512,
            "batch_size": cls.BATCH_SIZE
        }


# 全局配置实例
vector_db_config = VectorDBConfig()


class ModelManager:
    """模型管理器 - 单例模式管理嵌入和重排模型"""
    
    _instance = None
    _embedding_model = None
    _reranker_model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_embedding_model(self):
        """获取嵌入模型（懒加载）"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                config = vector_db_config.get_embedding_model_config()
                self._embedding_model = SentenceTransformer(
                    config["model_name"],
                    device=config["device"]
                )
                print(f"✅ 嵌入模型加载成功: {config['model_name']}")
            except Exception as e:
                print(f"❌ 嵌入模型加载失败: {e}")
                raise
        return self._embedding_model
    
    def get_reranker_model(self):
        """获取重排模型（懒加载）"""
        if not vector_db_config.USE_RERANKER:
            return None
            
        if self._reranker_model is None:
            try:
                from sentence_transformers import CrossEncoder
                config = vector_db_config.get_reranker_config()
                self._reranker_model = CrossEncoder(
                    config["model_name"],
                    device=config["device"],
                    max_length=config["max_length"]
                )
                print(f"✅ 重排模型加载成功: {config['model_name']}")
            except Exception as e:
                print(f"⚠️ 重排模型加载失败: {e}")
                self._reranker_model = None
        return self._reranker_model
    
    def clear_cache(self):
        """清理模型缓存"""
        self._embedding_model = None
        self._reranker_model = None
        print("🧹 模型缓存已清理")


# 全局模型管理器实例
model_manager = ModelManager()
