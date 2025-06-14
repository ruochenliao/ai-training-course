import React from 'react'
import { BackTop } from 'antd'
import { useTheme } from '../../contexts/ThemeContext'
import { cn } from '../../utils'
import AppFooter from '../common/AppFooter'

interface AppPageProps {
  children: React.ReactNode
  showFooter?: boolean
  className?: string
}

/**
 * 应用页面容器组件
 * 对应Vue版本的AppPage.vue
 */
const AppPage: React.FC<AppPageProps> = ({ children, showFooter = false, className }) => {
  const { isDark } = useTheme()

  return (
    <section
      className={cn(
        // 对应Vue版本的 cus-scroll-y wh-full flex-col bg-[#f5f6fb] p-15 dark:bg-hex-121212
        'custom-scroll-y w-full h-full flex flex-col p-4',
        isDark ? 'bg-gray-900' : 'bg-gray-50',
        className,
      )}
      style={{
        // 页面切换动画效果
        animation: 'fadeSlideIn 0.3s ease-out',
      }}
    >
      {children}

      {showFooter && (
        <div className='mt-4'>
          <AppFooter />
        </div>
      )}

      <BackTop style={{ bottom: 20 }} visibilityHeight={400} />
    </section>
  )
}

export default AppPage
