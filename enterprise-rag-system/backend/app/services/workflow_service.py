"""
AutoGen工作流协调服务
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, AsyncGenerator

from loguru import logger

from app import (
    QueryContext,
    RetrievalResult,
    query_analyzer,
    vector_retriever,
    graph_retriever,
    result_fusion,
    answer_generator
)
from app.core import WorkflowException


class WorkflowType(Enum):
    """工作流类型"""
    SIMPLE_QA = "simple_qa"  # 简单问答
    COMPLEX_RETRIEVAL = "complex_retrieval"  # 复杂检索
    MULTI_SOURCE = "multi_source"  # 多源融合
    REASONING = "reasoning"  # 推理问答


@dataclass
class WorkflowConfig:
    """工作流配置"""
    workflow_type: WorkflowType
    enable_vector_search: bool = True
    enable_graph_search: bool = True
    enable_result_fusion: bool = True
    max_parallel_tasks: int = 3
    timeout_seconds: int = 30


@dataclass
class WorkflowResult:
    """工作流结果"""
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    confidence_score: float
    processing_time: float


class RAGWorkflowOrchestrator:
    """RAG工作流协调器"""
    
    def __init__(self):
        self.default_config = WorkflowConfig(
            workflow_type=WorkflowType.MULTI_SOURCE,
            enable_vector_search=True,
            enable_graph_search=True,
            enable_result_fusion=True
        )
    
    async def execute_workflow(
        self,
        context: QueryContext,
        config: WorkflowConfig = None
    ) -> WorkflowResult:
        """执行工作流"""
        start_time = asyncio.get_event_loop().time()
        config = config or self.default_config
        
        try:
            logger.info(f"开始执行工作流: {config.workflow_type.value}")
            
            # 1. 查询分析阶段
            analysis_result = await self._execute_query_analysis(context)
            
            # 2. 根据分析结果选择检索策略
            retrieval_strategy = self._determine_retrieval_strategy(
                analysis_result, config
            )
            
            # 3. 执行检索阶段
            retrieval_results = await self._execute_retrieval_phase(
                context, retrieval_strategy, config
            )
            
            # 4. 结果融合阶段
            fusion_result = await self._execute_fusion_phase(
                retrieval_results, config
            )
            
            # 5. 答案生成阶段
            final_answer = await self._execute_generation_phase(
                context, fusion_result
            )
            
            # 6. 计算处理时间
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # 7. 构建最终结果
            workflow_result = WorkflowResult(
                answer=final_answer["answer"],
                sources=final_answer["sources"],
                metadata={
                    **final_answer["metadata"],
                    "analysis_result": analysis_result,
                    "retrieval_strategy": retrieval_strategy,
                    "workflow_type": config.workflow_type.value
                },
                confidence_score=final_answer["confidence_score"],
                processing_time=processing_time
            )
            
            logger.info(f"工作流执行完成，耗时: {processing_time:.2f}秒")
            return workflow_result
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            raise WorkflowException(f"工作流执行失败: {e}")
    
    async def execute_workflow_stream(
        self,
        context: QueryContext,
        config: WorkflowConfig = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流"""
        config = config or self.default_config
        
        try:
            logger.info(f"开始流式执行工作流: {config.workflow_type.value}")
            
            # 发送开始事件
            yield {
                "type": "workflow_start",
                "data": {"workflow_type": config.workflow_type.value}
            }
            
            # 1. 查询分析阶段
            yield {"type": "stage_start", "data": {"stage": "query_analysis"}}
            analysis_result = await self._execute_query_analysis(context)
            yield {
                "type": "stage_complete", 
                "data": {"stage": "query_analysis", "result": analysis_result}
            }
            
            # 2. 确定检索策略
            retrieval_strategy = self._determine_retrieval_strategy(
                analysis_result, config
            )
            yield {
                "type": "strategy_determined",
                "data": {"strategy": retrieval_strategy}
            }
            
            # 3. 执行检索阶段
            yield {"type": "stage_start", "data": {"stage": "retrieval"}}
            retrieval_results = await self._execute_retrieval_phase(
                context, retrieval_strategy, config
            )
            yield {
                "type": "stage_complete",
                "data": {"stage": "retrieval", "result_count": len(retrieval_results)}
            }
            
            # 4. 结果融合阶段
            yield {"type": "stage_start", "data": {"stage": "fusion"}}
            fusion_result = await self._execute_fusion_phase(
                retrieval_results, config
            )
            yield {
                "type": "stage_complete",
                "data": {"stage": "fusion", "final_count": fusion_result.get("final_count", 0)}
            }
            
            # 5. 流式答案生成
            yield {"type": "stage_start", "data": {"stage": "generation"}}
            
            answer_chunks = []
            async for chunk in answer_generator.generate_stream(context, fusion_result):
                answer_chunks.append(chunk)
                yield {
                    "type": "answer_chunk",
                    "data": {"chunk": chunk}
                }
            
            # 6. 发送完成事件
            final_answer = "".join(answer_chunks)
            sources = result_fusion._prepare_sources(fusion_result.get("fused_results", []))
            
            yield {
                "type": "workflow_complete",
                "data": {
                    "answer": final_answer,
                    "sources": sources,
                    "confidence_score": fusion_result.get("fusion_score", 0.0)
                }
            }
            
        except Exception as e:
            logger.error(f"流式工作流执行失败: {e}")
            yield {
                "type": "workflow_error",
                "data": {"error": str(e)}
            }
    
    async def _execute_query_analysis(self, context: QueryContext) -> Dict[str, Any]:
        """执行查询分析"""
        try:
            return await query_analyzer.process(context)
        except Exception as e:
            logger.error(f"查询分析失败: {e}")
            # 返回默认分析结果
            return {
                "intent": "question_answering",
                "query_type": "simple",
                "search_strategy": "hybrid",
                "complexity": "medium"
            }
    
    def _determine_retrieval_strategy(
        self, 
        analysis_result: Dict[str, Any], 
        config: WorkflowConfig
    ) -> Dict[str, bool]:
        """确定检索策略"""
        strategy = {
            "use_vector": config.enable_vector_search,
            "use_graph": config.enable_graph_search,
            "use_parallel": True
        }
        
        # 根据查询分析结果调整策略
        query_type = analysis_result.get("query_type", "simple")
        search_strategy = analysis_result.get("search_strategy", "hybrid")
        
        if query_type == "simple" and search_strategy == "vector":
            strategy["use_graph"] = False
        elif query_type == "complex" and search_strategy == "graph":
            strategy["use_vector"] = False
        
        return strategy
    
    async def _execute_retrieval_phase(
        self,
        context: QueryContext,
        strategy: Dict[str, bool],
        config: WorkflowConfig
    ) -> List[RetrievalResult]:
        """执行检索阶段"""
        retrieval_tasks = []
        
        # 创建检索任务
        if strategy.get("use_vector", True):
            retrieval_tasks.append(
                asyncio.create_task(vector_retriever.process(context))
            )
        
        if strategy.get("use_graph", True):
            retrieval_tasks.append(
                asyncio.create_task(graph_retriever.process(context))
            )
        
        # 执行检索任务
        if strategy.get("use_parallel", True):
            # 并行执行
            results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
        else:
            # 串行执行
            results = []
            for task in retrieval_tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    logger.error(f"检索任务失败: {e}")
                    results.append(e)
        
        # 过滤成功的结果
        successful_results = [
            result for result in results 
            if isinstance(result, RetrievalResult)
        ]
        
        if not successful_results:
            logger.warning("所有检索任务都失败了")
            # 返回空结果
            return [RetrievalResult(
                source="fallback",
                results=[],
                score=0.0,
                metadata={"error": "所有检索任务失败"}
            )]
        
        return successful_results
    
    async def _execute_fusion_phase(
        self,
        retrieval_results: List[RetrievalResult],
        config: WorkflowConfig
    ) -> Dict[str, Any]:
        """执行融合阶段"""
        if not config.enable_result_fusion or len(retrieval_results) <= 1:
            # 如果不启用融合或只有一个结果，直接返回
            if retrieval_results:
                return {
                    "fused_results": retrieval_results[0].results,
                    "fusion_score": retrieval_results[0].score,
                    "final_count": len(retrieval_results[0].results)
                }
            else:
                return {
                    "fused_results": [],
                    "fusion_score": 0.0,
                    "final_count": 0
                }
        
        return await result_fusion.process(retrieval_results)
    
    async def _execute_generation_phase(
        self,
        context: QueryContext,
        fusion_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行生成阶段"""
        return await answer_generator.process(context, fusion_result)


# 全局工作流协调器实例
workflow_orchestrator = RAGWorkflowOrchestrator()
