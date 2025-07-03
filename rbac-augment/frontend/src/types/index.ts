/**
 * 类型定义入口文件
 */

export * from './api'
export * from './auth'
export * from './user'
export * from './role'
export * from './permission'
export * from './menu'
export * from './department'

// 通用类型
export interface SelectOption {
  label: string
  value: string | number
  disabled?: boolean
}

// 表格列配置
export interface TableColumn {
  prop: string
  label: string
  width?: string | number
  minWidth?: string | number
  fixed?: boolean | string
  sortable?: boolean
  align?: 'left' | 'center' | 'right'
  formatter?: (row: any, column: any, cellValue: any, index: number) => string
}

// 表单规则
export interface FormRule {
  required?: boolean
  message?: string
  trigger?: string | string[]
  min?: number
  max?: number
  pattern?: RegExp
  validator?: (rule: any, value: any, callback: any) => void
}

// 路由元信息
export interface RouteMeta {
  title?: string
  icon?: string
  cache?: boolean
  hidden?: boolean
  external?: boolean
  roles?: string[]
  permissions?: string[]
}

// 组件尺寸
export type ComponentSize = 'large' | 'default' | 'small'

// 主题模式
export type ThemeMode = 'light' | 'dark' | 'auto'

// 语言类型
export type Language = 'zh-CN' | 'en-US'
