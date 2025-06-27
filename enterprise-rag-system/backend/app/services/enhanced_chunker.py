"""
增强版智能文档分块服务
支持语义分块、结构感知、质量评估、自适应分块
"""

import hashlib
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from app.core.config import settings
from app.services.chunker import DocumentChunker, ChunkConfig
from app.services.embedding_service import embedding_service
from loguru import logger

from app.core.exceptions import DocumentProcessingException


@dataclass
class EnhancedChunkConfig:
    """增强版分块配置"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    strategy: str = "adaptive"  # adaptive, semantic, recursive, fixed, structure_aware
    preserve_structure: bool = True
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    
    # 语义分块参数
    semantic_similarity_threshold: float = 0.8
    semantic_window_size: int = 3
    
    # 结构感知参数
    respect_headers: bool = True
    respect_lists: bool = True
    respect_tables: bool = True
    respect_code_blocks: bool = True
    
    # 质量控制参数
    min_quality_score: float = 0.7
    enable_quality_filter: bool = True
    
    # 自适应参数
    adaptive_threshold: float = 0.75
    content_type_weights: Dict[str, float] = field(default_factory=lambda: {
        'text': 1.0,
        'code': 0.8,
        'table': 0.9,
        'list': 0.85,
        'header': 1.1
    })


@dataclass
class ChunkAnalysis:
    """分块分析结果"""
    chunk_id: str
    content: str
    content_type: str
    quality_score: float
    semantic_coherence: float
    structure_integrity: float
    readability_score: float
    metadata: Dict[str, Any]
    
    def overall_score(self) -> float:
        """计算综合评分"""
        return (
            self.quality_score * 0.3 +
            self.semantic_coherence * 0.3 +
            self.structure_integrity * 0.2 +
            self.readability_score * 0.2
        )


class ContentTypeDetector:
    """内容类型检测器"""
    
    def __init__(self):
        self.patterns = {
            'header': [
                r'^#{1,6}\s+.+$',  # Markdown标题
                r'^.+\n[=-]+\s*$',  # 下划线标题
                r'^\d+\.\s+.+$',   # 数字标题
                r'^[一二三四五六七八九十]+[、\.]\s+.+$'  # 中文数字标题
            ],
            'list': [
                r'^\s*[-*+]\s+.+$',  # 无序列表
                r'^\s*\d+\.\s+.+$',  # 有序列表
                r'^\s*[a-zA-Z]\.\s+.+$',  # 字母列表
                r'^\s*[①②③④⑤⑥⑦⑧⑨⑩]\s+.+$'  # 圆圈数字列表
            ],
            'code': [
                r'```[\s\S]*?```',  # 代码块
                r'`[^`]+`',  # 内联代码
                r'^\s{4,}.+$',  # 缩进代码
            ],
            'table': [
                r'\|.*\|.*\n(?:\|.*\|.*\n)*',  # Markdown表格
                r'^\s*\+[-+]+\+\s*$',  # ASCII表格边框
            ],
            'formula': [
                r'\$\$[\s\S]*?\$\$',  # 块级公式
                r'\$[^$]+\$',  # 内联公式
            ],
            'quote': [
                r'^>\s+.+$',  # 引用
                r'^".*"$',  # 引号
                r'^「.*」$',  # 中文引号
            ]
        }
    
    def detect_content_type(self, text: str) -> str:
        """检测内容类型"""
        text_lines = text.split('\n')
        type_scores = defaultdict(int)
        
        for line in text_lines:
            line = line.strip()
            if not line:
                continue
                
            for content_type, patterns in self.patterns.items():
                for pattern in patterns:
                    if re.match(pattern, line, re.MULTILINE):
                        type_scores[content_type] += 1
                        break
        
        if not type_scores:
            return 'text'
        
        # 返回得分最高的类型
        return max(type_scores.items(), key=lambda x: x[1])[0]
    
    def analyze_structure(self, text: str) -> Dict[str, Any]:
        """分析文本结构"""
        lines = text.split('\n')
        structure = {
            'total_lines': len(lines),
            'empty_lines': sum(1 for line in lines if not line.strip()),
            'header_count': 0,
            'list_count': 0,
            'code_blocks': 0,
            'tables': 0,
            'avg_line_length': 0
        }
        
        line_lengths = []
        for line in lines:
            line_lengths.append(len(line))
            
            # 检测各种结构元素
            if re.match(r'^#{1,6}\s+', line):
                structure['header_count'] += 1
            elif re.match(r'^\s*[-*+]\s+', line):
                structure['list_count'] += 1
            elif re.match(r'```', line):
                structure['code_blocks'] += 1
            elif '|' in line and line.count('|') >= 2:
                structure['tables'] += 1
        
        structure['avg_line_length'] = np.mean(line_lengths) if line_lengths else 0
        structure['line_length_std'] = np.std(line_lengths) if line_lengths else 0
        
        return structure


class EnhancedDocumentChunker:
    """增强版智能文档分块器"""
    
    def __init__(self, config: Optional[EnhancedChunkConfig] = None):
        self.config = config or EnhancedChunkConfig()
        self.base_chunker = DocumentChunker()
        self.content_detector = ContentTypeDetector()
        
        # 缓存嵌入向量
        self.embedding_cache = {}
        
        logger.info("增强版文档分块器初始化完成")
    
    async def chunk_document(
        self,
        content: str,
        document_id: int,
        knowledge_base_id: int,
        metadata: Dict[str, Any] = None
    ) -> List[ChunkAnalysis]:
        """智能分块文档"""
        try:
            start_time = time.time()
            
            # 预处理内容
            processed_content = self._preprocess_content(content)
            
            # 根据策略选择分块方法
            if self.config.strategy == "adaptive":
                chunks = await self._adaptive_chunking(processed_content)
            elif self.config.strategy == "semantic":
                chunks = await self._semantic_chunking(processed_content)
            elif self.config.strategy == "structure_aware":
                chunks = await self._structure_aware_chunking(processed_content)
            else:
                # 回退到基础分块
                base_chunks = await self.base_chunker.chunk_text(
                    processed_content, document_id, knowledge_base_id, metadata or {}
                )
                chunks = [chunk.content for chunk in base_chunks]
            
            # 分析和评估分块
            chunk_analyses = await self._analyze_chunks(chunks, metadata or {})
            
            # 质量过滤
            if self.config.enable_quality_filter:
                chunk_analyses = self._filter_by_quality(chunk_analyses)
            
            # 后处理优化
            chunk_analyses = await self._post_process_chunks(chunk_analyses)
            
            processing_time = time.time() - start_time
            
            logger.info(f"文档分块完成: {len(chunk_analyses)} 个分块, 耗时: {processing_time:.2f}s")
            
            return chunk_analyses
            
        except Exception as e:
            logger.error(f"增强版文档分块失败: {e}")
            raise DocumentProcessingException(f"增强版文档分块失败: {e}")
    
    def _preprocess_content(self, content: str) -> str:
        """预处理内容"""
        # 标准化换行符
        content = re.sub(r'\r\n|\r', '\n', content)
        
        # 清理多余的空白字符
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # 标准化空格
        content = re.sub(r'[ \t]+', ' ', content)
        
        return content.strip()
    
    async def _adaptive_chunking(self, content: str) -> List[str]:
        """自适应分块"""
        # 分析内容特征
        content_type = self.content_detector.detect_content_type(content)
        structure = self.content_detector.analyze_structure(content)
        
        # 根据内容类型调整分块策略
        if content_type in ['code', 'table']:
            return await self._structure_aware_chunking(content)
        elif structure['header_count'] > 0:
            return await self._header_based_chunking(content)
        else:
            return await self._semantic_chunking(content)
    
    async def _semantic_chunking(self, content: str) -> List[str]:
        """语义感知分块"""
        try:
            # 按段落分割
            paragraphs = re.split(r'\n\s*\n', content)
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            if len(paragraphs) <= 1:
                return [content]
            
            # 计算段落嵌入
            embeddings = await self._get_paragraph_embeddings(paragraphs)
            
            # 基于语义相似度分组
            chunks = await self._group_by_semantic_similarity(paragraphs, embeddings)
            
            return chunks
            
        except Exception as e:
            logger.warning(f"语义分块失败，回退到递归分块: {e}")
            return self.base_chunker._recursive_split(content, self.base_chunker.separators)
    
    async def _structure_aware_chunking(self, content: str) -> List[str]:
        """结构感知分块"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 检测结构元素
            if self._is_header(line):
                # 保存当前块
                if current_chunk and current_size >= self.config.min_chunk_size:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # 开始新块
                current_chunk.append(line)
                current_size += len(line)
                
            elif self._is_code_block_start(line):
                # 处理代码块
                code_block, i = self._extract_code_block(lines, i)
                
                if current_size + len(code_block) > self.config.max_chunk_size:
                    if current_chunk:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                        current_size = 0
                
                current_chunk.append(code_block)
                current_size += len(code_block)
                
            elif self._is_table_start(line):
                # 处理表格
                table, i = self._extract_table(lines, i)
                
                if current_size + len(table) > self.config.max_chunk_size:
                    if current_chunk:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                        current_size = 0
                
                current_chunk.append(table)
                current_size += len(table)
                
            else:
                # 普通行
                if current_size + len(line) > self.config.max_chunk_size:
                    if current_chunk:
                        chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                        current_size = 0
                
                current_chunk.append(line)
                current_size += len(line)
            
            i += 1
        
        # 添加最后一个块
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    async def _header_based_chunking(self, content: str) -> List[str]:
        """基于标题的分块"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            if self._is_header(line) and current_chunk:
                # 遇到新标题，保存当前块
                chunk_content = '\n'.join(current_chunk).strip()
                if chunk_content:
                    chunks.append(chunk_content)
                current_chunk = [line]
            else:
                current_chunk.append(line)
        
        # 添加最后一个块
        if current_chunk:
            chunk_content = '\n'.join(current_chunk).strip()
            if chunk_content:
                chunks.append(chunk_content)
        
        return chunks
    
    async def _get_paragraph_embeddings(self, paragraphs: List[str]) -> List[List[float]]:
        """获取段落嵌入向量"""
        embeddings = []
        
        for paragraph in paragraphs:
            # 检查缓存
            cache_key = hashlib.md5(paragraph.encode()).hexdigest()
            if cache_key in self.embedding_cache:
                embeddings.append(self.embedding_cache[cache_key])
            else:
                try:
                    embedding = await embedding_service.embed_text(paragraph)
                    self.embedding_cache[cache_key] = embedding
                    embeddings.append(embedding)
                except Exception as e:
                    logger.warning(f"获取段落嵌入失败: {e}")
                    # 使用零向量作为后备
                    embeddings.append([0.0] * settings.EMBEDDING_DIMENSION)
        
        return embeddings
    
    async def _group_by_semantic_similarity(
        self, 
        paragraphs: List[str], 
        embeddings: List[List[float]]
    ) -> List[str]:
        """基于语义相似度分组段落"""
        if not embeddings or len(embeddings) != len(paragraphs):
            return paragraphs
        
        chunks = []
        current_chunk_paragraphs = []
        current_chunk_size = 0
        
        for i, (paragraph, embedding) in enumerate(zip(paragraphs, embeddings)):
            paragraph_size = len(paragraph)
            
            # 检查是否应该开始新块
            should_start_new_chunk = False
            
            if current_chunk_size + paragraph_size > self.config.chunk_size:
                should_start_new_chunk = True
            elif current_chunk_paragraphs and i > 0:
                # 计算与当前块的语义相似度
                prev_embedding = embeddings[i-1]
                similarity = self._calculate_cosine_similarity(embedding, prev_embedding)
                
                if similarity < self.config.semantic_similarity_threshold:
                    should_start_new_chunk = True
            
            if should_start_new_chunk and current_chunk_paragraphs:
                # 保存当前块
                chunk_content = '\n\n'.join(current_chunk_paragraphs)
                chunks.append(chunk_content)
                current_chunk_paragraphs = []
                current_chunk_size = 0
            
            current_chunk_paragraphs.append(paragraph)
            current_chunk_size += paragraph_size
        
        # 添加最后一个块
        if current_chunk_paragraphs:
            chunk_content = '\n\n'.join(current_chunk_paragraphs)
            chunks.append(chunk_content)
        
        return chunks
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception:
            return 0.0
    
    async def _analyze_chunks(self, chunks: List[str], metadata: Dict[str, Any]) -> List[ChunkAnalysis]:
        """分析分块质量"""
        analyses = []
        
        for i, chunk in enumerate(chunks):
            content_type = self.content_detector.detect_content_type(chunk)
            
            analysis = ChunkAnalysis(
                chunk_id=f"chunk_{i}",
                content=chunk,
                content_type=content_type,
                quality_score=self._calculate_quality_score(chunk),
                semantic_coherence=await self._calculate_semantic_coherence(chunk),
                structure_integrity=self._calculate_structure_integrity(chunk),
                readability_score=self._calculate_readability_score(chunk),
                metadata={
                    **metadata,
                    'chunk_index': i,
                    'content_type': content_type,
                    'char_count': len(chunk),
                    'word_count': len(chunk.split()),
                    'line_count': len(chunk.split('\n'))
                }
            )
            
            analyses.append(analysis)
        
        return analyses
    
    def _calculate_quality_score(self, chunk: str) -> float:
        """计算分块质量评分"""
        score = 1.0
        
        # 长度评分
        length = len(chunk)
        if length < self.config.min_chunk_size:
            score *= 0.5
        elif length > self.config.max_chunk_size:
            score *= 0.7
        
        # 完整性评分
        if not chunk.strip().endswith(('。', '.', '!', '?', '！', '？', '\n')):
            score *= 0.9
        
        # 结构完整性
        brackets = [('(', ')'), ('[', ']'), ('{', '}'), ('「', '」'), ('《', '》')]
        for open_b, close_b in brackets:
            if chunk.count(open_b) != chunk.count(close_b):
                score *= 0.8
        
        return min(score, 1.0)
    
    async def _calculate_semantic_coherence(self, chunk: str) -> float:
        """计算语义连贯性"""
        # 简化实现：基于句子间的词汇重叠
        sentences = re.split(r'[。.!?！？]', chunk)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            return 1.0
        
        coherence_scores = []
        for i in range(len(sentences) - 1):
            words1 = set(sentences[i].split())
            words2 = set(sentences[i + 1].split())
            
            if not words1 or not words2:
                continue
            
            overlap = len(words1 & words2)
            union = len(words1 | words2)
            
            if union > 0:
                coherence_scores.append(overlap / union)
        
        return np.mean(coherence_scores) if coherence_scores else 0.5
    
    def _calculate_structure_integrity(self, chunk: str) -> float:
        """计算结构完整性"""
        structure = self.content_detector.analyze_structure(chunk)
        
        score = 1.0
        
        # 检查是否有未闭合的结构
        if structure['code_blocks'] % 2 != 0:
            score *= 0.7
        
        # 检查行长度一致性
        if structure['line_length_std'] > structure['avg_line_length']:
            score *= 0.9
        
        return score
    
    def _calculate_readability_score(self, chunk: str) -> float:
        """计算可读性评分"""
        sentences = re.split(r'[。.!?！？]', chunk)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # 平均句长
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # 基于平均句长的可读性评分
        if avg_sentence_length <= 15:
            return 0.9
        elif avg_sentence_length <= 25:
            return 0.7
        elif avg_sentence_length <= 35:
            return 0.5
        else:
            return 0.3
    
    def _filter_by_quality(self, analyses: List[ChunkAnalysis]) -> List[ChunkAnalysis]:
        """基于质量过滤分块"""
        filtered = []
        
        for analysis in analyses:
            if analysis.overall_score() >= self.config.min_quality_score:
                filtered.append(analysis)
            else:
                logger.debug(f"过滤低质量分块: {analysis.chunk_id}, 评分: {analysis.overall_score():.3f}")
        
        return filtered
    
    async def _post_process_chunks(self, analyses: List[ChunkAnalysis]) -> List[ChunkAnalysis]:
        """后处理优化分块"""
        # 合并过小的相邻分块
        optimized = []
        i = 0
        
        while i < len(analyses):
            current = analyses[i]
            
            # 检查是否需要与下一个分块合并
            if (i + 1 < len(analyses) and 
                len(current.content) < self.config.min_chunk_size and
                len(current.content) + len(analyses[i + 1].content) <= self.config.max_chunk_size):
                
                # 合并分块
                next_chunk = analyses[i + 1]
                merged_content = current.content + '\n\n' + next_chunk.content
                
                merged_analysis = ChunkAnalysis(
                    chunk_id=f"merged_{current.chunk_id}_{next_chunk.chunk_id}",
                    content=merged_content,
                    content_type=current.content_type,
                    quality_score=(current.quality_score + next_chunk.quality_score) / 2,
                    semantic_coherence=(current.semantic_coherence + next_chunk.semantic_coherence) / 2,
                    structure_integrity=(current.structure_integrity + next_chunk.structure_integrity) / 2,
                    readability_score=(current.readability_score + next_chunk.readability_score) / 2,
                    metadata={
                        **current.metadata,
                        'merged': True,
                        'original_chunks': [current.chunk_id, next_chunk.chunk_id]
                    }
                )
                
                optimized.append(merged_analysis)
                i += 2  # 跳过下一个分块
            else:
                optimized.append(current)
                i += 1
        
        return optimized
    
    def _is_header(self, line: str) -> bool:
        """检查是否为标题"""
        patterns = [
            r'^#{1,6}\s+',  # Markdown标题
            r'^.+\n[=-]+\s*$',  # 下划线标题
            r'^\d+\.\s+.+$',   # 数字标题
        ]
        
        for pattern in patterns:
            if re.match(pattern, line.strip()):
                return True
        return False
    
    def _is_code_block_start(self, line: str) -> bool:
        """检查是否为代码块开始"""
        return line.strip().startswith('```')
    
    def _is_table_start(self, line: str) -> bool:
        """检查是否为表格开始"""
        return '|' in line and line.count('|') >= 2
    
    def _extract_code_block(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """提取代码块"""
        code_lines = [lines[start_idx]]
        i = start_idx + 1
        
        while i < len(lines):
            code_lines.append(lines[i])
            if lines[i].strip().startswith('```'):
                break
            i += 1
        
        return '\n'.join(code_lines), i
    
    def _extract_table(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """提取表格"""
        table_lines = [lines[start_idx]]
        i = start_idx + 1
        
        while i < len(lines) and '|' in lines[i]:
            table_lines.append(lines[i])
            i += 1
        
        return '\n'.join(table_lines), i - 1


# 全局增强版分块服务实例
enhanced_chunker = EnhancedDocumentChunker()
