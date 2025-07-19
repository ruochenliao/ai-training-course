"""
文件类型配置
定义支持的文件类型和处理方法
"""
from enum import Enum
from typing import Dict, List


class FileProcessingMethod(Enum):
    """文件处理方法"""
    TEXT = "text"
    MARKDOWN = "markdown"
    PDF_CONVERTER = "pdf_converter"


# 文件扩展名到处理方法的映射
FILE_TYPE_MAPPING: Dict[str, FileProcessingMethod] = {
    '.txt': FileProcessingMethod.TEXT,
    '.md': FileProcessingMethod.MARKDOWN,
    '.markdown': FileProcessingMethod.MARKDOWN,
    '.pdf': FileProcessingMethod.PDF_CONVERTER,
    '.docx': FileProcessingMethod.PDF_CONVERTER,
    '.doc': FileProcessingMethod.PDF_CONVERTER,
    '.xlsx': FileProcessingMethod.PDF_CONVERTER,
    '.xls': FileProcessingMethod.PDF_CONVERTER,
    '.pptx': FileProcessingMethod.PDF_CONVERTER,
    '.ppt': FileProcessingMethod.PDF_CONVERTER,
}

# 支持的文件扩展名
SUPPORTED_EXTENSIONS: List[str] = list(FILE_TYPE_MAPPING.keys())


def get_processing_method(file_extension: str) -> FileProcessingMethod:
    """
    根据文件扩展名获取处理方法
    
    Args:
        file_extension: 文件扩展名（包含点号）
        
    Returns:
        处理方法
        
    Raises:
        ValueError: 不支持的文件类型
    """
    extension = file_extension.lower()
    if extension not in FILE_TYPE_MAPPING:
        raise ValueError(f"不支持的文件类型: {extension}")
    
    return FILE_TYPE_MAPPING[extension]


def is_supported_extension(file_extension: str) -> bool:
    """
    检查文件扩展名是否支持
    
    Args:
        file_extension: 文件扩展名（包含点号）
        
    Returns:
        是否支持
    """
    return file_extension.lower() in FILE_TYPE_MAPPING
