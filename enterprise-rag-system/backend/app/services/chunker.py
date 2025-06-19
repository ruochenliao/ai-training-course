"""
智能文档分块服务
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from loguru import logger

from app.core.config import settings
from app.core.exceptions import DocumentProcessingException
from app.models.knowledge import DocumentChunk


@dataclass
class ChunkConfig:
    """分块配置"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    strategy: str = "semantic"  # semantic, recursive, fixed
    preserve_structure: bool = True
    min_chunk_size: int = 100
    max_chunk_size: int = 2000


class DocumentChunker:
    """智能文档分块器"""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            strategy=settings.CHUNK_STRATEGY
        )
        
        # 结构化分隔符优先级
        self.separators = [
            "\n\n\n",  # 章节分隔
            "\n\n",    # 段落分隔
            "\n",      # 行分隔
            "。",      # 句子分隔（中文）
            ".",       # 句子分隔（英文）
            "；",      # 分号（中文）
            ";",       # 分号（英文）
            "，",      # 逗号（中文）
            ",",       # 逗号（英文）
            " ",       # 空格
            ""         # 字符级别
        ]
        
        # 保护块模式
        self.protected_patterns = [
            r'```[\s\S]*?```',           # 代码块
            r'\|.*?\|.*?\n(?:\|.*?\|.*?\n)*',  # 表格
            r'\$\$[\s\S]*?\$\$',         # LaTeX公式块
            r'\$[^$]*?\$',               # 内联公式
            r'!\[.*?\]\(.*?\)',          # 图片链接
            r'\[.*?\]\(.*?\)',           # 普通链接
        ]
    
    async def chunk_text(
        self, 
        text: str, 
        document_id: int,
        knowledge_base_id: int,
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """对文本进行智能分块"""
        try:
            if self.config.strategy == "semantic":
                return await self._semantic_chunking(text, document_id, knowledge_base_id, metadata)
            elif self.config.strategy == "recursive":
                return await self._recursive_chunking(text, document_id, knowledge_base_id, metadata)
            else:
                return await self._fixed_chunking(text, document_id, knowledge_base_id, metadata)
                
        except Exception as e:
            logger.error(f"文档分块失败: {e}")
            raise DocumentProcessingException(f"文档分块失败: {e}")
    
    async def _semantic_chunking(
        self, 
        text: str, 
        document_id: int,
        knowledge_base_id: int,
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """语义感知分块"""
        try:
            # 预处理：识别和保护特殊块
            protected_blocks, processed_text = self._protect_special_blocks(text)
            
            # 按段落分割
            paragraphs = self._split_by_paragraphs(processed_text)
            
            # 语义相似度分组
            chunks = await self._group_by_semantic_similarity(paragraphs)
            
            # 后处理：恢复特殊块
            chunks = self._restore_special_blocks(chunks, protected_blocks)
            
            # 创建DocumentChunk对象
            return await self._create_document_chunks(
                chunks, document_id, knowledge_base_id, metadata
            )
            
        except Exception as e:
            logger.error(f"语义分块失败: {e}")
            # 降级到递归分块
            return await self._recursive_chunking(text, document_id, knowledge_base_id, metadata)
    
    async def _recursive_chunking(
        self, 
        text: str, 
        document_id: int,
        knowledge_base_id: int,
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """递归分块"""
        try:
            # 保护特殊块
            protected_blocks, processed_text = self._protect_special_blocks(text)
            
            # 递归分割
            chunks = self._recursive_split(processed_text, self.separators)
            
            # 恢复特殊块
            chunks = self._restore_special_blocks(chunks, protected_blocks)
            
            # 创建DocumentChunk对象
            return await self._create_document_chunks(
                chunks, document_id, knowledge_base_id, metadata
            )
            
        except Exception as e:
            logger.error(f"递归分块失败: {e}")
            # 降级到固定分块
            return await self._fixed_chunking(text, document_id, knowledge_base_id, metadata)
    
    async def _fixed_chunking(
        self, 
        text: str, 
        document_id: int,
        knowledge_base_id: int,
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """固定大小分块"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            # 如果不是最后一块，尝试在合适的位置分割
            if end < len(text):
                # 寻找最近的句号或换行符
                for i in range(end, max(start + self.config.min_chunk_size, end - 100), -1):
                    if text[i] in ['。', '.', '\n']:
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(chunk_text)
            
            # 计算下一个起始位置（考虑重叠）
            start = end - self.config.chunk_overlap
            if start < 0:
                start = end
        
        # 创建DocumentChunk对象
        return await self._create_document_chunks(
            chunks, document_id, knowledge_base_id, metadata
        )
    
    def _protect_special_blocks(self, text: str) -> Tuple[List[Dict], str]:
        """保护特殊块"""
        protected_blocks = []
        processed_text = text
        
        for i, pattern in enumerate(self.protected_patterns):
            matches = list(re.finditer(pattern, processed_text, re.MULTILINE))
            
            for j, match in enumerate(reversed(matches)):  # 从后往前替换，避免位置偏移
                placeholder = f"__PROTECTED_BLOCK_{i}_{j}__"
                protected_blocks.append({
                    'placeholder': placeholder,
                    'content': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'type': self._get_block_type(pattern)
                })
                
                processed_text = (
                    processed_text[:match.start()] + 
                    placeholder + 
                    processed_text[match.end():]
                )
        
        return protected_blocks, processed_text
    
    def _restore_special_blocks(self, chunks: List[str], protected_blocks: List[Dict]) -> List[str]:
        """恢复特殊块"""
        restored_chunks = []
        
        for chunk in chunks:
            restored_chunk = chunk
            for block in protected_blocks:
                if block['placeholder'] in restored_chunk:
                    restored_chunk = restored_chunk.replace(
                        block['placeholder'], 
                        block['content']
                    )
            restored_chunks.append(restored_chunk)
        
        return restored_chunks
    
    def _get_block_type(self, pattern: str) -> str:
        """根据模式获取块类型"""
        if 'code' in pattern or '```' in pattern:
            return 'code'
        elif 'table' in pattern or '|' in pattern:
            return 'table'
        elif '$' in pattern:
            return 'formula'
        elif '!' in pattern and '](' in pattern:
            return 'image'
        elif '](' in pattern:
            return 'link'
        else:
            return 'unknown'
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 清理空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    async def _group_by_semantic_similarity(self, paragraphs: List[str]) -> List[str]:
        """按语义相似度分组段落"""
        # 这里应该使用嵌入模型计算相似度
        # 简化实现：按长度和位置分组
        
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            # 如果当前块加上新段落超过最大大小，开始新块
            if (current_size + paragraph_size > self.config.chunk_size and 
                current_size > self.config.min_chunk_size):
                
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                
                current_chunk = paragraph
                current_size = paragraph_size
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size += paragraph_size
        
        # 添加最后一个块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """递归分割文本"""
        if not separators:
            return [text] if text else []
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        # 如果文本长度小于最大块大小，直接返回
        if len(text) <= self.config.max_chunk_size:
            return [text] if text else []
        
        # 按当前分隔符分割
        if separator:
            parts = text.split(separator)
        else:
            # 字符级别分割
            parts = [text[i:i+self.config.chunk_size] 
                    for i in range(0, len(text), self.config.chunk_size)]
        
        chunks = []
        current_chunk = ""
        
        for part in parts:
            # 如果部分本身就太大，递归分割
            if len(part) > self.config.max_chunk_size:
                # 先保存当前块
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # 递归分割大部分
                sub_chunks = self._recursive_split(part, remaining_separators)
                chunks.extend(sub_chunks)
            else:
                # 尝试添加到当前块
                potential_chunk = current_chunk + separator + part if current_chunk else part
                
                if len(potential_chunk) <= self.config.chunk_size:
                    current_chunk = potential_chunk
                else:
                    # 当前块已满，开始新块
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = part
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    async def _create_document_chunks(
        self, 
        chunks: List[str], 
        document_id: int,
        knowledge_base_id: int,
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """创建DocumentChunk对象"""
        document_chunks = []
        
        for i, chunk_content in enumerate(chunks):
            if not chunk_content.strip():
                continue
            
            # 计算内容哈希
            content_hash = hashlib.md5(chunk_content.encode()).hexdigest()
            
            # 计算统计信息
            char_count = len(chunk_content)
            word_count = len(chunk_content.split())
            
            # 创建分块元数据
            chunk_metadata = {
                **metadata,
                'chunk_strategy': self.config.strategy,
                'chunk_config': {
                    'chunk_size': self.config.chunk_size,
                    'chunk_overlap': self.config.chunk_overlap
                }
            }
            
            # 创建DocumentChunk
            chunk = await DocumentChunk.create(
                document_id=document_id,
                chunk_index=i,
                content=chunk_content,
                content_hash=content_hash,
                char_count=char_count,
                word_count=word_count,
                metadata=chunk_metadata
            )
            
            document_chunks.append(chunk)
        
        logger.info(f"创建了 {len(document_chunks)} 个文档分块")
        return document_chunks
    
    def _calculate_chunk_quality(self, chunk: str) -> float:
        """计算分块质量评分"""
        score = 1.0
        
        # 长度评分
        length = len(chunk)
        if length < self.config.min_chunk_size:
            score *= 0.5
        elif length > self.config.max_chunk_size:
            score *= 0.7
        
        # 完整性评分（是否以句号结尾）
        if not chunk.strip().endswith(('。', '.', '!', '?', '！', '？')):
            score *= 0.9
        
        # 结构完整性评分
        if chunk.count('(') != chunk.count(')'):
            score *= 0.8
        if chunk.count('[') != chunk.count(']'):
            score *= 0.8
        if chunk.count('{') != chunk.count('}'):
            score *= 0.8
        
        return min(score, 1.0)
    
    def get_chunk_preview(self, chunk: str, max_length: int = 100) -> str:
        """获取分块预览"""
        if len(chunk) <= max_length:
            return chunk
        return chunk[:max_length] + "..."
