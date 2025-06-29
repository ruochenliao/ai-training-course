import React from 'react'
import {useTheme} from '@/contexts/ThemeContext.tsx'
import {cn} from '@/utils/index.ts'

/**
 * 应用页脚组件
 * 对应Vue版本的AppFooter.vue
 */
const AppFooter: React.FC = () => {
  const { isDark } = useTheme()
  const currentYear = new Date().getFullYear()

  return (
    <footer className={cn('text-center py-4 text-sm', isDark ? 'text-gray-400' : 'text-gray-500')}>
      <div className='border-t border-gray-200 dark:border-gray-700 pt-4'>© {currentYear} 智能客服系统 • 版权所有</div>
    </footer>
  )
}

export default AppFooter
