import React from 'react'
import {Space} from 'antd'
import MenuCollapse from './MenuCollapse.tsx'
import BreadCrumb from './Breadcrumb.tsx'
import Languages from './Languages.tsx'
import ThemeMode from './ThemeMode.tsx'
import FullScreen from './FullScreen.tsx'
import GithubSite from './GithubSite.tsx'
import UserAvatar from './UserAvatar.tsx'

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
    <div
      className='enterprise-header-content'
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        height: '100%',
      }}
    >
      {/* 左侧区域：菜单折叠和面包屑导航 */}
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <MenuCollapse />
        <div
          className='enterprise-breadcrumb'
          style={{
            marginLeft: '16px',
            display: window.innerWidth > 768 ? 'block' : 'none',
          }}
        >
          <BreadCrumb />
        </div>
      </div>

      {/* 右侧区域：功能区和用户信息 */}
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Space size='large' className='enterprise-header-actions'>
          <Languages />
          <ThemeMode />
          <FullScreen />
          <GithubSite />
        </Space>
        <div
          className='enterprise-user-section'
          style={{
            marginLeft: '24px',
            paddingLeft: '24px',
            borderLeft: '1px solid #f0f0f0',
          }}
        >
          <UserAvatar />
        </div>
      </div>
    </div>
  )
}

export default Header
