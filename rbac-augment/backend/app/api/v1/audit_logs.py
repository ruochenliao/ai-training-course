"""
审计日志API端点
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException

from app.utils.deps import get_current_user, get_current_superuser, CurrentUserPermissions
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogStatistics,
    AuditLogCleanupRequest,
    AuditLogExportRequest,
    AuditLogBatchDeleteRequest,
    AuditLogSearchParams
)
from app.utils.response import success_response, error_response
from app.utils.pagination import paginate

router = APIRouter()


@router.get("/")
async def get_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource: Optional[str] = Query(None, description="资源类型"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    level: Optional[str] = Query(None, description="日志级别"),
    result: Optional[str] = Query(None, description="操作结果"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    ip_address: Optional[str] = Query(None, description="IP地址"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_user)
):
    """获取审计日志列表"""
    from app.services.audit_log_service import audit_log_service

    try:
        # 处理日期时间参数
        start_datetime = None
        end_datetime = None

        if start_time and start_time.strip():
            try:
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                pass  # 忽略无效的日期格式

        if end_time and end_time.strip():
            try:
                end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                pass  # 忽略无效的日期格式

        # 使用服务层获取审计日志
        logs_data = await audit_log_service.get_audit_logs(
            page=page,
            page_size=page_size,
            action=action,
            resource_type=resource,
            user_id=user_id,
            level=level,
            status=result,
            start_time=start_datetime,
            end_time=end_datetime,
            ip_address=ip_address,
            keyword=keyword
        )

        return success_response(data=logs_data)
    except Exception as e:
        # 返回空数据结构
        empty_data = {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "has_next": False,
            "has_prev": False
        }
        return success_response(data=empty_data)


@router.get("/stats")
async def get_audit_log_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """获取审计日志统计信息"""
    from app.services.audit_log_service import audit_log_service
    
    try:
        # 使用服务层获取统计信息
        stats_data = await audit_log_service.get_statistics(days=days)
        
        return success_response(data=stats_data)
    except Exception as e:
        # 返回空统计数据
        now = datetime.now()
        empty_stats = {
            "total_logs": 0,
            "today_logs": 0,
            "success_logs": 0,
            "failed_logs": 0,
            "logs_by_action": {},
            "logs_by_level": {},
            "logs_by_resource": {},
            "top_users": [],
            "recent_critical": [],
            "time_range": {
                "start_time": now - timedelta(days=days),
                "end_time": now,
                "days": days
            }
        }
        return success_response(data=empty_stats)


@router.get("/{log_id}")
async def get_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取单条审计日志详情"""
    from app.services.audit_log_service import audit_log_service
    
    try:
        # 使用服务层获取审计日志详情
        log_data = await audit_log_service.get_audit_log_detail(log_id)
        
        if not log_data:
            raise HTTPException(status_code=404, detail="审计日志不存在")
        
        return success_response(data=log_data)
    except HTTPException as e:
        # 重新抛出HTTP异常
        raise e
    except Exception as e:
        # 返回空数据
        return error_response(message="获取审计日志详情失败", code=500)


@router.post("/cleanup")
async def cleanup_audit_logs(
    cleanup_request: AuditLogCleanupRequest,
    current_user: User = Depends(get_current_superuser)
):
    """清理过期审计日志（仅超级管理员可操作）"""
    from app.services.audit_log_service import audit_log_service
    
    try:
        # 执行清理操作
        result = await audit_log_service.cleanup_logs(
            days=cleanup_request.days,
            level=cleanup_request.level
        )
        
        if not result["success"]:
            return error_response(message=result["message"], code=500)
        
        return success_response(data=result)
    except Exception as e:
        # 返回错误响应
        return error_response(message="清理审计日志失败", code=500)


@router.post("/export")
async def export_audit_logs(
    export_request: AuditLogExportRequest,
    current_user: User = Depends(get_current_user)
):
    """导出审计日志"""
    from app.services.audit_log_service import audit_log_service
    
    try:
        # 构建搜索参数
        search_params = AuditLogSearchParams(
            keyword=export_request.keyword,
            action=export_request.action,
            resource_type=export_request.resource_type,
            level=export_request.level,
            status=export_request.status,
            user_id=export_request.user_id,
            username=export_request.username,
            user_ip=export_request.ip_address,
            start_time=export_request.start_time,
            end_time=export_request.end_time
        )
        
        # 获取导出数据
        export_data = await audit_log_service.export_logs(
            search_params=search_params,
            export_format=export_request.format,
            max_records=export_request.max_records
        )
        
        return success_response(data=export_data)
    except Exception as e:
        # 返回错误响应
        return error_response(message="导出审计日志失败", code=500)
    # 处理日期时间参数
    start_datetime = None
    end_datetime = None

    if export_request.start_time and export_request.start_time.strip():
        try:
            start_datetime = datetime.fromisoformat(export_request.start_time.replace('Z', '+00:00'))
        except ValueError:
            pass  # 忽略无效的日期格式

    if export_request.end_time and export_request.end_time.strip():
        try:
            end_datetime = datetime.fromisoformat(export_request.end_time.replace('Z', '+00:00'))
        except ValueError:
            pass  # 忽略无效的日期格式

    # 生成CSV文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"audit_logs_{timestamp}.csv"
    
    # 使用服务层获取审计日志数据
    from app.services.audit_log_service import audit_log_service
    logs_data = await audit_log_service.get_audit_logs(
        page=1,
        page_size=10000,  # 导出时获取更多数据
        action=export_request.action,
        resource_type=export_request.resource_type,
        user_id=export_request.user_id,
        level=export_request.level,
        status=export_request.status,
        start_time=start_datetime,
        end_time=end_datetime,
        ip_address=export_request.ip_address,
        keyword=export_request.keyword
    )
    
    # 这里应该有实际的CSV生成和保存逻辑
    # 暂时返回下载信息
    export_data = {
        "filename": filename,
        "download_url": f"/api/v1/downloads/{filename}",
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        "record_count": logs_data.get("total", 0)
    }
    
    return success_response(data=export_data)


@router.post("/batch-delete")
async def batch_delete_audit_logs(
    delete_request: AuditLogBatchDeleteRequest,
    current_user: User = Depends(get_current_superuser)
):
    """批量删除审计日志（仅超级管理员可操作）"""
    from app.services.audit_log_service import audit_log_service
    
    try:
        # 执行批量删除
        deleted_count = await audit_log_service.batch_delete(delete_request.log_ids)
        
        return success_response(data={
            "success": True,
            "message": f"成功删除 {deleted_count} 条审计日志",
            "deleted_count": deleted_count,
            "requested_count": len(delete_request.log_ids)
        })
    except Exception as e:
        # 返回错误响应
        return error_response(message="批量删除审计日志失败", code=500)
