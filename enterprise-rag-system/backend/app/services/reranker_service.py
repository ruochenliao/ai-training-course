"""
重排模型服务
"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

import httpx
from app.core.config import settings
from loguru import logger

from app.core.exceptions import AIServiceException


@dataclass
class RerankRequest:
    """重排请求"""
    query: str
    documents: List[str]
    model: str = "gte-rerank"
    top_k: Optional[int] = None
    return_documents: bool = True


@dataclass
class RerankResult:
    """重排结果"""
    index: int
    relevance_score: float
    document: Optional[str] = None


@dataclass
class RerankResponse:
    """重排响应"""
    results: List[RerankResult]
    model: str
    usage: Dict[str, int]


class RerankerService:
    """重排模型服务类"""
    
    def __init__(self):
        self.api_base = settings.RERANKER_API_BASE
        self.api_key = settings.RERANKER_API_KEY
        self.model_name = settings.RERANKER_MODEL_NAME
        
        # HTTP客户端配置
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self.limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        
        # 批处理配置
        self.max_batch_size = 100
        self.max_query_length = 512
        self.max_document_length = 2048
    
    async def rerank(
        self, 
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
        model: str = None,
        return_documents: bool = True
    ) -> List[RerankResult]:
        """重排文档"""
        try:
            # 预处理
            processed_query = self._preprocess_query(query)
            processed_documents = self._preprocess_documents(documents)
            
            # 批处理
            all_results = []
            for batch_start in range(0, len(processed_documents), self.max_batch_size):
                batch_end = min(batch_start + self.max_batch_size, len(processed_documents))
                batch_documents = processed_documents[batch_start:batch_end]
                
                batch_results = await self._rerank_batch(
                    processed_query,
                    batch_documents,
                    model,
                    return_documents
                )
                
                # 调整索引
                for result in batch_results:
                    result.index += batch_start
                
                all_results.extend(batch_results)
            
            # 按相关性分数排序
            all_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # 应用top_k限制
            if top_k:
                all_results = all_results[:top_k]
            
            return all_results
            
        except Exception as e:
            logger.error(f"文档重排失败: {e}")
            raise AIServiceException(f"文档重排失败: {e}")
    
    async def _rerank_batch(
        self,
        query: str,
        documents: List[str],
        model: str = None,
        return_documents: bool = True
    ) -> List[RerankResult]:
        """批量重排"""
        try:
            request_data = {
                "model": model or self.model_name,
                "query": query,
                "documents": documents,
                "return_documents": return_documents
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
                response = await client.post(
                    f"{self.api_base}/rerank",
                    json=request_data,
                    headers=headers
                )
                
                if response.status_code != 200:
                    error_msg = f"重排API错误: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise AIServiceException(error_msg)
                
                result = response.json()
                
                # 解析结果
                rerank_results = []
                for item in result["results"]:
                    rerank_result = RerankResult(
                        index=item["index"],
                        relevance_score=item["relevance_score"],
                        document=item.get("document") if return_documents else None
                    )
                    rerank_results.append(rerank_result)
                
                return rerank_results
                
        except Exception as e:
            logger.error(f"批量重排失败: {e}")
            raise AIServiceException(f"批量重排失败: {e}")
    
    def _preprocess_query(self, query: str) -> str:
        """预处理查询"""
        # 清理和截断查询
        cleaned_query = query.strip()
        
        if len(cleaned_query) > self.max_query_length:
            cleaned_query = cleaned_query[:self.max_query_length]
            logger.warning(f"查询被截断到 {self.max_query_length} 字符")
        
        return cleaned_query
    
    def _preprocess_documents(self, documents: List[str]) -> List[str]:
        """预处理文档"""
        processed = []
        
        for doc in documents:
            # 清理文档
            cleaned_doc = doc.strip()
            
            # 截断过长的文档
            if len(cleaned_doc) > self.max_document_length:
                cleaned_doc = cleaned_doc[:self.max_document_length]
                logger.warning(f"文档被截断到 {self.max_document_length} 字符")
            
            # 跳过空文档
            if not cleaned_doc:
                cleaned_doc = " "  # 用空格替代空文档
            
            processed.append(cleaned_doc)
        
        return processed
    
    async def rerank_with_metadata(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        content_field: str = "content",
        top_k: Optional[int] = None,
        model: str = None
    ) -> List[Dict[str, Any]]:
        """带元数据的重排"""
        try:
            # 提取文档内容
            doc_contents = []
            for doc in documents:
                content = doc.get(content_field, "")
                doc_contents.append(str(content))
            
            # 执行重排
            rerank_results = await self.rerank(
                query=query,
                documents=doc_contents,
                top_k=top_k,
                model=model,
                return_documents=False
            )
            
            # 组合结果和元数据
            ranked_documents = []
            for result in rerank_results:
                original_doc = documents[result.index].copy()
                original_doc["relevance_score"] = result.relevance_score
                original_doc["rerank_index"] = result.index
                ranked_documents.append(original_doc)
            
            return ranked_documents
            
        except Exception as e:
            logger.error(f"带元数据重排失败: {e}")
            raise AIServiceException(f"带元数据重排失败: {e}")
    
    async def compute_relevance_scores(
        self,
        query: str,
        documents: List[str],
        model: str = None
    ) -> List[float]:
        """计算相关性分数"""
        try:
            rerank_results = await self.rerank(
                query=query,
                documents=documents,
                model=model,
                return_documents=False
            )
            
            # 创建分数列表（保持原始顺序）
            scores = [0.0] * len(documents)
            for result in rerank_results:
                scores[result.index] = result.relevance_score
            
            return scores
            
        except Exception as e:
            logger.error(f"计算相关性分数失败: {e}")
            raise AIServiceException(f"计算相关性分数失败: {e}")
    
    async def filter_by_relevance(
        self,
        query: str,
        documents: List[str],
        threshold: float = 0.5,
        model: str = None
    ) -> List[Tuple[int, str, float]]:
        """按相关性过滤文档"""
        try:
            rerank_results = await self.rerank(
                query=query,
                documents=documents,
                model=model,
                return_documents=True
            )
            
            # 过滤低相关性文档
            filtered_results = []
            for result in rerank_results:
                if result.relevance_score >= threshold:
                    filtered_results.append((
                        result.index,
                        result.document or documents[result.index],
                        result.relevance_score
                    ))
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"按相关性过滤失败: {e}")
            raise AIServiceException(f"按相关性过滤失败: {e}")
    
    async def compare_documents(
        self,
        query: str,
        doc1: str,
        doc2: str,
        model: str = None
    ) -> Dict[str, Any]:
        """比较两个文档的相关性"""
        try:
            documents = [doc1, doc2]
            rerank_results = await self.rerank(
                query=query,
                documents=documents,
                model=model,
                return_documents=False
            )
            
            # 组织比较结果
            scores = {0: 0.0, 1: 0.0}
            for result in rerank_results:
                scores[result.index] = result.relevance_score
            
            return {
                "doc1_score": scores[0],
                "doc2_score": scores[1],
                "winner": "doc1" if scores[0] > scores[1] else "doc2",
                "score_difference": abs(scores[0] - scores[1])
            }
            
        except Exception as e:
            logger.error(f"文档比较失败: {e}")
            raise AIServiceException(f"文档比较失败: {e}")
    
    async def batch_rerank_queries(
        self,
        queries: List[str],
        documents: List[str],
        top_k: Optional[int] = None,
        model: str = None
    ) -> Dict[str, List[RerankResult]]:
        """批量查询重排"""
        try:
            results = {}
            
            # 并发处理多个查询
            tasks = []
            for query in queries:
                task = self.rerank(
                    query=query,
                    documents=documents,
                    top_k=top_k,
                    model=model,
                    return_documents=False
                )
                tasks.append(task)
            
            # 等待所有任务完成
            all_results = await asyncio.gather(*tasks)
            
            # 组织结果
            for i, query in enumerate(queries):
                results[query] = all_results[i]
            
            return results
            
        except Exception as e:
            logger.error(f"批量查询重排失败: {e}")
            raise AIServiceException(f"批量查询重排失败: {e}")
    
    async def check_model_health(self) -> Dict[str, Any]:
        """检查模型健康状态"""
        try:
            test_query = "What is artificial intelligence?"
            test_documents = [
                "Artificial intelligence is a branch of computer science.",
                "Machine learning is a subset of AI.",
                "The weather is nice today."
            ]
            
            start_time = asyncio.get_event_loop().time()
            results = await self.rerank(
                query=test_query,
                documents=test_documents,
                return_documents=False
            )
            end_time = asyncio.get_event_loop().time()
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "response_time": end_time - start_time,
                "test_results_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"重排模型健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "max_batch_size": self.max_batch_size,
            "max_query_length": self.max_query_length,
            "max_document_length": self.max_document_length,
            "api_base": self.api_base
        }


# 全局重排服务实例
reranker_service = RerankerService()
