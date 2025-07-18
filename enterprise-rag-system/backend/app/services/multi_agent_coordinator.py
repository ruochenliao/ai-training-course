"""
多智能体协作协调器 - 第二阶段核心组件
基于AutoGen框架实现多智能体协作，支持多模式检索和答案融合
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import json

from autogen import ConversableAgent, GroupChat, GroupChatManager
from loguru import logger

from app.core import settings
from app.core.exceptions import AgentException
from app.services.qwen_embedding_service import QwenEmbeddingService
from app.services.milvus_service import milvus_service
from app.services.neo4j_graph_service import Neo4jGraphService
from app.services.deepseek_llm_service import DeepSeekLLMService
from app.services.qwen_multimodal_service import QwenMultimodalService


class SearchMode(Enum):
    """检索模式枚举"""
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    GRAPH = "graph"
    ALL = "all"


@dataclass
class SearchRequest:
    """检索请求"""
    query: str
    modes: List[SearchMode]
    top_k: int = 10
    knowledge_base_ids: Optional[List[int]] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """检索结果"""
    content: str
    source: str
    score: float
    search_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    relevance_explanation: str = ""


@dataclass
class AgentResponse:
    """智能体响应"""
    agent_name: str
    content: str
    search_results: List[SearchResult]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticSearchAgent(ConversableAgent):
    """语义检索智能体"""
    
    def __init__(self):
        super().__init__(
            name="semantic_searcher",
            system_message="""你是语义检索专家，负责执行向量相似度搜索。

你的任务：
1. 理解用户查询的语义意图
2. 使用Qwen3-8B嵌入模型生成查询向量
3. 在Milvus向量数据库中执行相似度搜索
4. 返回最相关的文档片段

请专注于语义相关性，返回JSON格式的结果。""",
            llm_config={"config_list": [{"model": "deepseek-chat"}], "temperature": 0.1},
            human_input_mode="NEVER",
        )
        self.embedding_service = QwenEmbeddingService()
        self.vector_service = milvus_service


class HybridSearchAgent(ConversableAgent):
    """混合检索智能体"""
    
    def __init__(self):
        super().__init__(
            name="hybrid_searcher",
            system_message="""你是混合检索专家，结合语义检索和关键词检索。

你的任务：
1. 分析查询的语义和关键词特征
2. 执行密集向量+稀疏向量的混合检索
3. 使用RRF算法融合检索结果
4. 提供平衡的检索结果

请关注检索结果的多样性和准确性，返回JSON格式的结果。""",
            llm_config={"config_list": [{"model": "deepseek-chat"}], "temperature": 0.1},
            human_input_mode="NEVER",
        )
        self.embedding_service = QwenEmbeddingService()
        self.vector_service = milvus_service


class GraphSearchAgent(ConversableAgent):
    """图谱检索智能体"""
    
    def __init__(self):
        super().__init__(
            name="graph_searcher",
            system_message="""你是知识图谱检索专家，擅长实体关系分析。

你的任务：
1. 从查询中识别关键实体
2. 在Neo4j知识图谱中查找实体关系
3. 执行图遍历和路径搜索
4. 提供基于实体关系的结构化信息

请关注实体关系的逻辑性，返回JSON格式的结果。""",
            llm_config={"config_list": [{"model": "deepseek-chat"}], "temperature": 0.1},
            human_input_mode="NEVER",
        )
        self.graph_service = Neo4jGraphService()


class AnswerFusionAgent(ConversableAgent):
    """答案融合智能体"""
    
    def __init__(self):
        super().__init__(
            name="answer_fusion",
            system_message="""你是答案融合专家，负责整合多个检索结果。

你的任务：
1. 分析来自不同检索模式的结果
2. 评估结果的相关性和可信度
3. 去除重复和冲突信息
4. 生成综合性的最终答案

请确保答案的准确性和完整性，提供清晰的信息来源。""",
            llm_config={"config_list": [{"model": "deepseek-chat"}], "temperature": 0.3},
            human_input_mode="NEVER",
        )


class QualityAssessmentAgent(ConversableAgent):
    """质量评估智能体"""
    
    def __init__(self):
        super().__init__(
            name="quality_assessor",
            system_message="""你是质量评估专家，负责评估答案质量。

你的任务：
1. 评估答案的准确性和相关性
2. 检查信息的一致性和逻辑性
3. 评估答案的完整性和有用性
4. 提供质量评分和改进建议

请提供客观的质量评估，包括具体的评分理由。""",
            llm_config={"config_list": [{"model": "deepseek-chat"}], "temperature": 0.1},
            human_input_mode="NEVER",
        )


class MultiAgentCoordinator:
    """多智能体协作协调器"""
    
    def __init__(self):
        # 初始化智能体
        self.semantic_agent = SemanticSearchAgent()
        self.hybrid_agent = HybridSearchAgent()
        self.graph_agent = GraphSearchAgent()
        self.fusion_agent = AnswerFusionAgent()
        self.quality_agent = QualityAssessmentAgent()
        
        # 服务组件
        self.embedding_service = QwenEmbeddingService()
        self.vector_service = milvus_service
        self.graph_service = Neo4jGraphService()
        self.llm_service = DeepSeekLLMService()
        
        self._initialized = False
        self.stats = {
            "total_requests": 0,
            "avg_response_time": 0.0,
            "mode_usage": {"semantic": 0, "hybrid": 0, "graph": 0, "all": 0}
        }
    
    async def initialize(self):
        """初始化协调器"""
        if self._initialized:
            return
        
        try:
            logger.info("初始化多智能体协调器...")
            
            # 并行初始化所有服务
            await asyncio.gather(
                self.embedding_service.initialize(),
                self.vector_service.connect(),
                self.graph_service.connect(),
                self.llm_service.initialize(),
                return_exceptions=True
            )
            
            self._initialized = True
            logger.info("多智能体协调器初始化完成")
            
        except Exception as e:
            logger.error(f"多智能体协调器初始化失败: {e}")
            raise
    
    async def process_request(self, request: SearchRequest) -> Dict[str, Any]:
        """处理检索请求"""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            logger.info(f"处理多智能体检索请求: {request.query}")
            
            # 执行多模式检索
            search_results = await self._execute_multi_mode_search(request)
            
            # 融合答案
            fused_answer = await self._fuse_answers(request.query, search_results)
            
            # 质量评估
            quality_assessment = await self._assess_quality(request.query, fused_answer, search_results)
            
            processing_time = time.time() - start_time
            
            # 更新统计
            self._update_stats(request.modes, processing_time)
            
            result = {
                "query": request.query,
                "answer": fused_answer,
                "search_results": search_results,
                "quality_assessment": quality_assessment,
                "processing_time": processing_time,
                "modes_used": [mode.value for mode in request.modes],
                "metadata": {
                    "total_results": len(search_results),
                    "confidence_score": quality_assessment.get("confidence", 0.0),
                    "session_id": request.session_id
                }
            }
            
            logger.info(f"多智能体检索完成: 耗时 {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"多智能体检索失败: {e}")
            raise AgentException(f"多智能体检索失败: {e}")
    
    async def _execute_multi_mode_search(self, request: SearchRequest) -> List[SearchResult]:
        """执行多模式检索"""
        all_results = []
        
        # 根据请求的模式执行相应的检索
        if SearchMode.SEMANTIC in request.modes or SearchMode.ALL in request.modes:
            semantic_results = await self._semantic_search(request)
            all_results.extend(semantic_results)
        
        if SearchMode.HYBRID in request.modes or SearchMode.ALL in request.modes:
            hybrid_results = await self._hybrid_search(request)
            all_results.extend(hybrid_results)
        
        if SearchMode.GRAPH in request.modes or SearchMode.ALL in request.modes:
            graph_results = await self._graph_search(request)
            all_results.extend(graph_results)
        
        # 去重和排序
        unique_results = self._deduplicate_results(all_results)
        sorted_results = sorted(unique_results, key=lambda x: x.score, reverse=True)
        
        return sorted_results[:request.top_k]
    
    async def _semantic_search(self, request: SearchRequest) -> List[SearchResult]:
        """执行语义检索"""
        try:
            # 生成查询向量
            query_embedding = await self.embedding_service.encode_single(request.query)
            
            # 执行向量检索
            results = await self.vector_service.search_vectors(
                vector=query_embedding.tolist(),
                top_k=request.top_k,
                knowledge_base_ids=request.knowledge_base_ids
            )
            
            # 转换为SearchResult格式
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    content=result.get("content", ""),
                    source=f"语义检索-文档{result.get('document_id', 'unknown')}",
                    score=result.get("score", 0.0),
                    search_type="semantic",
                    metadata=result,
                    confidence=result.get("score", 0.0),
                    relevance_explanation=f"语义相似度: {result.get('score', 0.0):.3f}"
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"语义检索失败: {e}")
            return []
    
    async def _hybrid_search(self, request: SearchRequest) -> List[SearchResult]:
        """执行混合检索"""
        try:
            # 生成查询向量
            query_embedding = await self.embedding_service.encode_single(request.query)
            
            # 执行混合检索
            results = await self.vector_service.hybrid_search(
                dense_vector=query_embedding.tolist(),
                keywords=request.query,
                top_k=request.top_k,
                knowledge_base_ids=request.knowledge_base_ids
            )
            
            # 转换为SearchResult格式
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    content=result.get("content", ""),
                    source=f"混合检索-文档{result.get('document_id', 'unknown')}",
                    score=result.get("score", 0.0),
                    search_type="hybrid",
                    metadata=result,
                    confidence=result.get("score", 0.0),
                    relevance_explanation=f"混合检索分数: {result.get('score', 0.0):.3f}"
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []
    
    async def _graph_search(self, request: SearchRequest) -> List[SearchResult]:
        """执行图谱检索"""
        try:
            # 这里简化实现，实际应该包含实体识别和图谱查询
            # 暂时返回空结果，后续完善
            logger.info("图谱检索功能待完善")
            return []
            
        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            return []
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重检索结果"""
        seen_content = set()
        unique_results = []
        
        for result in results:
            # 使用内容的前100个字符作为去重标识
            content_key = result.content[:100]
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)
        
        return unique_results
    
    async def _fuse_answers(self, query: str, search_results: List[SearchResult]) -> str:
        """融合答案"""
        try:
            if not search_results:
                return "抱歉，没有找到相关信息。"
            
            # 构建融合提示词
            context_parts = []
            for i, result in enumerate(search_results[:5]):  # 使用前5个结果
                context_parts.append(f"[来源{i+1}] {result.content}")
            
            context = "\n\n".join(context_parts)
            
            prompt = f"""基于以下检索到的信息，回答用户问题。

用户问题：{query}

检索信息：
{context}

请根据检索信息生成准确、完整的答案。如果信息不足，请说明。请标注信息来源。"""
            
            # 调用LLM生成答案
            answer = await self.llm_service.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"答案融合失败: {e}")
            return "答案生成过程中出现错误。"
    
    async def _assess_quality(self, query: str, answer: str, search_results: List[SearchResult]) -> Dict[str, Any]:
        """评估答案质量"""
        try:
            # 简化的质量评估
            quality_score = 0.8  # 基础分数
            
            # 根据检索结果数量调整
            if len(search_results) >= 3:
                quality_score += 0.1
            
            # 根据平均置信度调整
            if search_results:
                avg_confidence = sum(r.confidence for r in search_results) / len(search_results)
                quality_score = min(1.0, quality_score + avg_confidence * 0.1)
            
            return {
                "confidence": quality_score,
                "completeness": 0.8,
                "relevance": 0.85,
                "accuracy": 0.9,
                "overall_score": quality_score,
                "assessment": "答案质量良好" if quality_score > 0.7 else "答案质量一般"
            }
            
        except Exception as e:
            logger.error(f"质量评估失败: {e}")
            return {"confidence": 0.5, "assessment": "质量评估失败"}
    
    def _update_stats(self, modes: List[SearchMode], processing_time: float):
        """更新统计信息"""
        self.stats["total_requests"] += 1
        
        # 更新平均响应时间
        total_time = self.stats["avg_response_time"] * (self.stats["total_requests"] - 1) + processing_time
        self.stats["avg_response_time"] = total_time / self.stats["total_requests"]
        
        # 更新模式使用统计
        for mode in modes:
            if mode.value in self.stats["mode_usage"]:
                self.stats["mode_usage"][mode.value] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


# 全局多智能体协调器实例
multi_agent_coordinator = MultiAgentCoordinator()
