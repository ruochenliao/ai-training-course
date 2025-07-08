from typing import List, Optional, Tuple
from tortoise.expressions import Q

from app.core.crud import CRUDBase
from app.models.admin import Model
from app.schemas.models import ModelCreate, ModelUpdate


class ModelController(CRUDBase[Model, ModelCreate, ModelUpdate]):
    def __init__(self):
        super().__init__(model=Model)

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
