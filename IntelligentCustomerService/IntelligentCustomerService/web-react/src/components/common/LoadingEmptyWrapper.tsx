import React from 'react'
import { Empty, Spin } from 'antd'
import { useTranslation } from 'react-i18next'
import { useTheme } from '../../contexts/ThemeContext'
import { cn } from '../../utils'

interface LoadingEmptyWrapperProps {
  loading?: boolean
  empty?: boolean
  children: React.ReactNode
  emptyDescription?: string
  emptyImage?: React.ReactNode
  className?: string
  size?: 'small' | 'default' | 'large'
  minHeight?: number | string
}

/**
 * 加载和空状态包装组件
 * 对应Vue版本的LoadingEmptyWrapper.vue
 */
const LoadingEmptyWrapper: React.FC<LoadingEmptyWrapperProps> = ({
  loading = false,
  empty = false,
  children,
  emptyDescription,
  emptyImage,
  className,
  size = 'default',
  minHeight = 200,
}) => {
  const { t } = useTranslation()
  const { isDark } = useTheme()

  const containerStyle = {
    minHeight: typeof minHeight === 'number' ? `${minHeight}px` : minHeight,
  }

  if (loading) {
    return (
      <div className={cn('flex justify-center items-center', isDark ? 'text-white' : 'text-gray-800', className)} style={containerStyle}>
        <Spin size={size} />
      </div>
    )
  }

  if (empty) {
    return (
      <div className={cn('flex justify-center items-center', className)} style={containerStyle}>
        <Empty description={emptyDescription || t('common.noData') || '暂无数据'} image={emptyImage} />
      </div>
    )
  }

  return <>{children}</>
}

export default LoadingEmptyWrapper
