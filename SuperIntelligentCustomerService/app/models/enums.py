from enum import Enum, StrEnum


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class MethodType(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class KnowledgeType(StrEnum):
    """知识库类型枚举"""
    GENERAL = "general"          # 通用知识库
    TECHNICAL = "technical"      # 技术文档
    FAQ = "faq"                 # 常见问题
    POLICY = "policy"           # 政策制度
    PRODUCT = "product"         # 产品说明
    TRAINING = "training"       # 培训材料
    CUSTOM = "custom"           # 自定义


class EmbeddingStatus(StrEnum):
    """文件嵌入处理状态枚举"""
    PENDING = "pending"         # 等待处理
    PROCESSING = "processing"   # 处理中
    COMPLETED = "completed"     # 处理完成
    FAILED = "failed"          # 处理失败


class FileType(StrEnum):
    """支持的文件类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    GIF = "gif"
    WEBP = "webp"
