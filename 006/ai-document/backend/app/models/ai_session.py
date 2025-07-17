from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class AISession(Base):
    __tablename__ = "ai_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    ai_type = Column(String(50), nullable=False)  # AI工具类型：AI写作、AI润色、deepseek等
    prompt = Column(Text)
    response = Column(Text)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    session_metadata = Column(JSON)  # 存储额外的会话信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User")
    document = relationship("Document")
    
    def __repr__(self):
        return f"<AISession(id={self.id}, session_id='{self.session_id}', ai_type='{self.ai_type}')>"
