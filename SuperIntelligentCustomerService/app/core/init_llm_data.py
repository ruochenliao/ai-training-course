# -*- coding: utf-8 -*-
"""
LLM模型数据初始化
基于 llms.py 的配置初始化数据库数据
"""
from ..models.llm_models import LLMProvider, LLMModel
from ..utils.security import encrypt_api_key


async def init_llm_providers():
    """初始化LLM提供商数据"""
    providers_data = [
        {
            "name": "deepseek",
            "display_name": "DeepSeek",
            "description": "DeepSeek AI提供的大语言模型服务",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": encrypt_api_key("sk-56f5743d59364543a00109a4c1c10a56"),
            "headers": {},
            "is_active": True,
            "sort_order": 1
        },
        {
            "name": "qwen",
            "display_name": "通义千问",
            "description": "阿里云通义千问大语言模型服务",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": encrypt_api_key("sk-aeb8d69039b14320b0fe58cb8285d8b1"),
            "headers": {},
            "is_active": True,
            "sort_order": 2
        }
    ]
    
    for provider_data in providers_data:
        # 检查是否已存在
        existing = await LLMProvider.filter(name=provider_data["name"]).first()
        if not existing:
            await LLMProvider.create(**provider_data)
            print(f"✅ 创建提供商: {provider_data['display_name']}")
        else:
            print(f"⏭️  提供商已存在: {provider_data['display_name']}")


async def init_llm_models():
    """初始化LLM模型数据"""
    # 获取提供商
    deepseek_provider = await LLMProvider.filter(name="deepseek").first()
    qwen_provider = await LLMProvider.filter(name="qwen").first()
    
    if not deepseek_provider or not qwen_provider:
        print("❌ 提供商不存在，请先初始化提供商数据")
        return
    
    models_data = [
        {
            "provider": deepseek_provider,
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
            "provider": deepseek_provider,
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
            "provider": qwen_provider,
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
    
    for model_data in models_data:
        # 检查是否已存在
        existing = await LLMModel.filter(
            provider=model_data["provider"],
            model_name=model_data["model_name"]
        ).first()
        
        if not existing:
            await LLMModel.create(**model_data)
            print(f"✅ 创建模型: {model_data['display_name']}")
        else:
            print(f"⏭️  模型已存在: {model_data['display_name']}")


async def init_llm_data():
    """初始化所有LLM相关数据"""
    print("🚀 开始初始化LLM数据...")
    
    try:
        # 初始化提供商
        print("\n📦 初始化LLM提供商...")
        await init_llm_providers()
        
        # 初始化模型
        print("\n🤖 初始化LLM模型...")
        await init_llm_models()
        
        print("\n🎉 LLM数据初始化完成！")
        
    except Exception as e:
        print(f"\n❌ LLM数据初始化失败: {str(e)}")
        raise


async def reset_llm_data():
    """重置LLM数据（删除所有数据并重新初始化）"""
    print("⚠️  开始重置LLM数据...")
    
    try:
        # 删除所有模型
        await LLMModel.all().delete()
        print("🗑️  已删除所有模型数据")
        
        # 删除所有提供商
        await LLMProvider.all().delete()
        print("🗑️  已删除所有提供商数据")
        
        # 重新初始化
        await init_llm_data()
        
        print("🎉 LLM数据重置完成！")
        
    except Exception as e:
        print(f"❌ LLM数据重置失败: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio
    from tortoise import Tortoise
    
    async def main():
        # 初始化数据库连接
        await Tortoise.init(
            db_url="sqlite://db.sqlite3",
            modules={"models": ["app.models"]}
        )
        
        # 初始化数据
        await init_llm_data()
        
        # 关闭数据库连接
        await Tortoise.close_connections()
    
    asyncio.run(main())
