"""
数据库配置和初始化
"""

from tortoise import Tortoise
from loguru import logger

from app.core.config import settings


# Tortoise ORM配置
TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "app.models.knowledge", 
                "app.models.conversation",
                "app.models.system",
            ],
            "default_connection": "default",
        },
    },
}


async def init_db():
    """初始化数据库"""
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas()
        logger.info("数据库初始化成功")
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
    from app.models.user import User, Role, Permission
    from app.models.system import SystemConfig
    
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
        
        # 创建系统配置
        configs = [
            ("system.name", "企业级Agent+RAG知识库系统", "system", "系统名称"),
            ("system.version", "1.0.0", "system", "系统版本"),
            ("system.description", "基于多智能体协作的企业级知识库系统", "system", "系统描述"),
            ("ai.llm_model", "deepseek-chat", "ai_model", "默认LLM模型"),
            ("ai.embedding_model", "text-embedding-v1", "ai_model", "默认嵌入模型"),
            ("ai.reranker_model", "gte-rerank", "ai_model", "默认重排模型"),
            ("retrieval.default_top_k", 10, "feature", "默认检索数量"),
            ("retrieval.score_threshold", 0.7, "feature", "相似度阈值"),
            ("chunk.size", 1000, "feature", "分块大小"),
            ("chunk.overlap", 200, "feature", "分块重叠"),
        ]
        
        for key, value, config_type, name in configs:
            config = await SystemConfig.get_or_none(key=key)
            if not config:
                await SystemConfig.create(
                    key=key,
                    value=value,
                    config_type=config_type,
                    name=name
                )
        
        logger.info("创建系统配置")
        
    except Exception as e:
        logger.error(f"创建初始数据失败: {e}")
        raise
