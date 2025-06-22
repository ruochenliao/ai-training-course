"""
智能问答服务
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, AsyncGenerator

from app.core.config import settings
from app.services.advanced_search_service import advanced_search_service, SearchConfig, SearchType
from app.services.entity_extraction_service import entity_extraction_service
from app.services.llm_service import llm_service
from app.services.vlm_service import vlm_service
from loguru import logger

from app.core.exceptions import QAException


class QuestionType(Enum):
    """问题类型枚举"""
    FACTUAL = "factual"  # 事实性问题
    ANALYTICAL = "analytical"  # 分析性问题
    COMPARATIVE = "comparative"  # 比较性问题
    PROCEDURAL = "procedural"  # 程序性问题
    CREATIVE = "creative"  # 创造性问题
    MULTIMODAL = "multimodal"  # 多模态问题


@dataclass
class QAContext:
    """问答上下文"""
    question: str
    question_type: QuestionType
    knowledge_base_id: int
    user_id: str
    session_id: str
    history: List[Dict[str, str]] = None
    constraints: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.constraints is None:
            self.constraints = {}


@dataclass
class QAResult:
    """问答结果"""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    reasoning: str = ""
    suggestions: List[str] = None
    related_questions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.related_questions is None:
            self.related_questions = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "sources": self.sources,
            "reasoning": self.reasoning,
            "suggestions": self.suggestions,
            "related_questions": self.related_questions
        }


class IntelligentQAService:
    """智能问答服务类"""
    
    def __init__(self):
        """初始化问答服务"""
        self.max_context_length = 8000
        self.max_sources = 10
        self.confidence_threshold = 0.7
        
        # 问题类型识别模板
        self.question_patterns = {
            QuestionType.FACTUAL: ["什么是", "谁是", "哪里", "何时", "多少"],
            QuestionType.ANALYTICAL: ["为什么", "如何分析", "原因", "影响"],
            QuestionType.COMPARATIVE: ["比较", "区别", "相同", "不同", "优缺点"],
            QuestionType.PROCEDURAL: ["如何", "怎样", "步骤", "流程", "方法"],
            QuestionType.CREATIVE: ["设计", "创建", "建议", "方案", "策略"],
            QuestionType.MULTIMODAL: ["图片", "图表", "视频", "音频", "文件"]
        }
        
        logger.info("智能问答服务初始化完成")
    
    async def answer_question(
        self,
        context: QAContext,
        stream: bool = False
    ) -> QAResult:
        """
        回答问题
        
        Args:
            context: 问答上下文
            stream: 是否流式返回
            
        Returns:
            问答结果
        """
        try:
            # 1. 问题分析
            question_type = await self._analyze_question_type(context.question)
            context.question_type = question_type
            
            # 2. 检索相关信息
            sources = await self._retrieve_relevant_information(context)
            
            # 3. 生成答案
            if stream:
                # 流式生成（这里简化处理，实际应该返回AsyncGenerator）
                answer = await self._generate_answer_stream(context, sources)
            else:
                answer = await self._generate_answer(context, sources)
            
            # 4. 评估置信度
            confidence = await self._evaluate_confidence(context.question, answer, sources)
            
            # 5. 生成推理过程
            reasoning = await self._generate_reasoning(context, sources, answer)
            
            # 6. 生成建议和相关问题
            suggestions = await self._generate_suggestions(context, answer)
            related_questions = await self._generate_related_questions(context)
            
            result = QAResult(
                answer=answer,
                confidence=confidence,
                sources=[source.to_dict() for source in sources],
                reasoning=reasoning,
                suggestions=suggestions,
                related_questions=related_questions
            )
            
            logger.info(f"问答完成，置信度: {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"问答失败: {e}")
            raise QAException(f"问答失败: {e}")
    
    async def answer_question_stream(
        self,
        context: QAContext
    ) -> AsyncGenerator[str, None]:
        """流式问答"""
        try:
            # 问题分析
            question_type = await self._analyze_question_type(context.question)
            context.question_type = question_type
            
            # 检索信息
            sources = await self._retrieve_relevant_information(context)
            
            # 流式生成答案
            async for chunk in self._generate_answer_stream(context, sources):
                yield chunk
                
        except Exception as e:
            logger.error(f"流式问答失败: {e}")
            yield f"抱歉，回答问题时出现错误: {str(e)}"
    
    async def _analyze_question_type(self, question: str) -> QuestionType:
        """分析问题类型"""
        try:
            # 基于关键词的简单分类
            question_lower = question.lower()
            
            for q_type, patterns in self.question_patterns.items():
                for pattern in patterns:
                    if pattern in question_lower:
                        return q_type
            
            # 使用LLM进行更精确的分类
            prompt = f"""
请分析以下问题的类型，从以下选项中选择最合适的一个：
1. factual - 事实性问题（询问具体信息）
2. analytical - 分析性问题（询问原因、影响等）
3. comparative - 比较性问题（比较不同事物）
4. procedural - 程序性问题（询问如何做某事）
5. creative - 创造性问题（需要创新思维）
6. multimodal - 多模态问题（涉及图片、文件等）

问题：{question}

请只返回类型名称（如：factual）
"""
            
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            type_str = response["content"].strip().lower()
            for q_type in QuestionType:
                if q_type.value == type_str:
                    return q_type
            
            return QuestionType.FACTUAL  # 默认类型
            
        except Exception as e:
            logger.warning(f"问题类型分析失败，使用默认类型: {e}")
            return QuestionType.FACTUAL
    
    async def _retrieve_relevant_information(self, context: QAContext):
        """检索相关信息"""
        try:
            # 根据问题类型选择搜索策略
            search_config = self._get_search_config_for_question_type(context.question_type)
            
            # 执行搜索
            results = await advanced_search_service.search(
                query=context.question,
                knowledge_base_id=context.knowledge_base_id,
                config=search_config
            )
            
            return results[:self.max_sources]
            
        except Exception as e:
            logger.error(f"信息检索失败: {e}")
            return []
    
    def _get_search_config_for_question_type(self, question_type: QuestionType) -> SearchConfig:
        """根据问题类型获取搜索配置"""
        if question_type == QuestionType.FACTUAL:
            return SearchConfig(
                search_type=SearchType.VECTOR,
                top_k=5,
                enable_rerank=True
            )
        elif question_type == QuestionType.ANALYTICAL:
            return SearchConfig(
                search_type=SearchType.HYBRID,
                top_k=8,
                vector_weight=0.6,
                graph_weight=0.4
            )
        elif question_type == QuestionType.COMPARATIVE:
            return SearchConfig(
                search_type=SearchType.SEMANTIC,
                top_k=10,
                enable_expansion=True
            )
        elif question_type == QuestionType.PROCEDURAL:
            return SearchConfig(
                search_type=SearchType.KEYWORD,
                top_k=6,
                enable_rerank=True
            )
        else:
            return SearchConfig(
                search_type=SearchType.HYBRID,
                top_k=8
            )
    
    async def _generate_answer(self, context: QAContext, sources) -> str:
        """生成答案"""
        try:
            # 构建上下文
            context_text = self._build_context_text(sources)
            
            # 构建提示词
            prompt = self._build_answer_prompt(context, context_text)
            
            # 生成答案
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response["content"]
            
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return "抱歉，我无法回答这个问题。"
    
    async def _generate_answer_stream(self, context: QAContext, sources) -> AsyncGenerator[str, None]:
        """流式生成答案"""
        try:
            # 构建上下文和提示词
            context_text = self._build_context_text(sources)
            prompt = self._build_answer_prompt(context, context_text)
            
            # 流式生成
            async for chunk in llm_service.chat_stream(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"流式答案生成失败: {e}")
            yield "抱歉，我无法回答这个问题。"
    
    def _build_context_text(self, sources) -> str:
        """构建上下文文本"""
        context_parts = []
        
        for i, source in enumerate(sources, 1):
            context_parts.append(f"[参考资料{i}]\n{source.content}\n")
        
        context_text = "\n".join(context_parts)
        
        # 限制长度
        if len(context_text) > self.max_context_length:
            context_text = context_text[:self.max_context_length] + "..."
        
        return context_text
    
    def _build_answer_prompt(self, context: QAContext, context_text: str) -> str:
        """构建答案提示词"""
        question_type_prompts = {
            QuestionType.FACTUAL: "请基于提供的参考资料，准确回答用户的问题。",
            QuestionType.ANALYTICAL: "请基于提供的参考资料，深入分析并回答用户的问题，包括原因、影响等。",
            QuestionType.COMPARATIVE: "请基于提供的参考资料，比较分析相关内容，指出异同点。",
            QuestionType.PROCEDURAL: "请基于提供的参考资料，详细说明操作步骤或流程。",
            QuestionType.CREATIVE: "请基于提供的参考资料，创造性地回答问题，提供建议或方案。",
            QuestionType.MULTIMODAL: "请基于提供的参考资料，综合分析多种信息形式。"
        }
        
        type_instruction = question_type_prompts.get(
            context.question_type, 
            "请基于提供的参考资料回答用户的问题。"
        )
        
        prompt = f"""
{type_instruction}

参考资料：
{context_text}

用户问题：{context.question}

回答要求：
1. 答案要准确、完整、有逻辑性
2. 优先使用参考资料中的信息
3. 如果参考资料不足，请明确说明
4. 保持客观中立的语调
5. 适当引用参考资料来源

请回答：
"""
        
        return prompt
    
    async def _evaluate_confidence(self, question: str, answer: str, sources) -> float:
        """评估答案置信度"""
        try:
            # 基于多个因素评估置信度
            factors = []
            
            # 1. 源文档数量和质量
            source_score = min(len(sources) / 5.0, 1.0)
            factors.append(source_score)
            
            # 2. 源文档相关性
            if sources:
                avg_relevance = sum(source.score for source in sources) / len(sources)
                factors.append(avg_relevance)
            
            # 3. 答案长度合理性
            answer_length_score = min(len(answer) / 200.0, 1.0)
            factors.append(answer_length_score)
            
            # 4. 使用LLM评估答案质量
            quality_score = await self._evaluate_answer_quality(question, answer)
            factors.append(quality_score)
            
            # 计算综合置信度
            confidence = sum(factors) / len(factors)
            return min(max(confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.warning(f"置信度评估失败: {e}")
            return 0.5
    
    async def _evaluate_answer_quality(self, question: str, answer: str) -> float:
        """使用LLM评估答案质量"""
        try:
            prompt = f"""
请评估以下答案对问题的回答质量，给出0-1之间的分数：

问题：{question}
答案：{answer}

评估标准：
- 答案是否直接回答了问题
- 答案是否准确和完整
- 答案是否逻辑清晰
- 答案是否有足够的细节

请只返回一个0-1之间的数字分数。
"""
            
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            
            score_str = response["content"].strip()
            score = float(score_str)
            return min(max(score, 0.0), 1.0)
            
        except Exception as e:
            logger.warning(f"答案质量评估失败: {e}")
            return 0.7
    
    async def _generate_reasoning(self, context: QAContext, sources, answer: str) -> str:
        """生成推理过程"""
        try:
            prompt = f"""
请解释回答以下问题的推理过程：

问题：{context.question}
答案：{answer}
参考资料数量：{len(sources)}

请简要说明：
1. 使用了哪些关键信息
2. 推理的逻辑过程
3. 为什么得出这个结论

推理过程：
"""
            
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300
            )
            
            return response["content"]
            
        except Exception as e:
            logger.warning(f"推理过程生成失败: {e}")
            return ""
    
    async def _generate_suggestions(self, context: QAContext, answer: str) -> List[str]:
        """生成建议"""
        try:
            prompt = f"""
基于以下问答，请提供3个有用的建议或后续行动：

问题：{context.question}
答案：{answer}

建议格式：每行一个建议，以"-"开头

建议：
"""
            
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=200
            )
            
            suggestions = []
            for line in response["content"].split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    suggestions.append(line[1:].strip())
            
            return suggestions[:3]
            
        except Exception as e:
            logger.warning(f"建议生成失败: {e}")
            return []
    
    async def _generate_related_questions(self, context: QAContext) -> List[str]:
        """生成相关问题"""
        try:
            prompt = f"""
基于用户的问题，请生成3个相关的问题：

原问题：{context.question}

相关问题格式：每行一个问题

相关问题：
"""
            
            response = await llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            
            questions = []
            for line in response["content"].split('\n'):
                line = line.strip()
                if line and line.endswith('?'):
                    questions.append(line)
            
            return questions[:3]
            
        except Exception as e:
            logger.warning(f"相关问题生成失败: {e}")
            return []


# 全局智能问答服务实例
intelligent_qa_service = IntelligentQAService()
