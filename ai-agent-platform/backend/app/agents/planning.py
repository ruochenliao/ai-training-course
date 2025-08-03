"""
规划智能体

负责将复杂任务分解为可执行的步骤，并制定执行计划。
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .base import BaseAgent, AgentMessage, AgentConfig
from .llm_interface import llm_manager

logger = logging.getLogger(__name__)


class TaskStep:
    """任务步骤"""
    
    def __init__(self, id: str, name: str, description: str, 
                 agent_type: str, dependencies: List[str] = None,
                 estimated_time: int = 5, priority: int = 1):
        self.id = id
        self.name = name
        self.description = description
        self.agent_type = agent_type
        self.dependencies = dependencies or []
        self.estimated_time = estimated_time  # 预估时间（分钟）
        self.priority = priority  # 优先级 1-5
        self.status = "pending"  # pending, in_progress, completed, failed
        self.result = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None


class ExecutionPlan:
    """执行计划"""
    
    def __init__(self, id: str, title: str, description: str, steps: List[TaskStep]):
        self.id = id
        self.title = title
        self.description = description
        self.steps = steps
        self.status = "created"  # created, executing, completed, failed
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.total_estimated_time = sum(step.estimated_time for step in steps)
    
    def get_next_steps(self) -> List[TaskStep]:
        """获取下一步可执行的任务"""
        next_steps = []
        for step in self.steps:
            if step.status == "pending":
                # 检查依赖是否完成
                dependencies_completed = all(
                    self.get_step_by_id(dep_id).status == "completed" 
                    for dep_id in step.dependencies
                )
                if dependencies_completed:
                    next_steps.append(step)
        
        # 按优先级排序
        return sorted(next_steps, key=lambda x: x.priority, reverse=True)
    
    def get_step_by_id(self, step_id: str) -> Optional[TaskStep]:
        """根据ID获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def update_step_status(self, step_id: str, status: str, result: Any = None):
        """更新步骤状态"""
        step = self.get_step_by_id(step_id)
        if step:
            step.status = status
            step.result = result
            if status == "in_progress" and not step.started_at:
                step.started_at = datetime.now()
            elif status in ["completed", "failed"]:
                step.completed_at = datetime.now()
    
    def get_progress(self) -> Dict[str, Any]:
        """获取执行进度"""
        total_steps = len(self.steps)
        completed_steps = len([s for s in self.steps if s.status == "completed"])
        failed_steps = len([s for s in self.steps if s.status == "failed"])
        in_progress_steps = len([s for s in self.steps if s.status == "in_progress"])
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "in_progress_steps": in_progress_steps,
            "progress_percentage": (completed_steps / total_steps * 100) if total_steps > 0 else 0,
            "estimated_remaining_time": sum(
                step.estimated_time for step in self.steps 
                if step.status in ["pending", "in_progress"]
            )
        }


class PlanningAgent(BaseAgent):
    """规划智能体"""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="PlanningAgent",
                description="负责将复杂任务分解为可执行的步骤并制定执行计划",
                model="gpt-4o",
                temperature=0.3,
                system_prompt=self._get_system_prompt()
            )
        super().__init__(config)
        
        # 存储执行计划
        self.execution_plans: Dict[str, ExecutionPlan] = {}
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的任务规划助手，负责将复杂的用户请求分解为可执行的步骤。

可用的智能体类型：
- customer_service: 处理客户服务相关任务
- text2sql: 处理数据查询和分析任务
- knowledge_qa: 处理知识检索和问答任务
- content_creation: 处理内容创作任务

请将用户的复杂请求分解为具体的执行步骤，返回以下JSON格式：
{
    "plan_title": "计划标题",
    "plan_description": "计划描述",
    "steps": [
        {
            "id": "step_1",
            "name": "步骤名称",
            "description": "详细描述",
            "agent_type": "负责的智能体类型",
            "dependencies": ["依赖的步骤ID"],
            "estimated_time": 5,
            "priority": 3,
            "parameters": {
                "key": "value"
            }
        }
    ],
    "total_estimated_time": 15,
    "complexity": "simple|medium|complex"
}

规划原则：
1. 步骤要具体可执行
2. 合理设置依赖关系
3. 估算执行时间（分钟）
4. 设置优先级（1-5，5最高）
5. 考虑并行执行的可能性
6. 为每个步骤选择最合适的智能体"""
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理规划请求"""
        try:
            # 分析并创建执行计划
            plan = await self._create_execution_plan(message.content)
            
            # 存储计划
            self.execution_plans[plan.id] = plan
            
            # 构建响应
            response_content = json.dumps({
                "plan_id": plan.id,
                "plan_title": plan.title,
                "plan_description": plan.description,
                "total_steps": len(plan.steps),
                "total_estimated_time": plan.total_estimated_time,
                "next_steps": [
                    {
                        "id": step.id,
                        "name": step.name,
                        "agent_type": step.agent_type,
                        "priority": step.priority
                    }
                    for step in plan.get_next_steps()
                ]
            }, ensure_ascii=False, indent=2)
            
            response = AgentMessage(
                id=f"planning_response_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=response_content,
                message_type="execution_plan",
                metadata={
                    "plan_id": plan.id,
                    "original_message_id": message.id
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"规划处理失败: {e}")
            error_response = AgentMessage(
                id=f"planning_error_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=f"任务规划失败: {str(e)}",
                message_type="error"
            )
            return error_response
    
    async def _create_execution_plan(self, user_request: str) -> ExecutionPlan:
        """创建执行计划"""
        # 构建规划提示
        prompt = f"""
用户请求：{user_request}

请为这个请求创建详细的执行计划。
"""
        
        # 调用LLM进行规划
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=2000
        )
        
        try:
            # 解析JSON响应
            plan_data = json.loads(response.content)
            
            # 创建任务步骤
            steps = []
            for step_data in plan_data.get("steps", []):
                step = TaskStep(
                    id=step_data["id"],
                    name=step_data["name"],
                    description=step_data["description"],
                    agent_type=step_data["agent_type"],
                    dependencies=step_data.get("dependencies", []),
                    estimated_time=step_data.get("estimated_time", 5),
                    priority=step_data.get("priority", 1)
                )
                steps.append(step)
            
            # 创建执行计划
            plan_id = f"plan_{datetime.now().timestamp()}"
            plan = ExecutionPlan(
                id=plan_id,
                title=plan_data.get("plan_title", "执行计划"),
                description=plan_data.get("plan_description", ""),
                steps=steps
            )
            
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            # 创建简单的默认计划
            step = TaskStep(
                id="step_1",
                name="处理用户请求",
                description=user_request,
                agent_type="customer_service"
            )
            
            plan_id = f"plan_{datetime.now().timestamp()}"
            return ExecutionPlan(
                id=plan_id,
                title="简单执行计划",
                description="无法解析复杂计划，使用简单处理",
                steps=[step]
            )
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成响应"""
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.content
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """获取执行计划"""
        return self.execution_plans.get(plan_id)
    
    def get_all_plans(self) -> List[ExecutionPlan]:
        """获取所有执行计划"""
        return list(self.execution_plans.values())
    
    def update_step_status(self, plan_id: str, step_id: str, status: str, result: Any = None):
        """更新步骤状态"""
        plan = self.get_plan(plan_id)
        if plan:
            plan.update_step_status(step_id, status, result)
            
            # 检查计划是否完成
            if status == "completed":
                self._check_plan_completion(plan)
    
    def _check_plan_completion(self, plan: ExecutionPlan):
        """检查计划是否完成"""
        all_completed = all(step.status == "completed" for step in plan.steps)
        any_failed = any(step.status == "failed" for step in plan.steps)
        
        if all_completed:
            plan.status = "completed"
            plan.completed_at = datetime.now()
        elif any_failed:
            plan.status = "failed"
            plan.completed_at = datetime.now()
    
    def get_next_steps(self, plan_id: str) -> List[TaskStep]:
        """获取计划的下一步任务"""
        plan = self.get_plan(plan_id)
        if plan:
            return plan.get_next_steps()
        return []
    
    def get_plan_progress(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """获取计划进度"""
        plan = self.get_plan(plan_id)
        if plan:
            return plan.get_progress()
        return None
    
    async def optimize_plan(self, plan_id: str) -> bool:
        """优化执行计划"""
        plan = self.get_plan(plan_id)
        if not plan:
            return False
        
        try:
            # 分析当前计划状态
            progress = plan.get_progress()
            
            # 构建优化提示
            prompt = f"""
当前执行计划状态：
- 总步骤数：{progress['total_steps']}
- 已完成：{progress['completed_steps']}
- 失败：{progress['failed_steps']}
- 进行中：{progress['in_progress_steps']}
- 剩余预估时间：{progress['estimated_remaining_time']}分钟

请分析是否需要优化计划，如果需要，请提供优化建议。
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.5,
                max_tokens=1000
            )
            
            # 这里可以根据LLM的建议来实际优化计划
            logger.info(f"计划优化建议: {response.content}")
            return True
            
        except Exception as e:
            logger.error(f"计划优化失败: {e}")
            return False
