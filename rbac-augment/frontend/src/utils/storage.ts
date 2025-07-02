/**
 * 本地存储工具函数
 */

/**
 * localStorage 封装
 */
export const storage = {
  /**
   * 设置存储项
   */
  set(key: string, value: any): void {
    try {
      const serializedValue = JSON.stringify(value)
      localStorage.setItem(key, serializedValue)
    } catch (error) {
      console.error('Failed to set localStorage item:', error)
    }
  },

  /**
   * 获取存储项
   */
  get<T = any>(key: string): T | null {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.error('Failed to get localStorage item:', error)
      return null
    }
  },

  /**
   * 移除存储项
   */
  remove(key: string): void {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('Failed to remove localStorage item:', error)
    }
  },

  /**
   * 清空所有存储项
   */
  clear(): void {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('Failed to clear localStorage:', error)
    }
  },

  /**
   * 检查存储项是否存在
   */
  has(key: string): boolean {
    return localStorage.getItem(key) !== null
  }
}

/**
 * sessionStorage 封装
 */
export const sessionStorage = {
  /**
   * 设置存储项
   */
  set(key: string, value: any): void {
    try {
      const serializedValue = JSON.stringify(value)
      window.sessionStorage.setItem(key, serializedValue)
    } catch (error) {
      console.error('Failed to set sessionStorage item:', error)
    }
  },

  /**
   * 获取存储项
   */
  get<T = any>(key: string): T | null {
    try {
      const item = window.sessionStorage.getItem(key)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.error('Failed to get sessionStorage item:', error)
      return null
    }
  },

  /**
   * 移除存储项
   */
  remove(key: string): void {
    try {
      window.sessionStorage.removeItem(key)
    } catch (error) {
      console.error('Failed to remove sessionStorage item:', error)
    }
  },

  /**
   * 清空所有存储项
   */
  clear(): void {
    try {
      window.sessionStorage.clear()
    } catch (error) {
      console.error('Failed to clear sessionStorage:', error)
    }
  },

  /**
   * 检查存储项是否存在
   */
  has(key: string): boolean {
    return window.sessionStorage.getItem(key) !== null
  }
}

/**
 * 带过期时间的存储
 */
export const expiredStorage = {
  /**
   * 设置带过期时间的存储项
   */
  set(key: string, value: any, expireTime: number): void {
    const data = {
      value,
      expireTime: Date.now() + expireTime
    }
    storage.set(key, data)
  },

  /**
   * 获取存储项（自动检查过期时间）
   */
  get<T = any>(key: string): T | null {
    const data = storage.get(key)
    
    if (!data) {
      return null
    }
    
    if (Date.now() > data.expireTime) {
      storage.remove(key)
      return null
    }
    
    return data.value
  },

  /**
   * 移除存储项
   */
  remove(key: string): void {
    storage.remove(key)
  }
}
