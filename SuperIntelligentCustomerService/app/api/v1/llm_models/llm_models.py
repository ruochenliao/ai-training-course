# -*- coding: utf-8 -*-
"""
LLM模型管理API路由
简化版本：只保留LLM模型管理功能
"""
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.controllers.llm_models import llm_model_controller
from app.core.dependency import DependAuth
from app.core.llms import model_client_manager
from app.models.admin import User
from app.models.llm_models import LLMModel
from app.schemas.base import Success, SuccessExtra
from app.schemas.llm_models import (
    LLMModelCreate, LLMModelUpdate, LLMModelResponse, LLMModelListResponse
)

router = APIRouter()


def model_to_dict(model: LLMModel) -> dict:
    """将模型对象转换为字典"""
    return {
        "id": model.id,
        "provider_name": model.provider_name,
        "provider_display_name": model.provider_display_name,
        "base_url": model.base_url,
        "model_name": model.model_name,
        "display_name": model.display_name,
        "description": model.description,
        "category": model.category,
        "vision": model.vision,
        "function_calling": model.function_calling,
        "json_output": model.json_output,
        "structured_output": model.structured_output,
        "multiple_system_messages": model.multiple_system_messages,
        "model_family": model.model_family,
        "max_tokens": model.max_tokens,
        "temperature": model.temperature,
        "top_p": model.top_p,
        "input_price_per_1k": float(model.input_price_per_1k),
        "output_price_per_1k": float(model.output_price_per_1k),
        "system_prompt": model.system_prompt,
        "is_active": model.is_active,
        "is_default": model.is_default,
        "sort_order": model.sort_order,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


# ==================== LLM模型管理 ====================

@router.get("/models", summary="获取LLM模型列表", response_model=LLMModelListResponse)
async def get_model_list(
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    category: Optional[str] = Query(None, description="模型分类"),
    provider_name: Optional[str] = Query(None, description="提供商名称"),
    model_name: Optional[str] = Query(None, description="模型名称"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = DependAuth
):
    """获取LLM模型列表"""
    try:
        from tortoise.queryset import Q

        # 构建查询条件
        search = Q()
        if category:
            search &= Q(category=category)
        if provider_name:
            search &= Q(provider_name=provider_name)
        if model_name:
            search &= Q(model_name__icontains=model_name) | Q(display_name__icontains=model_name)
        if is_active is not None:
            search &= Q(is_active=is_active)
        
        total, models = await llm_model_controller.list(
            page=page,
            page_size=page_size,
            search=search,
            order=["sort_order", "display_name"]
        )

        return SuccessExtra(
            data=[model_to_dict(model) for model in models],
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.post("/models", summary="创建LLM模型", response_model=LLMModelResponse)
async def create_model(
    model_data: LLMModelCreate,
    current_user: User = DependAuth
):
    """创建LLM模型"""
    try:
        # 检查模型名称是否已存在
        existing = await llm_model_controller.get_by_name(
            model_data.model_name,
            model_data.provider_name if hasattr(model_data, 'provider_name') else None
        )
        if existing:
            raise HTTPException(status_code=400, detail="模型名称已存在")
        
        model = await llm_model_controller.create(model_data)
        
        # 重新加载模型客户端
        await model_client_manager.reload_models()
        
        return Success(data=model_to_dict(model), msg="创建模型成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模型失败: {str(e)}")


@router.put("/models/{model_id}", summary="更新LLM模型", response_model=LLMModelResponse)
async def update_model(
    model_id: int,
    model_data: LLMModelUpdate,
    current_user: User = DependAuth
):
    """更新LLM模型"""
    try:
        model = await llm_model_controller.update(model_id, model_data)
        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 重新加载模型客户端
        await model_client_manager.reload_models()
        
        return Success(data=model_to_dict(model), msg="更新模型成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新模型失败: {str(e)}")


@router.delete("/models/{model_id}", summary="删除LLM模型")
async def delete_model(
    model_id: int,
    current_user: User = DependAuth
):
    """删除LLM模型"""
    try:
        await llm_model_controller.remove(model_id)
        
        # 重新加载模型客户端
        await model_client_manager.reload_models()
        
        return Success(msg="删除模型成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除模型失败: {str(e)}")


@router.post("/models/{model_id}/toggle", summary="切换模型状态", response_model=LLMModelResponse)
async def toggle_model_status(
    model_id: int,
    current_user: User = DependAuth
):
    """切换模型启用状态"""
    try:
        model = await llm_model_controller.toggle_model_status(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 重新加载模型客户端
        await model_client_manager.reload_models()
        
        return Success(data=model_to_dict(model), msg="切换模型状态成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换模型状态失败: {str(e)}")


@router.post("/models/{model_id}/set-default", summary="设置默认模型")
async def set_default_model(
    model_id: int,
    category: Optional[str] = Query(None, description="模型分类"),
    current_user: User = DependAuth
):
    """设置默认模型"""
    try:
        success = await llm_model_controller.set_default_model(model_id, category)
        if not success:
            raise HTTPException(status_code=400, detail="设置默认模型失败")
        
        return Success(msg="设置默认模型成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设置默认模型失败: {str(e)}")


# ==================== 模型分类和统计 ====================

@router.get("/categories", summary="获取模型分类列表")
async def get_model_categories(current_user: User = DependAuth):
    """获取所有模型分类"""
    try:
        categories = await llm_model_controller.get_model_categories()
        return Success(data=categories)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型分类失败: {str(e)}")


# 注意：使用统计功能已移除，可通过日志系统或其他方式实现


# ==================== 模型客户端管理 ====================

@router.get("/available-models", summary="获取可用模型列表")
async def get_available_models(current_user: User = DependAuth):
    """获取所有可用的模型客户端"""
    try:
        # 确保LLM客户端管理器已初始化
        if not model_client_manager._initialized:
            await model_client_manager.initialize()

        models = await model_client_manager.list_available_models()
        return Success(data=models)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取可用模型列表失败: {str(e)}")


@router.post("/reload-models", summary="重新加载模型配置")
async def reload_models(current_user: User = DependAuth):
    """重新加载模型配置"""
    try:
        await model_client_manager.reload_models()
        return Success(msg="重新加载模型配置成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载模型配置失败: {str(e)}")
