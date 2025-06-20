"""
智能体管理器
负责协调和管理所有智能体的协作，实现多智能体工作流
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum

from .base_agent import BaseAgent
from .chat_agent import ChatAgent
from .knowledge_agent import KnowledgeAgent
from .tool_agent import ToolAgent
from .multimodal_agent import MultimodalAgent
from ..core.model_manager import model_manager

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """智能体类型枚举"""
    CHAT = "chat"
    KNOWLEDGE = "knowledge"
    TOOL = "tool"
    MULTIMODAL = "multimodal"


class WorkflowStep:
    """工作流步骤"""
    
    def __init__(
        self,
        agent_type: AgentType,
        condition: Optional[callable] = None,
        priority: int = 0,
        parallel: bool = False
    ):
        self.agent_type = agent_type
        self.condition = condition  # 执行条件函数
        self.priority = priority  # 优先级（数字越小优先级越高）
        self.parallel = parallel  # 是否可以并行执行
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0


class AgentManager:
    """
    智能体管理器
    
    主要职责：
    - 管理所有智能体的生命周期
    - 协调智能体之间的协作
    - 实现智能体工作流
    - 处理智能体间的消息传递
    - 监控智能体性能和状态
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化智能体管理器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.workflows: Dict[str, List[WorkflowStep]] = {}
        self.is_initialized = False
        
        # 管理器统计
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.created_at = datetime.now()
        
        # 默认工作流配置
        self._setup_default_workflows()
        
        logger.info("智能体管理器初始化完成")
    
    def _setup_default_workflows(self):
        """设置默认工作流"""
        
        # 标准聊天工作流
        self.workflows["standard_chat"] = [
            WorkflowStep(
                agent_type=AgentType.MULTIMODAL,
                condition=lambda ctx: self._has_multimodal_content(ctx),
                priority=1
            ),
            WorkflowStep(
                agent_type=AgentType.KNOWLEDGE,
                condition=lambda ctx: self._needs_knowledge_search(ctx),
                priority=2
            ),
            WorkflowStep(
                agent_type=AgentType.TOOL,
                condition=lambda ctx: self._needs_tool_call(ctx),
                priority=3
            ),
            WorkflowStep(
                agent_type=AgentType.CHAT,
                condition=None,  # 总是执行
                priority=4
            )
        ]
        
        # 知识检索工作流
        self.workflows["knowledge_search"] = [
            WorkflowStep(
                agent_type=AgentType.KNOWLEDGE,
                condition=None,
                priority=1
            ),
            WorkflowStep(
                agent_type=AgentType.CHAT,
                condition=None,
                priority=2
            )
        ]
        
        # 工具调用工作流
        self.workflows["tool_execution"] = [
            WorkflowStep(
                agent_type=AgentType.TOOL,
                condition=None,
                priority=1
            ),
            WorkflowStep(
                agent_type=AgentType.CHAT,
                condition=None,
                priority=2
            )
        ]
        
        # 多模态分析工作流
        self.workflows["multimodal_analysis"] = [
            WorkflowStep(
                agent_type=AgentType.MULTIMODAL,
                condition=None,
                priority=1
            ),
            WorkflowStep(
                agent_type=AgentType.KNOWLEDGE,
                condition=lambda ctx: self._needs_knowledge_search(ctx),
                priority=2
            ),
            WorkflowStep(
                agent_type=AgentType.CHAT,
                condition=None,
                priority=3
            )
        ]
    
    async def initialize(self):
        """初始化所有智能体"""
        try:
            # 初始化聊天智能体
            chat_config = self.config.get('chat_agent', {})
            self.agents[AgentType.CHAT] = ChatAgent(
                name="ChatAgent",
                model_config=chat_config
            )
            
            # 初始化知识检索智能体
            knowledge_config = self.config.get('knowledge_agent', {})
            knowledge_agent = KnowledgeAgent(
                name="KnowledgeAgent",
                model_config=knowledge_config
            )
            await knowledge_agent.initialize_services()
            self.agents[AgentType.KNOWLEDGE] = knowledge_agent
            
            # 初始化工具调用智能体
            tool_config = self.config.get('tool_agent', {})
            tool_agent = ToolAgent(
                name="ToolAgent",
                model_config=tool_config
            )
            await tool_agent.initialize_tools()
            self.agents[AgentType.TOOL] = tool_agent
            
            # 初始化多模态智能体
            multimodal_config = self.config.get('multimodal_agent', {})
            multimodal_agent = MultimodalAgent(
                name="MultimodalAgent",
                model_config=multimodal_config
            )
            await multimodal_agent.initialize_services()
            self.agents[AgentType.MULTIMODAL] = multimodal_agent
            
            # 设置智能体间的协作关系
            await self._setup_agent_collaboration()
            
            # 注入服务依赖
            await self._inject_services()
            
            self.is_initialized = True
            logger.info("所有智能体初始化完成")
            
        except Exception as e:
            logger.error(f"智能体初始化失败: {str(e)}")
            raise
    
    async def _setup_agent_collaboration(self):
        """设置智能体协作关系"""
        try:
            chat_agent = self.agents.get(AgentType.CHAT)
            knowledge_agent = self.agents.get(AgentType.KNOWLEDGE)
            tool_agent = self.agents.get(AgentType.TOOL)
            multimodal_agent = self.agents.get(AgentType.MULTIMODAL)
            
            # 为聊天智能体设置协作者
            if isinstance(chat_agent, ChatAgent):
                chat_agent.set_collaborator_agents(
                    knowledge_agent=knowledge_agent,
                    tool_agent=tool_agent,
                    multimodal_agent=multimodal_agent
                )
            
            logger.info("智能体协作关系设置完成")
            
        except Exception as e:
            logger.error(f"设置智能体协作关系失败: {str(e)}")
            raise
    
    async def _inject_services(self):
        """注入服务依赖"""
        try:
            # 获取服务实例
            memory_service = None  # 这里应该注入实际的记忆服务
            tool_service = self.agents.get(AgentType.TOOL)
            knowledge_service = self.agents.get(AgentType.KNOWLEDGE)
            model_service = model_manager
            
            # 为所有智能体注入服务
            for agent in self.agents.values():
                agent.inject_services(
                    memory_service=memory_service,
                    tool_service=tool_service,
                    knowledge_service=knowledge_service,
                    model_service=model_service
                )
            
            logger.info("服务依赖注入完成")
            
        except Exception as e:
            logger.error(f"服务依赖注入失败: {str(e)}")
            raise
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        model_config: Optional[Dict[str, Any]] = None,
        workflow: str = "standard_chat"
    ) -> str:
        """
        处理用户消息
        
        Args:
            message: 用户消息
            context: 上下文信息
            model_config: 模型配置
            workflow: 工作流名称
            
        Returns:
            处理结果
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            self.total_requests += 1
            
            # 选择工作流
            workflow_steps = self.workflows.get(workflow, self.workflows["standard_chat"])
            
            # 执行工作流
            result = await self._execute_workflow(
                workflow_steps, message, context, model_config
            )
            
            self.successful_requests += 1
            return result
            
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"消息处理失败: {str(e)}")
            return f"抱歉，处理您的消息时遇到了问题：{str(e)}"
    
    async def stream_chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        model_config: Optional[Dict[str, Any]] = None,
        workflow: str = "standard_chat"
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天处理
        
        Args:
            message: 用户消息
            context: 上下文信息
            model_config: 模型配置
            workflow: 工作流名称
            
        Yields:
            流式响应片段
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            self.total_requests += 1
            
            # 选择工作流
            workflow_steps = self.workflows.get(workflow, self.workflows["standard_chat"])
            
            # 执行流式工作流
            async for chunk in self._execute_workflow_stream(
                workflow_steps, message, context, model_config
            ):
                yield chunk
            
            self.successful_requests += 1
            
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"流式聊天处理失败: {str(e)}")
            yield f"抱歉，处理您的消息时遇到了问题：{str(e)}"
    
    async def _execute_workflow(
        self,
        workflow_steps: List[WorkflowStep],
        message: str,
        context: Optional[Dict[str, Any]] = None,
        model_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """执行工作流"""
        try:
            # 按优先级排序
            sorted_steps = sorted(workflow_steps, key=lambda x: x.priority)
            
            # 收集所有执行结果
            execution_results = {}
            
            for step in sorted_steps:
                step.execution_count += 1
                
                # 检查执行条件
                if step.condition and not step.condition(context):
                    continue
                
                try:
                    # 获取对应的智能体
                    agent = self.agents.get(step.agent_type)
                    if not agent:
                        logger.warning(f"智能体 {step.agent_type} 不可用")
                        continue
                    
                    # 执行智能体处理
                    result = await agent.process_message(message, context)
                    execution_results[step.agent_type] = result
                    step.success_count += 1
                    
                    # 如果是聊天智能体，直接返回结果
                    if step.agent_type == AgentType.CHAT:
                        return result
                    
                except Exception as e:
                    step.error_count += 1
                    logger.error(f"工作流步骤 {step.agent_type} 执行失败: {str(e)}")
                    execution_results[step.agent_type] = f"执行失败: {str(e)}"
            
            # 如果没有聊天智能体结果，组合其他结果
            return self._combine_results(execution_results)
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            return f"工作流执行失败: {str(e)}"
    
    async def _execute_workflow_stream(
        self,
        workflow_steps: List[WorkflowStep],
        message: str,
        context: Optional[Dict[str, Any]] = None,
        model_config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """执行流式工作流"""
        try:
            # 按优先级排序
            sorted_steps = sorted(workflow_steps, key=lambda x: x.priority)
            
            # 收集非聊天智能体的结果
            pre_results = {}
            
            for step in sorted_steps:
                # 检查执行条件
                if step.condition and not step.condition(context):
                    continue
                
                agent = self.agents.get(step.agent_type)
                if not agent:
                    continue
                
                try:
                    if step.agent_type == AgentType.CHAT:
                        # 聊天智能体使用流式输出
                        if hasattr(agent, 'stream_chat'):
                            async for chunk in agent.stream_chat(message, context):
                                yield chunk
                        else:
                            result = await agent.process_message(message, context)
                            # 模拟流式输出
                            for char in result:
                                yield char
                                await asyncio.sleep(0.01)
                        return
                    else:
                        # 其他智能体正常执行
                        result = await agent.process_message(message, context)
                        pre_results[step.agent_type] = result
                        
                except Exception as e:
                    logger.error(f"流式工作流步骤 {step.agent_type} 执行失败: {str(e)}")
                    pre_results[step.agent_type] = f"执行失败: {str(e)}"
            
            # 如果没有聊天智能体，返回组合结果
            combined_result = self._combine_results(pre_results)
            for char in combined_result:
                yield char
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"流式工作流执行失败: {str(e)}")
            error_msg = f"流式工作流执行失败: {str(e)}"
            for char in error_msg:
                yield char
                await asyncio.sleep(0.01)
    
    def _combine_results(self, results: Dict[AgentType, str]) -> str:
        """组合多个智能体的执行结果"""
        if not results:
            return "没有获得任何处理结果。"
        
        combined_parts = []
        
        if AgentType.MULTIMODAL in results:
            combined_parts.append(f"📸 多模态分析:\n{results[AgentType.MULTIMODAL]}")
        
        if AgentType.KNOWLEDGE in results:
            combined_parts.append(f"📚 知识检索:\n{results[AgentType.KNOWLEDGE]}")
        
        if AgentType.TOOL in results:
            combined_parts.append(f"🔧 工具执行:\n{results[AgentType.TOOL]}")
        
        return "\n\n".join(combined_parts)
    
    # 条件判断函数
    def _has_multimodal_content(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """检查是否包含多模态内容"""
        if not context:
            return False
        return bool(context.get('images') or context.get('files'))
    
    def _needs_knowledge_search(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """检查是否需要知识搜索"""
        if not context:
            return True  # 默认启用知识搜索
        return context.get('enable_knowledge', True)
    
    def _needs_tool_call(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """检查是否需要工具调用"""
        if not context:
            return True  # 默认启用工具调用
        return context.get('enable_tools', True)
    
    async def get_agent_status(self, agent_type: Optional[AgentType] = None) -> Dict[str, Any]:
        """获取智能体状态"""
        if agent_type:
            agent = self.agents.get(agent_type)
            if agent:
                return agent.get_status()
            else:
                return {"error": f"智能体 {agent_type} 不存在"}
        else:
            # 返回所有智能体状态
            status = {}
            for agent_type, agent in self.agents.items():
                status[agent_type.value] = agent.get_status()
            return status
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                "manager_status": "healthy",
                "is_initialized": self.is_initialized,
                "total_agents": len(self.agents),
                "healthy_agents": 0,
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": self.successful_requests / max(self.total_requests, 1),
                "agents": {},
                "workflows": list(self.workflows.keys())
            }
            
            # 检查每个智能体的健康状态
            for agent_type, agent in self.agents.items():
                try:
                    is_healthy = await agent.health_check()
                    agent_status = agent.get_status()
                    agent_status["is_healthy"] = is_healthy
                    
                    health_status["agents"][agent_type.value] = agent_status
                    
                    if is_healthy:
                        health_status["healthy_agents"] += 1
                        
                except Exception as e:
                    health_status["agents"][agent_type.value] = {
                        "is_healthy": False,
                        "error": str(e)
                    }
            
            # 检查工作流状态
            workflow_stats = {}
            for workflow_name, steps in self.workflows.items():
                workflow_stats[workflow_name] = {
                    "total_steps": len(steps),
                    "steps": [
                        {
                            "agent_type": step.agent_type.value,
                            "execution_count": step.execution_count,
                            "success_count": step.success_count,
                            "error_count": step.error_count,
                            "success_rate": step.success_count / max(step.execution_count, 1)
                        }
                        for step in steps
                    ]
                }
            
            health_status["workflow_stats"] = workflow_stats
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return {
                "manager_status": "error",
                "error": str(e),
                "is_initialized": self.is_initialized
            }
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        return {
            "created_at": self.created_at.isoformat(),
            "is_initialized": self.is_initialized,
            "total_agents": len(self.agents),
            "total_workflows": len(self.workflows),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / max(self.total_requests, 1),
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds()
        }
