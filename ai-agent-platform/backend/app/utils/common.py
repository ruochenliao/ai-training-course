"""
通用工具函数
"""
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
import re


def generate_uuid() -> str:
    """
    生成UUID字符串
    
    Returns:
        UUID字符串
    """
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """
    生成短ID
    
    Args:
        length: ID长度
        
    Returns:
        短ID字符串
    """
    return str(uuid.uuid4()).replace('-', '')[:length]


def calculate_md5(content: str) -> str:
    """
    计算字符串的MD5哈希值
    
    Args:
        content: 要计算哈希的字符串
        
    Returns:
        MD5哈希值
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def calculate_sha256(content: str) -> str:
    """
    计算字符串的SHA256哈希值
    
    Args:
        content: 要计算哈希的字符串
        
    Returns:
        SHA256哈希值
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化后的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否为有效邮箱格式
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username: str) -> bool:
    """
    验证用户名格式
    
    Args:
        username: 用户名
        
    Returns:
        是否为有效用户名格式
    """
    # 用户名只能包含字母、数字、下划线，长度3-20位
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None


def clean_text(text: str) -> str:
    """
    清理文本内容
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 移除特殊字符（保留基本标点）
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"\'-]', '', text)
    
    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    提取关键词（简单实现）
    
    Args:
        text: 文本内容
        max_keywords: 最大关键词数量
        
    Returns:
        关键词列表
    """
    # 简单的关键词提取：分词并过滤停用词
    words = re.findall(r'\b\w+\b', text.lower())
    
    # 简单的停用词列表
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # 过滤停用词和短词
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    
    # 统计词频并返回最常见的词
    from collections import Counter
    word_counts = Counter(keywords)
    
    return [word for word, count in word_counts.most_common(max_keywords)]


def safe_int(value: Any, default: int = 0) -> int:
    """
    安全转换为整数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        转换后的整数
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全转换为浮点数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        转换后的浮点数
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并多个字典
    
    Args:
        *dicts: 要合并的字典
        
    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def get_current_timestamp() -> int:
    """
    获取当前时间戳
    
    Returns:
        当前时间戳（秒）
    """
    return int(datetime.now().timestamp())


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        
    Returns:
        格式化后的日期时间字符串
    """
    return dt.strftime(format_str)
