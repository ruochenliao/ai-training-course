"""
智能文档分块服务 - 企业级RAG系统
严格按照技术栈要求：RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
支持语义分块、递归分块、固定分块策略
"""
import hashlib
import re
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any

import jieba
from app.core.config import settings
from app.models.sqlalchemy_models import DocumentChunk, ChunkType
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import (
    CharacterTextSplitter,
    TokenTextSplitter,
    MarkdownHeaderTextSplitter
)
from loguru import logger


class ChunkStrategy(str, Enum):
    """分块策略枚举"""
    RECURSIVE = "recursive"  # 递归分块 (默认)
    SEMANTIC = "semantic"    # 语义分块
    FIXED = "fixed"         # 固定长度分块
    MARKDOWN = "markdown"   # Markdown结构分块
    TOKEN = "token"         # Token级别分块


class IntelligentChunker:
    """智能文档分块器"""
    
    def __init__(self):
        self.default_chunk_size = 1000
        self.default_overlap = 200
        self.max_chunk_size = 2000
        self.min_chunk_size = 100
        
        # 中文分句正则
        self.chinese_sentence_pattern = re.compile(r'[。！？；\n]+')
        
        # 初始化jieba分词
        jieba.initialize()
        
        # 分块质量评估阈值
        self.quality_thresholds = {
            "min_chars": 50,
            "max_chars": 2000,
            "min_words": 10,
            "max_overlap_ratio": 0.5
        }
    
    def create_recursive_splitter(self, chunk_size: int = None, overlap: int = None) -> RecursiveCharacterTextSplitter:
        """创建递归字符分割器"""
        chunk_size = chunk_size or self.default_chunk_size
        overlap = overlap or self.default_overlap
        
        # 中英文混合分隔符
        separators = [
            "\n\n",  # 段落分隔
            "\n",    # 行分隔
            "。",    # 中文句号
            "！",    # 中文感叹号
            "？",    # 中文问号
            "；",    # 中文分号
            ".",     # 英文句号
            "!",     # 英文感叹号
            "?",     # 英文问号
            ";",     # 英文分号
            " ",     # 空格
            "",      # 字符级别
        ]
        
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=separators,
            keep_separator=True,
            is_separator_regex=False,
            length_function=len
        )
    
    def create_semantic_splitter(self, chunk_size: int = None) -> CharacterTextSplitter:
        """创建语义分块器"""
        chunk_size = chunk_size or self.default_chunk_size
        
        return CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=self.default_overlap,
            separator="\n\n",
            keep_separator=True,
            length_function=len
        )
    
    def create_markdown_splitter(self) -> MarkdownHeaderTextSplitter:
        """创建Markdown结构分块器"""
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        
        return MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )
    
    def create_token_splitter(self, chunk_size: int = None) -> TokenTextSplitter:
        """创建Token级别分块器"""
        chunk_size = chunk_size or (self.default_chunk_size // 4)  # Token通常比字符少
        
        return TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=self.default_overlap // 4,
            encoding_name="cl100k_base"  # GPT-4使用的编码
        )
    
    def detect_content_type(self, content: str) -> ChunkType:
        """检测内容类型"""
        content_lower = content.lower().strip()
        
        # 检测代码块
        if any(keyword in content_lower for keyword in ['def ', 'class ', 'import ', 'function', '```', 'SELECT', 'INSERT']):
            return ChunkType.CODE
        
        # 检测表格
        if '|' in content and content.count('|') > 4:
            return ChunkType.TABLE
        
        # 检测图片引用
        if any(keyword in content_lower for keyword in ['![', '<img', 'image:', '图片', '图像']):
            return ChunkType.IMAGE
        
        # 默认为文本
        return ChunkType.TEXT
    
    def calculate_chunk_hash(self, content: str) -> str:
        """计算分块内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def assess_chunk_quality(self, chunk: str) -> Dict[str, Any]:
        """评估分块质量"""
        char_count = len(chunk)
        word_count = len(jieba.lcut(chunk))
        line_count = chunk.count('\n') + 1
        
        # 计算质量分数
        quality_score = 1.0
        issues = []
        
        # 检查长度
        if char_count < self.quality_thresholds["min_chars"]:
            quality_score -= 0.3
            issues.append("chunk_too_short")
        elif char_count > self.quality_thresholds["max_chars"]:
            quality_score -= 0.2
            issues.append("chunk_too_long")
        
        # 检查词数
        if word_count < self.quality_thresholds["min_words"]:
            quality_score -= 0.2
            issues.append("insufficient_words")
        
        # 检查完整性 (是否以句号结尾)
        if not chunk.strip().endswith(('。', '.', '！', '!', '？', '?')):
            quality_score -= 0.1
            issues.append("incomplete_sentence")
        
        quality_score = max(0.0, quality_score)
        
        return {
            "quality_score": quality_score,
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "issues": issues,
            "is_high_quality": quality_score >= 0.7
        }
    
    def chunk_text(
        self, 
        content: str, 
        strategy: ChunkStrategy = ChunkStrategy.RECURSIVE,
        chunk_size: int = None,
        overlap: int = None,
        preserve_structure: bool = True
    ) -> List[Dict[str, Any]]:
        """智能分块文本"""
        try:
            logger.info(f"开始分块文本，策略: {strategy}, 长度: {len(content)}")
            
            # 预处理内容
            content = self._preprocess_content(content)
            
            # 根据策略选择分块器
            if strategy == ChunkStrategy.RECURSIVE:
                splitter = self.create_recursive_splitter(chunk_size, overlap)
                chunks = splitter.split_text(content)
            
            elif strategy == ChunkStrategy.SEMANTIC:
                chunks = self._semantic_chunk(content, chunk_size)
            
            elif strategy == ChunkStrategy.MARKDOWN:
                splitter = self.create_markdown_splitter()
                docs = splitter.split_text(content)
                chunks = [doc.page_content for doc in docs]
            
            elif strategy == ChunkStrategy.TOKEN:
                splitter = self.create_token_splitter(chunk_size)
                chunks = splitter.split_text(content)
            
            elif strategy == ChunkStrategy.FIXED:
                chunks = self._fixed_chunk(content, chunk_size or self.default_chunk_size)
            
            else:
                raise ValueError(f"不支持的分块策略: {strategy}")
            
            # 处理分块结果
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                chunk_info = {
                    "index": i,
                    "content": chunk.strip(),
                    "content_hash": self.calculate_chunk_hash(chunk.strip()),
                    "chunk_type": self.detect_content_type(chunk),
                    "strategy": strategy,
                    "quality": self.assess_chunk_quality(chunk.strip()),
                    "metadata": {
                        "start_position": content.find(chunk) if chunk in content else -1,
                        "end_position": content.find(chunk) + len(chunk) if chunk in content else -1,
                        "chunk_size_actual": len(chunk.strip()),
                        "created_at": datetime.now().isoformat()
                    }
                }
                
                processed_chunks.append(chunk_info)
            
            logger.info(f"分块完成，共生成 {len(processed_chunks)} 个分块")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"文本分块失败: {e}")
            raise
    
    def _preprocess_content(self, content: str) -> str:
        """预处理内容"""
        # 清理多余的空白字符
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        # 确保段落间有适当的分隔
        content = re.sub(r'([。！？])\s*([A-Z\u4e00-\u9fff])', r'\1\n\n\2', content)
        
        return content.strip()
    
    def _semantic_chunk(self, content: str, chunk_size: int = None) -> List[str]:
        """语义分块"""
        chunk_size = chunk_size or self.default_chunk_size
        
        # 按段落分割
        paragraphs = content.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前分块加上新段落不超过限制，则合并
            if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 保存当前分块
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个段落过长，需要进一步分割
                if len(paragraph) > chunk_size:
                    sub_chunks = self._split_long_paragraph(paragraph, chunk_size)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # 添加最后一个分块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str, chunk_size: int) -> List[str]:
        """分割过长的段落"""
        # 按句子分割
        sentences = self.chinese_sentence_pattern.split(paragraph)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                if current_chunk:
                    current_chunk += sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个句子仍然过长，强制分割
                if len(sentence) > chunk_size:
                    for i in range(0, len(sentence), chunk_size):
                        chunks.append(sentence[i:i + chunk_size])
                    current_chunk = ""
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _fixed_chunk(self, content: str, chunk_size: int) -> List[str]:
        """固定长度分块"""
        chunks = []
        overlap = self.default_overlap
        
        for i in range(0, len(content), chunk_size - overlap):
            chunk = content[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def optimize_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """优化分块结果"""
        optimized_chunks = []
        
        for chunk in chunks:
            # 跳过低质量分块
            if chunk["quality"]["quality_score"] < 0.3:
                logger.warning(f"跳过低质量分块: {chunk['quality']['issues']}")
                continue
            
            # 合并过短的相邻分块
            if (optimized_chunks and 
                chunk["quality"]["char_count"] < self.quality_thresholds["min_chars"] and
                optimized_chunks[-1]["quality"]["char_count"] < self.default_chunk_size // 2):
                
                # 合并分块
                last_chunk = optimized_chunks[-1]
                merged_content = last_chunk["content"] + "\n\n" + chunk["content"]
                merged_hash = self.calculate_chunk_hash(merged_content)
                merged_quality = self.assess_chunk_quality(merged_content)
                
                optimized_chunks[-1] = {
                    **last_chunk,
                    "content": merged_content,
                    "content_hash": merged_hash,
                    "quality": merged_quality,
                    "metadata": {
                        **last_chunk["metadata"],
                        "merged": True,
                        "original_chunks": [last_chunk["index"], chunk["index"]]
                    }
                }
                
                logger.info(f"合并分块 {last_chunk['index']} 和 {chunk['index']}")
            else:
                optimized_chunks.append(chunk)
        
        # 重新编号
        for i, chunk in enumerate(optimized_chunks):
            chunk["index"] = i
        
        return optimized_chunks
    
    def get_chunking_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取分块统计信息"""
        if not chunks:
            return {}
        
        total_chunks = len(chunks)
        total_chars = sum(chunk["quality"]["char_count"] for chunk in chunks)
        total_words = sum(chunk["quality"]["word_count"] for chunk in chunks)
        
        quality_scores = [chunk["quality"]["quality_score"] for chunk in chunks]
        high_quality_count = sum(1 for chunk in chunks if chunk["quality"]["is_high_quality"])
        
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk["chunk_type"]
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "total_words": total_words,
            "avg_chunk_size": total_chars / total_chunks if total_chunks > 0 else 0,
            "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "high_quality_ratio": high_quality_count / total_chunks if total_chunks > 0 else 0,
            "chunk_types": chunk_types,
            "quality_distribution": {
                "excellent": sum(1 for s in quality_scores if s >= 0.9),
                "good": sum(1 for s in quality_scores if 0.7 <= s < 0.9),
                "fair": sum(1 for s in quality_scores if 0.5 <= s < 0.7),
                "poor": sum(1 for s in quality_scores if s < 0.5)
            }
        }


# 全局智能分块器实例
intelligent_chunker = IntelligentChunker()


# 便捷函数
async def chunk_document_content(
    content: str,
    strategy: ChunkStrategy = ChunkStrategy.RECURSIVE,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[Dict[str, Any]]:
    """分块文档内容的便捷函数"""
    chunks = intelligent_chunker.chunk_text(
        content=content,
        strategy=strategy,
        chunk_size=chunk_size,
        overlap=overlap
    )
    
    # 优化分块结果
    optimized_chunks = intelligent_chunker.optimize_chunks(chunks)
    
    return optimized_chunks


async def get_chunking_statistics(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """获取分块统计信息的便捷函数"""
    return intelligent_chunker.get_chunking_stats(chunks)
