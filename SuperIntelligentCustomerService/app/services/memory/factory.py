"""
记忆服务工厂类
提供记忆服务的创建、管理和生命周期控制
支持单例模式、健康检查和优雅关闭
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

from .base import BaseMemoryService, MemoryType, ServiceStatus
from .chat_memory import ChatMemoryService
from .private_memory import PrivateMemoryService
from .public_memory import PublicMemoryService

logger = logging.getLogger(__name__)


class MemoryServiceFactory:
    """
    记忆服务工厂类
    管理不同类型记忆服务的创建和生命周期，实现单例模式避免重复创建
    """

    def __init__(self, db_path: str = None):
        """
        初始化记忆服务工厂

        Args:
            db_path: 数据库路径（用于聊天记忆服务）
        """
        self.db_path = db_path
        self.created_at = datetime.now()

        # 服务实例缓存
        self._chat_memory_services: Dict[str, ChatMemoryService] = {}
        self._private_memory_services: Dict[str, PrivateMemoryService] = {}
        self._public_memory_service: Optional[PublicMemoryService] = None

        # 服务统计
        self._service_stats = {
            "total_created": 0,
            "active_services": 0,
            "error_count": 0
        }

        logger.info("记忆服务工厂初始化完成")
    
    def get_chat_memory_service(self, user_id: str) -> ChatMemoryService:
        """
        获取聊天记忆服务（单例模式）

        Args:
            user_id: 用户ID

        Returns:
            聊天记忆服务实例
        """
        try:
            if user_id not in self._chat_memory_services:
                service = ChatMemoryService(user_id=user_id, db_path=self.db_path)
                self._chat_memory_services[user_id] = service
                self._service_stats["total_created"] += 1
                self._service_stats["active_services"] += 1
                logger.info(f"创建聊天记忆服务: {user_id}")

            return self._chat_memory_services[user_id]
        except Exception as e:
            self._service_stats["error_count"] += 1
            logger.error(f"获取聊天记忆服务失败: {e}")
            raise

    def get_private_memory_service(self, user_id: str) -> PrivateMemoryService:
        """
        获取私有记忆服务（单例模式）

        Args:
            user_id: 用户ID

        Returns:
            私有记忆服务实例
        """
        try:
            if user_id not in self._private_memory_services:
                service = PrivateMemoryService(user_id=user_id)
                self._private_memory_services[user_id] = service
                self._service_stats["total_created"] += 1
                self._service_stats["active_services"] += 1
                logger.info(f"创建私有记忆服务: {user_id}")

            return self._private_memory_services[user_id]
        except Exception as e:
            self._service_stats["error_count"] += 1
            logger.error(f"获取私有记忆服务失败: {e}")
            raise

    def get_public_memory_service(self) -> PublicMemoryService:
        """
        获取公共记忆服务（单例模式）

        Returns:
            公共记忆服务实例
        """
        try:
            if self._public_memory_service is None:
                service = PublicMemoryService()
                self._public_memory_service = service
                self._service_stats["total_created"] += 1
                self._service_stats["active_services"] += 1
                logger.info("创建公共记忆服务")

            return self._public_memory_service
        except Exception as e:
            self._service_stats["error_count"] += 1
            logger.error(f"获取公共记忆服务失败: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        执行所有服务的健康检查

        Returns:
            健康检查结果
        """
        health_status = {
            "factory_status": "healthy",
            "factory_uptime": (datetime.now() - self.created_at).total_seconds(),
            "service_stats": self._service_stats.copy(),
            "services": {}
        }

        try:
            # 检查聊天记忆服务
            for user_id, service in self._chat_memory_services.items():
                health_status["services"][f"chat_{user_id}"] = await service.health_check()

            # 检查私有记忆服务
            for user_id, service in self._private_memory_services.items():
                health_status["services"][f"private_{user_id}"] = await service.health_check()

            # 检查公共记忆服务
            if self._public_memory_service:
                health_status["services"]["public"] = await self._public_memory_service.health_check()

            # 统计健康状态
            error_services = [
                name for name, status in health_status["services"].items()
                if status.get("status") == ServiceStatus.ERROR.value
            ]

            if error_services:
                health_status["factory_status"] = "degraded"
                health_status["error_services"] = error_services

        except Exception as e:
            health_status["factory_status"] = "error"
            health_status["error"] = str(e)
            logger.error(f"健康检查失败: {e}")

        return health_status

    async def cleanup_inactive_services(self, max_idle_hours: int = 24) -> int:
        """
        清理长时间未使用的服务

        Args:
            max_idle_hours: 最大空闲时间（小时）

        Returns:
            清理的服务数量
        """
        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_idle_hours)

        try:
            # 清理聊天记忆服务
            inactive_chat_users = []
            for user_id, service in self._chat_memory_services.items():
                if service.last_accessed and service.last_accessed < cutoff_time:
                    await service.close()
                    inactive_chat_users.append(user_id)
                    cleaned_count += 1

            for user_id in inactive_chat_users:
                del self._chat_memory_services[user_id]

            # 清理私有记忆服务
            inactive_private_users = []
            for user_id, service in self._private_memory_services.items():
                if service.last_accessed and service.last_accessed < cutoff_time:
                    await service.close()
                    inactive_private_users.append(user_id)
                    cleaned_count += 1

            for user_id in inactive_private_users:
                del self._private_memory_services[user_id]

            # 更新统计
            self._service_stats["active_services"] -= cleaned_count

            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个非活跃服务")

        except Exception as e:
            logger.error(f"清理非活跃服务失败: {e}")

        return cleaned_count

    async def close_all_services(self) -> None:
        """
        优雅关闭所有服务
        """
        try:
            # 关闭所有聊天记忆服务
            for service in self._chat_memory_services.values():
                await service.close()

            # 关闭所有私有记忆服务
            for service in self._private_memory_services.values():
                await service.close()

            # 关闭公共记忆服务
            if self._public_memory_service:
                await self._public_memory_service.close()

            logger.info("所有记忆服务已关闭")

        except Exception as e:
            logger.error(f"关闭服务时发生错误: {e}")

    def clear_cache(self) -> None:
        """
        清理缓存的服务实例（同步方法，向后兼容）
        """
        asyncio.create_task(self.close_all_services())
        self._chat_memory_services.clear()
        self._private_memory_services.clear()
        self._public_memory_service = None
        self._service_stats["active_services"] = 0
        logger.info("服务缓存已清理")

    def get_service_by_type(self, memory_type: MemoryType, user_id: str = None) -> BaseMemoryService:
        """
        根据记忆类型获取服务

        Args:
            memory_type: 记忆类型
            user_id: 用户ID（聊天和私有记忆需要）

        Returns:
            记忆服务实例
        """
        if memory_type == MemoryType.CHAT:
            if not user_id:
                raise ValueError("聊天记忆服务需要用户ID")
            return self.get_chat_memory_service(user_id)
        elif memory_type == MemoryType.PRIVATE:
            if not user_id:
                raise ValueError("私有记忆服务需要用户ID")
            return self.get_private_memory_service(user_id)
        elif memory_type == MemoryType.PUBLIC:
            return self.get_public_memory_service()
        else:
            raise ValueError(f"不支持的记忆类型: {memory_type}")

    def get_all_services(self) -> List[BaseMemoryService]:
        """
        获取所有活跃的服务实例

        Returns:
            服务实例列表
        """
        services = []

        # 添加聊天记忆服务
        services.extend(self._chat_memory_services.values())

        # 添加私有记忆服务
        services.extend(self._private_memory_services.values())

        # 添加公共记忆服务
        if self._public_memory_service:
            services.append(self._public_memory_service)

        return services

    def get_factory_stats(self) -> Dict[str, Any]:
        """
        获取工厂统计信息

        Returns:
            统计信息
        """
        return {
            "created_at": self.created_at.isoformat(),
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
            "service_stats": self._service_stats.copy(),
            "active_chat_services": len(self._chat_memory_services),
            "active_private_services": len(self._private_memory_services),
            "public_service_active": self._public_memory_service is not None
        }
