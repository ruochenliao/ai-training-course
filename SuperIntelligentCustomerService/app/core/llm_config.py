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
        "api_key": "sk-56f5743d59364543a00109a4c1c10a56",
        "model_name": "deepseek-chat",
        "display_name": "DeepSeek Chat",
        "description": "DeepSeek Chat模型，适合日常对话和函数调用",
        "category": "文本模型",
        "vision": False,
        "function_calling": True,
        "json_output": False,
        "structured_output": False,
        "multiple_system_messages": False,
        "model_family": "unknown",
        "max_tokens": 128000,
        "temperature": 0.7,
        "top_p": 0.9,
        "input_price_per_1k": 0.0014,
        "output_price_per_1k": 0.0028,
        "system_prompt": """你是超级智能客服，专业、友好、乐于助人。你可以用中文回复用户的问题。

## 重要格式要求：
**必须使用标准 Markdown 格式**输出所有回复，特别注意：

1. **代码块格式**：
```语言名称
代码内容（必须有正确的换行符和缩进）
```

2. **确保代码块内容格式化良好**：
   - 每行代码独立成行
   - 保持正确的缩进
   - 包含适当的注释
   - 不要将所有代码挤在一行

3. **使用适当的 Markdown 语法**：
   - 标题：# ## ###
   - 列表：- 或 1.
   - 强调：**粗体** *斜体*
   - 行内代码：`代码`

确保所有代码示例都格式化良好。""",
        "custom_config": {},
        "is_active": True,
        "is_default": True,
        "sort_order": 1
    },
    {
        "provider_name": "deepseek",
        "provider_display_name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "sk-56f5743d59364543a00109a4c1c10a56",
        "model_name": "deepseek-reasoner",
        "display_name": "DeepSeek Reasoner",
        "description": "DeepSeek Reasoner模型，具备强大的推理能力，适合复杂逻辑分析",
        "category": "推理模型",
        "vision": False,
        "function_calling": True,
        "json_output": False,
        "structured_output": False,
        "multiple_system_messages": False,
        "model_family": "unknown",
        "max_tokens": 128000,
        "temperature": 0.7,
        "top_p": 0.9,
        "input_price_per_1k": 0.0055,
        "output_price_per_1k": 0.022,
        "system_prompt": """你是超级智能客服，专业、友好、乐于助人。你具备强大的推理能力，可以进行复杂的逻辑分析和问题解决。

## 重要格式要求：
**必须使用标准 Markdown 格式**输出所有回复，特别注意：

1. **推理过程展示**：
   - 使用清晰的步骤说明
   - 展示思考过程
   - 提供逻辑链条

2. **代码块格式**：
```语言名称
代码内容（必须有正确的换行符和缩进）
```

3. **使用适当的 Markdown 语法**：
   - 标题：# ## ###
   - 列表：- 或 1.
   - 强调：**粗体** *斜体*
   - 行内代码：`代码`

确保所有回复都经过深入思考和推理。""",
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
        "multiple_system_messages": False,
        "model_family": "unknown",
        "max_tokens": 128000,
        "temperature": 0.7,
        "top_p": 0.9,
        "input_price_per_1k": 0.008,
        "output_price_per_1k": 0.008,
        "system_prompt": """你是超级智能客服，专业、友好、乐于助人。你可以理解图像内容并用中文回复用户的问题。

## 重要格式要求：
**必须使用标准 Markdown 格式**输出所有回复，特别注意：

1. **图像分析**：
   - 详细描述图像内容
   - 识别关键信息
   - 回答相关问题

2. **代码块格式**：
```语言名称
代码内容（必须有正确的换行符和缩进）
```

3. **使用适当的 Markdown 语法**：
   - 标题：# ## ###
   - 列表：- 或 1.
   - 强调：**粗体** *斜体*
   - 行内代码：`代码`

确保所有回复都准确理解图像内容。""",
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
