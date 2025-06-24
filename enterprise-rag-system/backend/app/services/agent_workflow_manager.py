"""
智能体工作流管理器
基于AutoGen实现复杂的多智能体工作流编排
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

import autogen
from autogen import GroupChat, GroupChatManager
from loguru import logger

from app.core.config import settings
from app.core.exceptions import WorkflowException
from app.services.enhanced_autogen_service import (
    EnhancedAutoGenService, SearchMode, AgentTask, AgentResponse
)


class WorkflowType(Enum):
    """工作流类型"""
    SIMPLE_QA = "simple_qa"
    COMPLEX_RESEARCH = "complex_research"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    MULTI_STEP_REASONING = "multi_step_reasoning"
    FACT_CHECKING = "fact_checking"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str
    step_type: str
    description: str
    agent_roles: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str
    workflow_type: WorkflowType
    name: str
    description: str
    steps: List[WorkflowStep]
    global_timeout: int = 600
    parallel_execution: bool = False


@dataclass
class WorkflowExecution:
    """工作流执行实例"""
    execution_id: str
    workflow_def: WorkflowDefinition
    status: TaskStatus
    start_time: float
    end_time: Optional[float] = None
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    progress: float = 0.0


class AgentWorkflowManager:
    """智能体工作流管理器"""
    
    def __init__(self):
        self.autogen_service = EnhancedAutoGenService()
        self.workflow_definitions = {}
        self.active_executions = {}
        self.execution_history = []
        
        # 预定义工作流
        self._initialize_predefined_workflows()
        
        logger.info("智能体工作流管理器初始化完成")
    
    def _initialize_predefined_workflows(self):
        """初始化预定义工作流"""
        
        # 简单问答工作流
        simple_qa = WorkflowDefinition(
            workflow_id="simple_qa",
            workflow_type=WorkflowType.SIMPLE_QA,
            name="简单问答",
            description="单轮问答，适用于简单的事实性查询",
            steps=[
                WorkflowStep(
                    step_id="search",
                    step_type="search",
                    description="执行检索",
                    agent_roles=["semantic_searcher"],
                    parameters={"search_modes": ["semantic"], "top_k": 10}
                ),
                WorkflowStep(
                    step_id="generate",
                    step_type="generate",
                    description="生成答案",
                    agent_roles=["answer_generator"],
                    dependencies=["search"]
                )
            ],
            global_timeout=300
        )
        
        # 复杂研究工作流
        complex_research = WorkflowDefinition(
            workflow_id="complex_research",
            workflow_type=WorkflowType.COMPLEX_RESEARCH,
            name="复杂研究",
            description="多角度深入研究，适用于复杂的研究性查询",
            steps=[
                WorkflowStep(
                    step_id="semantic_search",
                    step_type="search",
                    description="语义检索",
                    agent_roles=["semantic_searcher"],
                    parameters={"search_modes": ["semantic"], "top_k": 15}
                ),
                WorkflowStep(
                    step_id="graph_search",
                    step_type="search",
                    description="图谱检索",
                    agent_roles=["graph_searcher"],
                    parameters={"search_modes": ["graph"], "top_k": 15}
                ),
                WorkflowStep(
                    step_id="hybrid_search",
                    step_type="search",
                    description="混合检索",
                    agent_roles=["hybrid_searcher"],
                    parameters={"search_modes": ["hybrid"], "top_k": 20},
                    dependencies=["semantic_search", "graph_search"]
                ),
                WorkflowStep(
                    step_id="quality_assessment",
                    step_type="assessment",
                    description="质量评估",
                    agent_roles=["quality_assessor"],
                    dependencies=["hybrid_search"]
                ),
                WorkflowStep(
                    step_id="generate_comprehensive",
                    step_type="generate",
                    description="生成综合答案",
                    agent_roles=["answer_generator"],
                    dependencies=["quality_assessment"]
                )
            ],
            global_timeout=600,
            parallel_execution=True
        )
        
        # 比较分析工作流
        comparative_analysis = WorkflowDefinition(
            workflow_id="comparative_analysis",
            workflow_type=WorkflowType.COMPARATIVE_ANALYSIS,
            name="比较分析",
            description="对比分析多个概念或实体",
            steps=[
                WorkflowStep(
                    step_id="entity_extraction",
                    step_type="extraction",
                    description="提取比较对象",
                    agent_roles=["graph_searcher"],
                    parameters={"extract_entities": True}
                ),
                WorkflowStep(
                    step_id="parallel_research",
                    step_type="search",
                    description="并行研究各对象",
                    agent_roles=["semantic_searcher", "graph_searcher"],
                    parameters={"search_modes": ["semantic", "graph"], "top_k": 10},
                    dependencies=["entity_extraction"]
                ),
                WorkflowStep(
                    step_id="comparison_analysis",
                    step_type="analysis",
                    description="执行比较分析",
                    agent_roles=["answer_generator"],
                    parameters={"analysis_type": "comparison"},
                    dependencies=["parallel_research"]
                )
            ],
            global_timeout=450
        )
        
        # 多步推理工作流
        multi_step_reasoning = WorkflowDefinition(
            workflow_id="multi_step_reasoning",
            workflow_type=WorkflowType.MULTI_STEP_REASONING,
            name="多步推理",
            description="需要多步逻辑推理的复杂问题",
            steps=[
                WorkflowStep(
                    step_id="problem_decomposition",
                    step_type="decomposition",
                    description="问题分解",
                    agent_roles=["coordinator"],
                    parameters={"decompose_query": True}
                ),
                WorkflowStep(
                    step_id="sub_problem_research",
                    step_type="search",
                    description="子问题研究",
                    agent_roles=["semantic_searcher", "graph_searcher"],
                    parameters={"search_modes": ["hybrid"], "top_k": 8},
                    dependencies=["problem_decomposition"]
                ),
                WorkflowStep(
                    step_id="reasoning_synthesis",
                    step_type="reasoning",
                    description="推理综合",
                    agent_roles=["answer_generator"],
                    parameters={"reasoning_mode": "step_by_step"},
                    dependencies=["sub_problem_research"]
                ),
                WorkflowStep(
                    step_id="logic_verification",
                    step_type="verification",
                    description="逻辑验证",
                    agent_roles=["quality_assessor"],
                    dependencies=["reasoning_synthesis"]
                )
            ],
            global_timeout=500
        )
        
        # 事实核查工作流
        fact_checking = WorkflowDefinition(
            workflow_id="fact_checking",
            workflow_type=WorkflowType.FACT_CHECKING,
            name="事实核查",
            description="验证信息的准确性和可信度",
            steps=[
                WorkflowStep(
                    step_id="claim_extraction",
                    step_type="extraction",
                    description="提取待验证声明",
                    agent_roles=["coordinator"],
                    parameters={"extract_claims": True}
                ),
                WorkflowStep(
                    step_id="evidence_search",
                    step_type="search",
                    description="证据搜索",
                    agent_roles=["semantic_searcher", "graph_searcher"],
                    parameters={"search_modes": ["semantic", "graph"], "top_k": 20},
                    dependencies=["claim_extraction"]
                ),
                WorkflowStep(
                    step_id="credibility_assessment",
                    step_type="assessment",
                    description="可信度评估",
                    agent_roles=["quality_assessor"],
                    dependencies=["evidence_search"]
                ),
                WorkflowStep(
                    step_id="fact_check_report",
                    step_type="generate",
                    description="生成核查报告",
                    agent_roles=["answer_generator"],
                    parameters={"report_type": "fact_check"},
                    dependencies=["credibility_assessment"]
                )
            ],
            global_timeout=400
        )
        
        # 注册所有工作流
        workflows = [simple_qa, complex_research, comparative_analysis, multi_step_reasoning, fact_checking]
        for workflow in workflows:
            self.workflow_definitions[workflow.workflow_id] = workflow
    
    async def initialize(self):
        """初始化工作流管理器"""
        await self.autogen_service.initialize()
        logger.info("工作流管理器初始化完成")
    
    def get_workflow_recommendation(self, query: str) -> WorkflowType:
        """根据查询推荐工作流类型"""
        query_lower = query.lower()
        
        # 比较分析
        if any(word in query_lower for word in ["比较", "对比", "区别", "差异", "相同", "不同"]):
            return WorkflowType.COMPARATIVE_ANALYSIS
        
        # 多步推理
        elif any(word in query_lower for word in ["为什么", "如何", "步骤", "过程", "原因", "推理"]):
            return WorkflowType.MULTI_STEP_REASONING
        
        # 事实核查
        elif any(word in query_lower for word in ["是否", "真的", "确实", "验证", "核实"]):
            return WorkflowType.FACT_CHECKING
        
        # 复杂研究
        elif len(query.split()) > 15 or any(word in query_lower for word in ["详细", "全面", "深入", "分析"]):
            return WorkflowType.COMPLEX_RESEARCH
        
        # 默认简单问答
        else:
            return WorkflowType.SIMPLE_QA
    
    async def execute_workflow(
        self,
        query: str,
        workflow_type: Optional[WorkflowType] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """执行工作流"""
        try:
            # 自动推荐工作流类型
            if workflow_type is None:
                workflow_type = self.get_workflow_recommendation(query)
            
            # 获取工作流定义
            workflow_def = self.workflow_definitions.get(workflow_type.value)
            if not workflow_def:
                raise WorkflowException(f"未找到工作流定义: {workflow_type.value}")
            
            # 创建执行实例
            execution = WorkflowExecution(
                execution_id=f"exec_{int(time.time())}_{len(self.execution_history)}",
                workflow_def=workflow_def,
                status=TaskStatus.RUNNING,
                start_time=time.time()
            )
            
            self.active_executions[execution.execution_id] = execution
            
            logger.info(f"开始执行工作流: {workflow_type.value}, 执行ID: {execution.execution_id}")
            
            # 执行工作流步骤
            if workflow_def.parallel_execution:
                await self._execute_parallel_workflow(execution, query, parameters or {})
            else:
                await self._execute_sequential_workflow(execution, query, parameters or {})
            
            # 完成执行
            execution.status = TaskStatus.COMPLETED
            execution.end_time = time.time()
            execution.progress = 1.0
            
            # 移动到历史记录
            self.execution_history.append(execution)
            del self.active_executions[execution.execution_id]
            
            logger.info(f"工作流执行完成: {execution.execution_id}, 耗时: {execution.end_time - execution.start_time:.2f}s")
            
            return execution
            
        except Exception as e:
            if 'execution' in locals():
                execution.status = TaskStatus.FAILED
                execution.error_message = str(e)
                execution.end_time = time.time()
                
                self.execution_history.append(execution)
                if execution.execution_id in self.active_executions:
                    del self.active_executions[execution.execution_id]
            
            logger.error(f"工作流执行失败: {e}")
            raise WorkflowException(f"工作流执行失败: {e}")
    
    async def _execute_sequential_workflow(
        self,
        execution: WorkflowExecution,
        query: str,
        parameters: Dict[str, Any]
    ):
        """执行顺序工作流"""
        total_steps = len(execution.workflow_def.steps)
        
        for i, step in enumerate(execution.workflow_def.steps):
            try:
                execution.current_step = step.step_id
                execution.progress = i / total_steps
                
                logger.info(f"执行步骤: {step.step_id} - {step.description}")
                
                # 检查依赖
                if not self._check_dependencies(step, execution.step_results):
                    raise WorkflowException(f"步骤 {step.step_id} 的依赖未满足")
                
                # 执行步骤
                step_result = await self._execute_step(step, query, execution.step_results, parameters)
                execution.step_results[step.step_id] = step_result
                
            except Exception as e:
                logger.error(f"步骤执行失败: {step.step_id}, 错误: {e}")
                if step.retry_count < step.max_retries:
                    step.retry_count += 1
                    logger.info(f"重试步骤: {step.step_id}, 第 {step.retry_count} 次")
                    continue
                else:
                    raise WorkflowException(f"步骤 {step.step_id} 执行失败: {e}")
    
    async def _execute_parallel_workflow(
        self,
        execution: WorkflowExecution,
        query: str,
        parameters: Dict[str, Any]
    ):
        """执行并行工作流"""
        # 构建依赖图
        dependency_graph = self._build_dependency_graph(execution.workflow_def.steps)
        
        # 按层级执行
        completed_steps = set()
        total_steps = len(execution.workflow_def.steps)
        
        while len(completed_steps) < total_steps:
            # 找到可以执行的步骤
            ready_steps = []
            for step in execution.workflow_def.steps:
                if (step.step_id not in completed_steps and 
                    all(dep in completed_steps for dep in step.dependencies)):
                    ready_steps.append(step)
            
            if not ready_steps:
                raise WorkflowException("工作流出现循环依赖或无法继续执行")
            
            # 并行执行就绪的步骤
            step_tasks = []
            for step in ready_steps:
                execution.current_step = step.step_id
                step_tasks.append(self._execute_step(step, query, execution.step_results, parameters))
            
            # 等待所有步骤完成
            step_results = await asyncio.gather(*step_tasks, return_exceptions=True)
            
            # 处理结果
            for step, result in zip(ready_steps, step_results):
                if isinstance(result, Exception):
                    logger.error(f"步骤执行失败: {step.step_id}, 错误: {result}")
                    raise WorkflowException(f"步骤 {step.step_id} 执行失败: {result}")
                else:
                    execution.step_results[step.step_id] = result
                    completed_steps.add(step.step_id)
            
            # 更新进度
            execution.progress = len(completed_steps) / total_steps
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        query: str,
        previous_results: Dict[str, Any],
        global_parameters: Dict[str, Any]
    ) -> Any:
        """执行单个步骤"""
        # 合并参数
        step_params = {**global_parameters, **step.parameters}
        
        if step.step_type == "search":
            # 执行检索步骤
            search_modes = step_params.get("search_modes", ["semantic"])
            top_k = step_params.get("top_k", 10)
            
            response = await self.autogen_service.process_query(
                query=query,
                search_modes=search_modes,
                top_k=top_k
            )
            
            return {
                "type": "search_result",
                "response": response,
                "search_results": response.search_results
            }
        
        elif step.step_type == "generate":
            # 执行生成步骤
            # 收集所有检索结果
            all_results = []
            for result in previous_results.values():
                if isinstance(result, dict) and "search_results" in result:
                    all_results.extend(result["search_results"])
            
            # 生成答案
            answer, confidence = await self.autogen_service.answer_agent.generate_answer(
                query, all_results, include_sources=True
            )
            
            return {
                "type": "generated_answer",
                "answer": answer,
                "confidence": confidence
            }
        
        elif step.step_type == "assessment":
            # 执行评估步骤
            all_results = []
            for result in previous_results.values():
                if isinstance(result, dict) and "search_results" in result:
                    all_results.extend(result["search_results"])
            
            quality_metrics = await self.autogen_service.quality_agent.assess_search_quality(query, all_results)
            
            return {
                "type": "quality_assessment",
                "metrics": quality_metrics
            }
        
        else:
            # 其他步骤类型的默认处理
            return {
                "type": step.step_type,
                "status": "completed",
                "message": f"步骤 {step.step_id} 执行完成"
            }
    
    def _check_dependencies(self, step: WorkflowStep, completed_results: Dict[str, Any]) -> bool:
        """检查步骤依赖"""
        return all(dep in completed_results for dep in step.dependencies)
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """构建依赖图"""
        graph = {}
        for step in steps:
            graph[step.step_id] = step.dependencies
        return graph
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        execution = self.active_executions.get(execution_id)
        if not execution:
            # 查找历史记录
            for hist_exec in self.execution_history:
                if hist_exec.execution_id == execution_id:
                    execution = hist_exec
                    break
        
        if not execution:
            return None
        
        return {
            "execution_id": execution.execution_id,
            "workflow_type": execution.workflow_def.workflow_type.value,
            "status": execution.status.value,
            "progress": execution.progress,
            "current_step": execution.current_step,
            "start_time": execution.start_time,
            "end_time": execution.end_time,
            "error_message": execution.error_message,
            "completed_steps": list(execution.step_results.keys())
        }
    
    def get_workflow_definitions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有工作流定义"""
        return {
            wf_id: {
                "workflow_id": wf.workflow_id,
                "workflow_type": wf.workflow_type.value,
                "name": wf.name,
                "description": wf.description,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "step_type": step.step_type,
                        "description": step.description,
                        "agent_roles": step.agent_roles,
                        "dependencies": step.dependencies
                    }
                    for step in wf.steps
                ],
                "global_timeout": wf.global_timeout,
                "parallel_execution": wf.parallel_execution
            }
            for wf_id, wf in self.workflow_definitions.items()
        }


# 全局工作流管理器实例
agent_workflow_manager = AgentWorkflowManager()
