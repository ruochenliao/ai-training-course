"""
智能文本分块系统
支持多种文档类型的语义分块，包括Markdown、代码、多语言文本等

核心组件：
- ChunkerConfig: 分块配置类，支持字节级大小控制和重叠比例
- TextChunker: 智能文本分块器，支持多种分块策略
- ChunkInfo: 文本块信息数据结构
- LanguageDetector: 语言检测器
- ContentTypeDetector: 内容类型检测器

支持功能：
- Markdown智能分块（标题层级、特殊块保护）
- 多语言支持（中英文自动检测和分割）
- 特殊内容处理（代码块、表格、数学公式保护）
- 字节级大小控制和重叠比例配置
- 并行处理和批量操作
- 详细的统计信息和性能监控
"""

# 导入配置类和枚举
from .chunker_config import (
    ChunkerConfig,
    ChunkStrategy,
    LanguageType,
    ContentType
)

# 导入核心分块器
from .text_chunker import (
    TextChunker,
    ChunkInfo,
    ProtectedBlock,
    LanguageDetector,
    ContentTypeDetector
)

# 导出所有公共接口
__all__ = [
    # 配置类和枚举
    'ChunkerConfig',
    'ChunkStrategy',
    'LanguageType',
    'ContentType',
    
    # 核心分块器
    'TextChunker',
    'ChunkInfo',
    'ProtectedBlock',
    'LanguageDetector',
    'ContentTypeDetector'
]

# 版本信息
__version__ = "1.0.0"
__author__ = "Intelligent Customer Service Team"
__description__ = "智能文本分块系统 - 支持多种文档类型的语义分块"

# 便捷函数
def create_default_chunker(
    chunk_size: int = 1024,
    overlap_ratio: float = 0.1,
    strategy: ChunkStrategy = ChunkStrategy.RECURSIVE
) -> TextChunker:
    """
    创建默认配置的文本分块器
    
    Args:
        chunk_size: 块大小（字节）
        overlap_ratio: 重叠比例
        strategy: 分块策略
        
    Returns:
        文本分块器实例
    """
    config = ChunkerConfig(
        chunk_size=chunk_size,
        chunk_overlap_ratio=overlap_ratio,
        strategy=strategy
    )
    return TextChunker(config)


def create_markdown_chunker(
    chunk_size: int = 1024,
    overlap_ratio: float = 0.1
) -> TextChunker:
    """
    创建Markdown专用分块器
    
    Args:
        chunk_size: 块大小（字节）
        overlap_ratio: 重叠比例
        
    Returns:
        Markdown分块器实例
    """
    config = ChunkerConfig.create_markdown_config(chunk_size, overlap_ratio)
    return TextChunker(config)


def create_code_chunker(
    chunk_size: int = 2048,
    overlap_ratio: float = 0.05
) -> TextChunker:
    """
    创建代码文件专用分块器
    
    Args:
        chunk_size: 块大小（字节）
        overlap_ratio: 重叠比例
        
    Returns:
        代码分块器实例
    """
    config = ChunkerConfig.create_code_config(chunk_size, overlap_ratio)
    return TextChunker(config)


def create_chinese_chunker(
    chunk_size: int = 1024,
    overlap_ratio: float = 0.1
) -> TextChunker:
    """
    创建中文文本专用分块器
    
    Args:
        chunk_size: 块大小（字节）
        overlap_ratio: 重叠比例
        
    Returns:
        中文分块器实例
    """
    config = ChunkerConfig.create_chinese_config(chunk_size, overlap_ratio)
    return TextChunker(config)


def create_english_chunker(
    chunk_size: int = 1024,
    overlap_ratio: float = 0.1
) -> TextChunker:
    """
    创建英文文本专用分块器
    
    Args:
        chunk_size: 块大小（字节）
        overlap_ratio: 重叠比例
        
    Returns:
        英文分块器实例
    """
    config = ChunkerConfig.create_english_config(chunk_size, overlap_ratio)
    return TextChunker(config)


async def chunk_text_simple(
    text: str,
    chunk_size: int = 1024,
    overlap_ratio: float = 0.1,
    strategy: ChunkStrategy = ChunkStrategy.RECURSIVE
) -> List[ChunkInfo]:
    """
    简单文本分块函数
    
    Args:
        text: 输入文本
        chunk_size: 块大小（字节）
        overlap_ratio: 重叠比例
        strategy: 分块策略
        
    Returns:
        分块信息列表
    """
    chunker = create_default_chunker(chunk_size, overlap_ratio, strategy)
    try:
        return await chunker.chunk_text(text)
    finally:
        chunker.close()


async def chunk_markdown_simple(
    text: str,
    chunk_size: int = 1024,
    overlap_ratio: float = 0.1
) -> List[ChunkInfo]:
    """
    简单Markdown分块函数
    
    Args:
        text: Markdown文本
        chunk_size: 块大小（字节）
        overlap_ratio: 重叠比例
        
    Returns:
        分块信息列表
    """
    chunker = create_markdown_chunker(chunk_size, overlap_ratio)
    try:
        return await chunker.chunk_text(text)
    finally:
        chunker.close()


async def chunk_file_simple(
    file_path: str,
    chunk_size: int = 1024,
    overlap_ratio: float = 0.1,
    encoding: str = 'utf-8'
) -> List[ChunkInfo]:
    """
    简单文件分块函数
    
    Args:
        file_path: 文件路径
        chunk_size: 块大小（字节）
        overlap_ratio: 重叠比例
        encoding: 文件编码
        
    Returns:
        分块信息列表
    """
    chunker = create_default_chunker(chunk_size, overlap_ratio)
    try:
        return await chunker.chunk_file(file_path, encoding)
    finally:
        chunker.close()


# 示例用法
"""
# 基本用法示例

# 1. 使用默认配置分块文本
from app.services.text_chunker import chunk_text_simple

text = "这是一个很长的文档内容..."
chunks = await chunk_text_simple(text, chunk_size=1024, overlap_ratio=0.1)

# 2. 使用Markdown专用分块器
from app.services.text_chunker import create_markdown_chunker

markdown_text = '''
# 标题1
这是第一段内容...

## 标题2
这是第二段内容...

```python
def hello():
    print("Hello, World!")
```
'''

chunker = create_markdown_chunker(chunk_size=512)
chunks = await chunker.chunk_text(markdown_text)
chunker.close()

# 3. 使用自定义配置
from app.services.text_chunker import ChunkerConfig, TextChunker, ChunkStrategy

config = ChunkerConfig(
    chunk_size=2048,
    chunk_overlap_ratio=0.15,
    strategy=ChunkStrategy.SEMANTIC,
    language=LanguageType.CHINESE,
    enable_parallel_processing=True
)

chunker = TextChunker(config)
chunks = await chunker.chunk_text(text)
stats = chunker.get_stats()
chunker.close()

# 4. 批量处理文件
texts = ["文本1", "文本2", "文本3"]
batch_results = await chunker.batch_chunk_texts(texts)

# 5. 使用上下文管理器
with TextChunker(config) as chunker:
    chunks = await chunker.chunk_text(text)
    # 自动关闭资源
"""

# 配置示例
"""
# 配置示例

# 基础配置
basic_config = ChunkerConfig(
    chunk_size=1024,           # 1KB块大小
    chunk_overlap_ratio=0.1,   # 10%重叠
    strategy=ChunkStrategy.RECURSIVE
)

# Markdown配置
markdown_config = ChunkerConfig.create_markdown_config(
    chunk_size=1024,
    overlap_ratio=0.1
)

# 代码文件配置
code_config = ChunkerConfig.create_code_config(
    chunk_size=2048,
    overlap_ratio=0.05
)

# 中文文本配置
chinese_config = ChunkerConfig.create_chinese_config(
    chunk_size=1024,
    overlap_ratio=0.1
)

# 高级配置
advanced_config = ChunkerConfig(
    chunk_size=1024,
    chunk_overlap_ratio=0.1,
    strategy=ChunkStrategy.ADAPTIVE,
    language=LanguageType.AUTO,
    content_type=ContentType.PLAIN_TEXT,
    enable_parallel_processing=True,
    max_workers=4,
    debug_mode=True,
    preserve_structure_info=True
)
"""
