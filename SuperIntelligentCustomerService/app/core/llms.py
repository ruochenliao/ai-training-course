# -*- coding: utf-8 -*-
"""
LLM模型客户端管理器
基于数据库配置动态创建和管理模型客户端
"""
from typing import Dict, Optional, List

from autogen_core.models import ModelInfo, ModelFamily, ChatCompletionClient
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import _MODEL_INFO, _MODEL_TOKEN_LIMITS


class LLMModelClientManager:
    """LLM模型客户端管理器"""

    def __init__(self):
        self._clients: Dict[str, ChatCompletionClient] = {}
        self._model_info_cache: Dict[str, ModelInfo] = {}
        self._initialized = False

    async def initialize(self):
        """初始化模型客户端管理器"""
        if self._initialized:
            return

        # 只从数据库加载模型，不使用硬编码配置
        success = await self.load_models_from_database()
        if not success:
            print("❌ 数据库中没有可用的模型配置，请先初始化模型数据")
            print("💡 提示：可以通过管理界面添加模型配置，或运行数据初始化脚本")

        self._initialized = True

    async def load_models_from_database(self):
        """从数据库重新加载模型配置（用于热重载）"""
        try:
            from tortoise import Tortoise
            if not Tortoise._inited:
                print("数据库未初始化，无法重新加载")
                return False

            from ..models.llm_models import LLMModel
            models = await LLMModel.filter(is_active=True).order_by("sort_order", "display_name")

            if not models:
                print("数据库中没有找到模型配置")
                return False

            # 清空现有客户端
            self._clients.clear()
            self._model_info_cache.clear()

            for model in models:
                try:
                    # 创建模型信息
                    model_info = ModelInfo(
                        vision=model.vision,
                        function_calling=model.function_calling,
                        json_output=model.json_output,
                        structured_output=model.structured_output,
                        multiple_system_messages=model.multiple_system_messages,
                        family=ModelFamily.UNKNOWN
                    )

                    # 解密API密钥
                    from ..utils.security import decrypt_api_key
                    api_key = decrypt_api_key(model.api_key) if model.api_key else ""

                    # 创建客户端
                    client = OpenAIChatCompletionClient(
                        model=model.model_name,
                        base_url=model.base_url,
                        api_key=api_key,
                        model_info=model_info,
                        temperature=model.temperature,
                        top_p=model.top_p,
                        max_tokens=model.max_tokens
                    )

                    # 注册客户端
                    client_key = f"{model.provider_name}:{model.model_name}"
                    self._clients[client_key] = client
                    self._clients[model.model_name] = client

                    # 缓存模型信息
                    self._model_info_cache[model.model_name] = model_info

                    # 更新全局模型信息
                    _MODEL_INFO[model.model_name] = model_info
                    _MODEL_TOKEN_LIMITS[model.model_name] = model.max_tokens

                    print(f"✅ 加载模型: {model.display_name}")

                except Exception as e:
                    print(f"❌ 加载模型失败 {model.model_name}: {e}")
                    continue

            print(f"✅ 从数据库加载了 {len(self._clients)} 个模型客户端")
            return True

        except Exception as e:
            print(f"❌ 从数据库加载模型失败: {e}")
            return False

    async def get_client(self, model_name: str) -> Optional[ChatCompletionClient]:
        """获取模型客户端"""
        if not self._initialized:
            await self.initialize()

        return self._clients.get(model_name)

    async def get_default_client(self) -> Optional[ChatCompletionClient]:
        """获取默认模型客户端"""
        if not self._initialized:
            await self.initialize()

        # 从数据库查询默认模型
        from tortoise import Tortoise
        if Tortoise._inited:
            from ..models.llm_models import LLMModel
            default_model = await LLMModel.filter(is_active=True, is_default=True).first()
            if default_model:
                return self._clients.get(default_model.model_name)

        # 如果没有设置默认模型，返回第一个可用的客户端
        return next(iter(self._clients.values()), None)

    async def list_available_models(self) -> List[str]:
        """列出所有可用的模型"""
        if not self._initialized:
            await self.initialize()

        # 直接从数据库查询活跃的模型
        from tortoise import Tortoise
        if Tortoise._inited:
            from ..models.llm_models import LLMModel
            models = await LLMModel.filter(is_active=True).order_by("sort_order", "display_name")
            return [model.model_name for model in models]

        return []

    async def reload_models(self):
        """重新加载模型配置（从数据库）"""
        success = await self.load_models_from_database()
        if not success:
            print("❌ 重新加载模型失败：数据库中没有可用的模型配置")
        return success


# 创建全局模型客户端管理器实例
model_client_manager = LLMModelClientManager()


# 核心API函数
async def get_model_client(model_name: str) -> Optional[ChatCompletionClient]:
    """获取指定的模型客户端"""
    return await model_client_manager.get_client(model_name)


async def get_default_model_client() -> Optional[ChatCompletionClient]:
    """获取默认模型客户端"""
    return await model_client_manager.get_default_client()


async def list_available_models() -> List[str]:
    """列出所有可用的模型"""
    return await model_client_manager.list_available_models()


async def initialize_llm_clients():
    """初始化LLM客户端"""
    await model_client_manager.initialize()
    print("✅ LLM客户端管理器初始化完成")
