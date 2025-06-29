"""
监控调度服务
"""

import asyncio
import time
from typing import Dict, Any
from datetime import datetime

from loguru import logger

from app.services.health import HealthService
from app.services.business_metrics import get_business_metrics_service
from app.services.alert_service import get_alert_service
from app.core.error_monitoring import get_error_monitor
from app.core.permission_cache import get_permission_cache
from app.core.permission_audit import get_permission_auditor


class MonitoringScheduler:
    """监控调度器"""
    
    def __init__(self):
        self.running = False
        self.tasks = {}
        
        # 调度配置
        self.schedules = {
            "health_check": {"interval": 60, "last_run": 0},  # 每分钟
            "alert_check": {"interval": 300, "last_run": 0},  # 每5分钟
            "metrics_collection": {"interval": 600, "last_run": 0},  # 每10分钟
            "cleanup": {"interval": 3600, "last_run": 0},  # 每小时
            "daily_report": {"interval": 86400, "last_run": 0},  # 每天
        }
    
    async def start(self):
        """启动监控调度器"""
        if self.running:
            logger.warning("监控调度器已在运行")
            return
        
        self.running = True
        logger.info("监控调度器启动")
        
        # 启动主循环
        asyncio.create_task(self._main_loop())
    
    async def stop(self):
        """停止监控调度器"""
        self.running = False
        
        # 等待所有任务完成
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        
        logger.info("监控调度器停止")
    
    async def _main_loop(self):
        """主循环"""
        while self.running:
            try:
                current_time = time.time()
                
                # 检查各个调度任务
                for task_name, schedule in self.schedules.items():
                    if current_time - schedule["last_run"] >= schedule["interval"]:
                        # 启动任务
                        if task_name not in self.tasks or self.tasks[task_name].done():
                            self.tasks[task_name] = asyncio.create_task(
                                self._run_task(task_name)
                            )
                        schedule["last_run"] = current_time
                
                # 等待一段时间再检查
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                logger.error(f"监控调度器主循环错误: {e}")
                await asyncio.sleep(60)  # 出错时等待更长时间
    
    async def _run_task(self, task_name: str):
        """运行指定任务"""
        try:
            logger.debug(f"开始执行监控任务: {task_name}")
            start_time = time.time()
            
            if task_name == "health_check":
                await self._health_check_task()
            elif task_name == "alert_check":
                await self._alert_check_task()
            elif task_name == "metrics_collection":
                await self._metrics_collection_task()
            elif task_name == "cleanup":
                await self._cleanup_task()
            elif task_name == "daily_report":
                await self._daily_report_task()
            
            duration = time.time() - start_time
            logger.debug(f"监控任务 {task_name} 完成，耗时 {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"监控任务 {task_name} 执行失败: {e}")
    
    async def _health_check_task(self):
        """健康检查任务"""
        health_service = HealthService()
        health_status = await health_service.check_all()
        
        # 记录健康状态
        if health_status["status"] != "healthy":
            logger.warning(f"系统健康检查异常: {health_status}")
        
        # 可以在这里添加健康状态的持久化存储
    
    async def _alert_check_task(self):
        """告警检查任务"""
        try:
            # 收集系统数据
            health_service = HealthService()
            health_data = await health_service.check_all()
            
            error_monitor = get_error_monitor()
            performance_data = error_monitor.get_performance_metrics(300)  # 5分钟窗口
            
            business_service = get_business_metrics_service()
            business_data = await business_service.collect_all_metrics()
            
            permission_cache = get_permission_cache()
            cache_stats = permission_cache.get_stats()
            
            # 组合检查数据
            check_data = {
                **health_data.get("checks", {}),
                "performance": performance_data,
                "cache": cache_stats,
                "document_metrics": business_data.document_metrics,
                "user_metrics": business_data.user_metrics,
            }
            
            # 执行告警检查
            alert_service = get_alert_service()
            triggered_alerts = await alert_service.check_alerts(check_data)
            
            if triggered_alerts:
                logger.info(f"告警检查触发 {len(triggered_alerts)} 个告警")
                for alert in triggered_alerts:
                    logger.warning(f"新告警: {alert.title} - {alert.message}")
            
        except Exception as e:
            logger.error(f"告警检查任务失败: {e}")
    
    async def _metrics_collection_task(self):
        """指标收集任务"""
        try:
            # 收集业务指标
            business_service = get_business_metrics_service()
            metrics = await business_service.collect_all_metrics()
            
            # 记录关键指标
            logger.info(
                f"业务指标收集完成: "
                f"用户 {metrics.user_metrics.get('total_users', 0)}, "
                f"知识库 {metrics.knowledge_base_metrics.get('total_knowledge_bases', 0)}, "
                f"文档 {metrics.document_metrics.get('total_documents', 0)}"
            )
            
            # 可以在这里添加指标的持久化存储或发送到外部监控系统
            
        except Exception as e:
            logger.error(f"指标收集任务失败: {e}")
    
    async def _cleanup_task(self):
        """清理任务"""
        try:
            # 清理错误监控数据
            error_monitor = get_error_monitor()
            error_monitor.clear_old_data()
            
            # 清理权限缓存过期数据
            permission_cache = get_permission_cache()
            # 权限缓存有自动清理机制，这里可以强制清理
            
            # 清理审计日志
            permission_auditor = get_permission_auditor()
            audit_cleared = permission_auditor.clear_old_logs(168)  # 保留7天
            
            # 清理告警数据
            alert_service = get_alert_service()
            alerts_cleared = alert_service.clear_old_alerts(168)  # 保留7天
            
            logger.info(f"清理任务完成: 审计日志 {audit_cleared} 条, 告警 {alerts_cleared} 条")
            
        except Exception as e:
            logger.error(f"清理任务失败: {e}")
    
    async def _daily_report_task(self):
        """每日报告任务"""
        try:
            # 生成每日监控报告
            current_time = datetime.now()
            
            # 收集24小时内的统计数据
            error_monitor = get_error_monitor()
            daily_performance = error_monitor.get_performance_metrics(86400)  # 24小时
            daily_errors = error_monitor.get_error_statistics(86400)
            
            business_service = get_business_metrics_service()
            business_summary = business_service.get_metrics_summary(24)
            
            alert_service = get_alert_service()
            daily_alerts = alert_service.get_alert_history(24)
            alert_stats = alert_service.get_stats()
            
            permission_cache = get_permission_cache()
            cache_stats = permission_cache.get_stats()
            
            permission_auditor = get_permission_auditor()
            audit_stats = permission_auditor.get_stats()
            
            # 生成报告
            report = {
                "date": current_time.strftime("%Y-%m-%d"),
                "performance": {
                    "total_requests": daily_performance.get("total_requests", 0),
                    "avg_response_time": daily_performance.get("avg_response_time", 0),
                    "error_rate": daily_performance.get("error_rate", 0),
                    "p95_response_time": daily_performance.get("p95_response_time", 0)
                },
                "errors": {
                    "total_errors": daily_errors.get("total_errors", 0),
                    "error_types": len(daily_errors.get("error_breakdown", {}))
                },
                "alerts": {
                    "total_alerts": len(daily_alerts),
                    "critical_alerts": len([a for a in daily_alerts if a.level.value == "critical"]),
                    "resolved_alerts": len([a for a in daily_alerts if a.resolved])
                },
                "cache": {
                    "hit_rate": cache_stats.get("hit_rate", 0),
                    "total_operations": cache_stats.get("hits", 0) + cache_stats.get("misses", 0)
                },
                "audit": {
                    "total_logs": audit_stats.get("total_logs", 0),
                    "success_rate": audit_stats.get("success_rate", 0)
                },
                "business": business_summary.get("latest_metrics", {})
            }
            
            # 记录每日报告
            logger.info(f"每日监控报告生成完成: {report}")
            
            # 可以在这里发送报告邮件或保存到文件
            
        except Exception as e:
            logger.error(f"每日报告任务失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "running": self.running,
            "schedules": {
                name: {
                    "interval": schedule["interval"],
                    "last_run": schedule["last_run"],
                    "next_run": schedule["last_run"] + schedule["interval"],
                    "task_running": name in self.tasks and not self.tasks[name].done()
                }
                for name, schedule in self.schedules.items()
            },
            "active_tasks": len([task for task in self.tasks.values() if not task.done()])
        }
    
    async def run_task_now(self, task_name: str) -> bool:
        """立即运行指定任务"""
        if task_name not in self.schedules:
            return False
        
        if task_name in self.tasks and not self.tasks[task_name].done():
            logger.warning(f"任务 {task_name} 正在运行中")
            return False
        
        self.tasks[task_name] = asyncio.create_task(self._run_task(task_name))
        self.schedules[task_name]["last_run"] = time.time()
        
        logger.info(f"手动触发监控任务: {task_name}")
        return True


# 全局监控调度器实例
monitoring_scheduler = MonitoringScheduler()


def get_monitoring_scheduler() -> MonitoringScheduler:
    """获取监控调度器实例"""
    return monitoring_scheduler


# 启动函数，在应用启动时调用
async def start_monitoring():
    """启动监控服务"""
    scheduler = get_monitoring_scheduler()
    await scheduler.start()
    logger.info("监控服务已启动")


# 停止函数，在应用关闭时调用
async def stop_monitoring():
    """停止监控服务"""
    scheduler = get_monitoring_scheduler()
    await scheduler.stop()
    logger.info("监控服务已停止")
