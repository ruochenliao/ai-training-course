// 工具函数集合

// 导出所有工具函数
export * from './format'
export * from './validation'
export * from './storage'
export * from './request'
export * from './date'
export * from './file'
export * from './url'
export * from './dom'
export * from './common'

// 常用工具函数
export const utils = {
  // 防抖函数
  debounce: <T extends (...args: any[]) => any>(
    func: T,
    wait: number,
    immediate = false
  ): ((...args: Parameters<T>) => void) => {
    let timeout: NodeJS.Timeout | null = null
    return (...args: Parameters<T>) => {
      const callNow = immediate && !timeout
      if (timeout) clearTimeout(timeout)
      timeout = setTimeout(() => {
        timeout = null
        if (!immediate) func(...args)
      }, wait)
      if (callNow) func(...args)
    }
  },

  // 节流函数
  throttle: <T extends (...args: any[]) => any>(func: T, wait: number): ((...args: Parameters<T>) => void) => {
    let inThrottle: boolean
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args)
        inThrottle = true
        setTimeout(() => (inThrottle = false), wait)
      }
    }
  },

  // 深拷贝
  deepClone: <T>(obj: T): T => {
    if (obj === null || typeof obj !== 'object') return obj
    if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T
    if (obj instanceof Array) return obj.map(item => utils.deepClone(item)) as unknown as T
    if (typeof obj === 'object') {
      const clonedObj = {} as T
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          clonedObj[key] = utils.deepClone(obj[key])
        }
      }
      return clonedObj
    }
    return obj
  },

  // 生成唯一ID
  generateId: (prefix = 'id'): string => {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  },

  // 获取数据类型
  getType: (value: any): string => {
    return Object.prototype.toString.call(value).slice(8, -1).toLowerCase()
  },

  // 判断是否为空值
  isEmpty: (value: any): boolean => {
    if (value === null || value === undefined) return true
    if (typeof value === 'string') return value.trim() === ''
    if (Array.isArray(value)) return value.length === 0
    if (typeof value === 'object') return Object.keys(value).length === 0
    return false
  },

  // 安全的JSON解析
  safeJsonParse: <T = any>(str: string, defaultValue: T): T => {
    try {
      return JSON.parse(str)
    } catch {
      return defaultValue
    }
  },

  // 安全的JSON字符串化
  safeJsonStringify: (obj: any, defaultValue = '{}'): string => {
    try {
      return JSON.stringify(obj)
    } catch {
      return defaultValue
    }
  },

  // 数组去重
  unique: <T>(arr: T[], key?: keyof T): T[] => {
    if (!key) {
      return [...new Set(arr)]
    }
    const seen = new Set()
    return arr.filter(item => {
      const value = item[key]
      if (seen.has(value)) {
        return false
      }
      seen.add(value)
      return true
    })
  },

  // 数组分组
  groupBy: <T>(arr: T[], key: keyof T): Record<string, T[]> => {
    return arr.reduce(
      (groups, item) => {
        const group = String(item[key])
        groups[group] = groups[group] || []
        groups[group].push(item)
        return groups
      },
      {} as Record<string, T[]>
    )
  },

  // 对象属性排序
  sortObjectKeys: <T extends Record<string, any>>(obj: T): T => {
    const sorted = {} as T
    Object.keys(obj)
      .sort()
      .forEach(key => {
        sorted[key as keyof T] = obj[key]
      })
    return sorted
  },

  // 延迟执行
  sleep: (ms: number): Promise<void> => {
    return new Promise(resolve => setTimeout(resolve, ms))
  },

  // 重试函数
  retry: async <T>(fn: () => Promise<T>, retries = 3, delay = 1000): Promise<T> => {
    try {
      return await fn()
    } catch (error) {
      if (retries > 0) {
        await utils.sleep(delay)
        return utils.retry(fn, retries - 1, delay)
      }
      throw error
    }
  },

  // 格式化文件大小
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  },

  // 格式化数字
  formatNumber: (num: number, precision = 2): string => {
    if (num >= 1e9) return (num / 1e9).toFixed(precision) + 'B'
    if (num >= 1e6) return (num / 1e6).toFixed(precision) + 'M'
    if (num >= 1e3) return (num / 1e3).toFixed(precision) + 'K'
    return num.toString()
  },

  // 复制到剪贴板
  copyToClipboard: async (text: string): Promise<boolean> => {
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(text)
        return true
      } else {
        // 降级方案
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.opacity = '0'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        const successful = document.execCommand('copy')
        document.body.removeChild(textArea)
        return successful
      }
    } catch {
      return false
    }
  },

  // 下载文件
  downloadFile: (url: string, filename?: string): void => {
    const link = document.createElement('a')
    link.href = url
    if (filename) link.download = filename
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  },

  // 获取URL参数
  getUrlParams: (url?: string): Record<string, string> => {
    const urlStr = url || window.location.href
    const params: Record<string, string> = {}
    const urlObj = new URL(urlStr)
    urlObj.searchParams.forEach((value, key) => {
      params[key] = value
    })
    return params
  },

  // 设置URL参数
  setUrlParams: (params: Record<string, string>, url?: string): string => {
    const urlObj = new URL(url || window.location.href)
    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        urlObj.searchParams.set(key, value)
      } else {
        urlObj.searchParams.delete(key)
      }
    })
    return urlObj.toString()
  },

  // 滚动到元素
  scrollToElement: (
    element: HTMLElement | string,
    options: ScrollIntoViewOptions = { behavior: 'smooth', block: 'center' }
  ): void => {
    const el = typeof element === 'string' ? document.querySelector(element) : element
    if (el) {
      el.scrollIntoView(options)
    }
  },

  // 获取元素位置
  getElementPosition: (element: HTMLElement): { top: number; left: number } => {
    const rect = element.getBoundingClientRect()
    return {
      top: rect.top + window.scrollY,
      left: rect.left + window.scrollX,
    }
  },

  // 检测设备类型
  getDeviceType: (): 'mobile' | 'tablet' | 'desktop' => {
    const width = window.innerWidth
    if (width < 768) return 'mobile'
    if (width < 1024) return 'tablet'
    return 'desktop'
  },

  // 检测浏览器
  getBrowser: (): string => {
    const userAgent = navigator.userAgent
    if (userAgent.includes('Chrome')) return 'Chrome'
    if (userAgent.includes('Firefox')) return 'Firefox'
    if (userAgent.includes('Safari')) return 'Safari'
    if (userAgent.includes('Edge')) return 'Edge'
    return 'Unknown'
  },
}
