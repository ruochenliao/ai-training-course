// Copyright (c) 2025 左岚. All rights reserved.

/**
 * Element Plus 扩展类型声明
 * 用于解决 Element Plus 组件库中的类型错误
 */

// 声明 Element Plus 全局配置类型
declare module 'element-plus' {
  import type { Ref } from 'vue'

  interface ConfigProviderProps {
    locale?: any
    size?: string
    zIndex?: number
    button?: any
    message?: any
    // 其他可能的配置项
  }

  export function useGlobalConfig(): {
    locale: Ref<any>
    size: Ref<string>
    zIndex: Ref<number>
    [key: string]: any
  }
}