// Copyright (c) 2025 左岚. All rights reserved.

/**
 * Element Plus 相关类型声明 - 完整重构版本
 */

import type { App, Plugin } from 'vue'

// Element Plus 语言包类型
export interface ElementPlusLocale {
  name: string
  el: Record<string, any>
}

// 声明 Element Plus 语言包模块
declare module 'element-plus/dist/locale/zh-cn.mjs' {
  const locale: ElementPlusLocale
  export default locale
}

declare module 'element-plus/dist/locale/en.mjs' {
  const locale: ElementPlusLocale
  export default locale
}

// Element Plus 配置选项
export interface ElementPlusOptions {
  locale?: ElementPlusLocale
  size?: 'large' | 'default' | 'small'
  zIndex?: number
  namespace?: string
}

// Element Plus 插件类型
export interface ElementPlusPlugin extends Plugin {
  install(app: App, options?: ElementPlusOptions): void
}

// 声明 Element Plus 主模块
declare module 'element-plus' {
  import type { Component, App } from 'vue'

  // 主要导出
  const ElementPlus: ElementPlusPlugin
  export default ElementPlus

  // 消息组件类型
  export interface MessageOptions {
    message: string
    type?: 'success' | 'warning' | 'info' | 'error'
    duration?: number
    showClose?: boolean
    center?: boolean
    onClose?: () => void
  }

  export interface MessageInstance {
    close(): void
  }

  export const ElMessage: {
    (options: MessageOptions | string): MessageInstance
    success(message: string | MessageOptions): MessageInstance
    warning(message: string | MessageOptions): MessageInstance
    info(message: string | MessageOptions): MessageInstance
    error(message: string | MessageOptions): MessageInstance
    closeAll(): void
  }

  // 消息框组件类型
  export interface MessageBoxOptions {
    title?: string
    message?: string
    type?: 'success' | 'warning' | 'info' | 'error'
    confirmButtonText?: string
    cancelButtonText?: string
    showCancelButton?: boolean
    showConfirmButton?: boolean
    beforeClose?: (action: string, instance: any, done: () => void) => void
  }

  export const ElMessageBox: {
    (options: MessageBoxOptions): Promise<any>
    confirm(message: string, title?: string, options?: MessageBoxOptions): Promise<any>
    alert(message: string, title?: string, options?: MessageBoxOptions): Promise<any>
    prompt(message: string, title?: string, options?: MessageBoxOptions): Promise<any>
  }

  // 表单相关类型
  export interface FormValidateCallback {
    (isValid: boolean, invalidFields?: Record<string, any>): void
  }

  export interface FormInstance {
    validate(): Promise<boolean>
    validate(callback: FormValidateCallback): void
    validateField(props: string | string[]): Promise<boolean>
    validateField(props: string | string[], callback: FormValidateCallback): void
    resetFields(): void
    clearValidate(props?: string | string[]): void
    scrollToField(prop: string): void
  }

  export interface FormItemRule {
    required?: boolean
    message?: string
    trigger?: string | string[]
    min?: number
    max?: number
    len?: number
    pattern?: RegExp
    validator?: (rule: any, value: any, callback: (error?: Error) => void) => void
    asyncValidator?: (rule: any, value: any, callback: (error?: Error) => void) => Promise<void>
  }

  export interface FormRules {
    [key: string]: FormItemRule | FormItemRule[]
  }

  // 表格相关类型
  export interface TableInstance {
    clearSelection(): void
    toggleRowSelection(row: any, selected?: boolean): void
    toggleAllSelection(): void
    toggleRowExpansion(row: any, expanded?: boolean): void
    setCurrentRow(row?: any): void
    clearSort(): void
    clearFilter(columnKeys?: string[]): void
    doLayout(): void
    sort(prop: string, order: string): void
  }
}