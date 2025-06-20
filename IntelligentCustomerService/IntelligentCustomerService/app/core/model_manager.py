"""
模型服务管理器
统一管理所有AI模型服务，包括大语言模型、多模态模型、嵌入模型等
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator, Union
from datetime import datetime
from enum import Enum
import json

from openai import AsyncOpenAI
from modelscope import snapshot_download
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """模型类型枚举"""
    LLM = "llm"  # 大语言模型
    MULTIMODAL = "multimodal"  # 多模态模型
    EMBEDDING = "embedding"  # 嵌入模型
    RERANK = "rerank"  # 重排模型


class ModelStatus(Enum):
    """模型状态枚举"""
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    OFFLINE = "offline"


class ModelService:
    """单个模型服务基类"""
    
    def __init__(self, model_name: str, model_type: ModelType, config: Dict[str, Any]):
        self.model_name = model_name
        self.model_type = model_type
        self.config = config
        self.status = ModelStatus.OFFLINE
        self.created_at = datetime.now()
        self.last_used = None
        self.usage_count = 0
        self.error_count = 0
        
    async def load(self):
        """加载模型"""
        self.status = ModelStatus.LOADING
        try:
            await self._load_model()
            self.status = ModelStatus.READY
            logger.info(f"模型 {self.model_name} 加载成功")
        except Exception as e:
            self.status = ModelStatus.ERROR
            logger.error(f"模型 {self.model_name} 加载失败: {str(e)}")
            raise
    
    async def _load_model(self):
        """子类实现具体的模型加载逻辑"""
        pass
    
    def is_ready(self) -> bool:
        """检查模型是否就绪"""
        return self.status == ModelStatus.READY
    
    def update_usage(self):
        """更新使用统计"""
        self.usage_count += 1
        self.last_used = datetime.now()


class LLMService(ModelService):
    """大语言模型服务"""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, ModelType.LLM, config)
        self.client = None
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.default_params = config.get('default_params', {})
    
    async def _load_model(self):
        """加载LLM模型"""
        if not self.api_key:
            raise ValueError(f"模型 {self.model_name} 缺少API密钥")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # 测试连接
        try:
            await self.client.models.list()
        except Exception as e:
            raise ConnectionError(f"无法连接到模型服务: {str(e)}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """聊天补全"""
        if not self.is_ready():
            raise RuntimeError(f"模型 {self.model_name} 未就绪")
        
        try:
            self.update_usage()
            
            # 合并默认参数和传入参数
            params = {**self.default_params, **kwargs}
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **params
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"LLM聊天补全失败: {str(e)}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式聊天补全"""
        if not self.is_ready():
            raise RuntimeError(f"模型 {self.model_name} 未就绪")
        
        try:
            self.update_usage()
            
            # 合并默认参数和传入参数
            params = {**self.default_params, **kwargs}
            params['stream'] = True
            
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **params
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            self.error_count += 1
            logger.error(f"LLM流式聊天补全失败: {str(e)}")
            raise


class MultimodalService(ModelService):
    """多模态模型服务"""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, ModelType.MULTIMODAL, config)
        self.client = None
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
    
    async def _load_model(self):
        """加载多模态模型"""
        if not self.api_key:
            raise ValueError(f"模型 {self.model_name} 缺少API密钥")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def analyze_image(
        self,
        image_data: Union[str, bytes],
        prompt: str = "请描述这张图片",
        **kwargs
    ) -> str:
        """分析图片"""
        if not self.is_ready():
            raise RuntimeError(f"模型 {self.model_name} 未就绪")
        
        try:
            self.update_usage()
            
            # 构建多模态消息
            if isinstance(image_data, bytes):
                import base64
                image_url = f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"
            else:
                image_url = image_data
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **kwargs
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"图片分析失败: {str(e)}")
            raise


class EmbeddingService(ModelService):
    """嵌入模型服务"""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, ModelType.EMBEDDING, config)
        self.tokenizer = None
        self.model = None
        self.device = config.get('device', 'cpu')
        self.max_length = config.get('max_length', 512)
        self.model_path = None
    
    async def _load_model(self):
        """加载嵌入模型"""
        try:
            # 从ModelScope下载模型
            self.model_path = snapshot_download(
                self.model_name,
                cache_dir=self.config.get('cache_dir', './models')
            )
            
            # 加载tokenizer和模型
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModel.from_pretrained(self.model_path)
            
            # 移动到指定设备
            if torch.cuda.is_available() and self.device == 'cuda':
                self.model = self.model.cuda()
            
            self.model.eval()
            
        except Exception as e:
            raise RuntimeError(f"嵌入模型加载失败: {str(e)}")
    
    async def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """文本编码为向量"""
        if not self.is_ready():
            raise RuntimeError(f"模型 {self.model_name} 未就绪")
        
        try:
            self.update_usage()
            
            if isinstance(texts, str):
                texts = [texts]
            
            embeddings = []
            
            # 批量处理
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Tokenize
                inputs = self.tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors='pt'
                )
                
                # 移动到设备
                if self.device == 'cuda' and torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                
                # 推理
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # 使用[CLS]token的embedding或者平均池化
                    batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                
                embeddings.append(batch_embeddings)
            
            # 合并所有批次的结果
            all_embeddings = np.vstack(embeddings)
            
            # 归一化
            if normalize:
                norms = np.linalg.norm(all_embeddings, axis=1, keepdims=True)
                all_embeddings = all_embeddings / norms
            
            return all_embeddings
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"文本编码失败: {str(e)}")
            raise


class RerankService(ModelService):
    """重排模型服务"""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, ModelType.RERANK, config)
        self.tokenizer = None
        self.model = None
        self.device = config.get('device', 'cpu')
        self.max_length = config.get('max_length', 512)
        self.model_path = None
    
    async def _load_model(self):
        """加载重排模型"""
        try:
            # 从ModelScope下载模型
            self.model_path = snapshot_download(
                self.model_name,
                cache_dir=self.config.get('cache_dir', './models')
            )
            
            # 加载tokenizer和模型
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModel.from_pretrained(self.model_path)
            
            # 移动到指定设备
            if torch.cuda.is_available() and self.device == 'cuda':
                self.model = self.model.cuda()
            
            self.model.eval()
            
        except Exception as e:
            raise RuntimeError(f"重排模型加载失败: {str(e)}")
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """重排文档"""
        if not self.is_ready():
            raise RuntimeError(f"模型 {self.model_name} 未就绪")
        
        try:
            self.update_usage()
            
            scores = []
            
            for doc in documents:
                # 构建query-document对
                inputs = self.tokenizer(
                    query,
                    doc,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors='pt'
                )
                
                # 移动到设备
                if self.device == 'cuda' and torch.cuda.is_available():
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                
                # 推理
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # 获取相关性分数
                    score = torch.sigmoid(outputs.logits).item()
                
                scores.append(score)
            
            # 构建结果
            results = [
                {
                    'document': doc,
                    'score': score,
                    'index': idx
                }
                for idx, (doc, score) in enumerate(zip(documents, scores))
            ]
            
            # 按分数排序
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # 返回top_k结果
            if top_k:
                results = results[:top_k]
            
            return results
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"文档重排失败: {str(e)}")
            raise


class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        self.models: Dict[str, ModelService] = {}
        self.default_models: Dict[ModelType, str] = {}
        self.config = {}
        
        logger.info("模型管理器初始化完成")
    
    def load_config(self, config: Dict[str, Any]):
        """加载配置"""
        self.config = config
        
        # 设置默认模型
        self.default_models = {
            ModelType.LLM: config.get('default_llm', 'deepseek-chat'),
            ModelType.MULTIMODAL: config.get('default_multimodal', 'qwen-vl-max'),
            ModelType.EMBEDDING: config.get('default_embedding', 'Qwen/Qwen3-0.6B'),
            ModelType.RERANK: config.get('default_rerank', 'Qwen/Qwen3-Reranker-0.6B')
        }
    
    async def register_model(
        self,
        model_name: str,
        model_type: ModelType,
        config: Dict[str, Any]
    ):
        """注册模型"""
        try:
            # 创建模型服务
            if model_type == ModelType.LLM:
                service = LLMService(model_name, config)
            elif model_type == ModelType.MULTIMODAL:
                service = MultimodalService(model_name, config)
            elif model_type == ModelType.EMBEDDING:
                service = EmbeddingService(model_name, config)
            elif model_type == ModelType.RERANK:
                service = RerankService(model_name, config)
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
            
            # 加载模型
            await service.load()
            
            # 注册到管理器
            self.models[model_name] = service
            
            logger.info(f"模型 {model_name} ({model_type.value}) 注册成功")
            
        except Exception as e:
            logger.error(f"模型 {model_name} 注册失败: {str(e)}")
            raise
    
    def get_model(self, model_name: str) -> Optional[ModelService]:
        """获取模型服务"""
        return self.models.get(model_name)
    
    def get_default_model(self, model_type: ModelType) -> Optional[ModelService]:
        """获取默认模型"""
        default_name = self.default_models.get(model_type)
        if default_name:
            return self.get_model(default_name)
        return None
    
    def list_models(self, model_type: Optional[ModelType] = None) -> List[Dict[str, Any]]:
        """列出模型"""
        models = []
        for name, service in self.models.items():
            if model_type is None or service.model_type == model_type:
                models.append({
                    'name': name,
                    'type': service.model_type.value,
                    'status': service.status.value,
                    'usage_count': service.usage_count,
                    'error_count': service.error_count,
                    'last_used': service.last_used.isoformat() if service.last_used else None
                })
        return models
    
    async def switch_default_model(self, model_type: ModelType, model_name: str):
        """切换默认模型"""
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未注册")
        
        service = self.models[model_name]
        if service.model_type != model_type:
            raise ValueError(f"模型类型不匹配: {service.model_type} != {model_type}")
        
        self.default_models[model_type] = model_name
        logger.info(f"切换默认{model_type.value}模型为: {model_name}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            'total_models': len(self.models),
            'ready_models': 0,
            'error_models': 0,
            'models': []
        }
        
        for name, service in self.models.items():
            model_health = {
                'name': name,
                'type': service.model_type.value,
                'status': service.status.value,
                'is_healthy': service.status == ModelStatus.READY and service.error_count < 10
            }
            
            health_status['models'].append(model_health)
            
            if service.status == ModelStatus.READY:
                health_status['ready_models'] += 1
            elif service.status == ModelStatus.ERROR:
                health_status['error_models'] += 1
        
        return health_status


# 全局模型管理器实例
model_manager = ModelManager()
