import React from 'react';
import { Layout, Menu, Avatar, Dropdown, Typography, Space, Button, Breadcrumb } from 'antd';
import {
  HomeOutlined,
  EditOutlined,
  DatabaseOutlined,
  RobotOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  FileTextOutlined,
  BulbOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/useAuthStore';

const { Header } = Layout;
const { Text } = Typography;

interface GlobalNavigationProps {
  style?: React.CSSProperties;
}

const GlobalNavigation: React.FC<GlobalNavigationProps> = ({ style }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();

  // 根据当前路径确定选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path === '/' || path === '/home') return 'home';
    if (path.startsWith('/editor') || path.startsWith('/standard-editor') || path.startsWith('/ai-writing')) return 'editor';
    if (path.startsWith('/templates')) return 'templates';
    if (path.startsWith('/agents')) return 'agents';
    if (path.startsWith('/writing-themes')) return 'writing-themes';
    return '';
  };

  // 获取面包屑导航
  const getBreadcrumbItems = () => {
    const path = location.pathname;
    const items = [
      {
        title: <HomeOutlined />,
        onClick: () => navigate('/')
      }
    ];

    if (path.startsWith('/templates')) {
      items.push({
        title: '模板管理',
        onClick: () => navigate('/templates')
      });
    } else if (path.startsWith('/agents')) {
      items.push({
        title: '智能体管理',
        onClick: () => navigate('/agents')
      });
    } else if (path.startsWith('/writing-themes')) {
      items.push({
        title: '写作主题管理',
        onClick: () => navigate('/writing-themes')
      });
    } else if (path.startsWith('/ai-writing')) {
      items.push({
        title: '开始写作',
        onClick: () => navigate('/standard-editor')
      });
      items.push({
        title: 'AI写作向导'
      });
    } else if (path.startsWith('/editor') || path.startsWith('/standard-editor')) {
      items.push({
        title: '开始写作'
      });
    }

    return items;
  };

  // 菜单项配置
  const menuItems = [
    {
      key: 'home',
      icon: <HomeOutlined />,
      label: '首页',
      onClick: () => navigate('/')
    },
    {
      key: 'editor',
      icon: <EditOutlined />,
      label: '开始写作',
      onClick: () => navigate('/standard-editor')
    }
  ];

  // 管理员菜单项
  if (user?.is_superuser) {
    menuItems.push(
      {
        key: 'templates',
        icon: <DatabaseOutlined />,
        label: '模板管理',
        onClick: () => navigate('/templates')
      },
      {
        key: 'writing-themes',
        icon: <BulbOutlined />,
        label: '写作主题管理',
        onClick: () => navigate('/writing-themes')
      },
      {
        key: 'agents',
        icon: <RobotOutlined />,
        label: '智能体管理',
        onClick: () => navigate('/agents')
      }
    );
  }

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料'
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置'
    },
    {
      type: 'divider' as const
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout
    }
  ];

  return (
    <div>
      <Header
        style={{
          background: '#fff',
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 1000,
          ...style
        }}
      >
        {/* 左侧：Logo + 导航菜单 */}
        <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
          {/* Logo */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              marginRight: 32,
              cursor: 'pointer'
            }}
            onClick={() => navigate('/')}
          >
            <FileTextOutlined style={{ fontSize: 24, color: '#1890ff', marginRight: 8 }} />
            <Typography.Title level={4} style={{ margin: 0, color: '#1890ff' }}>
              AI写作平台
            </Typography.Title>
          </div>

          {/* 导航菜单 */}
          <Menu
            mode="horizontal"
            selectedKeys={[getSelectedKey()]}
            style={{
              border: 'none',
              background: 'transparent',
              flex: 1,
              minWidth: 0
            }}
            items={menuItems}
          />
        </div>

        {/* 右侧：用户信息 */}
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div style={{
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              padding: '8px 12px',
              borderRadius: 6,
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f5f5f5';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
            >
              <Avatar
                icon={<UserOutlined />}
                style={{ marginRight: 8 }}
                size="small"
              />
              <Text style={{ maxWidth: 120 }} ellipsis>
                {user?.full_name || user?.username || '用户'}
              </Text>
            </div>
          </Dropdown>
        </div>
      </Header>

      {/* 面包屑导航 */}
      {getBreadcrumbItems().length > 1 && (
        <div style={{
          background: '#fafafa',
          padding: '8px 24px',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <Breadcrumb
            items={getBreadcrumbItems()}
            style={{ fontSize: 12 }}
          />
        </div>
      )}
    </div>
  );
};

export default GlobalNavigation;
