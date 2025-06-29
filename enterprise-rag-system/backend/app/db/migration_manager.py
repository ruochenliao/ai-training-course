"""
数据库迁移管理器
"""

import importlib.util
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger
from tortoise import Tortoise


class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migration_table = "schema_migrations"
    
    async def init_migration_table(self):
        """初始化迁移记录表"""
        db = Tortoise.get_connection("default")
        
        await db.execute_query(f"""
            CREATE TABLE IF NOT EXISTS `{self.migration_table}` (
                `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
                `version` VARCHAR(255) NOT NULL UNIQUE,
                `applied_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                INDEX `idx_version` (`version`)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        """)
        
        logger.info("迁移记录表初始化完成")
    
    async def get_applied_migrations(self) -> List[str]:
        """获取已应用的迁移"""
        db = Tortoise.get_connection("default")
        
        try:
            result = await db.execute_query(
                f"SELECT version FROM `{self.migration_table}` ORDER BY version"
            )
            return [row[0] for row in result[1]]
        except Exception:
            # 表不存在，返回空列表
            return []
    
    def get_available_migrations(self) -> List[str]:
        """获取可用的迁移文件"""
        migrations = []
        
        if not self.migrations_dir.exists():
            return migrations
        
        for file_path in self.migrations_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            
            # 提取版本号（文件名前缀）
            version = file_path.stem
            migrations.append(version)
        
        return sorted(migrations)
    
    def load_migration_module(self, version: str):
        """加载迁移模块"""
        migration_file = self.migrations_dir / f"{version}.py"
        
        if not migration_file.exists():
            raise FileNotFoundError(f"迁移文件不存在: {migration_file}")
        
        spec = importlib.util.spec_from_file_location(version, migration_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
    
    async def apply_migration(self, version: str) -> bool:
        """应用单个迁移"""
        try:
            logger.info(f"应用迁移: {version}")
            
            # 加载迁移模块
            module = self.load_migration_module(version)
            
            if not hasattr(module, 'upgrade'):
                raise AttributeError(f"迁移 {version} 缺少 upgrade 函数")
            
            # 执行迁移
            db = Tortoise.get_connection("default")
            sql = await module.upgrade(db)
            
            if sql:
                # 分割SQL语句并执行
                statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                for statement in statements:
                    await db.execute_query(statement)
            
            # 记录迁移
            await db.execute_query(
                f"INSERT INTO `{self.migration_table}` (version) VALUES (?)",
                [version]
            )
            
            logger.info(f"迁移 {version} 应用成功")
            return True
            
        except Exception as e:
            logger.error(f"应用迁移 {version} 失败: {e}")
            raise
    
    async def rollback_migration(self, version: str) -> bool:
        """回滚单个迁移"""
        try:
            logger.info(f"回滚迁移: {version}")
            
            # 加载迁移模块
            module = self.load_migration_module(version)
            
            if not hasattr(module, 'downgrade'):
                raise AttributeError(f"迁移 {version} 缺少 downgrade 函数")
            
            # 执行回滚
            db = Tortoise.get_connection("default")
            sql = await module.downgrade(db)
            
            if sql:
                # 分割SQL语句并执行
                statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                for statement in statements:
                    await db.execute_query(statement)
            
            # 删除迁移记录
            await db.execute_query(
                f"DELETE FROM `{self.migration_table}` WHERE version = ?",
                [version]
            )
            
            logger.info(f"迁移 {version} 回滚成功")
            return True
            
        except Exception as e:
            logger.error(f"回滚迁移 {version} 失败: {e}")
            raise
    
    async def migrate(self, target_version: str = None) -> Dict[str, Any]:
        """执行迁移到指定版本"""
        await self.init_migration_table()
        
        applied_migrations = await self.get_applied_migrations()
        available_migrations = self.get_available_migrations()
        
        if target_version:
            if target_version not in available_migrations:
                raise ValueError(f"目标版本不存在: {target_version}")
            
            # 迁移到指定版本
            target_index = available_migrations.index(target_version)
            pending_migrations = available_migrations[:target_index + 1]
        else:
            # 迁移到最新版本
            pending_migrations = available_migrations
        
        # 找出需要应用的迁移
        to_apply = [m for m in pending_migrations if m not in applied_migrations]
        
        results = {
            'applied_count': 0,
            'applied_migrations': [],
            'errors': []
        }
        
        for migration in to_apply:
            try:
                await self.apply_migration(migration)
                results['applied_count'] += 1
                results['applied_migrations'].append(migration)
            except Exception as e:
                results['errors'].append({
                    'migration': migration,
                    'error': str(e)
                })
                break  # 停止后续迁移
        
        logger.info(f"迁移完成: 应用了 {results['applied_count']} 个迁移")
        return results
    
    async def rollback(self, target_version: str = None, steps: int = 1) -> Dict[str, Any]:
        """回滚迁移"""
        applied_migrations = await self.get_applied_migrations()
        
        if not applied_migrations:
            logger.info("没有可回滚的迁移")
            return {'rollback_count': 0, 'rollback_migrations': [], 'errors': []}
        
        if target_version:
            if target_version not in applied_migrations:
                raise ValueError(f"目标版本未应用: {target_version}")
            
            # 回滚到指定版本之后的所有迁移
            target_index = applied_migrations.index(target_version)
            to_rollback = applied_migrations[target_index + 1:]
        else:
            # 回滚指定步数
            to_rollback = applied_migrations[-steps:]
        
        # 按逆序回滚
        to_rollback.reverse()
        
        results = {
            'rollback_count': 0,
            'rollback_migrations': [],
            'errors': []
        }
        
        for migration in to_rollback:
            try:
                await self.rollback_migration(migration)
                results['rollback_count'] += 1
                results['rollback_migrations'].append(migration)
            except Exception as e:
                results['errors'].append({
                    'migration': migration,
                    'error': str(e)
                })
                break  # 停止后续回滚
        
        logger.info(f"回滚完成: 回滚了 {results['rollback_count']} 个迁移")
        return results
    
    async def status(self) -> Dict[str, Any]:
        """获取迁移状态"""
        await self.init_migration_table()
        
        applied_migrations = await self.get_applied_migrations()
        available_migrations = self.get_available_migrations()
        
        pending_migrations = [m for m in available_migrations if m not in applied_migrations]
        
        return {
            'total_migrations': len(available_migrations),
            'applied_migrations': len(applied_migrations),
            'pending_migrations': len(pending_migrations),
            'applied_list': applied_migrations,
            'pending_list': pending_migrations,
            'latest_applied': applied_migrations[-1] if applied_migrations else None,
            'latest_available': available_migrations[-1] if available_migrations else None
        }
    
    async def create_migration(self, name: str, description: str = "") -> str:
        """创建新的迁移文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{name}"
        migration_file = self.migrations_dir / f"{version}.py"
        
        # 确保迁移目录存在
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成迁移文件模板
        template = f'''"""
{description or f"迁移: {name}"}
"""

from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- 在这里添加升级SQL语句
        -- 例如: CREATE TABLE ...
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        -- 在这里添加回滚SQL语句
        -- 例如: DROP TABLE ...
    """
'''
        
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(template)
        
        logger.info(f"创建迁移文件: {migration_file}")
        return version


# 全局迁移管理器实例
migration_manager = MigrationManager()
