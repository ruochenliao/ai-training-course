import React from 'react'
import {Button} from 'antd'
import {Icon} from '@iconify/react'
import {useAppStore} from '@/store/app.ts'

/**
 * 全屏切换组件 - 对应Vue版本的FullScreen.vue
 *
 * 功能特性：
 * 1. 全屏/退出全屏切换
 * 2. 图标动态显示
 * 3. 浏览器全屏API调用
 */
const FullScreen: React.FC = () => {
  const { fullscreen, toggleFullscreen } = useAppStore()

  const handleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
    toggleFullscreen()
  }

  return (
    <Button
      type='text'
      icon={<Icon icon={fullscreen ? 'mdi:fullscreen-exit' : 'mdi:fullscreen'} style={{ fontSize: '16px' }} />}
      onClick={handleFullscreen}
      className='flex-center'
      title={fullscreen ? '退出全屏' : '全屏'}
    />
  )
}

export default FullScreen
