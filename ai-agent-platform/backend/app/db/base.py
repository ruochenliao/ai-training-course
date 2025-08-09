"""
# Copyright (c) 2025 左岚. All rights reserved.

数据库基础设置和初始化
"""
from app.db.base_class import Base  # noqa

# 导入所有模型，确保它们被注册到Base.metadata中
from app.models.user import User, Role, OperationLog  # noqa
from app.models.agent import Agent, AgentTemplate  # noqa
from app.models.knowledge import KnowledgeBase, File, DocumentChunk  # noqa
from app.models.chat import ChatSession, ChatMessage, Conversation  # noqa
