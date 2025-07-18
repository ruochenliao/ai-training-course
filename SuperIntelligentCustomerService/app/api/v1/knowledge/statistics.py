"""
知识库统计API路由
提供知识库的统计分析功能
"""
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.services.knowledge_statistics import knowledge_statistics_service
from app.services.knowledge_permission_service import check_knowledge_base_access
from app.core.dependency import DependAuth
from app.models.admin import User

router = APIRouter()


class StatsResponse(BaseModel):
    """统计响应基类"""
    success: bool
    data: Dict[str, Any]
    msg: str


@router.get("/knowledge-base/{kb_id}", summary="获取知识库统计", response_model=dict)
async def get_knowledge_base_statistics(
    kb_id: int,
    current_user: User = DependAuth
):
    """
    获取指定知识库的详细统计信息
    
    Args:
        kb_id: 知识库ID
        current_user: 当前用户
        
    Returns:
        知识库统计数据
    """
    try:
        # 检查权限
        has_access = await check_knowledge_base_access(kb_id, current_user.id, "read")
        if not has_access:
            raise HTTPException(status_code=403, detail="无权限访问此知识库")
        
        # 获取统计数据
        stats = await knowledge_statistics_service.get_knowledge_base_stats(kb_id)
        if not stats:
            raise HTTPException(status_code=404, detail="知识库不存在")
        
        return {
            "success": True,
            "data": stats.to_dict(),
            "msg": "获取知识库统计成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库统计失败: {str(e)}")


@router.get("/user", summary="获取用户统计", response_model=dict)
async def get_user_statistics(
    current_user: User = DependAuth
):
    """
    获取当前用户的知识库统计信息
    
    Args:
        current_user: 当前用户
        
    Returns:
        用户统计数据
    """
    try:
        stats = await knowledge_statistics_service.get_user_stats(current_user.id)
        
        return {
            "success": True,
            "data": stats,
            "msg": "获取用户统计成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户统计失败: {str(e)}")


@router.get("/system", summary="获取系统统计", response_model=dict)
async def get_system_statistics(
    current_user: User = DependAuth
):
    """
    获取系统整体统计信息（需要管理员权限）
    
    Args:
        current_user: 当前用户
        
    Returns:
        系统统计数据
    """
    try:
        # 检查管理员权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        stats = await knowledge_statistics_service.get_system_stats()
        
        return {
            "success": True,
            "data": stats.to_dict(),
            "msg": "获取系统统计成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")


@router.get("/trending", summary="获取趋势统计", response_model=dict)
async def get_trending_statistics(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    current_user: User = DependAuth
):
    """
    获取趋势统计信息
    
    Args:
        days: 统计天数（1-90天）
        current_user: 当前用户
        
    Returns:
        趋势统计数据
    """
    try:
        # 检查管理员权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        stats = await knowledge_statistics_service.get_trending_stats(days)
        
        return {
            "success": True,
            "data": stats,
            "msg": f"获取{days}天趋势统计成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势统计失败: {str(e)}")


@router.get("/dashboard", summary="获取仪表板数据", response_model=dict)
async def get_dashboard_data(
    current_user: User = DependAuth
):
    """
    获取用户仪表板所需的统计数据
    
    Args:
        current_user: 当前用户
        
    Returns:
        仪表板数据
    """
    try:
        # 获取用户统计
        user_stats = await knowledge_statistics_service.get_user_stats(current_user.id)
        
        # 如果是管理员，还获取系统统计
        system_stats = None
        if current_user.is_superuser:
            system_stats = await knowledge_statistics_service.get_system_stats()
        
        # 获取最近7天趋势（仅管理员）
        trending_stats = None
        if current_user.is_superuser:
            trending_stats = await knowledge_statistics_service.get_trending_stats(7)
        
        dashboard_data = {
            "user": user_stats,
            "system": system_stats.to_dict() if system_stats else None,
            "trending": trending_stats,
            "is_admin": current_user.is_superuser
        }
        
        return {
            "success": True,
            "data": dashboard_data,
            "msg": "获取仪表板数据成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")


@router.get("/compare", summary="比较知识库统计", response_model=dict)
async def compare_knowledge_bases(
    kb_ids: str = Query(..., description="知识库ID列表，逗号分隔"),
    current_user: User = DependAuth
):
    """
    比较多个知识库的统计信息
    
    Args:
        kb_ids: 知识库ID列表（逗号分隔）
        current_user: 当前用户
        
    Returns:
        知识库比较数据
    """
    try:
        # 解析知识库ID列表
        try:
            kb_id_list = [int(kb_id.strip()) for kb_id in kb_ids.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail="知识库ID格式错误")
        
        if len(kb_id_list) > 10:
            raise HTTPException(status_code=400, detail="最多只能比较10个知识库")
        
        comparison_data = []
        
        for kb_id in kb_id_list:
            # 检查权限
            has_access = await check_knowledge_base_access(kb_id, current_user.id, "read")
            if not has_access:
                comparison_data.append({
                    "kb_id": kb_id,
                    "error": "无权限访问"
                })
                continue
            
            # 获取统计数据
            stats = await knowledge_statistics_service.get_knowledge_base_stats(kb_id)
            if stats:
                comparison_data.append(stats.to_dict())
            else:
                comparison_data.append({
                    "kb_id": kb_id,
                    "error": "知识库不存在"
                })
        
        return {
            "success": True,
            "data": {
                "comparison": comparison_data,
                "summary": {
                    "total_compared": len(comparison_data),
                    "successful": len([item for item in comparison_data if "error" not in item]),
                    "failed": len([item for item in comparison_data if "error" in item])
                }
            },
            "msg": f"比较{len(kb_id_list)}个知识库完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"比较知识库失败: {str(e)}")


@router.get("/export", summary="导出统计数据", response_model=dict)
async def export_statistics(
    type: str = Query("user", description="导出类型: user, system, trending"),
    format: str = Query("json", description="导出格式: json, csv"),
    days: Optional[int] = Query(None, description="趋势统计天数"),
    current_user: User = DependAuth
):
    """
    导出统计数据
    
    Args:
        type: 导出类型
        format: 导出格式
        days: 趋势统计天数
        current_user: 当前用户
        
    Returns:
        导出的统计数据
    """
    try:
        if type == "system" or type == "trending":
            if not current_user.is_superuser:
                raise HTTPException(status_code=403, detail="需要管理员权限")
        
        export_data = {}
        
        if type == "user":
            export_data = await knowledge_statistics_service.get_user_stats(current_user.id)
        elif type == "system":
            stats = await knowledge_statistics_service.get_system_stats()
            export_data = stats.to_dict()
        elif type == "trending":
            trend_days = days or 7
            export_data = await knowledge_statistics_service.get_trending_stats(trend_days)
        else:
            raise HTTPException(status_code=400, detail="不支持的导出类型")
        
        # 添加导出元数据
        export_data["export_info"] = {
            "type": type,
            "format": format,
            "exported_by": current_user.username,
            "exported_at": knowledge_statistics_service._format_size(0)  # 使用当前时间
        }
        
        return {
            "success": True,
            "data": export_data,
            "msg": f"导出{type}统计数据成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出统计数据失败: {str(e)}")


@router.get("/health", summary="获取系统健康状态", response_model=dict)
async def get_system_health(
    current_user: User = DependAuth
):
    """
    获取系统健康状态统计
    
    Args:
        current_user: 当前用户
        
    Returns:
        系统健康状态
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 获取系统统计
        system_stats = await knowledge_statistics_service.get_system_stats()
        
        # 计算健康指标
        total_files = system_stats.total_files
        failed_files = system_stats.failed_files
        processing_files = system_stats.processing_files
        
        # 计算健康分数
        health_score = 100
        if total_files > 0:
            failure_rate = failed_files / total_files
            if failure_rate > 0.1:  # 失败率超过10%
                health_score -= 30
            elif failure_rate > 0.05:  # 失败率超过5%
                health_score -= 15
            
            processing_rate = processing_files / total_files
            if processing_rate > 0.2:  # 处理中文件超过20%
                health_score -= 20
            elif processing_rate > 0.1:  # 处理中文件超过10%
                health_score -= 10
        
        # 确定健康状态
        if health_score >= 90:
            health_status = "excellent"
            health_message = "系统运行状态优秀"
        elif health_score >= 70:
            health_status = "good"
            health_message = "系统运行状态良好"
        elif health_score >= 50:
            health_status = "warning"
            health_message = "系统运行状态需要关注"
        else:
            health_status = "critical"
            health_message = "系统运行状态需要紧急处理"
        
        health_data = {
            "health_score": health_score,
            "health_status": health_status,
            "health_message": health_message,
            "metrics": {
                "total_files": total_files,
                "failed_files": failed_files,
                "processing_files": processing_files,
                "success_rate": f"{((total_files - failed_files) / total_files * 100):.1f}%" if total_files > 0 else "0%",
                "failure_rate": f"{(failed_files / total_files * 100):.1f}%" if total_files > 0 else "0%"
            },
            "recommendations": []
        }
        
        # 添加建议
        if failed_files > 0:
            health_data["recommendations"].append("检查失败的文件处理任务")
        if processing_files > total_files * 0.1:
            health_data["recommendations"].append("关注处理队列，可能存在积压")
        
        return {
            "success": True,
            "data": health_data,
            "msg": "获取系统健康状态成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统健康状态失败: {str(e)}")
