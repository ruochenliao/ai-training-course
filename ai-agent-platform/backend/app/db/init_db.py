"""
数据库初始化脚本
"""
import logging
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db, check_db_connection
from app import crud
from app.schemas.user import UserCreate
from app.core.config import settings
from app.models.user import Role
from app.models.agent import AgentTemplate, AgentType, AgentStatus
from app.models.knowledge import KnowledgeBaseType
from app.models.chat import Conversation, ChatSession, SessionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_initial_roles(db: Session) -> None:
    """
    创建初始角色数据
    """
    logger.info("创建初始角色数据...")

    # 基础角色数据
    roles_data = [
        {
            "name": "admin",
            "description": "系统管理员，拥有所有权限",
            "permissions": {
                "users": ["create", "read", "update", "delete"],
                "agents": ["create", "read", "update", "delete"],
                "knowledge": ["create", "read", "update", "delete"],
                "chat": ["create", "read", "update", "delete"],
                "system": ["read", "update"]
            },
            "is_active": True
        },
        {
            "name": "user",
            "description": "普通用户，基础功能权限",
            "permissions": {
                "agents": ["create", "read", "update"],
                "knowledge": ["create", "read", "update"],
                "chat": ["create", "read", "update"],
                "profile": ["read", "update"]
            },
            "is_active": True
        },
        {
            "name": "viewer",
            "description": "访客用户，只读权限",
            "permissions": {
                "agents": ["read"],
                "knowledge": ["read"],
                "chat": ["read"]
            },
            "is_active": True
        }
    ]

    for role_data in roles_data:
        # 检查角色是否已存在
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.add(role)
            logger.info(f"创建角色: {role_data['name']}")
        else:
            logger.info(f"角色已存在: {role_data['name']}")

    db.commit()


def create_agent_templates(db: Session) -> None:
    """
    创建智能体模板数据
    """
    logger.info("创建智能体模板数据...")

    # 智能体模板数据
    templates_data = [
        {
            "name": "智能客服助手",
            "description": "专业的客服助手，能够回答常见问题，处理客户咨询",
            "category": "客服",
            "avatar_url": "/avatars/customer-service.png",
            "template_config": {
                "model_name": "gpt-3.5-turbo",
                "temperature": "0.7",
                "max_tokens": "2000"
            },
            "prompt_template": "你是一个专业的客服助手。请以友好、耐心的态度回答用户的问题。如果遇到无法解决的问题，请引导用户联系人工客服。",
            "tags": ["客服", "问答", "助手"],
            "sort_order": "1",
            "is_active": True,
            "is_featured": True,
            "use_count": "0"
        },
        {
            "name": "代码助手",
            "description": "专业的编程助手，帮助解决代码问题，提供编程建议",
            "category": "编程",
            "avatar_url": "/avatars/code-assistant.png",
            "template_config": {
                "model_name": "gpt-4",
                "temperature": "0.3",
                "max_tokens": "3000"
            },
            "prompt_template": "你是一个专业的编程助手。请帮助用户解决编程问题，提供清晰的代码示例和解释。支持多种编程语言。",
            "tags": ["编程", "代码", "开发"],
            "sort_order": "2",
            "is_active": True,
            "is_featured": True,
            "use_count": "0"
        },
        {
            "name": "文案创作助手",
            "description": "专业的文案创作助手，帮助创作各类文案内容",
            "category": "创作",
            "avatar_url": "/avatars/writer.png",
            "template_config": {
                "model_name": "gpt-3.5-turbo",
                "temperature": "0.8",
                "max_tokens": "2500"
            },
            "prompt_template": "你是一个专业的文案创作助手。请根据用户需求创作高质量的文案内容，包括广告文案、产品描述、社交媒体内容等。",
            "tags": ["文案", "创作", "营销"],
            "sort_order": "3",
            "is_active": True,
            "is_featured": True,
            "use_count": "0"
        },
        {
            "name": "数据分析助手",
            "description": "专业的数据分析助手，帮助分析数据，生成报告",
            "category": "分析",
            "avatar_url": "/avatars/data-analyst.png",
            "template_config": {
                "model_name": "gpt-4",
                "temperature": "0.5",
                "max_tokens": "3000"
            },
            "prompt_template": "你是一个专业的数据分析助手。请帮助用户分析数据，提供洞察和建议，生成清晰的分析报告。",
            "tags": ["数据", "分析", "报告"],
            "sort_order": "4",
            "is_active": True,
            "is_featured": False,
            "use_count": "0"
        },
        {
            "name": "学习助手",
            "description": "专业的学习助手，帮助解答学习问题，提供学习建议",
            "category": "教育",
            "avatar_url": "/avatars/tutor.png",
            "template_config": {
                "model_name": "gpt-3.5-turbo",
                "temperature": "0.6",
                "max_tokens": "2000"
            },
            "prompt_template": "你是一个专业的学习助手。请帮助用户解答学习问题，提供清晰的解释和学习建议。适合各个年龄段的学习者。",
            "tags": ["教育", "学习", "辅导"],
            "sort_order": "5",
            "is_active": True,
            "is_featured": False,
            "use_count": "0"
        },
        {
            "name": "翻译助手",
            "description": "专业的翻译助手，支持多语言翻译和语言学习",
            "category": "语言",
            "avatar_url": "/avatars/translator.png",
            "template_config": {
                "model_name": "gpt-3.5-turbo",
                "temperature": "0.3",
                "max_tokens": "2000"
            },
            "prompt_template": "你是一个专业的翻译助手。请提供准确的翻译服务，支持多种语言之间的翻译，并能解释语言用法和文化背景。",
            "tags": ["翻译", "语言", "国际化"],
            "sort_order": "6",
            "is_active": True,
            "is_featured": False,
            "use_count": "0"
        }
    ]

    for template_data in templates_data:
        # 检查模板是否已存在
        existing_template = db.query(AgentTemplate).filter(
            AgentTemplate.name == template_data["name"]
        ).first()
        if not existing_template:
            template = AgentTemplate(**template_data)
            db.add(template)
            logger.info(f"创建智能体模板: {template_data['name']}")
        else:
            logger.info(f"智能体模板已存在: {template_data['name']}")

    db.commit()


def create_sample_chat_sessions(db: Session, user) -> None:
    """
    创建示例聊天会话数据
    """
    logger.info("创建示例聊天会话数据...")

    # 获取第一个智能体
    from app.models.agent import Agent
    agent = db.query(Agent).first()

    if not agent:
        logger.warning("没有找到智能体，跳过创建示例聊天会话")
        return

    # 示例聊天会话数据
    sessions_data = [
        {
            "title": "智能体功能咨询",
            "status": SessionStatus.ACTIVE,
            "user_id": user.id,
            "agent_id": agent.id,
            "config": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "context": {
                "topic": "智能体功能介绍",
                "language": "zh-CN"
            },
            "message_count": 2,
            "total_tokens": 150,
            "is_pinned": False,
            "is_archived": False
        },
        {
            "title": "平台使用指南",
            "status": SessionStatus.ACTIVE,
            "user_id": user.id,
            "agent_id": agent.id,
            "config": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.6,
                "max_tokens": 2000
            },
            "context": {
                "topic": "平台使用教程",
                "language": "zh-CN"
            },
            "message_count": 4,
            "total_tokens": 300,
            "is_pinned": True,
            "is_archived": False
        },
        {
            "title": "技术支持咨询",
            "status": SessionStatus.ENDED,
            "user_id": user.id,
            "agent_id": agent.id,
            "config": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.5,
                "max_tokens": 2000
            },
            "context": {
                "topic": "技术问题解答",
                "language": "zh-CN"
            },
            "message_count": 6,
            "total_tokens": 450,
            "is_pinned": False,
            "is_archived": True
        }
    ]

    for session_data in sessions_data:
        # 检查会话是否已存在
        existing_session = db.query(ChatSession).filter(
            ChatSession.title == session_data["title"],
            ChatSession.user_id == user.id
        ).first()

        if not existing_session:
            session = ChatSession(**session_data)
            db.add(session)
            logger.info(f"创建示例聊天会话: {session_data['title']}")
        else:
            logger.info(f"示例聊天会话已存在: {session_data['title']}")

    db.commit()


def create_initial_data(db: Session) -> None:
    """
    创建初始数据

    Args:
        db: 数据库会话
    """
    # 检查是否已存在超级用户
    user = crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER_EMAIL,
            username=settings.FIRST_SUPERUSER_USERNAME,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            full_name="Super User",
            is_superuser=True,
            is_active=True,
        )
        user = crud.user.create(db, obj_in=user_in)
        logger.info(f"创建超级用户: {user.email}")
    else:
        logger.info(f"超级用户已存在: {user.email}")

    # 创建基础角色
    create_initial_roles(db)

    # 创建智能体模板
    create_agent_templates(db)

    # 创建示例聊天会话
    create_sample_chat_sessions(db, user)


def is_database_empty(db: Session) -> bool:
    """
    检查数据库是否为空（没有用户数据）
    """
    try:
        # 检查用户表是否有数据
        user_count = db.query(crud.user.model).count()
        return user_count == 0
    except Exception as e:
        logger.warning(f"检查数据库状态失败: {e}")
        return True  # 如果检查失败，假设数据库为空


def init() -> None:
    """
    初始化数据库和数据
    """
    # 检查数据库连接
    if not check_db_connection():
        logger.error("❌ 数据库连接失败，请检查配置")
        return

    # 自动创建数据库表（静默）
    init_db()
    logger.info("✅ 数据库表检查完成")

    # 检查是否需要初始化数据
    db = SessionLocal()
    try:
        if is_database_empty(db):
            logger.info("📊 初始化基础数据...")
            create_initial_data(db)
            logger.info("✅ 数据库初始化完成")
        else:
            logger.info("📊 数据库已就绪")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init()
