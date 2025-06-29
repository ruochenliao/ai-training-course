"""
增强版AutoGen多智能体服务
集成第二阶段开发的增强服务，实现完整的多智能体协作系统
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from autogen import ConversableAgent
from loguru import logger

from app import LLMService
from app import enhanced_graph_service
# 导入增强版服务
from app import enhanced_vector_db_service
from app import qwen_model_manager
from app.core import AgentException
from app.core import settings


class SearchMode(Enum):
    """检索模式枚举"""
    SEMANTIC = "semantic"
    GRAPH = "graph"
    HYBRID = "hybrid"
    AUTO = "auto"


class AgentRole(Enum):
    """智能体角色枚举"""
    COORDINATOR = "coordinator"
    SEMANTIC_SEARCHER = "semantic_searcher"
    GRAPH_SEARCHER = "graph_searcher"
    HYBRID_SEARCHER = "hybrid_searcher"
    ANSWER_GENERATOR = "answer_generator"
    QUALITY_ASSESSOR = "quality_assessor"


@dataclass
class SearchResult:
    """增强版检索结果"""
    content: str
    source: str
    score: float
    metadata: Dict[str, Any]
    search_type: str
    confidence: float = 0.0
    relevance_explanation: str = ""


@dataclass
class AgentTask:
    """智能体任务"""
    task_id: str
    query: str
    search_modes: List[SearchMode]
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    timeout: int = 300


@dataclass
class AgentResponse:
    """增强版智能体响应"""
    task_id: str
    content: str
    agent_name: str
    search_results: List[SearchResult]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, float] = field(default_factory=dict)


class EnhancedSemanticSearchAgent(ConversableAgent):
    """增强版语义检索智能体"""
    
    def __init__(self):
        super().__init__(
            name="enhanced_semantic_search_agent",
            system_message="""你是一个专业的语义检索智能体，使用最先进的向量检索技术。
            
            你的核心能力：
            1. 理解用户查询的语义意图
            2. 使用通义千问3-8B嵌入模型生成高质量查询向量
            3. 在Milvus向量数据库中执行高效的相似度搜索
            4. 支持混合检索（向量+关键词）
            5. 使用重排模型优化结果排序
            
            请始终关注检索结果的相关性和准确性。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.AUTOGEN_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )
        self.vector_service = enhanced_vector_db_service
        self.embedding_service = None
        self.stats = {"total_searches": 0, "avg_response_time": 0.0}
    
    async def initialize(self):
        """初始化智能体"""
        await self.vector_service.initialize()
        self.embedding_service = await qwen_model_manager.get_embedding_service()
        logger.info("语义检索智能体初始化完成")
    
    async def semantic_search(
        self, 
        query: str, 
        top_k: int = 10,
        knowledge_base_ids: Optional[List[int]] = None,
        use_rerank: bool = True
    ) -> List[SearchResult]:
        """执行语义检索"""
        start_time = time.time()
        
        try:
            # 生成查询向量
            query_vector = await self.embedding_service.embed_query(query)
            
            if use_rerank:
                # 使用重排的语义检索
                results = await self.vector_service.semantic_search_with_rerank(
                    collection_name=settings.MILVUS_COLLECTION_NAME,
                    query_vector=query_vector,
                    query_text=query,
                    top_k=top_k,
                    knowledge_base_ids=knowledge_base_ids
                )
            else:
                # 普通向量检索
                results = await self.vector_service._vector_search(
                    collection_name=settings.MILVUS_COLLECTION_NAME,
                    query_vectors=[query_vector],
                    top_k=top_k,
                    knowledge_base_ids=knowledge_base_ids,
                    search_config=None
                )
                results = results[0] if results else []
            
            # 转换为SearchResult格式
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    content=result.get("content", ""),
                    source=result.get("source", "语义检索"),
                    score=result.get("score", 0.0),
                    metadata=result.get("metadata", {}),
                    search_type="semantic",
                    confidence=result.get("score", 0.0),
                    relevance_explanation=f"语义相似度: {result.get('score', 0.0):.3f}"
                ))
            
            # 更新统计
            processing_time = time.time() - start_time
            self._update_stats(processing_time)
            
            logger.info(f"语义检索完成: {len(search_results)} 个结果, 耗时: {processing_time:.2f}s")
            return search_results
            
        except Exception as e:
            logger.error(f"语义检索失败: {e}")
            return []
    
    def _update_stats(self, processing_time: float):
        """更新统计信息"""
        self.stats["total_searches"] += 1
        total_time = self.stats["avg_response_time"] * (self.stats["total_searches"] - 1) + processing_time
        self.stats["avg_response_time"] = total_time / self.stats["total_searches"]


class EnhancedGraphSearchAgent(ConversableAgent):
    """增强版图谱检索智能体"""
    
    def __init__(self):
        super().__init__(
            name="enhanced_graph_search_agent",
            system_message="""你是一个专业的知识图谱检索智能体，擅长实体关系分析。
            
            你的核心能力：
            1. 从用户查询中识别关键实体
            2. 在Neo4j知识图谱中查找实体关系
            3. 执行多跳路径搜索
            4. 分析实体间的复杂关系网络
            5. 提供基于图谱结构的推理结果
            
            请关注实体关系的逻辑性和完整性。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.AUTOGEN_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )
        self.graph_service = enhanced_graph_service
        self.stats = {"total_searches": 0, "entities_found": 0}
    
    async def initialize(self):
        """初始化智能体"""
        await self.graph_service.initialize()
        logger.info("图谱检索智能体初始化完成")
    
    async def graph_search(
        self, 
        query: str, 
        max_depth: int = 3,
        max_results: int = 10,
        knowledge_base_ids: Optional[List[int]] = None
    ) -> List[SearchResult]:
        """执行图谱检索"""
        start_time = time.time()
        
        try:
            # 实体抽取
            entities = await self.graph_service.extract_entities(query)
            
            if not entities:
                logger.info("未找到相关实体")
                return []
            
            search_results = []
            
            for entity in entities[:5]:  # 限制实体数量
                # 获取实体邻居
                neighbors = await self.graph_service.get_entity_neighbors(
                    entity_name=entity,
                    max_depth=max_depth,
                    knowledge_base_ids=knowledge_base_ids
                )
                
                for neighbor in neighbors[:max_results//len(entities)]:
                    entity_info = neighbor.get("entity", {})
                    relationship = neighbor.get("relationship", {})
                    distance = neighbor.get("distance", 0)
                    
                    # 构建描述
                    description = f"实体: {entity_info.get('name', '')} (类型: {entity_info.get('type', '')})"
                    if relationship:
                        description += f"\n关系: {relationship.get('type', '')} (置信度: {relationship.get('confidence', 0.0):.2f})"
                    
                    search_results.append(SearchResult(
                        content=description,
                        source=f"知识图谱-{entity}",
                        score=1.0 / (distance + 1),  # 距离越近分数越高
                        metadata={
                            "entity": entity,
                            "neighbor": entity_info,
                            "relationship": relationship,
                            "distance": distance
                        },
                        search_type="graph",
                        confidence=relationship.get("confidence", 0.5),
                        relevance_explanation=f"图谱距离: {distance}, 关系类型: {relationship.get('type', 'unknown')}"
                    ))
            
            # 更新统计
            self.stats["total_searches"] += 1
            self.stats["entities_found"] += len(entities)
            
            processing_time = time.time() - start_time
            logger.info(f"图谱检索完成: {len(search_results)} 个结果, 耗时: {processing_time:.2f}s")
            
            return search_results
            
        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            return []


class EnhancedHybridSearchAgent(ConversableAgent):
    """增强版混合检索智能体"""
    
    def __init__(self):
        super().__init__(
            name="enhanced_hybrid_search_agent",
            system_message="""你是一个专业的混合检索智能体，融合多种检索技术。
            
            你的核心能力：
            1. 同时执行语义检索和图谱检索
            2. 智能融合不同检索结果
            3. 使用重排模型优化结果排序
            4. 根据查询特点调整检索权重
            5. 提供最优的综合检索结果
            
            请确保检索结果的多样性和互补性。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.AUTOGEN_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )
        self.vector_service = enhanced_vector_db_service
        self.graph_service = enhanced_graph_service
        self.embedding_service = None
        self.reranker_service = None
    
    async def initialize(self):
        """初始化智能体"""
        await self.vector_service.initialize()
        await self.graph_service.initialize()
        self.embedding_service = await qwen_model_manager.get_embedding_service()
        self.reranker_service = await qwen_model_manager.get_reranker_service()
        logger.info("混合检索智能体初始化完成")
    
    async def hybrid_search(
        self, 
        query: str, 
        top_k: int = 10,
        vector_weight: float = 0.7,
        graph_weight: float = 0.3,
        knowledge_base_ids: Optional[List[int]] = None
    ) -> List[SearchResult]:
        """执行混合检索"""
        start_time = time.time()
        
        try:
            # 生成查询向量
            query_vector = await self.embedding_service.embed_query(query)
            
            # 执行混合检索
            hybrid_result = await self.vector_service.hybrid_search(
                collection_name=settings.MILVUS_COLLECTION_NAME,
                query_vector=query_vector,
                query_text=query,
                top_k=top_k,
                vector_weight=vector_weight,
                keyword_weight=1.0 - vector_weight,
                knowledge_base_ids=knowledge_base_ids
            )
            
            # 转换结果格式
            search_results = []
            for result in hybrid_result.combined_results:
                search_types = result.get('search_types', ['hybrid'])
                
                search_results.append(SearchResult(
                    content=result.get("content", ""),
                    source=result.get("source", "混合检索"),
                    score=result.get("combined_score", 0.0),
                    metadata={
                        **result.get("metadata", {}),
                        "vector_score": result.get("vector_score", 0.0),
                        "keyword_score": result.get("keyword_score", 0.0),
                        "search_types": search_types
                    },
                    search_type="hybrid",
                    confidence=result.get("combined_score", 0.0),
                    relevance_explanation=f"混合评分: {result.get('combined_score', 0.0):.3f} (向量: {result.get('vector_score', 0.0):.3f}, 关键词: {result.get('keyword_score', 0.0):.3f})"
                ))
            
            processing_time = time.time() - start_time
            logger.info(f"混合检索完成: {len(search_results)} 个结果, 耗时: {processing_time:.2f}s")
            
            return search_results
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []


class EnhancedAnswerGenerationAgent(ConversableAgent):
    """增强版答案生成智能体"""
    
    def __init__(self):
        super().__init__(
            name="enhanced_answer_generation_agent",
            system_message="""你是一个专业的答案生成智能体，擅长综合分析和内容生成。
            
            你的核心能力：
            1. 分析多源检索结果的相关性和可信度
            2. 综合不同类型的信息源
            3. 生成准确、完整、有条理的答案
            4. 标注信息来源和置信度
            5. 识别信息不足的情况并给出建议
            
            请确保答案的准确性、完整性和可读性。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.LLM_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )
        self.llm_service = LLMService()
        self.stats = {"total_generations": 0, "avg_confidence": 0.0}
    
    async def generate_answer(
        self, 
        query: str, 
        search_results: List[SearchResult],
        include_sources: bool = True,
        max_sources: int = None
    ) -> Tuple[str, float]:
        """生成答案"""
        start_time = time.time()
        
        try:
            if not search_results:
                return "抱歉，没有找到相关信息来回答您的问题。", 0.0
            
            max_sources = max_sources or settings.QA_MAX_SOURCES
            top_results = search_results[:max_sources]
            
            # 构建上下文
            context_parts = []
            source_info = []
            
            for i, result in enumerate(top_results):
                context_parts.append(
                    f"信息源{i+1} (来源: {result.source}, 相关度: {result.score:.3f}, 类型: {result.search_type}):\n"
                    f"{result.content}\n"
                )
                
                source_info.append({
                    "index": i+1,
                    "source": result.source,
                    "score": result.score,
                    "type": result.search_type
                })
            
            context = "\n".join(context_parts)
            
            # 构建提示词
            prompt = f"""基于以下检索到的信息，请回答用户的问题。

用户问题: {query}

相关信息:
{context}

请根据上述信息生成一个准确、完整、有条理的答案。要求：
1. 综合分析所有相关信息
2. 按重要性和逻辑顺序组织答案
3. 如果信息不足，请明确指出
4. 保持客观和准确
5. 使用清晰易懂的语言

答案:"""
            
            # 生成答案
            response = await self.llm_service.generate_response(
                prompt=prompt,
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE
            )
            
            answer = response.get("content", "抱歉，无法生成答案。")
            
            # 计算置信度
            confidence = self._calculate_answer_confidence(top_results, answer)
            
            # 添加来源信息
            if include_sources and source_info:
                sources_text = "\n\n参考来源:\n"
                for source in source_info:
                    sources_text += f"- {source['source']} (相关度: {source['score']:.3f})\n"
                answer += sources_text
            
            # 更新统计
            self.stats["total_generations"] += 1
            total_confidence = self.stats["avg_confidence"] * (self.stats["total_generations"] - 1) + confidence
            self.stats["avg_confidence"] = total_confidence / self.stats["total_generations"]
            
            processing_time = time.time() - start_time
            logger.info(f"答案生成完成, 置信度: {confidence:.3f}, 耗时: {processing_time:.2f}s")
            
            return answer, confidence
            
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return "抱歉，答案生成过程中出现错误。", 0.0
    
    def _calculate_answer_confidence(self, results: List[SearchResult], answer: str) -> float:
        """计算答案置信度"""
        if not results:
            return 0.0
        
        # 基于检索结果质量
        avg_score = sum(r.score for r in results) / len(results)
        max_score = max(r.score for r in results)
        
        # 基于结果数量
        result_count_factor = min(len(results) / 5, 1.0)  # 5个结果为满分
        
        # 基于答案长度（合理长度加分）
        answer_length = len(answer)
        length_factor = 1.0
        if 100 <= answer_length <= 1000:
            length_factor = 1.0
        elif answer_length < 100:
            length_factor = 0.8
        else:
            length_factor = 0.9
        
        # 综合计算
        confidence = (avg_score * 0.4 + max_score * 0.3 + result_count_factor * 0.2 + length_factor * 0.1)
        
        return min(confidence, 1.0)


class QualityAssessmentAgent(ConversableAgent):
    """质量评估智能体"""

    def __init__(self):
        super().__init__(
            name="quality_assessment_agent",
            system_message="""你是一个专业的质量评估智能体，负责评估检索结果和答案质量。

            你的核心能力：
            1. 评估检索结果的相关性和准确性
            2. 分析答案的完整性和逻辑性
            3. 检测信息的一致性和可信度
            4. 识别潜在的错误或偏差
            5. 提供质量改进建议

            请提供客观、准确的质量评估。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.AUTOGEN_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )

    async def assess_search_quality(self, query: str, results: List[SearchResult]) -> Dict[str, float]:
        """评估检索质量"""
        try:
            if not results:
                return {
                    "relevance": 0.0,
                    "diversity": 0.0,
                    "coverage": 0.0,
                    "confidence": 0.0,
                    "overall": 0.0
                }

            # 相关性评估
            relevance = sum(r.score for r in results) / len(results)

            # 多样性评估（基于来源类型）
            source_types = set(r.search_type for r in results)
            diversity = len(source_types) / 3.0  # 假设最多3种类型

            # 覆盖度评估（基于结果数量）
            coverage = min(len(results) / 10.0, 1.0)  # 10个结果为满分

            # 置信度评估
            confidence = sum(r.confidence for r in results) / len(results)

            # 综合评分
            overall = (relevance * 0.4 + diversity * 0.2 + coverage * 0.2 + confidence * 0.2)

            return {
                "relevance": relevance,
                "diversity": diversity,
                "coverage": coverage,
                "confidence": confidence,
                "overall": overall
            }

        except Exception as e:
            logger.error(f"检索质量评估失败: {e}")
            return {"overall": 0.0}

    async def assess_answer_quality(self, query: str, answer: str, sources: List[SearchResult]) -> Dict[str, float]:
        """评估答案质量"""
        try:
            # 完整性评估
            completeness = self._assess_completeness(query, answer)

            # 准确性评估
            accuracy = self._assess_accuracy(answer, sources)

            # 清晰度评估
            clarity = self._assess_clarity(answer)

            # 一致性评估
            consistency = self._assess_consistency(answer, sources)

            # 综合评分
            overall = (completeness * 0.3 + accuracy * 0.3 + clarity * 0.2 + consistency * 0.2)

            return {
                "completeness": completeness,
                "accuracy": accuracy,
                "clarity": clarity,
                "consistency": consistency,
                "overall": overall
            }

        except Exception as e:
            logger.error(f"答案质量评估失败: {e}")
            return {"overall": 0.0}

    def _assess_completeness(self, query: str, answer: str) -> float:
        """评估答案完整性"""
        # 简化实现：基于答案长度和关键词覆盖
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())

        keyword_coverage = len(query_words & answer_words) / len(query_words) if query_words else 0

        # 答案长度评估
        length_score = 1.0
        if len(answer) < 50:
            length_score = 0.5
        elif len(answer) > 2000:
            length_score = 0.8

        return (keyword_coverage * 0.6 + length_score * 0.4)

    def _assess_accuracy(self, answer: str, sources: List[SearchResult]) -> float:
        """评估答案准确性"""
        if not sources:
            return 0.5

        # 基于来源质量评估准确性
        avg_source_score = sum(s.score for s in sources) / len(sources)
        return min(avg_source_score * 1.2, 1.0)

    def _assess_clarity(self, answer: str) -> float:
        """评估答案清晰度"""
        # 基于句子结构和长度
        sentences = answer.split('。')
        if not sentences:
            return 0.0

        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # 理想句长为10-20词
        if 10 <= avg_sentence_length <= 20:
            return 1.0
        elif 5 <= avg_sentence_length <= 30:
            return 0.8
        else:
            return 0.6

    def _assess_consistency(self, answer: str, sources: List[SearchResult]) -> float:
        """评估答案一致性"""
        # 简化实现：检查答案是否与来源信息一致
        if not sources:
            return 0.5

        # 基于来源置信度评估一致性
        avg_confidence = sum(s.confidence for s in sources) / len(sources)
        return avg_confidence


class EnhancedCoordinatorAgent(ConversableAgent):
    """增强版协调智能体"""

    def __init__(self):
        super().__init__(
            name="enhanced_coordinator_agent",
            system_message="""你是智能体系统的协调员，负责任务分发和结果整合。

            你的核心职责：
            1. 分析用户查询特点，选择最适合的检索策略
            2. 协调多个专业智能体的工作
            3. 整合不同智能体的结果
            4. 监控任务执行状态和质量
            5. 优化整体系统性能

            请确保任务分配的合理性和结果整合的有效性。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.AUTOGEN_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )
        self.task_history = []
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "avg_response_time": 0.0,
            "avg_quality_score": 0.0
        }

    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """分析查询特点"""
        try:
            analysis = {
                "query_type": "general",
                "complexity": "medium",
                "recommended_modes": [SearchMode.SEMANTIC],
                "estimated_time": 30,
                "priority": 1
            }

            query_lower = query.lower()

            # 查询类型分析
            if any(word in query_lower for word in ["关系", "连接", "相关", "影响"]):
                analysis["query_type"] = "relational"
                analysis["recommended_modes"] = [SearchMode.GRAPH, SearchMode.HYBRID]
            elif any(word in query_lower for word in ["定义", "是什么", "概念"]):
                analysis["query_type"] = "definitional"
                analysis["recommended_modes"] = [SearchMode.SEMANTIC]
            elif any(word in query_lower for word in ["比较", "区别", "差异"]):
                analysis["query_type"] = "comparative"
                analysis["recommended_modes"] = [SearchMode.HYBRID]
            elif any(word in query_lower for word in ["步骤", "如何", "方法"]):
                analysis["query_type"] = "procedural"
                analysis["recommended_modes"] = [SearchMode.SEMANTIC, SearchMode.GRAPH]

            # 复杂度分析
            word_count = len(query.split())
            if word_count > 20:
                analysis["complexity"] = "high"
                analysis["estimated_time"] = 60
            elif word_count < 5:
                analysis["complexity"] = "low"
                analysis["estimated_time"] = 15

            # 优先级分析
            if any(word in query_lower for word in ["紧急", "重要", "立即"]):
                analysis["priority"] = 3

            return analysis

        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            return {
                "query_type": "general",
                "recommended_modes": [SearchMode.SEMANTIC],
                "estimated_time": 30
            }

    async def create_task(self, query: str, search_modes: Optional[List[SearchMode]] = None) -> AgentTask:
        """创建智能体任务"""
        analysis = await self.analyze_query(query)

        if search_modes is None:
            search_modes = analysis.get("recommended_modes", [SearchMode.SEMANTIC])

        task = AgentTask(
            task_id=f"task_{int(time.time())}_{len(self.task_history)}",
            query=query,
            search_modes=search_modes,
            parameters={
                "top_k": 10,
                "max_depth": 3,
                "use_rerank": True
            },
            priority=analysis.get("priority", 1),
            timeout=analysis.get("estimated_time", 30) * 2  # 预留缓冲时间
        )

        self.task_history.append(task)
        return task

    def update_performance_metrics(self, task_success: bool, response_time: float, quality_score: float):
        """更新性能指标"""
        self.performance_metrics["total_tasks"] += 1

        if task_success:
            self.performance_metrics["successful_tasks"] += 1

        # 更新平均响应时间
        total_time = (self.performance_metrics["avg_response_time"] *
                     (self.performance_metrics["total_tasks"] - 1) + response_time)
        self.performance_metrics["avg_response_time"] = total_time / self.performance_metrics["total_tasks"]

        # 更新平均质量分数
        total_quality = (self.performance_metrics["avg_quality_score"] *
                        (self.performance_metrics["total_tasks"] - 1) + quality_score)
        self.performance_metrics["avg_quality_score"] = total_quality / self.performance_metrics["total_tasks"]

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        success_rate = (self.performance_metrics["successful_tasks"] /
                       max(self.performance_metrics["total_tasks"], 1))

        return {
            **self.performance_metrics,
            "success_rate": success_rate,
            "recent_tasks": len([t for t in self.task_history[-10:]])  # 最近10个任务
        }


class EnhancedAutoGenService:
    """增强版AutoGen多智能体服务主类"""

    def __init__(self):
        # 初始化所有智能体
        self.semantic_agent = EnhancedSemanticSearchAgent()
        self.graph_agent = EnhancedGraphSearchAgent()
        self.hybrid_agent = EnhancedHybridSearchAgent()
        self.answer_agent = EnhancedAnswerGenerationAgent()
        self.quality_agent = QualityAssessmentAgent()
        self.coordinator = EnhancedCoordinatorAgent()

        # 服务状态
        self.initialized = False
        self.agents = {
            AgentRole.SEMANTIC_SEARCHER: self.semantic_agent,
            AgentRole.GRAPH_SEARCHER: self.graph_agent,
            AgentRole.HYBRID_SEARCHER: self.hybrid_agent,
            AgentRole.ANSWER_GENERATOR: self.answer_agent,
            AgentRole.QUALITY_ASSESSOR: self.quality_agent,
            AgentRole.COORDINATOR: self.coordinator
        }

        # 统计信息
        self.service_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "avg_processing_time": 0.0,
            "avg_quality_score": 0.0
        }

        logger.info("增强版AutoGen服务初始化完成")

    async def initialize(self):
        """初始化所有智能体"""
        if self.initialized:
            return

        try:
            # 并行初始化所有智能体
            await asyncio.gather(
                self.semantic_agent.initialize(),
                self.graph_agent.initialize(),
                self.hybrid_agent.initialize(),
                return_exceptions=True
            )

            self.initialized = True
            logger.info("所有智能体初始化完成")

        except Exception as e:
            logger.error(f"智能体初始化失败: {e}")
            raise AgentException(f"智能体初始化失败: {e}")

    async def process_query(
        self,
        query: str,
        search_modes: Optional[List[str]] = None,
        top_k: int = 10,
        knowledge_base_ids: Optional[List[int]] = None,
        include_quality_assessment: bool = True
    ) -> AgentResponse:
        """处理用户查询"""
        start_time = time.time()

        try:
            # 确保服务已初始化
            if not self.initialized:
                await self.initialize()

            # 转换搜索模式
            if search_modes:
                modes = [SearchMode(mode) for mode in search_modes if mode in [m.value for m in SearchMode]]
            else:
                modes = None

            # 创建任务
            task = await self.coordinator.create_task(query, modes)

            # 执行多智能体检索
            all_results = await self._execute_multi_agent_search(
                task, top_k, knowledge_base_ids
            )

            # 去重和排序
            unique_results = self._deduplicate_results(all_results)
            top_results = sorted(unique_results, key=lambda x: x.score, reverse=True)[:top_k]

            # 生成答案
            answer, answer_confidence = await self.answer_agent.generate_answer(
                query, top_results, include_sources=True, max_sources=settings.QA_MAX_SOURCES
            )

            # 质量评估
            quality_metrics = {}
            if include_quality_assessment:
                search_quality = await self.quality_agent.assess_search_quality(query, top_results)
                answer_quality = await self.quality_agent.assess_answer_quality(query, answer, top_results)
                quality_metrics = {
                    "search_quality": search_quality,
                    "answer_quality": answer_quality,
                    "overall_quality": (search_quality.get("overall", 0.0) + answer_quality.get("overall", 0.0)) / 2
                }

            # 计算处理时间
            processing_time = time.time() - start_time

            # 创建响应
            response = AgentResponse(
                task_id=task.task_id,
                content=answer,
                agent_name="enhanced_autogen_multi_agent",
                search_results=top_results,
                confidence=answer_confidence,
                processing_time=processing_time,
                metadata={
                    "query_analysis": await self.coordinator.analyze_query(query),
                    "search_modes_used": [mode.value for mode in task.search_modes],
                    "total_results_found": len(all_results),
                    "knowledge_base_ids": knowledge_base_ids
                },
                quality_metrics=quality_metrics
            )

            # 更新统计信息
            self._update_service_stats(True, processing_time, quality_metrics.get("overall_quality", 0.0))
            self.coordinator.update_performance_metrics(
                True, processing_time, quality_metrics.get("overall_quality", 0.0)
            )

            logger.info(f"查询处理完成: {task.task_id}, 耗时: {processing_time:.2f}s, 置信度: {answer_confidence:.3f}")

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            self._update_service_stats(False, processing_time, 0.0)

            logger.error(f"查询处理失败: {e}")

            return AgentResponse(
                task_id=f"error_{int(time.time())}",
                content=f"抱歉，查询处理过程中出现错误: {str(e)}",
                agent_name="enhanced_autogen_multi_agent",
                search_results=[],
                confidence=0.0,
                processing_time=processing_time,
                metadata={"error": str(e)},
                quality_metrics={}
            )

    async def _execute_multi_agent_search(
        self,
        task: AgentTask,
        top_k: int,
        knowledge_base_ids: Optional[List[int]]
    ) -> List[SearchResult]:
        """执行多智能体检索"""
        all_results = []
        search_tasks = []

        # 根据任务配置执行不同的检索
        for mode in task.search_modes:
            if mode == SearchMode.SEMANTIC:
                search_tasks.append(
                    self.semantic_agent.semantic_search(
                        task.query, top_k, knowledge_base_ids,
                        task.parameters.get("use_rerank", True)
                    )
                )
            elif mode == SearchMode.GRAPH:
                search_tasks.append(
                    self.graph_agent.graph_search(
                        task.query, task.parameters.get("max_depth", 3),
                        top_k, knowledge_base_ids
                    )
                )
            elif mode == SearchMode.HYBRID:
                search_tasks.append(
                    self.hybrid_agent.hybrid_search(
                        task.query, top_k,
                        task.parameters.get("vector_weight", 0.7),
                        task.parameters.get("graph_weight", 0.3),
                        knowledge_base_ids
                    )
                )
            elif mode == SearchMode.AUTO:
                # 自动模式：根据查询特点选择最佳策略
                query_analysis = await self.coordinator.analyze_query(task.query)
                recommended_modes = query_analysis.get("recommended_modes", [SearchMode.SEMANTIC])

                for rec_mode in recommended_modes:
                    if rec_mode == SearchMode.SEMANTIC:
                        search_tasks.append(
                            self.semantic_agent.semantic_search(task.query, top_k, knowledge_base_ids)
                        )
                    elif rec_mode == SearchMode.GRAPH:
                        search_tasks.append(
                            self.graph_agent.graph_search(task.query, 3, top_k, knowledge_base_ids)
                        )
                    elif rec_mode == SearchMode.HYBRID:
                        search_tasks.append(
                            self.hybrid_agent.hybrid_search(task.query, top_k, 0.7, 0.3, knowledge_base_ids)
                        )

        # 并行执行所有检索任务
        if search_tasks:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"检索任务失败: {result}")

        return all_results

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重检索结果"""
        seen_content = set()
        unique_results = []

        for result in results:
            # 使用内容的前200字符作为去重标识
            content_hash = hash(result.content[:200])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)

        return unique_results

    def _update_service_stats(self, success: bool, processing_time: float, quality_score: float):
        """更新服务统计信息"""
        self.service_stats["total_queries"] += 1

        if success:
            self.service_stats["successful_queries"] += 1

        # 更新平均处理时间
        total_time = (self.service_stats["avg_processing_time"] *
                     (self.service_stats["total_queries"] - 1) + processing_time)
        self.service_stats["avg_processing_time"] = total_time / self.service_stats["total_queries"]

        # 更新平均质量分数
        if quality_score > 0:
            total_quality = (self.service_stats["avg_quality_score"] *
                           (self.service_stats["total_queries"] - 1) + quality_score)
            self.service_stats["avg_quality_score"] = total_quality / self.service_stats["total_queries"]

    async def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        status = {
            "service_initialized": self.initialized,
            "agents_status": {},
            "service_stats": self.service_stats,
            "coordinator_performance": self.coordinator.get_performance_report()
        }

        # 获取各智能体的统计信息
        if hasattr(self.semantic_agent, 'stats'):
            status["agents_status"]["semantic_agent"] = self.semantic_agent.stats

        if hasattr(self.graph_agent, 'stats'):
            status["agents_status"]["graph_agent"] = self.graph_agent.stats

        if hasattr(self.answer_agent, 'stats'):
            status["agents_status"]["answer_agent"] = self.answer_agent.stats

        return status

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "issues": [],
            "recommendations": []
        }

        try:
            # 检查初始化状态
            if not self.initialized:
                health_status["issues"].append("服务未初始化")
                health_status["recommendations"].append("调用initialize()方法")
                health_status["status"] = "unhealthy"

            # 检查成功率
            success_rate = (self.service_stats["successful_queries"] /
                           max(self.service_stats["total_queries"], 1))

            if success_rate < 0.8:
                health_status["issues"].append(f"成功率较低: {success_rate:.2%}")
                health_status["recommendations"].append("检查模型和数据库连接")
                health_status["status"] = "warning"

            # 检查平均响应时间
            if self.service_stats["avg_processing_time"] > 30:
                health_status["issues"].append(f"响应时间较长: {self.service_stats['avg_processing_time']:.2f}s")
                health_status["recommendations"].append("优化检索参数或增加资源")
                health_status["status"] = "warning"

            # 检查质量分数
            if self.service_stats["avg_quality_score"] < 0.7:
                health_status["issues"].append(f"质量分数较低: {self.service_stats['avg_quality_score']:.3f}")
                health_status["recommendations"].append("检查知识库质量和模型配置")
                health_status["status"] = "warning"

        except Exception as e:
            health_status["status"] = "error"
            health_status["issues"].append(f"健康检查失败: {str(e)}")

        return health_status

    async def optimize_performance(self) -> Dict[str, Any]:
        """性能优化建议"""
        optimization_report = {
            "current_performance": self.service_stats,
            "optimization_suggestions": [],
            "estimated_improvements": {}
        }

        try:
            # 分析处理时间
            avg_time = self.service_stats["avg_processing_time"]
            if avg_time > 20:
                optimization_report["optimization_suggestions"].append({
                    "area": "响应时间",
                    "suggestion": "减少top_k参数或启用结果缓存",
                    "expected_improvement": "20-30%"
                })

            # 分析成功率
            success_rate = (self.service_stats["successful_queries"] /
                           max(self.service_stats["total_queries"], 1))
            if success_rate < 0.9:
                optimization_report["optimization_suggestions"].append({
                    "area": "成功率",
                    "suggestion": "检查模型配置和错误处理机制",
                    "expected_improvement": "10-15%"
                })

            # 分析质量分数
            if self.service_stats["avg_quality_score"] < 0.8:
                optimization_report["optimization_suggestions"].append({
                    "area": "答案质量",
                    "suggestion": "优化提示词模板和重排模型参数",
                    "expected_improvement": "15-25%"
                })

        except Exception as e:
            optimization_report["error"] = str(e)

        return optimization_report

    async def reset_stats(self):
        """重置统计信息"""
        self.service_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "avg_processing_time": 0.0,
            "avg_quality_score": 0.0
        }

        # 重置智能体统计
        for agent in [self.semantic_agent, self.graph_agent, self.answer_agent]:
            if hasattr(agent, 'stats'):
                if hasattr(agent.stats, 'clear'):
                    agent.stats.clear()
                else:
                    for key in agent.stats:
                        if isinstance(agent.stats[key], (int, float)):
                            agent.stats[key] = 0

        # 重置协调器统计
        self.coordinator.task_history.clear()
        self.coordinator.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "avg_response_time": 0.0,
            "avg_quality_score": 0.0
        }

        logger.info("统计信息已重置")


# 全局增强版AutoGen服务实例
enhanced_autogen_service = EnhancedAutoGenService()
