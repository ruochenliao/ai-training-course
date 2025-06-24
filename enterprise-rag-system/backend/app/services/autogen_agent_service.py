"""
AutoGen多智能体服务
基于Microsoft AutoGen框架实现的多智能体系统
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

import autogen
from autogen import ConversableAgent, GroupChat, GroupChatManager
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent

from app.core.config import settings
from app.services.vector_db import VectorDBService
from app.services.graph_db_service import GraphDBService
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from app.services.reranker_service import RerankerService

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """检索结果数据类"""
    content: str
    source: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class AgentResponse:
    """智能体响应数据类"""
    content: str
    agent_name: str
    search_results: List[SearchResult]
    confidence: float


class SemanticSearchAgent(ConversableAgent):
    """语义检索智能体"""
    
    def __init__(self, vector_service: VectorDBService, embedding_service: EmbeddingService):
        super().__init__(
            name="semantic_search_agent",
            system_message="""你是一个专业的语义检索智能体。
            你的任务是根据用户查询，使用向量相似度搜索找到最相关的文档内容。
            请分析查询意图，执行语义检索，并返回最相关的结果。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.AUTOGEN_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )
        self.vector_service = vector_service
        self.embedding_service = embedding_service
    
    async def semantic_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """执行语义检索"""
        try:
            # 生成查询向量
            query_vector = await self.embedding_service.embed_query(query)
            
            # 向量检索
            results = await self.vector_service.search(
                query_vector=query_vector,
                top_k=top_k,
                score_threshold=settings.DEFAULT_SCORE_THRESHOLD
            )
            
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    content=result.get("content", ""),
                    source=result.get("source", ""),
                    score=result.get("score", 0.0),
                    metadata=result.get("metadata", {})
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"语义检索失败: {e}")
            return []


class GraphSearchAgent(ConversableAgent):
    """图谱检索智能体"""
    
    def __init__(self, graph_service: GraphDBService):
        super().__init__(
            name="graph_search_agent",
            system_message="""你是一个专业的知识图谱检索智能体。
            你的任务是根据用户查询，在知识图谱中查找相关的实体和关系。
            请分析查询中的实体，执行图谱遍历，并返回相关的知识路径。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.AUTOGEN_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )
        self.graph_service = graph_service
    
    async def graph_search(self, query: str, max_depth: int = 3) -> List[SearchResult]:
        """执行图谱检索"""
        try:
            # 实体识别和图谱查询
            entities = await self.graph_service.extract_entities(query)
            
            search_results = []
            for entity in entities:
                # 查找相关路径
                paths = await self.graph_service.find_paths(
                    entity, 
                    max_depth=max_depth,
                    max_nodes=settings.GRAPH_MAX_NODES
                )
                
                for path in paths:
                    search_results.append(SearchResult(
                        content=path.get("description", ""),
                        source=f"知识图谱-{entity}",
                        score=path.get("relevance", 0.0),
                        metadata={
                            "entity": entity,
                            "path": path.get("path", []),
                            "relations": path.get("relations", [])
                        }
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            return []


class HybridSearchAgent(ConversableAgent):
    """混合检索智能体"""
    
    def __init__(self, 
                 vector_service: VectorDBService, 
                 graph_service: GraphDBService,
                 embedding_service: EmbeddingService,
                 reranker_service: RerankerService):
        super().__init__(
            name="hybrid_search_agent",
            system_message="""你是一个专业的混合检索智能体。
            你的任务是融合语义检索和图谱检索的结果，使用重排模型优化结果排序。
            请综合分析不同检索方式的结果，提供最优的检索结果。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.AUTOGEN_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )
        self.vector_service = vector_service
        self.graph_service = graph_service
        self.embedding_service = embedding_service
        self.reranker_service = reranker_service
    
    async def hybrid_search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """执行混合检索"""
        try:
            # 并行执行语义检索和图谱检索
            semantic_task = self._semantic_search(query, top_k * 2)
            graph_task = self._graph_search(query, top_k * 2)
            
            semantic_results, graph_results = await asyncio.gather(
                semantic_task, graph_task, return_exceptions=True
            )
            
            # 合并结果
            all_results = []
            if isinstance(semantic_results, list):
                all_results.extend(semantic_results)
            if isinstance(graph_results, list):
                all_results.extend(graph_results)
            
            # 使用重排模型优化排序
            if all_results and len(all_results) > 1:
                reranked_results = await self.reranker_service.rerank(
                    query=query,
                    documents=[r.content for r in all_results],
                    top_k=top_k
                )
                
                # 重新排序结果
                final_results = []
                for idx in reranked_results["indices"][:top_k]:
                    if idx < len(all_results):
                        result = all_results[idx]
                        result.score = reranked_results["scores"][len(final_results)]
                        final_results.append(result)
                
                return final_results
            
            return all_results[:top_k]
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []
    
    async def _semantic_search(self, query: str, top_k: int) -> List[SearchResult]:
        """内部语义检索方法"""
        query_vector = await self.embedding_service.embed_query(query)
        results = await self.vector_service.search(
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=settings.DEFAULT_SCORE_THRESHOLD
        )
        
        return [SearchResult(
            content=r.get("content", ""),
            source=r.get("source", ""),
            score=r.get("score", 0.0),
            metadata=r.get("metadata", {})
        ) for r in results]
    
    async def _graph_search(self, query: str, top_k: int) -> List[SearchResult]:
        """内部图谱检索方法"""
        entities = await self.graph_service.extract_entities(query)
        
        results = []
        for entity in entities[:5]:  # 限制实体数量
            paths = await self.graph_service.find_paths(entity, max_depth=2)
            for path in paths[:top_k//len(entities) if entities else top_k]:
                results.append(SearchResult(
                    content=path.get("description", ""),
                    source=f"知识图谱-{entity}",
                    score=path.get("relevance", 0.0),
                    metadata={
                        "entity": entity,
                        "path": path.get("path", [])
                    }
                ))
        
        return results


class AnswerGenerationAgent(ConversableAgent):
    """答案生成智能体"""
    
    def __init__(self, llm_service: LLMService):
        super().__init__(
            name="answer_generation_agent",
            system_message="""你是一个专业的答案生成智能体。
            你的任务是基于检索到的相关文档内容，生成准确、完整、有用的答案。
            请仔细分析检索结果，综合信息，生成高质量的回答。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": settings.AUTOGEN_TEMPERATURE,
                "timeout": settings.AUTOGEN_TIMEOUT,
            },
            human_input_mode="NEVER",
        )
        self.llm_service = llm_service
    
    async def generate_answer(self, 
                            query: str, 
                            search_results: List[SearchResult]) -> str:
        """基于检索结果生成答案"""
        try:
            # 构建上下文
            context_parts = []
            for i, result in enumerate(search_results[:settings.QA_MAX_SOURCES]):
                context_parts.append(
                    f"文档{i+1} (来源: {result.source}, 相关度: {result.score:.3f}):\n"
                    f"{result.content}\n"
                )
            
            context = "\n".join(context_parts)
            
            # 生成答案
            prompt = f"""基于以下检索到的相关文档内容，请回答用户的问题。

用户问题: {query}

相关文档内容:
{context}

请根据上述文档内容，生成准确、完整、有用的答案。如果文档内容不足以回答问题，请说明需要更多信息。
"""
            
            response = await self.llm_service.generate_response(
                prompt=prompt,
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE
            )
            
            return response.get("content", "抱歉，无法生成答案。")
            
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return "抱歉，答案生成过程中出现错误。"


class AutoGenAgentService:
    """AutoGen多智能体服务主类"""
    
    def __init__(self):
        self.vector_service = VectorDBService()
        self.graph_service = GraphDBService()
        self.llm_service = LLMService()
        self.embedding_service = EmbeddingService()
        self.reranker_service = RerankerService()
        
        # 初始化智能体
        self.semantic_agent = SemanticSearchAgent(
            self.vector_service, self.embedding_service
        )
        self.graph_agent = GraphSearchAgent(self.graph_service)
        self.hybrid_agent = HybridSearchAgent(
            self.vector_service, self.graph_service,
            self.embedding_service, self.reranker_service
        )
        self.answer_agent = AnswerGenerationAgent(self.llm_service)
        
        # 协调智能体
        self.coordinator = ConversableAgent(
            name="coordinator",
            system_message="""你是智能体协调员，负责协调不同检索智能体的工作。
            根据用户查询的特点，选择合适的检索策略，并整合结果。""",
            llm_config={
                "config_list": settings.AUTOGEN_CONFIG_LIST,
                "temperature": 0.1,
            },
            human_input_mode="NEVER",
        )
    
    async def process_query(self, 
                          query: str, 
                          search_modes: List[str] = ["semantic"],
                          top_k: int = 10) -> AgentResponse:
        """处理用户查询"""
        try:
            all_results = []
            
            # 根据选择的检索模式执行检索
            if "semantic" in search_modes:
                semantic_results = await self.semantic_agent.semantic_search(query, top_k)
                all_results.extend(semantic_results)
            
            if "graph" in search_modes:
                graph_results = await self.graph_agent.graph_search(query, top_k)
                all_results.extend(graph_results)
            
            if "hybrid" in search_modes:
                hybrid_results = await self.hybrid_agent.hybrid_search(query, top_k)
                all_results.extend(hybrid_results)
            
            # 去重和排序
            unique_results = self._deduplicate_results(all_results)
            top_results = sorted(unique_results, key=lambda x: x.score, reverse=True)[:top_k]
            
            # 生成答案
            answer = await self.answer_agent.generate_answer(query, top_results)
            
            # 计算置信度
            confidence = self._calculate_confidence(top_results)
            
            return AgentResponse(
                content=answer,
                agent_name="autogen_multi_agent",
                search_results=top_results,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"查询处理失败: {e}")
            return AgentResponse(
                content="抱歉，查询处理过程中出现错误。",
                agent_name="autogen_multi_agent",
                search_results=[],
                confidence=0.0
            )
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """去重检索结果"""
        seen_content = set()
        unique_results = []
        
        for result in results:
            content_hash = hash(result.content[:200])  # 使用前200字符去重
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _calculate_confidence(self, results: List[SearchResult]) -> float:
        """计算答案置信度"""
        if not results:
            return 0.0
        
        # 基于检索结果的分数计算置信度
        avg_score = sum(r.score for r in results) / len(results)
        max_score = max(r.score for r in results) if results else 0.0
        
        # 综合平均分和最高分
        confidence = (avg_score * 0.6 + max_score * 0.4)
        return min(confidence, 1.0)
