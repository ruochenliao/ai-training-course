// 组件相关类型定义

import { CSSProperties, ReactNode } from 'react'

// 基础组件 Props
export interface BaseComponentProps {
  className?: string
  style?: CSSProperties
  children?: ReactNode
  id?: string
  'data-testid'?: string
}

// 尺寸类型
export type Size = 'small' | 'medium' | 'large'
export type ButtonSize = 'small' | 'middle' | 'large'

// 颜色类型
export type Color = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info'
export type ButtonType = 'primary' | 'default' | 'dashed' | 'text' | 'link'

// 位置类型
export type Position = 'top' | 'bottom' | 'left' | 'right'
export type Placement =
  | 'top'
  | 'topLeft'
  | 'topRight'
  | 'bottom'
  | 'bottomLeft'
  | 'bottomRight'
  | 'left'
  | 'leftTop'
  | 'leftBottom'
  | 'right'
  | 'rightTop'
  | 'rightBottom'

// 布局组件
export interface LayoutProps extends BaseComponentProps {
  direction?: 'horizontal' | 'vertical'
  align?: 'start' | 'center' | 'end' | 'stretch'
  justify?: 'start' | 'center' | 'end' | 'space-between' | 'space-around' | 'space-evenly'
  gap?: number | string
  wrap?: boolean
}

export interface HeaderProps extends BaseComponentProps {
  title?: string
  subtitle?: string
  extra?: ReactNode
  onBack?: () => void
  showBack?: boolean
}

export interface SidebarProps extends BaseComponentProps {
  collapsed?: boolean
  onCollapse?: (collapsed: boolean) => void
  width?: number
  collapsedWidth?: number
  theme?: 'light' | 'dark'
}

// 表单组件
export interface FormProps extends BaseComponentProps {
  layout?: 'horizontal' | 'vertical' | 'inline'
  onSubmit?: (values: any) => void
  onReset?: () => void
  initialValues?: Record<string, any>
  disabled?: boolean
}

export interface InputProps extends BaseComponentProps {
  value?: string
  defaultValue?: string
  placeholder?: string
  disabled?: boolean
  readOnly?: boolean
  size?: Size
  prefix?: ReactNode
  suffix?: ReactNode
  onChange?: (value: string) => void
  onFocus?: () => void
  onBlur?: () => void
  onPressEnter?: () => void
}

export interface ButtonProps extends BaseComponentProps {
  type?: ButtonType
  size?: ButtonSize
  disabled?: boolean
  loading?: boolean
  icon?: ReactNode
  shape?: 'default' | 'circle' | 'round'
  block?: boolean
  danger?: boolean
  ghost?: boolean
  onClick?: () => void
  htmlType?: 'button' | 'submit' | 'reset'
}

// 数据展示组件
export interface TableProps<T = any> extends BaseComponentProps {
  dataSource?: T[]
  columns?: TableColumn<T>[]
  loading?: boolean
  pagination?: PaginationProps | false
  rowKey?: string | ((record: T) => string)
  scroll?: { x?: number; y?: number }
  size?: Size
  bordered?: boolean
  showHeader?: boolean
}

export interface TableColumn<T = any> {
  title: string
  dataIndex?: string
  key?: string
  width?: number | string
  fixed?: 'left' | 'right'
  align?: 'left' | 'center' | 'right'
  sorter?: boolean | ((a: T, b: T) => number)
  render?: (value: any, record: T, index: number) => ReactNode
  ellipsis?: boolean
}

export interface PaginationProps {
  current?: number
  total?: number
  pageSize?: number
  showSizeChanger?: boolean
  showQuickJumper?: boolean
  onChange?: (page: number, pageSize: number) => void
}

// 反馈组件
export interface ModalProps extends BaseComponentProps {
  visible?: boolean
  title?: string
  width?: number | string
  centered?: boolean
  closable?: boolean
  maskClosable?: boolean
  footer?: ReactNode | null
  confirmLoading?: boolean
  onOk?: () => void
  onCancel?: () => void
}

export interface NotificationProps {
  type?: 'success' | 'info' | 'warning' | 'error'
  title: string
  description?: string
  duration?: number
  onClose?: () => void
}

// 导航组件
export interface MenuProps extends BaseComponentProps {
  mode?: 'horizontal' | 'vertical' | 'inline'
  theme?: 'light' | 'dark'
  selectedKeys?: string[]
  openKeys?: string[]
  inlineCollapsed?: boolean
  onClick?: (info: { key: string; keyPath: string[] }) => void
}

export interface MenuItemProps extends BaseComponentProps {
  key: string
  icon?: ReactNode
  disabled?: boolean
  title?: string
}

// 业务组件
export interface ChatMessageProps extends BaseComponentProps {
  message: {
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    timestamp: string
    loading?: boolean
    error?: boolean
  }
  showAvatar?: boolean
  showTime?: boolean
  onRetry?: () => void
  onCopy?: () => void
}

export interface FileUploadProps extends BaseComponentProps {
  accept?: string
  multiple?: boolean
  maxSize?: number
  disabled?: boolean
  beforeUpload?: (file: File) => boolean | Promise<boolean>
  onChange?: (info: { file: File; fileList: File[] }) => void
  onRemove?: (file: File) => boolean | Promise<boolean>
}

export interface SearchProps extends BaseComponentProps {
  placeholder?: string
  value?: string
  size?: Size
  disabled?: boolean
  loading?: boolean
  onSearch?: (value: string) => void
  onChange?: (value: string) => void
}

// 主题相关
export interface ThemeConfig {
  primaryColor: string
  borderRadius: number
  fontSize: number
  fontFamily: string
  colorBgBase: string
  colorTextBase: string
}

// 响应式相关
export interface ResponsiveProps {
  xs?: any
  sm?: any
  md?: any
  lg?: any
  xl?: any
  xxl?: any
}
