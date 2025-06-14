import React from 'react'
import {Button} from 'antd'
import {Icon} from '@iconify/react'
import {useTheme} from '../../contexts/ThemeContext'

/**
 * 主题模式切换组件 - 对应Vue版本的ThemeMode.vue
 *
 * 功能特性：
 * 1. 亮色/暗色主题切换
 * 2. 图标动态显示
 * 3. 主题状态持久化
 */
const ThemeMode: React.FC = () => {
  const { isDark, toggleTheme } = useTheme()

  return (
    <Button
      type='text'
      icon={<Icon icon={isDark ? 'mdi:weather-sunny' : 'mdi:weather-night'} style={{ fontSize: '16px' }} />}
      onClick={toggleTheme}
      className='flex-center'
      title={isDark ? '切换到亮色模式' : '切换到暗色模式'}
    />
  )
}

export default ThemeMode
