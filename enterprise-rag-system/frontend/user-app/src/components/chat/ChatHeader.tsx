/**
 * 聊天头部组件
 * 显示对话信息、连接状态和操作按钮
 */

'use client';

import React, {useState} from 'react';
import {motion} from 'framer-motion';
import {Badge, Button, Dropdown, Modal, Switch, Tooltip, Typography} from 'antd';
import {
    BarChartOutlined,
    BulbFilled,
    BulbOutlined,
    DisconnectOutlined,
    MoreOutlined,
    PlusOutlined,
    SearchOutlined,
    SettingOutlined,
    ShareAltOutlined,
    WifiOutlined
} from '@ant-design/icons';
import {useTheme, useThemeToggle} from '@/contexts/ThemeContext';

const { Text } = Typography;

interface ChatHeaderProps {
  conversationId?: string;
  onNewConversation?: () => void;
  onShowSearch?: () => void;
  onShowAnalytics?: () => void;
  onShowSettings?: () => void;
  isConnected?: boolean;
  className?: string;
}

export function ChatHeader({
  conversationId,
  onNewConversation,
  onShowSearch,
  onShowAnalytics,
  onShowSettings,
  isConnected = false,
  className = ''
}: ChatHeaderProps) {
  const { theme, themeName } = useTheme();
  const { toggleTheme, isDark } = useThemeToggle();
  const [showSettings, setShowSettings] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);

  // 更多操作菜单
  const moreMenuItems = [
    {
      key: 'search',
      label: '高级搜索',
      icon: <SearchOutlined />,
      onClick: onShowSearch
    },
    {
      key: 'analytics',
      label: '数据分析',
      icon: <BarChartOutlined />,
      onClick: onShowAnalytics
    },
    {
      type: 'divider' as const
    },
    {
      key: 'share',
      label: '分享对话',
      icon: <ShareAltOutlined />,
      onClick: () => {
        // 实现分享功能
        if (navigator.share) {
          navigator.share({
            title: '智能对话',
            text: '查看我与AI的对话',
            url: window.location.href
          });
        } else {
          // 复制链接到剪贴板
          navigator.clipboard.writeText(window.location.href);
        }
      }
    },
    {
      key: 'settings',
      label: '设置',
      icon: <SettingOutlined />,
      onClick: () => setShowSettings(true)
    }
  ];

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`flex items-center justify-between px-4 py-3 border-b ${className}`}
        style={{ 
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.outline 
        }}
      >
        {/* 左侧：标题和状态 */}
        <div className="flex items-center gap-3">
          {/* 标题 */}
          <div>
            <Text 
              strong 
              className="text-lg"
              style={{ color: theme.colors.onSurface }}
            >
              智能助手
            </Text>
            {conversationId && (
              <Text 
                className="text-sm ml-2"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                #{conversationId.slice(-8)}
              </Text>
            )}
          </div>

          {/* 连接状态 */}
          <Badge 
            status={isConnected ? "success" : "error"} 
            text={
              <span style={{ color: theme.colors.onSurfaceVariant }}>
                {isConnected ? "已连接" : "未连接"}
              </span>
            }
          />
        </div>

        {/* 右侧：操作按钮 */}
        <div className="flex items-center gap-2">
          {/* 主题切换 */}
          <Tooltip title={isDark ? "切换到浅色主题" : "切换到深色主题"}>
            <Button
              type="text"
              icon={isDark ? <BulbOutlined /> : <BulbFilled />}
              onClick={toggleTheme}
              style={{ color: theme.colors.onSurfaceVariant }}
            />
          </Tooltip>

          {/* 连接状态指示 */}
          <Tooltip title={isConnected ? "WebSocket已连接" : "WebSocket未连接"}>
            <Button
              type="text"
              icon={isConnected ? <WifiOutlined /> : <DisconnectOutlined />}
              style={{ 
                color: isConnected ? theme.colors.success : theme.colors.error 
              }}
            />
          </Tooltip>

          {/* 新建对话 */}
          <Tooltip title="新建对话">
            <Button
              type="text"
              icon={<PlusOutlined />}
              onClick={onNewConversation}
              style={{ color: theme.colors.onSurfaceVariant }}
            />
          </Tooltip>

          {/* 更多操作 */}
          <Dropdown 
            menu={{ items: moreMenuItems }} 
            placement="bottomRight"
            trigger={['click']}
          >
            <Button
              type="text"
              icon={<MoreOutlined />}
              style={{ color: theme.colors.onSurfaceVariant }}
            />
          </Dropdown>
        </div>
      </motion.div>

      {/* 设置模态框 */}
      <Modal
        title="聊天设置"
        open={showSettings}
        onCancel={() => setShowSettings(false)}
        footer={[
          <Button key="cancel" onClick={() => setShowSettings(false)}>
            取消
          </Button>,
          <Button 
            key="ok" 
            type="primary" 
            onClick={() => setShowSettings(false)}
            style={{
              backgroundColor: theme.colors.primary,
              borderColor: theme.colors.primary
            }}
          >
            确定
          </Button>
        ]}
        style={{ 
          backgroundColor: theme.colors.surface,
          color: theme.colors.onSurface 
        }}
      >
        <div className="space-y-4">
          {/* 主题设置 */}
          <div className="flex items-center justify-between">
            <div>
              <div style={{ color: theme.colors.onSurface }}>深色主题</div>
              <div 
                className="text-sm"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                切换界面主题颜色
              </div>
            </div>
            <Switch
              checked={isDark}
              onChange={toggleTheme}
              checkedChildren={<BulbFilled />}
              unCheckedChildren={<BulbOutlined />}
            />
          </div>

          {/* 自动滚动 */}
          <div className="flex items-center justify-between">
            <div>
              <div style={{ color: theme.colors.onSurface }}>自动滚动</div>
              <div 
                className="text-sm"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                新消息时自动滚动到底部
              </div>
            </div>
            <Switch
              checked={autoScroll}
              onChange={setAutoScroll}
            />
          </div>

          {/* 声音提示 */}
          <div className="flex items-center justify-between">
            <div>
              <div style={{ color: theme.colors.onSurface }}>声音提示</div>
              <div 
                className="text-sm"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                收到新消息时播放提示音
              </div>
            </div>
            <Switch
              checked={soundEnabled}
              onChange={setSoundEnabled}
            />
          </div>

          {/* 快捷键说明 */}
          <div>
            <div 
              className="mb-2"
              style={{ color: theme.colors.onSurface }}
            >
              快捷键
            </div>
            <div className="space-y-1 text-sm">
              <div style={{ color: theme.colors.onSurfaceVariant }}>
                <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Enter</kbd> 发送消息
              </div>
              <div style={{ color: theme.colors.onSurfaceVariant }}>
                <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Shift + Enter</kbd> 换行
              </div>
              <div style={{ color: theme.colors.onSurfaceVariant }}>
                <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Ctrl + K</kbd> 新建对话
              </div>
              <div style={{ color: theme.colors.onSurfaceVariant }}>
                <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">Ctrl + /</kbd> 显示帮助
              </div>
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}
