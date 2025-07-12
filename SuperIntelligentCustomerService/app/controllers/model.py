from typing import List, Optional, Tuple

from tortoise.expressions import Q

from ..core.crud import CRUDBase
from ..models.admin import Model
from ..schemas.models import ModelCreate, ModelUpdate
from ..utils.encryption import encrypt_api_key, decrypt_api_key, is_api_key_encrypted


class ModelController(CRUDBase[Model, ModelCreate, ModelUpdate]):
    def __init__(self):
        super().__init__(model=Model)

    async def create(self, obj_in: ModelCreate) -> Model:
        """创建模型，强制加密API密钥"""
        # 强制加密所有API密钥，不允许明文存储
        if obj_in.api_key:
            if is_api_key_encrypted(obj_in.api_key):
                raise ValueError("API密钥已经是加密格式，请提供明文密钥")
            obj_in.api_key = encrypt_api_key(obj_in.api_key)

        return await super().create(obj_in)

    async def update(self, id: int, obj_in: ModelUpdate) -> Optional[Model]:
        """更新模型，强制加密API密钥"""
        # 强制加密所有API密钥，不允许明文存储
        if obj_in.api_key:
            if is_api_key_encrypted(obj_in.api_key):
                raise ValueError("API密钥已经是加密格式，请提供明文密钥")
            obj_in.api_key = encrypt_api_key(obj_in.api_key)

        return await super().update(id=id, obj_in=obj_in)

    async def get_decrypted_model(self, id: int) -> Optional[Model]:
        """获取模型并解密API密钥"""
        model = await self.get(id=id)
        if model and model.api_key:
            # 创建一个副本以避免修改原对象
            model_dict = await model.to_dict()
            model_dict['api_key'] = decrypt_api_key(model.api_key)
            return model_dict
        return model

    async def get_model_by_name_decrypted(self, model_name: str) -> Optional[dict]:
        """根据模型名称获取模型并解密API密钥"""
        model = await self.get_model_by_name(model_name)
        if model and model.api_key:
            # 验证API密钥必须是加密的
            if not is_api_key_encrypted(model.api_key):
                raise ValueError(f"模型 {model_name} 的API密钥未加密，数据不一致")
            model_dict = await model.to_dict()
            model_dict['api_key'] = decrypt_api_key(model.api_key)
            return model_dict
        return model

    async def validate_all_api_keys_encrypted(self) -> bool:
        """验证所有模型的API密钥都已加密"""
        models = await self.model.all()
        for model in models:
            if model.api_key and not is_api_key_encrypted(model.api_key):
                raise ValueError(f"模型 {model.model_name} 的API密钥未加密，请运行迁移脚本")
        return True

    async def get_active_models(
        self, 
        page: int = 1, 
        page_size: int = 50,
        category: Optional[str] = None,
        model_type: Optional[str] = None
    ) -> Tuple[int, List[Model]]:
        """获取启用的模型列表"""
        q = Q(is_active=True)
        if category:
            q &= Q(category=category)
        if model_type:
            q &= Q(model_type=model_type)
        
        return await self.list(page=page, page_size=page_size, search=q, order=["category", "model_name"])

    async def get_model_by_name(self, model_name: str) -> Optional[Model]:
        """根据模型名称获取模型"""
        return await self.model.filter(model_name=model_name, is_active=True).first()

    async def get_models_by_category(self, category: str) -> List[Model]:
        """根据分类获取模型列表"""
        return await self.model.filter(category=category, is_active=True).order_by("model_name")

    async def get_model_categories(self) -> List[str]:
        """获取所有模型分类"""
        categories = await self.model.filter(is_active=True).distinct().values_list("category", flat=True)
        return list(categories)

    async def toggle_model_status(self, model_id: int) -> Optional[Model]:
        """切换模型启用状态"""
        model = await self.get(id=model_id)
        if model:
            model.is_active = not model.is_active
            await model.save()
        return model


model_controller = ModelController()
