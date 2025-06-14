import {type ClassValue, clsx} from 'clsx'
import {twMerge} from 'tailwind-merge'
import dayjs from 'dayjs'

/**
 * 合并className
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化时间
 */
export function formatTime(time: string | Date, format = 'YYYY-MM-DD HH:mm:ss'): string {
  return dayjs(time).format(format)
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(time: string | Date): string {
  return dayjs(time).fromNow()
}

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(func: T, wait: number): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }

    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(func: T, limit: number): (...args: Parameters<T>) => void {
  let inThrottle: boolean

  return function executedFunction(this: any, ...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

/**
 * 深拷贝
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as T
  }

  if (obj instanceof Array) {
    return obj.map((item) => deepClone(item)) as T
  }

  if (typeof obj === 'object') {
    const clonedObj = {} as T
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }

  return obj
}

/**
 * 生成随机字符串
 */
export function generateRandomString(length = 8): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''

  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }

  return result
}

/**
 * 下载文件
 */
export function downloadFile(url: string, filename?: string): void {
  const link = document.createElement('a')
  link.href = url
  link.download = filename || 'download'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * 复制到剪贴板
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    // 降级方案
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()

    try {
      document.execCommand('copy')
      document.body.removeChild(textArea)
      return true
    } catch (err) {
      document.body.removeChild(textArea)
      return false
    }
  }
}

/**
 * 获取文件扩展名
 */
export function getFileExtension(filename: string): string {
  return filename.slice(((filename.lastIndexOf('.') - 1) >>> 0) + 2)
}

/**
 * 验证邮箱格式
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * 验证手机号格式
 */
export function isValidPhone(phone: string): boolean {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

/**
 * 验证身份证号格式
 */
export function isValidIdCard(idCard: string): boolean {
  const idCardRegex = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/
  return idCardRegex.test(idCard)
}

/**
 * 检查是否为外链 - 对应Vue版本的 isExternal
 */
export function isExternal(path: string): boolean {
  return /^(https?:|mailto:|tel:)/.test(path)
}

/**
 * 树形数据转换为扁平数组
 */
export function treeToFlat<T extends { children?: T[] }>(tree: T[]): T[] {
  const result: T[] = []

  function traverse(nodes: T[]) {
    nodes.forEach((node) => {
      const { children, ...rest } = node
      result.push(rest as T)

      if (children && children.length > 0) {
        traverse(children)
      }
    })
  }

  traverse(tree)
  return result
}

/**
 * 扁平数组转换为树形数据
 */
export function flatToTree<T extends { id: string; parentId?: string }>(flat: T[], parentId?: string): (T & { children?: T[] })[] {
  return flat
    .filter((item) => item.parentId === parentId)
    .map((item) => ({
      ...item,
      children: flatToTree(flat, item.id),
    }))
}

/**
 * 获取浏览器信息
 */
export function getBrowserInfo() {
  const ua = navigator.userAgent
  const windowAny = window as any
  const isOpera = (!!windowAny.opr && !!windowAny.opr.addons) || !!windowAny.opera || navigator.userAgent.indexOf(' OPR/') >= 0
  const isFirefox = typeof windowAny.InstallTrigger !== 'undefined'
  const isSafari =
    /constructor/i.test(window.HTMLElement.toString()) ||
    (function (p) {
      return p.toString() === '[object SafariRemoteNotification]'
    })(!windowAny.safari || (typeof windowAny.safari !== 'undefined' && windowAny.safari.pushNotification))
  const isIE = /*@cc_on!@*/ false || !!(document as any).documentMode
  const isEdge = !isIE && !!windowAny.StyleMedia
  const isChrome = !!windowAny.chrome && (!!windowAny.chrome.webstore || !!windowAny.chrome.runtime)
  const isBlink = (isChrome || isOpera) && !!window.CSS

  return {
    isOpera,
    isFirefox,
    isSafari,
    isIE,
    isEdge,
    isChrome,
    isBlink,
    userAgent: ua,
  }
}

/**
 * 获取设备信息
 */
export function getDeviceInfo() {
  const ua = navigator.userAgent
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua)
  const isTablet = /iPad|Android(?!.*Mobile)/i.test(ua)
  const isDesktop = !isMobile && !isTablet

  return {
    isMobile,
    isTablet,
    isDesktop,
    userAgent: ua,
  }
}
