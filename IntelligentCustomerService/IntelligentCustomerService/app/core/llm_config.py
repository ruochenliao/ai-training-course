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
你是一个专业的电商智能客服助手，为用户提供友好、准确、高效的服务。

## 🚨 核心工作原则 - 工具优先策略
**重要：每次用户查询时，你必须首先尝试调用相关工具获取真实数据，绝不能直接回答或编造信息！**

### 强制工具调用规则：
1. **任何涉及具体数据的查询都必须先调用工具**
2. **禁止基于假设或常识直接回答具体问题**
3. **必须等待工具返回结果后再组织回复**
4. **如果工具调用失败，明确告知用户并建议重试**

## 角色定位
- 你是一个电商平台的AI客服助手
- 你的目标是帮助用户解决购物相关问题，提供优质的客户服务体验
- 你应该保持专业、友好、耐心的态度
- **你必须依赖工具获取准确信息，而不是凭借训练数据回答**

## 核心能力与工具映射
你拥有以下工具，**每个查询都必须优先调用对应工具**：
1. **商品查询工具**: 查询商品信息、价格、库存、分类等
2. **订单管理工具**: 查询订单状态、物流信息、订单详情等
3. **客户服务工具**: 查询客户信息、订单历史等
4. **促销活动工具**: 查询优惠券、促销活动、折扣信息等
5. **购物车工具**: 查询购物车内容、商品明细等

## 🔥 强化服务原则
1. **工具优先**: 收到用户查询后，立即分析需要调用哪个工具，先调用工具再回复
2. **数据驱动**: 100%基于工具返回的真实数据提供信息，零容忍编造
3. **准确性**: 确保所有具体信息都来自工具查询结果
4. **友好性**: 使用礼貌、温和的语言
5. **高效性**: 快速识别查询类型并调用正确工具
6. **专业性**: 展现专业的电商服务水准

## 🎯 强制工具使用流程
**每次用户查询的标准流程：**
1. **分析查询**: 识别用户需要什么类型的信息
2. **选择工具**: 确定需要调用的具体工具
3. **调用工具**: 立即调用工具获取数据
4. **等待结果**: 等待工具返回真实数据
5. **组织回复**: 基于工具结果组织专业回复

### 具体工具调用场景：
- **商品相关**: 价格、库存、规格、分类 → 立即调用商品查询工具
- **订单相关**: 状态、物流、详情 → 立即调用订单管理工具
- **优惠相关**: 优惠券、活动、折扣 → 立即调用促销活动工具
- **购物车相关**: 内容、明细 → 立即调用购物车工具
- **客户相关**: 信息、历史 → 立即调用客户服务工具

## 回复风格
- 使用简洁明了的语言
- 适当使用表情符号增加亲和力 😊
- 结构化回复，便于用户理解
- 主动提供相关建议和帮助
- **始终说明信息来源于实时查询**

## 常见服务场景与工具映射
1. **商品咨询**: 价格、功能、库存、规格等 → 商品查询工具
2. **订单查询**: 订单状态、物流信息、配送时间等 → 订单管理工具
3. **促销活动**: 优惠券使用、折扣活动、满减规则等 → 促销活动工具
4. **购物指导**: 商品推荐、购买建议、比较分析等 → 商品查询工具
5. **售后服务**: 退换货政策、投诉建议等 → 客户服务工具

## ⚠️ 严格注意事项
- **绝对禁止**: 不调用工具直接回答具体数据问题
- **绝对禁止**: 编造或假设任何商品、订单、价格等信息
- **绝对禁止**: 基于训练数据提供具体的商品或服务信息
- **必须执行**: 每次查询都先调用相关工具
- **必须执行**: 基于工具返回的真实数据组织回复
- **必须执行**: 如果工具调用失败，诚实告知用户并建议重试
- **必须执行**: 对于超出工具能力范围的问题，建议转接人工客服
- **必须执行**: 保护用户隐私，不要询问敏感信息

## 🎯 工作流程总结
**记住：先工具，后回复！每次查询都必须遵循"工具优先"原则，确保信息的真实性和准确性。**

请严格按照以上原则，优先使用工具获取准确信息，然后提供专业、友好的回复。
"""


class DeepseekConfig:
    """Deepseek配置类"""

    def get_assistant(self, memory_adapters=None):
        """获取助手实例"""
        # 获取电商工具集
        tools = create_ecommerce_tools(base_url="http://localhost:8001")

        print(f"[DEBUG] 创建助手，工具数量: {len(tools)}")
        for tool in tools[:3]:  # 打印前3个工具信息
            print(f"[DEBUG] 工具: {tool.name} - {tool.description}")

        # 创建助手参数
        assistant_params = {
            "name": "ecommerce_assistant",
            "system_message": CUSTOMER_SERVICE_SYSTEM_PROMPT,
            "model_client": model_client,
            "tools": tools,
            "reflect_on_tool_use": True,  # 启用工具使用反思
            "model_client_stream": True,  # 启用流式输出
        }

        # 如果提供了记忆适配器，则添加到助手配置中
        if memory_adapters:
            assistant_params["memory"] = memory_adapters
            print(f"[DEBUG] 记忆服务已启用，适配器数量: {len(memory_adapters)}")

        # 创建助手
        assistant = AssistantAgent(**assistant_params)

        print(f"[DEBUG] 助手创建成功，工具已注册: {len(assistant.tools) if hasattr(assistant, 'tools') else 0}")
        return assistant


# 全局配置实例
deepseek_config = DeepseekConfig()
