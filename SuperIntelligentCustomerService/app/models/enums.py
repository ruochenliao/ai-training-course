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
    GENERAL = "general"
    TECHNICAL = "technical"
    FAQ = "faq"
    POLICY = "policy"
    PRODUCT = "product"


class EmbeddingStatus(StrEnum):
    """嵌入处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(StrEnum):
    """文件类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    JPG = "jpg"
    PNG = "png"
    XLSX = "xlsx"
    PPTX = "pptx"

