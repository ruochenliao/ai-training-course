"""
审计日志API端点
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException

from app.utils.deps import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogStatistics
)
from app.utils.response import success_response
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
    current_user: User = Depends(get_current_user)
):
    """获取审计日志列表"""

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

    # 暂时返回模拟数据
    mock_data = {
        "items": [
            {
                "id": 1,
                "action": "LOGIN",
                "resource_type": "user",
                "resource_name": "用户登录",
                "description": "用户登录系统",
                "status": "SUCCESS",
                "level": "MEDIUM",
                "username": "admin",
                "user_ip": "127.0.0.1",
                "created_at": "2025-07-05T21:00:00Z"
            },
            {
                "id": 2,
                "action": "VIEW",
                "resource_type": "user",
                "resource_name": "查看用户列表",
                "description": "查看用户管理页面",
                "status": "SUCCESS",
                "level": "LOW",
                "username": "admin",
                "user_ip": "127.0.0.1",
                "created_at": "2025-07-05T20:59:00Z"
            }
        ],
        "total": 2,
        "page": page,
        "page_size": page_size,
        "total_pages": 1,
        "has_next": False,
        "has_prev": False
    }

    return success_response(data=mock_data)


@router.get("/stats")
async def get_audit_log_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """获取审计日志统计信息"""
    
    # 返回模拟统计数据
    stats = {
        "total_logs": 150,
        "level_stats": {
            "low": 80,
            "medium": 50,
            "high": 15,
            "critical": 5
        },
        "result_stats": {
            "success": 140,
            "failure": 10
        },
        "action_stats": [
            {"action": "LOGIN", "count": 45},
            {"action": "VIEW", "count": 60},
            {"action": "CREATE", "count": 20},
            {"action": "UPDATE", "count": 15},
            {"action": "DELETE", "count": 10}
        ],
        "user_stats": [
            {"user_id": 1, "username": "admin", "count": 80},
            {"user_id": 2, "username": "manager", "count": 40},
            {"user_id": 3, "username": "user", "count": 30}
        ],
        "high_risk_count": 20,
        "time_range": {
            "start_time": datetime.now() - timedelta(days=days),
            "end_time": datetime.now(),
            "days": days
        }
    }

    return success_response(data=stats)


@router.get("/{log_id}")
async def get_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取审计日志详情"""

    # 返回模拟数据
    mock_log = {
        "id": log_id,
        "action": "LOGIN",
        "resource_type": "user",
        "resource_name": "用户登录",
        "description": "用户登录系统",
        "status": "SUCCESS",
        "level": "MEDIUM",
        "username": "admin",
        "user_ip": "127.0.0.1",
        "created_at": "2025-07-05T21:00:00Z",
        "details": {"browser": "Chrome", "os": "Windows"}
    }

    return success_response(data=mock_log)


@router.delete("/cleanup")
async def cleanup_audit_logs(
    days: int = Query(90, ge=30, description="保留天数"),
    current_user: User = Depends(get_current_user)
):
    """清理过期的审计日志"""
    
    # 只有超级用户才能清理日志
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 计算清理时间点
    cleanup_time = datetime.now() - timedelta(days=days)
    
    # 删除过期日志
    deleted_count = await AuditLog.filter(created_at__lt=cleanup_time).delete()
    
    return success_response(
        data={"deleted_count": deleted_count, "cleanup_time": cleanup_time},
        message=f"成功清理 {deleted_count} 条过期审计日志"
    )


@router.get("/export/csv")
async def export_audit_logs_csv(
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_user)
):
    """导出审计日志为CSV格式"""

    from fastapi.responses import StreamingResponse
    import csv
    import io

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

    # 模拟数据
    logs = [
        {
            "id": 1,
            "action": "LOGIN",
            "resource": "user",
            "username": "admin",
            "user_ip": "127.0.0.1",
            "created_at": "2025-07-05T21:00:00Z"
        }
    ]
    
    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        'ID', '操作', '资源', '资源ID', '用户ID', '用户名', 
        'IP地址', '用户代理', '级别', '风险分数', '结果', 
        '请求数据', '响应数据', '错误信息', '创建时间'
    ])
    
    # 写入数据
    for log in logs:
        writer.writerow([
            log.id,
            log.action,
            log.resource,
            log.resource_id,
            log.user_id,
            log.username,
            log.ip_address,
            log.user_agent,
            log.level,
            log.risk_score,
            log.result,
            str(log.request_data) if log.request_data else '',
            str(log.response_data) if log.response_data else '',
            log.error_message,
            log.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    
    # 返回CSV文件
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }
    )
