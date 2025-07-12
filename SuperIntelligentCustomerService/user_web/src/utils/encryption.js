/**
 * 前端AES加密解密工具
 * 与后端Python Fernet加密保持一致
 */
import CryptoJS from 'crypto-js'

class AESCrypto {
  constructor(password = null) {
    // 使用与后端相同的密码和盐值
    this.password = password || import.meta.env.VITE_ENCRYPTION_KEY || 'SuperIntelligentCustomerService2025'
    this.salt = 'SuperIntelligentCustomerService' // 与后端保持一致的盐值

    // 生成与后端PBKDF2相同的密钥
    this.key = this.deriveKey(this.password, this.salt)
  }

  /**
   * 使用PBKDF2派生密钥，与后端Python实现保持一致
   */
  deriveKey(password, salt) {
    // 使用PBKDF2派生32字节密钥，100000次迭代，与后端保持一致
    const key = CryptoJS.PBKDF2(password, salt, {
      keySize: 256 / 32, // 32字节 = 256位
      iterations: 100000,
      hasher: CryptoJS.algo.SHA256
    })
    return key
  }

  /**
   * 加密字符串 - 兼容Python Fernet格式
   * @param {string} plaintext - 明文字符串
   * @returns {string} 加密后的base64编码字符串
   */
  encrypt(plaintext) {
    if (!plaintext) {
      return plaintext
    }

    try {
      // 生成随机IV
      const iv = CryptoJS.lib.WordArray.random(16)

      // 使用AES-256-CBC加密
      const encrypted = CryptoJS.AES.encrypt(plaintext, this.key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
      })

      // 组合IV和加密数据，然后base64编码
      const combined = iv.concat(encrypted.ciphertext)
      return CryptoJS.enc.Base64.stringify(combined)
    } catch (error) {
      throw new Error(`加密失败: ${error.message}`)
    }
  }

  /**
   * 解密字符串 - 通过后端API解密
   * @param {string} ciphertext - 加密后的base64编码字符串
   * @returns {Promise<string>} 解密后的明文字符串
   */
  async decrypt(ciphertext) {
    if (!ciphertext) {
      return ciphertext
    }

    try {
      // 调用后端API进行解密
      const response = await fetch('/api/v1/system/model/decrypt-api-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'token': localStorage.getItem('token') || 'dev'
        },
        body: JSON.stringify({
          encrypted_key: ciphertext
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()
      if (result.code !== 200) {
        throw new Error(result.msg || '解密失败')
      }

      return result.data.decrypted_key
    } catch (error) {
      throw new Error(`API密钥解密失败: ${error.message}`)
    }
  }

  /**
   * 判断字符串是否已加密
   * @param {string} text - 待判断的字符串
   * @returns {boolean} True表示已加密，False表示未加密
   */
  isEncrypted(text) {
    if (!text) {
      return false
    }

    // 简单的启发式检测：Fernet加密的结果通常是base64编码的长字符串
    try {
      // 检查是否是有效的base64字符串且长度合理
      const decoded = atob(text)
      return decoded.length > 32 && /^[A-Za-z0-9+/=]+$/.test(text)
    } catch {
      return false
    }
  }
}

// 创建全局加密实例
const crypto = new AESCrypto()

/**
 * 加密API密钥
 * @param {string} apiKey - 原始API密钥
 * @returns {string} 加密后的API密钥
 */
export function encryptApiKey(apiKey) {
  return crypto.encrypt(apiKey)
}

/**
 * 解密API密钥
 * @param {string} encryptedApiKey - 加密的API密钥
 * @returns {Promise<string>} 解密后的API密钥
 */
export async function decryptApiKey(encryptedApiKey) {
  return await crypto.decrypt(encryptedApiKey)
}

/**
 * 判断API密钥是否已加密
 * @param {string} apiKey - API密钥
 * @returns {boolean} True表示已加密，False表示未加密
 */
export function isApiKeyEncrypted(apiKey) {
  return crypto.isEncrypted(apiKey)
}

/**
 * 安全地获取解密后的API密钥
 * 如果解密失败，返回null而不是抛出异常
 * @param {string} encryptedApiKey - 加密的API密钥
 * @returns {Promise<string|null>} 解密后的API密钥或null
 */
export async function safeDecryptApiKey(encryptedApiKey) {
  try {
    return await decryptApiKey(encryptedApiKey)
  } catch (error) {
    console.error('API密钥解密失败:', error.message)
    return null
  }
}

export default crypto
