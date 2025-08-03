"""
向量化管理器

负责文本的向量化处理，支持多种嵌入模型。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from openai import AsyncOpenAI
import hashlib
import json
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """嵌入模型基类"""
    
    def __init__(self, model_name: str, dimension: int):
        self.model_name = model_name
        self.dimension = dimension
    
    async def embed_text(self, text: str) -> List[float]:
        """将文本转换为向量"""
        raise NotImplementedError
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量"""
        raise NotImplementedError


class OpenAIEmbedding(EmbeddingModel):
    """OpenAI嵌入模型"""
    
    def __init__(self, model_name: str = "text-embedding-3-small", api_key: str = None):
        # 根据模型设置维度
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        
        super().__init__(model_name, dimensions.get(model_name, 1536))
        
        self.client = AsyncOpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """将单个文本转换为向量"""
        try:
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI嵌入失败: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量"""
        try:
            # OpenAI API支持批量处理，但有限制
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await self.client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
        except Exception as e:
            logger.error(f"OpenAI批量嵌入失败: {e}")
            raise


class LocalEmbedding(EmbeddingModel):
    """本地嵌入模型（使用sentence-transformers）"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            super().__init__(model_name, self.model.get_sentence_embedding_dimension())
        except ImportError:
            raise ImportError("需要安装sentence-transformers: pip install sentence-transformers")
    
    async def embed_text(self, text: str) -> List[float]:
        """将单个文本转换为向量"""
        try:
            # sentence-transformers是同步的，在线程池中运行
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, self.model.encode, text
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"本地嵌入失败: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量将文本转换为向量"""
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, self.model.encode, texts
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"本地批量嵌入失败: {e}")
            raise


class EmbeddingCache:
    """嵌入缓存"""
    
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, List[float]] = {}
        self.max_size = max_size
    
    def _get_cache_key(self, text: str, model_name: str) -> str:
        """生成缓存键"""
        content = f"{model_name}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, text: str, model_name: str) -> Optional[List[float]]:
        """获取缓存的嵌入"""
        key = self._get_cache_key(text, model_name)
        return self.cache.get(key)
    
    def set(self, text: str, model_name: str, embedding: List[float]):
        """设置缓存的嵌入"""
        if len(self.cache) >= self.max_size:
            # 简单的LRU：删除第一个元素
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        key = self._get_cache_key(text, model_name)
        self.cache[key] = embedding
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()


class EmbeddingManager:
    """嵌入管理器"""
    
    def __init__(self, default_model: str = "openai"):
        self.models: Dict[str, EmbeddingModel] = {}
        self.default_model = default_model
        self.cache = EmbeddingCache()
        
        # 初始化默认模型
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化嵌入模型"""
        try:
            # OpenAI模型
            self.models["openai"] = OpenAIEmbedding()
            self.models["openai-small"] = OpenAIEmbedding("text-embedding-3-small")
            self.models["openai-large"] = OpenAIEmbedding("text-embedding-3-large")
            
            # 本地模型
            try:
                self.models["local"] = LocalEmbedding()
                self.models["local-multilingual"] = LocalEmbedding("paraphrase-multilingual-MiniLM-L12-v2")
            except ImportError:
                logger.warning("本地嵌入模型不可用，请安装sentence-transformers")
            
            logger.info(f"初始化嵌入模型: {list(self.models.keys())}")
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {e}")
    
    def get_model(self, model_name: str = None) -> EmbeddingModel:
        """获取嵌入模型"""
        model_name = model_name or self.default_model
        if model_name not in self.models:
            raise ValueError(f"未找到嵌入模型: {model_name}")
        return self.models[model_name]
    
    async def embed_text(self, text: str, model_name: str = None, use_cache: bool = True) -> List[float]:
        """将文本转换为向量"""
        model = self.get_model(model_name)
        
        # 检查缓存
        if use_cache:
            cached_embedding = self.cache.get(text, model.model_name)
            if cached_embedding is not None:
                return cached_embedding
        
        # 生成嵌入
        embedding = await model.embed_text(text)
        
        # 缓存结果
        if use_cache:
            self.cache.set(text, model.model_name, embedding)
        
        return embedding
    
    async def embed_texts(self, texts: List[str], model_name: str = None, 
                         use_cache: bool = True) -> List[List[float]]:
        """批量将文本转换为向量"""
        model = self.get_model(model_name)
        
        if not use_cache:
            return await model.embed_texts(texts)
        
        # 检查缓存并分离已缓存和未缓存的文本
        cached_embeddings = {}
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cached_embedding = self.cache.get(text, model.model_name)
            if cached_embedding is not None:
                cached_embeddings[i] = cached_embedding
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # 为未缓存的文本生成嵌入
        if uncached_texts:
            new_embeddings = await model.embed_texts(uncached_texts)
            
            # 缓存新生成的嵌入
            for text, embedding in zip(uncached_texts, new_embeddings):
                self.cache.set(text, model.model_name, embedding)
            
            # 将新嵌入添加到结果中
            for i, embedding in zip(uncached_indices, new_embeddings):
                cached_embeddings[i] = embedding
        
        # 按原始顺序返回结果
        return [cached_embeddings[i] for i in range(len(texts))]
    
    def get_dimension(self, model_name: str = None) -> int:
        """获取模型的向量维度"""
        model = self.get_model(model_name)
        return model.dimension
    
    def list_models(self) -> List[str]:
        """列出可用的模型"""
        return list(self.models.keys())
    
    async def similarity(self, text1: str, text2: str, model_name: str = None) -> float:
        """计算两个文本的相似度"""
        embeddings = await self.embed_texts([text1, text2], model_name)
        
        # 计算余弦相似度
        vec1 = np.array(embeddings[0])
        vec2 = np.array(embeddings[1])
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("嵌入缓存已清空")


# 全局嵌入管理器
embedding_manager = EmbeddingManager()
