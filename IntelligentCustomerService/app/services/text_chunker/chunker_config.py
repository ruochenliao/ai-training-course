"""
文本分块配置类
支持字节级大小控制、重叠比例、语言设置等配置选项
"""
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional


class ChunkStrategy(str, Enum):
    """分块策略枚举"""
    RECURSIVE = "recursive"      # 递归分块（默认）
    SEMANTIC = "semantic"        # 语义分块
    MARKDOWN = "markdown"        # Markdown结构分块
    FIXED = "fixed"             # 固定长度分块
    ADAPTIVE = "adaptive"        # 自适应分块


class LanguageType(str, Enum):
    """语言类型枚举"""
    AUTO = "auto"               # 自动检测
    CHINESE = "chinese"         # 中文
    ENGLISH = "english"         # 英文
    MIXED = "mixed"            # 中英混合


class ContentType(str, Enum):
    """内容类型枚举"""
    PLAIN_TEXT = "plain_text"   # 纯文本
    MARKDOWN = "markdown"       # Markdown文档
    CODE = "code"              # 代码文件
    HTML = "html"              # HTML文档
    JSON = "json"              # JSON数据
    XML = "xml"                # XML文档


@dataclass
class ChunkerConfig:
    """
    文本分块器配置类
    支持字节级大小控制、重叠比例、语言设置等
    """
    
    # 基础配置
    chunk_size: int = 1024                    # 块大小（字节）
    chunk_overlap_ratio: float = 0.1         # 重叠比例（10%）
    min_chunk_size: int = 100                 # 最小块大小（字节）
    max_chunk_size: int = 4096               # 最大块大小（字节）
    
    # 策略配置
    strategy: ChunkStrategy = ChunkStrategy.RECURSIVE
    language: LanguageType = LanguageType.AUTO
    content_type: ContentType = ContentType.PLAIN_TEXT
    
    # 语言特定配置
    chinese_separators: List[str] = field(default_factory=lambda: [
        "\n\n\n",  # 章节分隔
        "\n\n",    # 段落分隔
        "\n",      # 行分隔
        "。",      # 句号
        "！",      # 感叹号
        "？",      # 问号
        "；",      # 分号
        "，",      # 逗号
        "、",      # 顿号
        " ",       # 空格
        ""         # 字符级别
    ])
    
    english_separators: List[str] = field(default_factory=lambda: [
        "\n\n\n",  # 章节分隔
        "\n\n",    # 段落分隔
        "\n",      # 行分隔
        ". ",      # 句点+空格
        "! ",      # 感叹号+空格
        "? ",      # 问号+空格
        "; ",      # 分号+空格
        ", ",      # 逗号+空格
        " ",       # 空格
        ""         # 字符级别
    ])
    
    # Markdown特定配置
    markdown_headers: List[str] = field(default_factory=lambda: [
        "# ",      # H1
        "## ",     # H2
        "### ",    # H3
        "#### ",   # H4
        "##### ",  # H5
        "###### "  # H6
    ])
    
    # 特殊块保护模式
    protected_patterns: Dict[str, str] = field(default_factory=lambda: {
        "code_block": r'```[\s\S]*?```',                    # 代码块
        "inline_code": r'`[^`\n]+`',                        # 内联代码
        "math_block": r'\$\$[\s\S]*?\$\$',                  # 数学公式块
        "inline_math": r'\$[^$\n]+\$',                      # 内联数学公式
        "table": r'\|.*?\|.*?\n(?:\|.*?\|.*?\n)*',          # Markdown表格
        "image": r'!\[.*?\]\(.*?\)',                        # 图片链接
        "link": r'\[.*?\]\(.*?\)',                          # 普通链接
        "html_tag": r'<[^>]+>.*?</[^>]+>',                  # HTML标签
        "yaml_front_matter": r'^---\n[\s\S]*?\n---\n',     # YAML前置元数据
    })
    
    # 性能配置
    enable_parallel_processing: bool = True    # 启用并行处理
    max_workers: int = 4                      # 最大工作线程数
    batch_size: int = 100                     # 批处理大小
    
    # 质量控制配置
    min_meaningful_length: int = 20           # 最小有意义长度
    remove_empty_chunks: bool = True          # 移除空块
    remove_whitespace_only: bool = True       # 移除仅包含空白字符的块
    normalize_whitespace: bool = True         # 标准化空白字符
    
    # 调试配置
    debug_mode: bool = False                  # 调试模式
    preserve_structure_info: bool = True      # 保留结构信息
    add_chunk_metadata: bool = True           # 添加块元数据
    
    def __post_init__(self):
        """初始化后验证和调整配置"""
        # 验证块大小配置
        if self.chunk_size < self.min_chunk_size:
            self.chunk_size = self.min_chunk_size
        
        if self.chunk_size > self.max_chunk_size:
            self.chunk_size = self.max_chunk_size
        
        # 验证重叠比例
        if self.chunk_overlap_ratio < 0:
            self.chunk_overlap_ratio = 0
        elif self.chunk_overlap_ratio >= 1:
            self.chunk_overlap_ratio = 0.9
        
        # 计算重叠大小
        self.chunk_overlap = int(self.chunk_size * self.chunk_overlap_ratio)
        
        # 验证工作线程数
        if self.max_workers < 1:
            self.max_workers = 1
        elif self.max_workers > 16:
            self.max_workers = 16
    
    @property
    def chunk_overlap_bytes(self) -> int:
        """获取重叠字节数"""
        return self.chunk_overlap
    
    @property
    def effective_chunk_size(self) -> int:
        """获取有效块大小（考虑重叠）"""
        return self.chunk_size - self.chunk_overlap
    
    def get_separators_for_language(self, language: LanguageType = None) -> List[str]:
        """
        根据语言类型获取分隔符
        
        Args:
            language: 语言类型，如果为None则使用配置的语言
            
        Returns:
            分隔符列表
        """
        lang = language or self.language
        
        if lang == LanguageType.CHINESE:
            return self.chinese_separators
        elif lang == LanguageType.ENGLISH:
            return self.english_separators
        elif lang == LanguageType.MIXED:
            # 混合语言：合并中英文分隔符
            mixed_separators = []
            # 先添加通用分隔符
            for sep in ["\n\n\n", "\n\n", "\n"]:
                if sep not in mixed_separators:
                    mixed_separators.append(sep)
            
            # 添加中文分隔符
            for sep in self.chinese_separators[3:]:  # 跳过已添加的换行符
                if sep not in mixed_separators:
                    mixed_separators.append(sep)
            
            # 添加英文分隔符
            for sep in self.english_separators[3:]:  # 跳过已添加的换行符
                if sep not in mixed_separators:
                    mixed_separators.append(sep)
            
            return mixed_separators
        else:  # AUTO
            # 自动检测时使用混合分隔符
            return self.get_separators_for_language(LanguageType.MIXED)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap_ratio": self.chunk_overlap_ratio,
            "chunk_overlap": self.chunk_overlap,
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size,
            "strategy": self.strategy.value,
            "language": self.language.value,
            "content_type": self.content_type.value,
            "enable_parallel_processing": self.enable_parallel_processing,
            "max_workers": self.max_workers,
            "batch_size": self.batch_size,
            "debug_mode": self.debug_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkerConfig':
        """从字典创建配置对象"""
        # 转换枚举值
        if "strategy" in data:
            data["strategy"] = ChunkStrategy(data["strategy"])
        if "language" in data:
            data["language"] = LanguageType(data["language"])
        if "content_type" in data:
            data["content_type"] = ContentType(data["content_type"])
        
        return cls(**data)
    
    @classmethod
    def create_markdown_config(
        cls,
        chunk_size: int = 1024,
        overlap_ratio: float = 0.1
    ) -> 'ChunkerConfig':
        """创建Markdown专用配置"""
        return cls(
            chunk_size=chunk_size,
            chunk_overlap_ratio=overlap_ratio,
            strategy=ChunkStrategy.MARKDOWN,
            content_type=ContentType.MARKDOWN,
            preserve_structure_info=True
        )
    
    @classmethod
    def create_code_config(
        cls,
        chunk_size: int = 2048,
        overlap_ratio: float = 0.05
    ) -> 'ChunkerConfig':
        """创建代码文件专用配置"""
        return cls(
            chunk_size=chunk_size,
            chunk_overlap_ratio=overlap_ratio,
            strategy=ChunkStrategy.RECURSIVE,
            content_type=ContentType.CODE,
            normalize_whitespace=False  # 代码文件保持原始空白字符
        )
    
    @classmethod
    def create_chinese_config(
        cls,
        chunk_size: int = 1024,
        overlap_ratio: float = 0.1
    ) -> 'ChunkerConfig':
        """创建中文文本专用配置"""
        return cls(
            chunk_size=chunk_size,
            chunk_overlap_ratio=overlap_ratio,
            language=LanguageType.CHINESE,
            strategy=ChunkStrategy.SEMANTIC
        )
    
    @classmethod
    def create_english_config(
        cls,
        chunk_size: int = 1024,
        overlap_ratio: float = 0.1
    ) -> 'ChunkerConfig':
        """创建英文文本专用配置"""
        return cls(
            chunk_size=chunk_size,
            chunk_overlap_ratio=overlap_ratio,
            language=LanguageType.ENGLISH,
            strategy=ChunkStrategy.RECURSIVE
        )
