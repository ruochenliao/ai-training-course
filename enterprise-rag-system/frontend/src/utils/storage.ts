// 存储工具函数

/**
 * 存储类型
 */
export type StorageType = 'localStorage' | 'sessionStorage'

/**
 * 存储项接口
 */
interface StorageItem<T = any> {
  value: T
  timestamp: number
  expires?: number
}

/**
 * 存储管理器类
 */
class StorageManager {
  private storage: Storage

  constructor(type: StorageType = 'localStorage') {
    this.storage = type === 'localStorage' ? localStorage : sessionStorage
  }

  /**
   * 设置存储项
   */
  set<T>(key: string, value: T, expires?: number): boolean {
    try {
      const item: StorageItem<T> = {
        value,
        timestamp: Date.now(),
        expires: expires ? Date.now() + expires : undefined,
      }
      this.storage.setItem(key, JSON.stringify(item))
      return true
    } catch (error) {
      console.error('Storage set error:', error)
      return false
    }
  }

  /**
   * 获取存储项
   */
  get<T>(key: string, defaultValue?: T): T | undefined {
    try {
      const itemStr = this.storage.getItem(key)
      if (!itemStr) return defaultValue

      const item: StorageItem<T> = JSON.parse(itemStr)

      // 检查是否过期
      if (item.expires && Date.now() > item.expires) {
        this.remove(key)
        return defaultValue
      }

      return item.value
    } catch (error) {
      console.error('Storage get error:', error)
      return defaultValue
    }
  }

  /**
   * 移除存储项
   */
  remove(key: string): boolean {
    try {
      this.storage.removeItem(key)
      return true
    } catch (error) {
      console.error('Storage remove error:', error)
      return false
    }
  }

  /**
   * 清空所有存储项
   */
  clear(): boolean {
    try {
      this.storage.clear()
      return true
    } catch (error) {
      console.error('Storage clear error:', error)
      return false
    }
  }

  /**
   * 检查存储项是否存在
   */
  has(key: string): boolean {
    return this.storage.getItem(key) !== null
  }

  /**
   * 获取所有键名
   */
  keys(): string[] {
    const keys: string[] = []
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i)
      if (key) keys.push(key)
    }
    return keys
  }

  /**
   * 获取存储大小（字节）
   */
  size(): number {
    let total = 0
    for (let i = 0; i < this.storage.length; i++) {
      const key = this.storage.key(i)
      if (key) {
        const value = this.storage.getItem(key)
        if (value) {
          total += key.length + value.length
        }
      }
    }
    return total
  }

  /**
   * 清理过期项
   */
  cleanup(): number {
    let cleaned = 0
    const keys = this.keys()

    keys.forEach(key => {
      try {
        const itemStr = this.storage.getItem(key)
        if (itemStr) {
          const item: StorageItem = JSON.parse(itemStr)
          if (item.expires && Date.now() > item.expires) {
            this.remove(key)
            cleaned++
          }
        }
      } catch (error) {
        // 如果解析失败，也删除该项
        this.remove(key)
        cleaned++
      }
    })

    return cleaned
  }

  /**
   * 获取存储使用情况
   */
  getUsage(): { used: number; available: number; percentage: number } {
    const used = this.size()
    // 大多数浏览器的localStorage限制是5MB
    const available = 5 * 1024 * 1024
    const percentage = (used / available) * 100

    return { used, available, percentage }
  }
}

// 创建默认实例
export const localStorage = new StorageManager('localStorage')
export const sessionStorage = new StorageManager('sessionStorage')

/**
 * Cookie 管理器
 */
export const cookieManager = {
  /**
   * 设置 Cookie
   */
  set(
    name: string,
    value: string,
    options: {
      expires?: number | Date
      path?: string
      domain?: string
      secure?: boolean
      sameSite?: 'strict' | 'lax' | 'none'
    } = {}
  ): void {
    let cookieString = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`

    if (options.expires) {
      const expires = typeof options.expires === 'number' ? new Date(Date.now() + options.expires) : options.expires
      cookieString += `; expires=${expires.toUTCString()}`
    }

    if (options.path) {
      cookieString += `; path=${options.path}`
    }

    if (options.domain) {
      cookieString += `; domain=${options.domain}`
    }

    if (options.secure) {
      cookieString += '; secure'
    }

    if (options.sameSite) {
      cookieString += `; samesite=${options.sameSite}`
    }

    document.cookie = cookieString
  },

  /**
   * 获取 Cookie
   */
  get(name: string): string | null {
    const nameEQ = encodeURIComponent(name) + '='
    const cookies = document.cookie.split(';')

    for (let cookie of cookies) {
      cookie = cookie.trim()
      if (cookie.indexOf(nameEQ) === 0) {
        return decodeURIComponent(cookie.substring(nameEQ.length))
      }
    }

    return null
  },

  /**
   * 删除 Cookie
   */
  remove(name: string, path?: string, domain?: string): void {
    this.set(name, '', {
      expires: new Date(0),
      path,
      domain,
    })
  },

  /**
   * 获取所有 Cookie
   */
  getAll(): Record<string, string> {
    const cookies: Record<string, string> = {}

    document.cookie.split(';').forEach(cookie => {
      const [name, value] = cookie.trim().split('=')
      if (name && value) {
        cookies[decodeURIComponent(name)] = decodeURIComponent(value)
      }
    })

    return cookies
  },

  /**
   * 检查 Cookie 是否存在
   */
  has(name: string): boolean {
    return this.get(name) !== null
  },
}

/**
 * 内存缓存管理器
 */
class MemoryCache {
  private cache = new Map<string, StorageItem>()
  private maxSize: number
  private ttl: number

  constructor(maxSize = 100, ttl = 5 * 60 * 1000) {
    // 默认5分钟
    this.maxSize = maxSize
    this.ttl = ttl
  }

  /**
   * 设置缓存
   */
  set<T>(key: string, value: T, ttl?: number): void {
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
    }

    const expires = ttl ? Date.now() + ttl : Date.now() + this.ttl
    this.cache.set(key, {
      value,
      timestamp: Date.now(),
      expires,
    })
  }

  /**
   * 获取缓存
   */
  get<T>(key: string): T | undefined {
    const item = this.cache.get(key)
    if (!item) return undefined

    // 检查是否过期
    if (Date.now() > item.expires!) {
      this.cache.delete(key)
      return undefined
    }

    return item.value as T
  }

  /**
   * 删除缓存
   */
  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  /**
   * 清空缓存
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * 检查缓存是否存在
   */
  has(key: string): boolean {
    const item = this.cache.get(key)
    if (!item) return false

    // 检查是否过期
    if (Date.now() > item.expires!) {
      this.cache.delete(key)
      return false
    }

    return true
  }

  /**
   * 获取缓存大小
   */
  size(): number {
    return this.cache.size
  }

  /**
   * 清理过期缓存
   */
  cleanup(): number {
    let cleaned = 0
    const now = Date.now()

    for (const [key, item] of this.cache.entries()) {
      if (now > item.expires!) {
        this.cache.delete(key)
        cleaned++
      }
    }

    return cleaned
  }

  /**
   * 获取所有键
   */
  keys(): string[] {
    return Array.from(this.cache.keys())
  }

  /**
   * 获取缓存统计信息
   */
  stats(): {
    size: number
    maxSize: number
    hitRate: number
    memoryUsage: number
  } {
    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      hitRate: 0, // 需要额外实现命中率统计
      memoryUsage: this.cache.size * 1024, // 估算值
    }
  }
}

// 创建默认内存缓存实例
export const memoryCache = new MemoryCache()

/**
 * 存储工具函数
 */
export const storageUtils = {
  /**
   * 检查存储支持
   */
  isSupported(type: StorageType): boolean {
    try {
      const storage = type === 'localStorage' ? window.localStorage : window.sessionStorage
      const testKey = '__storage_test__'
      storage.setItem(testKey, 'test')
      storage.removeItem(testKey)
      return true
    } catch {
      return false
    }
  },

  /**
   * 获取存储配额信息
   */
  async getQuota(): Promise<{ usage: number; quota: number } | null> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate()
        return {
          usage: estimate.usage || 0,
          quota: estimate.quota || 0,
        }
      } catch {
        return null
      }
    }
    return null
  },

  /**
   * 压缩存储数据
   */
  compress(data: string): string {
    // 简单的压缩实现，实际项目中可以使用更好的压缩算法
    return btoa(encodeURIComponent(data))
  },

  /**
   * 解压存储数据
   */
  decompress(data: string): string {
    try {
      return decodeURIComponent(atob(data))
    } catch {
      return data
    }
  },
}

// 定期清理过期数据
setInterval(() => {
  localStorage.cleanup()
  sessionStorage.cleanup()
  memoryCache.cleanup()
}, 60 * 1000) // 每分钟清理一次
