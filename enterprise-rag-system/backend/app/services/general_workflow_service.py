"""
通用工作流引擎服务
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Callable

# 移除 get_database 导入，使用 Tortoise ORM
from loguru import logger

from app.core.exceptions import WorkflowException


class WorkflowStatus(Enum):
    """工作流状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class TaskType(Enum):
    """任务类型"""
    DOCUMENT_PROCESS = "document_process"
    EMBEDDING_GENERATE = "embedding_generate"
    ENTITY_EXTRACT = "entity_extract"
    GRAPH_BUILD = "graph_build"
    INDEX_UPDATE = "index_update"
    NOTIFICATION = "notification"
    DATA_SYNC = "data_sync"
    BACKUP = "backup"
    CLEANUP = "cleanup"
    CUSTOM = "custom"


@dataclass
class WorkflowTask:
    """工作流任务"""
    id: str
    name: str
    type: TaskType
    config: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 3600  # 秒
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowInstance:
    """工作流实例"""
    id: str
    workflow_id: str
    status: WorkflowStatus
    context: Dict[str, Any]
    current_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class GeneralWorkflowService:
    """通用工作流引擎服务类"""
    
    def __init__(self):
        """初始化工作流服务"""
        # 使用 Tortoise ORM，不需要数据库连接池
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.instances: Dict[str, WorkflowInstance] = {}
        self.task_handlers: Dict[TaskType, Callable] = {}
        self.running_instances: Dict[str, asyncio.Task] = {}
        
        # 注册默认任务处理器
        self._register_default_handlers()
        
        # 预定义工作流模板
        self._create_default_workflows()
        
        logger.info("通用工作流引擎服务初始化完成")
    
    async def create_workflow(
        self,
        name: str,
        description: str,
        tasks: List[Dict[str, Any]],
        triggers: List[Dict[str, Any]] = None
    ) -> str:
        """创建工作流"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # 构建任务列表
            workflow_tasks = []
            for task_config in tasks:
                task = WorkflowTask(
                    id=task_config.get("id", str(uuid.uuid4())),
                    name=task_config["name"],
                    type=TaskType(task_config["type"]),
                    config=task_config.get("config", {}),
                    dependencies=task_config.get("dependencies", []),
                    max_retries=task_config.get("max_retries", 3),
                    timeout=task_config.get("timeout", 3600)
                )
                workflow_tasks.append(task)
            
            # 创建工作流定义
            workflow = WorkflowDefinition(
                id=workflow_id,
                name=name,
                description=description,
                tasks=workflow_tasks,
                triggers=triggers or []
            )
            
            # 验证工作流
            await self._validate_workflow(workflow)
            
            # 存储工作流
            self.workflows[workflow_id] = workflow
            await self._save_workflow_to_db(workflow)
            
            logger.info(f"创建工作流成功: {name} ({workflow_id})")
            return workflow_id
            
        except Exception as e:
            logger.error(f"创建工作流失败: {e}")
            raise WorkflowException(f"创建工作流失败: {e}")
    
    async def start_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any] = None
    ) -> str:
        """启动工作流实例"""
        try:
            if workflow_id not in self.workflows:
                raise WorkflowException(f"工作流 {workflow_id} 不存在")
            
            workflow = self.workflows[workflow_id]
            instance_id = str(uuid.uuid4())
            
            # 创建工作流实例
            instance = WorkflowInstance(
                id=instance_id,
                workflow_id=workflow_id,
                status=WorkflowStatus.ACTIVE,
                context=context or {}
            )
            
            self.instances[instance_id] = instance
            await self._save_instance_to_db(instance)
            
            # 启动工作流执行
            task = asyncio.create_task(self._execute_workflow(instance_id))
            self.running_instances[instance_id] = task
            
            logger.info(f"启动工作流实例: {workflow.name} ({instance_id})")
            return instance_id
            
        except Exception as e:
            logger.error(f"启动工作流失败: {e}")
            raise WorkflowException(f"启动工作流失败: {e}")
    
    async def get_workflow_status(self, instance_id: str) -> Dict[str, Any]:
        """获取工作流状态"""
        try:
            if instance_id not in self.instances:
                raise WorkflowException(f"工作流实例 {instance_id} 不存在")
            
            instance = self.instances[instance_id]
            workflow = self.workflows[instance.workflow_id]
            
            # 计算进度
            total_tasks = len(workflow.tasks)
            completed_tasks = len(instance.completed_tasks)
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # 获取任务状态
            task_statuses = {}
            for task in workflow.tasks:
                if task.id in instance.completed_tasks:
                    task_statuses[task.id] = TaskStatus.COMPLETED
                elif task.id in instance.failed_tasks:
                    task_statuses[task.id] = TaskStatus.FAILED
                elif task.id in instance.current_tasks:
                    task_statuses[task.id] = TaskStatus.RUNNING
                else:
                    task_statuses[task.id] = TaskStatus.PENDING
            
            return {
                "instance_id": instance_id,
                "workflow_id": instance.workflow_id,
                "workflow_name": workflow.name,
                "status": instance.status.value,
                "progress": progress,
                "started_at": instance.started_at.isoformat(),
                "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
                "current_tasks": instance.current_tasks,
                "completed_tasks": instance.completed_tasks,
                "failed_tasks": instance.failed_tasks,
                "task_statuses": {k: v.value for k, v in task_statuses.items()},
                "error": instance.error
            }
            
        except Exception as e:
            logger.error(f"获取工作流状态失败: {e}")
            raise WorkflowException(f"获取工作流状态失败: {e}")
    
    def _create_default_workflows(self):
        """创建默认工作流模板"""
        
        # 文档处理工作流
        document_workflow_tasks = [
            {
                "id": "upload_task",
                "name": "文档上传",
                "type": "document_process",
                "config": {"action": "upload"},
                "dependencies": []
            },
            {
                "id": "parse_task", 
                "name": "文档解析",
                "type": "document_process",
                "config": {"action": "parse"},
                "dependencies": ["upload_task"]
            },
            {
                "id": "embedding_task",
                "name": "生成向量",
                "type": "embedding_generate",
                "config": {},
                "dependencies": ["parse_task"]
            },
            {
                "id": "index_task",
                "name": "更新索引",
                "type": "index_update", 
                "config": {},
                "dependencies": ["embedding_task"]
            },
            {
                "id": "notify_task",
                "name": "完成通知",
                "type": "notification",
                "config": {"message": "文档处理完成"},
                "dependencies": ["index_task"]
            }
        ]
        
        # 知识图谱构建工作流
        graph_workflow_tasks = [
            {
                "id": "extract_entities",
                "name": "实体抽取",
                "type": "entity_extract",
                "config": {},
                "dependencies": []
            },
            {
                "id": "build_graph",
                "name": "构建图谱",
                "type": "graph_build",
                "config": {},
                "dependencies": ["extract_entities"]
            },
            {
                "id": "update_index",
                "name": "更新图谱索引",
                "type": "index_update",
                "config": {"type": "graph"},
                "dependencies": ["build_graph"]
            }
        ]
        
        # 系统维护工作流
        maintenance_workflow_tasks = [
            {
                "id": "backup_data",
                "name": "数据备份",
                "type": "backup",
                "config": {"type": "full"},
                "dependencies": []
            },
            {
                "id": "cleanup_temp",
                "name": "清理临时文件",
                "type": "cleanup",
                "config": {"path": "/tmp"},
                "dependencies": []
            },
            {
                "id": "sync_data",
                "name": "数据同步",
                "type": "data_sync",
                "config": {},
                "dependencies": ["backup_data"]
            }
        ]
        
        # 创建默认工作流（这里简化处理，实际应该调用create_workflow）
        self.default_workflows = {
            "document_processing": document_workflow_tasks,
            "graph_building": graph_workflow_tasks,
            "system_maintenance": maintenance_workflow_tasks
        }
    
    def _register_default_handlers(self):
        """注册默认任务处理器"""
        
        async def document_process_handler(task: WorkflowTask, instance: WorkflowInstance):
            """文档处理任务处理器"""
            action = task.config.get("action", "process")
            document_id = instance.context.get("document_id")
            
            logger.info(f"执行文档处理: {action}, 文档ID: {document_id}")
            
            # 模拟处理时间
            await asyncio.sleep(2)
            
            return {
                "status": "completed",
                "action": action,
                "document_id": document_id,
                "processed_at": datetime.now().isoformat()
            }
        
        async def embedding_generate_handler(task: WorkflowTask, instance: WorkflowInstance):
            """向量生成任务处理器"""
            logger.info("生成文档向量")
            
            # 模拟向量生成
            await asyncio.sleep(3)
            
            return {
                "status": "generated",
                "embedding_count": 150,
                "dimension": 768,
                "generated_at": datetime.now().isoformat()
            }
        
        async def entity_extract_handler(task: WorkflowTask, instance: WorkflowInstance):
            """实体抽取任务处理器"""
            logger.info("抽取文档实体")
            
            # 模拟实体抽取
            await asyncio.sleep(2)
            
            return {
                "status": "extracted",
                "entity_count": 25,
                "relation_count": 40,
                "extracted_at": datetime.now().isoformat()
            }
        
        async def notification_handler(task: WorkflowTask, instance: WorkflowInstance):
            """通知任务处理器"""
            message = task.config.get("message", "任务完成")
            recipient = task.config.get("recipient", "system")
            
            logger.info(f"发送通知: {message} -> {recipient}")
            
            # 模拟发送通知
            await asyncio.sleep(0.5)
            
            return {
                "status": "sent",
                "message": message,
                "recipient": recipient,
                "sent_at": datetime.now().isoformat()
            }
        
        # 注册处理器
        self.task_handlers[TaskType.DOCUMENT_PROCESS] = document_process_handler
        self.task_handlers[TaskType.EMBEDDING_GENERATE] = embedding_generate_handler
        self.task_handlers[TaskType.ENTITY_EXTRACT] = entity_extract_handler
        self.task_handlers[TaskType.NOTIFICATION] = notification_handler
    
    async def _execute_workflow(self, instance_id: str):
        """执行工作流"""
        try:
            instance = self.instances[instance_id]
            workflow = self.workflows[instance.workflow_id]
            
            logger.info(f"开始执行工作流实例: {instance_id}")
            
            while instance.status == WorkflowStatus.ACTIVE:
                # 获取可执行的任务
                ready_tasks = await self._get_ready_tasks(workflow, instance)
                
                if not ready_tasks:
                    # 检查是否所有任务都完成
                    if len(instance.completed_tasks) == len(workflow.tasks):
                        instance.status = WorkflowStatus.COMPLETED
                        instance.completed_at = datetime.now()
                        logger.info(f"工作流实例 {instance_id} 执行完成")
                        break
                    else:
                        # 等待其他任务完成
                        await asyncio.sleep(1)
                        continue
                
                # 并行执行就绪的任务
                tasks = []
                for task in ready_tasks:
                    instance.current_tasks.append(task.id)
                    task_coroutine = self._execute_task(task, instance)
                    tasks.append(task_coroutine)
                
                # 等待任务完成
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理任务结果
                for i, result in enumerate(results):
                    task = ready_tasks[i]
                    instance.current_tasks.remove(task.id)
                    
                    if isinstance(result, Exception):
                        instance.failed_tasks.append(task.id)
                        task.status = TaskStatus.FAILED
                        task.error = str(result)
                        
                        logger.error(f"任务 {task.name} 失败: {result}")
                        
                        # 检查是否为关键任务
                        if task.config.get("critical", False):
                            instance.status = WorkflowStatus.FAILED
                            instance.error = f"关键任务 {task.name} 失败: {result}"
                            break
                    else:
                        instance.completed_tasks.append(task.id)
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        task.completed_at = datetime.now()
                        logger.info(f"任务 {task.name} 完成")
                
                await self._save_instance_to_db(instance)
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            instance.status = WorkflowStatus.FAILED
            instance.error = str(e)
            instance.completed_at = datetime.now()
            await self._save_instance_to_db(instance)
        finally:
            # 清理运行中的实例
            if instance_id in self.running_instances:
                del self.running_instances[instance_id]
    
    async def _get_ready_tasks(
        self,
        workflow: WorkflowDefinition,
        instance: WorkflowInstance
    ) -> List[WorkflowTask]:
        """获取可执行的任务"""
        ready_tasks = []
        
        for task in workflow.tasks:
            # 跳过已完成、失败或正在运行的任务
            if (task.id in instance.completed_tasks or 
                task.id in instance.failed_tasks or 
                task.id in instance.current_tasks):
                continue
            
            # 检查依赖是否满足
            dependencies_met = all(
                dep_id in instance.completed_tasks 
                for dep_id in task.dependencies
            )
            
            if dependencies_met:
                ready_tasks.append(task)
        
        return ready_tasks
    
    async def _execute_task(
        self,
        task: WorkflowTask,
        instance: WorkflowInstance
    ) -> Dict[str, Any]:
        """执行单个任务"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            logger.info(f"开始执行任务: {task.name} ({task.type.value})")
            
            # 获取任务处理器
            handler = self.task_handlers.get(task.type)
            if not handler:
                raise WorkflowException(f"未找到任务类型 {task.type.value} 的处理器")
            
            # 执行任务
            result = await asyncio.wait_for(
                handler(task, instance),
                timeout=task.timeout
            )
            
            return result
            
        except asyncio.TimeoutError:
            raise WorkflowException(f"任务 {task.name} 执行超时")
        except Exception as e:
            raise WorkflowException(f"任务 {task.name} 执行失败: {e}")
    
    async def _validate_workflow(self, workflow: WorkflowDefinition):
        """验证工作流定义"""
        # 检查任务ID唯一性
        task_ids = [task.id for task in workflow.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise WorkflowException("任务ID必须唯一")
        
        # 检查依赖关系
        for task in workflow.tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    raise WorkflowException(f"任务 {task.name} 的依赖 {dep_id} 不存在")
    
    async def _save_workflow_to_db(self, workflow: WorkflowDefinition):
        """保存工作流到数据库"""
        # 这里应该实现数据库保存逻辑
        pass
    
    async def _save_instance_to_db(self, instance: WorkflowInstance):
        """保存工作流实例到数据库"""
        # 这里应该实现数据库保存逻辑
        pass


# 全局通用工作流服务实例
general_workflow_service = GeneralWorkflowService()
