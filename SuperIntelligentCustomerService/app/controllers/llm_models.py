# -*- coding: utf-8 -*-
"""
LLM模型管理控制器
"""
from typing import List, Optional, Tuple

from tortoise.queryset import Q

from ..core.crud import CRUDBase
from ..models.llm_models import LLMProvider, LLMModel, LLMModelUsage, LLMModelPreset
from ..schemas.llm_models import (
    LLMProviderCreate, LLMProviderUpdate,
    LLMModelCreate, LLMModelUpdate,
    LLMModelPresetCreate, LLMModelPresetUpdate,
    ModelClientConfig
)
from ..utils.security import encrypt_api_key, decrypt_api_key, is_api_key_encrypted


class LLMProviderController(CRUDBase[LLMProvider, LLMProviderCreate, LLMProviderUpdate]):
    """LLM提供商控制器"""
    
    def __init__(self):
        super().__init__(model=LLMProvider)
    
    async def create(self, obj_in: LLMProviderCreate) -> LLMProvider:
        """创建提供商，加密API密钥"""
        if obj_in.api_key:
            if is_api_key_encrypted(obj_in.api_key):
                raise ValueError("API密钥已经是加密格式，请提供明文密钥")
            obj_in.api_key = encrypt_api_key(obj_in.api_key)
        
        return await super().create(obj_in)
    
    async def update(self, id: int, obj_in: LLMProviderUpdate) -> Optional[LLMProvider]:
        """更新提供商，加密API密钥"""
        if obj_in.api_key:
            if is_api_key_encrypted(obj_in.api_key):
                raise ValueError("API密钥已经是加密格式，请提供明文密钥")
            obj_in.api_key = encrypt_api_key(obj_in.api_key)
        
        return await super().update(id=id, obj_in=obj_in)
    
    async def get_active_providers(self) -> List[LLMProvider]:
        """获取启用的提供商列表"""
        return await self.model.filter(is_active=True).order_by("sort_order", "name")
    
    async def get_by_name(self, name: str) -> Optional[LLMProvider]:
        """根据名称获取提供商"""
        return await self.model.filter(name=name).first()


class LLMModelController(CRUDBase[LLMModel, LLMModelCreate, LLMModelUpdate]):
    """LLM模型控制器"""
    
    def __init__(self):
        super().__init__(model=LLMModel)
    
    async def get_active_models(
        self, 
        page: int = 1, 
        page_size: int = 50,
        category: Optional[str] = None,
        provider_id: Optional[int] = None
    ) -> Tuple[int, List[LLMModel]]:
        """获取启用的模型列表"""
        q = Q(is_active=True)
        if category:
            q &= Q(category=category)
        if provider_id:
            q &= Q(provider_id=provider_id)
        
        return await self.list(
            page=page, 
            page_size=page_size, 
            search=q, 
            order=["sort_order", "display_name"]
        )
    
    async def get_by_name(self, model_name: str, provider_id: Optional[int] = None) -> Optional[LLMModel]:
        """根据模型名称获取模型"""
        q = Q(model_name=model_name, is_active=True)
        if provider_id:
            q &= Q(provider_id=provider_id)
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
        """获取包含提供商信息的模型"""
        return await self.model.filter(id=model_id).prefetch_related("provider").first()
    
    async def get_client_config(self, model_id: int) -> Optional[ModelClientConfig]:
        """获取模型客户端配置"""
        model = await self.get_model_with_provider(model_id)
        if not model:
            return None
        
        provider = model.provider
        
        # 解密API密钥
        api_key = provider.api_key
        if api_key and is_api_key_encrypted(api_key):
            api_key = decrypt_api_key(api_key)
        
        config_data = {
            "model": model.model_name,
            "base_url": provider.base_url,
            "api_key": api_key,
            "model_info": await model.to_model_info(),
            "temperature": model.temperature,
            "top_p": model.top_p,
            "max_tokens": model.max_tokens,
            "custom_config": model.custom_config
        }
        
        return ModelClientConfig(**config_data)


class LLMModelPresetController(CRUDBase[LLMModelPreset, LLMModelPresetCreate, LLMModelPresetUpdate]):
    """LLM模型预设控制器"""
    
    def __init__(self):
        super().__init__(model=LLMModelPreset)
    
    async def create(self, obj_in: LLMModelPresetCreate) -> LLMModelPreset:
        """创建预设并关联模型"""
        model_ids = obj_in.model_ids
        obj_data = obj_in.model_dump(exclude={"model_ids"})
        
        preset = await super().create(obj_data)
        
        # 关联模型
        if model_ids:
            models = await LLMModel.filter(id__in=model_ids)
            await preset.models.add(*models)
        
        return preset
    
    async def update(self, id: int, obj_in: LLMModelPresetUpdate) -> Optional[LLMModelPreset]:
        """更新预设并更新模型关联"""
        preset = await self.get(id=id)
        if not preset:
            return None
        
        model_ids = obj_in.model_ids
        obj_data = obj_in.model_dump(exclude={"model_ids"}, exclude_unset=True)
        
        # 更新基本信息
        preset = await super().update(id=id, obj_in=obj_data)
        
        # 更新模型关联
        if model_ids is not None:
            await preset.models.clear()
            if model_ids:
                models = await LLMModel.filter(id__in=model_ids)
                await preset.models.add(*models)
        
        return preset
    
    async def get_active_presets(self) -> List[LLMModelPreset]:
        """获取启用的预设列表"""
        return await self.model.filter(is_active=True).order_by("sort_order", "display_name")
    
    async def get_public_presets(self) -> List[LLMModelPreset]:
        """获取公开的预设列表"""
        return await self.model.filter(
            is_active=True, 
            is_public=True
        ).order_by("sort_order", "display_name")
    
    async def get_preset_with_models(self, preset_id: int) -> Optional[LLMModelPreset]:
        """获取包含模型信息的预设"""
        return await self.model.filter(id=preset_id).prefetch_related("models__provider").first()


class LLMModelUsageController:
    """LLM模型使用统计控制器"""
    
    async def record_usage(
        self,
        model_id: int,
        input_tokens: int,
        output_tokens: int,
        response_time: float,
        success: bool = True,
        cost: float = 0
    ) -> None:
        """记录模型使用情况"""
        from datetime import date
        
        today = date.today()
        
        # 获取或创建今日统计记录
        usage, created = await LLMModelUsage.get_or_create(
            model_id=model_id,
            date=today,
            defaults={
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0,
                "avg_response_time": 0,
                "success_rate": 100
            }
        )
        
        # 更新统计数据
        usage.total_requests += 1
        usage.total_input_tokens += input_tokens
        usage.total_output_tokens += output_tokens
        usage.total_cost += cost
        
        # 更新平均响应时间
        if usage.total_requests == 1:
            usage.avg_response_time = response_time
        else:
            usage.avg_response_time = (
                (usage.avg_response_time * (usage.total_requests - 1) + response_time) 
                / usage.total_requests
            )
        
        # 更新成功率
        if success:
            success_count = usage.total_requests * (usage.success_rate / 100)
            usage.success_rate = (success_count / usage.total_requests) * 100
        else:
            success_count = usage.total_requests * (usage.success_rate / 100) - 1
            usage.success_rate = max(0, (success_count / usage.total_requests) * 100)
        
        await usage.save()
    
    async def get_model_usage_stats(
        self,
        model_id: int,
        days: int = 30
    ) -> List[LLMModelUsage]:
        """获取模型使用统计"""
        from datetime import date, timedelta
        
        start_date = date.today() - timedelta(days=days)
        
        return await LLMModelUsage.filter(
            model_id=model_id,
            date__gte=start_date
        ).order_by("-date")


# 创建控制器实例
llm_provider_controller = LLMProviderController()
llm_model_controller = LLMModelController()
llm_model_preset_controller = LLMModelPresetController()
llm_model_usage_controller = LLMModelUsageController()
