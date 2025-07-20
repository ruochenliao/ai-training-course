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

        # 直接使用默认配置，简化启动流程
        await self._create_default_clients()
        self._initialized = True

    async def load_models_from_database(self):
        """从数据库重新加载模型配置（用于热重载）"""
        try:
            from tortoise import Tortoise
            if not Tortoise._inited:
                print("数据库未初始化，无法重新加载")
                return False

            from ..models.llm_models import LLMModel
            models = await LLMModel.filter(is_active=True).prefetch_related("provider").order_by("sort_order", "display_name")

            if not models:
                print("数据库中没有找到模型配置")
                return False

            # 清空现有客户端
            self._clients.clear()
            self._model_info_cache.clear()

            for model in models:
                try:
                    provider = await model.provider

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
                    api_key = decrypt_api_key(provider.api_key) if provider.api_key else ""

                    # 创建客户端
                    client = OpenAIChatCompletionClient(
                        model=model.model_name,
                        base_url=provider.base_url,
                        api_key=api_key,
                        model_info=model_info,
                        temperature=model.temperature,
                        top_p=model.top_p,
                        max_tokens=model.max_tokens
                    )

                    # 注册客户端
                    client_key = f"{provider.name}:{model.model_name}"
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

    async def _create_default_clients(self):
        """创建默认的模型客户端（兼容原有配置）"""
        # 定义Deepseek模型信息（基于实际验证结果）
        deepseek_model_info = ModelInfo(
            vision=False,  # 不支持视觉功能
            function_calling=True,  # ✅ 验证支持函数调用
            json_output=False,  # ❌ API不支持结构化输出
            structured_output=False,  # ❌ API不支持结构化输出
            family=ModelFamily.UNKNOWN,  # 模型系列为未知
        )

        # 创建Deepseek客户端
        deepseek_chat_client = OpenAIChatCompletionClient(
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            api_key="sk-56f5743d59364543a00109a4c1c10a56",
            model_info=deepseek_model_info,
        )

        deepseek_reasoner_client = OpenAIChatCompletionClient(
            model="deepseek-reasoner",
            base_url="https://api.deepseek.com/v1",
            api_key="sk-56f5743d59364543a00109a4c1c10a56",
            model_info=deepseek_model_info,
        )

        # 创建Qwen VL Plus客户端
        qwen_vl_plus_model_info = ModelInfo(
            vision=True,  # ✅ 理论支持视觉功能
            function_calling=False,  # ❌ 验证中模型没有返回函数调用
            json_output=False,  # ❌ 返回文本而非JSON格式
            structured_output=False,  # ❌ 不支持结构化输出
            family=ModelFamily.UNKNOWN,  # 模型系列为未知
        )

        qwen_vl_plus_client = OpenAIChatCompletionClient(
            model="qwen-vl-plus",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="sk-aeb8d69039b14320b0fe58cb8285d8b1",
            model_info=qwen_vl_plus_model_info,
        )

        # 注册客户端
        self._clients["deepseek:deepseek-chat"] = deepseek_chat_client
        self._clients["deepseek-chat"] = deepseek_chat_client
        self._clients["deepseek:deepseek-reasoner"] = deepseek_reasoner_client
        self._clients["deepseek-reasoner"] = deepseek_reasoner_client
        self._clients["qwen:qwen-vl-plus"] = qwen_vl_plus_client
        self._clients["qwen-vl-plus"] = qwen_vl_plus_client

        # 缓存模型信息
        self._model_info_cache["deepseek-chat"] = deepseek_model_info
        self._model_info_cache["deepseek-reasoner"] = deepseek_model_info
        self._model_info_cache["qwen-vl-plus"] = qwen_vl_plus_model_info

        # 更新全局模型信息
        _MODEL_INFO.update({
            "deepseek-chat": deepseek_model_info,
            "deepseek-reasoner": deepseek_model_info,
            "qwen-vl-plus": qwen_vl_plus_model_info,
        })

        _MODEL_TOKEN_LIMITS.update({
            "deepseek-chat": 128000,
            "deepseek-reasoner": 128000,
            "qwen-vl-plus": 128000,
        })

    async def get_client(self, model_name: str) -> Optional[ChatCompletionClient]:
        """获取模型客户端"""
        if not self._initialized:
            await self.initialize()

        return self._clients.get(model_name)

    async def get_default_client(self) -> Optional[ChatCompletionClient]:
        """获取默认模型客户端"""
        if not self._initialized:
            await self.initialize()

        # 优先返回deepseek-chat作为默认客户端
        return self._clients.get("deepseek-chat") or next(iter(self._clients.values()), None)

    async def list_available_models(self) -> List[str]:
        """列出所有可用的模型"""
        if not self._initialized:
            await self.initialize()

        return list(self._clients.keys())

    async def reload_models(self):
        """重新加载模型配置（从数据库）"""
        success = await self.load_models_from_database()
        if not success:
            # 如果数据库加载失败，回退到默认配置
            await self._create_default_clients()
        return success

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        return self._model_info_cache.get(model_name)


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


async def reload_llm_models():
    """重新加载LLM模型配置"""
    return await model_client_manager.reload_models()
