import React from 'react'
import {Icon} from '@iconify/react'
import {useAppStore} from '../../store/app'

/**
 * 菜单折叠按钮组件 - 对应Vue版本的MenuCollapse.vue
 *
 * 功能特性：
 * 1. 图标大小20px，鼠标指针样式
 * 2. 折叠状态显示展开图标（format-indent-increase）
 * 3. 展开状态显示折叠图标（format-indent-decrease）
 * 4. 点击切换侧边栏折叠状态
 */
const MenuCollapse: React.FC = () => {
  const { collapsed, toggleCollapsed } = useAppStore()

  return (
    <Icon
      icon={collapsed ? 'mdi:format-indent-increase' : 'mdi:format-indent-decrease'}
      style={{ fontSize: '20px', cursor: 'pointer' }}
      onClick={toggleCollapsed}
    />
  )
}

export default MenuCollapse
