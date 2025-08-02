"""
数据库初始化脚本
"""
import logging
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db, check_db_connection
from app import crud
from app.schemas.user import UserCreate
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def init() -> None:
    """
    初始化数据库和数据
    """
    logger.info("开始初始化数据库...")
    
    # 检查数据库连接
    if not check_db_connection():
        logger.error("数据库连接失败，请检查配置")
        return
    
    # 创建数据库表
    init_db()
    
    # 创建初始数据
    db = SessionLocal()
    try:
        create_initial_data(db)
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"创建初始数据失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init()
