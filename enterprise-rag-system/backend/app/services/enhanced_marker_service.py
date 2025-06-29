"""
增强版Marker文档解析服务
基于官方源码优化，支持进度跟踪、质量评估、批量处理
"""

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional, Callable

from loguru import logger

from app import MarkerService
from app.core import DocumentProcessingException


class DocumentProcessor:
    """文档处理器 - 支持进度跟踪"""
    
    def __init__(self, file_path: str, file_name: str):
        self.file_path = file_path
        self.file_name = file_name
        self.status = "pending"
        self.progress = 0.0
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
    
    def update_progress(self, progress: float, status: str = None):
        """更新处理进度"""
        self.progress = min(max(progress, 0.0), 1.0)
        if status:
            self.status = status
    
    def set_result(self, result: Dict[str, Any]):
        """设置处理结果"""
        self.result = result
        self.status = "completed"
        self.progress = 1.0
        self.end_time = time.time()
    
    def set_error(self, error: str):
        """设置错误信息"""
        self.error = error
        self.status = "failed"
        self.end_time = time.time()
    
    def get_info(self) -> Dict[str, Any]:
        """获取处理信息"""
        info = {
            'file_name': self.file_name,
            'file_path': self.file_path,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time,
            'end_time': self.end_time
        }
        
        if self.start_time and self.end_time:
            info['processing_time'] = self.end_time - self.start_time
        
        if self.error:
            info['error'] = self.error
        
        return info


class EnhancedMarkerService:
    """增强版Marker文档解析服务"""
    
    def __init__(self):
        self.base_service = MarkerService()
        self.processors: Dict[str, DocumentProcessor] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_processing_time': 0.0,
            'avg_processing_time': 0.0
        }
        
        logger.info("增强版Marker服务初始化完成")
    
    async def parse_document_with_progress(
        self,
        file_path: str,
        file_name: str,
        extract_images: bool = True,
        extract_tables: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """
        解析文档并跟踪进度
        
        Returns:
            处理器ID，用于查询进度
        """
        processor_id = f"{file_name}_{int(time.time())}"
        processor = DocumentProcessor(file_path, file_name)
        processor.start_time = time.time()
        
        self.processors[processor_id] = processor
        
        # 异步处理
        asyncio.create_task(self._process_document_async(
            processor_id, processor, extract_images, extract_tables, progress_callback
        ))
        
        return processor_id
    
    async def _process_document_async(
        self,
        processor_id: str,
        processor: DocumentProcessor,
        extract_images: bool,
        extract_tables: bool,
        progress_callback: Optional[Callable[[float, str], None]]
    ):
        """异步处理文档"""
        try:
            # 更新进度
            processor.update_progress(0.1, "starting")
            if progress_callback:
                progress_callback(0.1, "starting")
            
            # 文件验证
            processor.update_progress(0.2, "validating")
            if progress_callback:
                progress_callback(0.2, "validating")
            
            if not os.path.exists(processor.file_path):
                raise DocumentProcessingException(f"文件不存在: {processor.file_path}")
            
            # 开始解析
            processor.update_progress(0.3, "parsing")
            if progress_callback:
                progress_callback(0.3, "parsing")
            
            result = await self.base_service.parse_document(
                processor.file_path,
                processor.file_name,
                extract_images,
                extract_tables
            )
            
            # 后处理
            processor.update_progress(0.8, "post_processing")
            if progress_callback:
                progress_callback(0.8, "post_processing")
            
            # 质量评估
            result = await self._enhance_result(result)
            
            # 完成
            processor.set_result(result)
            if progress_callback:
                progress_callback(1.0, "completed")
            
            # 更新统计
            self._update_stats(True, processor.end_time - processor.start_time)
            
        except Exception as e:
            processor.set_error(str(e))
            if progress_callback:
                progress_callback(0.0, f"failed: {str(e)}")
            
            self._update_stats(False, 0)
            logger.error(f"文档处理失败 {processor.file_name}: {e}")
    
    async def _enhance_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """增强处理结果"""
        # 添加内容摘要
        if result.get('content'):
            result['summary'] = self._generate_summary(result['content'])
        
        # 添加关键词
        result['keywords'] = self._extract_keywords(result.get('content', ''))
        
        # 添加语言检测
        result['detected_language'] = self._detect_language(result.get('content', ''))
        
        # 添加可读性评分
        result['readability_score'] = self._calculate_readability(result.get('content', ''))
        
        return result
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成内容摘要"""
        if not content:
            return ""
        
        # 简单的摘要生成（取前几句）
        sentences = content.split('。')
        summary_parts = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > max_length:
                break
            summary_parts.append(sentence)
            current_length += len(sentence)
        
        return '。'.join(summary_parts) + ('。' if summary_parts else '')
    
    def _extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """提取关键词"""
        if not content:
            return []
        
        # 简单的关键词提取（基于词频）
        import re
        from collections import Counter
        
        # 移除标点符号，分词
        words = re.findall(r'\b\w+\b', content.lower())
        
        # 过滤停用词（简化版）
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        words = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 统计词频
        word_freq = Counter(words)
        
        # 返回最频繁的词
        return [word for word, _ in word_freq.most_common(max_keywords)]
    
    def _detect_language(self, content: str) -> str:
        """检测语言"""
        if not content:
            return "unknown"
        
        # 简单的语言检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        english_chars = len(re.findall(r'[a-zA-Z]', content))
        
        if chinese_chars > english_chars:
            return "chinese"
        elif english_chars > 0:
            return "english"
        else:
            return "unknown"
    
    def _calculate_readability(self, content: str) -> float:
        """计算可读性评分"""
        if not content:
            return 0.0
        
        # 简单的可读性评分
        sentences = len(content.split('。'))
        words = len(content.split())
        
        if sentences == 0:
            return 0.0
        
        avg_words_per_sentence = words / sentences
        
        # 基于平均句长的可读性评分（简化）
        if avg_words_per_sentence <= 15:
            return 0.9
        elif avg_words_per_sentence <= 25:
            return 0.7
        elif avg_words_per_sentence <= 35:
            return 0.5
        else:
            return 0.3
    
    def get_processing_status(self, processor_id: str) -> Optional[Dict[str, Any]]:
        """获取处理状态"""
        processor = self.processors.get(processor_id)
        if not processor:
            return None
        
        return processor.get_info()
    
    def get_processing_result(self, processor_id: str) -> Optional[Dict[str, Any]]:
        """获取处理结果"""
        processor = self.processors.get(processor_id)
        if not processor or processor.status != "completed":
            return None
        
        return processor.result
    
    async def batch_process_documents(
        self,
        file_paths: List[str],
        extract_images: bool = True,
        extract_tables: bool = True,
        max_concurrent: int = 3,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[str]:
        """
        批量处理文档
        
        Returns:
            处理器ID列表
        """
        processor_ids = []
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            processor_id = await self.parse_document_with_progress(
                file_path, file_name, extract_images, extract_tables
            )
            processor_ids.append(processor_id)
        
        return processor_ids
    
    def get_batch_status(self, processor_ids: List[str]) -> Dict[str, Any]:
        """获取批量处理状态"""
        total = len(processor_ids)
        completed = 0
        failed = 0
        total_progress = 0.0
        
        for processor_id in processor_ids:
            processor = self.processors.get(processor_id)
            if processor:
                total_progress += processor.progress
                if processor.status == "completed":
                    completed += 1
                elif processor.status == "failed":
                    failed += 1
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'in_progress': total - completed - failed,
            'overall_progress': total_progress / total if total > 0 else 0.0,
            'completion_rate': completed / total if total > 0 else 0.0
        }
    
    def _update_stats(self, success: bool, processing_time: float):
        """更新统计信息"""
        self.stats['total_processed'] += 1
        
        if success:
            self.stats['successful'] += 1
            self.stats['total_processing_time'] += processing_time
            self.stats['avg_processing_time'] = (
                self.stats['total_processing_time'] / self.stats['successful']
            )
        else:
            self.stats['failed'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return self.stats.copy()
    
    def cleanup_completed_processors(self, max_age_hours: int = 24):
        """清理已完成的处理器"""
        current_time = time.time()
        to_remove = []
        
        for processor_id, processor in self.processors.items():
            if processor.end_time and (current_time - processor.end_time) > (max_age_hours * 3600):
                to_remove.append(processor_id)
        
        for processor_id in to_remove:
            del self.processors[processor_id]
        
        logger.info(f"清理了 {len(to_remove)} 个过期处理器")


# 全局增强版Marker服务实例
enhanced_marker_service = EnhancedMarkerService()
