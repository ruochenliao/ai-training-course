"""
异步文件处理系统
支持多种文档格式转换为Markdown，使用asyncio.Queue实现任务队列

核心组件：
- FileProcessor: 异步文件处理器，支持任务队列和进程池
- ProcessorConfig: 处理器配置类
- DocumentConverter: 多种文档格式转换器
- MultimodalProcessor: 图片描述生成处理器
- TaskManager: 任务队列和状态管理

支持功能：
- PDF转换（marker-pdf）
- Office文档转换（docx, xlsx, pptx）
- 文本文件处理（txt, md, csv, json等）
- 图片描述生成（多模态LLM）
- 异步任务队列和进程池
- 状态管理和错误重试
- 批量处理和并发控制
"""

# 导入配置类和枚举
from .processor_config import (
    ProcessorConfig,
    ProcessingStatus,
    FileType,
    ConversionMethod
)

# 导入核心处理器
from .file_processor import (
    FileProcessor,
    ProcessingResult
)

# 导入转换器
from .document_converter import DocumentConverter
from .multimodal_processor import MultimodalProcessor

# 导入任务管理
from .task_manager import (
    TaskManager,
    ProcessingTask
)

# 导出所有公共接口
__all__ = [
    # 配置类和枚举
    'ProcessorConfig',
    'ProcessingStatus',
    'FileType',
    'ConversionMethod',
    
    # 核心处理器
    'FileProcessor',
    'ProcessingResult',
    
    # 转换器
    'DocumentConverter',
    'MultimodalProcessor',
    
    # 任务管理
    'TaskManager',
    'ProcessingTask'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "Intelligent Customer Service Team"
__description__ = "异步文件处理系统 - 支持多种文档格式转换为Markdown"

# 便捷函数
async def create_file_processor(
    max_workers: int = 4,
    queue_size: int = 1000,
    max_retries: int = 3
) -> FileProcessor:
    """
    创建并启动文件处理器
    
    Args:
        max_workers: 最大工作进程数
        queue_size: 任务队列大小
        max_retries: 最大重试次数
        
    Returns:
        已启动的文件处理器
    """
    config = ProcessorConfig(
        max_workers=max_workers,
        queue_size=queue_size,
        max_retries=max_retries
    )
    
    processor = FileProcessor(config)
    await processor.start()
    return processor


async def process_single_file(
    file_path: str,
    metadata: dict = None,
    config: ProcessorConfig = None
) -> ProcessingResult:
    """
    处理单个文件的便捷函数
    
    Args:
        file_path: 文件路径
        metadata: 文件元数据
        config: 处理器配置
        
    Returns:
        处理结果
    """
    processor = FileProcessor(config or ProcessorConfig())
    
    try:
        await processor.start()
        
        # 提交任务
        task_id = await processor.submit_file(file_path, metadata)
        
        # 等待完成
        result = None
        while True:
            result = await processor.get_task_status(task_id)
            if result and result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                break
            await asyncio.sleep(1)
        
        return result
        
    finally:
        await processor.stop()


async def process_batch_files(
    file_paths: list,
    metadata_list: list = None,
    config: ProcessorConfig = None,
    max_concurrent: int = 5
) -> list:
    """
    批量处理文件的便捷函数
    
    Args:
        file_paths: 文件路径列表
        metadata_list: 元数据列表
        config: 处理器配置
        max_concurrent: 最大并发数
        
    Returns:
        处理结果列表
    """
    if not file_paths:
        return []
    
    # 限制并发数
    if len(file_paths) > max_concurrent:
        # 分批处理
        results = []
        for i in range(0, len(file_paths), max_concurrent):
            batch_files = file_paths[i:i + max_concurrent]
            batch_metadata = metadata_list[i:i + max_concurrent] if metadata_list else None
            
            batch_results = await process_batch_files(
                batch_files, batch_metadata, config, max_concurrent
            )
            results.extend(batch_results)
        
        return results
    
    processor = FileProcessor(config or ProcessorConfig())
    
    try:
        await processor.start()
        
        # 批量提交任务
        task_ids = await processor.submit_batch(file_paths, metadata_list)
        
        # 等待所有任务完成
        results = []
        while len(results) < len(task_ids):
            for task_id in task_ids:
                if any(r.task_id == task_id for r in results):
                    continue
                
                result = await processor.get_task_status(task_id)
                if result and result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                    results.append(result)
            
            if len(results) < len(task_ids):
                await asyncio.sleep(1)
        
        return results
        
    finally:
        await processor.stop()


# 示例用法
"""
# 基本用法示例

# 1. 创建和使用文件处理器
import asyncio
from app.services.file_processor import create_file_processor

async def main():
    # 创建处理器
    processor = await create_file_processor(max_workers=4)
    
    try:
        # 提交文件处理任务
        task_id = await processor.submit_file(
            file_path="/path/to/document.pdf",
            metadata={"source": "upload", "user_id": "123"}
        )
        
        # 监控处理进度
        while True:
            result = await processor.get_task_status(task_id)
            if result.status == ProcessingStatus.COMPLETED:
                print(f"处理完成: {result.markdown_content}")
                break
            elif result.status == ProcessingStatus.FAILED:
                print(f"处理失败: {result.error_message}")
                break
            
            await asyncio.sleep(1)
    
    finally:
        await processor.stop()

# 2. 使用便捷函数处理单个文件
from app.services.file_processor import process_single_file

async def process_file():
    result = await process_single_file("/path/to/document.docx")
    if result.status == ProcessingStatus.COMPLETED:
        print(result.markdown_content)

# 3. 批量处理文件
from app.services.file_processor import process_batch_files

async def batch_process():
    files = ["/path/to/file1.pdf", "/path/to/file2.docx", "/path/to/image.jpg"]
    results = await process_batch_files(files)
    
    for result in results:
        print(f"文件: {result.file_path}")
        print(f"状态: {result.status}")
        if result.status == ProcessingStatus.COMPLETED:
            print(f"内容: {result.markdown_content[:100]}...")

# 4. 使用自定义配置
from app.services.file_processor import ProcessorConfig, FileProcessor

async def custom_config():
    config = ProcessorConfig(
        max_workers=8,
        queue_size=2000,
        max_retries=5,
        processing_timeout=600
    )
    
    async with FileProcessor(config) as processor:
        # 使用上下文管理器自动启动和停止
        task_id = await processor.submit_file("/path/to/large_file.pdf")
        # ... 处理逻辑

# 5. 带回调函数的处理
async def with_callbacks():
    processor = await create_file_processor()
    
    def progress_callback(task_id, progress, message):
        print(f"任务 {task_id}: {progress}% - {message}")
    
    def completion_callback(task_id, result):
        print(f"任务 {task_id} 完成: {result.get('success', False)}")
    
    try:
        task_id = await processor.submit_file(
            "/path/to/file.pdf",
            progress_callback=progress_callback,
            completion_callback=completion_callback
        )
        
        await processor.wait_for_completion()
    
    finally:
        await processor.stop()
"""

# 配置示例
"""
# 配置示例

# 基础配置
basic_config = ProcessorConfig(
    max_workers=4,
    queue_size=1000,
    max_retries=3,
    processing_timeout=300
)

# 高性能配置
high_performance_config = ProcessorConfig.create_high_performance_config()

# 低资源配置
low_resource_config = ProcessorConfig.create_low_resource_config()

# 自定义配置
custom_config = ProcessorConfig(
    max_workers=8,
    queue_size=2000,
    batch_size=20,
    max_retries=5,
    retry_delay=10.0,
    exponential_backoff=True,
    max_file_size=200 * 1024 * 1024,  # 200MB
    multimodal_config={
        "model_name": "qwen-vl-plus",
        "api_key": "your_api_key",
        "max_tokens": 3000,
        "temperature": 0.1
    }
)
"""
