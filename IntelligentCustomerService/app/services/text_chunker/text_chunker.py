"""
智能文本分块系统
支持多种文档类型的语义分块，包括Markdown、代码、多语言文本等
"""
import asyncio
import hashlib
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_text_splitters import MarkdownHeaderTextSplitter, CharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    RecursiveCharacterTextSplitter = None
    MarkdownHeaderTextSplitter = None
    CharacterTextSplitter = None

from .chunker_config import ChunkerConfig, ChunkStrategy, LanguageType, ContentType

logger = logging.getLogger(__name__)


@dataclass
class ChunkInfo:
    """文本块信息"""
    content: str
    index: int
    start_position: int
    end_position: int
    byte_length: int
    char_length: int
    language: LanguageType
    content_type: ContentType
    chunk_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.chunk_hash:
            self.chunk_hash = hashlib.md5(self.content.encode('utf-8')).hexdigest()
        
        if not self.byte_length:
            self.byte_length = len(self.content.encode('utf-8'))
        
        if not self.char_length:
            self.char_length = len(self.content)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "index": self.index,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "byte_length": self.byte_length,
            "char_length": self.char_length,
            "language": self.language.value,
            "content_type": self.content_type.value,
            "chunk_hash": self.chunk_hash,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


@dataclass
class ProtectedBlock:
    """受保护的特殊块"""
    placeholder: str
    content: str
    start_position: int
    end_position: int
    block_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class LanguageDetector:
    """语言检测器"""
    
    @staticmethod
    def detect_language(text: str) -> LanguageType:
        """
        检测文本语言类型
        
        Args:
            text: 输入文本
            
        Returns:
            语言类型
        """
        if not text.strip():
            return LanguageType.AUTO
        
        # 统计CJK字符（中日韩字符）
        cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u3300-\u33ff\ufe30-\ufe4f\uf900-\ufaff\u2f800-\u2fa1f]+')
        cjk_chars = len(cjk_pattern.findall(text))
        
        # 统计英文字符
        english_pattern = re.compile(r'[a-zA-Z]+')
        english_chars = len(english_pattern.findall(text))
        
        total_chars = len(re.sub(r'\s+', '', text))  # 去除空白字符后的总字符数
        
        if total_chars == 0:
            return LanguageType.AUTO
        
        cjk_ratio = cjk_chars / total_chars
        english_ratio = english_chars / total_chars
        
        # 判断语言类型
        if cjk_ratio > 0.3:
            if english_ratio > 0.2:
                return LanguageType.MIXED
            else:
                return LanguageType.CHINESE
        elif english_ratio > 0.5:
            return LanguageType.ENGLISH
        else:
            return LanguageType.MIXED


class ContentTypeDetector:
    """内容类型检测器"""
    
    @staticmethod
    def detect_content_type(text: str, filename: str = None) -> ContentType:
        """
        检测内容类型
        
        Args:
            text: 文本内容
            filename: 文件名（可选）
            
        Returns:
            内容类型
        """
        # 根据文件扩展名判断
        if filename:
            filename_lower = filename.lower()
            if filename_lower.endswith('.md'):
                return ContentType.MARKDOWN
            elif filename_lower.endswith(('.py', '.js', '.java', '.cpp', '.c', '.go', '.rs')):
                return ContentType.CODE
            elif filename_lower.endswith(('.html', '.htm')):
                return ContentType.HTML
            elif filename_lower.endswith('.json'):
                return ContentType.JSON
            elif filename_lower.endswith('.xml'):
                return ContentType.XML
        
        # 根据内容特征判断
        text_sample = text[:1000]  # 取前1000字符进行检测
        
        # Markdown特征
        markdown_patterns = [
            r'^#{1,6}\s+',      # 标题
            r'```[\s\S]*?```',  # 代码块
            r'\[.*?\]\(.*?\)',  # 链接
            r'!\[.*?\]\(.*?\)', # 图片
            r'\|.*?\|',         # 表格
        ]
        
        markdown_score = sum(1 for pattern in markdown_patterns 
                           if re.search(pattern, text_sample, re.MULTILINE))
        
        if markdown_score >= 2:
            return ContentType.MARKDOWN
        
        # HTML特征
        if re.search(r'<[^>]+>', text_sample):
            return ContentType.HTML
        
        # JSON特征
        if text_sample.strip().startswith(('{', '[')):
            try:
                import json
                json.loads(text_sample)
                return ContentType.JSON
            except:
                pass
        
        # XML特征
        if text_sample.strip().startswith('<?xml') or re.search(r'<[^>]+>.*</[^>]+>', text_sample):
            return ContentType.XML
        
        # 代码特征
        code_patterns = [
            r'def\s+\w+\s*\(',      # Python函数
            r'function\s+\w+\s*\(', # JavaScript函数
            r'class\s+\w+\s*{',     # 类定义
            r'import\s+\w+',        # 导入语句
            r'#include\s*<',        # C/C++包含
        ]
        
        code_score = sum(1 for pattern in code_patterns 
                        if re.search(pattern, text_sample))
        
        if code_score >= 1:
            return ContentType.CODE
        
        return ContentType.PLAIN_TEXT


class TextChunker:
    """
    智能文本分块器
    支持多种文档类型的语义分块
    """
    
    def __init__(self, config: ChunkerConfig = None):
        """
        初始化文本分块器
        
        Args:
            config: 分块配置
        """
        self.config = config or ChunkerConfig()
        self.language_detector = LanguageDetector()
        self.content_type_detector = ContentTypeDetector()
        
        # 初始化线程池
        if self.config.enable_parallel_processing:
            self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        else:
            self.executor = None
        
        # 统计信息
        self.stats = {
            "total_chunks_created": 0,
            "total_bytes_processed": 0,
            "total_processing_time": 0.0,
            "language_distribution": {},
            "content_type_distribution": {},
            "average_chunk_size": 0.0
        }
        
        logger.info(f"文本分块器初始化完成，策略: {self.config.strategy.value}")
    
    async def chunk_text(
        self,
        text: str,
        filename: str = None,
        metadata: Dict[str, Any] = None
    ) -> List[ChunkInfo]:
        """
        对文本进行智能分块
        
        Args:
            text: 输入文本
            filename: 文件名（用于类型检测）
            metadata: 额外元数据
            
        Returns:
            文本块信息列表
        """
        try:
            start_time = time.time()
            
            if not text or not text.strip():
                return []
            
            # 检测语言和内容类型
            detected_language = self.language_detector.detect_language(text)
            detected_content_type = self.content_type_detector.detect_content_type(text, filename)
            
            # 更新配置（如果是自动检测）
            if self.config.language == LanguageType.AUTO:
                self.config.language = detected_language
            
            if self.config.content_type == ContentType.PLAIN_TEXT and detected_content_type != ContentType.PLAIN_TEXT:
                self.config.content_type = detected_content_type
            
            # 预处理文本
            processed_text = self._preprocess_text(text)
            
            # 根据策略选择分块方法
            if self.config.strategy == ChunkStrategy.MARKDOWN and detected_content_type == ContentType.MARKDOWN:
                chunks = await self._markdown_chunking(processed_text)
            elif self.config.strategy == ChunkStrategy.SEMANTIC:
                chunks = await self._semantic_chunking(processed_text)
            elif self.config.strategy == ChunkStrategy.ADAPTIVE:
                chunks = await self._adaptive_chunking(processed_text)
            else:  # RECURSIVE or FIXED
                chunks = await self._recursive_chunking(processed_text)
            
            # 创建ChunkInfo对象
            chunk_infos = []
            for i, chunk_content in enumerate(chunks):
                if not chunk_content.strip() and self.config.remove_empty_chunks:
                    continue
                
                # 计算位置信息
                start_pos = text.find(chunk_content)
                if start_pos == -1:
                    start_pos = 0  # 如果找不到，设为0
                end_pos = start_pos + len(chunk_content)
                
                # 创建块信息
                chunk_info = ChunkInfo(
                    content=chunk_content,
                    index=i,
                    start_position=start_pos,
                    end_position=end_pos,
                    byte_length=len(chunk_content.encode('utf-8')),
                    char_length=len(chunk_content),
                    language=detected_language,
                    content_type=detected_content_type,
                    chunk_hash="",  # 将在__post_init__中计算
                    metadata=metadata or {}
                )
                
                chunk_infos.append(chunk_info)
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self._update_stats(chunk_infos, processing_time, detected_language, detected_content_type)
            
            logger.info(f"文本分块完成: {len(chunk_infos)}块, 耗时: {processing_time:.2f}秒")
            
            return chunk_infos
            
        except Exception as e:
            logger.error(f"文本分块失败: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本
        """
        if not text:
            return ""
        
        # 标准化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 标准化空白字符（如果启用）
        if self.config.normalize_whitespace:
            # 移除行尾空白
            text = re.sub(r'[ \t]+\n', '\n', text)
            # 标准化多个空格为单个空格
            text = re.sub(r'[ \t]+', ' ', text)
            # 限制连续换行符不超过3个
            text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        return text.strip()
    
    async def _markdown_chunking(self, text: str) -> List[str]:
        """
        Markdown智能分块
        
        Args:
            text: Markdown文本
            
        Returns:
            分块列表
        """
        try:
            # 保护特殊块
            protected_blocks, processed_text = self._protect_special_blocks(text)
            
            # 使用LangChain的MarkdownHeaderTextSplitter
            if LANGCHAIN_AVAILABLE:
                headers_to_split_on = [
                    ("#", "Header 1"),
                    ("##", "Header 2"),
                    ("###", "Header 3"),
                    ("####", "Header 4"),
                    ("#####", "Header 5"),
                    ("######", "Header 6"),
                ]
                
                markdown_splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=headers_to_split_on
                )
                
                # 分割文档
                docs = markdown_splitter.split_text(processed_text)
                chunks = [doc.page_content for doc in docs]
                
                # 进一步分割过大的块
                final_chunks = []
                for chunk in chunks:
                    if len(chunk.encode('utf-8')) > self.config.chunk_size:
                        # 使用递归分块处理大块
                        sub_chunks = await self._recursive_chunking(chunk)
                        final_chunks.extend(sub_chunks)
                    else:
                        final_chunks.append(chunk)
                
                chunks = final_chunks
            else:
                # 降级到手动Markdown分块
                chunks = self._manual_markdown_chunking(processed_text)
            
            # 恢复特殊块
            chunks = self._restore_special_blocks(chunks, protected_blocks)
            
            return chunks
            
        except Exception as e:
            logger.warning(f"Markdown分块失败，降级到递归分块: {e}")
            return await self._recursive_chunking(text)

    def _manual_markdown_chunking(self, text: str) -> List[str]:
        """
        手动Markdown分块（当LangChain不可用时）

        Args:
            text: Markdown文本

        Returns:
            分块列表
        """
        chunks = []
        current_chunk = ""
        lines = text.split('\n')

        for line in lines:
            # 检查是否是标题行
            is_header = False
            for header in self.config.markdown_headers:
                if line.strip().startswith(header):
                    is_header = True
                    break

            # 如果遇到标题且当前块不为空，保存当前块
            if is_header and current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'

                # 检查块大小
                if len(current_chunk.encode('utf-8')) > self.config.chunk_size:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    async def _recursive_chunking(self, text: str) -> List[str]:
        """
        递归分块

        Args:
            text: 输入文本

        Returns:
            分块列表
        """
        try:
            # 保护特殊块
            protected_blocks, processed_text = self._protect_special_blocks(text)

            # 获取分隔符
            separators = self.config.get_separators_for_language()

            if LANGCHAIN_AVAILABLE:
                # 使用LangChain的RecursiveCharacterTextSplitter
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap,
                    separators=separators,
                    length_function=lambda x: len(x.encode('utf-8'))  # 使用字节长度
                )
                chunks = splitter.split_text(processed_text)
            else:
                # 手动递归分块
                chunks = self._manual_recursive_split(processed_text, separators)

            # 恢复特殊块
            chunks = self._restore_special_blocks(chunks, protected_blocks)

            return chunks

        except Exception as e:
            logger.warning(f"递归分块失败，降级到固定分块: {e}")
            return self._fixed_chunking(text)

    def _manual_recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """
        手动递归分割

        Args:
            text: 输入文本
            separators: 分隔符列表

        Returns:
            分块列表
        """
        if not text or len(text.encode('utf-8')) <= self.config.chunk_size:
            return [text] if text else []

        # 尝试使用分隔符分割
        for separator in separators:
            if separator in text:
                parts = text.split(separator)
                chunks = []
                current_chunk = ""

                for part in parts:
                    # 计算添加当前部分后的大小
                    test_chunk = current_chunk + separator + part if current_chunk else part
                    test_size = len(test_chunk.encode('utf-8'))

                    if test_size <= self.config.chunk_size:
                        current_chunk = test_chunk
                    else:
                        # 保存当前块
                        if current_chunk:
                            chunks.append(current_chunk)

                        # 如果单个部分过大，递归分割
                        if len(part.encode('utf-8')) > self.config.chunk_size:
                            sub_chunks = self._manual_recursive_split(part, separators[1:])
                            chunks.extend(sub_chunks)
                            current_chunk = ""
                        else:
                            current_chunk = part

                # 添加最后一个块
                if current_chunk:
                    chunks.append(current_chunk)

                return chunks

        # 如果所有分隔符都无效，按字符分割
        return self._fixed_chunking(text)

    def _fixed_chunking(self, text: str) -> List[str]:
        """
        固定长度分块

        Args:
            text: 输入文本

        Returns:
            分块列表
        """
        chunks = []
        text_bytes = text.encode('utf-8')

        start = 0
        while start < len(text_bytes):
            end = start + self.config.chunk_size

            # 确保不在字符中间切断
            while end < len(text_bytes) and (text_bytes[end] & 0xC0) == 0x80:
                end += 1

            chunk_bytes = text_bytes[start:end]
            chunk_text = chunk_bytes.decode('utf-8', errors='ignore')

            if chunk_text.strip():
                chunks.append(chunk_text)

            # 计算下一个起始位置（考虑重叠）
            start = end - self.config.chunk_overlap
            if start < 0:
                start = end

        return chunks

    async def _semantic_chunking(self, text: str) -> List[str]:
        """
        语义分块

        Args:
            text: 输入文本

        Returns:
            分块列表
        """
        try:
            # 保护特殊块
            protected_blocks, processed_text = self._protect_special_blocks(text)

            # 按段落分割
            paragraphs = self._split_by_paragraphs(processed_text)

            # 语义相似度分组
            chunks = await self._group_by_semantic_similarity(paragraphs)

            # 恢复特殊块
            chunks = self._restore_special_blocks(chunks, protected_blocks)

            return chunks

        except Exception as e:
            logger.warning(f"语义分块失败，降级到递归分块: {e}")
            return await self._recursive_chunking(text)

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """
        按段落分割文本

        Args:
            text: 输入文本

        Returns:
            段落列表
        """
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', text)

        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    async def _group_by_semantic_similarity(self, paragraphs: List[str]) -> List[str]:
        """
        按语义相似度分组段落

        Args:
            paragraphs: 段落列表

        Returns:
            分组后的块列表
        """
        # 简化版语义分组：按长度和内容相关性分组
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            # 计算添加当前段落后的大小
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            test_size = len(test_chunk.encode('utf-8'))

            if test_size <= self.config.chunk_size:
                current_chunk = test_chunk
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk)

                # 如果单个段落过大，分割它
                if len(paragraph.encode('utf-8')) > self.config.chunk_size:
                    sub_chunks = await self._recursive_chunking(paragraph)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph

        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def _adaptive_chunking(self, text: str) -> List[str]:
        """
        自适应分块

        Args:
            text: 输入文本

        Returns:
            分块列表
        """
        # 根据内容类型选择最佳策略
        if self.config.content_type == ContentType.MARKDOWN:
            return await self._markdown_chunking(text)
        elif self.config.content_type == ContentType.CODE:
            # 代码文件使用较小的重叠
            original_overlap = self.config.chunk_overlap
            self.config.chunk_overlap = int(self.config.chunk_size * 0.05)  # 5%重叠
            chunks = await self._recursive_chunking(text)
            self.config.chunk_overlap = original_overlap  # 恢复原始重叠
            return chunks
        else:
            return await self._semantic_chunking(text)

    def _protect_special_blocks(self, text: str) -> Tuple[List[ProtectedBlock], str]:
        """
        保护特殊块（代码块、表格、数学公式等）

        Args:
            text: 输入文本

        Returns:
            (受保护块列表, 处理后的文本)
        """
        protected_blocks = []
        processed_text = text

        # 按优先级处理保护模式
        for block_type, pattern in self.config.protected_patterns.items():
            matches = list(re.finditer(pattern, processed_text, re.MULTILINE | re.DOTALL))

            # 从后往前替换，避免位置偏移
            for i, match in enumerate(reversed(matches)):
                placeholder = f"__PROTECTED_{block_type.upper()}_{len(protected_blocks)}__"

                protected_block = ProtectedBlock(
                    placeholder=placeholder,
                    content=match.group(),
                    start_position=match.start(),
                    end_position=match.end(),
                    block_type=block_type,
                    metadata={
                        "original_length": len(match.group()),
                        "byte_length": len(match.group().encode('utf-8'))
                    }
                )

                protected_blocks.append(protected_block)

                # 替换为占位符
                processed_text = (
                    processed_text[:match.start()] +
                    placeholder +
                    processed_text[match.end():]
                )

        return protected_blocks, processed_text

    def _restore_special_blocks(self, chunks: List[str], protected_blocks: List[ProtectedBlock]) -> List[str]:
        """
        恢复特殊块

        Args:
            chunks: 分块列表
            protected_blocks: 受保护块列表

        Returns:
            恢复后的分块列表
        """
        if not protected_blocks:
            return chunks

        restored_chunks = []

        for chunk in chunks:
            restored_chunk = chunk

            # 恢复所有占位符
            for block in protected_blocks:
                if block.placeholder in restored_chunk:
                    restored_chunk = restored_chunk.replace(block.placeholder, block.content)

            restored_chunks.append(restored_chunk)

        return restored_chunks

    def _update_stats(
        self,
        chunks: List[ChunkInfo],
        processing_time: float,
        language: LanguageType,
        content_type: ContentType
    ):
        """
        更新统计信息

        Args:
            chunks: 分块信息列表
            processing_time: 处理时间
            language: 语言类型
            content_type: 内容类型
        """
        self.stats["total_chunks_created"] += len(chunks)
        self.stats["total_processing_time"] += processing_time

        # 统计字节数
        total_bytes = sum(chunk.byte_length for chunk in chunks)
        self.stats["total_bytes_processed"] += total_bytes

        # 更新平均块大小
        if self.stats["total_chunks_created"] > 0:
            self.stats["average_chunk_size"] = (
                self.stats["total_bytes_processed"] / self.stats["total_chunks_created"]
            )

        # 更新语言分布
        lang_key = language.value
        self.stats["language_distribution"][lang_key] = (
            self.stats["language_distribution"].get(lang_key, 0) + len(chunks)
        )

        # 更新内容类型分布
        content_key = content_type.value
        self.stats["content_type_distribution"][content_key] = (
            self.stats["content_type_distribution"].get(content_key, 0) + len(chunks)
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            **self.stats,
            "config": self.config.to_dict(),
            "langchain_available": LANGCHAIN_AVAILABLE
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_chunks_created": 0,
            "total_bytes_processed": 0,
            "total_processing_time": 0.0,
            "language_distribution": {},
            "content_type_distribution": {},
            "average_chunk_size": 0.0
        }

    async def chunk_file(
        self,
        file_path: str,
        encoding: str = 'utf-8',
        metadata: Dict[str, Any] = None
    ) -> List[ChunkInfo]:
        """
        分块文件

        Args:
            file_path: 文件路径
            encoding: 文件编码
            metadata: 额外元数据

        Returns:
            分块信息列表
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                text = f.read()

            filename = file_path.split('/')[-1]  # 提取文件名

            # 添加文件信息到元数据
            file_metadata = metadata or {}
            file_metadata.update({
                "file_path": file_path,
                "file_name": filename,
                "file_size": len(text.encode('utf-8')),
                "encoding": encoding
            })

            return await self.chunk_text(text, filename, file_metadata)

        except Exception as e:
            logger.error(f"分块文件失败: {file_path}, 错误: {e}")
            raise

    async def batch_chunk_texts(
        self,
        texts: List[str],
        filenames: List[str] = None,
        metadatas: List[Dict[str, Any]] = None
    ) -> List[List[ChunkInfo]]:
        """
        批量分块文本

        Args:
            texts: 文本列表
            filenames: 文件名列表（可选）
            metadatas: 元数据列表（可选）

        Returns:
            分块信息列表的列表
        """
        if not texts:
            return []

        # 准备参数
        filenames = filenames or [None] * len(texts)
        metadatas = metadatas or [None] * len(texts)

        # 确保列表长度一致
        min_length = min(len(texts), len(filenames), len(metadatas))
        texts = texts[:min_length]
        filenames = filenames[:min_length]
        metadatas = metadatas[:min_length]

        if self.config.enable_parallel_processing and self.executor:
            # 并行处理
            tasks = []
            for text, filename, metadata in zip(texts, filenames, metadatas):
                task = asyncio.create_task(self.chunk_text(text, filename, metadata))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理异常
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"批量分块第{i}个文本失败: {result}")
                    final_results.append([])
                else:
                    final_results.append(result)

            return final_results
        else:
            # 串行处理
            results = []
            for text, filename, metadata in zip(texts, filenames, metadatas):
                try:
                    chunks = await self.chunk_text(text, filename, metadata)
                    results.append(chunks)
                except Exception as e:
                    logger.error(f"批量分块文本失败: {e}")
                    results.append([])

            return results

    def close(self):
        """关闭分块器，释放资源"""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None

        logger.info("文本分块器已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
