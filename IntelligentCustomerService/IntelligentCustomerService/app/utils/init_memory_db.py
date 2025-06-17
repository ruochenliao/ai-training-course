"""
记忆数据库初始化工具
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

from app.settings import settings

logger = logging.getLogger(__name__)


def init_memory_database(db_path: str = None):
    """初始化记忆数据库"""
    
    if db_path is None:
        # 使用项目配置的数据库路径
        db_path = settings.TORTOISE_ORM["connections"]["sqlite"]["credentials"]["file_path"]
    
    # 确保数据库目录存在
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        # 创建聊天记忆表（仍需要SQLite存储对话历史）
        conn.executescript("""
            -- 聊天记忆表
            CREATE TABLE IF NOT EXISTS chat_memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- 创建聊天记忆索引
            CREATE INDEX IF NOT EXISTS idx_chat_user_session ON chat_memories(user_id, session_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_chat_user_time ON chat_memories(user_id, created_at DESC);

            -- 删除不再使用的私有记忆和公共记忆表
            DROP TABLE IF EXISTS private_memories;
            DROP TABLE IF EXISTS public_memories;
        """)
        
        logger.info(f"记忆数据库初始化完成: {db_path}")
        logger.info("注意：私有记忆和公共记忆现在使用ChromaDB向量数据库存储")


if __name__ == "__main__":
    init_memory_database()
    print("记忆数据库初始化完成！")
