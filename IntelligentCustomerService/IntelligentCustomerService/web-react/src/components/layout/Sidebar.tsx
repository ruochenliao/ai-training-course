import React, {useState} from 'react'
import type {MenuProps} from 'antd'
import {Layout, Menu} from 'antd'
import {
    ApartmentOutlined,
    ApiOutlined,
    AppstoreOutlined,
    DashboardOutlined,
    FileSearchOutlined,
    MenuOutlined,
    TeamOutlined,
    UserOutlined,
    WarningOutlined
} from '@ant-design/icons'
import {useLocation, useNavigate} from 'react-router-dom'
import {useTranslation} from 'react-i18next'
import {useThemeStore} from '@/store/theme'

const { Sider } = Layout

type MenuItem = Required<MenuProps>['items'][number]

const Sidebar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { sidebarCollapsed } = useThemeStore()
  
  // 默认展开的子菜单
  const [openKeys, setOpenKeys] = useState<string[]>(() => {
    const pathname = location.pathname;
    if (pathname.startsWith('/dashboard/system')) return ['system'];
    if (pathname.startsWith('/dashboard/error')) return ['error'];
    return [];
  });

  // 菜单项
  const menuItems: MenuItem[] = [
    {
      key: '/dashboard/workbench',
      icon: <DashboardOutlined />,
      label: '工作台',
    },
    {
      key: 'system',
      icon: <AppstoreOutlined />,
      label: '系统管理',
      children: [
        {
          key: '/dashboard/system/user',
          icon: <UserOutlined />,
          label: '用户管理',
        },
        {
          key: '/dashboard/system/role',
          icon: <TeamOutlined />,
          label: '角色管理',
        },
        {
          key: '/dashboard/system/menu',
          icon: <MenuOutlined />,
          label: '菜单管理',
        },
        {
          key: '/dashboard/system/api',
          icon: <ApiOutlined />,
          label: 'API管理',
        },
        {
          key: '/dashboard/system/dept',
          icon: <ApartmentOutlined />,
          label: '部门管理',
        },
        {
          key: '/dashboard/system/auditlog',
          icon: <FileSearchOutlined />,
          label: '审计日志',
        },
      ],
    },
    {
      key: '/dashboard/menu',
      icon: <AppstoreOutlined />,
      label: '一级菜单',
    },
    {
      key: 'error',
      icon: <WarningOutlined />,
      label: '错误页',
      children: [
        {
          key: '/dashboard/error/401',
          label: '401',
        },
        {
          key: '/dashboard/error/403',
          label: '403',
        },
        {
          key: '/dashboard/error/404',
          label: '404',
        },
        {
          key: '/dashboard/error/500',
          label: '500',
        },
      ],
    },
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    // 不要导航到父菜单项
    if (key === 'system' || key === 'error') return;
    navigate(key);
  }

  // 处理子菜单展开/收起
  const handleOpenChange = (keys: string[]) => {
    setOpenKeys(keys);
  };

  // 获取当前选中的菜单项
  const getSelectedKeys = () => {
    const pathname = location.pathname;
    return [pathname];
  }

  return (
    <Sider
      className="sidebar"
      collapsed={sidebarCollapsed}
      width={220}
      collapsedWidth={64}
      theme="light"
      style={{ background: '#fff' }}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-gray-200">
        {sidebarCollapsed ? (
          <div className="text-xl font-bold text-primary-600">VFA</div>
        ) : (
          <div className="text-xl font-bold text-primary-600">
            Vue FastAPI Admin
          </div>
        )}
      </div>

      {/* 菜单 */}
      <Menu
        mode="inline"
        selectedKeys={getSelectedKeys()}
        openKeys={openKeys}
        onOpenChange={handleOpenChange}
        items={menuItems}
        onClick={handleMenuClick}
        className="border-r-0"
        style={{ borderRight: 'none' }}
      />
    </Sider>
  )
}

export default Sidebar