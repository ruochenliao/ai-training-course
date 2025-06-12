import React from 'react'
import { Link } from 'react-router-dom'
import { Icon } from '@iconify/react'
import { useAppStore } from '../../store/app'

/**
 * 侧边栏Logo组件 - 对应Vue版本的SideLogo.vue
 * 
 * 功能特性：
 * 1. 显示系统Logo和标题
 * 2. 折叠时只显示Logo
 * 3. 支持点击跳转首页
 * 4. 使用主题色彩
 */
const SideLogo: React.FC = () => {
  const { collapsed } = useAppStore()
  
  // 从环境变量获取标题 - 对应Vue版本的 import.meta.env.VITE_TITLE
  const title = import.meta.env.VITE_TITLE || '智能客服系统'

  return (
    <Link 
      to="/" 
      className="h-60 f-c-c block no-underline"
    >
      {/* Logo图标 - 对应Vue版本的 icon-custom-logo */}
      <Icon 
        icon="mdi:customer-service" 
        className="text-36 color-primary"
      />
      
      {/* 标题 - 对应Vue版本的 v-show="!appStore.collapsed" */}
      {!collapsed && (
        <h2 className="ml-2 mr-8 max-w-150 flex-shrink-0 text-16 font-bold color-primary">
          {title}
        </h2>
      )}
    </Link>
  )
}

export default SideLogo
