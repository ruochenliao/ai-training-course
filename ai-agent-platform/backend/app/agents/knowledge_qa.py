"""
# Copyright (c) 2025 左岚. All rights reserved.

知识库问答智能体

基于企业知识库回答专业问题，提供准确的信息检索和问答服务。
"""

# # Standard library imports
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any, Dict, List, Optional

# # Local folder imports
from ..rag.generator import CitationStyle, GenerationStrategy
from ..rag.rag_agent import RAGAgent, RAGConfig
from .base import AgentConfig, AgentMessage, BaseAgent
from .llm_interface import llm_manager

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """问题类型"""
    FACTUAL = "factual"  # 事实性问题
    PROCEDURAL = "procedural"  # 程序性问题
    CONCEPTUAL = "conceptual"  # 概念性问题
    COMPARATIVE = "comparative"  # 比较性问题
    TROUBLESHOOTING = "troubleshooting"  # 故障排除
    POLICY = "policy"  # 政策规定


class AnswerQuality(Enum):
    """答案质量"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class KnowledgeQASession:
    """知识问答会话"""
    
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.questions: List[Dict[str, Any]] = []
        self.context_memory: List[str] = []
        self.topic_focus = None
        self.satisfaction_score = None
    
    def add_question(self, question: str, answer: str, sources: List[Dict[str, Any]],
                    confidence: float, question_type: QuestionType):
        """添加问答记录"""
        qa_record = {
            "id": len(self.questions) + 1,
            "question": question,
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "question_type": question_type.value,
            "timestamp": datetime.now().isoformat()
        }
        self.questions.append(qa_record)
        
        # 更新上下文记忆
        self.context_memory.append(f"Q: {question}")
        self.context_memory.append(f"A: {answer[:200]}...")
        
        # 保持上下文记忆在合理长度
        if len(self.context_memory) > 10:
            self.context_memory = self.context_memory[-10:]
    
    def get_context(self) -> str:
        """获取会话上下文"""
        return "\n".join(self.context_memory)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "questions": self.questions,
            "topic_focus": self.topic_focus,
            "satisfaction_score": self.satisfaction_score,
            "question_count": len(self.questions)
        }


class KnowledgeQAAgent(BaseAgent):
    """知识库问答智能体"""
    
    def __init__(self, config: AgentConfig = None, rag_agent: RAGAgent = None):
        if config is None:
            config = AgentConfig(
                name="KnowledgeQAAgent",
                description="基于企业知识库的专业问答智能体",
                model="gpt-4o",
                temperature=0.7,
                system_prompt=self._get_system_prompt()
            )
        
        super().__init__(config)
        
        # RAG智能体
        self.rag_agent = rag_agent or self._create_default_rag_agent()
        
        # 会话管理
        self.sessions: Dict[str, KnowledgeQASession] = {}
        
        # 知识库统计
        self.stats = {
            "total_questions": 0,
            "successful_answers": 0,
            "average_confidence": 0.0,
            "popular_topics": {},
            "user_satisfaction": 0.0
        }
        
        # 问题分类缓存
        self.question_cache: Dict[str, Dict[str, Any]] = {}
    
    def _create_default_rag_agent(self) -> RAGAgent:
        """创建默认RAG智能体"""
        rag_config = RAGConfig(
            vector_store_type="memory",
            embedding_model="openai",
            retrieval_top_k=5,
            generation_strategy=GenerationStrategy.ABSTRACTIVE,
            citation_style=CitationStyle.NUMBERED,
            enable_query_expansion=True,
            enable_reranking=True
        )
        
        rag_agent = RAGAgent(rag_config=rag_config)
        return rag_agent
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的知识库问答助手，专门基于企业知识库为用户提供准确、有用的答案。

核心能力：
1. 理解用户问题的真实意图
2. 从知识库中检索相关信息
3. 生成准确、完整的答案
4. 提供可靠的信息来源
5. 处理复杂的多步骤问题

问答原则：
1. 准确性：基于知识库内容提供准确信息
2. 完整性：尽可能提供全面的答案
3. 可追溯：明确标注信息来源
4. 诚实性：承认知识库中没有的信息
5. 有用性：提供实用的建议和指导

回答风格：
- 专业但易懂
- 结构清晰，逻辑分明
- 适当使用例子和类比
- 主动提供相关信息
- 鼓励进一步提问

特殊处理：
- 对于模糊问题，主动澄清
- 对于复杂问题，分步骤回答
- 对于政策问题，强调时效性
- 对于技术问题，提供详细步骤
- 对于比较问题，列出优缺点

始终记住：你的目标是帮助用户快速找到准确的信息，解决实际问题。"""
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """处理知识问答请求"""
        try:
            # 获取或创建会话
            session_id = message.metadata.get("session_id", f"session_{message.sender}_{datetime.now().timestamp()}")
            session = self._get_or_create_session(session_id, message.sender)
            
            # 分析问题类型
            question_analysis = await self._analyze_question(message.content, session.get_context())
            
            # 构建增强查询
            enhanced_query = await self._enhance_query(message.content, session.get_context(), question_analysis)
            
            # 执行RAG查询
            rag_result = await self.rag_agent.query(
                query=enhanced_query,
                kb_filter=message.metadata.get("kb_filter"),
                top_k=message.metadata.get("top_k", 5)
            )
            
            # 生成最终答案
            final_answer = await self._generate_contextual_answer(
                question=message.content,
                rag_result=rag_result,
                question_analysis=question_analysis,
                session_context=session.get_context()
            )
            
            # 记录问答
            session.add_question(
                question=message.content,
                answer=final_answer["answer"],
                sources=rag_result["sources"],
                confidence=final_answer["confidence"],
                question_type=QuestionType(question_analysis.get("type", "factual"))
            )
            
            # 更新统计
            self._update_stats(final_answer["confidence"], question_analysis.get("topic"))
            
            # 构建响应
            response_content = json.dumps({
                "answer": final_answer["answer"],
                "sources": rag_result["sources"],
                "confidence": final_answer["confidence"],
                "question_type": question_analysis.get("type"),
                "follow_up_suggestions": final_answer.get("follow_up_suggestions", [])
            }, ensure_ascii=False, indent=2)
            
            response = AgentMessage(
                id=f"qa_response_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=response_content,
                message_type="knowledge_qa_response",
                metadata={
                    "original_message_id": message.id,
                    "session_id": session_id,
                    "question_analysis": question_analysis,
                    "rag_metadata": rag_result["metadata"]
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"知识问答处理失败: {e}")
            error_response = AgentMessage(
                id=f"qa_error_{message.id}",
                sender=self.name,
                receiver=message.sender,
                content=f"知识库查询失败: {str(e)}",
                message_type="error"
            )
            return error_response
    
    async def _analyze_question(self, question: str, context: str = "") -> Dict[str, Any]:
        """分析问题类型和特征"""
        try:
            # 检查缓存
            cache_key = f"{question}_{len(context)}"
            if cache_key in self.question_cache:
                return self.question_cache[cache_key]
            
            prompt = f"""
请分析以下问题的类型和特征：

问题：{question}

会话上下文：
{context}

请返回JSON格式的分析结果：
{{
    "type": "factual|procedural|conceptual|comparative|troubleshooting|policy",
    "complexity": "simple|medium|complex",
    "topic": "主要话题",
    "intent": "用户意图描述",
    "keywords": ["关键词1", "关键词2"],
    "requires_context": true/false,
    "follow_up_likely": true/false,
    "urgency": "low|medium|high"
}}

分析要点：
1. 问题类型（事实性、程序性、概念性、比较性、故障排除、政策）
2. 复杂程度
3. 主要话题领域
4. 用户真实意图
5. 关键词提取
6. 是否需要上下文
7. 是否可能有后续问题
8. 紧急程度
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.3,
                max_tokens=500
            )
            
            try:
                analysis = json.loads(response.content)
                self.question_cache[cache_key] = analysis
                return analysis
            except json.JSONDecodeError:
                return {
                    "type": "factual",
                    "complexity": "medium",
                    "topic": "general",
                    "intent": "信息查询",
                    "keywords": [],
                    "requires_context": False,
                    "follow_up_likely": False,
                    "urgency": "medium"
                }
                
        except Exception as e:
            logger.error(f"问题分析失败: {e}")
            return {
                "type": "factual",
                "complexity": "medium",
                "topic": "general",
                "intent": "分析失败",
                "keywords": [],
                "requires_context": False,
                "follow_up_likely": False,
                "urgency": "medium"
            }
    
    async def _enhance_query(self, question: str, context: str, analysis: Dict[str, Any]) -> str:
        """增强查询"""
        try:
            if not analysis.get("requires_context") or not context:
                return question
            
            prompt = f"""
基于会话上下文，增强用户的查询以提高检索效果。

原始问题：{question}

会话上下文：
{context}

问题分析：{json.dumps(analysis, ensure_ascii=False)}

请生成一个增强的查询，要求：
1. 保持原问题的核心意图
2. 添加必要的上下文信息
3. 使用更精确的关键词
4. 适合向量检索

增强查询：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.5,
                max_tokens=200
            )
            
            enhanced_query = response.content.strip()
            return enhanced_query if enhanced_query else question
            
        except Exception as e:
            logger.error(f"查询增强失败: {e}")
            return question
    
    async def _generate_contextual_answer(self, question: str, rag_result: Dict[str, Any],
                                        question_analysis: Dict[str, Any], session_context: str) -> Dict[str, Any]:
        """生成上下文相关的答案"""
        try:
            # 如果RAG结果置信度很高，直接使用
            if rag_result["confidence"] > 0.8:
                answer = rag_result["answer"]
                confidence = rag_result["confidence"]
            else:
                # 使用上下文增强答案
                prompt = f"""
基于检索到的信息和会话上下文，为用户问题生成准确、有用的答案。

用户问题：{question}

问题分析：{json.dumps(question_analysis, ensure_ascii=False)}

检索到的信息：
{rag_result["answer"]}

会话上下文：
{session_context}

请生成一个高质量的答案，要求：
1. 基于检索信息回答问题
2. 考虑会话上下文
3. 根据问题类型调整回答风格
4. 提供清晰的结构和逻辑
5. 在适当时候提供例子或建议

答案：
"""
                
                response = await llm_manager.generate(
                    prompt=prompt,
                    model=self.model,
                    temperature=0.7,
                    max_tokens=1500
                )
                
                answer = response.content
                confidence = min(rag_result["confidence"] + 0.1, 0.95)
            
            # 生成后续问题建议
            follow_up_suggestions = await self._generate_follow_up_suggestions(
                question, answer, question_analysis
            )
            
            return {
                "answer": answer,
                "confidence": confidence,
                "follow_up_suggestions": follow_up_suggestions
            }
            
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return {
                "answer": rag_result["answer"],
                "confidence": rag_result["confidence"],
                "follow_up_suggestions": []
            }
    
    async def _generate_follow_up_suggestions(self, question: str, answer: str,
                                            analysis: Dict[str, Any]) -> List[str]:
        """生成后续问题建议"""
        try:
            if not analysis.get("follow_up_likely"):
                return []
            
            prompt = f"""
基于用户的问题和答案，生成3个相关的后续问题建议。

原问题：{question}
答案：{answer[:300]}...
问题类型：{analysis.get("type")}
话题：{analysis.get("topic")}

请生成JSON数组格式的后续问题：
["后续问题1", "后续问题2", "后续问题3"]

要求：
1. 与原问题相关但不重复
2. 能够深入探讨相关话题
3. 实用且有价值
4. 简洁明了
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.8,
                max_tokens=300
            )
            
            try:
                suggestions = json.loads(response.content)
                return suggestions if isinstance(suggestions, list) else []
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            logger.error(f"后续问题生成失败: {e}")
            return []
    
    def _get_or_create_session(self, session_id: str, user_id: str) -> KnowledgeQASession:
        """获取或创建会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = KnowledgeQASession(session_id, user_id)
        return self.sessions[session_id]
    
    def _update_stats(self, confidence: float, topic: str = None):
        """更新统计信息"""
        self.stats["total_questions"] += 1
        
        if confidence > 0.7:
            self.stats["successful_answers"] += 1
        
        # 更新平均置信度
        total = self.stats["total_questions"]
        current_avg = self.stats["average_confidence"]
        self.stats["average_confidence"] = (current_avg * (total - 1) + confidence) / total
        
        # 更新热门话题
        if topic:
            if topic not in self.stats["popular_topics"]:
                self.stats["popular_topics"][topic] = 0
            self.stats["popular_topics"][topic] += 1
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """生成响应"""
        response = await llm_manager.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.content
    
    async def initialize_rag(self):
        """初始化RAG系统"""
        await self.rag_agent.initialize()
    
    async def add_knowledge(self, content: str, metadata: Dict[str, Any] = None, kb_id: str = "default"):
        """添加知识到知识库"""
        return await self.rag_agent.add_document(content, metadata, kb_id)
    
    def get_session(self, session_id: str) -> Optional[KnowledgeQASession]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def list_sessions(self, user_id: str = None) -> List[KnowledgeQASession]:
        """列出会话"""
        sessions = list(self.sessions.values())
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        return sessions
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "active_sessions": len(self.sessions),
            "cache_size": len(self.question_cache)
        }
