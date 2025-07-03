"""
添加部门字段到用户表的迁移脚本
"""

from tortoise import Tortoise
from app.core.config import settings


async def upgrade():
    """升级数据库结构"""
    # 连接数据库
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]}
    )
    
    # 获取数据库连接
    conn = Tortoise.get_connection("default")
    
    try:
        # 创建部门表
        await conn.execute_script("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                parent_id INTEGER,
                level INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                manager_id INTEGER,
                phone VARCHAR(20),
                email VARCHAR(100),
                address VARCHAR(255),
                is_active BOOLEAN DEFAULT 1,
                is_deleted BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES departments (id),
                FOREIGN KEY (manager_id) REFERENCES users (id)
            );
        """)
        
        # 添加部门字段到用户表
        await conn.execute_script("""
            ALTER TABLE users ADD COLUMN department_id INTEGER;
        """)
        
        # 添加外键约束（如果数据库支持）
        try:
            await conn.execute_script("""
                ALTER TABLE users ADD CONSTRAINT fk_user_department 
                FOREIGN KEY (department_id) REFERENCES departments (id);
            """)
        except:
            # 如果数据库不支持添加外键约束，忽略错误
            pass
        
        print("数据库迁移完成：添加了部门表和用户部门关联字段")
        
    except Exception as e:
        print(f"迁移过程中出现错误: {e}")
        raise
    
    finally:
        await Tortoise.close_connections()


async def downgrade():
    """降级数据库结构"""
    # 连接数据库
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]}
    )
    
    # 获取数据库连接
    conn = Tortoise.get_connection("default")
    
    try:
        # 删除用户表的部门字段
        await conn.execute_script("""
            ALTER TABLE users DROP COLUMN department_id;
        """)
        
        # 删除部门表
        await conn.execute_script("""
            DROP TABLE IF EXISTS departments;
        """)
        
        print("数据库回滚完成：删除了部门表和用户部门关联字段")
        
    except Exception as e:
        print(f"回滚过程中出现错误: {e}")
        raise
    
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    import asyncio
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
