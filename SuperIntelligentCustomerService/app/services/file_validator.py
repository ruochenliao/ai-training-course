"""
文件验证服务
实现文件上传的类型检查、大小限制、安全验证等功能
"""
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

import magic

from app.core.knowledge_logger import get_logger

logger = get_logger("file_processing")


@dataclass
class FileValidationResult:
    """文件验证结果"""
    is_valid: bool
    file_type: str
    file_size: int
    file_hash: str
    mime_type: str
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "is_valid": self.is_valid,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "mime_type": self.mime_type,
            "errors": self.errors,
            "warnings": self.warnings
        }


class FileValidator:
    """文件验证器"""
    
    # 支持的文件类型映射
    SUPPORTED_TYPES = {
        'pdf': {
            'extensions': ['.pdf'],
            'mime_types': ['application/pdf'],
            'max_size': 50 * 1024 * 1024,  # 50MB
            'description': 'PDF文档'
        },
        'docx': {
            'extensions': ['.docx'],
            'mime_types': [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ],
            'max_size': 30 * 1024 * 1024,  # 30MB
            'description': 'Word文档'
        },
        'doc': {
            'extensions': ['.doc'],
            'mime_types': ['application/msword'],
            'max_size': 30 * 1024 * 1024,  # 30MB
            'description': 'Word文档(旧版)'
        },
        'txt': {
            'extensions': ['.txt'],
            'mime_types': ['text/plain'],
            'max_size': 10 * 1024 * 1024,  # 10MB
            'description': '纯文本文件'
        },
        'md': {
            'extensions': ['.md', '.markdown'],
            'mime_types': ['text/markdown', 'text/plain'],
            'max_size': 5 * 1024 * 1024,  # 5MB
            'description': 'Markdown文档'
        },
        'xlsx': {
            'extensions': ['.xlsx'],
            'mime_types': [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ],
            'max_size': 20 * 1024 * 1024,  # 20MB
            'description': 'Excel表格'
        },
        'xls': {
            'extensions': ['.xls'],
            'mime_types': ['application/vnd.ms-excel'],
            'max_size': 20 * 1024 * 1024,  # 20MB
            'description': 'Excel表格(旧版)'
        },
        'pptx': {
            'extensions': ['.pptx'],
            'mime_types': [
                'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            ],
            'max_size': 50 * 1024 * 1024,  # 50MB
            'description': 'PowerPoint演示文稿'
        },
        'ppt': {
            'extensions': ['.ppt'],
            'mime_types': ['application/vnd.ms-powerpoint'],
            'max_size': 50 * 1024 * 1024,  # 50MB
            'description': 'PowerPoint演示文稿(旧版)'
        }
    }
    
    # 危险文件扩展名黑名单
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.app', '.deb', '.pkg', '.dmg', '.iso', '.msi', '.run',
        '.sh', '.ps1', '.php', '.asp', '.jsp', '.py', '.rb', '.pl'
    }
    
    def __init__(self):
        self.logger = logger
    
    def validate_file(
        self,
        file_content: bytes,
        filename: str,
        allowed_types: Optional[List[str]] = None,
        max_size: Optional[int] = None
    ) -> FileValidationResult:
        """
        验证文件
        
        Args:
            file_content: 文件内容
            filename: 文件名
            allowed_types: 允许的文件类型列表
            max_size: 最大文件大小
            
        Returns:
            文件验证结果
        """
        errors = []
        warnings = []
        
        try:
            # 基本信息提取
            file_size = len(file_content)
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # 获取文件扩展名
            file_ext = Path(filename).suffix.lower()
            
            # 检测MIME类型
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
            except Exception as e:
                mime_type = "application/octet-stream"
                warnings.append(f"无法检测MIME类型: {e}")
            
            # 确定文件类型
            file_type = self._determine_file_type(file_ext, mime_type)
            
            # 验证文件类型
            if not self._validate_file_type(file_type, allowed_types):
                supported_types = allowed_types or list(self.SUPPORTED_TYPES.keys())
                errors.append(f"不支持的文件类型: {file_type}，支持的类型: {', '.join(supported_types)}")
            
            # 验证文件大小
            size_error = self._validate_file_size(file_size, file_type, max_size)
            if size_error:
                errors.append(size_error)
            
            # 安全检查
            security_errors = self._security_check(filename, file_content, mime_type)
            errors.extend(security_errors)
            
            # 内容验证
            content_warnings = self._validate_content(file_content, file_type)
            warnings.extend(content_warnings)
            
            return FileValidationResult(
                is_valid=len(errors) == 0,
                file_type=file_type,
                file_size=file_size,
                file_hash=file_hash,
                mime_type=mime_type,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"文件验证异常: {e}", exception=e)
            return FileValidationResult(
                is_valid=False,
                file_type="unknown",
                file_size=len(file_content) if file_content else 0,
                file_hash="",
                mime_type="",
                errors=[f"文件验证异常: {str(e)}"],
                warnings=[]
            )
    
    def _determine_file_type(self, file_ext: str, mime_type: str) -> str:
        """确定文件类型"""
        # 首先根据扩展名匹配
        for file_type, config in self.SUPPORTED_TYPES.items():
            if file_ext in config['extensions']:
                return file_type
        
        # 如果扩展名不匹配，尝试根据MIME类型匹配
        for file_type, config in self.SUPPORTED_TYPES.items():
            if mime_type in config['mime_types']:
                return file_type
        
        # 都不匹配则返回扩展名（去掉点号）
        return file_ext.lstrip('.') if file_ext else 'unknown'
    
    def _validate_file_type(self, file_type: str, allowed_types: Optional[List[str]]) -> bool:
        """验证文件类型是否被允许"""
        if allowed_types is None:
            # 如果没有指定允许类型，检查是否在支持的类型中
            return file_type in self.SUPPORTED_TYPES
        
        return file_type in allowed_types
    
    def _validate_file_size(
        self, 
        file_size: int, 
        file_type: str, 
        max_size: Optional[int]
    ) -> Optional[str]:
        """验证文件大小"""
        # 使用指定的最大大小
        if max_size is not None:
            if file_size > max_size:
                return f"文件大小超过限制: {self._format_size(file_size)} > {self._format_size(max_size)}"
        
        # 使用类型默认的最大大小
        elif file_type in self.SUPPORTED_TYPES:
            type_max_size = self.SUPPORTED_TYPES[file_type]['max_size']
            if file_size > type_max_size:
                return f"文件大小超过{file_type}类型限制: {self._format_size(file_size)} > {self._format_size(type_max_size)}"
        
        # 检查最小大小
        if file_size < 1:
            return "文件不能为空"
        
        return None
    
    def _security_check(self, filename: str, file_content: bytes, mime_type: str) -> List[str]:
        """安全检查"""
        errors = []
        
        # 检查危险扩展名
        file_ext = Path(filename).suffix.lower()
        if file_ext in self.DANGEROUS_EXTENSIONS:
            errors.append(f"危险的文件类型: {file_ext}")
        
        # 检查文件名
        if not self._is_safe_filename(filename):
            errors.append("文件名包含不安全字符")
        
        # 检查文件头
        if not self._validate_file_header(file_content, mime_type):
            errors.append("文件头验证失败，可能是伪造的文件类型")
        
        # 检查文件内容
        if self._contains_malicious_content(file_content):
            errors.append("文件可能包含恶意内容")
        
        return errors
    
    def _is_safe_filename(self, filename: str) -> bool:
        """检查文件名是否安全"""
        # 检查路径遍历攻击
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # 检查特殊字符
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in dangerous_chars):
            return False
        
        # 检查长度
        if len(filename) > 255:
            return False
        
        return True
    
    def _validate_file_header(self, file_content: bytes, mime_type: str) -> bool:
        """验证文件头"""
        if len(file_content) < 4:
            return False
        
        # 常见文件头签名
        file_signatures = {
            b'\x25\x50\x44\x46': 'application/pdf',  # PDF
            b'\x50\x4B\x03\x04': 'application/zip',   # ZIP/DOCX/XLSX/PPTX
            b'\xD0\xCF\x11\xE0': 'application/msword', # DOC/XLS/PPT
        }
        
        # 检查文件头
        for signature, expected_mime in file_signatures.items():
            if file_content.startswith(signature):
                # 对于ZIP格式的Office文档，需要更详细的检查
                if signature == b'\x50\x4B\x03\x04':
                    return self._validate_office_zip(file_content, mime_type)
                return True
        
        # 对于文本文件，检查是否包含有效的文本内容
        if mime_type.startswith('text/'):
            try:
                file_content.decode('utf-8')
                return True
            except UnicodeDecodeError:
                try:
                    file_content.decode('gbk')
                    return True
                except UnicodeDecodeError:
                    return False
        
        return True
    
    def _validate_office_zip(self, file_content: bytes, mime_type: str) -> bool:
        """验证Office ZIP格式文档"""
        try:
            import zipfile
            import io
            
            with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
                # 检查是否包含Office文档的特征文件
                office_indicators = [
                    'word/', 'xl/', 'ppt/',  # Office 2007+
                    '[Content_Types].xml',   # Office 2007+
                    '_rels/.rels'           # Office 2007+
                ]
                
                file_list = zf.namelist()
                return any(
                    any(indicator in filename for filename in file_list)
                    for indicator in office_indicators
                )
        except:
            return False
    
    def _contains_malicious_content(self, file_content: bytes) -> bool:
        """检查是否包含恶意内容"""
        # 检查可疑的脚本内容
        malicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'onload=',
            b'onerror=',
            b'eval(',
            b'exec(',
        ]
        
        content_lower = file_content.lower()
        return any(pattern in content_lower for pattern in malicious_patterns)
    
    def _validate_content(self, file_content: bytes, file_type: str) -> List[str]:
        """验证文件内容"""
        warnings = []
        
        # 检查文件是否为空
        if len(file_content) == 0:
            warnings.append("文件内容为空")
            return warnings
        
        # 对于文本文件，检查编码
        if file_type in ['txt', 'md']:
            try:
                content = file_content.decode('utf-8')
                if not content.strip():
                    warnings.append("文件内容为空白")
            except UnicodeDecodeError:
                try:
                    content = file_content.decode('gbk')
                    warnings.append("文件使用GBK编码，建议使用UTF-8")
                except UnicodeDecodeError:
                    warnings.append("文件编码无法识别")
        
        # 检查文件是否过小（可能损坏）
        min_sizes = {
            'pdf': 1024,      # 1KB
            'docx': 5120,     # 5KB
            'doc': 2048,      # 2KB
            'xlsx': 5120,     # 5KB
            'xls': 2048,      # 2KB
            'pptx': 10240,    # 10KB
            'ppt': 5120,      # 5KB
        }
        
        if file_type in min_sizes and len(file_content) < min_sizes[file_type]:
            warnings.append(f"文件大小异常小，可能已损坏")
        
        return warnings
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def get_supported_types(self) -> Dict[str, Any]:
        """获取支持的文件类型信息"""
        return {
            file_type: {
                'extensions': config['extensions'],
                'max_size': config['max_size'],
                'max_size_formatted': self._format_size(config['max_size']),
                'description': config['description']
            }
            for file_type, config in self.SUPPORTED_TYPES.items()
        }
    
    def is_type_supported(self, file_type: str) -> bool:
        """检查文件类型是否被支持"""
        return file_type in self.SUPPORTED_TYPES


# 全局文件验证器实例
file_validator = FileValidator()


def validate_uploaded_file(
    file_content: bytes,
    filename: str,
    allowed_types: Optional[List[str]] = None,
    max_size: Optional[int] = None
) -> FileValidationResult:
    """
    验证上传的文件
    
    Args:
        file_content: 文件内容
        filename: 文件名
        allowed_types: 允许的文件类型
        max_size: 最大文件大小
        
    Returns:
        验证结果
    """
    return file_validator.validate_file(file_content, filename, allowed_types, max_size)


def get_file_type_info() -> Dict[str, Any]:
    """获取支持的文件类型信息"""
    return file_validator.get_supported_types()
