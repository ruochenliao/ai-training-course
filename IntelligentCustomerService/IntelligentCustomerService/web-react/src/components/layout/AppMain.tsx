import React from 'react'
import { useAppStore } from '../../store/app'

interface AppMainProps {
  children?: React.ReactNode
}

/**
 * 主内容区域组件 - 对应Vue版本的AppMain.vue
 * 
 * 功能特性：
 * 1. 渲染当前路由对应的页面组件
 * 2. 支持页面重载功能
 * 3. 对应Vue版本的router-view和KeepAlive功能
 */
const AppMain: React.FC<AppMainProps> = ({ children }) => {
  const { reloading } = useAppStore()

  // 对应Vue版本的 v-if="appStore.reloadFlag"
  if (reloading) {
    return (
      <div className="wh-full flex-center">
        <div className="text-gray-500">页面重载中...</div>
      </div>
    )
  }

  // 对应Vue版本的 router-view 渲染
  return (
    <div className="wh-full overflow-auto">
      {children}
    </div>
  )
}

export default AppMain
