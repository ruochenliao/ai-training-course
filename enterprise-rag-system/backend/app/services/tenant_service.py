"""
多租户支持服务
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional

# 移除 get_database 导入，使用 Tortoise ORM
from app.models.knowledge import KnowledgeBase
from app.models.user import User
from loguru import logger

from app.core.exceptions import TenantException


class TenantStatus(Enum):
    """租户状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"


class SubscriptionPlan(Enum):
    """订阅计划"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class TenantConfig:
    """租户配置"""
    max_users: int = 10
    max_knowledge_bases: int = 5
    max_documents: int = 1000
    max_storage_gb: int = 10
    max_api_calls_per_day: int = 10000
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []


@dataclass
class TenantUsage:
    """租户使用情况"""
    users_count: int = 0
    knowledge_bases_count: int = 0
    documents_count: int = 0
    storage_used_gb: float = 0.0
    api_calls_today: int = 0
    last_activity: Optional[datetime] = None


@dataclass
class Tenant:
    """租户信息"""
    id: int
    name: str
    domain: str
    status: TenantStatus
    plan: SubscriptionPlan
    config: TenantConfig
    usage: TenantUsage
    created_at: datetime
    expires_at: Optional[datetime] = None
    owner_id: Optional[int] = None


class TenantService:
    """多租户服务类"""
    
    def __init__(self):
        """初始化多租户服务"""
        # 使用 Tortoise ORM，不需要数据库连接池
        
        # 预定义计划配置
        self.plan_configs = {
            SubscriptionPlan.FREE: TenantConfig(
                max_users=5,
                max_knowledge_bases=2,
                max_documents=100,
                max_storage_gb=1,
                max_api_calls_per_day=1000,
                features=["basic_search", "document_upload"]
            ),
            SubscriptionPlan.BASIC: TenantConfig(
                max_users=20,
                max_knowledge_bases=10,
                max_documents=5000,
                max_storage_gb=10,
                max_api_calls_per_day=10000,
                features=["basic_search", "document_upload", "advanced_search", "analytics"]
            ),
            SubscriptionPlan.PROFESSIONAL: TenantConfig(
                max_users=100,
                max_knowledge_bases=50,
                max_documents=50000,
                max_storage_gb=100,
                max_api_calls_per_day=100000,
                features=["basic_search", "document_upload", "advanced_search", "analytics", "api_access", "custom_models"]
            ),
            SubscriptionPlan.ENTERPRISE: TenantConfig(
                max_users=-1,  # 无限制
                max_knowledge_bases=-1,
                max_documents=-1,
                max_storage_gb=-1,
                max_api_calls_per_day=-1,
                features=["all"]
            )
        }
        
        logger.info("多租户服务初始化完成")
    
    async def create_tenant(
        self,
        name: str,
        domain: str,
        plan: SubscriptionPlan,
        owner_email: str,
        trial_days: int = 30
    ) -> Tenant:
        """创建新租户"""
        try:
            # 检查域名是否已存在
            existing = await self._get_tenant_by_domain(domain)
            if existing:
                raise TenantException(f"域名 {domain} 已被使用")
            
            # 获取计划配置
            config = self.plan_configs[plan]
            
            # 设置过期时间
            expires_at = None
            status = TenantStatus.ACTIVE
            if plan == SubscriptionPlan.FREE or trial_days > 0:
                expires_at = datetime.now() + timedelta(days=trial_days)
                status = TenantStatus.TRIAL
            
            # 创建租户记录
            tenant_id = await self._create_tenant_record(
                name, domain, status, plan, config, expires_at
            )
            
            # 创建租户管理员用户
            admin_user = await self._create_tenant_admin(tenant_id, owner_email)
            
            # 更新租户所有者
            await self._update_tenant_owner(tenant_id, admin_user.id)
            
            # 初始化租户资源
            await self._initialize_tenant_resources(tenant_id)
            
            tenant = await self.get_tenant(tenant_id)
            logger.info(f"创建租户成功: {name} ({domain})")
            
            return tenant
            
        except Exception as e:
            logger.error(f"创建租户失败: {e}")
            raise TenantException(f"创建租户失败: {e}")
    
    async def get_tenant(self, tenant_id: int) -> Tenant:
        """获取租户信息"""
        try:
            query = """
            SELECT * FROM tenants WHERE id = %s
            """
            
            async with self.db.acquire() as conn:
                row = await conn.fetchrow(query, tenant_id)
                
            if not row:
                raise TenantException(f"租户 {tenant_id} 不存在")
            
            # 获取使用情况
            usage = await self._get_tenant_usage(tenant_id)
            
            # 构建租户对象
            tenant = Tenant(
                id=row["id"],
                name=row["name"],
                domain=row["domain"],
                status=TenantStatus(row["status"]),
                plan=SubscriptionPlan(row["plan"]),
                config=self._parse_config(row["config"]),
                usage=usage,
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                owner_id=row["owner_id"]
            )
            
            return tenant
            
        except Exception as e:
            logger.error(f"获取租户信息失败: {e}")
            raise TenantException(f"获取租户信息失败: {e}")
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """根据域名获取租户"""
        try:
            tenant_row = await self._get_tenant_by_domain(domain)
            if not tenant_row:
                return None
            
            return await self.get_tenant(tenant_row["id"])
            
        except Exception as e:
            logger.error(f"根据域名获取租户失败: {e}")
            return None
    
    async def update_tenant_plan(
        self,
        tenant_id: int,
        new_plan: SubscriptionPlan,
        extend_days: int = 0
    ) -> Tenant:
        """更新租户计划"""
        try:
            tenant = await self.get_tenant(tenant_id)
            
            # 检查是否可以降级
            if new_plan.value < tenant.plan.value:
                await self._validate_downgrade(tenant, new_plan)
            
            # 获取新计划配置
            new_config = self.plan_configs[new_plan]
            
            # 更新过期时间
            new_expires_at = tenant.expires_at
            if extend_days > 0:
                base_date = tenant.expires_at if tenant.expires_at else datetime.now()
                new_expires_at = base_date + timedelta(days=extend_days)
            
            # 更新数据库
            query = """
            UPDATE tenants
            SET plan = %s, config = %s, expires_at = %s, updated_at = %s
            WHERE id = %s
            """
            
            async with self.db.acquire() as conn:
                await conn.execute(
                    query,
                    new_plan.value,
                    self._serialize_config(new_config),
                    new_expires_at,
                    datetime.now(),
                    tenant_id
                )
            
            logger.info(f"更新租户计划: {tenant_id} -> {new_plan.value}")
            return await self.get_tenant(tenant_id)
            
        except Exception as e:
            logger.error(f"更新租户计划失败: {e}")
            raise TenantException(f"更新租户计划失败: {e}")
    
    async def check_tenant_limits(
        self,
        tenant_id: int,
        resource_type: str,
        requested_amount: int = 1
    ) -> bool:
        """检查租户资源限制"""
        try:
            tenant = await self.get_tenant(tenant_id)
            
            # 检查租户状态
            if tenant.status not in [TenantStatus.ACTIVE, TenantStatus.TRIAL]:
                return False
            
            # 检查过期时间
            if tenant.expires_at and tenant.expires_at < datetime.now():
                await self._update_tenant_status(tenant_id, TenantStatus.EXPIRED)
                return False
            
            # 检查具体资源限制
            if resource_type == "users":
                limit = tenant.config.max_users
                current = tenant.usage.users_count
            elif resource_type == "knowledge_bases":
                limit = tenant.config.max_knowledge_bases
                current = tenant.usage.knowledge_bases_count
            elif resource_type == "documents":
                limit = tenant.config.max_documents
                current = tenant.usage.documents_count
            elif resource_type == "storage":
                limit = tenant.config.max_storage_gb
                current = tenant.usage.storage_used_gb
            elif resource_type == "api_calls":
                limit = tenant.config.max_api_calls_per_day
                current = tenant.usage.api_calls_today
            else:
                return True  # 未知资源类型，默认允许
            
            # -1 表示无限制
            if limit == -1:
                return True
            
            return (current + requested_amount) <= limit
            
        except Exception as e:
            logger.error(f"检查租户限制失败: {e}")
            return False
    
    async def check_feature_access(
        self,
        tenant_id: int,
        feature: str
    ) -> bool:
        """检查功能访问权限"""
        try:
            tenant = await self.get_tenant(tenant_id)
            
            # 检查租户状态
            if tenant.status not in [TenantStatus.ACTIVE, TenantStatus.TRIAL]:
                return False
            
            # 企业版拥有所有功能
            if "all" in tenant.config.features:
                return True
            
            return feature in tenant.config.features
            
        except Exception as e:
            logger.error(f"检查功能访问权限失败: {e}")
            return False
    
    async def record_api_usage(self, tenant_id: int, calls_count: int = 1):
        """记录API使用量"""
        try:
            today = datetime.now().date()
            
            query = """
            INSERT INTO tenant_api_usage (tenant_id, date, calls_count)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE calls_count = calls_count + %s
            """
            
            async with self.db.acquire() as conn:
                await conn.execute(query, tenant_id, today, calls_count, calls_count)
                
        except Exception as e:
            logger.error(f"记录API使用量失败: {e}")
    
    async def get_tenant_analytics(
        self,
        tenant_id: int,
        time_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """获取租户分析数据"""
        try:
            if not time_range:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                time_range = (start_date, end_date)
            
            start_date, end_date = time_range
            
            # 获取基础统计
            tenant = await self.get_tenant(tenant_id)
            
            # 获取使用趋势
            usage_trend = await self._get_usage_trend(tenant_id, start_date, end_date)
            
            # 获取功能使用统计
            feature_usage = await self._get_feature_usage_stats(tenant_id, start_date, end_date)
            
            # 计算资源利用率
            utilization = self._calculate_resource_utilization(tenant)
            
            return {
                "tenant_info": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "plan": tenant.plan.value,
                    "status": tenant.status.value
                },
                "usage_trend": usage_trend,
                "feature_usage": feature_usage,
                "resource_utilization": utilization,
                "current_usage": {
                    "users": tenant.usage.users_count,
                    "knowledge_bases": tenant.usage.knowledge_bases_count,
                    "documents": tenant.usage.documents_count,
                    "storage_gb": tenant.usage.storage_used_gb,
                    "api_calls_today": tenant.usage.api_calls_today
                },
                "limits": {
                    "max_users": tenant.config.max_users,
                    "max_knowledge_bases": tenant.config.max_knowledge_bases,
                    "max_documents": tenant.config.max_documents,
                    "max_storage_gb": tenant.config.max_storage_gb,
                    "max_api_calls_per_day": tenant.config.max_api_calls_per_day
                }
            }
            
        except Exception as e:
            logger.error(f"获取租户分析数据失败: {e}")
            raise TenantException(f"获取租户分析数据失败: {e}")
    
    async def suspend_tenant(self, tenant_id: int, reason: str = ""):
        """暂停租户"""
        try:
            await self._update_tenant_status(tenant_id, TenantStatus.SUSPENDED)
            
            # 记录暂停原因
            if reason:
                await self._log_tenant_action(tenant_id, "suspend", {"reason": reason})
            
            logger.info(f"暂停租户: {tenant_id}, 原因: {reason}")
            
        except Exception as e:
            logger.error(f"暂停租户失败: {e}")
            raise TenantException(f"暂停租户失败: {e}")
    
    async def activate_tenant(self, tenant_id: int):
        """激活租户"""
        try:
            await self._update_tenant_status(tenant_id, TenantStatus.ACTIVE)
            await self._log_tenant_action(tenant_id, "activate", {})
            
            logger.info(f"激活租户: {tenant_id}")
            
        except Exception as e:
            logger.error(f"激活租户失败: {e}")
            raise TenantException(f"激活租户失败: {e}")
    
    # 私有辅助方法
    async def _get_tenant_by_domain(self, domain: str):
        """根据域名获取租户记录"""
        query = "SELECT * FROM tenants WHERE domain = %s"
        async with self.db.acquire() as conn:
            return await conn.fetchrow(query, domain)
    
    async def _create_tenant_record(
        self,
        name: str,
        domain: str,
        status: TenantStatus,
        plan: SubscriptionPlan,
        config: TenantConfig,
        expires_at: Optional[datetime]
    ) -> int:
        """创建租户记录"""
        query = """
        INSERT INTO tenants (name, domain, status, plan, config, expires_at, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        async with self.db.acquire() as conn:
            result = await conn.execute(
                query,
                name,
                domain,
                status.value,
                plan.value,
                self._serialize_config(config),
                expires_at,
                datetime.now()
            )
            return result.lastrowid
    
    async def _create_tenant_admin(self, tenant_id: int, email: str) -> User:
        """创建租户管理员用户"""
        # 这里需要调用用户服务创建管理员
        # 简化实现
        admin_user = await User.create(
            username=f"admin_{tenant_id}",
            email=email,
            hashed_password="temp_password",  # 需要生成临时密码
            is_active=True,
            tenant_id=tenant_id,
            role="admin"
        )
        return admin_user
    
    async def _update_tenant_owner(self, tenant_id: int, owner_id: int):
        """更新租户所有者"""
        query = "UPDATE tenants SET owner_id = %s WHERE id = %s"
        async with self.db.acquire() as conn:
            await conn.execute(query, owner_id, tenant_id)
    
    async def _initialize_tenant_resources(self, tenant_id: int):
        """初始化租户资源"""
        # 创建默认知识库等初始化操作
        pass
    
    async def _get_tenant_usage(self, tenant_id: int) -> TenantUsage:
        """获取租户使用情况"""
        # 获取用户数量
        users_count = await User.filter(tenant_id=tenant_id).count()
        
        # 获取知识库数量
        kb_count = await KnowledgeBase.filter(tenant_id=tenant_id).count()
        
        # 获取文档数量和存储使用量
        # 这里需要根据实际的文档模型实现
        documents_count = 0
        storage_used_gb = 0.0
        
        # 获取今日API调用量
        api_calls_today = await self._get_api_calls_today(tenant_id)
        
        # 获取最后活动时间
        last_activity = await self._get_last_activity(tenant_id)
        
        return TenantUsage(
            users_count=users_count,
            knowledge_bases_count=kb_count,
            documents_count=documents_count,
            storage_used_gb=storage_used_gb,
            api_calls_today=api_calls_today,
            last_activity=last_activity
        )
    
    def _parse_config(self, config_json: str) -> TenantConfig:
        """解析配置JSON"""
        import json
        config_dict = json.loads(config_json) if config_json else {}
        return TenantConfig(**config_dict)
    
    def _serialize_config(self, config: TenantConfig) -> str:
        """序列化配置为JSON"""
        import json
        return json.dumps(config.__dict__)
    
    async def _update_tenant_status(self, tenant_id: int, status: TenantStatus):
        """更新租户状态"""
        query = "UPDATE tenants SET status = %s, updated_at = %s WHERE id = %s"
        async with self.db.acquire() as conn:
            await conn.execute(query, status.value, datetime.now(), tenant_id)
    
    async def _log_tenant_action(self, tenant_id: int, action: str, details: Dict[str, Any]):
        """记录租户操作日志"""
        # 实现租户操作日志记录
        pass
    
    def _calculate_resource_utilization(self, tenant: Tenant) -> Dict[str, float]:
        """计算资源利用率"""
        utilization = {}
        
        if tenant.config.max_users > 0:
            utilization["users"] = (tenant.usage.users_count / tenant.config.max_users) * 100
        
        if tenant.config.max_knowledge_bases > 0:
            utilization["knowledge_bases"] = (tenant.usage.knowledge_bases_count / tenant.config.max_knowledge_bases) * 100
        
        if tenant.config.max_documents > 0:
            utilization["documents"] = (tenant.usage.documents_count / tenant.config.max_documents) * 100
        
        if tenant.config.max_storage_gb > 0:
            utilization["storage"] = (tenant.usage.storage_used_gb / tenant.config.max_storage_gb) * 100
        
        return utilization


# 全局多租户服务实例
tenant_service = TenantService()
