# Copyright (c) 2025 左岚. All rights reserved.
"""
审计日志服务
提供审计日志的业务逻辑处理
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from ..models.audit_log import AuditLog, AuditAction, AuditLevel, AuditStatus
from ..schemas.audit_log import AuditLogSearchParams, AuditLogCreate
from ..crud.audit_log import CRUDAuditLog


class AuditLogService:
    """审计日志服务类"""

    def __init__(self):
        self.crud = CRUDAuditLog(AuditLog)

    async def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[int] = None,
        level: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        username: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取审计日志列表"""
        try:
            # 构建搜索参数
            search_params = AuditLogSearchParams(
                keyword=keyword,
                action=action,
                resource_type=resource_type,
                level=level,
                status=status,
                user_id=user_id,
                username=username,
                user_ip=ip_address,
                start_time=start_time,
                end_time=end_time
            )

            # 查询数据
            items, total = await self.crud.search(search_params, page, page_size)

            # 计算分页信息
            total_pages = (total + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1

            # 转换为响应格式
            result_items = []
            for item in items:
                result_items.append({
                    "id": item.id,
                    "action": item.action,
                    "resource_type": item.resource_type,
                    "resource_name": item.resource_name,
                    "description": item.description,
                    "status": item.status,
                    "level": item.level,
                    "username": item.username,
                    "user_ip": item.user_ip,
                    "created_at": item.created_at
                })

            return {
                "items": result_items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        except Exception as e:
            # 返回空数据结构
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }

    async def get_audit_log_detail(self, log_id: int) -> Optional[Dict[str, Any]]:
        """获取审计日志详情"""
        try:
            # 查询数据
            log = await self.crud.get(log_id)
            if not log:
                return None

            # 转换为响应格式
            return log.to_dict()
        except Exception as e:
            # 发生异常时返回None
            return None

    async def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取审计日志统计信息"""
        stats = await self.crud.get_statistics()

        # 处理时间范围
        now = datetime.now()
        stats["time_range"] = {
            "start_time": now - timedelta(days=days),
            "end_time": now,
            "days": days
        }

        return stats

    async def cleanup_logs(self, days: int = 90, level: Optional[str] = None) -> Dict[str, Any]:
        """清理过期审计日志"""
        try:
            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 执行清理
            deleted_count = await self.crud.delete_old_logs(cutoff_date, level)
            
            return {
                "success": True,
                "message": f"成功清理 {deleted_count} 条审计日志",
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date,
                "level": level
            }
        except Exception as e:
            # 返回错误信息
            return {
                "success": False,
                "message": f"清理审计日志失败: {str(e)}",
                "deleted_count": 0,
                "cutoff_date": datetime.now() - timedelta(days=days),
                "level": level
            }

    async def get_user_activity(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """获取用户活动统计"""
        try:
            # 获取时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 获取用户活动数据
            activity_data = await self.crud.get_user_activity(user_id, start_time, end_time)
            
            # 计算风险评分
            risk_score = 0
            if activity_data["failed_operations"] > 0:
                # 失败操作越多，风险越高
                risk_score += min(activity_data["failed_operations"] * 10, 50)
            
            if activity_data["critical_operations"] > 0:
                # 关键操作越多，风险越高
                risk_score += min(activity_data["critical_operations"] * 5, 30)
                
            if activity_data["unusual_time_operations"] > 0:
                # 非常规时间操作越多，风险越高
                risk_score += min(activity_data["unusual_time_operations"] * 5, 20)
            
            # 添加风险评分
            activity_data["risk_score"] = risk_score
            activity_data["risk_level"] = "高" if risk_score > 70 else "中" if risk_score > 30 else "低"
            
            # 添加时间范围
            activity_data["time_range"] = {
                "start_time": start_time,
                "end_time": end_time,
                "days": days
            }
            
            return activity_data
        except Exception as e:
            # 返回空数据结构
            return {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "critical_operations": 0,
                "unusual_time_operations": 0,
                "operations_by_type": {},
                "operations_by_day": {},
                "risk_score": 0,
                "risk_level": "低",
                "time_range": {
                    "start_time": datetime.now() - timedelta(days=days),
                    "end_time": datetime.now(),
                    "days": days
                }
            }

    async def export_logs(
        self, 
        search_params: AuditLogSearchParams,
        export_format: str = "csv",
        max_records: int = 1000
    ) -> Dict[str, Any]:
        """导出审计日志"""
        try:
            # 查询数据
            logs, total = await self.crud.search(search_params, page=1, page_size=max_records)
            
            # 转换为导出格式
            file_content = ""
            filename = f"audit_logs_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            if export_format.lower() == "csv":
                # 生成CSV内容
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # 写入表头
                writer.writerow([
                    "ID", "操作类型", "资源类型", "资源名称", "描述", "状态", 
                    "级别", "用户名", "IP地址", "创建时间"
                ])
                
                # 写入数据行
                for log in logs:
                    writer.writerow([
                        log.id, log.action, log.resource_type, log.resource_name,
                        log.description, log.status, log.level, log.username,
                        log.user_ip, log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    ])
                
                file_content = output.getvalue()
                filename += ".csv"
                mime_type = "text/csv"
            
            elif export_format.lower() == "json":
                # 生成JSON内容
                import json
                
                data = []
                for log in logs:
                    data.append(log.to_dict())
                
                file_content = json.dumps(data, ensure_ascii=False, default=str)
                filename += ".json"
                mime_type = "application/json"
            
            else:
                # 不支持的格式
                return {
                    "success": False,
                    "message": f"不支持的导出格式: {export_format}",
                    "filename": "",
                    "content": "",
                    "mime_type": "",
                    "total": 0
                }
            
            # 返回导出数据
            return {
                "success": True,
                "message": f"成功导出 {len(logs)} 条审计日志",
                "filename": filename,
                "content": file_content,
                "mime_type": mime_type,
                "total": len(logs)
            }
        except Exception as e:
            # 返回错误信息
            return {
                "success": False,
                "message": f"导出审计日志失败: {str(e)}",
                "filename": "",
                "content": "",
                "mime_type": "",
                "total": 0
            }

    async def batch_delete(self, log_ids: List[int]) -> int:
        """批量删除审计日志"""
        try:
            # 执行批量删除
            deleted_count = await self.crud.batch_delete(log_ids)
            return deleted_count
        except Exception as e:
            # 发生异常时返回0
            return 0


# 创建服务实例
audit_log_service = AuditLogService()