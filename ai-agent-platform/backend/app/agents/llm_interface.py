"""
LLM接口封装

提供统一的LLM调用接口，支持多种模型切换和错误处理。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from abc import ABC, abstractmethod
import openai
from openai import AsyncOpenAI
import json
import time
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMResponse:
    """LLM响应模型"""
    
    def __init__(self, content: str, model: str, usage: Dict[str, int] = None, 
                 metadata: Dict[str, Any] = None):
        self.content = content
        self.model = model
        self.usage = usage or {}
        self.metadata = metadata or {}
        self.timestamp = time.time()


class BaseLLMProvider(ABC):
    """LLM提供者基类"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本"""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """对话生成"""
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """流式对话生成"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI提供者"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.client = AsyncOpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=base_url or settings.OPENAI_BASE_URL
        )
    
    async def generate(self, prompt: str, model: str = "gpt-4o", 
                      temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> LLMResponse:
        """生成文本"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(content=content, model=model, usage=usage)
            
        except Exception as e:
            logger.error(f"OpenAI生成失败: {e}")
            raise
    
    async def generate_stream(self, prompt: str, model: str = "gpt-4o", 
                             temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        try:
            messages = [{"role": "user", "content": prompt}]
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI流式生成失败: {e}")
            raise
    
    async def chat(self, messages: List[Dict[str, str]], model: str = "gpt-4o", 
                  temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> LLMResponse:
        """对话生成"""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(content=content, model=model, usage=usage)
            
        except Exception as e:
            logger.error(f"OpenAI对话生成失败: {e}")
            raise
    
    async def chat_stream(self, messages: List[Dict[str, str]], model: str = "gpt-4o", 
                         temperature: float = 0.7, max_tokens: int = 4000, **kwargs) -> AsyncGenerator[str, None]:
        """流式对话生成"""
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI流式对话生成失败: {e}")
            raise


class LLMManager:
    """LLM管理器"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider = "openai"
        
        # 初始化默认提供者
        self.register_provider("openai", OpenAIProvider())
    
    def register_provider(self, name: str, provider: BaseLLMProvider):
        """注册LLM提供者"""
        self.providers[name] = provider
        logger.info(f"注册LLM提供者: {name}")
    
    def get_provider(self, name: str = None) -> BaseLLMProvider:
        """获取LLM提供者"""
        provider_name = name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"未找到LLM提供者: {provider_name}")
        return self.providers[provider_name]
    
    async def generate(self, prompt: str, provider: str = None, **kwargs) -> LLMResponse:
        """生成文本"""
        llm_provider = self.get_provider(provider)
        return await llm_provider.generate(prompt, **kwargs)
    
    async def generate_stream(self, prompt: str, provider: str = None, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        llm_provider = self.get_provider(provider)
        async for chunk in llm_provider.generate_stream(prompt, **kwargs):
            yield chunk
    
    async def chat(self, messages: List[Dict[str, str]], provider: str = None, **kwargs) -> LLMResponse:
        """对话生成"""
        llm_provider = self.get_provider(provider)
        return await llm_provider.chat(messages, **kwargs)
    
    async def chat_stream(self, messages: List[Dict[str, str]], provider: str = None, **kwargs) -> AsyncGenerator[str, None]:
        """流式对话生成"""
        llm_provider = self.get_provider(provider)
        async for chunk in llm_provider.chat_stream(messages, **kwargs):
            yield chunk
    
    def list_providers(self) -> List[str]:
        """列出所有提供者"""
        return list(self.providers.keys())


# 全局LLM管理器
llm_manager = LLMManager()


class LLMRetryMixin:
    """LLM重试混入类"""
    
    async def call_with_retry(self, func, max_retries: int = 3, delay: float = 1.0, **kwargs):
        """带重试的LLM调用"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await func(**kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"LLM调用失败，第{attempt + 1}次重试: {e}")
                    await asyncio.sleep(delay * (2 ** attempt))  # 指数退避
                else:
                    logger.error(f"LLM调用失败，已达到最大重试次数: {e}")
        
        raise last_exception


class TokenCounter:
    """Token计数器"""
    
    @staticmethod
    def count_tokens(text: str, model: str = "gpt-4o") -> int:
        """估算token数量"""
        # 简单估算：1个token约等于4个字符（英文）或1.5个字符（中文）
        # 这是一个粗略估算，实际应该使用tiktoken库
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            # 包含中文
            return int(len(text) / 1.5)
        else:
            # 纯英文
            return int(len(text) / 4)
    
    @staticmethod
    def truncate_text(text: str, max_tokens: int, model: str = "gpt-4o") -> str:
        """截断文本到指定token数量"""
        current_tokens = TokenCounter.count_tokens(text, model)
        if current_tokens <= max_tokens:
            return text
        
        # 按比例截断
        ratio = max_tokens / current_tokens
        truncate_length = int(len(text) * ratio * 0.9)  # 留一些余量
        return text[:truncate_length] + "..."
