import React from 'react'
import SideLogo from './SideLogo.tsx'
import SideMenu from './SideMenu.tsx'

/**
 * 侧边栏组件 - 对应Vue版本的sidebar/index.vue
 *
 * 组件结构：
 * - SideLogo: Logo组件
 * - SideMenu: 导航菜单组件
 */

const Sidebar: React.FC = () => {
  return (
    <>
      <SideLogo />
      <SideMenu />
    </>
  )
}

export default Sidebar
