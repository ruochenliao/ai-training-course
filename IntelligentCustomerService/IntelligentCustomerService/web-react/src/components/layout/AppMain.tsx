import React from 'react'
import { Spin } from 'antd'
import { useAppStore } from '@/store/app.ts'

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

  // 页面重载时显示加载状态
  if (reloading) {
    return (
      <div className='flex items-center justify-center h-full w-full'>
        <Spin size='large' tip='页面重载中...' />
      </div>
    )
  }

  // 渲染页面内容
  return (
    <div className='h-full w-full overflow-auto p-4'>
      <div className='fade-in'>{children}</div>
    </div>
  )
}

export default AppMain
