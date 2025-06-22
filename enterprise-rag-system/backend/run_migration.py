#!/usr/bin/env python3
"""
手动运行数据库迁移脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from loguru import logger
from tortoise import Tortoise
from app.core.config import settings


async def run_migration():
    """运行数据库迁移"""
    try:
        # 初始化数据库连接
        await Tortoise.init(
            db_url=settings.DATABASE_URL,
            modules={"models": ["app.models.user", "app.models.knowledge", "app.models.conversation", "app.models.system"]}
        )
        
        logger.info("🔧 开始执行数据库迁移...")
        
        # 获取数据库连接
        db = Tortoise.get_connection("default")
        
        # 导入并执行迁移
        from app.db.migrations.fix_system_configs import upgrade

        logger.info("📝 执行迁移: fix_system_configs")
        migration_sql = await upgrade(db)
        
        # 执行迁移SQL
        await db.execute_script(migration_sql)
        
        logger.info("✅ 数据库迁移完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(run_migration())
