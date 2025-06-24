"""
通义千问模型服务
集成通义千问3-8B嵌入模型和通义千问3-Reranker-8B重排模型
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union
import numpy as np
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
from modelscope import snapshot_download
import dashscope
from dashscope import TextEmbedding, TextRerank

from app.core.config import settings

logger = logging.getLogger(__name__)


class QwenEmbeddingService:
    """通义千问3-8B嵌入模型服务"""
    
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.model_path = settings.EMBEDDING_MODEL_PATH
        self.api_key = settings.EMBEDDING_API_KEY
        self.dimension = settings.EMBEDDING_DIMENSION
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.max_length = settings.EMBEDDING_MAX_LENGTH
        
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 设置DashScope API Key
        if self.api_key:
            dashscope.api_key = self.api_key
    
    async def initialize(self):
        """初始化模型"""
        try:
            # 检查本地模型是否存在
            if not os.path.exists(self.model_path):
                logger.info(f"本地模型不存在，从魔塔社区下载: {self.model_name}")
                await self._download_model()
            
            # 加载本地模型
            await self._load_local_model()
            logger.info("通义千问嵌入模型初始化完成")
            
        except Exception as e:
            logger.error(f"嵌入模型初始化失败: {e}")
            logger.info("将使用API模式")
    
    async def _download_model(self):
        """从魔塔社区下载模型"""
        try:
            # 创建模型目录
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # 下载模型
            model_dir = snapshot_download(
                self.model_name,
                cache_dir=os.path.dirname(self.model_path),
                revision="master"
            )
            
            # 移动到指定路径
            if model_dir != self.model_path:
                import shutil
                shutil.move(model_dir, self.model_path)
            
            logger.info(f"模型下载完成: {self.model_path}")
            
        except Exception as e:
            logger.error(f"模型下载失败: {e}")
            raise
    
    async def _load_local_model(self):
        """加载本地模型"""
        try:
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # 加载模型
            self.model = AutoModel.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            ).to(self.device)
            
            # 设置为评估模式
            self.model.eval()
            
            logger.info(f"本地模型加载完成，设备: {self.device}")
            
        except Exception as e:
            logger.error(f"本地模型加载失败: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量文本嵌入"""
        try:
            if self.model and self.tokenizer:
                return await self._embed_texts_local(texts)
            else:
                return await self._embed_texts_api(texts)
                
        except Exception as e:
            logger.error(f"文本嵌入失败: {e}")
            return []
    
    async def embed_query(self, query: str) -> List[float]:
        """单个查询嵌入"""
        try:
            results = await self.embed_texts([query])
            return results[0] if results else []
            
        except Exception as e:
            logger.error(f"查询嵌入失败: {e}")
            return []
    
    async def _embed_texts_local(self, texts: List[str]) -> List[List[float]]:
        """使用本地模型进行嵌入"""
        embeddings = []
        
        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            
            # Tokenize
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt"
            ).to(self.device)
            
            # 生成嵌入
            with torch.no_grad():
                outputs = self.model(**inputs)
                # 使用池化策略获取句子嵌入
                batch_embeddings = self._mean_pooling(
                    outputs.last_hidden_state,
                    inputs["attention_mask"]
                )
                
                # 归一化
                batch_embeddings = torch.nn.functional.normalize(
                    batch_embeddings, p=2, dim=1
                )
                
                embeddings.extend(batch_embeddings.cpu().numpy().tolist())
        
        return embeddings
    
    async def _embed_texts_api(self, texts: List[str]) -> List[List[float]]:
        """使用API进行嵌入"""
        if not self.api_key:
            raise ValueError("API Key未配置")
        
        embeddings = []
        
        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            
            try:
                response = TextEmbedding.call(
                    model="text-embedding-v2",
                    input=batch_texts
                )
                
                if response.status_code == 200:
                    for item in response.output["embeddings"]:
                        embeddings.append(item["embedding"])
                else:
                    logger.error(f"API调用失败: {response}")
                    
            except Exception as e:
                logger.error(f"API嵌入失败: {e}")
        
        return embeddings
    
    def _mean_pooling(self, token_embeddings, attention_mask):
        """平均池化"""
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


class QwenRerankerService:
    """通义千问3-Reranker-8B重排模型服务"""
    
    def __init__(self):
        self.model_name = settings.RERANKER_MODEL_NAME
        self.model_path = settings.RERANKER_MODEL_PATH
        self.api_key = settings.RERANKER_API_KEY
        self.top_k = settings.RERANKER_TOP_K
        self.batch_size = settings.RERANKER_BATCH_SIZE
        
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 设置DashScope API Key
        if self.api_key:
            dashscope.api_key = self.api_key
    
    async def initialize(self):
        """初始化重排模型"""
        try:
            # 检查本地模型是否存在
            if not os.path.exists(self.model_path):
                logger.info(f"本地重排模型不存在，从魔塔社区下载: {self.model_name}")
                await self._download_model()
            
            # 加载本地模型
            await self._load_local_model()
            logger.info("通义千问重排模型初始化完成")
            
        except Exception as e:
            logger.error(f"重排模型初始化失败: {e}")
            logger.info("将使用API模式")
    
    async def _download_model(self):
        """从魔塔社区下载重排模型"""
        try:
            # 创建模型目录
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # 下载模型
            model_dir = snapshot_download(
                self.model_name,
                cache_dir=os.path.dirname(self.model_path),
                revision="master"
            )
            
            # 移动到指定路径
            if model_dir != self.model_path:
                import shutil
                shutil.move(model_dir, self.model_path)
            
            logger.info(f"重排模型下载完成: {self.model_path}")
            
        except Exception as e:
            logger.error(f"重排模型下载失败: {e}")
            raise
    
    async def _load_local_model(self):
        """加载本地重排模型"""
        try:
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # 加载模型
            self.model = AutoModel.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            ).to(self.device)
            
            # 设置为评估模式
            self.model.eval()
            
            logger.info(f"本地重排模型加载完成，设备: {self.device}")
            
        except Exception as e:
            logger.error(f"本地重排模型加载失败: {e}")
            raise
    
    async def rerank(self, 
                    query: str, 
                    documents: List[str], 
                    top_k: Optional[int] = None) -> Dict[str, Any]:
        """重排文档"""
        try:
            if top_k is None:
                top_k = self.top_k
            
            if self.model and self.tokenizer:
                return await self._rerank_local(query, documents, top_k)
            else:
                return await self._rerank_api(query, documents, top_k)
                
        except Exception as e:
            logger.error(f"文档重排失败: {e}")
            return {"indices": list(range(min(len(documents), top_k))), "scores": [0.0] * min(len(documents), top_k)}
    
    async def _rerank_local(self, 
                           query: str, 
                           documents: List[str], 
                           top_k: int) -> Dict[str, Any]:
        """使用本地模型重排"""
        scores = []
        
        # 分批处理
        for i in range(0, len(documents), self.batch_size):
            batch_docs = documents[i:i + self.batch_size]
            
            # 构建输入对
            pairs = [[query, doc] for doc in batch_docs]
            
            # Tokenize
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # 计算相关性分数
            with torch.no_grad():
                outputs = self.model(**inputs)
                batch_scores = outputs.logits.squeeze(-1).cpu().numpy().tolist()
                scores.extend(batch_scores)
        
        # 排序并返回top_k
        scored_docs = list(enumerate(scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        top_indices = [idx for idx, _ in scored_docs[:top_k]]
        top_scores = [score for _, score in scored_docs[:top_k]]
        
        return {
            "indices": top_indices,
            "scores": top_scores
        }
    
    async def _rerank_api(self, 
                         query: str, 
                         documents: List[str], 
                         top_k: int) -> Dict[str, Any]:
        """使用API重排"""
        if not self.api_key:
            raise ValueError("API Key未配置")
        
        try:
            response = TextRerank.call(
                model="gte-rerank",
                query=query,
                documents=documents,
                top_n=top_k
            )
            
            if response.status_code == 200:
                results = response.output["results"]
                indices = [item["index"] for item in results]
                scores = [item["relevance_score"] for item in results]
                
                return {
                    "indices": indices,
                    "scores": scores
                }
            else:
                logger.error(f"重排API调用失败: {response}")
                
        except Exception as e:
            logger.error(f"API重排失败: {e}")
        
        # 返回默认排序
        return {
            "indices": list(range(min(len(documents), top_k))),
            "scores": [0.0] * min(len(documents), top_k)
        }


class QwenModelManager:
    """通义千问模型管理器"""
    
    def __init__(self):
        self.embedding_service = QwenEmbeddingService()
        self.reranker_service = QwenRerankerService()
        self._initialized = False
    
    async def initialize(self):
        """初始化所有模型"""
        if self._initialized:
            return
        
        try:
            # 并行初始化模型
            await asyncio.gather(
                self.embedding_service.initialize(),
                self.reranker_service.initialize(),
                return_exceptions=True
            )
            
            self._initialized = True
            logger.info("通义千问模型管理器初始化完成")
            
        except Exception as e:
            logger.error(f"模型管理器初始化失败: {e}")
            raise
    
    async def get_embedding_service(self) -> QwenEmbeddingService:
        """获取嵌入服务"""
        if not self._initialized:
            await self.initialize()
        return self.embedding_service
    
    async def get_reranker_service(self) -> QwenRerankerService:
        """获取重排服务"""
        if not self._initialized:
            await self.initialize()
        return self.reranker_service


# 全局模型管理器实例
qwen_model_manager = QwenModelManager()
