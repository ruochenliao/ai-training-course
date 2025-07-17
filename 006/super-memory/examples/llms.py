from autogen_ext.models.openai import OpenAIChatCompletionClient


def _setup_model_client():
    """设置模型客户端"""
    model_config = {"model": "deepseek-chat", "api_key": "sk-aef890875b8048e4bffe760f393d649a", "model_info": {
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "structured_output": True,  # 添加 structured_output 字段
        "family": "unknown",
        "multiple_system_messages": True
    }, "base_url": "https://api.deepseek.com/v1"}

    return OpenAIChatCompletionClient(**model_config)

model_client = _setup_model_client()