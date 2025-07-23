# -*- coding: utf-8 -*-
"""
LLM模型管理控制器
简化版本：只保留LLM模型控制器
"""
from typing import List, Optional, Tuple

from tortoise.queryset import Q

from ..core.crud import CRUDBase
from ..models.llm_models import LLMModel
from ..schemas.llm_models import (
    LLMModelCreate, LLMModelUpdate,
    ModelClientConfig
)
from ..utils.security import encrypt_api_key, decrypt_api_key, is_api_key_encrypted


class LLMModelController(CRUDBase[LLMModel, LLMModelCreate, LLMModelUpdate]):
    """LLM模型控制器"""

    def __init__(self):
        super().__init__(model=LLMModel)

    async def create(self, obj_in: LLMModelCreate) -> LLMModel:
        """创建模型，加密API密钥"""
        if obj_in.api_key:
            if is_api_key_encrypted(obj_in.api_key):
                raise ValueError("API密钥已经是加密格式，请提供明文密钥")
            obj_in.api_key = encrypt_api_key(obj_in.api_key)

        return await super().create(obj_in)

    async def update(self, id: int, obj_in: LLMModelUpdate) -> Optional[LLMModel]:
        """更新模型，加密API密钥"""
        if obj_in.api_key:
            if is_api_key_encrypted(obj_in.api_key):
                raise ValueError("API密钥已经是加密格式，请提供明文密钥")
            obj_in.api_key = encrypt_api_key(obj_in.api_key)

        return await super().update(id=id, obj_in=obj_in)

    async def get_active_models(
        self,
        page: int = 1,
        page_size: int = 50,
        category: Optional[str] = None,
        provider_name: Optional[str] = None
    ) -> Tuple[int, List[LLMModel]]:
        """获取启用的模型列表"""
        q = Q(is_active=True)
        if category:
            q &= Q(category=category)
        if provider_name:
            q &= Q(provider_name=provider_name)

        return await self.list(
            page=page,
            page_size=page_size,
            search=q,
            order=["sort_order", "display_name"]
        )

    async def get_by_name(self, model_name: str, provider_name: Optional[str] = None) -> Optional[LLMModel]:
        """根据模型名称获取模型"""
        q = Q(model_name=model_name, is_active=True)
        if provider_name:
            q &= Q(provider_name=provider_name)
        return await self.model.filter(q).first()
    
    async def get_models_by_category(self, category: str) -> List[LLMModel]:
        """根据分类获取模型列表"""
        return await self.model.filter(
            category=category, 
            is_active=True
        ).order_by("sort_order", "display_name")
    
    async def get_model_categories(self) -> List[str]:
        """获取所有模型分类"""
        categories = await self.model.filter(is_active=True).distinct().values_list("category", flat=True)
        return list(categories)
    
    async def get_default_model(self, category: Optional[str] = None) -> Optional[LLMModel]:
        """获取默认模型"""
        q = Q(is_active=True, is_default=True)
        if category:
            q &= Q(category=category)
        return await self.model.filter(q).first()
    
    async def set_default_model(self, model_id: int, category: Optional[str] = None) -> bool:
        """设置默认模型"""
        try:
            # 先取消同分类下的其他默认模型
            q = Q(is_default=True)
            if category:
                q &= Q(category=category)
            
            await self.model.filter(q).update(is_default=False)
            
            # 设置新的默认模型
            model = await self.get(id=model_id)
            if model:
                model.is_default = True
                await model.save()
                return True
            return False
        except Exception:
            return False
    
    async def toggle_model_status(self, model_id: int) -> Optional[LLMModel]:
        """切换模型启用状态"""
        model = await self.get(id=model_id)
        if model:
            model.is_active = not model.is_active
            await model.save()
        return model
    
    async def get_model_with_provider(self, model_id: int) -> Optional[LLMModel]:
        """获取模型（简化版本，提供商信息已内置）"""
        return await self.get(id=model_id)
    
    async def get_client_config(self, model_id: int) -> Optional[ModelClientConfig]:
        """获取模型客户端配置"""
        model = await self.get_model_with_provider(model_id)
        if not model:
            return None

        # 解密API密钥
        api_key = model.api_key
        if api_key and is_api_key_encrypted(api_key):
            api_key = decrypt_api_key(api_key)

        config_data = {
            "model": model.model_name,
            "base_url": model.base_url,
            "api_key": api_key,
            "model_info": await model.to_model_info(),
            "temperature": model.temperature,
            "top_p": model.top_p,
            "max_tokens": model.max_tokens,
            "custom_config": model.custom_config
        }

        return ModelClientConfig(**config_data)


# 创建控制器实例
llm_model_controller = LLMModelController()
