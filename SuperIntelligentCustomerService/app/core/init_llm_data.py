# -*- coding: utf-8 -*-
"""
LLM模型数据初始化
使用统一配置源初始化数据库数据
"""
from ..models.llm_models import LLMModel
from ..utils.security import encrypt_api_key
from .llm_config import get_llm_models_config


async def init_llm_models():
    """初始化LLM模型数据"""
    # 从统一配置获取模型数据
    models_config = get_llm_models_config()

    for model_data in models_config:
        # 加密API密钥
        model_data_copy = model_data.copy()
        if model_data_copy.get("api_key"):
            model_data_copy["api_key"] = encrypt_api_key(model_data_copy["api_key"])
        # 检查是否已存在
        existing = await LLMModel.filter(
            model_name=model_data_copy["model_name"]
        ).first()

        if not existing:
            await LLMModel.create(**model_data_copy)
            print(f"✅ 创建模型: {model_data_copy['display_name']}")
        else:
            print(f"⏭️  模型已存在: {model_data_copy['display_name']}")


async def init_llm_data():
    """初始化所有LLM相关数据"""
    print("🚀 开始初始化LLM数据...")

    try:
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
        
        # 重新初始化
        await init_llm_data()
        
        print("🎉 LLM数据重置完成！")
        
    except Exception as e:
        print(f"❌ LLM数据重置失败: {str(e)}")
        raise