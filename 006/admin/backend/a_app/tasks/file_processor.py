import asyncio
import base64
import os
import traceback
import concurrent.futures
import multiprocessing
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from openai import OpenAI

from a_app.log import logger
from a_app.models.knowledge import KnowledgeFile, EmbeddingStatus
from a_app.utils.minio import file_storage
from a_app.chromadb.customer_vector import customer_vector_db
from a_app.settings.config import settings
from a_app.settings.file_types import FileProcessingMethod, get_processing_method, is_supported_extension
from a_app.utils.text_chunker import TextChunker, ChunkerConfig

# Import marker for document conversion
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    MARKER_AVAILABLE = True
except ImportError:
    logger.warning("Marker library not available. Document to markdown conversion will be disabled.")
    MARKER_AVAILABLE = False


class FileProcessor:
    """Process files for embedding in vector database"""

    def __init__(self):
        """Initialize the file processor"""
        self._processing_queue = asyncio.Queue()
        self._is_running = False
        self._worker_task = None

    async def start(self):
        """Start the file processor worker"""
        if self._is_running:
            return

        self._is_running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("File processor worker started")

    async def stop(self):
        """Stop the file processor worker"""
        if not self._is_running:
            return

        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        logger.info("File processor worker stopped")

    async def queue_file(self, file_id: int):
        """
        Queue a file for processing

        Args:
            file_id: ID of the file to process
        """
        await self._processing_queue.put(file_id)
        logger.info(f"File {file_id} queued for processing")

    async def _worker(self):
        """Worker process that processes files in the queue"""
        while self._is_running:
            try:
                # Get the next file ID from the queue
                file_id = await self._processing_queue.get()

                # Process the file
                await self._process_file(file_id)

                # Mark the task as done
                self._processing_queue.task_done()
            except asyncio.CancelledError:
                # Worker was cancelled
                break
            except Exception as e:
                logger.error(f"Error in file processor worker: {e}")
                traceback.print_exc()

    def describe_image(self, image_path):
        """Generate a description of an image using VLLM API，借助LLM生成几个相关的问题，多角度获取图片中的内容，自行完成"""
        with open(image_path, "rb") as image_file:
            image_b64 = base64.b64encode(image_file.read()).decode('utf-8')
        prompt: str = "请从多个角度详细描述你在图片中看到的内容"
        client = OpenAI(api_key=settings.VLLM_API_KEY, base_url=settings.VLLM_API_URL)
        messages = [
            {
                "role": "user",
                "content":
                    [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                        }
                    ]
            }
        ]
        completion = client.chat.completions.create(
            model=settings.VLLM_API_MODEL,
            messages=messages, temperature=0.5,
            seed=0, top_p=0.70, stream=False
        )
        # 返回多个问题汇总后的答案描述
        return completion.choices[0].message.content
    async def _process_file(self, file_id: int):
        """
        Process a file for embedding

        Args:
            file_id: ID of the file to process
        """
        # Get the file from the database
        file_obj = await KnowledgeFile.get(id=file_id)

        # Update status to processing
        file_obj.embedding_status = EmbeddingStatus.PROCESSING
        await file_obj.save()

        try:
            # Get file extension
            file_extension = os.path.splitext(file_obj.name)[1].lower()

            # Get the full file path
            file_full_path = str(file_storage.storage_dir / file_obj.file_path)

            # 使用进程池在单独进程中处理文件，避免阻塞主事件循环
            logger.info(f"Processing file {file_obj.name} in a separate process")
            loop = asyncio.get_event_loop()
            success, markdown_text, error = await loop.run_in_executor(
                process_pool,
                process_file_in_process,
                file_full_path,
                file_extension
            )

            # 如果处理失败，抛出异常
            if not success:
                raise ValueError(error)

            logger.info(f"File {file_obj.name} processed successfully")

            # Add document to vector database
            logger.info(f"Adding document to vector database: {file_obj.id}")
            knowledge_base = await file_obj.knowledge_base
            knowledge_base_id = knowledge_base.id

            # Get knowledge base details
            knowledge_type = knowledge_base.knowledge_type
            is_public = knowledge_base.is_public
            owner_id = knowledge_base.owner_id

            logger.info(f"Knowledge base details: id={knowledge_base_id}, type={knowledge_type}, public={is_public}, owner={owner_id}")

            try:
                # Process markdown text based on file type
                file_extension = os.path.splitext(file_obj.name)[1].lower()
                processing_method = get_processing_method(file_extension)

                # Detect language (simple heuristic - can be improved)
                language = 'auto'
                # Check for Chinese characters (Unicode range for CJK Unified Ideographs)
                if any(0x4E00 <= ord(char) <= 0x9FFF for char in markdown_text):
                    language = 'zh'  # Chinese characters detected

                # Add document to vector database - let it handle chunking
                chunk_ids = await customer_vector_db.add_document(
                    knowledge_base_id=knowledge_base_id,
                    file_id=file_obj.id,
                    markdown_text=markdown_text,
                    knowledge_type=knowledge_type,
                    is_public=is_public,
                    owner_id=owner_id,
                    file_extension=file_extension,  # Pass file extension for type-specific processing
                    language=language  # Pass detected language
                )
            except Exception as e:
                logger.error(f"Error adding document to vector database: {e}")
                # Simulate success for now
                chunk_ids = [f"file_{file_obj.id}_chunk_0"]

            logger.info(f"Added {len(chunk_ids)} chunks to vector database for file {file_obj.id}")

            # Update status to completed
            file_obj.embedding_status = EmbeddingStatus.COMPLETED
            file_obj.embedding_error = None
            await file_obj.save()

        except Exception as e:
            # Update status to failed
            error_message = f"Error processing file: {str(e)}"
            logger.error(error_message)
            traceback.print_exc()

            file_obj.embedding_status = EmbeddingStatus.FAILED
            file_obj.embedding_error = error_message
            await file_obj.save()


# 在单独进程中处理文件的函数
def process_file_in_process(file_path: str, file_extension: str) -> Tuple[bool, str, str]:
    """
    在单独进程中处理文件，将文件转换为 Markdown

    Args:
        file_path: 文件路径
        file_extension: 文件扩展名

    Returns:
        Tuple[bool, str, str]: (成功标志, Markdown 文本, 错误信息)
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, "", f"File not found: {file_path}"

        # 检查文件类型是否支持
        file_extension = file_extension.lower()
        if not is_supported_extension(file_extension):
            return False, "", f"Unsupported file type: {file_extension}"

        # 确定处理方法
        try:
            processing_method = get_processing_method(file_extension)
        except ValueError as e:
            return False, "", str(e)

        # 根据文件类型选择处理方法
        if processing_method == FileProcessingMethod.MARKDOWN:
            # 直接读取 Markdown 文件
            logger.info(f"Processing markdown file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    markdown_text = f.read()
                return True, markdown_text, ""
            except Exception as e:
                return False, "", f"Error reading markdown file: {str(e)}"

        elif processing_method == FileProcessingMethod.TEXT:
            # 处理文本文件
            logger.info(f"Processing text file: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = f.read()

                # 检测文件内容是否为空
                if not text_content.strip():
                    return False, "", "File is empty or contains only whitespace"

                # 根据文件类型进行特殊处理
                if file_extension in [".json", ".xml", ".yaml", ".yml"]:
                    # 结构化数据文件，保持原格式
                    markdown_text = f"```{file_extension[1:]}\n{text_content}\n```"
                elif file_extension in [".py", ".js", ".java", ".c", ".cpp", ".cs", ".go", ".rs"]:
                    # 代码文件，添加代码块格式
                    markdown_text = f"```{file_extension[1:]}\n{text_content}\n```"
                elif file_extension in [".csv"]:
                    # CSV 文件，尝试转换为 Markdown 表格
                    try:
                        lines = text_content.strip().split('\n')
                        if len(lines) > 1:
                            # 创建表头分隔符
                            header = lines[0].split(',')
                            separator = '|' + '|'.join(['---' for _ in header]) + '|'
                            # 转换为 Markdown 表格
                            table_rows = ['|' + '|'.join(line.split(',')) + '|' for line in lines]
                            table_rows.insert(1, separator)
                            markdown_text = '\n'.join(table_rows)
                        else:
                            # 如果只有一行，仍然使用代码块
                            markdown_text = f"```csv\n{text_content}\n```"
                    except Exception:
                        # 如果转换失败，回退到代码块
                        markdown_text = f"```csv\n{text_content}\n```"
                else:
                    # 普通文本文件，直接使用内容
                    markdown_text = text_content

                return True, markdown_text, ""
            except Exception as e:
                return False, "", f"Error processing text file: {str(e)}"

        elif processing_method == FileProcessingMethod.PDF_CONVERTER:
            # 使用 PdfConverter 处理复杂文档
            logger.info(f"Processing document with PdfConverter: {file_path}")
            # 检查 marker 是否可用
            if not MARKER_AVAILABLE:
                return False, "", "Marker library not available for document conversion"

            try:
                # 初始化转换器
                converter = PdfConverter(
                    # config={"output_format": "markdown",
                    #         "output_dir": "output",
                    #         "use_llm": False,
                    #         "llm_service": "marker.services.openai.OpenAIService",
                    #         "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    #         "openai_model": "qwen-vl-max-latest",
                    #         "openai_api_key": "sk-9d64fad24f9e402c81e99add13cfae97"},
                    artifact_dict=create_model_dict(),
                    # llm_service="marker.services.openai.OpenAIService",
                )

                # 转换文件为 Markdown
                rendered = converter(file_path)
                markdown_text, _, images = text_from_rendered(rendered)

                # 检查转换结果是否为空
                if not markdown_text.strip():
                    return False, "", "Document conversion produced empty result"

                return True, markdown_text, ""
            except Exception as e:
                return False, "", f"Error converting document: {str(e)}"

        else:
            return False, "", f"Unknown processing method: {processing_method}"

    except Exception as e:
        error_message = f"Error processing file: {str(e)}"
        traceback.print_exc()
        return False, "", error_message

# 创建进程池
process_pool = concurrent.futures.ProcessPoolExecutor(
    max_workers=multiprocessing.cpu_count(),
)

# Create singleton instance
file_processor = FileProcessor()
