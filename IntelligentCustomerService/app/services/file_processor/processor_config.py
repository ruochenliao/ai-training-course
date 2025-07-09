"""
文件处理器配置类
定义处理状态、任务配置和转换器设置
"""
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional


class ProcessingStatus(str, Enum):
    """文件处理状态枚举"""
    PENDING = "pending"           # 等待处理
    QUEUED = "queued"            # 已加入队列
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"       # 处理完成
    FAILED = "failed"            # 处理失败
    CANCELLED = "cancelled"       # 已取消
    RETRYING = "retrying"        # 重试中


class FileType(str, Enum):
    """支持的文件类型枚举"""
    # PDF文档
    PDF = "pdf"
    
    # Office文档
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    DOC = "doc"
    XLS = "xls"
    PPT = "ppt"
    
    # 文本文件
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    HTML = "html"
    RTF = "rtf"
    
    # 图片文件
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    BMP = "bmp"
    WEBP = "webp"
    TIFF = "tiff"
    
    # 其他
    UNKNOWN = "unknown"


class ConversionMethod(str, Enum):
    """转换方法枚举"""
    MARKER_PDF = "marker_pdf"           # 使用marker-pdf转换PDF
    PYTHON_DOCX = "python_docx"         # 使用python-docx转换Word
    OPENPYXL = "openpyxl"              # 使用openpyxl转换Excel
    PYTHON_PPTX = "python_pptx"        # 使用python-pptx转换PowerPoint
    MULTIMODAL_LLM = "multimodal_llm"   # 使用多模态LLM处理图片
    DIRECT_READ = "direct_read"         # 直接读取文本文件
    PANDAS = "pandas"                   # 使用pandas处理CSV
    BEAUTIFULSOUP = "beautifulsoup"     # 使用BeautifulSoup处理HTML


@dataclass
class ProcessorConfig:
    """文件处理器配置"""
    
    # 基础配置
    max_workers: int = 4                    # 最大工作进程数
    queue_size: int = 1000                  # 任务队列大小
    batch_size: int = 10                    # 批处理大小
    
    # 超时配置
    processing_timeout: int = 300           # 处理超时时间（秒）
    queue_timeout: int = 60                 # 队列等待超时时间（秒）
    
    # 重试配置
    max_retries: int = 3                    # 最大重试次数
    retry_delay: float = 5.0                # 重试延迟（秒）
    exponential_backoff: bool = True        # 是否使用指数退避
    
    # 文件大小限制
    max_file_size: int = 100 * 1024 * 1024  # 最大文件大小（100MB）
    max_image_size: int = 10 * 1024 * 1024  # 最大图片大小（10MB）
    
    # 临时文件配置
    temp_dir: str = field(default_factory=lambda: str(Path.home() / ".file_processor_temp"))
    cleanup_temp_files: bool = True         # 是否清理临时文件
    temp_file_ttl: int = 3600              # 临时文件生存时间（秒）
    
    # 转换器配置
    supported_formats: Dict[FileType, ConversionMethod] = field(default_factory=lambda: {
        # PDF文档
        FileType.PDF: ConversionMethod.MARKER_PDF,
        
        # Office文档
        FileType.DOCX: ConversionMethod.PYTHON_DOCX,
        FileType.XLSX: ConversionMethod.OPENPYXL,
        FileType.PPTX: ConversionMethod.PYTHON_PPTX,
        FileType.DOC: ConversionMethod.PYTHON_DOCX,  # 需要先转换为docx
        FileType.XLS: ConversionMethod.OPENPYXL,     # 需要先转换为xlsx
        FileType.PPT: ConversionMethod.PYTHON_PPTX,  # 需要先转换为pptx
        
        # 文本文件
        FileType.TXT: ConversionMethod.DIRECT_READ,
        FileType.MD: ConversionMethod.DIRECT_READ,
        FileType.CSV: ConversionMethod.PANDAS,
        FileType.JSON: ConversionMethod.DIRECT_READ,
        FileType.XML: ConversionMethod.DIRECT_READ,
        FileType.HTML: ConversionMethod.BEAUTIFULSOUP,
        FileType.RTF: ConversionMethod.DIRECT_READ,
        
        # 图片文件
        FileType.JPG: ConversionMethod.MULTIMODAL_LLM,
        FileType.JPEG: ConversionMethod.MULTIMODAL_LLM,
        FileType.PNG: ConversionMethod.MULTIMODAL_LLM,
        FileType.GIF: ConversionMethod.MULTIMODAL_LLM,
        FileType.BMP: ConversionMethod.MULTIMODAL_LLM,
        FileType.WEBP: ConversionMethod.MULTIMODAL_LLM,
        FileType.TIFF: ConversionMethod.MULTIMODAL_LLM,
    })
    
    # Marker PDF配置
    marker_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_pages": None,
        "langs": ["zh", "en"],
        "batch_multiplier": 2,
        "extract_images": True,
        "extract_tables": True
    })
    
    # 多模态LLM配置
    multimodal_config: Dict[str, Any] = field(default_factory=lambda: {
        "model_name": "qwen-vl-plus",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "max_tokens": 2000,
        "temperature": 0.1,
        "default_prompt": "请详细描述这张图片的内容，包括主要对象、场景、文字信息等。",
        "batch_size": 5,
        "timeout": 30
    })
    
    # Office文档配置
    office_config: Dict[str, Any] = field(default_factory=lambda: {
        "extract_images": True,
        "extract_tables": True,
        "preserve_formatting": True,
        "include_headers_footers": True
    })
    
    # 文本处理配置
    text_config: Dict[str, Any] = field(default_factory=lambda: {
        "encoding": "utf-8",
        "fallback_encodings": ["gbk", "gb2312", "latin-1"],
        "normalize_whitespace": True,
        "remove_empty_lines": True
    })
    
    # 数据库配置
    database_config: Dict[str, Any] = field(default_factory=lambda: {
        "update_interval": 5.0,  # 状态更新间隔（秒）
        "batch_update": True,    # 是否批量更新
        "enable_progress_tracking": True
    })
    
    # 日志配置
    logging_config: Dict[str, Any] = field(default_factory=lambda: {
        "log_level": "INFO",
        "log_file": None,
        "enable_performance_logging": True,
        "log_processing_details": True
    })
    
    def __post_init__(self):
        """初始化后验证和调整配置"""
        # 确保临时目录存在
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        
        # 验证工作进程数
        if self.max_workers < 1:
            self.max_workers = 1
        elif self.max_workers > 16:
            self.max_workers = 16
        
        # 验证队列大小
        if self.queue_size < 10:
            self.queue_size = 10
        
        # 验证重试次数
        if self.max_retries < 0:
            self.max_retries = 0
        elif self.max_retries > 10:
            self.max_retries = 10
    
    @classmethod
    def detect_file_type(cls, file_path: str) -> FileType:
        """
        检测文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件类型
        """
        if not file_path:
            return FileType.UNKNOWN
        
        # 获取文件扩展名
        ext = Path(file_path).suffix.lower().lstrip('.')
        
        # 映射扩展名到文件类型
        ext_mapping = {
            'pdf': FileType.PDF,
            'docx': FileType.DOCX,
            'xlsx': FileType.XLSX,
            'pptx': FileType.PPTX,
            'doc': FileType.DOC,
            'xls': FileType.XLS,
            'ppt': FileType.PPT,
            'txt': FileType.TXT,
            'md': FileType.MD,
            'markdown': FileType.MD,
            'csv': FileType.CSV,
            'json': FileType.JSON,
            'xml': FileType.XML,
            'html': FileType.HTML,
            'htm': FileType.HTML,
            'rtf': FileType.RTF,
            'jpg': FileType.JPG,
            'jpeg': FileType.JPEG,
            'png': FileType.PNG,
            'gif': FileType.GIF,
            'bmp': FileType.BMP,
            'webp': FileType.WEBP,
            'tiff': FileType.TIFF,
            'tif': FileType.TIFF
        }
        
        return ext_mapping.get(ext, FileType.UNKNOWN)
    
    def is_supported(self, file_type: FileType) -> bool:
        """
        检查文件类型是否支持
        
        Args:
            file_type: 文件类型
            
        Returns:
            是否支持
        """
        return file_type in self.supported_formats
    
    def get_conversion_method(self, file_type: FileType) -> Optional[ConversionMethod]:
        """
        获取文件类型对应的转换方法
        
        Args:
            file_type: 文件类型
            
        Returns:
            转换方法
        """
        return self.supported_formats.get(file_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "max_workers": self.max_workers,
            "queue_size": self.queue_size,
            "batch_size": self.batch_size,
            "processing_timeout": self.processing_timeout,
            "max_retries": self.max_retries,
            "max_file_size": self.max_file_size,
            "temp_dir": self.temp_dir,
            "supported_formats": {k.value: v.value for k, v in self.supported_formats.items()},
            "marker_config": self.marker_config,
            "multimodal_config": {k: v for k, v in self.multimodal_config.items() if k != "api_key"},
            "office_config": self.office_config,
            "text_config": self.text_config
        }
    
    @classmethod
    def create_default_config(cls) -> 'ProcessorConfig':
        """创建默认配置"""
        return cls()
    
    @classmethod
    def create_high_performance_config(cls) -> 'ProcessorConfig':
        """创建高性能配置"""
        return cls(
            max_workers=8,
            queue_size=2000,
            batch_size=20,
            processing_timeout=600,
            max_retries=5
        )
    
    @classmethod
    def create_low_resource_config(cls) -> 'ProcessorConfig':
        """创建低资源配置"""
        return cls(
            max_workers=2,
            queue_size=100,
            batch_size=5,
            processing_timeout=180,
            max_retries=2
        )
