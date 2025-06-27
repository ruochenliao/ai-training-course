"""
基于bge-reranker-v2-m3的重排序服务 - 企业级RAG系统
严格按照技术栈要求：bge-reranker-v2-m3 (BAAI/bge-reranker-v2-m3)
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import torch
from FlagEmbedding import FlagReranker
from app.core.config import settings
from loguru import logger


class BGERerankerService:
    """BGE Reranker v2-m3 重排序服务"""
    
    def __init__(self):
        self.reranker = None
        self.model_name = "BAAI/bge-reranker-v2-m3"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_length = 8192  # 最大输入长度
        self.batch_size = 16  # 批处理大小
        self._initialized = False
    
    async def initialize(self):
        """初始化BGE Reranker模型"""
        if self._initialized:
            return
        
        try:
            logger.info("正在初始化BGE Reranker v2-m3模型...")
            
            # 在线程池中加载模型，避免阻塞
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model)
            
            self._initialized = True
            logger.info(f"BGE Reranker模型初始化完成 (设备: {self.device})")
            
        except Exception as e:
            logger.error(f"BGE Reranker模型初始化失败: {e}")
            raise
    
    def _load_model(self):
        """同步加载模型"""
        try:
            # 加载BGE Reranker模型
            self.reranker = FlagReranker(
                self.model_name,
                use_fp16=True if self.device == "cuda" else False,
                cache_dir=settings.MODELSCOPE_CACHE_DIR
            )
            
            logger.info("BGE Reranker模型加载完成")
            
        except Exception as e:
            logger.error(f"BGE Reranker模型加载失败: {e}")
            raise
    
    def _preprocess_query_passage_pair(self, query: str, passage: str) -> Tuple[str, str]:
        """预处理查询和段落对"""
        # 清理文本
        query = query.strip()
        passage = passage.strip()
        
        # 截断过长的文本
        if len(query) > 512:  # 查询通常较短
            query = query[:512]
            logger.warning(f"查询过长，已截断到 {len(query)} 字符")
        
        if len(passage) > self.max_length - len(query) - 100:  # 为特殊token预留空间
            passage = passage[:self.max_length - len(query) - 100]
            logger.warning(f"段落过长，已截断到 {len(passage)} 字符")
        
        return query, passage
    
    async def rerank_single(self, query: str, passage: str) -> float:
        """对单个查询-段落对进行重排序评分"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 预处理文本
            processed_query, processed_passage = self._preprocess_query_passage_pair(query, passage)
            
            # 在线程池中执行重排序
            loop = asyncio.get_event_loop()
            score = await loop.run_in_executor(
                None, 
                self._rerank_sync, 
                [(processed_query, processed_passage)]
            )
            
            return score[0]
            
        except Exception as e:
            logger.error(f"重排序评分失败: {e}")
            return 0.0
    
    async def rerank_batch(self, query: str, passages: List[str]) -> List[float]:
        """批量重排序评分"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # 预处理文本对
            query_passage_pairs = []
            for passage in passages:
                processed_query, processed_passage = self._preprocess_query_passage_pair(query, passage)
                query_passage_pairs.append((processed_query, processed_passage))
            
            # 分批处理
            all_scores = []
            for i in range(0, len(query_passage_pairs), self.batch_size):
                batch_pairs = query_passage_pairs[i:i + self.batch_size]
                
                # 在线程池中执行重排序
                loop = asyncio.get_event_loop()
                batch_scores = await loop.run_in_executor(
                    None, 
                    self._rerank_sync, 
                    batch_pairs
                )
                
                all_scores.extend(batch_scores)
            
            return all_scores
            
        except Exception as e:
            logger.error(f"批量重排序失败: {e}")
            return [0.0] * len(passages)
    
    def _rerank_sync(self, query_passage_pairs: List[Tuple[str, str]]) -> List[float]:
        """同步执行重排序"""
        try:
            # 准备输入格式
            inputs = [[query, passage] for query, passage in query_passage_pairs]
            
            # 执行重排序
            scores = self.reranker.compute_score(inputs, normalize=True)
            
            # 确保返回列表格式
            if isinstance(scores, (int, float)):
                scores = [scores]
            elif isinstance(scores, np.ndarray):
                scores = scores.tolist()
            
            return scores
            
        except Exception as e:
            logger.error(f"同步重排序失败: {e}")
            return [0.0] * len(query_passage_pairs)
    
    async def rerank_and_sort(self, query: str, passages: List[str], top_k: Optional[int] = None) -> List[Tuple[int, str, float]]:
        """重排序并按分数排序"""
        try:
            # 获取重排序分数
            scores = await self.rerank_batch(query, passages)
            
            # 创建 (索引, 段落, 分数) 元组列表
            scored_passages = [(i, passage, score) for i, (passage, score) in enumerate(zip(passages, scores))]
            
            # 按分数降序排序
            scored_passages.sort(key=lambda x: x[2], reverse=True)
            
            # 返回top_k结果
            if top_k is not None:
                scored_passages = scored_passages[:top_k]
            
            return scored_passages
            
        except Exception as e:
            logger.error(f"重排序和排序失败: {e}")
            return [(i, passage, 0.0) for i, passage in enumerate(passages)]
    
    async def filter_by_threshold(self, query: str, passages: List[str], threshold: float = 0.5) -> List[Tuple[int, str, float]]:
        """根据阈值过滤相关段落"""
        try:
            # 获取重排序分数
            scores = await self.rerank_batch(query, passages)
            
            # 过滤低于阈值的结果
            filtered_results = []
            for i, (passage, score) in enumerate(zip(passages, scores)):
                if score >= threshold:
                    filtered_results.append((i, passage, score))
            
            # 按分数降序排序
            filtered_results.sort(key=lambda x: x[2], reverse=True)
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"阈值过滤失败: {e}")
            return []
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "max_length": self.max_length,
            "device": self.device,
            "batch_size": self.batch_size,
            "initialized": self._initialized,
            "supports_normalization": True,
            "score_range": [0.0, 1.0]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            if not self._initialized:
                return {
                    "status": "not_initialized",
                    "message": "模型未初始化"
                }
            
            # 测试重排序
            test_query = "什么是人工智能？"
            test_passage = "人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"
            
            start_time = datetime.now()
            score = await self.rerank_single(test_query, test_passage)
            end_time = datetime.now()
            
            latency = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "message": "模型运行正常",
                "test_score": score,
                "latency_ms": latency,
                "device": self.device
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"健康检查失败: {e}"
            }
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.reranker:
                del self.reranker
            
            # 清理GPU缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self._initialized = False
            logger.info("BGE Reranker服务资源已清理")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")


# 全局重排序服务实例
bge_reranker_service = BGERerankerService()


# 便捷函数
async def rerank_passages(query: str, passages: List[str], top_k: Optional[int] = None) -> List[Tuple[int, str, float]]:
    """重排序段落的便捷函数"""
    return await bge_reranker_service.rerank_and_sort(query, passages, top_k)


async def filter_relevant_passages(query: str, passages: List[str], threshold: float = 0.5) -> List[Tuple[int, str, float]]:
    """过滤相关段落的便捷函数"""
    return await bge_reranker_service.filter_by_threshold(query, passages, threshold)


async def calculate_relevance_score(query: str, passage: str) -> float:
    """计算相关性分数的便捷函数"""
    return await bge_reranker_service.rerank_single(query, passage)


# 重排序服务性能监控
class RerankerMetrics:
    """重排序服务性能指标"""
    
    def __init__(self):
        self.total_requests = 0
        self.total_pairs = 0
        self.total_latency = 0.0
        self.error_count = 0
    
    def record_request(self, pair_count: int, latency_ms: float, success: bool = True):
        """记录请求指标"""
        self.total_requests += 1
        self.total_pairs += pair_count
        self.total_latency += latency_ms
        
        if not success:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self.total_requests == 0:
            return {
                "total_requests": 0,
                "avg_latency_ms": 0,
                "avg_pairs_per_request": 0,
                "error_rate": 0,
                "throughput_pairs_per_second": 0
            }
        
        avg_latency = self.total_latency / self.total_requests
        avg_pairs = self.total_pairs / self.total_requests
        error_rate = self.error_count / self.total_requests
        throughput = self.total_pairs / (self.total_latency / 1000) if self.total_latency > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "avg_latency_ms": avg_latency,
            "avg_pairs_per_request": avg_pairs,
            "error_rate": error_rate,
            "throughput_pairs_per_second": throughput
        }


# 全局指标收集器
reranker_metrics = RerankerMetrics()


# 混合检索结果融合
class HybridSearchFusion:
    """混合检索结果融合器"""
    
    @staticmethod
    async def fuse_results(
        semantic_results: List[Tuple[int, str, float]], 
        bm25_results: List[Tuple[int, str, float]],
        query: str,
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3,
        rerank_top_k: int = 20
    ) -> List[Tuple[int, str, float]]:
        """融合语义检索和BM25检索结果"""
        try:
            # 合并结果并去重
            all_results = {}
            
            # 添加语义检索结果
            for idx, passage, score in semantic_results:
                all_results[idx] = {
                    "passage": passage,
                    "semantic_score": score,
                    "bm25_score": 0.0
                }
            
            # 添加BM25检索结果
            for idx, passage, score in bm25_results:
                if idx in all_results:
                    all_results[idx]["bm25_score"] = score
                else:
                    all_results[idx] = {
                        "passage": passage,
                        "semantic_score": 0.0,
                        "bm25_score": score
                    }
            
            # 计算融合分数
            fused_results = []
            for idx, data in all_results.items():
                fused_score = (
                    semantic_weight * data["semantic_score"] + 
                    bm25_weight * data["bm25_score"]
                )
                fused_results.append((idx, data["passage"], fused_score))
            
            # 按融合分数排序
            fused_results.sort(key=lambda x: x[2], reverse=True)
            
            # 取前rerank_top_k个结果进行重排序
            top_results = fused_results[:rerank_top_k]
            passages_to_rerank = [passage for _, passage, _ in top_results]
            
            # 使用BGE Reranker进行最终重排序
            reranked_results = await rerank_passages(query, passages_to_rerank)
            
            # 映射回原始索引
            final_results = []
            for rerank_idx, passage, rerank_score in reranked_results:
                original_idx = top_results[rerank_idx][0]
                final_results.append((original_idx, passage, rerank_score))
            
            return final_results
            
        except Exception as e:
            logger.error(f"混合检索结果融合失败: {e}")
            # 返回语义检索结果作为备选
            return semantic_results


# 全局融合器实例
hybrid_fusion = HybridSearchFusion()
