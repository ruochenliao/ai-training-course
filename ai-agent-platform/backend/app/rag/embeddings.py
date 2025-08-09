"""
# Copyright (c) 2025 左岚. All rights reserved.

向量化管理器

负责文本的向量化处理，支持多种嵌入模型。
"""

# # Standard library imports
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import logging
import threading
from typing import Any, Dict, List, Optional, Tuple

# # Third-party imports
import numpy as np
from openai import AsyncOpenAI

# # Local application imports
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

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):  # 使用小型中文嵌入模型，加载更快
        try:
            # # Standard library imports
            import os

            # # Third-party imports
            from sentence_transformers import SentenceTransformer

            # 设置模型缓存目录到项目的models文件夹
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            models_dir = os.path.join(project_root, "models")
            os.makedirs(models_dir, exist_ok=True)

            # 设置环境变量，让sentence-transformers使用我们的models目录
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = models_dir

            # 检查模型是否已存在
            model_path = os.path.join(models_dir, model_name.replace("/", "_"))
            if os.path.exists(model_path):
                logger.info(f"📂 加载本地模型: {model_name}")
            else:
                logger.info(f"📥 下载模型: {model_name}")

            self.model = SentenceTransformer(model_name, cache_folder=models_dir)
            super().__init__(model_name, self.model.get_sentence_embedding_dimension())
        except ImportError:
            raise ImportError("需要安装sentence-transformers: pip install sentence-transformers")


class BGEReranker:
    """BGE重排模型"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        try:
            # # Standard library imports
            import os

            # # Third-party imports
            from sentence_transformers import CrossEncoder

            # 设置模型缓存目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            models_dir = os.path.join(project_root, "models")
            os.makedirs(models_dir, exist_ok=True)
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = models_dir

            self.model_name = model_name
            self.model = CrossEncoder(model_name, cache_folder=models_dir)
            logger.info(f"✅ BGE重排模型加载完成: {model_name}")

        except ImportError:
            raise ImportError("需要安装sentence-transformers: pip install sentence-transformers")
        except Exception as e:
            logger.error(f"BGE重排模型加载失败: {e}")
            raise

    async def rerank(self, query: str, documents: List[str], top_k: int = 10) -> List[Tuple[int, float]]:
        """重排文档

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前k个结果

        Returns:
            List[Tuple[int, float]]: (原始索引, 重排分数) 的列表，按分数降序排列
        """
        try:
            if not documents:
                return []

            # 准备查询-文档对
            pairs = [(query, doc) for doc in documents]

            # 在线程池中运行重排（因为CrossEncoder是同步的）
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(None, self.model.predict, pairs)

            # 创建(索引, 分数)对并排序
            indexed_scores = [(i, float(score)) for i, score in enumerate(scores)]
            indexed_scores.sort(key=lambda x: x[1], reverse=True)

            return indexed_scores[:top_k]

        except Exception as e:
            logger.error(f"BGE重排失败: {e}")
            # 返回原始顺序
            return [(i, 0.0) for i in range(min(len(documents), top_k))]
    
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

    def __init__(self, default_model: str = "bge-zh"):  # 直接使用BGE中文模型作为默认
        self.models: Dict[str, EmbeddingModel] = {}
        self.reranker: Optional[BGEReranker] = None  # 重排模型
        self.default_model = default_model
        self.cache = EmbeddingCache()
        self._loading_models = set()  # 正在加载的模型
        self._loaded_models = set()  # 已加载的模型
        self._executor = ThreadPoolExecutor(max_workers=2)  # 后台加载线程池

        # 初始化默认模型
        self._initialize_models()

    def _is_model_downloaded(self, model_name: str) -> bool:
        """检查模型是否已下载到本地"""
        try:
            # # Standard library imports
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            models_dir = os.path.join(project_root, "models")

            # Hugging Face模型的存储格式是 models--org--model-name
            hf_model_path = os.path.join(models_dir, f"models--{model_name.replace('/', '--')}")

            # 检查模型目录是否存在
            if os.path.exists(hf_model_path):
                # 检查snapshots目录是否存在且不为空
                snapshots_dir = os.path.join(hf_model_path, "snapshots")
                if os.path.exists(snapshots_dir):
                    snapshots = os.listdir(snapshots_dir)
                    if snapshots:
                        # 检查最新的snapshot是否包含模型文件
                        latest_snapshot = os.path.join(snapshots_dir, snapshots[0])
                        if os.path.exists(latest_snapshot):
                            files = os.listdir(latest_snapshot)
                            has_config = any(f.startswith('config') and f.endswith('.json') for f in files)
                            has_model = any(f.endswith(('.bin', '.safetensors')) for f in files)
                            return has_config and has_model
            return False
        except Exception:
            return False
    
    def _initialize_models(self):
        """初始化嵌入模型"""
        try:
            # BGE中文嵌入模型（后台异步加载）
            logger.info("BGE嵌入模型将在后台加载...")

            # OpenAI模型（如果配置了API密钥）
            if settings.OPENAI_API_KEY:
                try:
                    self.models["openai"] = OpenAIEmbedding()
                    self.models["openai-small"] = OpenAIEmbedding("text-embedding-3-small")
                    self.models["openai-large"] = OpenAIEmbedding("text-embedding-3-large")
                except Exception as e:
                    logger.warning(f"OpenAI嵌入模型初始化失败: {e}")

            logger.info(f"初始化嵌入模型: {list(self.models.keys())}")
            logger.info(f"默认嵌入模型: {self.default_model}")
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {e}")

    def start_background_bge_loading(self):
        """启动后台BGE模型下载和加载任务"""
        self._start_background_loading()

    def _start_background_loading(self):
        """内部方法：启动后台BGE模型加载任务"""
        def load_bge_models():
            """智能加载BGE模型（优先使用本地已下载的模型）"""
            try:
                # 优先加载小型BGE中文模型（更快）
                if "bge-zh" not in self.models and "bge-zh" not in self._loaded_models:
                    self._loading_models.add("bge-zh")
                    try:
                        model_name = "BAAI/bge-small-zh-v1.5"
                        if self._is_model_downloaded(model_name):
                            logger.info("📂 加载本地BGE中文模型...")
                        else:
                            logger.info("📥 下载BGE中文模型...")

                        bge_zh_model = LocalEmbedding(model_name)
                        self.models["bge-zh"] = bge_zh_model
                        self._loaded_models.add("bge-zh")
                        logger.info("✅ BGE中文模型就绪")

                        # 设置BGE模型为默认模型
                        self.default_model = "bge-zh"
                        logger.info("🔄 BGE嵌入模型已就绪")
                    except Exception as e:
                        logger.error(f"❌ BGE中文模型加载失败: {e}")
                    finally:
                        self._loading_models.discard("bge-zh")

                # 然后加载大型BGE中文模型（可选）
                if "bge-large" not in self.models and "bge-large" not in self._loaded_models:
                    self._loading_models.add("bge-large")
                    try:
                        model_name = "BAAI/bge-large-zh-v1.5"
                        if self._is_model_downloaded(model_name):
                            logger.info("📂 加载本地BGE大型模型...")
                        else:
                            logger.info("📥 下载BGE大型模型...")

                        bge_large_model = LocalEmbedding(model_name)
                        self.models["bge-large"] = bge_large_model
                        self._loaded_models.add("bge-large")
                        logger.info("✅ BGE大型模型就绪")
                    except Exception as e:
                        logger.error(f"❌ BGE大型模型加载失败: {e}")
                    finally:
                        self._loading_models.discard("bge-large")

                # 加载BGE重排模型
                if self.reranker is None:
                    try:
                        reranker_model_name = "BAAI/bge-reranker-v2-m3"
                        if self._is_model_downloaded(reranker_model_name):
                            logger.info("📂 加载本地BGE重排模型...")
                        else:
                            logger.info("📥 下载BGE重排模型...")

                        self.reranker = BGEReranker(reranker_model_name)
                        logger.info("✅ BGE重排模型就绪")
                    except Exception as e:
                        logger.error(f"❌ BGE重排模型加载失败: {e}")

                logger.info(f"🎉 模型加载完成 - 嵌入: {len(self.models)}个, 重排: {'✅' if self.reranker else '❌'}")

            except Exception as e:
                logger.error(f"❌ BGE模型加载失败: {e}")

        # 在后台线程中执行加载任务
        self._executor.submit(load_bge_models)

    def get_model_status(self) -> Dict[str, str]:
        """获取模型加载状态"""
        status = {}
        for model_name in ["bge-zh", "bge-large"]:
            if model_name in self._loading_models:
                status[model_name] = "loading"
            elif model_name in self.models:
                status[model_name] = "ready"
            else:
                status[model_name] = "not_loaded"

        # 添加重排模型状态
        status["reranker"] = "ready" if self.reranker else "not_loaded"
        return status
    
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

    async def rerank_documents(self, query: str, documents: List[str], top_k: int = 10) -> List[Tuple[int, float]]:
        """使用BGE重排模型对文档进行重排

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前k个结果

        Returns:
            List[Tuple[int, float]]: (原始索引, 重排分数) 的列表，按分数降序排列
        """
        if self.reranker is None:
            logger.warning("重排模型未加载，返回原始顺序")
            return [(i, 0.0) for i in range(min(len(documents), top_k))]

        return await self.reranker.rerank(query, documents, top_k)

    def has_reranker(self) -> bool:
        """检查是否有可用的重排模型"""
        return self.reranker is not None


class TokenCounter:
    """Token计数器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """
        计算文本的token数量

        Args:
            text: 输入文本
            model: 模型名称

        Returns:
            token数量
        """
        try:
            # 简单的token估算，实际应该使用tiktoken库
            # 大约每4个字符为1个token
            return len(text) // 4
        except Exception as e:
            self.logger.error(f"计算token失败: {e}")
            return 0

    def count_tokens_batch(self, texts: List[str], model: str = "gpt-3.5-turbo") -> List[int]:
        """
        批量计算token数量

        Args:
            texts: 文本列表
            model: 模型名称

        Returns:
            token数量列表
        """
        return [self.count_tokens(text, model) for text in texts]


# 全局嵌入管理器
embedding_manager = EmbeddingManager()
token_counter = TokenCounter()
