"""
知识检索智能体
负责从向量数据库和知识库中检索相关信息，提供准确的知识回答
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from autogen_core import CancellationToken

from .base_agent import BaseAgent
from ..core.vector_store import get_vector_store
from ..core.model_manager import model_manager, ModelType

logger = logging.getLogger(__name__)


class KnowledgeAgent(BaseAgent):
    """
    知识检索智能体
    
    主要职责：
    - 理解用户查询意图
    - 从向量数据库检索相关知识
    - 使用重排模型优化检索结果
    - 基于检索结果生成准确回答
    - 管理知识库权限和访问控制
    """
    
    def __init__(
        self,
        name: str = "KnowledgeAgent",
        system_message: str = None,
        model_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        初始化知识检索智能体
        
        Args:
            name: 智能体名称
            system_message: 系统提示词
            model_config: 模型配置
            **kwargs: 其他配置参数
        """
        if system_message is None:
            system_message = self._get_default_system_message()
        
        super().__init__(
            name=name,
            system_message=system_message,
            model_config=model_config,
            **kwargs
        )
        
        # 知识检索配置
        self.search_top_k = model_config.get('search_top_k', 10) if model_config else 10
        self.rerank_top_k = model_config.get('rerank_top_k', 5) if model_config else 5
        self.similarity_threshold = model_config.get('similarity_threshold', 0.7) if model_config else 0.7
        self.max_context_length = model_config.get('max_context_length', 4000) if model_config else 4000
        
        # 向量存储和模型服务
        self.vector_store = None
        self.embedding_service = None
        self.rerank_service = None
        
        # 知识库权限配置
        self.allowed_collections = model_config.get('allowed_collections', ['documents', 'knowledge']) if model_config else ['documents', 'knowledge']
        self.user_access_control = model_config.get('user_access_control', True) if model_config else True
        
        logger.info(f"知识检索智能体 {self.name} 初始化完成")
    
    def _get_default_system_message(self) -> str:
        """获取默认系统提示词"""
        return """你是一个专业的知识检索助手。你的主要职责是：

1. 理解用户的问题和查询需求
2. 从知识库中检索最相关的信息
3. 基于检索到的知识提供准确、有用的回答
4. 确保回答的准确性和相关性
5. 当知识库中没有相关信息时，诚实说明

请始终基于检索到的知识内容回答问题，不要编造或推测信息。如果检索结果不足以回答问题，请明确说明并建议用户提供更多信息。"""
    
    async def initialize_services(self):
        """初始化服务依赖"""
        try:
            # 初始化向量存储
            self.vector_store = await get_vector_store()
            
            # 获取嵌入模型服务
            self.embedding_service = model_manager.get_default_model(ModelType.EMBEDDING)
            if not self.embedding_service:
                logger.warning("嵌入模型服务不可用，将影响知识检索功能")
            
            # 获取重排模型服务
            self.rerank_service = model_manager.get_default_model(ModelType.RERANK)
            if not self.rerank_service:
                logger.warning("重排模型服务不可用，将使用基础检索排序")
            
            logger.info(f"知识检索智能体 {self.name} 服务初始化完成")
            
        except Exception as e:
            logger.error(f"知识检索智能体服务初始化失败: {str(e)}")
            raise
    
    async def _handle_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> str:
        """
        处理知识检索请求的核心逻辑
        
        Args:
            message: 用户查询
            context: 上下文信息
            cancellation_token: 取消令牌
            
        Returns:
            基于知识库的回答
        """
        try:
            # 确保服务已初始化
            if not self.vector_store:
                await self.initialize_services()
            
            # 分析查询意图
            query_analysis = await self._analyze_query(message, context)
            
            # 执行知识检索
            search_results = await self._search_knowledge(
                query=message,
                context=context,
                query_analysis=query_analysis
            )
            
            # 检查检索结果质量
            if not search_results or len(search_results) == 0:
                return await self._handle_no_results(message, context)
            
            # 过滤低质量结果
            filtered_results = await self._filter_results(search_results, query_analysis)
            
            if not filtered_results:
                return await self._handle_low_quality_results(message, context)
            
            # 生成基于知识的回答
            response = await self._generate_knowledge_response(
                query=message,
                search_results=filtered_results,
                context=context
            )
            
            return response
            
        except Exception as e:
            logger.error(f"知识检索处理失败: {str(e)}")
            return f"抱歉，在检索知识时遇到了问题：{str(e)}"
    
    async def _analyze_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析用户查询意图
        
        Args:
            query: 用户查询
            context: 上下文信息
            
        Returns:
            查询分析结果
        """
        analysis = {
            'query_type': 'general',
            'keywords': [],
            'entities': [],
            'intent': 'information_seeking',
            'specificity': 'medium',
            'collections_to_search': self.allowed_collections.copy()
        }
        
        # 简单的查询分析（可以后续用更复杂的NLP模型替换）
        query_lower = query.lower()
        
        # 识别查询类型
        if any(word in query_lower for word in ['什么是', 'what is', '定义', 'definition']):
            analysis['query_type'] = 'definition'
            analysis['intent'] = 'definition_seeking'
        elif any(word in query_lower for word in ['如何', 'how to', '怎么', '方法']):
            analysis['query_type'] = 'how_to'
            analysis['intent'] = 'instruction_seeking'
        elif any(word in query_lower for word in ['为什么', 'why', '原因', 'reason']):
            analysis['query_type'] = 'explanation'
            analysis['intent'] = 'explanation_seeking'
        elif any(word in query_lower for word in ['比较', 'compare', '区别', 'difference']):
            analysis['query_type'] = 'comparison'
            analysis['intent'] = 'comparison_seeking'
        
        # 提取关键词（简单实现）
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '然而', '因为', '所以'}
        words = query.split()
        analysis['keywords'] = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 根据用户权限调整搜索范围
        if context and self.user_access_control:
            user_id = context.get('user_id')
            if user_id:
                # 可以根据用户权限调整搜索的知识库集合
                pass
        
        logger.debug(f"查询分析结果: {analysis}")
        return analysis
    
    async def _search_knowledge(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        query_analysis: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行知识检索
        
        Args:
            query: 查询文本
            context: 上下文信息
            query_analysis: 查询分析结果
            
        Returns:
            检索结果列表
        """
        try:
            if not self.embedding_service or not self.vector_store:
                logger.error("嵌入服务或向量存储不可用")
                return []
            
            # 生成查询向量
            query_vector = await self.embedding_service.encode([query])
            if query_vector is None or len(query_vector) == 0:
                logger.error("查询向量生成失败")
                return []
            
            query_vector = query_vector[0].tolist()
            
            # 构建过滤条件
            filter_expr = await self._build_filter_expression(context, query_analysis)
            
            all_results = []
            
            # 在允许的集合中搜索
            collections_to_search = query_analysis.get('collections_to_search', self.allowed_collections) if query_analysis else self.allowed_collections
            
            for collection_name in collections_to_search:
                try:
                    # 执行向量搜索
                    search_results = await self.vector_store.search_vectors(
                        collection_name=collection_name,
                        query_vectors=[query_vector],
                        top_k=self.search_top_k,
                        filter_expr=filter_expr
                    )
                    
                    if search_results and len(search_results) > 0:
                        # 添加集合信息
                        for result in search_results[0]:
                            result['collection'] = collection_name
                        all_results.extend(search_results[0])
                        
                except Exception as e:
                    logger.warning(f"在集合 {collection_name} 中搜索失败: {str(e)}")
                    continue
            
            # 按相似度排序
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # 使用重排模型优化结果
            if self.rerank_service and len(all_results) > 1:
                all_results = await self._rerank_results(query, all_results)
            
            # 返回top_k结果
            return all_results[:self.rerank_top_k]
            
        except Exception as e:
            logger.error(f"知识检索失败: {str(e)}")
            return []
    
    async def _build_filter_expression(
        self,
        context: Optional[Dict[str, Any]] = None,
        query_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        构建过滤表达式
        
        Args:
            context: 上下文信息
            query_analysis: 查询分析结果
            
        Returns:
            过滤表达式字符串
        """
        filters = []
        
        # 用户权限过滤
        if context and self.user_access_control:
            user_id = context.get('user_id')
            if user_id:
                filters.append(f"user_id == '{user_id}' or user_id == ''")
        
        # 时间过滤（可选）
        # filters.append("timestamp > 1640995200000")  # 2022年以后的数据
        
        # 组合过滤条件
        if filters:
            return " and ".join(f"({f})" for f in filters)
        
        return None
    
    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        使用重排模型优化检索结果
        
        Args:
            query: 查询文本
            results: 原始检索结果
            
        Returns:
            重排后的结果
        """
        try:
            if not self.rerank_service or len(results) <= 1:
                return results
            
            # 提取文档文本
            documents = [result.get('text', '') for result in results]
            
            # 执行重排
            rerank_results = await self.rerank_service.rerank(
                query=query,
                documents=documents,
                top_k=self.rerank_top_k
            )
            
            # 重新组织结果
            reranked = []
            for rerank_result in rerank_results:
                original_index = rerank_result['index']
                if original_index < len(results):
                    result = results[original_index].copy()
                    result['rerank_score'] = rerank_result['score']
                    result['combined_score'] = (
                        result.get('score', 0) * 0.7 + 
                        rerank_result['score'] * 0.3
                    )
                    reranked.append(result)
            
            return reranked
            
        except Exception as e:
            logger.error(f"重排失败: {str(e)}")
            return results
    
    async def _filter_results(
        self,
        results: List[Dict[str, Any]],
        query_analysis: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        过滤低质量检索结果
        
        Args:
            results: 检索结果
            query_analysis: 查询分析结果
            
        Returns:
            过滤后的结果
        """
        filtered = []
        
        for result in results:
            # 相似度阈值过滤
            score = result.get('combined_score', result.get('score', 0))
            if score < self.similarity_threshold:
                continue
            
            # 文本长度过滤
            text = result.get('text', '')
            if len(text.strip()) < 10:  # 过滤过短的文本
                continue
            
            # 重复内容过滤
            is_duplicate = False
            for existing in filtered:
                if self._calculate_text_similarity(text, existing.get('text', '')) > 0.9:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(result)
        
        return filtered
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单实现）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _generate_knowledge_response(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        基于检索结果生成回答
        
        Args:
            query: 用户查询
            search_results: 检索结果
            context: 上下文信息
            
        Returns:
            生成的回答
        """
        try:
            # 构建知识上下文
            knowledge_context = self._build_knowledge_context(search_results)
            
            # 构建提示词
            prompt = self._build_response_prompt(query, knowledge_context)
            
            # 使用LLM生成回答
            llm_service = model_manager.get_default_model(ModelType.LLM)
            if llm_service:
                messages = [
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt}
                ]
                
                response = await llm_service.chat_completion(
                    messages=messages,
                    temperature=0.3,  # 较低温度确保准确性
                    max_tokens=1024
                )
                
                return response
            else:
                # 降级处理：直接返回检索结果摘要
                return self._create_fallback_response(query, search_results)
                
        except Exception as e:
            logger.error(f"生成知识回答失败: {str(e)}")
            return self._create_fallback_response(query, search_results)
    
    def _build_knowledge_context(self, search_results: List[Dict[str, Any]]) -> str:
        """构建知识上下文"""
        context_parts = []
        total_length = 0
        
        for i, result in enumerate(search_results):
            text = result.get('text', '')
            source = result.get('source', '未知来源')
            score = result.get('combined_score', result.get('score', 0))
            
            # 构建单个知识片段
            knowledge_piece = f"知识片段{i+1} (相关度: {score:.2f}, 来源: {source}):\n{text}\n"
            
            # 检查长度限制
            if total_length + len(knowledge_piece) > self.max_context_length:
                break
            
            context_parts.append(knowledge_piece)
            total_length += len(knowledge_piece)
        
        return "\n".join(context_parts)
    
    def _build_response_prompt(self, query: str, knowledge_context: str) -> str:
        """构建响应提示词"""
        return f"""基于以下知识内容回答用户问题。请确保回答准确、相关且有用。

用户问题: {query}

相关知识:
{knowledge_context}

请基于上述知识内容回答用户问题。如果知识内容不足以完全回答问题，请说明并建议用户提供更多信息。"""
    
    def _create_fallback_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """创建降级回答"""
        if not search_results:
            return "抱歉，我没有找到相关的知识信息来回答您的问题。"
        
        # 简单拼接检索结果
        response_parts = ["根据我的知识库，我找到了以下相关信息：\n"]
        
        for i, result in enumerate(search_results[:3]):  # 最多显示3个结果
            text = result.get('text', '')[:200]  # 限制长度
            source = result.get('source', '知识库')
            response_parts.append(f"{i+1}. {text}... (来源: {source})")
        
        response_parts.append("\n如需更详细的信息，请提供更具体的问题。")
        
        return "\n".join(response_parts)
    
    async def _handle_no_results(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """处理无检索结果的情况"""
        return f"抱歉，我在知识库中没有找到关于「{query}」的相关信息。您可以：\n1. 尝试使用不同的关键词重新提问\n2. 提供更多背景信息\n3. 联系管理员添加相关知识内容"
    
    async def _handle_low_quality_results(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """处理低质量检索结果的情况"""
        return f"我找到了一些可能相关的信息，但相关性较低。建议您：\n1. 使用更具体的关键词\n2. 提供更多上下文信息\n3. 尝试换一种表达方式重新提问"
    
    async def search_knowledge_direct(
        self,
        query: str,
        collection_name: str = "documents",
        top_k: int = 5,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        直接知识检索接口（供其他组件调用）
        
        Args:
            query: 查询文本
            collection_name: 集合名称
            top_k: 返回结果数量
            user_id: 用户ID
            
        Returns:
            检索结果
        """
        try:
            context = {'user_id': user_id} if user_id else None
            query_analysis = {'collections_to_search': [collection_name]}
            
            return await self._search_knowledge(query, context, query_analysis)
            
        except Exception as e:
            logger.error(f"直接知识检索失败: {str(e)}")
            return []
    
    def get_search_stats(self) -> Dict[str, Any]:
        """获取检索统计信息"""
        return {
            'agent_name': self.name,
            'search_top_k': self.search_top_k,
            'rerank_top_k': self.rerank_top_k,
            'similarity_threshold': self.similarity_threshold,
            'allowed_collections': self.allowed_collections,
            'total_searches': self.message_count,
            'error_rate': self.error_count / max(self.message_count, 1)
        }
