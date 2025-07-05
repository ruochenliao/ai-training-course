// 企业级性能优化工具

import { ref, nextTick } from 'vue'
import type { Ref } from 'vue'

/**
 * 加载状态管理器
 */
export class LoadingManager {
  private loadingStates = new Map<string, boolean>()
  private globalLoading = ref(false)

  /**
   * 显示加载状态
   */
  show(key?: string): void {
    if (key) {
      this.loadingStates.set(key, true)
    } else {
      this.globalLoading.value = true
    }
  }

  /**
   * 隐藏加载状态
   */
  hide(key?: string): void {
    if (key) {
      this.loadingStates.set(key, false)
    } else {
      this.globalLoading.value = false
    }
  }

  /**
   * 检查加载状态
   */
  isLoading(key?: string): boolean {
    if (key) {
      return this.loadingStates.get(key) || false
    }
    return this.globalLoading.value
  }

  /**
   * 获取全局加载状态响应式引用
   */
  getGlobalLoading(): Ref<boolean> {
    return this.globalLoading
  }

  /**
   * 清除所有加载状态
   */
  clear(): void {
    this.loadingStates.clear()
    this.globalLoading.value = false
  }

  /**
   * 异步操作包装器
   */
  async wrap<T>(
    operation: () => Promise<T>,
    key?: string
  ): Promise<T> {
    try {
      this.show(key)
      return await operation()
    } finally {
      this.hide(key)
    }
  }
}

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  immediate: boolean = false
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      if (!immediate) func(...args)
    }

    const callNow = immediate && !timeout

    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)

    if (callNow) func(...args)
  }
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

/**
 * 图片懒加载指令
 */
export const lazyLoad = {
  mounted(el: HTMLImageElement, binding: any) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement
            img.src = binding.value
            img.classList.remove('lazy-loading')
            img.classList.add('lazy-loaded')
            observer.unobserve(img)
          }
        })
      },
      {
        threshold: 0.1,
        rootMargin: '50px'
      }
    )

    el.classList.add('lazy-loading')
    observer.observe(el)
  }
}

/**
 * 虚拟滚动管理器
 */
export class VirtualScrollManager {
  private containerHeight: number
  private itemHeight: number
  private items: any[]
  private visibleStart = ref(0)
  private visibleEnd = ref(0)
  private scrollTop = ref(0)

  constructor(containerHeight: number, itemHeight: number, items: any[]) {
    this.containerHeight = containerHeight
    this.itemHeight = itemHeight
    this.items = items
    this.updateVisibleRange()
  }

  /**
   * 更新可见范围
   */
  private updateVisibleRange(): void {
    const visibleCount = Math.ceil(this.containerHeight / this.itemHeight)
    const start = Math.floor(this.scrollTop.value / this.itemHeight)
    const end = Math.min(start + visibleCount + 2, this.items.length)

    this.visibleStart.value = Math.max(0, start - 2)
    this.visibleEnd.value = end
  }

  /**
   * 处理滚动事件
   */
  onScroll(event: Event): void {
    const target = event.target as HTMLElement
    this.scrollTop.value = target.scrollTop
    this.updateVisibleRange()
  }

  /**
   * 获取可见项目
   */
  getVisibleItems(): any[] {
    return this.items.slice(this.visibleStart.value, this.visibleEnd.value)
  }

  /**
   * 获取偏移量
   */
  getOffset(): number {
    return this.visibleStart.value * this.itemHeight
  }

  /**
   * 获取总高度
   */
  getTotalHeight(): number {
    return this.items.length * this.itemHeight
  }
}

/**
 * 缓存管理器
 */
export class CacheManager {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>()
  private maxSize: number

  constructor(maxSize: number = 100) {
    this.maxSize = maxSize
  }

  /**
   * 设置缓存
   */
  set(key: string, data: any, ttl: number = 5 * 60 * 1000): void {
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value
      this.cache.delete(oldestKey)
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    })
  }

  /**
   * 获取缓存
   */
  get(key: string): any | null {
    const item = this.cache.get(key)
    
    if (!item) {
      return null
    }

    // 检查是否过期
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key)
      return null
    }

    return item.data
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
   * 获取缓存大小
   */
  size(): number {
    return this.cache.size
  }

  /**
   * 清理过期缓存
   */
  cleanup(): void {
    const now = Date.now()
    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        this.cache.delete(key)
      }
    }
  }
}

/**
 * 请求取消管理器
 */
export class CancelTokenManager {
  private controllers = new Map<string, AbortController>()

  /**
   * 创建取消令牌
   */
  create(key?: string): AbortController {
    const controller = new AbortController()
    
    if (key) {
      // 如果已存在相同key的请求，先取消它
      this.cancel(key)
      this.controllers.set(key, controller)
    }

    return controller
  }

  /**
   * 取消请求
   */
  cancel(key?: string): void {
    if (key) {
      const controller = this.controllers.get(key)
      if (controller) {
        controller.abort()
        this.controllers.delete(key)
      }
    } else {
      // 取消所有请求
      this.cancelAll()
    }
  }

  /**
   * 取消所有请求
   */
  cancelAll(): void {
    for (const controller of this.controllers.values()) {
      controller.abort()
    }
    this.controllers.clear()
  }

  /**
   * 清理已完成的请求
   */
  cleanup(): void {
    for (const [key, controller] of this.controllers.entries()) {
      if (controller.signal.aborted) {
        this.controllers.delete(key)
      }
    }
  }
}

/**
 * 性能监控器
 */
export class PerformanceMonitor {
  private marks = new Map<string, number>()
  private measures = new Map<string, number>()

  /**
   * 标记开始时间
   */
  mark(name: string): void {
    this.marks.set(name, performance.now())
  }

  /**
   * 测量时间差
   */
  measure(name: string, startMark: string): number {
    const startTime = this.marks.get(startMark)
    if (!startTime) {
      console.warn(`Start mark "${startMark}" not found`)
      return 0
    }

    const duration = performance.now() - startTime
    this.measures.set(name, duration)
    
    console.log(`⏱️ ${name}: ${duration.toFixed(2)}ms`)
    return duration
  }

  /**
   * 获取测量结果
   */
  getMeasure(name: string): number | undefined {
    return this.measures.get(name)
  }

  /**
   * 清除标记
   */
  clearMarks(): void {
    this.marks.clear()
  }

  /**
   * 清除测量结果
   */
  clearMeasures(): void {
    this.measures.clear()
  }

  /**
   * 监控函数执行时间
   */
  async monitor<T>(name: string, fn: () => Promise<T>): Promise<T> {
    this.mark(`${name}-start`)
    try {
      const result = await fn()
      this.measure(name, `${name}-start`)
      return result
    } catch (error) {
      this.measure(`${name}-error`, `${name}-start`)
      throw error
    }
  }
}

/**
 * 动画帧管理器
 */
export class AnimationFrameManager {
  private callbacks = new Map<string, () => void>()
  private rafId: number | null = null

  /**
   * 添加动画回调
   */
  add(key: string, callback: () => void): void {
    this.callbacks.set(key, callback)
    this.start()
  }

  /**
   * 移除动画回调
   */
  remove(key: string): void {
    this.callbacks.delete(key)
    if (this.callbacks.size === 0) {
      this.stop()
    }
  }

  /**
   * 开始动画循环
   */
  private start(): void {
    if (this.rafId) return

    const loop = () => {
      for (const callback of this.callbacks.values()) {
        callback()
      }
      
      if (this.callbacks.size > 0) {
        this.rafId = requestAnimationFrame(loop)
      } else {
        this.rafId = null
      }
    }

    this.rafId = requestAnimationFrame(loop)
  }

  /**
   * 停止动画循环
   */
  private stop(): void {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId)
      this.rafId = null
    }
  }

  /**
   * 清除所有回调
   */
  clear(): void {
    this.callbacks.clear()
    this.stop()
  }
}

// 创建全局实例
export const loadingManager = new LoadingManager()
export const cacheManager = new CacheManager()
export const cancelTokenManager = new CancelTokenManager()
export const performanceMonitor = new PerformanceMonitor()
export const animationFrameManager = new AnimationFrameManager()

/**
 * 工具函数：等待指定时间
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 工具函数：重试机制
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      
      if (attempt === maxAttempts) {
        throw lastError
      }
      
      await sleep(delay * attempt)
    }
  }

  throw lastError!
}

/**
 * 工具函数：批量处理
 */
export async function batch<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  batchSize: number = 10,
  delay: number = 0
): Promise<R[]> {
  const results: R[] = []
  
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize)
    const batchResults = await Promise.all(batch.map(processor))
    results.push(...batchResults)
    
    if (delay > 0 && i + batchSize < items.length) {
      await sleep(delay)
    }
  }
  
  return results
}
