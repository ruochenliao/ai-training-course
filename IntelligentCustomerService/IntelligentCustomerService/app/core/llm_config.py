"""
Deepseek大模型配置
基于autogen 0.6.1框架
"""
import os
from typing import Dict

from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ModelInfo, ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import _MODEL_INFO, _MODEL_TOKEN_LIMITS

from app.core.agent_tools import create_ecommerce_tools

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
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-56f5743d59364543a00109a4c1c10a56"),  # API密钥
    model_info=deepseek_model_info,  # 指定模型信息
)

# 智能客服系统提示词
CUSTOMER_SERVICE_SYSTEM_PROMPT = """
你是一个专业的智能客服助手，为用户提供友好、准确、高效的服务。

## 角色定位
- 你是一个智能客服系统的AI助手
- 你的目标是帮助用户解决问题，提供优质的客户服务体验
- 你应该保持专业、友好、耐心的态度

## 服务原则
1. **准确性**: 提供准确、可靠的信息
2. **友好性**: 使用礼貌、温和的语言
3. **高效性**: 快速理解用户需求，提供有效解决方案
4. **专业性**: 展现专业的服务水准

## 回复风格
- 使用简洁明了的语言
- 适当使用表情符号增加亲和力
- 结构化回复，便于用户理解
- 主动提供相关建议和帮助

## 常见服务场景
1. 产品咨询：价格、功能、特性等
2. 技术支持：使用问题、故障排除等
3. 账户服务：注册、登录、密码重置等
4. 售后服务：退款、投诉、建议等
5. 一般咨询：联系方式、营业时间等

## 注意事项
- 如果遇到无法解决的问题，主动建议转接人工客服
- 保护用户隐私，不要询问敏感信息
- 对于涉及金钱、法律等重要事项，建议用户联系相关专业人员

请根据用户的问题，提供专业、友好的回复。使用工具获取准确的商品、订单等信息。
"""


class DeepseekConfig:
    """Deepseek配置类"""

    def get_assistant(self):
        """获取助手实例"""
        # 获取电商工具集
        tools = create_ecommerce_tools()

        # 创建助手
        assistant = AssistantAgent(
            name="shop_assistant",
            system_message=CUSTOMER_SERVICE_SYSTEM_PROMPT,
            model_client=model_client,
            tools=tools,
            reflect_on_tool_use=True,
            model_client_stream=True,  # 启用流式输出
        )
        return assistant


# 全局配置实例
deepseek_config = DeepseekConfig()
