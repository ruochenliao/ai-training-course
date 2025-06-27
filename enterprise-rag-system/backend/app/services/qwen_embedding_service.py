"""
基于Qwen2.5-7B-Instruct的嵌入服务 - 企业级RAG系统
严格按照技术栈要求：Qwen2.5-7B-Instruct (ModelScope部署)
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any

import numpy as np
import torch
from app.core.config import settings
from loguru import logger
from modelscope import AutoModel, AutoTokenizer
from modelscope.hub.snapshot_download import snapshot_download


class QwenEmbeddingService:
    """Qwen2.5-7B-Instruct 嵌入服务"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "qwen/Qwen2.5-7B-Instruct"
        self.max_length = 8192  # Qwen2.5支持的最大长度
        self.embedding_dim = 1024  # 嵌入维度
        self.batch_size = 32  # 批处理大小
        self._initialized = False
    
    async def initialize(self):
        """初始化Qwen2.5模型"""
        if self._initialized:
            return
        
        try:
            logger.info("正在初始化Qwen2.5-7B-Instruct嵌入模型...")
            
            # 在线程池中加载模型，避免阻塞
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
            
            self._initialized = True
            logger.info(f"Qwen2.5嵌入模型初始化完成 (设备: {self.device})")
            
        except Exception as e:
            logger.error(f"Qwen2.5模型初始化失败: {e}")
            raise
    
    def _load_model(self):
        """同步加载模型"""
        try:
            # 下载模型到本地缓存
            model_dir = snapshot_download(
                self.model_name,
                cache_dir=settings.MODELSCOPE_CACHE_DIR,
                revision="master"
            )
            
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_dir,
                trust_remote_code=True,
                padding_side="right"
            )
            
            # 加载模型
            self.model = AutoModel.from_pretrained(
                model_dir,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            # 设置为评估模式
            self.model.eval()
            
            # 移动到指定设备
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            logger.info(f"模型加载完成，参数量: {sum(p.numel() for p in self.model.parameters()):,}")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 清理文本
        text = text.strip()
        
        # 截断过长的文本
        if len(text) > self.max_length * 4:  # 粗略估计token数量
            text = text[:self.max_length * 4]
            logger.warning(f"文本过长，已截断到 {len(text)} 字符")
        
        return text
    
    async def encode_single(self, text: str) -> np.ndarray:
        """编码单个文本"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 预处理文本
            processed_text = self._preprocess_text(text)
            
            # 在线程池中执行编码
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self._encode_sync, 
                [processed_text]
            )
            
            return embedding[0]
            
        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            raise
    
    async def encode_batch(self, texts: List[str]) -> List[np.ndarray]:
        """批量编码文本"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 预处理文本
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # 分批处理
            embeddings = []
            for i in range(0, len(processed_texts), self.batch_size):
                batch_texts = processed_texts[i:i + self.batch_size]
                
                # 在线程池中执行编码
                loop = asyncio.get_event_loop()
                batch_embeddings = await loop.run_in_executor(
                    None, 
                    self._encode_sync, 
                    batch_texts
                )
                
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"批量文本编码失败: {e}")
            raise
    
    def _encode_sync(self, texts: List[str]) -> List[np.ndarray]:
        """同步编码文本"""
        try:
            with torch.no_grad():
                # Tokenize
                inputs = self.tokenizer(
                    texts,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt"
                )
                
                # 移动到设备
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # 获取模型输出
                outputs = self.model(**inputs)
                
                # 提取嵌入向量 (使用最后一层的hidden states)
                last_hidden_states = outputs.last_hidden_state
                
                # 使用attention mask进行平均池化
                attention_mask = inputs['attention_mask']
                mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_states.size()).float()
                
                # 计算加权平均
                sum_embeddings = torch.sum(last_hidden_states * mask_expanded, 1)
                sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
                embeddings = sum_embeddings / sum_mask
                
                # 归一化
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                
                # 转换为numpy数组
                embeddings_np = embeddings.cpu().numpy()
                
                return [emb for emb in embeddings_np]
                
        except Exception as e:
            logger.error(f"同步编码失败: {e}")
            raise
    
    async def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """计算两个嵌入向量的余弦相似度"""
        try:
            # 确保向量已归一化
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # 计算余弦相似度
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            return 0.0
    
    async def compute_similarity_batch(self, query_embedding: np.ndarray, embeddings: List[np.ndarray]) -> List[float]:
        """批量计算相似度"""
        try:
            similarities = []
            for embedding in embeddings:
                similarity = await self.compute_similarity(query_embedding, embedding)
                similarities.append(similarity)
            
            return similarities
            
        except Exception as e:
            logger.error(f"批量相似度计算失败: {e}")
            return [0.0] * len(embeddings)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "max_length": self.max_length,
            "device": self.device,
            "batch_size": self.batch_size,
            "initialized": self._initialized,
            "model_parameters": sum(p.numel() for p in self.model.parameters()) if self.model else 0
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self._initialized:
                return {
                    "status": "not_initialized",
                    "message": "模型未初始化"
                }
            
            # 测试编码
            test_text = "这是一个测试文本"
            start_time = datetime.now()
            embedding = await self.encode_single(test_text)
            end_time = datetime.now()
            
            latency = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "message": "模型运行正常",
                "test_embedding_shape": embedding.shape,
                "latency_ms": latency,
                "device": self.device
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"健康检查失败: {e}"
            }
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.model:
                del self.model
            if self.tokenizer:
                del self.tokenizer
            
            # 清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self._initialized = False
            logger.info("Qwen2.5嵌入服务资源已清理")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")


# 全局嵌入服务实例
qwen_embedding_service = QwenEmbeddingService()


# 便捷函数
async def encode_text(text: str) -> np.ndarray:
    """编码单个文本的便捷函数"""
    return await qwen_embedding_service.encode_single(text)


async def encode_texts(texts: List[str]) -> List[np.ndarray]:
    """批量编码文本的便捷函数"""
    return await qwen_embedding_service.encode_batch(texts)


async def calculate_similarity(text1: str, text2: str) -> float:
    """计算两个文本相似度的便捷函数"""
    embedding1 = await encode_text(text1)
    embedding2 = await encode_text(text2)
    return await qwen_embedding_service.compute_similarity(embedding1, embedding2)


# 嵌入服务性能监控
class EmbeddingMetrics:
    """嵌入服务性能指标"""
    
    def __init__(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        self.error_count = 0
    
    def record_request(self, token_count: int, latency_ms: float, success: bool = True):
        """记录请求指标"""
        self.total_requests += 1
        self.total_tokens += token_count
        self.total_latency += latency_ms
        
        if not success:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self.total_requests == 0:
            return {
                "total_requests": 0,
                "avg_latency_ms": 0,
                "avg_tokens_per_request": 0,
                "error_rate": 0,
                "throughput_tokens_per_second": 0
            }
        
        avg_latency = self.total_latency / self.total_requests
        avg_tokens = self.total_tokens / self.total_requests
        error_rate = self.error_count / self.total_requests
        throughput = self.total_tokens / (self.total_latency / 1000) if self.total_latency > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "avg_latency_ms": avg_latency,
            "avg_tokens_per_request": avg_tokens,
            "error_rate": error_rate,
            "throughput_tokens_per_second": throughput
        }


# 全局指标收集器
embedding_metrics = EmbeddingMetrics()
