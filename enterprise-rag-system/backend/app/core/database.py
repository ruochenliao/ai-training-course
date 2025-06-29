"""
数据库配置和初始化
"""

from loguru import logger
from tortoise import Tortoise

from app.core import settings

# Tortoise ORM配置
TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL.replace("mysql+aiomysql://", "mysql://")
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "app.models.knowledge",
                "app.models.conversation",
                "app.models.system",
                "app.models.rbac",  # 添加RBAC模型
            ],
            "default_connection": "default",
        },
    },
}


async def init_db():
    """初始化数据库"""
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        # 安全地生成表结构，不会覆盖已存在的表
        await Tortoise.generate_schemas(safe=True)
        logger.info("数据库初始化成功")

        # 初始化RBAC基础数据（如果失败不影响系统启动）
        try:
            from app.core import init_rbac_data
            await init_rbac_data()
        except Exception as rbac_error:
            logger.warning(f"RBAC初始化失败，系统将以基础模式启动: {rbac_error}")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def close_db():
    """关闭数据库连接"""
    try:
        await Tortoise.close_connections()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


async def create_initial_data():
    """创建初始数据"""
    from app.models import User, Role, Permission
    from app.models import SystemConfig
    
    try:
        # 创建超级管理员
        admin_user = await User.get_or_none(username="admin")
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="系统管理员",
                is_superuser=True,
                is_staff=True,
                status="active"
            )
            admin_user.set_password("admin123")
            await admin_user.save()
            logger.info("创建超级管理员账户: admin/admin123")
        
        # 创建默认角色
        admin_role = await Role.get_or_none(code="admin")
        if not admin_role:
            admin_role = await Role.create(
                name="管理员",
                code="admin",
                description="系统管理员角色"
            )
            logger.info("创建管理员角色")
        
        user_role = await Role.get_or_none(code="user")
        if not user_role:
            user_role = await Role.create(
                name="普通用户",
                code="user", 
                description="普通用户角色"
            )
            logger.info("创建普通用户角色")
        
        # 创建默认权限
        permissions = [
            ("user:read", "用户查看", "user", "user", "read"),
            ("user:write", "用户编辑", "user", "user", "write"),
            ("user:manage", "用户管理", "user", "user", "manage"),
            ("knowledge_base:read", "知识库查看", "knowledge", "knowledge_base", "read"),
            ("knowledge_base:write", "知识库编辑", "knowledge", "knowledge_base", "write"),
            ("knowledge_base:manage", "知识库管理", "knowledge", "knowledge_base", "manage"),
            ("document:read", "文档查看", "knowledge", "document", "read"),
            ("document:write", "文档编辑", "knowledge", "document", "write"),
            ("document:upload", "文档上传", "knowledge", "document", "upload"),
            ("chat:access", "聊天访问", "chat", "chat", "access"),
            ("search:access", "搜索访问", "search", "search", "access"),
        ]
        
        for code, name, group, resource, action in permissions:
            permission = await Permission.get_or_none(code=code)
            if not permission:
                await Permission.create(
                    name=name,
                    code=code,
                    group=group,
                    resource=resource,
                    action=action
                )
        
        logger.info("创建默认权限")
        
        # 系统配置已通过数据库迁移文件创建，这里只做检查
        config_count = await SystemConfig.all().count()
        if config_count > 0:
            logger.info(f"系统配置已存在，共 {config_count} 项配置")
        else:
            logger.warning("系统配置为空，请检查数据库迁移是否正确执行")
        
    except Exception as e:
        logger.error(f"创建初始数据失败: {e}")
        raise
