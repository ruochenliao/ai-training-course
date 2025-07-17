"""
统一的大模型客户端管理器
支持多种模型提供商，提供统一的访问接口
"""
import logging
from typing import Dict, Optional, Any, Union
from enum import Enum

from autogen_core.models import ChatCompletionClient, ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient

from app.config.base import settings

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    # 未来可以添加更多提供商
    # ANTHROPIC = "anthropic"
    # AZURE = "azure"
    # GOOGLE = "google"


class ModelClientManager:
    """大模型客户端管理器"""
    
    def __init__(self):
        self._clients: Dict[str, ChatCompletionClient] = {}
        self._default_provider = settings.default_model_provider
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化所有可用的模型客户端"""
        try:
            # 初始化DeepSeek客户端
            if settings.deepseek_api_key:
                self._clients[ModelProvider.DEEPSEEK] = self._create_deepseek_client()
                logger.info("DeepSeek客户端初始化成功")
            else:
                logger.warning("DeepSeek API Key未配置，跳过DeepSeek客户端初始化")
            
            # 初始化OpenAI客户端
            if settings.openai_api_key:
                self._clients[ModelProvider.OPENAI] = self._create_openai_client()
                logger.info("OpenAI客户端初始化成功")
            else:
                logger.warning("OpenAI API Key未配置，跳过OpenAI客户端初始化")
            
            # 检查是否有可用的客户端
            if not self._clients:
                logger.error("没有可用的模型客户端，请检查API Key配置")
                
        except Exception as e:
            logger.error(f"模型客户端初始化失败: {e}")
    
    def _create_deepseek_client(self) -> OpenAIChatCompletionClient:
        """创建DeepSeek客户端"""
        if not settings.deepseek_api_key:
            raise ValueError("DeepSeek API Key未配置")

        return OpenAIChatCompletionClient(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": True,
                "family": ModelFamily.UNKNOWN,
                "multiple_system_messages": True
            }
        )
    
    def _create_openai_client(self) -> OpenAIChatCompletionClient:
        """创建OpenAI客户端"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API Key未配置")

        return OpenAIChatCompletionClient(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model_info={
                "vision": False,
                "function_calling": True,
                "json_output": True,
                "structured_output": True,
                "family": ModelFamily.GPT_4O,
                "multiple_system_messages": True
            }
        )
    
    def get_client(self, provider: Optional[str] = None, model_name: Optional[str] = None) -> ChatCompletionClient:
        """
        获取模型客户端
        
        Args:
            provider: 模型提供商，如果为None则使用默认提供商
            model_name: 模型名称，用于选择合适的提供商
            
        Returns:
            ChatCompletionClient: 模型客户端实例
            
        Raises:
            ValueError: 当指定的提供商不可用时
        """
        # 如果指定了模型名称，尝试根据模型名称推断提供商
        if model_name and not provider:
            provider = self._infer_provider_from_model(model_name)
        
        # 使用指定的提供商或默认提供商
        target_provider = provider or self._default_provider
        
        # 获取客户端
        client = self._clients.get(target_provider)
        if client is None:
            # 如果指定的提供商不可用，尝试使用任何可用的客户端
            if self._clients:
                available_provider = next(iter(self._clients.keys()))
                logger.warning(f"提供商 {target_provider} 不可用，使用 {available_provider}")
                return self._clients[available_provider]
            else:
                raise ValueError("没有可用的模型客户端")
        
        return client
    
    def _infer_provider_from_model(self, model_name: str) -> str:
        """根据模型名称推断提供商"""
        model_name_lower = model_name.lower()
        
        if "deepseek" in model_name_lower:
            return ModelProvider.DEEPSEEK
        elif any(prefix in model_name_lower for prefix in ["gpt-", "text-", "davinci", "curie", "babbage", "ada"]):
            return ModelProvider.OPENAI
        else:
            # 默认返回默认提供商
            return self._default_provider
    
    def get_default_client(self) -> ChatCompletionClient:
        """获取默认模型客户端"""
        return self.get_client()
    
    def get_deepseek_client(self) -> ChatCompletionClient:
        """获取DeepSeek客户端"""
        return self.get_client(ModelProvider.DEEPSEEK)
    
    def get_openai_client(self) -> ChatCompletionClient:
        """获取OpenAI客户端"""
        return self.get_client(ModelProvider.OPENAI)
    
    def list_available_providers(self) -> list[str]:
        """列出所有可用的提供商"""
        return list(self._clients.keys())
    
    def is_provider_available(self, provider: str) -> bool:
        """检查指定的提供商是否可用"""
        return provider in self._clients
    
    def reload_clients(self):
        """重新加载所有客户端"""
        self._clients.clear()
        self._initialize_clients()
    
    def get_model_info(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """获取模型信息"""
        target_provider = provider or self._default_provider
        
        if target_provider == ModelProvider.DEEPSEEK:
            return {
                "provider": "DeepSeek",
                "model": settings.deepseek_model,
                "base_url": settings.deepseek_base_url,
                "max_tokens": settings.deepseek_max_tokens,
                "temperature": settings.deepseek_temperature,
                "supports_function_calling": True,
                "supports_json_output": True
            }
        elif target_provider == ModelProvider.OPENAI:
            return {
                "provider": "OpenAI",
                "model": settings.openai_model,
                "base_url": settings.openai_base_url,
                "max_tokens": settings.openai_max_tokens,
                "temperature": settings.openai_temperature,
                "supports_function_calling": True,
                "supports_json_output": True
            }
        else:
            return {"error": f"未知的提供商: {target_provider}"}


# 全局模型客户端管理器实例
model_client_manager = ModelClientManager()


# 便捷函数
def get_default_model_client() -> ChatCompletionClient:
    """获取默认模型客户端"""
    return model_client_manager.get_default_client()


def get_model_client(provider: Optional[str] = None, model_name: Optional[str] = None) -> ChatCompletionClient:
    """获取指定的模型客户端"""
    return model_client_manager.get_client(provider, model_name)


def get_deepseek_model_client() -> ChatCompletionClient:
    """获取DeepSeek模型客户端"""
    return model_client_manager.get_deepseek_client()


def get_openai_model_client() -> ChatCompletionClient:
    """获取OpenAI模型客户端"""
    return model_client_manager.get_openai_client()


def list_available_model_providers() -> list[str]:
    """列出所有可用的模型提供商"""
    return model_client_manager.list_available_providers()


def get_model_info(provider: Optional[str] = None) -> Dict[str, Any]:
    """获取模型信息"""
    return model_client_manager.get_model_info(provider)
