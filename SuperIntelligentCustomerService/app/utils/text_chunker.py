"""
文本分块工具
简化版本，用于向量数据库集成
"""
import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ChunkerConfig:
    """分块配置"""
    chunk_size_bytes: int = 1024
    overlap_ratio: float = 0.1
    respect_special_blocks: bool = True
    preserve_markdown_structure: bool = True
    language: str = 'auto'


class TextChunker:
    """文本分块器"""
    
    @staticmethod
    def chunk_text(text: str, config: ChunkerConfig) -> List[str]:
        """
        基础文本分块
        
        Args:
            text: 输入文本
            config: 分块配置
            
        Returns:
            文本块列表
        """
        if not text.strip():
            return []
        
        chunks = []
        chunk_size = config.chunk_size_bytes
        overlap_size = int(chunk_size * config.overlap_ratio)
        
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # 如果不是最后一块，尝试在合适的位置分割
            if end < text_length:
                # 寻找合适的分割点
                for split_char in ['\n\n', '\n', '。', '！', '？', '.', '!', '?', '；', ';']:
                    split_pos = text.rfind(split_char, start, end)
                    if split_pos > start:
                        end = split_pos + len(split_char)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 计算下一个开始位置，考虑重叠
            start = max(start + 1, end - overlap_size)
        
        return chunks
    
    @staticmethod
    def chunk_markdown(text: str, config: ChunkerConfig) -> List[str]:
        """
        Markdown感知的文本分块
        
        Args:
            text: Markdown文本
            config: 分块配置
            
        Returns:
            文本块列表
        """
        if not text.strip():
            return []
        
        # 如果不需要保持Markdown结构，使用基础分块
        if not config.preserve_markdown_structure:
            return TextChunker.chunk_text(text, config)
        
        # 简单的Markdown分块：按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        chunk_size = config.chunk_size_bytes
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前段落加上现有块超过大小限制
            if current_chunk and len(current_chunk) + len(paragraph) + 2 > chunk_size:
                # 保存当前块
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # 添加到当前块
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


def get_byte_length(text: str) -> int:
    """获取文本的字节长度"""
    return len(text.encode('utf-8'))


# 兼容性常量
LANGCHAIN_AVAILABLE = False
