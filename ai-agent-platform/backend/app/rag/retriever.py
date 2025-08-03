"""
文档检索器

负责查询扩展、文档检索和结果重排序。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import json
import re
from datetime import datetime

from .vectorstore import VectorStore, SearchResult, Document
from .embeddings import embedding_manager
from ..agents.llm_interface import llm_manager

logger = logging.getLogger(__name__)


class QueryExpander:
    """查询扩展器"""
    
    def __init__(self):
        self.expansion_cache: Dict[str, List[str]] = {}
    
    async def expand_query(self, query: str, max_expansions: int = 3) -> List[str]:
        """扩展查询"""
        try:
            # 检查缓存
            if query in self.expansion_cache:
                return self.expansion_cache[query]
            
            # 使用LLM生成查询扩展
            prompt = f"""
请为以下查询生成{max_expansions}个相关的扩展查询，用于提高搜索召回率。

原始查询：{query}

要求：
1. 扩展查询应该与原始查询语义相关
2. 使用不同的表达方式和同义词
3. 考虑用户可能的不同表达习惯
4. 返回JSON数组格式：["扩展查询1", "扩展查询2", "扩展查询3"]

扩展查询：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model="gpt-4o",
                temperature=0.7,
                max_tokens=500
            )
            
            try:
                expansions = json.loads(response.content)
                if isinstance(expansions, list):
                    # 添加原始查询
                    all_queries = [query] + expansions[:max_expansions]
                    self.expansion_cache[query] = all_queries
                    return all_queries
            except json.JSONDecodeError:
                pass
            
            # 如果解析失败，返回原始查询
            return [query]
            
        except Exception as e:
            logger.error(f"查询扩展失败: {e}")
            return [query]
    
    async def extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        try:
            prompt = f"""
请从以下查询中提取关键词，用于搜索过滤。

查询：{query}

要求：
1. 提取最重要的名词、动词和形容词
2. 去除停用词
3. 返回JSON数组格式：["关键词1", "关键词2", "关键词3"]

关键词：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model="gpt-4o",
                temperature=0.3,
                max_tokens=200
            )
            
            try:
                keywords = json.loads(response.content)
                if isinstance(keywords, list):
                    return keywords
            except json.JSONDecodeError:
                pass
            
            # 简单的关键词提取
            words = re.findall(r'\w+', query)
            return [word for word in words if len(word) > 2]
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []


class Reranker:
    """重排序器"""

    def __init__(self):
        pass

    async def rerank(self, query: str, results: List[SearchResult],
                    top_k: int = 10) -> List[SearchResult]:
        """重排序搜索结果"""
        try:
            if len(results) <= top_k:
                return results

            # 优先使用BGE重排模型
            if embedding_manager.has_reranker():
                reranked_results = await self._bge_rerank(query, results, top_k)
                if reranked_results:
                    return reranked_results

            # 如果BGE重排失败，使用LLM进行重排序
            reranked_results = await self._llm_rerank(query, results, top_k)

            # 如果LLM重排序失败，使用基于规则的重排序
            if not reranked_results:
                reranked_results = self._rule_based_rerank(query, results, top_k)

            return reranked_results

        except Exception as e:
            logger.error(f"重排序失败: {e}")
            return results[:top_k]

    async def _bge_rerank(self, query: str, results: List[SearchResult],
                         top_k: int) -> List[SearchResult]:
        """使用BGE重排模型重排序"""
        try:
            # 提取文档内容
            documents = [result.document.content for result in results]

            # 使用BGE重排模型
            reranked_indices = await embedding_manager.rerank_documents(query, documents, top_k)

            # 构建重排后的结果
            reranked_results = []
            for rank, (original_idx, rerank_score) in enumerate(reranked_indices):
                if 0 <= original_idx < len(results):
                    result = results[original_idx]
                    result.rank = rank + 1
                    result.rerank_score = rerank_score  # 添加重排分数
                    reranked_results.append(result)

            logger.info(f"✅ BGE重排完成，返回{len(reranked_results)}个结果")
            return reranked_results

        except Exception as e:
            logger.error(f"BGE重排失败: {e}")
            return []
    
    async def _llm_rerank(self, query: str, results: List[SearchResult], 
                         top_k: int) -> List[SearchResult]:
        """使用LLM重排序"""
        try:
            # 准备候选文档
            candidates = []
            for i, result in enumerate(results):
                candidates.append({
                    "index": i,
                    "content": result.document.content[:500],  # 截断长文本
                    "score": result.score
                })
            
            prompt = f"""
请根据查询的相关性对以下文档进行重排序。

查询：{query}

候选文档：
{json.dumps(candidates, ensure_ascii=False, indent=2)}

要求：
1. 根据文档与查询的相关性进行排序
2. 考虑文档的质量和完整性
3. 返回前{top_k}个最相关的文档索引
4. 返回JSON数组格式：[0, 3, 1, 2, ...]

重排序结果：
"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                model="gpt-4o",
                temperature=0.3,
                max_tokens=200
            )
            
            try:
                indices = json.loads(response.content)
                if isinstance(indices, list):
                    reranked_results = []
                    for rank, idx in enumerate(indices[:top_k]):
                        if 0 <= idx < len(results):
                            result = results[idx]
                            result.rank = rank + 1
                            reranked_results.append(result)
                    return reranked_results
            except (json.JSONDecodeError, IndexError):
                pass
            
            return []
            
        except Exception as e:
            logger.error(f"LLM重排序失败: {e}")
            return []
    
    def _rule_based_rerank(self, query: str, results: List[SearchResult], 
                          top_k: int) -> List[SearchResult]:
        """基于规则的重排序"""
        try:
            # 提取查询关键词
            query_words = set(re.findall(r'\w+', query.lower()))
            
            # 计算增强分数
            for result in results:
                content_words = set(re.findall(r'\w+', result.document.content.lower()))
                
                # 关键词匹配度
                keyword_match = len(query_words & content_words) / len(query_words) if query_words else 0
                
                # 文档长度惩罚（太短或太长的文档）
                content_length = len(result.document.content)
                length_penalty = 1.0
                if content_length < 50:
                    length_penalty = 0.5
                elif content_length > 2000:
                    length_penalty = 0.8
                
                # 元数据加权
                metadata_boost = 1.0
                if result.document.metadata.get("title"):
                    metadata_boost += 0.1
                if result.document.metadata.get("summary"):
                    metadata_boost += 0.1
                
                # 计算最终分数
                enhanced_score = (
                    result.score * 0.7 +
                    keyword_match * 0.2 +
                    length_penalty * 0.1
                ) * metadata_boost
                
                result.score = enhanced_score
            
            # 按增强分数排序
            sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
            
            # 更新排名
            for rank, result in enumerate(sorted_results[:top_k]):
                result.rank = rank + 1
            
            return sorted_results[:top_k]
            
        except Exception as e:
            logger.error(f"规则重排序失败: {e}")
            return results[:top_k]


class DocumentRetriever:
    """文档检索器"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.query_expander = QueryExpander()
        self.reranker = Reranker()
    
    async def retrieve(self, query: str, top_k: int = 10, 
                      expand_query: bool = True, rerank: bool = True,
                      filters: Dict[str, Any] = None) -> List[SearchResult]:
        """检索文档"""
        try:
            # 查询扩展
            queries = [query]
            if expand_query:
                queries = await self.query_expander.expand_query(query, max_expansions=2)
            
            # 多查询检索
            all_results = []
            for q in queries:
                # 生成查询嵌入
                query_embedding = await embedding_manager.embed_text(q)
                
                # 检索文档
                results = await self.vector_store.search(
                    query_embedding=query_embedding,
                    top_k=top_k * 2,  # 检索更多候选文档
                    filters=filters
                )
                
                all_results.extend(results)
            
            # 去重（基于文档ID）
            unique_results = {}
            for result in all_results:
                doc_id = result.document.id
                if doc_id not in unique_results or result.score > unique_results[doc_id].score:
                    unique_results[doc_id] = result
            
            results = list(unique_results.values())
            
            # 重排序
            if rerank and len(results) > top_k:
                results = await self.reranker.rerank(query, results, top_k)
            else:
                # 简单排序
                results = sorted(results, key=lambda x: x.score, reverse=True)[:top_k]
                for rank, result in enumerate(results):
                    result.rank = rank + 1
            
            logger.info(f"检索完成: 查询='{query}', 结果数={len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"文档检索失败: {e}")
            return []
    
    async def hybrid_retrieve(self, query: str, top_k: int = 10,
                             vector_weight: float = 0.7, keyword_weight: float = 0.3,
                             filters: Dict[str, Any] = None) -> List[SearchResult]:
        """混合检索（向量+关键词）"""
        try:
            # 向量检索
            vector_results = await self.retrieve(
                query=query,
                top_k=top_k * 2,
                expand_query=True,
                rerank=False,
                filters=filters
            )
            
            # 关键词检索（简单实现）
            keyword_results = await self._keyword_search(query, top_k * 2, filters)
            
            # 合并结果
            combined_results = self._combine_results(
                vector_results, keyword_results,
                vector_weight, keyword_weight
            )
            
            # 重排序
            final_results = await self.reranker.rerank(query, combined_results, top_k)
            
            return final_results
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return await self.retrieve(query, top_k, filters=filters)
    
    async def _keyword_search(self, query: str, top_k: int,
                             filters: Dict[str, Any] = None) -> List[SearchResult]:
        """关键词搜索"""
        try:
            # 提取关键词
            keywords = await self.query_expander.extract_keywords(query)
            
            # 简单的关键词匹配（在实际应用中可以使用更复杂的全文搜索）
            # 这里我们通过向量存储的元数据进行过滤
            results = []
            
            # 获取所有文档（这里简化处理，实际应该有专门的关键词索引）
            # 由于我们的向量存储接口限制，这里返回空结果
            # 在实际应用中，应该集成Elasticsearch等全文搜索引擎
            
            return results
            
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return []
    
    def _combine_results(self, vector_results: List[SearchResult], 
                        keyword_results: List[SearchResult],
                        vector_weight: float, keyword_weight: float) -> List[SearchResult]:
        """合并检索结果"""
        try:
            # 创建文档ID到结果的映射
            combined = {}
            
            # 添加向量检索结果
            for result in vector_results:
                doc_id = result.document.id
                combined[doc_id] = SearchResult(
                    document=result.document,
                    score=result.score * vector_weight,
                    rank=0
                )
            
            # 添加关键词检索结果
            for result in keyword_results:
                doc_id = result.document.id
                if doc_id in combined:
                    # 合并分数
                    combined[doc_id].score += result.score * keyword_weight
                else:
                    combined[doc_id] = SearchResult(
                        document=result.document,
                        score=result.score * keyword_weight,
                        rank=0
                    )
            
            # 排序并返回
            results = list(combined.values())
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"结果合并失败: {e}")
            return vector_results
    
    async def get_similar_documents(self, doc_id: str, top_k: int = 5) -> List[SearchResult]:
        """获取相似文档"""
        try:
            # 获取原文档
            document = await self.vector_store.get_document(doc_id)
            if not document or not document.embedding:
                return []
            
            # 使用文档的嵌入进行搜索
            results = await self.vector_store.search(
                query_embedding=document.embedding,
                top_k=top_k + 1  # +1 因为会包含原文档
            )
            
            # 过滤掉原文档
            similar_results = [r for r in results if r.document.id != doc_id]
            
            return similar_results[:top_k]
            
        except Exception as e:
            logger.error(f"获取相似文档失败: {e}")
            return []
    
    async def search_by_metadata(self, filters: Dict[str, Any], 
                                top_k: int = 10) -> List[SearchResult]:
        """基于元数据搜索"""
        try:
            # 这里需要向量存储支持元数据过滤
            # 由于我们的接口限制，这里简化实现
            results = []
            
            # 在实际应用中，应该在向量存储层面支持元数据过滤
            logger.info(f"元数据搜索: {filters}")
            
            return results
            
        except Exception as e:
            logger.error(f"元数据搜索失败: {e}")
            return []
