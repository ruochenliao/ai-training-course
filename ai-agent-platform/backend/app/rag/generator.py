"""
# Copyright (c) 2025 左岚. All rights reserved.

响应生成器

基于检索到的文档片段生成高质量的答案。
"""

# # Standard library imports
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

# # Local folder imports
from ..agents.llm_interface import TokenCounter, llm_manager
from .vectorstore import SearchResult

logger = logging.getLogger(__name__)


class GenerationStrategy(Enum):
    """生成策略"""
    EXTRACTIVE = "extractive"  # 抽取式
    ABSTRACTIVE = "abstractive"  # 生成式
    HYBRID = "hybrid"  # 混合式


class CitationStyle(Enum):
    """引用样式"""
    NUMBERED = "numbered"  # 数字引用 [1]
    AUTHOR_YEAR = "author_year"  # 作者年份 (Smith, 2023)
    FOOTNOTE = "footnote"  # 脚注样式


class GeneratedResponse:
    """生成的响应"""
    
    def __init__(self, answer: str, sources: List[Dict[str, Any]] = None,
                 confidence: float = 0.0, metadata: Dict[str, Any] = None):
        self.answer = answer
        self.sources = sources or []
        self.confidence = confidence
        self.metadata = metadata or {}
        self.generated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "answer": self.answer,
            "sources": self.sources,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat()
        }


class SourceCitation:
    """来源引用"""
    
    def __init__(self, style: CitationStyle = CitationStyle.NUMBERED):
        self.style = style
        self.citations = {}
        self.counter = 0
    
    def add_source(self, source: SearchResult) -> str:
        """添加来源并返回引用标记"""
        source_id = source.document.id
        
        if source_id not in self.citations:
            self.counter += 1
            self.citations[source_id] = {
                "index": self.counter,
                "document": source.document,
                "score": source.score
            }
        
        if self.style == CitationStyle.NUMBERED:
            return f"[{self.citations[source_id]['index']}]"
        elif self.style == CitationStyle.AUTHOR_YEAR:
            author = source.document.metadata.get("author", "Unknown")
            year = source.document.metadata.get("year", "N/A")
            return f"({author}, {year})"
        else:
            return f"[{self.citations[source_id]['index']}]"
    
    def get_source_list(self) -> List[Dict[str, Any]]:
        """获取来源列表"""
        sources = []
        for citation in sorted(self.citations.values(), key=lambda x: x["index"]):
            doc = citation["document"]
            source = {
                "index": citation["index"],
                "id": doc.id,
                "title": doc.metadata.get("title", "Untitled"),
                "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "score": citation["score"],
                "metadata": doc.metadata
            }
            sources.append(source)
        return sources


class ResponseGenerator:
    """响应生成器"""
    
    def __init__(self, model_name: str = "gpt-4o", max_context_length: int = 8000):
        self.model_name = model_name
        self.max_context_length = max_context_length
    
    async def generate(self, query: str, search_results: List[SearchResult],
                      strategy: GenerationStrategy = GenerationStrategy.ABSTRACTIVE,
                      citation_style: CitationStyle = CitationStyle.NUMBERED,
                      max_sources: int = 5) -> GeneratedResponse:
        """生成响应"""
        try:
            if not search_results:
                return self._generate_no_results_response(query)
            
            # 限制使用的来源数量
            top_results = search_results[:max_sources]
            
            # 根据策略生成响应
            if strategy == GenerationStrategy.EXTRACTIVE:
                return await self._extractive_generation(query, top_results, citation_style)
            elif strategy == GenerationStrategy.ABSTRACTIVE:
                return await self._abstractive_generation(query, top_results, citation_style)
            else:  # HYBRID
                return await self._hybrid_generation(query, top_results, citation_style)
                
        except Exception as e:
            logger.error(f"响应生成失败: {e}")
            return GeneratedResponse(
                answer="抱歉，生成回答时出现错误。",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _extractive_generation(self, query: str, results: List[SearchResult],
                                   citation_style: CitationStyle) -> GeneratedResponse:
        """抽取式生成"""
        try:
            citation = SourceCitation(citation_style)
            
            # 构建提示
            context_parts = []
            for result in results:
                citation_mark = citation.add_source(result)
                context_parts.append(f"{citation_mark} {result.document.content}")
            
            context = "\n\n".join(context_parts)
            
            prompt = f"""
基于以下文档内容回答问题，请直接从文档中提取相关信息。

问题：{query}

文档内容：
{context}

要求：
1. 直接从文档中提取相关信息回答问题
2. 保持引用标记 [1], [2] 等
3. 如果文档中没有相关信息，请明确说明
4. 回答要准确、简洁

回答：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model_name,
                temperature=0.3,
                max_tokens=1000
            )
            
            # 计算置信度（基于引用数量和结果分数）
            confidence = self._calculate_confidence(results, response.content)
            
            return GeneratedResponse(
                answer=response.content,
                sources=citation.get_source_list(),
                confidence=confidence,
                metadata={
                    "strategy": "extractive",
                    "model": self.model_name,
                    "sources_used": len(results)
                }
            )
            
        except Exception as e:
            logger.error(f"抽取式生成失败: {e}")
            raise
    
    async def _abstractive_generation(self, query: str, results: List[SearchResult],
                                    citation_style: CitationStyle) -> GeneratedResponse:
        """生成式回答"""
        try:
            citation = SourceCitation(citation_style)
            
            # 构建上下文
            context_parts = []
            for result in results:
                citation_mark = citation.add_source(result)
                context_parts.append(f"来源{citation_mark}：{result.document.content}")
            
            context = "\n\n".join(context_parts)
            
            # 截断上下文以适应模型限制
            if TokenCounter.count_tokens(context) > self.max_context_length:
                context = TokenCounter.truncate_text(context, self.max_context_length)
            
            prompt = f"""
你是一个专业的知识助手。请基于提供的文档内容回答用户的问题。

问题：{query}

参考文档：
{context}

回答要求：
1. 基于文档内容生成准确、完整的回答
2. 可以整合多个来源的信息
3. 在回答中适当引用来源，使用 [1], [2] 等标记
4. 如果文档内容不足以回答问题，请诚实说明
5. 回答要逻辑清晰、语言流畅
6. 避免重复文档中的原文，要用自己的话总结

回答：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model_name,
                temperature=0.7,
                max_tokens=1500
            )
            
            confidence = self._calculate_confidence(results, response.content)
            
            return GeneratedResponse(
                answer=response.content,
                sources=citation.get_source_list(),
                confidence=confidence,
                metadata={
                    "strategy": "abstractive",
                    "model": self.model_name,
                    "sources_used": len(results),
                    "context_length": TokenCounter.count_tokens(context)
                }
            )
            
        except Exception as e:
            logger.error(f"生成式回答失败: {e}")
            raise
    
    async def _hybrid_generation(self, query: str, results: List[SearchResult],
                               citation_style: CitationStyle) -> GeneratedResponse:
        """混合式生成"""
        try:
            # 先尝试抽取式
            extractive_response = await self._extractive_generation(query, results, citation_style)
            
            # 如果抽取式置信度较低，使用生成式
            if extractive_response.confidence < 0.6:
                abstractive_response = await self._abstractive_generation(query, results, citation_style)
                
                # 选择置信度更高的回答
                if abstractive_response.confidence > extractive_response.confidence:
                    abstractive_response.metadata["strategy"] = "hybrid_abstractive"
                    return abstractive_response
            
            extractive_response.metadata["strategy"] = "hybrid_extractive"
            return extractive_response
            
        except Exception as e:
            logger.error(f"混合式生成失败: {e}")
            raise
    
    def _generate_no_results_response(self, query: str) -> GeneratedResponse:
        """生成无结果响应"""
        return GeneratedResponse(
            answer="抱歉，我在知识库中没有找到与您的问题相关的信息。请尝试使用不同的关键词重新提问，或者联系管理员添加相关内容。",
            sources=[],
            confidence=0.0,
            metadata={
                "strategy": "no_results",
                "query": query
            }
        )
    
    def _calculate_confidence(self, results: List[SearchResult], answer: str) -> float:
        """计算置信度"""
        try:
            if not results:
                return 0.0
            
            # 基于多个因素计算置信度
            factors = []
            
            # 1. 最高相似度分数
            max_score = max(result.score for result in results)
            factors.append(min(max_score, 1.0))
            
            # 2. 结果数量（更多结果通常意味着更高置信度）
            result_count_factor = min(len(results) / 5.0, 1.0)
            factors.append(result_count_factor)
            
            # 3. 答案长度（太短或太长的答案置信度较低）
            answer_length = len(answer)
            if 50 <= answer_length <= 1000:
                length_factor = 1.0
            elif answer_length < 50:
                length_factor = answer_length / 50.0
            else:
                length_factor = max(0.5, 1000.0 / answer_length)
            factors.append(length_factor)
            
            # 4. 引用数量
            citation_count = answer.count('[') + answer.count('(')
            citation_factor = min(citation_count / len(results), 1.0)
            factors.append(citation_factor)
            
            # 加权平均
            weights = [0.4, 0.2, 0.2, 0.2]
            confidence = sum(f * w for f, w in zip(factors, weights))
            
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"置信度计算失败: {e}")
            return 0.5
    
    async def generate_summary(self, documents: List[SearchResult], 
                             max_length: int = 500) -> GeneratedResponse:
        """生成文档摘要"""
        try:
            if not documents:
                return GeneratedResponse(
                    answer="没有文档可以摘要。",
                    confidence=0.0
                )
            
            # 合并文档内容
            combined_content = "\n\n".join([doc.document.content for doc in documents])
            
            # 截断内容
            if TokenCounter.count_tokens(combined_content) > self.max_context_length:
                combined_content = TokenCounter.truncate_text(combined_content, self.max_context_length)
            
            prompt = f"""
请为以下文档内容生成一个简洁的摘要，长度不超过{max_length}字。

文档内容：
{combined_content}

要求：
1. 提取主要观点和关键信息
2. 保持逻辑清晰
3. 语言简洁明了
4. 长度控制在{max_length}字以内

摘要：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model_name,
                temperature=0.5,
                max_tokens=max_length * 2
            )
            
            return GeneratedResponse(
                answer=response.content,
                sources=[],
                confidence=0.8,
                metadata={
                    "strategy": "summary",
                    "document_count": len(documents),
                    "max_length": max_length
                }
            )
            
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return GeneratedResponse(
                answer="摘要生成失败。",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def answer_with_context(self, query: str, context: str,
                                 additional_instructions: str = "") -> GeneratedResponse:
        """基于给定上下文回答问题"""
        try:
            prompt = f"""
基于以下上下文回答问题。

问题：{query}

上下文：
{context}

{additional_instructions}

请提供准确、有用的回答：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model=self.model_name,
                temperature=0.7,
                max_tokens=1000
            )
            
            return GeneratedResponse(
                answer=response.content,
                sources=[],
                confidence=0.7,
                metadata={
                    "strategy": "context_based",
                    "context_length": len(context)
                }
            )
            
        except Exception as e:
            logger.error(f"基于上下文回答失败: {e}")
            return GeneratedResponse(
                answer="回答生成失败。",
                confidence=0.0,
                metadata={"error": str(e)}
            )
