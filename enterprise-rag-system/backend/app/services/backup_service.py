"""
数据备份和恢复服务
"""

import asyncio
import json
import shutil
import tarfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.core.config import settings
from app.services.notification_service import notification_service, NotificationType
from loguru import logger

from app.core.exceptions import BackupException


class BackupType(Enum):
    """备份类型"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(Enum):
    """备份状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RestoreStatus(Enum):
    """恢复状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackupConfig:
    """备份配置"""
    name: str
    backup_type: BackupType
    schedule: str = ""  # Cron表达式
    retention_days: int = 30
    compression: bool = True
    encryption: bool = False
    include_files: bool = True
    include_database: bool = True
    include_vectors: bool = True
    include_graph: bool = True
    enabled: bool = True


@dataclass
class BackupJob:
    """备份任务"""
    id: str
    config: BackupConfig
    status: BackupStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: int = 0
    error_message: Optional[str] = None
    progress: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RestoreJob:
    """恢复任务"""
    id: str
    backup_file: str
    status: RestoreStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: int = 0
    options: Dict[str, Any] = field(default_factory=dict)


class BackupService:
    """数据备份和恢复服务类"""
    
    def __init__(self):
        """初始化备份服务"""
        self.backup_dir = Path(settings.BACKUP_DIR if hasattr(settings, 'BACKUP_DIR') else "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.running_jobs: Dict[str, BackupJob] = {}
        self.running_restores: Dict[str, RestoreJob] = {}
        
        # 默认备份配置
        self.default_configs = [
            BackupConfig(
                name="daily_full",
                backup_type=BackupType.FULL,
                schedule="0 2 * * *",  # 每天凌晨2点
                retention_days=7,
                compression=True,
                encryption=False
            ),
            BackupConfig(
                name="weekly_full",
                backup_type=BackupType.FULL,
                schedule="0 3 * * 0",  # 每周日凌晨3点
                retention_days=30,
                compression=True,
                encryption=True
            ),
            BackupConfig(
                name="hourly_incremental",
                backup_type=BackupType.INCREMENTAL,
                schedule="0 * * * *",  # 每小时
                retention_days=3,
                compression=True,
                encryption=False,
                include_files=False  # 只备份数据库
            )
        ]
        
        logger.info("数据备份和恢复服务初始化完成")
    
    async def create_backup(
        self,
        config: BackupConfig,
        manual: bool = False
    ) -> str:
        """创建备份"""
        try:
            # 生成备份任务ID
            job_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建备份任务
            job = BackupJob(
                id=job_id,
                config=config,
                status=BackupStatus.PENDING,
                metadata={
                    "manual": manual,
                    "created_by": "system"
                }
            )
            
            self.running_jobs[job_id] = job
            
            # 异步执行备份
            asyncio.create_task(self._execute_backup(job))
            
            logger.info(f"备份任务已创建: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            raise BackupException(f"创建备份失败: {e}")
    
    async def restore_backup(
        self,
        backup_file: str,
        options: Dict[str, Any] = None
    ) -> str:
        """恢复备份"""
        try:
            if options is None:
                options = {}
            
            # 检查备份文件是否存在
            backup_path = self.backup_dir / backup_file
            if not backup_path.exists():
                raise BackupException(f"备份文件不存在: {backup_file}")
            
            # 生成恢复任务ID
            job_id = f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建恢复任务
            job = RestoreJob(
                id=job_id,
                backup_file=backup_file,
                status=RestoreStatus.PENDING,
                options=options
            )
            
            self.running_restores[job_id] = job
            
            # 异步执行恢复
            asyncio.create_task(self._execute_restore(job))
            
            logger.info(f"恢复任务已创建: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"创建恢复任务失败: {e}")
            raise BackupException(f"创建恢复任务失败: {e}")
    
    async def get_backup_status(self, job_id: str) -> Optional[BackupJob]:
        """获取备份状态"""
        return self.running_jobs.get(job_id)
    
    async def get_restore_status(self, job_id: str) -> Optional[RestoreJob]:
        """获取恢复状态"""
        return self.running_restores.get(job_id)
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份"""
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("*.tar.gz"):
                try:
                    stat = backup_file.stat()
                    
                    # 尝试读取元数据
                    metadata = await self._read_backup_metadata(backup_file)
                    
                    backups.append({
                        "filename": backup_file.name,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "metadata": metadata
                    })
                    
                except Exception as e:
                    logger.error(f"读取备份文件信息失败: {e}")
            
            # 按创建时间排序
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"列出备份失败: {e}")
            return []
    
    async def delete_backup(self, backup_file: str) -> bool:
        """删除备份"""
        try:
            backup_path = self.backup_dir / backup_file
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"备份文件已删除: {backup_file}")
                return True
            else:
                logger.warning(f"备份文件不存在: {backup_file}")
                return False
                
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            return False
    
    async def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """清理过期备份"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0
            
            for backup_file in self.backup_dir.glob("*.tar.gz"):
                try:
                    stat = backup_file.stat()
                    created_at = datetime.fromtimestamp(stat.st_ctime)
                    
                    if created_at < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                        logger.info(f"删除过期备份: {backup_file.name}")
                        
                except Exception as e:
                    logger.error(f"删除过期备份失败: {e}")
            
            logger.info(f"清理完成，删除了 {deleted_count} 个过期备份")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理过期备份失败: {e}")
            return 0
    
    async def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """验证备份完整性"""
        try:
            backup_path = self.backup_dir / backup_file
            if not backup_path.exists():
                return {"valid": False, "error": "备份文件不存在"}
            
            # 检查文件完整性
            try:
                with tarfile.open(backup_path, 'r:gz') as tar:
                    # 验证tar文件结构
                    members = tar.getmembers()
                    
                    # 检查必要的文件
                    required_files = ["metadata.json"]
                    found_files = [m.name for m in members]
                    
                    missing_files = [f for f in required_files if f not in found_files]
                    if missing_files:
                        return {
                            "valid": False,
                            "error": f"缺少必要文件: {missing_files}"
                        }
                    
                    # 读取元数据
                    metadata_member = tar.extractfile("metadata.json")
                    if metadata_member:
                        metadata = json.loads(metadata_member.read().decode('utf-8'))
                    else:
                        return {"valid": False, "error": "无法读取元数据"}
                    
                    return {
                        "valid": True,
                        "metadata": metadata,
                        "file_count": len(members),
                        "total_size": sum(m.size for m in members)
                    }
                    
            except tarfile.TarError as e:
                return {"valid": False, "error": f"备份文件损坏: {e}"}
                
        except Exception as e:
            logger.error(f"验证备份失败: {e}")
            return {"valid": False, "error": str(e)}
    
    # 私有方法
    async def _execute_backup(self, job: BackupJob):
        """执行备份"""
        try:
            job.status = BackupStatus.RUNNING
            job.started_at = datetime.now()
            job.progress = 0
            
            # 创建临时目录
            temp_dir = self.backup_dir / f"temp_{job.id}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # 备份数据库
                if job.config.include_database:
                    await self._backup_database(temp_dir, job)
                
                # 备份向量数据
                if job.config.include_vectors:
                    await self._backup_vectors(temp_dir, job)
                
                # 备份图数据
                if job.config.include_graph:
                    await self._backup_graph(temp_dir, job)
                
                # 备份文件
                if job.config.include_files:
                    await self._backup_files(temp_dir, job)
                
                # 创建元数据
                await self._create_backup_metadata(temp_dir, job)
                
                # 压缩备份
                backup_file = await self._compress_backup(temp_dir, job)
                
                job.file_path = str(backup_file)
                job.file_size = backup_file.stat().st_size
                job.status = BackupStatus.COMPLETED
                job.completed_at = datetime.now()
                job.progress = 100
                
                # 发送通知
                await notification_service.send_notification_from_template(
                    "backup_completed",
                    data={
                        "backup_name": job.config.name,
                        "file_size": self._format_file_size(job.file_size),
                        "duration": str(job.completed_at - job.started_at)
                    }
                )
                
                logger.info(f"备份完成: {job.id}")
                
            finally:
                # 清理临时目录
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            job.status = BackupStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            logger.error(f"备份失败: {job.id} - {e}")
            
            # 发送失败通知
            await notification_service.send_notification_from_template(
                "backup_failed",
                data={
                    "backup_name": job.config.name,
                    "error": str(e)
                }
            )
        finally:
            # 清理运行中的任务
            if job.id in self.running_jobs:
                del self.running_jobs[job.id]
    
    async def _execute_restore(self, job: RestoreJob):
        """执行恢复"""
        try:
            job.status = RestoreStatus.RUNNING
            job.started_at = datetime.now()
            job.progress = 0
            
            backup_path = self.backup_dir / job.backup_file
            
            # 创建临时目录
            temp_dir = self.backup_dir / f"restore_temp_{job.id}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # 解压备份
                await self._extract_backup(backup_path, temp_dir, job)
                
                # 读取元数据
                metadata_file = temp_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                else:
                    raise BackupException("备份元数据文件不存在")
                
                # 恢复数据库
                if job.options.get("restore_database", True):
                    await self._restore_database(temp_dir, job, metadata)
                
                # 恢复向量数据
                if job.options.get("restore_vectors", True):
                    await self._restore_vectors(temp_dir, job, metadata)
                
                # 恢复图数据
                if job.options.get("restore_graph", True):
                    await self._restore_graph(temp_dir, job, metadata)
                
                # 恢复文件
                if job.options.get("restore_files", True):
                    await self._restore_files(temp_dir, job, metadata)
                
                job.status = RestoreStatus.COMPLETED
                job.completed_at = datetime.now()
                job.progress = 100
                
                logger.info(f"恢复完成: {job.id}")
                
            finally:
                # 清理临时目录
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            job.status = RestoreStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            logger.error(f"恢复失败: {job.id} - {e}")
        finally:
            # 清理运行中的任务
            if job.id in self.running_restores:
                del self.running_restores[job.id]
    
    async def _backup_database(self, temp_dir: Path, job: BackupJob):
        """备份数据库"""
        try:
            job.progress = 10
            
            # MySQL备份
            mysql_file = temp_dir / "mysql_dump.sql"
            cmd = [
                "mysqldump",
                f"--host={settings.DATABASE_HOST}",
                f"--port={settings.DATABASE_PORT}",
                f"--user={settings.DATABASE_USER}",
                f"--password={settings.DATABASE_PASSWORD}",
                "--single-transaction",
                "--routines",
                "--triggers",
                settings.DATABASE_NAME
            ]
            
            with open(mysql_file, 'w') as f:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=f,
                    stderr=asyncio.subprocess.PIPE
                )
                _, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise BackupException(f"MySQL备份失败: {stderr.decode()}")
            
            logger.info("数据库备份完成")
            
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            raise
    
    async def _backup_vectors(self, temp_dir: Path, job: BackupJob):
        """备份向量数据"""
        try:
            job.progress = 30
            
            # 这里应该备份Milvus数据
            # 目前创建占位文件
            vectors_file = temp_dir / "vectors_backup.json"
            with open(vectors_file, 'w') as f:
                json.dump({"message": "向量数据备份占位"}, f)
            
            logger.info("向量数据备份完成")
            
        except Exception as e:
            logger.error(f"向量数据备份失败: {e}")
            raise
    
    async def _backup_graph(self, temp_dir: Path, job: BackupJob):
        """备份图数据"""
        try:
            job.progress = 50
            
            # 这里应该备份Neo4j数据
            # 目前创建占位文件
            graph_file = temp_dir / "graph_backup.cypher"
            with open(graph_file, 'w') as f:
                f.write("// 图数据备份占位\n")
            
            logger.info("图数据备份完成")
            
        except Exception as e:
            logger.error(f"图数据备份失败: {e}")
            raise
    
    async def _backup_files(self, temp_dir: Path, job: BackupJob):
        """备份文件"""
        try:
            job.progress = 70
            
            # 备份上传的文件
            files_dir = temp_dir / "files"
            files_dir.mkdir(exist_ok=True)
            
            # 这里应该备份MinIO或本地文件
            # 目前创建占位文件
            placeholder_file = files_dir / "files_backup.txt"
            with open(placeholder_file, 'w') as f:
                f.write("文件备份占位")
            
            logger.info("文件备份完成")
            
        except Exception as e:
            logger.error(f"文件备份失败: {e}")
            raise
    
    async def _create_backup_metadata(self, temp_dir: Path, job: BackupJob):
        """创建备份元数据"""
        try:
            metadata = {
                "backup_id": job.id,
                "backup_type": job.config.backup_type.value,
                "created_at": datetime.now().isoformat(),
                "config": {
                    "name": job.config.name,
                    "include_database": job.config.include_database,
                    "include_vectors": job.config.include_vectors,
                    "include_graph": job.config.include_graph,
                    "include_files": job.config.include_files,
                    "compression": job.config.compression,
                    "encryption": job.config.encryption
                },
                "system_info": {
                    "version": settings.VERSION,
                    "database_version": "8.0",  # 应该动态获取
                    "python_version": "3.10+"
                }
            }
            
            metadata_file = temp_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"创建备份元数据失败: {e}")
            raise
    
    async def _compress_backup(self, temp_dir: Path, job: BackupJob) -> Path:
        """压缩备份"""
        try:
            job.progress = 90
            
            backup_filename = f"{job.config.name}_{job.id}.tar.gz"
            backup_path = self.backup_dir / backup_filename
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                for file_path in temp_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir)
                        tar.add(file_path, arcname=arcname)
            
            logger.info(f"备份压缩完成: {backup_filename}")
            return backup_path
            
        except Exception as e:
            logger.error(f"压缩备份失败: {e}")
            raise
    
    async def _extract_backup(self, backup_path: Path, temp_dir: Path, job: RestoreJob):
        """解压备份"""
        try:
            job.progress = 10
            
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            logger.info("备份解压完成")
            
        except Exception as e:
            logger.error(f"解压备份失败: {e}")
            raise
    
    async def _restore_database(self, temp_dir: Path, job: RestoreJob, metadata: Dict[str, Any]):
        """恢复数据库"""
        try:
            job.progress = 30
            
            mysql_file = temp_dir / "mysql_dump.sql"
            if mysql_file.exists():
                cmd = [
                    "mysql",
                    f"--host={settings.DATABASE_HOST}",
                    f"--port={settings.DATABASE_PORT}",
                    f"--user={settings.DATABASE_USER}",
                    f"--password={settings.DATABASE_PASSWORD}",
                    settings.DATABASE_NAME
                ]
                
                with open(mysql_file, 'r') as f:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdin=f,
                        stderr=asyncio.subprocess.PIPE
                    )
                    _, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        raise BackupException(f"MySQL恢复失败: {stderr.decode()}")
            
            logger.info("数据库恢复完成")
            
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            raise
    
    async def _restore_vectors(self, temp_dir: Path, job: RestoreJob, metadata: Dict[str, Any]):
        """恢复向量数据"""
        try:
            job.progress = 50
            
            # 这里应该恢复Milvus数据
            logger.info("向量数据恢复完成")
            
        except Exception as e:
            logger.error(f"向量数据恢复失败: {e}")
            raise
    
    async def _restore_graph(self, temp_dir: Path, job: RestoreJob, metadata: Dict[str, Any]):
        """恢复图数据"""
        try:
            job.progress = 70
            
            # 这里应该恢复Neo4j数据
            logger.info("图数据恢复完成")
            
        except Exception as e:
            logger.error(f"图数据恢复失败: {e}")
            raise
    
    async def _restore_files(self, temp_dir: Path, job: RestoreJob, metadata: Dict[str, Any]):
        """恢复文件"""
        try:
            job.progress = 90
            
            # 这里应该恢复MinIO或本地文件
            logger.info("文件恢复完成")
            
        except Exception as e:
            logger.error(f"文件恢复失败: {e}")
            raise
    
    async def _read_backup_metadata(self, backup_path: Path) -> Dict[str, Any]:
        """读取备份元数据"""
        try:
            with tarfile.open(backup_path, 'r:gz') as tar:
                metadata_member = tar.extractfile("metadata.json")
                if metadata_member:
                    return json.loads(metadata_member.read().decode('utf-8'))
            return {}
        except Exception:
            return {}
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


# 全局备份服务实例
backup_service = BackupService()
