# 导入所有模型以确保它们被注册
from .user import User
from .document import Document
from .ai_session import AISession
from .template import TemplateCategory, TemplateType, TemplateFile, WritingScenarioConfig, WritingFieldConfig
from .agent_config import AgentConfig, AgentTool, AgentModel
from .writing_theme import WritingTheme, ThemeField, PromptTemplate, ThemeCategory as WritingThemeCategory, WritingHistory

# 设置关系
from sqlalchemy.orm import relationship
User.documents = relationship("Document", back_populates="user")

__all__ = [
    "User", "Document", "AISession",
    "TemplateCategory", "TemplateType", "TemplateFile", "WritingScenarioConfig", "WritingFieldConfig",
    "AgentConfig", "AgentTool", "AgentModel",
    "WritingTheme", "ThemeField", "PromptTemplate", "WritingThemeCategory", "WritingHistory"
]
