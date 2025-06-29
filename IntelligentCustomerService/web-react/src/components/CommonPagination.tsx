import React from 'react'
import {TablePaginationConfig} from 'antd'

export interface PaginationProps {
  current: number
  pageSize: number
  total: number
  onChange: (page: number, pageSize: number) => void
  onShowSizeChange?: (current: number, size: number) => void
  showQuickJumper?: boolean
  showSizeChanger?: boolean
  pageSizeOptions?: string[]
  className?: string
  style?: React.CSSProperties
}

/**
 * 通用分页组件配置
 * @param props 分页属性
 * @returns TablePaginationConfig对象
 */
export const CommonPagination = (props: PaginationProps): TablePaginationConfig => {
  const {
    current,
    pageSize,
    total,
    onChange,
    onShowSizeChange,
    showQuickJumper = true,
    showSizeChanger = true,
    pageSizeOptions = ['10', '20', '50', '100'],
    className,
    style,
  } = props

  const config: TablePaginationConfig = {
    current,
    pageSize,
    total,
    showQuickJumper,
    showSizeChanger,
    pageSizeOptions,
    onChange: (page, size) => {
      onChange(page, size)
    },
    onShowSizeChange:
      onShowSizeChange ||
      ((current, size) => {
        onChange(current, size)
      }),
    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条/总共 ${total} 条`,
  }

  // 仅当值存在时才添加样式和类名
  if (className) {
    config.className = className
  }

  if (style) {
    config.style = style
  }

  return config
}

export default CommonPagination
