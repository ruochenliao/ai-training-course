"""
工作流管理器

负责协调多个智能体的协作，管理任务执行流程。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from .base import BaseAgent, AgentMessage, agent_registry
from .router import RouterAgent
from .planning import PlanningAgent, ExecutionPlan, TaskStep

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """工作流状态"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowEvent:
    """工作流事件"""
    
    def __init__(self, event_type: str, data: Dict[str, Any], timestamp: datetime = None):
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now()


class WorkflowContext:
    """工作流上下文"""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.shared_data: Dict[str, Any] = {}
        self.events: List[WorkflowEvent] = []
    
    def set_variable(self, key: str, value: Any):
        """设置变量"""
        self.variables[key] = value
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(key, default)
    
    def set_shared_data(self, key: str, value: Any):
        """设置共享数据"""
        self.shared_data[key] = value
    
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """获取共享数据"""
        return self.shared_data.get(key, default)
    
    def add_event(self, event_type: str, data: Dict[str, Any]):
        """添加事件"""
        event = WorkflowEvent(event_type, data)
        self.events.append(event)


class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        self.workflows: Dict[str, 'Workflow'] = {}
        self.router_agent = None
        self.planning_agent = None
        
        # 事件回调
        self.event_callbacks: Dict[str, List[Callable]] = {}
    
    async def initialize(self):
        """初始化工作流管理器"""
        # 创建并注册路由智能体
        self.router_agent = RouterAgent()
        agent_registry.register(self.router_agent)
        await self.router_agent.start()
        
        # 创建并注册规划智能体
        self.planning_agent = PlanningAgent()
        agent_registry.register(self.planning_agent)
        await self.planning_agent.start()
        
        logger.info("工作流管理器初始化完成")
    
    async def create_workflow(self, workflow_id: str, user_request: str, 
                            user_id: str = None) -> 'Workflow':
        """创建新的工作流"""
        workflow = Workflow(workflow_id, user_request, user_id, self)
        self.workflows[workflow_id] = workflow
        
        logger.info(f"创建工作流: {workflow_id}")
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional['Workflow']:
        """获取工作流"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List['Workflow']:
        """列出所有工作流"""
        return list(self.workflows.values())
    
    def remove_workflow(self, workflow_id: str):
        """移除工作流"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            logger.info(f"移除工作流: {workflow_id}")
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """注册事件回调"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(f"事件回调执行失败: {e}")


class Workflow:
    """工作流"""
    
    def __init__(self, workflow_id: str, user_request: str, user_id: str, manager: WorkflowManager):
        self.id = workflow_id
        self.user_request = user_request
        self.user_id = user_id
        self.manager = manager
        self.status = WorkflowStatus.CREATED
        self.context = WorkflowContext()
        self.execution_plan: Optional[ExecutionPlan] = None
        self.current_step: Optional[TaskStep] = None
        self.results: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.error_message = None
    
    async def start(self) -> bool:
        """启动工作流"""
        try:
            self.status = WorkflowStatus.RUNNING
            self.started_at = datetime.now()
            
            # 添加启动事件
            self.context.add_event("workflow_started", {
                "workflow_id": self.id,
                "user_request": self.user_request
            })
            
            # 第一步：路由分析
            await self._route_request()
            
            # 第二步：任务规划
            await self._plan_execution()
            
            # 第三步：执行任务
            await self._execute_plan()
            
            return True
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            self.status = WorkflowStatus.FAILED
            self.error_message = str(e)
            self.completed_at = datetime.now()
            return False
    
    async def _route_request(self):
        """路由分析"""
        logger.info(f"工作流 {self.id}: 开始路由分析")
        
        # 创建路由请求消息
        message = AgentMessage(
            id=f"route_request_{self.id}",
            sender="workflow",
            receiver="RouterAgent",
            content=self.user_request
        )
        
        # 发送给路由智能体
        response = await self.manager.router_agent.receive_message(message)
        
        # 解析路由决策
        if response.message_type == "routing_decision":
            routing_decision = response.metadata.get("routing_decision", {})
            self.context.set_variable("routing_decision", routing_decision)
            
            logger.info(f"路由决策: {routing_decision.get('agent_type')}")
        else:
            raise Exception("路由分析失败")
    
    async def _plan_execution(self):
        """任务规划"""
        logger.info(f"工作流 {self.id}: 开始任务规划")
        
        # 创建规划请求消息
        message = AgentMessage(
            id=f"plan_request_{self.id}",
            sender="workflow",
            receiver="PlanningAgent",
            content=self.user_request
        )
        
        # 发送给规划智能体
        response = await self.manager.planning_agent.receive_message(message)
        
        # 获取执行计划
        if response.message_type == "execution_plan":
            plan_id = response.metadata.get("plan_id")
            self.execution_plan = self.manager.planning_agent.get_plan(plan_id)
            
            if self.execution_plan:
                logger.info(f"创建执行计划: {self.execution_plan.title}")
                self.context.set_variable("execution_plan_id", plan_id)
            else:
                raise Exception("无法获取执行计划")
        else:
            raise Exception("任务规划失败")
    
    async def _execute_plan(self):
        """执行计划"""
        if not self.execution_plan:
            raise Exception("没有可执行的计划")
        
        logger.info(f"工作流 {self.id}: 开始执行计划")
        
        while True:
            # 获取下一步任务
            next_steps = self.execution_plan.get_next_steps()
            
            if not next_steps:
                # 检查是否所有任务都完成
                all_completed = all(step.status == "completed" for step in self.execution_plan.steps)
                if all_completed:
                    self.status = WorkflowStatus.COMPLETED
                    self.completed_at = datetime.now()
                    logger.info(f"工作流 {self.id}: 执行完成")
                    break
                else:
                    # 有失败的任务
                    self.status = WorkflowStatus.FAILED
                    self.error_message = "存在失败的任务步骤"
                    self.completed_at = datetime.now()
                    break
            
            # 并行执行可执行的步骤
            tasks = []
            for step in next_steps:
                task = asyncio.create_task(self._execute_step(step))
                tasks.append(task)
            
            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_step(self, step: TaskStep):
        """执行单个步骤"""
        try:
            logger.info(f"执行步骤: {step.name}")
            
            # 更新步骤状态
            self.execution_plan.update_step_status(step.id, "in_progress")
            self.current_step = step
            
            # 根据智能体类型执行步骤
            result = await self._delegate_to_agent(step)
            
            # 更新步骤状态
            self.execution_plan.update_step_status(step.id, "completed", result)
            self.results[step.id] = result
            
            logger.info(f"步骤完成: {step.name}")
            
        except Exception as e:
            logger.error(f"步骤执行失败: {step.name}, 错误: {e}")
            self.execution_plan.update_step_status(step.id, "failed", str(e))
    
    async def _delegate_to_agent(self, step: TaskStep) -> Any:
        """委托给特定智能体执行"""
        # 获取对应的智能体
        agent = agent_registry.get(step.agent_type)
        
        if not agent:
            raise Exception(f"未找到智能体: {step.agent_type}")
        
        # 创建执行消息
        message = AgentMessage(
            id=f"step_request_{step.id}",
            sender="workflow",
            receiver=step.agent_type,
            content=step.description,
            metadata={
                "step_id": step.id,
                "workflow_id": self.id,
                "context": self.context.shared_data
            }
        )
        
        # 发送给智能体执行
        response = await agent.receive_message(message)
        
        return response.content
    
    def pause(self):
        """暂停工作流"""
        if self.status == WorkflowStatus.RUNNING:
            self.status = WorkflowStatus.PAUSED
            logger.info(f"工作流 {self.id}: 已暂停")
    
    def resume(self):
        """恢复工作流"""
        if self.status == WorkflowStatus.PAUSED:
            self.status = WorkflowStatus.RUNNING
            logger.info(f"工作流 {self.id}: 已恢复")
    
    def cancel(self):
        """取消工作流"""
        self.status = WorkflowStatus.CANCELLED
        self.completed_at = datetime.now()
        logger.info(f"工作流 {self.id}: 已取消")
    
    def get_progress(self) -> Dict[str, Any]:
        """获取工作流进度"""
        if self.execution_plan:
            plan_progress = self.execution_plan.get_progress()
        else:
            plan_progress = {}
        
        return {
            "workflow_id": self.id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "plan_progress": plan_progress,
            "current_step": self.current_step.name if self.current_step else None
        }


# 全局工作流管理器
workflow_manager = WorkflowManager()
