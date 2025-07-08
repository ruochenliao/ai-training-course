from typing import Optional
from app.controllers.model import model_controller
from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.schemas import Success, Fail
from app.schemas.models import ModelCreate, ModelUpdate
from app.core.dependency import DependAuth
from app.models.admin import User

router = APIRouter()


@router.get("/list", summary="获取模型列表")
async def get_model_list(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    category: Optional[str] = Query(None, description="模型分类"),
    model_name: Optional[str] = Query(None, description="模型名称"),
    model_type: Optional[str] = Query(None, description="模型类型"),
    current_user: User = DependAuth
):
    """
    获取模型列表
    """
    try:
        # 构建查询条件
        search = Q()
        if category:
            search &= Q(category__icontains=category)
        if model_name:
            search &= Q(model_name__icontains=model_name)
        if model_type:
            search &= Q(model_type=model_type)

        # 获取模型列表
        total, models = await model_controller.list(
            page=page,
            page_size=page_size,
            search=search,
            order=["category", "model_name"]
        )

        model_list = []
        for model in models:
            model_dict = await model.to_dict()
            model_list.append(model_dict)

        return Success(data=model_list, total=total)

    except Exception as e:
        return Fail(msg=f"获取模型列表失败: {str(e)}")


@router.get("/get", summary="获取模型详情")
async def get_model_by_id(
    id: int = Query(..., description="模型ID"),
    current_user: User = DependAuth
):
    """
    根据ID获取模型详情
    """
    try:
        model = await model_controller.get(id=id)
        model_dict = await model.to_dict()
        return Success(data=model_dict)
    except Exception as e:
        return Fail(msg=f"获取模型详情失败: {str(e)}")


@router.post("/create", summary="创建模型")
async def create_model(
    model_data: ModelCreate,
    current_user: User = DependAuth
):
    """
    创建新模型
    """
    try:
        # 检查模型名称是否已存在
        existing_model = await model_controller.model.filter(model_name=model_data.model_name).first()
        if existing_model:
            return Fail(msg="模型名称已存在")

        model = await model_controller.create(model_data)
        model_dict = await model.to_dict()
        return Success(data=model_dict, msg="创建模型成功")
    except Exception as e:
        return Fail(msg=f"创建模型失败: {str(e)}")


@router.post("/update", summary="更新模型")
async def update_model(
    model_data: ModelUpdate,
    current_user: User = DependAuth
):
    """
    更新模型信息
    """
    try:
        # 检查模型名称是否与其他模型冲突
        if model_data.model_name:
            existing_model = await model_controller.model.filter(
                model_name=model_data.model_name
            ).exclude(id=model_data.id).first()
            if existing_model:
                return Fail(msg="模型名称已存在")

        model = await model_controller.update(id=model_data.id, obj_in=model_data)
        model_dict = await model.to_dict()
        return Success(data=model_dict, msg="更新模型成功")
    except Exception as e:
        return Fail(msg=f"更新模型失败: {str(e)}")


@router.delete("/delete", summary="删除模型")
async def delete_model(
    id: int = Query(..., description="模型ID"),
    current_user: User = DependAuth
):
    """
    删除模型
    """
    try:
        await model_controller.remove(id=id)
        return Success(msg="删除模型成功")
    except Exception as e:
        return Fail(msg=f"删除模型失败: {str(e)}")


@router.get("/modelList", summary="获取可用模型列表")
async def get_available_models():
    """
    获取可用的模型列表（用于聊天页面选择）
    """
    try:
        # 获取启用的模型
        total, models = await model_controller.get_active_models(page_size=100)

        if models:
            model_list = []
            for model in models:
                model_dict = await model.to_dict()
                # 转换字段名以匹配前端期望的格式
                formatted_model = {
                    "id": model_dict["id"],
                    "category": model_dict["category"],
                    "modelName": model_dict["model_name"],
                    "modelDescribe": model_dict["model_describe"],
                    "modelPrice": float(model_dict["model_price"]) if model_dict["model_price"] else 0,
                    "modelType": model_dict["model_type"],
                    "modelShow": model_dict["model_show"],
                    "systemPrompt": model_dict["system_prompt"],
                    "apiHost": model_dict["api_host"],
                    "apiKey": model_dict["api_key"],
                    "remark": model_dict["remark"]
                }
                model_list.append(formatted_model)
            return Success(data=model_list)
        else:
            # 如果数据库中没有数据，返回默认模型
            return Success(data=[])

    except Exception as e:
        return Fail(msg=f"获取模型列表失败: {str(e)}")
