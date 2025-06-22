"""
搜索建议服务
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 移除 get_database 导入，使用 Tortoise ORM
from app.services.cache_service import cache_service
from app.services.embedding_service import embedding_service
from loguru import logger

from app.core.exceptions import SearchException


@dataclass
class SearchSuggestion:
    """搜索建议"""
    text: str
    score: float
    type: str  # "query", "completion", "correction", "related"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    original_query: str
    cleaned_query: str
    tokens: List[str]
    intent: str
    entities: List[str]
    language: str
    confidence: float


class SearchSuggestionService:
    """搜索建议服务类"""
    
    def __init__(self):
        """初始化搜索建议服务"""
        # 使用 Tortoise ORM，不需要数据库连接池
        
        # 查询历史缓存
        self.query_history = defaultdict(int)
        self.query_patterns = {}
        
        # 停用词列表
        self.stop_words = {
            "zh": {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"},
            "en": {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "up", "about", "into", "through", "during", "before", "after", "above", "below", "between", "among", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "this", "that", "these", "those"}
        }
        
        # 常见查询模板
        self.query_templates = [
            "什么是{entity}",
            "如何{action}",
            "{entity}的{attribute}是什么",
            "{entity}和{entity2}的区别",
            "怎样{action}{entity}",
            "{entity}有什么{attribute}",
            "为什么{entity}",
            "{entity}的作用",
            "{entity}的优缺点"
        ]
        
        logger.info("搜索建议服务初始化完成")
    
    async def get_suggestions(
        self,
        query: str,
        knowledge_base_id: Optional[int] = None,
        max_suggestions: int = 10,
        suggestion_types: List[str] = None
    ) -> List[SearchSuggestion]:
        """获取搜索建议"""
        try:
            if not query.strip():
                return []
            
            if suggestion_types is None:
                suggestion_types = ["completion", "correction", "related", "popular"]
            
            # 分析查询
            analysis = await self._analyze_query(query)
            
            # 获取各类型建议
            all_suggestions = []
            
            if "completion" in suggestion_types:
                completions = await self._get_query_completions(query, knowledge_base_id)
                all_suggestions.extend(completions)
            
            if "correction" in suggestion_types:
                corrections = await self._get_query_corrections(query, analysis)
                all_suggestions.extend(corrections)
            
            if "related" in suggestion_types:
                related = await self._get_related_queries(query, analysis, knowledge_base_id)
                all_suggestions.extend(related)
            
            if "popular" in suggestion_types:
                popular = await self._get_popular_queries(query, knowledge_base_id)
                all_suggestions.extend(popular)
            
            # 去重和排序
            unique_suggestions = self._deduplicate_suggestions(all_suggestions)
            sorted_suggestions = sorted(unique_suggestions, key=lambda x: x.score, reverse=True)
            
            return sorted_suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}")
            return []
    
    async def get_query_completions(
        self,
        partial_query: str,
        knowledge_base_id: Optional[int] = None,
        max_completions: int = 5
    ) -> List[SearchSuggestion]:
        """获取查询自动完成建议"""
        try:
            if len(partial_query.strip()) < 2:
                return []
            
            # 从缓存获取
            cache_key = f"completions:{partial_query}:{knowledge_base_id}"
            cached_result = await cache_service.get(cache_key, "search_suggestions")
            if cached_result:
                return [SearchSuggestion(**item) for item in cached_result]
            
            completions = []
            
            # 基于历史查询的完成
            history_completions = await self._get_history_completions(partial_query, knowledge_base_id)
            completions.extend(history_completions)
            
            # 基于文档内容的完成
            content_completions = await self._get_content_completions(partial_query, knowledge_base_id)
            completions.extend(content_completions)
            
            # 基于模板的完成
            template_completions = await self._get_template_completions(partial_query)
            completions.extend(template_completions)
            
            # 去重和排序
            unique_completions = self._deduplicate_suggestions(completions)
            sorted_completions = sorted(unique_completions, key=lambda x: x.score, reverse=True)
            
            result = sorted_completions[:max_completions]
            
            # 缓存结果
            cache_data = [suggestion.__dict__ for suggestion in result]
            await cache_service.set(cache_key, cache_data, "search_suggestions", ttl=3600)
            
            return result
            
        except Exception as e:
            logger.error(f"获取查询完成建议失败: {e}")
            return []
    
    async def record_search_query(
        self,
        query: str,
        knowledge_base_id: Optional[int] = None,
        user_id: Optional[int] = None,
        results_count: int = 0,
        clicked_results: List[str] = None
    ):
        """记录搜索查询"""
        try:
            if clicked_results is None:
                clicked_results = []
            
            # 存储到数据库
            query_record = {
                "query": query.strip(),
                "knowledge_base_id": knowledge_base_id,
                "user_id": user_id,
                "results_count": results_count,
                "clicked_results": clicked_results,
                "timestamp": datetime.now()
            }
            
            # 这里应该存储到数据库
            # await self._store_query_record(query_record)
            
            # 更新内存中的查询历史
            self.query_history[query.strip().lower()] += 1
            
            # 分析查询模式
            await self._analyze_query_patterns(query, knowledge_base_id)
            
        except Exception as e:
            logger.error(f"记录搜索查询失败: {e}")
    
    async def get_trending_queries(
        self,
        knowledge_base_id: Optional[int] = None,
        time_range: str = "24h",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取热门查询"""
        try:
            # 计算时间范围
            if time_range == "1h":
                start_time = datetime.now() - timedelta(hours=1)
            elif time_range == "24h":
                start_time = datetime.now() - timedelta(days=1)
            elif time_range == "7d":
                start_time = datetime.now() - timedelta(days=7)
            else:
                start_time = datetime.now() - timedelta(days=1)
            
            # 从数据库获取热门查询
            # 这里应该实现真实的数据库查询
            # 目前返回模拟数据
            trending_queries = [
                {"query": "人工智能", "count": 156, "growth": 23.5},
                {"query": "机器学习", "count": 134, "growth": 18.2},
                {"query": "深度学习", "count": 98, "growth": 15.7},
                {"query": "自然语言处理", "count": 87, "growth": 12.3},
                {"query": "计算机视觉", "count": 76, "growth": 9.8}
            ]
            
            return trending_queries[:limit]
            
        except Exception as e:
            logger.error(f"获取热门查询失败: {e}")
            return []
    
    async def get_query_suggestions_for_empty_results(
        self,
        original_query: str,
        knowledge_base_id: Optional[int] = None
    ) -> List[SearchSuggestion]:
        """为无结果查询提供建议"""
        try:
            suggestions = []
            
            # 查询纠错建议
            analysis = await self._analyze_query(original_query)
            corrections = await self._get_query_corrections(original_query, analysis)
            suggestions.extend(corrections)
            
            # 相关查询建议
            related = await self._get_related_queries(original_query, analysis, knowledge_base_id)
            suggestions.extend(related)
            
            # 简化查询建议
            simplified = await self._get_simplified_queries(original_query, analysis)
            suggestions.extend(simplified)
            
            # 扩展查询建议
            expanded = await self._get_expanded_queries(original_query, analysis)
            suggestions.extend(expanded)
            
            return sorted(suggestions, key=lambda x: x.score, reverse=True)[:10]
            
        except Exception as e:
            logger.error(f"获取无结果查询建议失败: {e}")
            return []
    
    # 私有辅助方法
    async def _analyze_query(self, query: str) -> QueryAnalysis:
        """分析查询"""
        try:
            cleaned_query = self._clean_query(query)
            tokens = self._tokenize_query(cleaned_query)
            language = self._detect_language(query)
            entities = await self._extract_entities(query)
            intent = await self._classify_intent(query, tokens)
            
            return QueryAnalysis(
                original_query=query,
                cleaned_query=cleaned_query,
                tokens=tokens,
                intent=intent,
                entities=entities,
                language=language,
                confidence=0.8  # 简化的置信度
            )
            
        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            return QueryAnalysis(
                original_query=query,
                cleaned_query=query,
                tokens=[query],
                intent="unknown",
                entities=[],
                language="zh",
                confidence=0.5
            )
    
    def _clean_query(self, query: str) -> str:
        """清理查询"""
        # 移除特殊字符，保留中文、英文、数字和空格
        cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', query)
        # 移除多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _tokenize_query(self, query: str) -> List[str]:
        """分词"""
        # 简单的分词实现
        # 实际应用中应该使用专业的分词工具
        tokens = []
        
        # 英文分词
        english_tokens = re.findall(r'[a-zA-Z]+', query)
        tokens.extend(english_tokens)
        
        # 中文分词（简化版）
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]+', query)
        for chars in chinese_chars:
            # 这里应该使用jieba等分词工具
            tokens.append(chars)
        
        # 数字
        numbers = re.findall(r'\d+', query)
        tokens.extend(numbers)
        
        return [token.lower() for token in tokens if len(token) > 1]
    
    def _detect_language(self, query: str) -> str:
        """检测语言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', query))
        english_chars = len(re.findall(r'[a-zA-Z]', query))
        
        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > 0:
            return "en"
        else:
            return "zh"  # 默认中文
    
    async def _extract_entities(self, query: str) -> List[str]:
        """提取实体"""
        # 简化的实体提取
        # 实际应用中应该使用NER模型
        entities = []
        
        # 常见技术实体
        tech_entities = [
            "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理",
            "计算机视觉", "数据挖掘", "大数据", "云计算", "区块链"
        ]
        
        for entity in tech_entities:
            if entity in query:
                entities.append(entity)
        
        return entities
    
    async def _classify_intent(self, query: str, tokens: List[str]) -> str:
        """分类查询意图"""
        # 简化的意图分类
        if any(word in query for word in ["什么是", "什么", "定义", "含义"]):
            return "definition"
        elif any(word in query for word in ["如何", "怎么", "怎样", "方法"]):
            return "how_to"
        elif any(word in query for word in ["为什么", "原因", "why"]):
            return "explanation"
        elif any(word in query for word in ["比较", "区别", "不同", "差异"]):
            return "comparison"
        elif any(word in query for word in ["优缺点", "优势", "缺点", "好处"]):
            return "evaluation"
        else:
            return "general"
    
    async def _get_query_completions(
        self,
        query: str,
        knowledge_base_id: Optional[int]
    ) -> List[SearchSuggestion]:
        """获取查询完成建议"""
        completions = []
        
        # 基于历史查询
        for hist_query, count in self.query_history.items():
            if hist_query.startswith(query.lower()) and hist_query != query.lower():
                score = min(count / 100.0, 1.0)  # 归一化分数
                completions.append(SearchSuggestion(
                    text=hist_query,
                    score=score,
                    type="completion",
                    metadata={"source": "history", "count": count}
                ))
        
        return completions
    
    async def _get_query_corrections(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> List[SearchSuggestion]:
        """获取查询纠错建议"""
        corrections = []
        
        # 简单的拼写纠错
        # 实际应用中应该使用专业的拼写检查工具
        common_corrections = {
            "机器学习": ["机器学习", "机器学习算法"],
            "人工智能": ["人工智能", "AI", "artificial intelligence"],
            "深度学习": ["深度学习", "深度神经网络"]
        }
        
        for correct_term, variations in common_corrections.items():
            for variation in variations:
                if self._calculate_similarity(query.lower(), variation.lower()) > 0.7:
                    corrections.append(SearchSuggestion(
                        text=correct_term,
                        score=0.8,
                        type="correction",
                        metadata={"original": query, "reason": "spelling"}
                    ))
        
        return corrections
    
    async def _get_related_queries(
        self,
        query: str,
        analysis: QueryAnalysis,
        knowledge_base_id: Optional[int]
    ) -> List[SearchSuggestion]:
        """获取相关查询建议"""
        related = []
        
        # 基于实体的相关查询
        for entity in analysis.entities:
            related_queries = [
                f"{entity}的应用",
                f"{entity}的原理",
                f"{entity}的发展历史",
                f"{entity}的优缺点"
            ]
            
            for rel_query in related_queries:
                if rel_query.lower() != query.lower():
                    related.append(SearchSuggestion(
                        text=rel_query,
                        score=0.6,
                        type="related",
                        metadata={"entity": entity, "relation": "entity_based"}
                    ))
        
        return related
    
    async def _get_popular_queries(
        self,
        query: str,
        knowledge_base_id: Optional[int]
    ) -> List[SearchSuggestion]:
        """获取热门查询建议"""
        popular = []
        
        # 获取最热门的查询
        top_queries = sorted(
            self.query_history.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        
        for pop_query, count in top_queries:
            if self._calculate_similarity(query.lower(), pop_query) > 0.3:
                score = min(count / 200.0, 1.0)
                popular.append(SearchSuggestion(
                    text=pop_query,
                    score=score,
                    type="popular",
                    metadata={"count": count, "rank": len(popular) + 1}
                ))
        
        return popular[:5]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 简单的Jaccard相似度
        set1 = set(text1.split())
        set2 = set(text2.split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _deduplicate_suggestions(
        self,
        suggestions: List[SearchSuggestion]
    ) -> List[SearchSuggestion]:
        """去重建议"""
        seen = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            text_lower = suggestion.text.lower()
            if text_lower not in seen:
                seen.add(text_lower)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions
    
    async def _get_history_completions(
        self,
        partial_query: str,
        knowledge_base_id: Optional[int]
    ) -> List[SearchSuggestion]:
        """基于历史的完成建议"""
        completions = []
        partial_lower = partial_query.lower()
        
        for query, count in self.query_history.items():
            if query.startswith(partial_lower) and len(query) > len(partial_lower):
                score = min(count / 100.0, 1.0)
                completions.append(SearchSuggestion(
                    text=query,
                    score=score,
                    type="completion",
                    metadata={"source": "history"}
                ))
        
        return completions
    
    async def _get_content_completions(
        self,
        partial_query: str,
        knowledge_base_id: Optional[int]
    ) -> List[SearchSuggestion]:
        """基于内容的完成建议"""
        # 这里应该从文档内容中提取相关的完成建议
        # 目前返回空列表
        return []
    
    async def _get_template_completions(self, partial_query: str) -> List[SearchSuggestion]:
        """基于模板的完成建议"""
        completions = []
        
        for template in self.query_templates:
            # 简单的模板匹配
            if any(word in partial_query for word in template.split()):
                # 这里应该实现更智能的模板填充
                completed = template.replace("{entity}", "相关概念").replace("{action}", "操作").replace("{attribute}", "特性")
                completions.append(SearchSuggestion(
                    text=completed,
                    score=0.4,
                    type="completion",
                    metadata={"source": "template"}
                ))
        
        return completions
    
    async def _get_simplified_queries(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> List[SearchSuggestion]:
        """获取简化查询建议"""
        simplified = []
        
        # 移除修饰词，保留核心概念
        core_tokens = [token for token in analysis.tokens 
                      if token not in self.stop_words.get(analysis.language, set())]
        
        if len(core_tokens) > 1:
            for token in core_tokens:
                simplified.append(SearchSuggestion(
                    text=token,
                    score=0.5,
                    type="simplified",
                    metadata={"original": query}
                ))
        
        return simplified
    
    async def _get_expanded_queries(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> List[SearchSuggestion]:
        """获取扩展查询建议"""
        expanded = []
        
        # 添加常见的扩展词
        expansion_words = ["原理", "应用", "方法", "技术", "系统", "算法"]
        
        for word in expansion_words:
            expanded_query = f"{query} {word}"
            expanded.append(SearchSuggestion(
                text=expanded_query,
                score=0.4,
                type="expanded",
                metadata={"original": query, "expansion": word}
            ))
        
        return expanded
    
    async def _analyze_query_patterns(self, query: str, knowledge_base_id: Optional[int]):
        """分析查询模式"""
        # 分析查询的时间模式、用户模式等
        # 用于优化建议算法
        pass


# 全局搜索建议服务实例
search_suggestion_service = SearchSuggestionService()
