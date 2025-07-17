# -*- coding: utf-8 -*-
"""
@Time ： 2025/4/29 20:46
@Author ：楚地仁人
@File ：llms.py
@IDE ：PyCharm

"""
from typing import Dict

from autogen_core.models import ModelInfo, ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import _MODEL_INFO, _MODEL_TOKEN_LIMITS

# 定义Deepseek模型信息
deepseek_model_info = ModelInfo(
    vision=False,  # 不支持视觉功能
    function_calling=True,  # 支持函数调用
    json_output=True,  # 支持JSON输出
    structured_output=True,  # 支持结构化输出
    family=ModelFamily.UNKNOWN,  # 模型系列为未知
)

# Deepseek模型配置字典
DEEPSEEK_MODELS: Dict[str, ModelInfo] = {
    "deepseek-chat": deepseek_model_info,  # 将模型信息关联到deepseek-chat模型
}

# Deepseek模型的令牌限制
DEEPSEEK_TOKEN_LIMITS: Dict[str, int] = {
    "deepseek-chat": 128000,  # 设置最大令牌数为128000
}

# 更新全局模型信息和令牌限制
_MODEL_INFO.update(DEEPSEEK_MODELS)
_MODEL_TOKEN_LIMITS.update(DEEPSEEK_TOKEN_LIMITS)

# 创建OpenAI兼容的聊天完成客户端
model_client = OpenAIChatCompletionClient(
    model="deepseek-chat",  # 使用的模型名称
    base_url="https://api.deepseek.com/v1",  # Deepseek API的基础URL
    api_key="sk-56f5743d59364543a00109a4c1c10a56",  # API密钥
    model_info=deepseek_model_info,  # 指定模型信息
)

# 创建支持视觉的模型客户端
deepseek_vl_model_info = ModelInfo(
    vision=True,  # 支持视觉功能
    function_calling=True,  # 支持函数调用
    json_output=True,  # 支持JSON输出
    structured_output=True,  # 支持结构化输出
    family=ModelFamily.UNKNOWN,  # 模型系列为未知
)

# 更新视觉模型信息
DEEPSEEK_VL_MODELS: Dict[str, ModelInfo] = {
    "deepseek-vl-chat": deepseek_vl_model_info,
}

DEEPSEEK_VL_TOKEN_LIMITS: Dict[str, int] = {
    "deepseek-vl-chat": 128000,
}

_MODEL_INFO.update(DEEPSEEK_VL_MODELS)
_MODEL_TOKEN_LIMITS.update(DEEPSEEK_VL_TOKEN_LIMITS)

# 创建支持视觉的模型客户端
vllm_model_client = OpenAIChatCompletionClient(
    model="deepseek-vl-chat",
    base_url="https://api.deepseek.com/v1",
    api_key="sk-56f5743d59364543a00109a4c1c10a56",
    model_info=deepseek_vl_model_info,
)
