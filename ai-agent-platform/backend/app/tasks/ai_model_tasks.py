# Copyright (c) 2025 左岚. All rights reserved.
"""
AI模型相关异步任务
"""

# # Standard library imports
from datetime import datetime
import logging
import time
from typing import Any, Dict, List, Optional

# # Local application imports
from app.agents.llm_interface import LLMInterface
from app.core.celery_app import celery_app
from app.core.metrics import metrics_manager

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, queue='ai_model', priority=8)
def process_ai_request(self, model_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
    """处理AI模型请求"""
    start_time = time.time()
    
    try:
        logger.info(f"开始处理AI请求: {model_name}")
        
        # 创建LLM接口
        llm = LLMInterface()
        
        # 处理请求
        response = llm.generate_response(prompt, **kwargs)
        
        # 记录指标
        duration = time.time() - start_time
        metrics_manager.record_ai_model_request(
            model_name=model_name,
            response_time=duration,
            status='success'
        )
        
        logger.info(f"AI请求处理完成: {model_name}, 耗时: {duration:.2f}s")
        
        return {
            'status': 'success',
            'response': response,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        duration = time.time() - start_time
        metrics_manager.record_ai_model_request(
            model_name=model_name,
            response_time=duration,
            status='error'
        )
        
        logger.error(f"AI请求处理失败: {model_name}, 错误: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, queue='ai_model', priority=6)
def batch_ai_processing(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """批量处理AI请求"""
    start_time = time.time()
    results = []
    
    try:
        logger.info(f"开始批量AI处理: {len(requests)} 个请求")
        
        for i, request in enumerate(requests):
            try:
                result = process_ai_request.apply(
                    args=(request['model_name'], request['prompt']),
                    kwargs=request.get('kwargs', {})
                )
                results.append({
                    'index': i,
                    'status': 'success',
                    'result': result.get()
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'status': 'error',
                    'error': str(e)
                })
        
        duration = time.time() - start_time
        logger.info(f"批量AI处理完成: {len(requests)} 个请求, 耗时: {duration:.2f}s")
        
        return {
            'status': 'success',
            'results': results,
            'total_requests': len(requests),
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"批量AI处理失败: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=2)


@celery_app.task(bind=True, queue='ai_model', priority=4)
def model_warmup(self, model_name: str) -> Dict[str, Any]:
    """模型预热任务"""
    start_time = time.time()
    
    try:
        logger.info(f"开始模型预热: {model_name}")
        
        # 创建LLM接口并进行预热
        llm = LLMInterface()
        warmup_prompt = "Hello, this is a warmup request."
        
        response = llm.generate_response(warmup_prompt, max_tokens=10)
        
        duration = time.time() - start_time
        logger.info(f"模型预热完成: {model_name}, 耗时: {duration:.2f}s")
        
        return {
            'status': 'success',
            'model_name': model_name,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"模型预热失败: {model_name}, 错误: {e}")
        raise self.retry(exc=e, countdown=30, max_retries=2)
