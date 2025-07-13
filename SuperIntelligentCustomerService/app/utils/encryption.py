"""
AES加密工具类
用于API密钥的加密和解密
"""
import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class AESCrypto:
    """AES加密解密工具类"""
    
    def __init__(self, password: str = None):
        """
        初始化加密工具
        
        Args:
            password: 加密密码，如果不提供则从环境变量获取
        """
        if password is None:
            password = os.getenv("ENCRYPTION_KEY", "SuperIntelligentCustomerService2025")
        
        # 使用固定的盐值确保密钥一致性
        salt = b"SuperIntelligentCustomerService"
        
        # 生成密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串
        
        Args:
            plaintext: 明文字符串
            
        Returns:
            加密后的base64编码字符串
        """
        if not plaintext:
            return plaintext
        
        try:
            encrypted_bytes = self.fernet.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            raise ValueError(f"加密失败: {str(e)}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        解密字符串

        Args:
            ciphertext: 加密后的base64编码字符串

        Returns:
            解密后的明文字符串
        """
        if not ciphertext:
            return ciphertext

        try:
            encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            # 不再兼容明文，解密失败直接抛出异常
            raise ValueError(f"API密钥解密失败，请确保密钥已正确加密: {str(e)}")
    
    def is_encrypted(self, text: str) -> bool:
        """
        判断字符串是否已加密

        Args:
            text: 待判断的字符串

        Returns:
            True表示已加密，False表示未加密
        """
        if not text:
            return False

        try:
            # 尝试base64解码和Fernet解密
            encrypted_bytes = base64.urlsafe_b64decode(text.encode('utf-8'))
            self.fernet.decrypt(encrypted_bytes)
            return True
        except:
            return False


# 全局加密实例
crypto = AESCrypto()


def encrypt_api_key(api_key: str) -> str:
    """
    加密API密钥
    
    Args:
        api_key: 原始API密钥
        
    Returns:
        加密后的API密钥
    """
    return crypto.encrypt(api_key)


def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    解密API密钥
    
    Args:
        encrypted_api_key: 加密的API密钥
        
    Returns:
        解密后的API密钥
    """
    return crypto.decrypt(encrypted_api_key)


def is_api_key_encrypted(api_key: str) -> bool:
    """
    判断API密钥是否已加密
    
    Args:
        api_key: API密钥
        
    Returns:
        True表示已加密，False表示未加密
    """
    return crypto.is_encrypted(api_key)
