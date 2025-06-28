"""
多智能体协作服务 - 基于AutoGen框架
实现智能体协作的RAG检索和回答生成
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from loguru import logger
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

from app.core.config import settings
from app.services.search_service import SearchService
from app.services.llm_service import llm_service


class AutoGenRAGService:
    """基于AutoGen的多智能体RAG服务"""
    
    def __init__(self):
        self.llm_config = {
            "model": settings.LLM_MODEL_NAME,
            "api_key": settings.LLM_API_KEY,
            "base_url": settings.LLM_BASE_URL,
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        # 智能体配置
        self.agents = {}
        self._initialized = False

        # 初始化搜索服务
        self.search_service = SearchService()
    
    async def initialize(self):
        """初始化智能体"""
        if self._initialized:
            return
        
        try:
            # 1. 检索专家智能体
            self.retrieval_agent = AssistantAgent(
                name="RetrievalExpert",
                system_message="""你是一个检索专家，负责从知识库中检索相关信息。
                你的任务是：
                1. 分析用户查询，提取关键信息
                2. 选择最合适的检索策略（向量检索、图谱检索、混合检索）
                3. 执行检索并返回相关文档片段
                4. 评估检索结果的相关性和质量
                
                请始终以JSON格式返回检索结果，包含：
                - retrieval_strategy: 使用的检索策略
                - results: 检索到的文档片段列表
                - confidence: 检索结果的置信度(0-1)
                - summary: 检索结果的简要总结
                """,
                llm_config=self.llm_config,
            )
            
            # 2. 分析专家智能体
            self.analysis_agent = AssistantAgent(
                name="AnalysisExpert",
                system_message="""你是一个分析专家，负责分析和整合检索到的信息。
                你的任务是：
                1. 分析检索到的文档片段
                2. 识别关键信息和概念
                3. 发现信息之间的关联关系
                4. 整合多个来源的信息
                5. 识别信息的可靠性和一致性
                
                请提供结构化的分析结果，包含：
                - key_concepts: 关键概念列表
                - relationships: 概念之间的关系
                - confidence_assessment: 信息可靠性评估
                - integration_summary: 信息整合总结
                """,
                llm_config=self.llm_config,
            )
            
            # 3. 回答生成智能体
            self.answer_agent = AssistantAgent(
                name="AnswerGenerator",
                system_message="""你是一个回答生成专家，负责基于检索和分析的结果生成高质量的回答。
                你的任务是：
                1. 基于检索到的信息生成准确、完整的回答
                2. 确保回答逻辑清晰、结构合理
                3. 适当引用来源信息
                4. 标注不确定或需要进一步验证的信息
                5. 提供相关的补充建议
                
                回答格式要求：
                - 直接回答用户问题
                - 提供支撑证据
                - 标注信息来源
                - 指出局限性（如有）
                """,
                llm_config=self.llm_config,
            )
            
            # 4. 质量控制智能体
            self.quality_agent = AssistantAgent(
                name="QualityController",
                system_message="""你是一个质量控制专家，负责评估和改进回答质量。
                你的任务是：
                1. 评估回答的准确性、完整性和相关性
                2. 检查回答是否充分利用了检索到的信息
                3. 识别回答中的潜在问题或改进点
                4. 提供质量评分和改进建议
                
                评估维度：
                - accuracy: 准确性 (0-10)
                - completeness: 完整性 (0-10)
                - relevance: 相关性 (0-10)
                - clarity: 清晰度 (0-10)
                - source_usage: 来源利用度 (0-10)
                """,
                llm_config=self.llm_config,
            )
            
            # 5. 用户代理
            self.user_proxy = UserProxyAgent(
                name="UserProxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0,
                code_execution_config=False,
            )
            
            # 创建群聊
            self.group_chat = GroupChat(
                agents=[
                    self.retrieval_agent,
                    self.analysis_agent,
                    self.answer_agent,
                    self.quality_agent,
                    self.user_proxy
                ],
                messages=[],
                max_round=10,
                speaker_selection_method="round_robin"
            )
            
            self.chat_manager = GroupChatManager(
                groupchat=self.group_chat,
                llm_config=self.llm_config
            )
            
            self._initialized = True
            logger.info("AutoGen多智能体服务初始化完成")
            
        except Exception as e:
            logger.error(f"AutoGen服务初始化失败: {str(e)}")
            raise e
    
    async def process_query(
        self,
        query: str,
        knowledge_base_ids: Optional[List[int]] = None,
        user_id: Optional[int] = None,
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """处理用户查询，返回智能体协作的结果"""
        try:
            if not self._initialized:
                await self.initialize()
            
            logger.info(f"开始处理查询: {query}")
            start_time = datetime.now()
            
            # 1. 检索阶段
            retrieval_result = await self._retrieval_phase(
                query, knowledge_base_ids, user_id
            )
            
            # 2. 分析阶段
            analysis_result = await self._analysis_phase(
                query, retrieval_result
            )
            
            # 3. 回答生成阶段
            answer_result = await self._answer_generation_phase(
                query, retrieval_result, analysis_result, conversation_context
            )
            
            # 4. 质量控制阶段
            quality_result = await self._quality_control_phase(
                query, retrieval_result, analysis_result, answer_result
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "query": query,
                "answer": answer_result.get("final_answer", ""),
                "sources": retrieval_result.get("results", []),
                "confidence": quality_result.get("overall_score", 0.0) / 10.0,
                "processing_time": processing_time,
                "agent_results": {
                    "retrieval": retrieval_result,
                    "analysis": analysis_result,
                    "answer": answer_result,
                    "quality": quality_result
                },
                "metadata": {
                    "knowledge_base_ids": knowledge_base_ids,
                    "user_id": user_id,
                    "timestamp": start_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"查询处理失败: {str(e)}")
            return {
                "query": query,
                "answer": "抱歉，处理您的查询时遇到了问题。请稍后重试。",
                "sources": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _retrieval_phase(
        self,
        query: str,
        knowledge_base_ids: Optional[List[int]],
        user_id: Optional[int]
    ) -> Dict[str, Any]:
        """检索阶段"""
        try:
            # 构建检索提示
            retrieval_prompt = f"""
            用户查询: {query}
            
            请分析这个查询并执行最合适的检索策略。
            可选策略：vector（向量检索）、graph（图谱检索）、hybrid（混合检索）
            
            请选择最佳策略并说明理由。
            """
            
            # 让检索智能体分析查询
            response = await self._get_agent_response(
                self.retrieval_agent, retrieval_prompt
            )
            
            # 解析智能体的建议
            strategy = self._extract_strategy_from_response(response)
            
            # 执行实际检索
            if strategy == "vector":
                search_result = await self.search_service.vector_search(
                    query, knowledge_base_ids, user_id=user_id
                )
            elif strategy == "graph":
                search_result = await self.search_service.graph_search(
                    query, knowledge_base_ids, user_id=user_id
                )
            else:  # hybrid
                search_result = await self.search_service.hybrid_search(
                    query, knowledge_base_ids, user_id=user_id
                )
            
            return {
                "strategy": strategy,
                "agent_reasoning": response,
                "results": search_result.get("results", []),
                "total_results": search_result.get("total", 0),
                "processing_time": search_result.get("processing_time", 0)
            }
            
        except Exception as e:
            logger.error(f"检索阶段失败: {str(e)}")
            return {
                "strategy": "hybrid",
                "results": [],
                "error": str(e)
            }
    
    async def _analysis_phase(
        self,
        query: str,
        retrieval_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析阶段"""
        try:
            results = retrieval_result.get("results", [])
            if not results:
                return {"analysis": "没有检索到相关信息", "key_concepts": []}
            
            # 构建分析提示
            analysis_prompt = f"""
            用户查询: {query}
            
            检索到的信息:
            {self._format_retrieval_results(results)}
            
            请分析这些信息，提取关键概念，识别概念间的关系，并评估信息的可靠性。
            """
            
            response = await self._get_agent_response(
                self.analysis_agent, analysis_prompt
            )
            
            return {
                "analysis": response,
                "key_concepts": self._extract_concepts_from_response(response),
                "confidence": self._extract_confidence_from_response(response)
            }
            
        except Exception as e:
            logger.error(f"分析阶段失败: {str(e)}")
            return {"analysis": "分析失败", "error": str(e)}
    
    async def _answer_generation_phase(
        self,
        query: str,
        retrieval_result: Dict[str, Any],
        analysis_result: Dict[str, Any],
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """回答生成阶段"""
        try:
            # 构建回答生成提示
            context_str = ""
            if conversation_context:
                context_str = f"\n对话历史:\n{self._format_conversation_context(conversation_context)}\n"
            
            answer_prompt = f"""
            用户查询: {query}
            {context_str}
            检索结果:
            {self._format_retrieval_results(retrieval_result.get("results", []))}
            
            分析结果:
            {analysis_result.get("analysis", "")}
            
            请基于以上信息生成一个准确、完整、有用的回答。
            """
            
            response = await self._get_agent_response(
                self.answer_agent, answer_prompt
            )
            
            return {
                "final_answer": response,
                "reasoning": "基于检索信息和分析结果生成"
            }
            
        except Exception as e:
            logger.error(f"回答生成阶段失败: {str(e)}")
            return {
                "final_answer": "抱歉，无法生成回答。",
                "error": str(e)
            }
    
    async def _quality_control_phase(
        self,
        query: str,
        retrieval_result: Dict[str, Any],
        analysis_result: Dict[str, Any],
        answer_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """质量控制阶段"""
        try:
            quality_prompt = f"""
            用户查询: {query}
            生成的回答: {answer_result.get("final_answer", "")}
            检索结果数量: {len(retrieval_result.get("results", []))}
            
            请评估这个回答的质量，从准确性、完整性、相关性、清晰度、来源利用度等维度打分(0-10)。
            """
            
            response = await self._get_agent_response(
                self.quality_agent, quality_prompt
            )
            
            scores = self._extract_scores_from_response(response)
            overall_score = sum(scores.values()) / len(scores) if scores else 5.0
            
            return {
                "quality_assessment": response,
                "scores": scores,
                "overall_score": overall_score,
                "recommendation": "通过" if overall_score >= 7.0 else "需要改进"
            }
            
        except Exception as e:
            logger.error(f"质量控制阶段失败: {str(e)}")
            return {"overall_score": 5.0, "error": str(e)}
    
    async def _get_agent_response(self, agent, prompt: str) -> str:
        """获取智能体响应"""
        try:
            # 使用LLM服务直接获取响应
            response = await llm_service.generate_response(
                prompt,
                temperature=0.7,
                max_tokens=1000
            )
            return response.get("content", "")
        except Exception as e:
            logger.error(f"获取智能体响应失败: {str(e)}")
            return "智能体响应失败"
    
    def _extract_strategy_from_response(self, response: str) -> str:
        """从响应中提取检索策略"""
        response_lower = response.lower()
        if "vector" in response_lower and "graph" not in response_lower:
            return "vector"
        elif "graph" in response_lower and "vector" not in response_lower:
            return "graph"
        else:
            return "hybrid"
    
    def _extract_concepts_from_response(self, response: str) -> List[str]:
        """从响应中提取关键概念"""
        # 简化实现，实际可以使用更复杂的NLP技术
        concepts = []
        lines = response.split('\n')
        for line in lines:
            if '概念' in line or 'concept' in line.lower():
                # 提取概念
                parts = line.split('：')
                if len(parts) > 1:
                    concepts.extend([c.strip() for c in parts[1].split('、')])
        return concepts[:10]  # 限制数量
    
    def _extract_confidence_from_response(self, response: str) -> float:
        """从响应中提取置信度"""
        # 简化实现
        if "高置信度" in response or "very confident" in response.lower():
            return 0.9
        elif "中等置信度" in response or "moderately confident" in response.lower():
            return 0.7
        elif "低置信度" in response or "low confidence" in response.lower():
            return 0.5
        else:
            return 0.6
    
    def _extract_scores_from_response(self, response: str) -> Dict[str, float]:
        """从响应中提取评分"""
        scores = {}
        dimensions = ["accuracy", "completeness", "relevance", "clarity", "source_usage"]
        
        for dim in dimensions:
            # 简化的分数提取逻辑
            if f"{dim}" in response.lower():
                # 尝试提取数字
                import re
                pattern = f"{dim}.*?([0-9]+(?:\.[0-9]+)?)"
                match = re.search(pattern, response.lower())
                if match:
                    scores[dim] = float(match.group(1))
                else:
                    scores[dim] = 7.0  # 默认分数
            else:
                scores[dim] = 7.0
        
        return scores
    
    def _format_retrieval_results(self, results: List[Dict]) -> str:
        """格式化检索结果"""
        if not results:
            return "无检索结果"
        
        formatted = []
        for i, result in enumerate(results[:5], 1):  # 限制显示数量
            content = result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")
            source = result.get("document_title", "未知来源")
            score = result.get("score", 0.0)
            
            formatted.append(f"{i}. 来源: {source} (相关度: {score:.2f})\n内容: {content}\n")
        
        return "\n".join(formatted)
    
    def _format_conversation_context(self, context: List[Dict]) -> str:
        """格式化对话上下文"""
        formatted = []
        for msg in context[-5:]:  # 只保留最近5条
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)


# 全局AutoGen服务实例
autogen_service = AutoGenRAGService()
