"""
权限管理API端点
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from app.core import get_current_user, PermissionChecker
from app.core.permission_cache import get_permission_cache
from app.core.permission_audit import get_permission_auditor, AuditAction, AuditLevel
from app.models import User

router = APIRouter()

# 权限检查器
require_permission_admin = PermissionChecker("permission:admin")
require_audit_view = PermissionChecker("audit:view")


class PermissionCacheStatsResponse(BaseModel):
    """权限缓存统计响应"""
    hits: int
    misses: int
    evictions: int
    hit_rate: float
    cache_sizes: Dict[str, int]
    total_cache_size: int


class AuditStatsResponse(BaseModel):
    """审计统计响应"""
    total_logs: int
    success_count: int
    failure_count: int
    success_rate: float
    by_action: Dict[str, int]
    by_level: Dict[str, int]
    by_user: Dict[str, int]
    memory_usage: Dict[str, int]


class UserPermissionCheckRequest(BaseModel):
    """用户权限检查请求"""
    user_id: int
    permission_codes: List[str]


class UserPermissionCheckResponse(BaseModel):
    """用户权限检查响应"""
    user_id: int
    permissions: Dict[str, bool]
    cached_results: Dict[str, bool]


@router.get("/cache/stats", response_model=PermissionCacheStatsResponse, summary="获取权限缓存统计")
async def get_permission_cache_stats(
    current_user: User = Depends(require_permission_admin)
) -> Any:
    """
    获取权限缓存统计信息
    """
    cache = get_permission_cache()
    stats = cache.get_stats()
    
    return PermissionCacheStatsResponse(**stats)


@router.post("/cache/clear", summary="清空权限缓存")
async def clear_permission_cache(
    current_user: User = Depends(require_permission_admin)
) -> Any:
    """
    清空所有权限缓存
    """
    cache = get_permission_cache()
    await cache.clear_all()
    
    return {
        "success": True,
        "message": "权限缓存已清空",
        "timestamp": cache.get_stats()["total_cache_size"]
    }


@router.delete("/cache/user/{user_id}", summary="清空用户权限缓存")
async def clear_user_permission_cache(
    user_id: int,
    current_user: User = Depends(require_permission_admin)
) -> Any:
    """
    清空指定用户的权限缓存
    """
    cache = get_permission_cache()
    await cache.invalidate_user(user_id)
    
    return {
        "success": True,
        "message": f"用户 {user_id} 的权限缓存已清空"
    }


@router.delete("/cache/role/{role_code}", summary="清空角色权限缓存")
async def clear_role_permission_cache(
    role_code: str,
    current_user: User = Depends(require_permission_admin)
) -> Any:
    """
    清空指定角色的权限缓存
    """
    cache = get_permission_cache()
    await cache.invalidate_role(role_code)
    
    return {
        "success": True,
        "message": f"角色 {role_code} 的权限缓存已清空"
    }


@router.post("/check", response_model=UserPermissionCheckResponse, summary="批量检查用户权限")
async def check_user_permissions(
    request: UserPermissionCheckRequest,
    current_user: User = Depends(require_permission_admin)
) -> Any:
    """
    批量检查用户权限
    """
    # 获取目标用户
    target_user = await User.get_or_none(id=request.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    cache = get_permission_cache()
    permissions = {}
    cached_results = {}
    
    # 检查每个权限
    for permission_code in request.permission_codes:
        # 先尝试从缓存获取
        cached_result = await cache.get_permission(request.user_id, permission_code)
        if cached_result is not None:
            permissions[permission_code] = cached_result
            cached_results[permission_code] = True
        else:
            # 从数据库查询
            has_permission = await target_user.has_permission(permission_code)
            permissions[permission_code] = has_permission
            cached_results[permission_code] = False
            
            # 设置缓存
            await cache.set_permission(request.user_id, permission_code, has_permission)
    
    return UserPermissionCheckResponse(
        user_id=request.user_id,
        permissions=permissions,
        cached_results=cached_results
    )


@router.get("/audit/stats", response_model=AuditStatsResponse, summary="获取审计统计")
async def get_audit_stats(
    current_user: User = Depends(require_audit_view)
) -> Any:
    """
    获取审计统计信息
    """
    auditor = get_permission_auditor()
    stats = auditor.get_stats()
    
    return AuditStatsResponse(**stats)


@router.get("/audit/logs", summary="获取审计日志")
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    action: Optional[str] = Query(None, description="动作类型"),
    level: Optional[str] = Query(None, description="日志级别"),
    success: Optional[bool] = Query(None, description="是否成功"),
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    current_user: User = Depends(require_audit_view)
) -> Any:
    """
    获取审计日志
    """
    import time
    
    auditor = get_permission_auditor()
    
    # 转换参数
    audit_action = None
    if action:
        try:
            audit_action = AuditAction(action)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的动作类型: {action}")
    
    audit_level = None
    if level:
        try:
            audit_level = AuditLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的日志级别: {level}")
    
    # 计算时间范围
    start_time = time.time() - (hours * 3600)
    
    # 获取日志
    logs = auditor.get_audit_logs(
        user_id=user_id,
        action=audit_action,
        level=audit_level,
        success=success,
        start_time=start_time,
        limit=limit
    )
    
    # 转换为可序列化格式
    result = []
    for log in logs:
        result.append({
            "timestamp": log.timestamp,
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action.value,
            "level": log.level.value,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "permission_code": log.permission_code,
            "role_code": log.role_code,
            "success": log.success,
            "message": log.message,
            "details": log.details,
            "client_ip": log.client_ip,
            "user_agent": log.user_agent,
            "request_id": log.request_id,
        })
    
    return {
        "logs": result,
        "total": len(result),
        "time_range_hours": hours,
        "filters": {
            "user_id": user_id,
            "action": action,
            "level": level,
            "success": success,
        }
    }


@router.get("/audit/user/{user_id}/activity", summary="获取用户活动日志")
async def get_user_activity(
    user_id: int,
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    current_user: User = Depends(require_audit_view)
) -> Any:
    """
    获取用户活动日志
    """
    # 检查目标用户是否存在
    target_user = await User.get_or_none(id=user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    auditor = get_permission_auditor()
    logs = auditor.get_user_activity(user_id, hours)
    
    # 转换为可序列化格式
    result = []
    for log in logs:
        result.append({
            "timestamp": log.timestamp,
            "action": log.action.value,
            "level": log.level.value,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "success": log.success,
            "message": log.message,
            "client_ip": log.client_ip,
        })
    
    return {
        "user_id": user_id,
        "username": target_user.username,
        "activity_logs": result,
        "total": len(result),
        "time_range_hours": hours,
    }


@router.get("/audit/failed-attempts", summary="获取失败的操作尝试")
async def get_failed_attempts(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    current_user: User = Depends(require_audit_view)
) -> Any:
    """
    获取失败的操作尝试
    """
    auditor = get_permission_auditor()
    logs = auditor.get_failed_attempts(hours)
    
    # 按用户分组统计
    user_failures = {}
    action_failures = {}
    
    for log in logs:
        # 按用户统计
        user_key = f"{log.user_id}:{log.username}" if log.username else str(log.user_id)
        user_failures[user_key] = user_failures.get(user_key, 0) + 1
        
        # 按动作统计
        action_key = log.action.value
        action_failures[action_key] = action_failures.get(action_key, 0) + 1
    
    # 转换为可序列化格式
    result = []
    for log in logs[:100]:  # 限制返回数量
        result.append({
            "timestamp": log.timestamp,
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action.value,
            "level": log.level.value,
            "message": log.message,
            "client_ip": log.client_ip,
        })
    
    return {
        "failed_attempts": result,
        "total_failures": len(logs),
        "time_range_hours": hours,
        "statistics": {
            "by_user": user_failures,
            "by_action": action_failures,
        }
    }


@router.post("/audit/cleanup", summary="清理审计日志")
async def cleanup_audit_logs(
    hours: int = Query(168, ge=24, le=8760, description="保留时间（小时）"),
    current_user: User = Depends(require_permission_admin)
) -> Any:
    """
    清理过期的审计日志
    """
    auditor = get_permission_auditor()
    cleared_count = auditor.clear_old_logs(hours)
    
    return {
        "success": True,
        "message": f"已清理 {cleared_count} 条过期审计日志",
        "retention_hours": hours,
        "remaining_logs": len(auditor.audit_logs)
    }
