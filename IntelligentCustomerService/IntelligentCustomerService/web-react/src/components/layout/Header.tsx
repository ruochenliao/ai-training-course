import React from 'react'
import MenuCollapse from './MenuCollapse'
import BreadCrumb from './Breadcrumb'
import Languages from './Languages'
import ThemeMode from './ThemeMode'
import FullScreen from './FullScreen'
import GithubSite from './GithubSite'
import UserAvatar from './UserAvatar'

/**
 * 顶部导航栏组件 - 对应Vue版本的header/index.vue
 *
 * 布局特性：
 * - 左侧：菜单折叠按钮 + 面包屑导航
 * - 右侧：功能按钮组 + 用户头像
 * - 响应式隐藏（面包屑在小屏幕隐藏）
 */

const Header: React.FC = () => {
  return (
    <div className="flex items-center w-full">
      {/* 左侧区域 - 对应Vue版本的第一个div */}
      <div className="flex items-center">
        <MenuCollapse />
        <div className="ml-15 hidden sm:block">
          <BreadCrumb />
        </div>
      </div>

      {/* 右侧区域 - 对应Vue版本的第二个div */}
      <div className="ml-auto flex items-center">
        <Languages />
        <ThemeMode />
        <GithubSite />
        <FullScreen />
        <UserAvatar />
      </div>
    </div>
  )
}

export default Header