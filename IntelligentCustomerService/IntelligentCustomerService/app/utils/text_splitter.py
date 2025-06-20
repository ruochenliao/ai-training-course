"""
智能文本分割器
基于语义和结构的智能文档分块
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from loguru import logger


@dataclass
class ChunkConfig:
    """分块配置"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    preserve_structure: bool = True
    respect_sentence_boundaries: bool = True


class IntelligentTextSplitter:
    """智能文本分割器"""
    
    def __init__(self):
        """初始化分割器"""
        # 分割优先级（从高到低）
        self.separators = [
            "\n\n\n",  # 多个换行（章节分隔）
            "\n\n",    # 双换行（段落分隔）
            "\n",      # 单换行（行分隔）
            "。",      # 中文句号
            "！",      # 中文感叹号
            "？",      # 中文问号
            ".",       # 英文句号
            "!",       # 英文感叹号
            "?",       # 英文问号
            ";",       # 分号
            "；",      # 中文分号
            ",",       # 逗号
            "，",      # 中文逗号
            " ",       # 空格
            ""         # 字符级分割（最后手段）
        ]
        
        # 结构标记模式
        self.structure_patterns = {
            'title': re.compile(r'^#{1,6}\s+.+$', re.MULTILINE),  # Markdown标题
            'list_item': re.compile(r'^\s*[-*+]\s+.+$', re.MULTILINE),  # 列表项
            'numbered_list': re.compile(r'^\s*\d+\.\s+.+$', re.MULTILINE),  # 编号列表
            'code_block': re.compile(r'```[\s\S]*?```', re.MULTILINE),  # 代码块
            'table_row': re.compile(r'\|.*\|', re.MULTILINE),  # 表格行
            'section_break': re.compile(r'^[-=]{3,}$', re.MULTILINE),  # 分节符
        }
        
        logger.info("智能文本分割器初始化完成")
    
    def split_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        config: Optional[ChunkConfig] = None
    ) -> List[str]:
        """
        智能分割文本
        
        Args:
            text: 要分割的文本
            chunk_size: 目标分块大小
            chunk_overlap: 分块重叠大小
            config: 分块配置
            
        Returns:
            分割后的文本块列表
        """
        if config is None:
            config = ChunkConfig(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        try:
            # 预处理文本
            text = self._preprocess_text(text)
            
            if len(text) <= config.chunk_size:
                return [text] if text.strip() else []
            
            # 检测文档结构
            structure_info = self._analyze_structure(text) if config.preserve_structure else {}
            
            # 执行分割
            if config.preserve_structure and structure_info:
                chunks = self._structure_aware_split(text, config, structure_info)
            else:
                chunks = self._recursive_split(text, config)
            
            # 后处理
            chunks = self._post_process_chunks(chunks, config)
            
            logger.info(f"文本分割完成: {len(text)} 字符 -> {len(chunks)} 个分块")
            return chunks
            
        except Exception as e:
            logger.error(f"文本分割失败: {e}")
            # 降级到简单分割
            return self._simple_split(text, config)
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 标准化换行符
        text = re.sub(r'\r\n|\r', '\n', text)
        
        # 移除过多的空白字符
        text = re.sub(r'\n{4,}', '\n\n\n', text)  # 最多保留3个连续换行
        text = re.sub(r'[ \t]{2,}', ' ', text)    # 多个空格/制表符合并为一个空格
        
        # 移除行首行尾空白
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """分析文档结构"""
        structure = {
            'titles': [],
            'lists': [],
            'code_blocks': [],
            'tables': [],
            'sections': []
        }
        
        try:
            # 检测标题
            for match in self.structure_patterns['title'].finditer(text):
                structure['titles'].append({
                    'start': match.start(),
                    'end': match.end(),
                    'level': len(match.group().split()[0]),  # #的数量
                    'text': match.group()
                })
            
            # 检测列表
            for match in self.structure_patterns['list_item'].finditer(text):
                structure['lists'].append({
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'bullet',
                    'text': match.group()
                })
            
            for match in self.structure_patterns['numbered_list'].finditer(text):
                structure['lists'].append({
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'numbered',
                    'text': match.group()
                })
            
            # 检测代码块
            for match in self.structure_patterns['code_block'].finditer(text):
                structure['code_blocks'].append({
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group()
                })
            
            # 检测表格
            table_lines = []
            for match in self.structure_patterns['table_row'].finditer(text):
                table_lines.append({
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group()
                })
            
            # 合并连续的表格行
            if table_lines:
                current_table = [table_lines[0]]
                for line in table_lines[1:]:
                    if line['start'] - current_table[-1]['end'] < 10:  # 行间距小于10字符
                        current_table.append(line)
                    else:
                        if len(current_table) > 1:  # 至少2行才算表格
                            structure['tables'].append({
                                'start': current_table[0]['start'],
                                'end': current_table[-1]['end'],
                                'rows': len(current_table)
                            })
                        current_table = [line]
                
                if len(current_table) > 1:
                    structure['tables'].append({
                        'start': current_table[0]['start'],
                        'end': current_table[-1]['end'],
                        'rows': len(current_table)
                    })
            
        except Exception as e:
            logger.warning(f"结构分析失败: {e}")
        
        return structure
    
    def _structure_aware_split(
        self,
        text: str,
        config: ChunkConfig,
        structure_info: Dict[str, Any]
    ) -> List[str]:
        """结构感知的分割"""
        chunks = []
        current_pos = 0
        
        # 获取所有结构边界点
        boundaries = []
        
        for title in structure_info.get('titles', []):
            boundaries.append(('title', title['start'], title['end']))
        
        for table in structure_info.get('tables', []):
            boundaries.append(('table', table['start'], table['end']))
        
        for code_block in structure_info.get('code_blocks', []):
            boundaries.append(('code', code_block['start'], code_block['end']))
        
        # 按位置排序
        boundaries.sort(key=lambda x: x[1])
        
        for boundary_type, start, end in boundaries:
            # 处理边界前的文本
            if start > current_pos:
                before_text = text[current_pos:start].strip()
                if before_text:
                    chunks.extend(self._recursive_split(before_text, config))
            
            # 处理结构化内容
            structure_text = text[start:end].strip()
            if structure_text:
                if boundary_type == 'code' or boundary_type == 'table':
                    # 代码块和表格尽量保持完整
                    if len(structure_text) <= config.max_chunk_size:
                        chunks.append(structure_text)
                    else:
                        chunks.extend(self._recursive_split(structure_text, config))
                else:
                    chunks.extend(self._recursive_split(structure_text, config))
            
            current_pos = end
        
        # 处理剩余文本
        if current_pos < len(text):
            remaining_text = text[current_pos:].strip()
            if remaining_text:
                chunks.extend(self._recursive_split(remaining_text, config))
        
        return chunks
    
    def _recursive_split(self, text: str, config: ChunkConfig) -> List[str]:
        """递归分割文本"""
        if len(text) <= config.chunk_size:
            return [text] if text.strip() else []
        
        # 尝试使用不同的分隔符
        for separator in self.separators:
            if separator in text:
                parts = text.split(separator)
                if len(parts) > 1:
                    chunks = []
                    current_chunk = ""
                    
                    for part in parts:
                        # 重新添加分隔符（除了最后一个空字符串分隔符）
                        if separator and part:
                            part = part + separator
                        
                        if len(current_chunk) + len(part) <= config.chunk_size:
                            current_chunk += part
                        else:
                            if current_chunk.strip():
                                chunks.append(current_chunk.strip())
                            
                            if len(part) > config.chunk_size:
                                # 递归处理过长的部分
                                chunks.extend(self._recursive_split(part, config))
                                current_chunk = ""
                            else:
                                current_chunk = part
                    
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    
                    # 添加重叠
                    if config.chunk_overlap > 0 and len(chunks) > 1:
                        chunks = self._add_overlap(chunks, config.chunk_overlap)
                    
                    return chunks
        
        # 如果没有找到合适的分隔符，强制分割
        return self._force_split(text, config)
    
    def _force_split(self, text: str, config: ChunkConfig) -> List[str]:
        """强制分割文本"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + config.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:].strip())
                break
            
            # 尝试在句子边界分割
            if config.respect_sentence_boundaries:
                for i in range(end, max(start + config.min_chunk_size, end - 100), -1):
                    if text[i] in ['。', '！', '？', '.', '!', '?']:
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - config.chunk_overlap
        
        return chunks
    
    def _add_overlap(self, chunks: List[str], overlap_size: int) -> List[str]:
        """添加分块重叠"""
        if len(chunks) <= 1 or overlap_size <= 0:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]
            
            # 从前一个分块的末尾提取重叠内容
            if len(prev_chunk) > overlap_size:
                overlap_text = prev_chunk[-overlap_size:]
                # 尝试在句子边界开始重叠
                for j in range(len(overlap_text)):
                    if overlap_text[j] in ['。', '！', '？', '.', '!', '?', '\n']:
                        overlap_text = overlap_text[j + 1:]
                        break
                
                if overlap_text.strip():
                    current_chunk = overlap_text + " " + current_chunk
            
            overlapped_chunks.append(current_chunk)
        
        return overlapped_chunks
    
    def _post_process_chunks(self, chunks: List[str], config: ChunkConfig) -> List[str]:
        """后处理分块"""
        processed_chunks = []
        
        for chunk in chunks:
            chunk = chunk.strip()
            
            # 过滤过短的分块
            if len(chunk) < config.min_chunk_size:
                # 尝试与前一个分块合并
                if processed_chunks and len(processed_chunks[-1]) + len(chunk) <= config.max_chunk_size:
                    processed_chunks[-1] += "\n" + chunk
                    continue
                # 如果无法合并且内容有意义，仍然保留
                elif chunk and not chunk.isspace():
                    processed_chunks.append(chunk)
            else:
                processed_chunks.append(chunk)
        
        return processed_chunks
    
    def _simple_split(self, text: str, config: ChunkConfig) -> List[str]:
        """简单分割（降级方案）"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + config.chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - config.chunk_overlap
        
        return chunks


# 全局智能文本分割器实例
intelligent_text_splitter = IntelligentTextSplitter()
