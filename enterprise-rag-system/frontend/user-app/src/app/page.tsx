'use client';

import React, {useState} from 'react';
import {Button, Drawer, Layout, Menu} from 'antd';
import {BarChartOutlined, MenuOutlined, MessageOutlined, NodeIndexOutlined, SearchOutlined} from '@ant-design/icons';
import {GeminiChatInterface} from '@/components/chat/GeminiChatInterface';
import {MultiModeSearch} from '@/components/search/MultiModeSearch';
import {KnowledgeGraph} from '@/components/visualization/KnowledgeGraph';
import {useTheme} from '@/contexts/ThemeContext';

const { Header, Sider, Content } = Layout;

type PageView = 'chat' | 'search' | 'graph' | 'analytics';

export default function HomePage() {
  const { theme } = useTheme();
  const [currentView, setCurrentView] = useState<PageView>('chat');
  const [siderCollapsed, setSiderCollapsed] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  // 菜单项配置
  const menuItems = [
    {
      key: 'chat',
      icon: <MessageOutlined />,
      label: '智能对话',
    },
    {
      key: 'search',
      icon: <SearchOutlined />,
      label: '多模式搜索',
    },
    {
      key: 'graph',
      icon: <NodeIndexOutlined />,
      label: '知识图谱',
    },
    {
      key: 'analytics',
      icon: <BarChartOutlined />,
      label: '数据分析',
    },
  ];

  // 渲染主要内容
  const renderContent = () => {
    switch (currentView) {
      case 'chat':
        return (
          <GeminiChatInterface
            onNewConversation={() => {
              console.log('新建对话');
            }}
          />
        );
      case 'search':
        return (
          <MultiModeSearch
            onSearch={async (query, mode, filters) => {
              console.log('搜索:', { query, mode, filters });
              return [];
            }}
          />
        );
      case 'graph':
        return (
          <KnowledgeGraph
            data={{ nodes: [], links: [] }}
            onNodeClick={(node) => {
              console.log('点击节点:', node);
            }}
            onLinkClick={(link) => {
              console.log('点击连接:', link);
            }}
          />
        );
      case 'analytics':
        return (
          <div className="p-6">
            <h2 style={{ color: theme.colors.onSurface }}>
              数据分析功能开发中...
            </h2>
          </div>
        );
      default:
        return null;
    }
  };

  // 侧边栏内容
  const siderContent = (
    <Menu
      mode="inline"
      selectedKeys={[currentView]}
      items={menuItems}
      onClick={({ key }) => {
        setCurrentView(key as PageView);
        setMobileDrawerOpen(false);
      }}
      style={{
        height: '100%',
        borderRight: 0,
        backgroundColor: 'transparent',
      }}
    />
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 桌面端侧边栏 */}
      <Sider
        collapsible
        collapsed={siderCollapsed}
        onCollapse={setSiderCollapsed}
        breakpoint="lg"
        collapsedWidth={80}
        width={240}
        style={{
          backgroundColor: theme.colors.surface,
          borderRight: `1px solid ${theme.colors.outline}`,
        }}
        className="hidden lg:block"
      >
        <div className="p-4">
          <div
            className="text-lg font-bold text-center"
            style={{ color: theme.colors.primary }}
          >
            {siderCollapsed ? 'RAG' : '企业级RAG系统'}
          </div>
        </div>
        {siderContent}
      </Sider>

      <Layout>
        {/* 移动端头部 */}
        <Header
          className="lg:hidden flex items-center justify-between px-4"
          style={{
            backgroundColor: theme.colors.surface,
            borderBottom: `1px solid ${theme.colors.outline}`,
            height: 64,
          }}
        >
          <div
            className="text-lg font-bold"
            style={{ color: theme.colors.primary }}
          >
            企业级RAG系统
          </div>
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={() => setMobileDrawerOpen(true)}
            style={{ color: theme.colors.onSurface }}
          />
        </Header>

        {/* 主要内容区域 */}
        <Content
          style={{
            backgroundColor: theme.colors.background,
            minHeight: 'calc(100vh - 64px)',
          }}
          className="lg:min-h-screen"
        >
          {renderContent()}
        </Content>
      </Layout>

      {/* 移动端抽屉菜单 */}
      <Drawer
        title="菜单"
        placement="left"
        onClose={() => setMobileDrawerOpen(false)}
        open={mobileDrawerOpen}
        className="lg:hidden"
        bodyStyle={{ padding: 0 }}
      >
        {siderContent}
      </Drawer>
    </Layout>
  );
}
