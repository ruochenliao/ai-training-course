# -*- coding: utf-8 -*-
"""
LLM模型统一配置
所有LLM模型的配置都在这里定义，避免重复维护
"""
from typing import List, Dict, Any

# 统一的LLM模型配置数据
LLM_MODELS_CONFIG: List[Dict[str, Any]] = [
    {
        "provider_name": "deepseek",
        "provider_display_name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "sk-bc51a0cbd90a43f9bcee3736678af370",
        "model_name": "deepseek-chat",
        "display_name": "DeepSeek Chat",
        "description": "DeepSeek Chat模型，适合日常对话和函数调用",
        "category": "文本模型",
        "vision": False,
        "function_calling": True,
        "json_output": False,
        "structured_output": False,
        "multiple_system_messages": True,
        "model_family": "unknown",
        "max_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.9,
        "input_price_per_1k": 0.0014,
        "output_price_per_1k": 0.0028,
        "system_prompt": """你是专业的智能客服助手，友好、耐心、乐于助人。请用中文回复用户问题，使用清晰的Markdown格式。""",
        "custom_config": {},
        "is_active": True,
        "is_default": True,
        "sort_order": 1
    },
    {
        "provider_name": "deepseek",
        "provider_display_name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "sk-bc51a0cbd90a43f9bcee3736678af370",
        "model_name": "deepseek-reasoner",
        "display_name": "DeepSeek Reasoner",
        "description": "DeepSeek Reasoner模型，具备强大的推理能力，适合复杂逻辑分析",
        "category": "推理模型",
        "vision": False,
        "function_calling": True,
        "json_output": False,
        "structured_output": False,
        "multiple_system_messages": True,
        "model_family": "unknown",
        "max_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.9,
        "input_price_per_1k": 0.0055,
        "output_price_per_1k": 0.022,
        "system_prompt": """你是专业的智能推理客服助手，具备强大的逻辑分析能力。请用中文回复用户问题，展示清晰的推理过程，使用Markdown格式。""",
        "custom_config": {},
        "is_active": True,
        "is_default": False,
        "sort_order": 2
    },
    {
        "provider_name": "qwen",
        "provider_display_name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": "sk-aeb8d69039b14320b0fe58cb8285d8b1",
        "model_name": "qwen-vl-plus",
        "display_name": "通义千问 VL Plus",
        "description": "通义千问视觉语言模型，支持图像理解和多模态对话",
        "category": "多模态模型",
        "vision": True,
        "function_calling": False,
        "json_output": False,
        "structured_output": False,
        "multiple_system_messages": True,
        "model_family": "unknown",
        "max_tokens": 8192,
        "temperature": 0.7,
        "top_p": 0.9,
        "input_price_per_1k": 0.008,
        "output_price_per_1k": 0.008,
        "system_prompt": """你是专业的多模态智能客服助手，可以理解图像内容。请用中文回复用户问题，准确分析图像信息，使用Markdown格式。""",
        "custom_config": {},
        "is_active": True,
        "is_default": False,
        "sort_order": 3
    }
]


def get_llm_models_config() -> List[Dict[str, Any]]:
    """获取LLM模型配置"""
    return LLM_MODELS_CONFIG


def get_model_config_by_name(model_name: str) -> Dict[str, Any]:
    """根据模型名称获取配置"""
    for config in LLM_MODELS_CONFIG:
        if config["model_name"] == model_name:
            return config
    return None


def get_default_model_config() -> Dict[str, Any]:
    """获取默认模型配置"""
    for config in LLM_MODELS_CONFIG:
        if config.get("is_default", False):
            return config
    # 如果没有设置默认模型，返回第一个
    return LLM_MODELS_CONFIG[0] if LLM_MODELS_CONFIG else None
