# -*- coding: utf-8 -*-
"""
LLM模型管理API路由
"""
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from ....controllers.llm_models import (
    llm_provider_controller,
    llm_model_controller,
    llm_model_usage_controller
)
from ....core.dependency import DependAuth
from ....core.llms import model_client_manager
from ....models.admin import User
from ....schemas.base import Success
from ....schemas.llm_models import (
    LLMProviderCreate, LLMProviderUpdate, LLMProviderResponse, LLMProviderListResponse,
    LLMModelCreate, LLMModelUpdate, LLMModelResponse, LLMModelListResponse
)

router = APIRouter()

# ==================== LLM提供商管理 ====================

@router.get("/providers", summary="获取LLM提供商列表", response_model=LLMProviderListResponse)
async def get_provider_list(
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    name: Optional[str] = Query(None, description="提供商名称"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = DependAuth
):
    """获取LLM提供商列表"""
    try:
        from tortoise.queryset import Q
        
        # 构建查询条件
        search = Q()
        if name:
            search &= Q(name__icontains=name) | Q(display_name__icontains=name)
        if is_active is not None:
            search &= Q(is_active=is_active)
        
        total, providers = await llm_provider_controller.list(
            page=page,
            page_size=page_size,
            search=search,
            order=["sort_order", "name"]
        )
        
        return Success(data=LLMProviderListResponse(total=total, items=providers))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {str(e)}")


@router.post("/providers", summary="创建LLM提供商", response_model=LLMProviderResponse)
async def create_provider(
    provider_data: LLMProviderCreate,
    current_user: User = DependAuth
):
    """创建LLM提供商"""
    try:
        # 检查名称是否已存在
        existing = await llm_provider_controller.get_by_name(provider_data.name)
        if existing:
            raise HTTPException(status_code=400, detail="提供商名称已存在")
        
        provider = await llm_provider_controller.create(provider_data)
        return Success(data=provider, msg="创建提供商成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建提供商失败: {str(e)}")


@router.put("/providers/{provider_id}", summary="更新LLM提供商", response_model=LLMProviderResponse)
async def update_provider(
    provider_id: int,
    provider_data: LLMProviderUpdate,
    current_user: User = DependAuth
):
    """更新LLM提供商"""
    try:
        provider = await llm_provider_controller.update(provider_id, provider_data)
        if not provider:
            raise HTTPException(status_code=404, detail="提供商不存在")
        
        # 重新加载模型客户端
        await model_client_manager.reload_models()
        
        return Success(data=provider, msg="更新提供商成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新提供商失败: {str(e)}")


@router.delete("/providers/{provider_id}", summary="删除LLM提供商")
async def delete_provider(
    provider_id: int,
    current_user: User = DependAuth
):
    """删除LLM提供商"""
    try:
        await llm_provider_controller.remove(provider_id)
        
        # 重新加载模型客户端
        await model_client_manager.reload_models()
        
        return Success(msg="删除提供商成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除提供商失败: {str(e)}")


# ==================== LLM模型管理 ====================

@router.get("/models", summary="获取LLM模型列表", response_model=LLMModelListResponse)
async def get_model_list(
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    category: Optional[str] = Query(None, description="模型分类"),
    provider_id: Optional[int] = Query(None, description="提供商ID"),
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
        if provider_id:
            search &= Q(provider_id=provider_id)
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
        
        # 预加载提供商信息
        for model in models:
            await model.fetch_related("provider")
        
        return Success(data=LLMModelListResponse(total=total, items=models))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.post("/models", summary="创建LLM模型", response_model=LLMModelResponse)
async def create_model(
    model_data: LLMModelCreate,
    current_user: User = DependAuth
):
    """创建LLM模型"""
    try:
        # 检查模型名称在同一提供商下是否已存在
        existing = await llm_model_controller.get_by_name(
            model_data.model_name, 
            model_data.provider_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="该提供商下模型名称已存在")
        
        model = await llm_model_controller.create(model_data)
        
        # 重新加载模型客户端
        await model_client_manager.reload_models()
        
        return Success(data=model, msg="创建模型成功")
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
        
        return Success(data=model, msg="更新模型成功")
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
        
        return Success(data=model, msg="切换模型状态成功")
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


@router.get("/models/{model_id}/usage", summary="获取模型使用统计")
async def get_model_usage_stats(
    model_id: int,
    days: int = Query(30, description="统计天数"),
    current_user: User = DependAuth
):
    """获取模型使用统计"""
    try:
        stats = await llm_model_usage_controller.get_model_usage_stats(model_id, days)
        return Success(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取使用统计失败: {str(e)}")


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
        # 如果数据库访问失败，返回默认模型列表
        default_models = ["deepseek-chat", "deepseek-reasoner", "qwen-vl-plus"]
        return Success(data=default_models, msg=f"使用默认模型列表: {str(e)}")


@router.post("/reload-models", summary="重新加载模型配置")
async def reload_models(current_user: User = DependAuth):
    """重新加载模型配置"""
    try:
        await model_client_manager.reload_models()
        return Success(msg="重新加载模型配置成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载模型配置失败: {str(e)}")
