"""
模型客户端管理API
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.model_clients import (
    model_client_manager,
    list_available_model_providers,
    get_model_info
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/model-clients", tags=["模型客户端管理"])


@router.get("/providers", response_model=List[str])
def get_available_providers(
    current_user: User = Depends(get_current_user)
):
    """获取所有可用的模型提供商"""
    return list_available_model_providers()


@router.get("/providers/{provider}/info")
def get_provider_info(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """获取指定提供商的模型信息"""
    try:
        info = get_model_info(provider)
        if "error" in info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=info["error"]
            )
        return info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模型信息失败: {str(e)}"
        )


@router.get("/default/info")
def get_default_model_info(
    current_user: User = Depends(get_current_user)
):
    """获取默认模型信息"""
    return get_model_info()


@router.post("/reload")
def reload_model_clients(
    current_user: User = Depends(get_current_user)
):
    """重新加载所有模型客户端"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        model_client_manager.reload_clients()
        return {
            "message": "模型客户端重新加载成功",
            "available_providers": list_available_model_providers()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新加载失败: {str(e)}"
        )


@router.get("/status")
def get_model_clients_status(
    current_user: User = Depends(get_current_user)
):
    """获取模型客户端状态"""
    try:
        available_providers = list_available_model_providers()
        status_info = {
            "total_providers": len(available_providers),
            "available_providers": available_providers,
            "default_provider": model_client_manager._default_provider,
            "providers_info": {}
        }
        
        # 获取每个提供商的详细信息
        for provider in available_providers:
            try:
                provider_info = get_model_info(provider)
                status_info["providers_info"][provider] = {
                    "status": "available",
                    "info": provider_info
                }
            except Exception as e:
                status_info["providers_info"][provider] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return status_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )


@router.post("/test/{provider}")
def test_model_client(
    provider: str,
    test_prompt: str = "Hello, this is a test message.",
    current_user: User = Depends(get_current_user)
):
    """测试指定提供商的模型客户端"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        # 检查提供商是否可用
        if not model_client_manager.is_provider_available(provider):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"提供商 {provider} 不可用"
            )
        
        # 这里可以添加实际的测试逻辑
        # 由于测试可能涉及实际的API调用，这里只返回基本信息
        provider_info = get_model_info(provider)
        
        return {
            "provider": provider,
            "status": "available",
            "test_prompt": test_prompt,
            "provider_info": provider_info,
            "message": f"提供商 {provider} 可用，但未执行实际API测试"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试失败: {str(e)}"
        )
