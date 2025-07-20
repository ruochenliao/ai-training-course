# -*- coding: utf-8 -*-
"""
安全工具模块
用于API密钥的加密和解密
"""
import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# 从环境变量获取加密密钥，如果没有则使用默认值
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "super-intelligent-customer-service-key")
SALT = b"llm_model_api_key_salt"


def _get_fernet_key() -> bytes:
    """生成Fernet加密密钥"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))
    return key


def encrypt_api_key(api_key: str) -> str:
    """
    加密API密钥
    
    Args:
        api_key: 明文API密钥
        
    Returns:
        加密后的API密钥（base64编码）
    """
    if not api_key:
        return ""
    
    try:
        fernet = Fernet(_get_fernet_key())
        encrypted_key = fernet.encrypt(api_key.encode())
        return base64.urlsafe_b64encode(encrypted_key).decode()
    except Exception as e:
        print(f"API密钥加密失败: {e}")
        return api_key  # 如果加密失败，返回原始密钥


def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    解密API密钥
    
    Args:
        encrypted_api_key: 加密的API密钥
        
    Returns:
        明文API密钥
    """
    if not encrypted_api_key:
        return ""
    
    try:
        # 如果不是加密格式，直接返回
        if not is_api_key_encrypted(encrypted_api_key):
            return encrypted_api_key
        
        fernet = Fernet(_get_fernet_key())
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_api_key.encode())
        decrypted_key = fernet.decrypt(encrypted_bytes)
        return decrypted_key.decode()
    except Exception as e:
        print(f"API密钥解密失败: {e}")
        return encrypted_api_key  # 如果解密失败，返回原始值


def is_api_key_encrypted(api_key: str) -> bool:
    """
    检查API密钥是否已加密
    
    Args:
        api_key: API密钥
        
    Returns:
        True if encrypted, False otherwise
    """
    if not api_key:
        return False
    
    try:
        # 尝试base64解码
        decoded = base64.urlsafe_b64decode(api_key.encode())
        # 检查长度是否符合Fernet加密后的格式
        return len(decoded) > 40  # Fernet加密后的最小长度
    except Exception:
        return False


def mask_api_key(api_key: str, show_chars: int = 4) -> str:
    """
    遮蔽API密钥，只显示前几位和后几位
    
    Args:
        api_key: API密钥
        show_chars: 显示的字符数
        
    Returns:
        遮蔽后的API密钥
    """
    if not api_key:
        return ""
    
    if len(api_key) <= show_chars * 2:
        return "*" * len(api_key)
    
    return f"{api_key[:show_chars]}{'*' * (len(api_key) - show_chars * 2)}{api_key[-show_chars:]}"


def generate_api_key_hash(api_key: str) -> str:
    """
    生成API密钥的哈希值，用于比较
    
    Args:
        api_key: API密钥
        
    Returns:
        API密钥的SHA256哈希值
    """
    if not api_key:
        return ""
    
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_api_key_format(api_key: str, provider: str = "") -> bool:
    """
    验证API密钥格式
    
    Args:
        api_key: API密钥
        provider: 提供商名称
        
    Returns:
        True if valid format, False otherwise
    """
    if not api_key:
        return False
    
    # 基本长度检查
    if len(api_key) < 10:
        return False
    
    # 根据提供商进行特定格式检查
    if provider.lower() == "openai":
        return api_key.startswith("sk-") and len(api_key) >= 40
    elif provider.lower() == "deepseek":
        return api_key.startswith("sk-") and len(api_key) >= 30
    elif provider.lower() == "qwen" or provider.lower() == "dashscope":
        return api_key.startswith("sk-") and len(api_key) >= 30
    
    # 默认检查：以sk-开头或者是其他格式的密钥
    return True


class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self):
        self._key_cache = {}
    
    def encrypt_and_store(self, api_key: str, key_id: str) -> str:
        """加密并存储API密钥"""
        encrypted_key = encrypt_api_key(api_key)
        self._key_cache[key_id] = {
            "encrypted": encrypted_key,
            "hash": generate_api_key_hash(api_key),
            "masked": mask_api_key(api_key)
        }
        return encrypted_key
    
    def get_decrypted_key(self, encrypted_key: str, key_id: Optional[str] = None) -> str:
        """获取解密的API密钥"""
        return decrypt_api_key(encrypted_key)
    
    def get_masked_key(self, key_id: str) -> str:
        """获取遮蔽的API密钥"""
        if key_id in self._key_cache:
            return self._key_cache[key_id]["masked"]
        return ""
    
    def verify_key(self, api_key: str, key_id: str) -> bool:
        """验证API密钥"""
        if key_id not in self._key_cache:
            return False
        
        stored_hash = self._key_cache[key_id]["hash"]
        current_hash = generate_api_key_hash(api_key)
        return stored_hash == current_hash
    
    def clear_cache(self):
        """清空缓存"""
        self._key_cache.clear()


# 创建全局API密钥管理器实例
api_key_manager = APIKeyManager()


# 兼容性函数
def encrypt_key(key: str) -> str:
    """兼容性函数：加密密钥"""
    return encrypt_api_key(key)


def decrypt_key(encrypted_key: str) -> str:
    """兼容性函数：解密密钥"""
    return decrypt_api_key(encrypted_key)


if __name__ == "__main__":
    # 测试加密解密功能
    test_key = "sk-test1234567890abcdef"
    print(f"原始密钥: {test_key}")
    
    encrypted = encrypt_api_key(test_key)
    print(f"加密后: {encrypted}")
    
    decrypted = decrypt_api_key(encrypted)
    print(f"解密后: {decrypted}")
    
    print(f"是否加密: {is_api_key_encrypted(encrypted)}")
    print(f"遮蔽显示: {mask_api_key(test_key)}")
    print(f"格式验证: {validate_api_key_format(test_key, 'openai')}")
    
    assert test_key == decrypted, "加密解密测试失败"
    print("✅ 加密解密测试通过")
