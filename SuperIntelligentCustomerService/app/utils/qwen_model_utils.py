"""
通义千问模型工具类
提供通义千问嵌入模型和重排模型的加载和管理功能
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    CrossEncoder = None

try:
    from transformers import AutoModel, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    AutoModel = None
    AutoTokenizer = None


class QwenModelManager:
    """通义千问模型管理器"""
    
    def __init__(self, models_dir: str = None):
        """
        初始化通义千问模型管理器
        
        Args:
            models_dir: 模型目录路径
        """
        if models_dir is None:
            models_dir = Path(__file__).parent.parent.parent / "models"
        
        self.models_dir = Path(models_dir)
        self.embedding_model_path = self.models_dir / "embedding" / "Qwen3-8B"
        self.reranker_model_path = self.models_dir / "reranker" / "Qwen3-Reranker-8B"
        
        self._embedding_model = None
        self._reranker_model = None
        
        logger.info(f"通义千问模型管理器初始化完成，模型目录: {self.models_dir}")
    
    def check_models_availability(self) -> Dict[str, bool]:
        """检查模型可用性"""
        return {
            "embedding_model_exists": self.embedding_model_path.exists(),
            "reranker_model_exists": self.reranker_model_path.exists(),
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
            "transformers_available": TRANSFORMERS_AVAILABLE
        }
    
    def get_embedding_model(self) -> Optional[SentenceTransformer]:
        """获取嵌入模型"""
        if self._embedding_model is None:
            self._embedding_model = self._load_embedding_model()
        return self._embedding_model
    
    def get_reranker_model(self) -> Optional[CrossEncoder]:
        """获取重排模型"""
        if self._reranker_model is None:
            self._reranker_model = self._load_reranker_model()
        return self._reranker_model
    
    def _load_embedding_model(self) -> Optional[SentenceTransformer]:
        """加载嵌入模型 - 必须使用通义千问模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers不可用，无法加载嵌入模型")
            raise RuntimeError("sentence-transformers依赖缺失，无法加载嵌入模型")

        # 检查通义千问嵌入模型是否存在
        if not self.embedding_model_path.exists():
            error_msg = f"通义千问嵌入模型路径不存在: {self.embedding_model_path}"
            logger.error(error_msg)
            logger.error("请运行 'python models/quick_download.py' 下载模型")
            raise FileNotFoundError(error_msg)

        try:
            logger.info(f"加载通义千问嵌入模型: {self.embedding_model_path}")
            model = SentenceTransformer(str(self.embedding_model_path), device='cpu')
            logger.info("通义千问嵌入模型加载成功")
            return model
        except Exception as e:
            error_msg = f"加载通义千问嵌入模型失败: {e}"
            logger.error(error_msg)
            logger.error("请检查模型文件完整性或重新下载模型")
            raise RuntimeError(error_msg)
    
    def _load_reranker_model(self) -> Optional[CrossEncoder]:
        """加载重排模型 - 必须使用通义千问模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers不可用，无法加载重排模型")
            raise RuntimeError("sentence-transformers依赖缺失，无法加载重排模型")

        # 检查通义千问重排模型是否存在
        if not self.reranker_model_path.exists():
            error_msg = f"通义千问重排模型路径不存在: {self.reranker_model_path}"
            logger.error(error_msg)
            logger.error("请运行 'python models/quick_download.py' 下载模型")
            raise FileNotFoundError(error_msg)

        try:
            logger.info(f"加载通义千问重排模型: {self.reranker_model_path}")
            model = CrossEncoder(str(self.reranker_model_path), device='cpu')
            logger.info("通义千问重排模型加载成功")
            return model
        except Exception as e:
            error_msg = f"加载通义千问重排模型失败: {e}"
            logger.error(error_msg)
            logger.error("请检查模型文件完整性或重新下载模型")
            raise RuntimeError(error_msg)
    
    def encode_texts(self, texts, batch_size: int = 32):
        """编码文本为向量"""
        model = self.get_embedding_model()
        if model is None:
            raise RuntimeError("嵌入模型不可用")
        
        return model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    
    def rerank_texts(self, query: str, texts: list, top_k: int = None):
        """重排文本 - 必须使用通义千问重排模型"""
        model = self.get_reranker_model()
        if model is None:
            raise RuntimeError("通义千问重排模型不可用，无法进行重排")

        # 构建查询-文本对
        pairs = [[query, text] for text in texts]

        # 计算相关性分数
        scores = model.predict(pairs)

        # 按分数排序
        scored_texts = list(zip(texts, scores))
        scored_texts.sort(key=lambda x: x[1], reverse=True)

        # 返回重排后的文本
        reranked_texts = [text for text, score in scored_texts]
        return reranked_texts[:top_k] if top_k else reranked_texts
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        availability = self.check_models_availability()
        
        info = {
            "models_directory": str(self.models_dir),
            "embedding_model_path": str(self.embedding_model_path),
            "reranker_model_path": str(self.reranker_model_path),
            "availability": availability,
            "embedding_model_loaded": self._embedding_model is not None,
            "reranker_model_loaded": self._reranker_model is not None
        }
        
        # 添加模型详细信息
        if self._embedding_model:
            info["embedding_model_info"] = {
                "model_name": getattr(self._embedding_model, 'model_name', 'unknown'),
                "max_seq_length": getattr(self._embedding_model, 'max_seq_length', 'unknown'),
                "device": str(getattr(self._embedding_model, 'device', 'unknown'))
            }
        
        if self._reranker_model:
            info["reranker_model_info"] = {
                "model_name": getattr(self._reranker_model, 'model_name', 'unknown'),
                "device": str(getattr(self._reranker_model, 'device', 'unknown'))
            }
        
        return info


# 全局实例
qwen_model_manager = QwenModelManager()
