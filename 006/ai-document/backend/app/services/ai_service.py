import uuid
import asyncio
import logging
from typing import AsyncGenerator, Optional, List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# AutoGen imports
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import GraphFlow, DiGraphBuilder
from autogen_agentchat.messages import TextMessage, ModelClientStreamingChunkEvent
from autogen_agentchat.base import TaskResult
from app.models.ai_session import AISession
from app.schemas.ai import AIRequest, AIStreamResponse
from app.core.model_clients import get_default_model_client
from app.config.autogen_config import (
    AGENT_CONFIGS,
    COLLABORATION_MODES,
    TASK_AGENT_MAPPING,
    COLLABORATIVE_TASK_MAPPING,
    MODEL_CONFIG,
    STREAMING_CONFIG
)


class AIService:
    """基于AutoGen的AI服务"""

    def __init__(self):
        # 使用统一的模型客户端管理器
        try:
            self.model_client = get_default_model_client()
        except ValueError as e:
            logger.warning(f"模型客户端初始化失败: {e}")
            self.model_client = None

        # 初始化智能体
        self.agents = {}
        if self.model_client:
            self._initialize_agents()
        else:
            logger.warning("由于模型客户端不可用，跳过智能体初始化")

    def _initialize_agents(self):
        """初始化各种专业智能体"""
        for agent_key, config in AGENT_CONFIGS.items():
            self.agents[agent_key] = AssistantAgent(
                name=config["name"],
                model_client=self.model_client,
                system_message=config["system_message"],
                model_client_stream=True
            )

    def get_agent_for_task(self, ai_type: str) -> AssistantAgent:
        """根据任务类型获取对应的智能体"""
        agent_key = TASK_AGENT_MAPPING.get(ai_type, 'writer')
        return self.agents[agent_key]

    def get_collaboration_mode(self, ai_type: str) -> dict:
        """获取协作模式配置"""
        mode_key = COLLABORATIVE_TASK_MAPPING.get(ai_type, 'writing')
        return COLLABORATION_MODES[mode_key]

    def create_session(self, db: Session, user_id: int, ai_request: AIRequest) -> AISession:
        """创建AI会话"""
        session_id = str(uuid.uuid4())

        ai_session = AISession(
            session_id=session_id,
            user_id=user_id,
            document_id=ai_request.document_id,
            ai_type=ai_request.ai_type,
            prompt=ai_request.prompt,
            status="pending",
            session_metadata=ai_request.metadata or {}
        )

        db.add(ai_session)
        db.commit()
        db.refresh(ai_session)
        return ai_session
    
    def update_session_status(self, db: Session, session_id: str, status: str, response: Optional[str] = None):
        """更新会话状态"""
        session = db.query(AISession).filter(AISession.session_id == session_id).first()
        if session:
            session.status = status
            if response:
                session.response = response
            db.commit()
    
    async def generate_single_agent_response(
        self,
        db: Session,
        session_id: str,
        ai_type: str,
        prompt: str,
        context: Optional[str] = None
    ) -> AsyncGenerator[AIStreamResponse, None]:
        """单智能体生成响应 - 支持真实流式输出"""
        try:
            self.update_session_status(db, session_id, "processing")

            # 获取对应的智能体
            agent = self.get_agent_for_task(ai_type)

            # 构建消息
            if context:
                full_prompt = f"上下文：{context}\n\n用户要求：{prompt}"
            else:
                full_prompt = prompt

            message = TextMessage(content=full_prompt, source="user")

            # 使用流式生成
            full_response = ""
            stream = agent.run_stream(task=[message])

            async for event in stream:
                # 处理流式输出事件
                if isinstance(event, ModelClientStreamingChunkEvent):
                    if event.content:
                        full_response += event.content
                        yield AIStreamResponse(
                            session_id=session_id,
                            content=event.content,
                            is_complete=False
                        )

                # 处理完成事件
                elif isinstance(event, TaskResult):
                    # 任务完成，获取完整响应
                    if event.messages and len(event.messages) > 0:
                        final_message = event.messages[-1]
                        if hasattr(final_message, 'content'):
                            full_response = final_message.content
                    break

            # 如果没有通过流式获得内容，但有最终响应，则发送最终响应
            if not full_response and hasattr(event, 'messages') and event.messages:
                full_response = event.messages[-1].content if event.messages[-1].content else ""

            # 完成响应 - 发送最终完整内容
            yield AIStreamResponse(
                session_id=session_id,
                content=full_response,
                is_complete=True
            )

            # 更新会话状态
            self.update_session_status(db, session_id, "completed", full_response.strip())

        except Exception as e:
            error_msg = str(e)
            self.update_session_status(db, session_id, "failed")

            yield AIStreamResponse(
                session_id=session_id,
                content="",
                is_complete=True,
                error=error_msg
            )
    
    async def generate_stream_response(
        self,
        db: Session,
        session_id: str,
        ai_type: str,
        prompt: str,
        context: Optional[str] = None
    ) -> AsyncGenerator[AIStreamResponse, None]:
        """生成流式响应 - 基于AutoGen"""
        # 检查是否需要多智能体协作
        if ai_type == "ai_collaborative":
            # 根据提示复杂度选择协作模式
            from app.utils.agent_utils import agent_manager
            complexity = agent_manager.get_task_complexity_score(prompt, context)
            strategy = agent_manager.suggest_collaboration_strategy(ai_type, complexity, prompt)

            async for response in self.generate_collaborative_response(
                db, session_id, prompt, context,
                agents_to_use=strategy["agents"],
                collaboration_mode=strategy["mode"]
            ):
                yield response
        else:
            async for response in self.generate_single_agent_response(
                db, session_id, ai_type, prompt, context
            ):
                yield response

    async def generate_collaborative_response(
        self,
        db: Session,
        session_id: str,
        prompt: str,
        context: Optional[str] = None,
        agents_to_use: List[str] = None,
        collaboration_mode: str = "writing"
    ) -> AsyncGenerator[AIStreamResponse, None]:
        """多智能体协作生成响应 - 基于GraphFlow的真实流式输出"""
        try:
            self.update_session_status(db, session_id, "processing")

            # 获取协作模式配置
            if not agents_to_use:
                mode_config = COLLABORATION_MODES.get(collaboration_mode, COLLABORATION_MODES["writing"])
                agents_to_use = mode_config["agents"]

            # 创建协作团队
            team = await self._create_collaboration_team(agents_to_use)

            # 构建初始消息
            if context:
                full_prompt = f"上下文：{context}\n\n任务：{prompt}\n\n请各位专家协作完成这个任务。"
            else:
                full_prompt = f"任务：{prompt}\n\n请各位专家协作完成这个任务。"

            initial_message = TextMessage(content=full_prompt, source="user")

            # 运行团队协作并处理流式输出
            full_response = ""
            stream = team.run_stream(task=initial_message)

            async for event in stream:
                # 处理流式输出事件
                if isinstance(event, ModelClientStreamingChunkEvent):
                    if event.content:
                        full_response += event.content
                        # 发送带来源信息的流式响应
                        yield AIStreamResponse(
                            session_id=session_id,
                            content=f"[{event.source}] {event.content}",
                            is_complete=False
                        )

                # 处理任务完成事件
                elif isinstance(event, TaskResult):
                    # 处理最终结果
                    if event.messages:
                        # 整合所有智能体的响应
                        integrated_response = await self._integrate_team_responses(event.messages)

                        # 发送整合后的最终响应
                        yield AIStreamResponse(
                            session_id=session_id,
                            content=f"\n\n=== 协作总结 ===\n{integrated_response}",
                            is_complete=False
                        )

                        full_response += f"\n\n=== 协作总结 ===\n{integrated_response}"
                    break

            # 完成响应
            yield AIStreamResponse(
                session_id=session_id,
                content="",
                is_complete=True
            )

            # 更新会话状态
            self.update_session_status(db, session_id, "completed", full_response.strip())

        except Exception as e:
            error_msg = str(e)
            self.update_session_status(db, session_id, "failed")

            yield AIStreamResponse(
                session_id=session_id,
                content="",
                is_complete=True,
                error=error_msg
            )

    async def _create_collaboration_team(self, agents_to_use: List[str]) -> GraphFlow:
        """创建基于GraphFlow的协作团队"""
        try:
            # 获取参与协作的智能体
            participating_agents = []
            for agent_key in agents_to_use:
                if agent_key in self.agents:
                    participating_agents.append(self.agents[agent_key])

            if not participating_agents:
                raise ValueError("没有找到可用的智能体")

            # 构建GraphFlow工作流
            builder = DiGraphBuilder()

            # 添加所有节点
            for agent in participating_agents:
                builder.add_node(agent)

            # 构建协作流程图
            if len(participating_agents) == 1:
                # 单智能体，无需连接
                pass
            elif len(participating_agents) == 2:
                # 两个智能体：顺序执行
                builder.add_edge(participating_agents[0], participating_agents[1])
            else:
                # 多智能体：构建协作流程
                # 第一个智能体开始
                for i in range(len(participating_agents) - 1):
                    builder.add_edge(participating_agents[i], participating_agents[i + 1])

                # 如果有reviewer，让它最后执行
                if 'reviewer' in agents_to_use and len(participating_agents) > 2:
                    reviewer_agent = None
                    for agent in participating_agents:
                        if agent.name == "ReviewerAgent":
                            reviewer_agent = agent
                            break

                    if reviewer_agent:
                        # 重新构建，让reviewer最后执行
                        builder = DiGraphBuilder()
                        for agent in participating_agents:
                            builder.add_node(agent)

                        # 其他智能体先执行
                        other_agents = [a for a in participating_agents if a != reviewer_agent]
                        for i in range(len(other_agents) - 1):
                            builder.add_edge(other_agents[i], other_agents[i + 1])

                        # 最后一个智能体连接到reviewer
                        if other_agents:
                            builder.add_edge(other_agents[-1], reviewer_agent)

            # 构建图
            graph = builder.build()

            # 创建GraphFlow团队
            team = GraphFlow(
                participants=participating_agents,
                graph=graph
            )

            return team

        except Exception as e:
            raise Exception(f"创建协作团队失败: {str(e)}")

    async def _integrate_team_responses(self, messages: List) -> str:
        """整合团队响应"""
        try:
            integrated_content = ""
            agent_responses = {}

            # 按智能体分类响应
            for message in messages:
                if hasattr(message, 'source') and hasattr(message, 'content'):
                    source = message.source
                    content = message.content

                    if source not in agent_responses:
                        agent_responses[source] = []
                    agent_responses[source].append(content)

            # 构建整合响应
            for agent_name, responses in agent_responses.items():
                if responses:
                    integrated_content += f"\n**{agent_name}的贡献：**\n"
                    for response in responses:
                        integrated_content += f"{response}\n"
                    integrated_content += "\n"

            # 如果没有分类响应，返回所有内容
            if not integrated_content:
                for message in messages:
                    if hasattr(message, 'content') and message.content:
                        integrated_content += message.content + "\n"

            return integrated_content.strip()

        except Exception as e:
            return f"整合团队响应时出错: {str(e)}"

    async def generate_collaborative_writing(
        self,
        db: Session,
        session_id: str,
        prompt: str,
        context: Optional[str] = None
    ) -> AsyncGenerator[AIStreamResponse, None]:
        """多智能体协作写作"""
        agents_to_use = ['writer', 'researcher', 'reviewer']
        async for response in self.generate_collaborative_response(
            db, session_id, prompt, context, agents_to_use
        ):
            yield response

    async def generate_expert_review(
        self,
        db: Session,
        session_id: str,
        content: str,
        review_type: str = "general"
    ) -> AsyncGenerator[AIStreamResponse, None]:
        """专家评审内容"""
        agents_to_use = ['reviewer', 'polisher']
        prompt = f"请对以下内容进行{review_type}评审：\n\n{content}"
        async for response in self.generate_collaborative_response(
            db, session_id, prompt, None, agents_to_use
        ):
            yield response


# 全局AI服务实例
ai_service = AIService()
