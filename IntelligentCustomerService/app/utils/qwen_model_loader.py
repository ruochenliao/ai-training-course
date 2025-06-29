"""
Qwen模型加载器
使用ModelScope社区的Qwen嵌入模型和重排模型
"""

import logging
from typing import Optional, List

import numpy as np

try:
    import torch
except ImportError:
    torch = None
    logging.warning("PyTorch未安装，将使用回退实现")

logger = logging.getLogger(__name__)


class QwenEmbeddingModel:
    """Qwen嵌入模型包装器"""
    
    def __init__(self, model_path: str, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self.model = None
        self.tokenizer = None
        self.dimension = 896  # Qwen3-0.6B的嵌入维度
        
    def load_model(self):
        """加载模型"""
        try:
            from modelscope import AutoModel, AutoTokenizer
            
            logger.info(f"正在加载Qwen嵌入模型: {self.model_path}")
            
            # 加载tokenizer和模型
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                cache_dir=None  # 使用默认缓存目录
            )
            
            self.model = AutoModel.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                cache_dir=None  # 使用默认缓存目录
            )
            
            # 设置设备
            if self.device == "cuda" and hasattr(self.model, "cuda"):
                self.model = self.model.cuda()
            
            # 设置为评估模式
            if hasattr(self.model, "eval"):
                self.model.eval()
                
            logger.info(f"Qwen嵌入模型加载成功: {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Qwen嵌入模型加载失败: {e}")
            return False
    
    def encode(self, texts: List[str] | str) -> np.ndarray:
        """编码文本为嵌入向量"""
        if self.model is None or self.tokenizer is None:
            if not self.load_model():
                raise RuntimeError("模型未加载")
        
        try:
            # 标准化输入
            if isinstance(texts, str):
                texts = [texts]
                single_input = True
            else:
                single_input = False
            
            # 使用模型编码
            embeddings = []
            for text in texts:
                # 简单的文本编码实现
                # 注意：这里需要根据具体的Qwen模型API进行调整
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                
                if self.device == "cuda" and hasattr(inputs, "cuda"):
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                
                if torch is not None:
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        # 获取最后一层的隐藏状态并进行池化
                        embedding = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                        embeddings.append(embedding)
                else:
                    # 回退到简单实现
                    embedding = np.random.randn(self.dimension).astype(np.float32)
                    embeddings.append(embedding)
            
            result = np.array(embeddings)
            
            if single_input:
                return result[0]
            return result
            
        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            # 返回随机向量作为回退
            if isinstance(texts, str):
                return np.random.randn(self.dimension).astype(np.float32)
            else:
                return np.random.randn(len(texts), self.dimension).astype(np.float32)


class QwenRerankerModel:
    """Qwen重排模型包装器"""
    
    def __init__(self, model_path: str, device: str = "cpu", max_length: int = 512):
        self.model_path = model_path
        self.device = device
        self.max_length = max_length
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        """加载重排模型"""
        try:
            from modelscope import AutoModel, AutoTokenizer
            
            logger.info(f"正在加载Qwen重排模型: {self.model_path}")
            
            # 加载tokenizer和模型
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                cache_dir=None
            )
            
            self.model = AutoModel.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                cache_dir=None
            )
            
            # 设置设备
            if self.device == "cuda" and hasattr(self.model, "cuda"):
                self.model = self.model.cuda()
            
            # 设置为评估模式
            if hasattr(self.model, "eval"):
                self.model.eval()
                
            logger.info(f"Qwen重排模型加载成功: {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Qwen重排模型加载失败: {e}")
            return False
    
    def predict(self, query_doc_pairs: List[tuple]) -> List[float]:
        """预测查询-文档对的相关性分数"""
        if self.model is None or self.tokenizer is None:
            if not self.load_model():
                raise RuntimeError("重排模型未加载")
        
        try:
            scores = []
            for query, doc in query_doc_pairs:
                # 简单的相关性计算实现
                # 注意：这里需要根据具体的Qwen重排模型API进行调整
                combined_text = f"查询: {query} 文档: {doc}"
                inputs = self.tokenizer(
                    combined_text, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=self.max_length
                )
                
                if self.device == "cuda":
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                
                if torch is not None:
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        # 简单的分数计算（需要根据实际模型调整）
                        score = float(outputs.last_hidden_state.mean().cpu().numpy())
                        scores.append(score)
                else:
                    # 回退到简单实现
                    score = 0.5  # 默认分数
                    scores.append(score)
            
            return scores
            
        except Exception as e:
            logger.error(f"重排预测失败: {e}")
            # 返回随机分数作为回退
            return [0.5] * len(query_doc_pairs)


class FallbackEmbeddingModel:
    """回退嵌入模型 - 使用简单的TF-IDF或随机向量"""
    
    def __init__(self, device: str = "cpu", dimension: int = 896):
        self.device = device
        self.dimension = dimension
        logger.info(f"初始化回退嵌入模型，维度: {dimension}")
    
    def encode(self, texts: List[str] | str) -> np.ndarray:
        """使用简单方法编码文本"""
        try:
            # 标准化输入
            if isinstance(texts, str):
                texts = [texts]
                single_input = True
            else:
                single_input = False
            
            # 简单的哈希编码方法
            embeddings = []
            for text in texts:
                # 使用文本哈希生成确定性的向量
                text_hash = hash(text)
                np.random.seed(abs(text_hash) % (2**32))
                embedding = np.random.randn(self.dimension).astype(np.float32)
                # 归一化
                embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)
            
            result = np.array(embeddings)
            
            if single_input:
                return result[0]
            return result
            
        except Exception as e:
            logger.error(f"回退编码失败: {e}")
            # 最后的回退：返回零向量
            if isinstance(texts, str):
                return np.zeros(self.dimension, dtype=np.float32)
            else:
                return np.zeros((len(texts), self.dimension), dtype=np.float32)


def create_qwen_embedding_model(model_path: str, device: str = "cpu") -> Optional[QwenEmbeddingModel]:
    """创建Qwen嵌入模型"""
    try:
        model = QwenEmbeddingModel(model_path, device)
        if model.load_model():
            return model
        return None
    except Exception as e:
        logger.error(f"创建Qwen嵌入模型失败: {e}")
        return None


def create_qwen_reranker_model(model_path: str, device: str = "cpu", max_length: int = 512) -> Optional[QwenRerankerModel]:
    """创建Qwen重排模型"""
    try:
        model = QwenRerankerModel(model_path, device, max_length)
        if model.load_model():
            return model
        return None
    except Exception as e:
        logger.error(f"创建Qwen重排模型失败: {e}")
        return None


def create_fallback_embedding_model(device: str = "cpu") -> FallbackEmbeddingModel:
    """创建回退嵌入模型"""
    return FallbackEmbeddingModel(device)
