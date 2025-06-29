"""
AutoGen智能体服务
"""

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, AsyncGenerator

from loguru import logger

from app.services.llm_service import LLMService
from app.services.milvus_service import MilvusService
from app.services import embedding_service
from app.services import neo4j_graph_service as neo4j_service
from app.core import AgentException
from app.core import settings

# 创建服务实例
llm_service = LLMService()
vector_db_service = MilvusService()


class AgentType(Enum):
    """智能体类型"""
    QUERY_ANALYZER = "query_analyzer"
    VECTOR_RETRIEVER = "vector_retriever"
    GRAPH_RETRIEVER = "graph_retriever"
    HYBRID_RETRIEVER = "hybrid_retriever"
    RESULT_FUSION = "result_fusion"
    ANSWER_GENERATOR = "answer_generator"


@dataclass
class AgentConfig:
    """智能体配置"""
    name: str
    agent_type: AgentType
    system_message: str
    model_client: Any = None
    max_consecutive_auto_reply: int = 3
    temperature: float = 0.1


@dataclass
class QueryContext:
    """查询上下文"""
    query: str
    user_id: int
    knowledge_base_ids: List[int]
    conversation_history: List[Dict[str, str]] = None
    metadata: Dict[str, Any] = None


@dataclass
class RetrievalResult:
    """检索结果"""
    source: str  # vector, graph, hybrid
    results: List[Dict[str, Any]]
    score: float
    metadata: Dict[str, Any] = None


class BaseRAGAgent:
    """RAG智能体基类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """初始化智能体"""
        try:
            # 暂时使用简化的智能体实现，不依赖AutoGen
            # 后续可以根据需要集成AutoGen
            self.agent = None  # 暂时设为None
            logger.info(f"初始化智能体: {self.config.name}")
        except Exception as e:
            logger.error(f"初始化智能体失败: {e}")
            raise AgentException(f"初始化智能体失败: {e}")
    
    async def process(self, context: QueryContext) -> Dict[str, Any]:
        """处理请求"""
        raise NotImplementedError("子类必须实现process方法")


class QueryAnalyzerAgent(BaseRAGAgent):
    """查询分析智能体"""
    
    def __init__(self):
        config = AgentConfig(
            name="query_analyzer",
            agent_type=AgentType.QUERY_ANALYZER,
            system_message="""你是一个专业的查询分析智能体。你的任务是分析用户的查询，提取关键信息，并制定检索策略。

请分析用户查询并返回以下信息：
1. 查询意图和类型
2. 关键实体和概念
3. 推荐的检索策略
4. 查询复杂度评估

请以JSON格式返回分析结果。"""
        )
        super().__init__(config)
    
    async def process(self, context: QueryContext) -> Dict[str, Any]:
        """分析查询"""
        try:
            # 使用LLM服务分析查询
            analysis = await llm_service.analyze_query_intent(context.query)
            
            # 增强分析结果
            analysis.update({
                "original_query": context.query,
                "user_id": context.user_id,
                "knowledge_base_ids": context.knowledge_base_ids,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            logger.info(f"查询分析完成: {context.query}")
            return analysis
            
        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            raise AgentException(f"查询分析失败: {e}")


class VectorRetrieverAgent(BaseRAGAgent):
    """向量检索智能体"""
    
    def __init__(self):
        config = AgentConfig(
            name="vector_retriever",
            agent_type=AgentType.VECTOR_RETRIEVER,
            system_message="""你是一个向量检索智能体。你的任务是基于语义相似度检索相关文档片段。

你需要：
1. 将查询转换为向量表示
2. 在向量数据库中搜索相似内容
3. 对结果进行重排和过滤
4. 返回高质量的检索结果"""
        )
        super().__init__(config)
    
    async def process(self, context: QueryContext) -> RetrievalResult:
        """执行向量检索"""
        try:
            # 1. 生成查询向量
            query_vector = await embedding_service.embed_text(context.query)
            
            # 2. 向量搜索
            search_results = await vector_db_service.search_vectors(
                collection_name=settings.MILVUS_COLLECTION_NAME,
                query_vectors=[query_vector],
                top_k=20,
                knowledge_base_ids=context.knowledge_base_ids
            )
            
            # 3. 处理搜索结果
            results = []
            if search_results and search_results[0]:
                for hit in search_results[0]:
                    result = {
                        "id": hit["id"],
                        "content": hit["content"],
                        "score": hit["score"],
                        "metadata": hit["metadata"],
                        "knowledge_base_id": hit["knowledge_base_id"],
                        "document_id": hit["document_id"],
                        "chunk_index": hit["chunk_index"]
                    }
                    results.append(result)
            
            # 4. 计算整体检索质量分数
            avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0
            
            retrieval_result = RetrievalResult(
                source="vector",
                results=results,
                score=avg_score,
                metadata={
                    "query": context.query,
                    "total_results": len(results),
                    "search_time": asyncio.get_event_loop().time()
                }
            )
            
            logger.info(f"向量检索完成，返回 {len(results)} 个结果")
            return retrieval_result
            
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            raise AgentException(f"向量检索失败: {e}")


class GraphRetrieverAgent(BaseRAGAgent):
    """图谱检索智能体"""
    
    def __init__(self):
        config = AgentConfig(
            name="graph_retriever",
            agent_type=AgentType.GRAPH_RETRIEVER,
            system_message="""你是一个图谱检索智能体。你的任务是基于知识图谱进行结构化查询和推理。

你需要：
1. 识别查询中的实体和关系
2. 构建Cypher查询语句
3. 在知识图谱中执行查询
4. 返回结构化的知识结果"""
        )
        super().__init__(config)
    
    async def process(self, context: QueryContext) -> RetrievalResult:
        """执行图谱检索"""
        try:
            # 1. 实体识别和关系抽取
            entities = await self._extract_entities(context.query)
            
            # 2. 构建Cypher查询
            cypher_query = await self._build_cypher_query(context.query, entities)
            
            # 3. 执行图谱查询
            graph_results = await neo4j_service.execute_query(
                cypher_query,
                knowledge_base_ids=context.knowledge_base_ids
            )
            
            # 4. 处理查询结果
            results = []
            for record in graph_results:
                result = {
                    "id": f"graph_{record.get('id', '')}",
                    "content": record.get("content", ""),
                    "entities": record.get("entities", []),
                    "relationships": record.get("relationships", []),
                    "score": record.get("score", 0.8),  # 图谱结果默认较高分数
                    "metadata": {
                        "source": "knowledge_graph",
                        "query_type": "cypher",
                        "entities": entities
                    }
                }
                results.append(result)
            
            # 5. 计算整体检索质量分数
            avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0
            
            retrieval_result = RetrievalResult(
                source="graph",
                results=results,
                score=avg_score,
                metadata={
                    "query": context.query,
                    "cypher_query": cypher_query,
                    "entities": entities,
                    "total_results": len(results)
                }
            )
            
            logger.info(f"图谱检索完成，返回 {len(results)} 个结果")
            return retrieval_result
            
        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            raise AgentException(f"图谱检索失败: {e}")
    
    async def _extract_entities(self, query: str) -> List[str]:
        """提取实体"""
        try:
            # 使用LLM提取实体
            system_prompt = "请从查询中提取关键实体，返回JSON格式的实体列表。"
            response = await llm_service.generate_text(
                prompt=f"查询: {query}",
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            # 解析实体
            try:
                entities_data = json.loads(response)
                return entities_data.get("entities", [])
            except json.JSONDecodeError:
                # 如果解析失败，使用简单的分词
                return query.split()
                
        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return []
    
    async def _build_cypher_query(self, query: str, entities: List[str]) -> str:
        """构建Cypher查询"""
        try:
            # 使用LLM生成Cypher查询
            system_prompt = """你是一个Cypher查询专家。请根据用户查询和提取的实体，生成合适的Cypher查询语句。

查询应该：
1. 查找相关的节点和关系
2. 返回有用的信息
3. 限制结果数量以提高性能

请只返回Cypher查询语句，不要包含其他内容。"""
            
            prompt = f"""
用户查询: {query}
提取的实体: {entities}

请生成Cypher查询语句:"""
            
            cypher_query = await llm_service.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            # 清理查询语句
            cypher_query = cypher_query.strip()
            if cypher_query.startswith("```"):
                cypher_query = cypher_query.split("\n")[1:-1]
                cypher_query = "\n".join(cypher_query)
            
            return cypher_query
            
        except Exception as e:
            logger.error(f"构建Cypher查询失败: {e}")
            # 返回一个默认的查询
            return "MATCH (n) RETURN n LIMIT 10"


class ResultFusionAgent(BaseRAGAgent):
    """结果融合智能体"""

    def __init__(self):
        config = AgentConfig(
            name="result_fusion",
            agent_type=AgentType.RESULT_FUSION,
            system_message="""你是一个结果融合智能体。你的任务是分析和融合来自不同检索源的结果。

你需要：
1. 分析不同检索结果的质量和相关性
2. 去除重复和冗余信息
3. 按相关性和重要性排序
4. 生成融合后的高质量结果集"""
        )
        super().__init__(config)

    async def process(self, retrieval_results: List[RetrievalResult]) -> Dict[str, Any]:
        """融合检索结果"""
        try:
            # 1. 收集所有结果
            all_results = []
            source_weights = {"vector": 0.4, "graph": 0.4, "hybrid": 0.2}

            for retrieval_result in retrieval_results:
                source = retrieval_result.source
                weight = source_weights.get(source, 0.3)

                for result in retrieval_result.results:
                    # 计算加权分数
                    weighted_score = result["score"] * weight

                    fusion_result = {
                        "id": result["id"],
                        "content": result["content"],
                        "original_score": result["score"],
                        "weighted_score": weighted_score,
                        "source": source,
                        "metadata": result.get("metadata", {}),
                        "knowledge_base_id": result.get("knowledge_base_id"),
                        "document_id": result.get("document_id")
                    }
                    all_results.append(fusion_result)

            # 2. 去重处理
            deduplicated_results = await self._deduplicate_results(all_results)

            # 3. 重新排序
            sorted_results = sorted(
                deduplicated_results,
                key=lambda x: x["weighted_score"],
                reverse=True
            )

            # 4. 选择top结果
            top_results = sorted_results[:10]

            # 5. 生成融合摘要
            fusion_summary = await self._generate_fusion_summary(top_results)

            fusion_result = {
                "fused_results": top_results,
                "total_sources": len(retrieval_results),
                "total_results": len(all_results),
                "deduplicated_count": len(deduplicated_results),
                "final_count": len(top_results),
                "fusion_summary": fusion_summary,
                "fusion_score": sum(r["weighted_score"] for r in top_results) / len(top_results) if top_results else 0.0
            }

            logger.info(f"结果融合完成，最终返回 {len(top_results)} 个结果")
            return fusion_result

        except Exception as e:
            logger.error(f"结果融合失败: {e}")
            raise AgentException(f"结果融合失败: {e}")

    async def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重处理"""
        try:
            # 基于内容相似度去重
            deduplicated = []
            seen_contents = set()

            for result in results:
                content = result["content"]
                content_hash = hash(content[:200])  # 使用前200字符的hash

                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    deduplicated.append(result)
                else:
                    # 如果内容重复，保留分数更高的
                    for i, existing in enumerate(deduplicated):
                        if hash(existing["content"][:200]) == content_hash:
                            if result["weighted_score"] > existing["weighted_score"]:
                                deduplicated[i] = result
                            break

            return deduplicated

        except Exception as e:
            logger.error(f"去重处理失败: {e}")
            return results

    async def _generate_fusion_summary(self, results: List[Dict[str, Any]]) -> str:
        """生成融合摘要"""
        try:
            if not results:
                return "未找到相关结果"

            # 提取关键信息
            contents = [r["content"][:500] for r in results[:5]]  # 取前5个结果的前500字符
            combined_content = "\n\n".join(contents)

            # 使用LLM生成摘要
            system_prompt = "请为以下检索结果生成一个简洁的摘要，突出关键信息和主要观点。"
            summary = await llm_service.generate_text(
                prompt=f"检索结果:\n{combined_content}",
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=300
            )

            return summary.strip()

        except Exception as e:
            logger.error(f"生成融合摘要失败: {e}")
            return "摘要生成失败"


class AnswerGeneratorAgent(BaseRAGAgent):
    """答案生成智能体"""

    def __init__(self):
        config = AgentConfig(
            name="answer_generator",
            agent_type=AgentType.ANSWER_GENERATOR,
            system_message="""你是一个专业的答案生成智能体。你的任务是基于融合后的检索结果生成准确、完整的答案。

你需要：
1. 分析用户查询和检索结果
2. 生成准确、相关的答案
3. 引用具体的来源信息
4. 确保答案的逻辑性和完整性"""
        )
        super().__init__(config)

    async def process(
        self,
        context: QueryContext,
        fusion_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成最终答案"""
        try:
            # 1. 准备上下文信息
            fused_results = fusion_result.get("fused_results", [])
            context_text = self._prepare_context(fused_results)

            # 2. 生成答案
            answer = await llm_service.generate_rag_answer(
                query=context.query,
                context=context_text,
                sources=fused_results,
                conversation_history=context.conversation_history
            )

            # 3. 准备来源引用
            sources = self._prepare_sources(fused_results)

            # 4. 生成答案元数据
            answer_metadata = {
                "query": context.query,
                "answer_length": len(answer),
                "source_count": len(sources),
                "fusion_score": fusion_result.get("fusion_score", 0.0),
                "generation_time": asyncio.get_event_loop().time()
            }

            final_answer = {
                "answer": answer,
                "sources": sources,
                "metadata": answer_metadata,
                "fusion_summary": fusion_result.get("fusion_summary", ""),
                "confidence_score": self._calculate_confidence_score(fusion_result)
            }

            logger.info(f"答案生成完成，长度: {len(answer)} 字符")
            return final_answer

        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            raise AgentException(f"答案生成失败: {e}")

    async def generate_stream(
        self,
        context: QueryContext,
        fusion_result: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """流式生成答案"""
        try:
            # 准备上下文信息
            fused_results = fusion_result.get("fused_results", [])
            context_text = self._prepare_context(fused_results)

            # 流式生成答案
            async for chunk in llm_service.generate_rag_answer_stream(
                query=context.query,
                context=context_text,
                sources=fused_results,
                conversation_history=context.conversation_history
            ):
                yield chunk

        except Exception as e:
            logger.error(f"流式答案生成失败: {e}")
            raise AgentException(f"流式答案生成失败: {e}")

    def _prepare_context(self, results: List[Dict[str, Any]]) -> str:
        """准备上下文文本"""
        context_parts = []
        for i, result in enumerate(results[:5], 1):  # 最多使用前5个结果
            content = result["content"]
            source = result.get("source", "unknown")
            context_parts.append(f"[来源{i} - {source}]\n{content}")

        return "\n\n".join(context_parts)

    def _prepare_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """准备来源信息"""
        sources = []
        for result in results:
            source = {
                "id": result["id"],
                "content_preview": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"],
                "score": result["weighted_score"],
                "source_type": result["source"],
                "metadata": result.get("metadata", {})
            }
            sources.append(source)

        return sources

    def _calculate_confidence_score(self, fusion_result: Dict[str, Any]) -> float:
        """计算置信度分数"""
        try:
            fusion_score = fusion_result.get("fusion_score", 0.0)
            result_count = fusion_result.get("final_count", 0)
            source_count = fusion_result.get("total_sources", 0)

            # 基于多个因素计算置信度
            confidence = (
                fusion_score * 0.5 +  # 融合分数权重50%
                min(result_count / 5, 1.0) * 0.3 +  # 结果数量权重30%
                min(source_count / 2, 1.0) * 0.2  # 来源数量权重20%
            )

            return min(confidence, 1.0)

        except Exception:
            return 0.5  # 默认置信度


# 全局智能体实例
query_analyzer = QueryAnalyzerAgent()
vector_retriever = VectorRetrieverAgent()
graph_retriever = GraphRetrieverAgent()
result_fusion = ResultFusionAgent()
answer_generator = AnswerGeneratorAgent()
