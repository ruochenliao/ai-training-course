"""
系统配置管理API端点 - 第四阶段核心功能
提供动态配置管理、配置验证、配置导入导出等API
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from loguru import logger

from app.core.response import success_response, error_response
from app.core.security import get_current_user, require_permissions
from app.models.user import User
from app.services.config_manager import config_manager, ConfigItem, ConfigCategory

router = APIRouter(prefix="/config", tags=["系统配置管理"])


class ConfigItemResponse(BaseModel):
    """配置项响应模型"""
    key: str
    value: Any
    description: str
    category: str
    data_type: str
    is_sensitive: bool
    requires_restart: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    updated_by: Optional[int]


class ConfigCategoryResponse(BaseModel):
    """配置分类响应模型"""
    name: str
    description: str
    items: List[ConfigItemResponse]


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""
    value: Any = Field(..., description="配置值")


class ConfigBatchUpdateRequest(BaseModel):
    """批量配置更新请求模型"""
    configs: Dict[str, Any] = Field(..., description="配置键值对")


@router.get("/categories", summary="获取所有配置分类")
async def get_config_categories(
    current_user: User = Depends(require_permissions(["config:read"]))
):
    """获取所有配置分类及其配置项"""
    try:
        categories = config_manager.get_all_categories()
        
        response_data = []
        for category in categories:
            items = []
            for item in category.items:
                # 敏感配置不返回实际值
                value = "***" if item.is_sensitive else item.value
                
                items.append(ConfigItemResponse(
                    key=item.key,
                    value=value,
                    description=item.description,
                    category=item.category,
                    data_type=item.data_type,
                    is_sensitive=item.is_sensitive,
                    requires_restart=item.requires_restart,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    updated_by=item.updated_by
                ))
            
            response_data.append(ConfigCategoryResponse(
                name=category.name,
                description=category.description,
                items=items
            ))
        
        return success_response(
            data={"categories": [cat.dict() for cat in response_data]},
            message="成功获取配置分类"
        )
        
    except Exception as e:
        logger.error(f"获取配置分类失败: {e}")
        return error_response(message=f"获取配置分类失败: {str(e)}")


@router.get("/category/{category_name}", summary="获取指定分类的配置")
async def get_config_by_category(
    category_name: str,
    current_user: User = Depends(require_permissions(["config:read"]))
):
    """获取指定分类的所有配置项"""
    try:
        configs = config_manager.get_configs_by_category(category_name)
        
        if not configs:
            return error_response(message=f"分类 '{category_name}' 不存在或没有配置项")
        
        response_items = []
        for config in configs:
            # 敏感配置不返回实际值
            value = "***" if config.is_sensitive else config.value
            
            response_items.append(ConfigItemResponse(
                key=config.key,
                value=value,
                description=config.description,
                category=config.category,
                data_type=config.data_type,
                is_sensitive=config.is_sensitive,
                requires_restart=config.requires_restart,
                created_at=config.created_at,
                updated_at=config.updated_at,
                updated_by=config.updated_by
            ))
        
        return success_response(
            data={
                "category": category_name,
                "items": [item.dict() for item in response_items]
            },
            message=f"成功获取分类 '{category_name}' 的配置"
        )
        
    except Exception as e:
        logger.error(f"获取分类配置失败: {e}")
        return error_response(message=f"获取分类配置失败: {str(e)}")


@router.get("/{config_key}", summary="获取指定配置项")
async def get_config_item(
    config_key: str,
    current_user: User = Depends(require_permissions(["config:read"]))
):
    """获取指定的配置项"""
    try:
        config_item = config_manager.get_config_item(config_key)
        
        if not config_item:
            return error_response(message=f"配置项 '{config_key}' 不存在")
        
        # 敏感配置不返回实际值
        value = "***" if config_item.is_sensitive else config_item.value
        
        response_item = ConfigItemResponse(
            key=config_item.key,
            value=value,
            description=config_item.description,
            category=config_item.category,
            data_type=config_item.data_type,
            is_sensitive=config_item.is_sensitive,
            requires_restart=config_item.requires_restart,
            created_at=config_item.created_at,
            updated_at=config_item.updated_at,
            updated_by=config_item.updated_by
        )
        
        return success_response(
            data=response_item.dict(),
            message=f"成功获取配置项 '{config_key}'"
        )
        
    except Exception as e:
        logger.error(f"获取配置项失败: {e}")
        return error_response(message=f"获取配置项失败: {str(e)}")


@router.put("/{config_key}", summary="更新指定配置项")
async def update_config_item(
    config_key: str,
    request: ConfigUpdateRequest,
    current_user: User = Depends(require_permissions(["config:write"]))
):
    """更新指定的配置项"""
    try:
        config_item = config_manager.get_config_item(config_key)
        
        if not config_item:
            return error_response(message=f"配置项 '{config_key}' 不存在")
        
        # 更新配置
        success = config_manager.set_config(config_key, request.value, current_user.id)
        
        if success:
            # 检查是否需要重启
            restart_required = config_item.requires_restart
            
            return success_response(
                data={
                    "key": config_key,
                    "value": request.value,
                    "restart_required": restart_required
                },
                message=f"配置项 '{config_key}' 更新成功" + 
                       (" (需要重启系统生效)" if restart_required else "")
            )
        else:
            return error_response(message=f"配置项 '{config_key}' 更新失败")
        
    except Exception as e:
        logger.error(f"更新配置项失败: {e}")
        return error_response(message=f"更新配置项失败: {str(e)}")


@router.put("/batch", summary="批量更新配置项")
async def batch_update_configs(
    request: ConfigBatchUpdateRequest,
    current_user: User = Depends(require_permissions(["config:write"]))
):
    """批量更新多个配置项"""
    try:
        results = {}
        restart_required_configs = []
        
        for config_key, value in request.configs.items():
            config_item = config_manager.get_config_item(config_key)
            
            if not config_item:
                results[config_key] = {"success": False, "message": "配置项不存在"}
                continue
            
            success = config_manager.set_config(config_key, value, current_user.id)
            
            if success:
                results[config_key] = {"success": True, "message": "更新成功"}
                if config_item.requires_restart:
                    restart_required_configs.append(config_key)
            else:
                results[config_key] = {"success": False, "message": "更新失败"}
        
        success_count = sum(1 for r in results.values() if r["success"])
        total_count = len(request.configs)
        
        return success_response(
            data={
                "results": results,
                "success_count": success_count,
                "total_count": total_count,
                "restart_required": len(restart_required_configs) > 0,
                "restart_required_configs": restart_required_configs
            },
            message=f"批量更新完成: {success_count}/{total_count} 成功" +
                   (f" (有{len(restart_required_configs)}个配置需要重启生效)" if restart_required_configs else "")
        )
        
    except Exception as e:
        logger.error(f"批量更新配置失败: {e}")
        return error_response(message=f"批量更新配置失败: {str(e)}")


@router.post("/{config_key}/reset", summary="重置配置项为默认值")
async def reset_config_item(
    config_key: str,
    current_user: User = Depends(require_permissions(["config:write"]))
):
    """重置指定配置项为默认值"""
    try:
        success = config_manager.reset_config(config_key, current_user.id)
        
        if success:
            config_item = config_manager.get_config_item(config_key)
            restart_required = config_item.requires_restart if config_item else False
            
            return success_response(
                data={
                    "key": config_key,
                    "value": config_item.value if config_item else None,
                    "restart_required": restart_required
                },
                message=f"配置项 '{config_key}' 已重置为默认值" +
                       (" (需要重启系统生效)" if restart_required else "")
            )
        else:
            return error_response(message=f"配置项 '{config_key}' 重置失败")
        
    except Exception as e:
        logger.error(f"重置配置项失败: {e}")
        return error_response(message=f"重置配置项失败: {str(e)}")


@router.get("/validate/all", summary="验证所有配置")
async def validate_all_configs(
    current_user: User = Depends(require_permissions(["config:read"]))
):
    """验证所有配置项的有效性"""
    try:
        validation_errors = config_manager.validate_all_configs()
        
        is_valid = len(validation_errors) == 0
        
        return success_response(
            data={
                "is_valid": is_valid,
                "error_count": len(validation_errors),
                "errors": validation_errors
            },
            message="配置验证完成" + (" - 所有配置有效" if is_valid else f" - 发现{len(validation_errors)}个错误")
        )
        
    except Exception as e:
        logger.error(f"配置验证失败: {e}")
        return error_response(message=f"配置验证失败: {str(e)}")


@router.get("/export/all", summary="导出所有配置")
async def export_all_configs(
    current_user: User = Depends(require_permissions(["config:admin"]))
):
    """导出所有配置项（敏感配置会被掩码）"""
    try:
        config_data = config_manager.export_configs()
        
        return success_response(
            data={
                "configs": config_data,
                "export_time": config_manager.config_cache.get("system.session_timeout", {}).updated_at,
                "total_count": len(config_data)
            },
            message=f"成功导出{len(config_data)}个配置项"
        )
        
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        return error_response(message=f"导出配置失败: {str(e)}")


@router.post("/import", summary="导入配置")
async def import_configs(
    config_data: Dict[str, Any] = Body(..., description="配置数据"),
    current_user: User = Depends(require_permissions(["config:admin"]))
):
    """导入配置项"""
    try:
        results = config_manager.import_configs(config_data, current_user.id)
        
        success_count = sum(1 for r in results.values() if r == "成功")
        total_count = len(config_data)
        
        return success_response(
            data={
                "results": results,
                "success_count": success_count,
                "total_count": total_count
            },
            message=f"配置导入完成: {success_count}/{total_count} 成功"
        )
        
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        return error_response(message=f"导入配置失败: {str(e)}")


@router.get("/search", summary="搜索配置项")
async def search_configs(
    keyword: str,
    category: Optional[str] = None,
    current_user: User = Depends(require_permissions(["config:read"]))
):
    """根据关键词搜索配置项"""
    try:
        all_configs = config_manager.config_cache.values()
        
        # 过滤配置
        filtered_configs = []
        for config in all_configs:
            # 分类过滤
            if category and config.category != category:
                continue
            
            # 关键词搜索
            if keyword.lower() in config.key.lower() or keyword.lower() in config.description.lower():
                # 敏感配置不返回实际值
                value = "***" if config.is_sensitive else config.value
                
                filtered_configs.append(ConfigItemResponse(
                    key=config.key,
                    value=value,
                    description=config.description,
                    category=config.category,
                    data_type=config.data_type,
                    is_sensitive=config.is_sensitive,
                    requires_restart=config.requires_restart,
                    created_at=config.created_at,
                    updated_at=config.updated_at,
                    updated_by=config.updated_by
                ))
        
        return success_response(
            data={
                "configs": [config.dict() for config in filtered_configs],
                "total_count": len(filtered_configs),
                "search_keyword": keyword,
                "search_category": category
            },
            message=f"搜索完成，找到{len(filtered_configs)}个配置项"
        )
        
    except Exception as e:
        logger.error(f"搜索配置失败: {e}")
        return error_response(message=f"搜索配置失败: {str(e)}")
