import React, {useCallback, useEffect, useState} from 'react'
import {Avatar, Badge, Button, Card, Dropdown, Layout, Menu, Modal, notification, Space, Tabs} from 'antd'
import {
    BarChartOutlined,
    BellOutlined,
    BookOutlined,
    GlobalOutlined,
    LogoutOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    MessageOutlined,
    PhoneOutlined,
    SettingOutlined,
    TeamOutlined,
    UserOutlined
} from '@ant-design/icons'
import ChatInterface from '@/components/CustomerService/ChatInterface'
import SessionList from '@/components/CustomerService/SessionList'
import KnowledgeBase from '@/components/CustomerService/KnowledgeBase'
import StatsDashboard from '@/components/CustomerService/StatsDashboard'
import './index.less'

// Mock数据类型定义
interface Message {
  id: string
  sessionId: string
  content: string
  type: 'text' | 'image' | 'file'
  sender: 'user' | 'agent'
  timestamp: number
}

interface Session {
  id: string
  userInfo: {
    id: string
    nickname: string
    avatar?: string
  }
  status: 'active' | 'waiting' | 'closed'
  lastMessage?: Message
  unreadCount: number
  createdAt: number
}

// Mock数据
const mockSessions: Session[] = [
  {
    id: '1',
    userInfo: {
      id: 'user1',
      nickname: '张三',
      avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4'
    },
    status: 'active',
    lastMessage: {
      id: 'msg1',
      sessionId: '1',
      content: '你好，我想咨询一下产品问题',
      type: 'text',
      sender: 'user',
      timestamp: Date.now() - 300000
    },
    unreadCount: 2,
    createdAt: Date.now() - 600000
  },
  {
    id: '2',
    userInfo: {
      id: 'user2',
      nickname: '李四',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=2'
    },
    status: 'waiting',
    lastMessage: {
      id: 'msg2',
      sessionId: '2',
      content: '请问售后服务怎么联系？',
      type: 'text',
      sender: 'user',
      timestamp: Date.now() - 180000
    },
    unreadCount: 1,
    createdAt: Date.now() - 900000
  },
  {
    id: '3',
    userInfo: {
      id: 'user3',
      nickname: '王五',
      avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=3'
    },
    status: 'active',
    lastMessage: {
      id: 'msg3',
      sessionId: '3',
      content: '谢谢您的帮助！',
      type: 'text',
      sender: 'user',
      timestamp: Date.now() - 120000
    },
    unreadCount: 0,
    createdAt: Date.now() - 1200000
  }
]

const mockNotifications = [
  {
    id: '1',
    title: '新用户接入',
    content: '用户张三发起了新的咨询会话',
    timestamp: Date.now() - 300000
  },
  {
    id: '2',
    title: '系统通知',
    content: '知识库已更新，请及时查看新增内容',
    timestamp: Date.now() - 600000
  }
]

// 格式化时间的工具函数
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleDateString()
  }
}

const { Header, Sider, Content } = Layout
const { TabPane } = Tabs

interface CustomerServiceProps {
  agentInfo?: {
    id: string
    name: string
    avatar?: string
    role: string
    status: 'online' | 'offline' | 'busy'
  }
}

const CustomerService: React.FC<CustomerServiceProps> = ({ agentInfo }) => {
  const [collapsed, setCollapsed] = useState(false)
  const [selectedMenu, setSelectedMenu] = useState('sessions')
  const [currentSession, setCurrentSession] = useState<Session | null>(null)
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState<any[]>(mockNotifications)
  const [showKnowledgeModal, setShowKnowledgeModal] = useState(false)
  const [agentStatus, setAgentStatus] = useState<'online' | 'offline' | 'busy'>('online')
  const [activeSessions, setActiveSessions] = useState<Session[]>(mockSessions)
  const [queueCount, setQueueCount] = useState(0)

  // 模拟WebSocket连接
  const isConnected = true
  const sendMessage = useCallback((message: any) => {
    console.log('发送消息:', message)
    // 模拟消息发送成功
    setTimeout(() => {
      notification.success({
        message: '消息发送成功',
        description: '您的消息已成功发送给用户'
      })
    }, 500)
  }, [])

  // 连接状态
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connected')

  // 模拟WebSocket消息处理
  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'new_session':
        // 新会话分配
        setActiveSessions(prev => [...prev, data.session])
        setQueueCount(prev => prev + 1)
        notification.info({
          message: '新会话分配',
          description: `用户 ${data.session.userInfo.nickname} 发起了新的咨询`
        })
        break
        
      case 'new_message':
        // 新消息
        if (data.message.sender === 'user') {
          setUnreadCount(prev => prev + 1)
          notification.info({
            message: '新消息',
            description: data.message.content
          })
        }
        break
        
      case 'session_closed':
        // 会话关闭
        setActiveSessions(prev => prev.filter(s => s.id !== data.sessionId))
        if (currentSession?.id === data.sessionId) {
          setCurrentSession(null)
        }
        break
        
      default:
        console.log('未知消息类型:', data.type)
    }
  }, [currentSession])

  // 模拟处理新消息
  const handleNewMessage = useCallback((message: Message) => {
    // 如果不是当前会话的消息，增加未读计数
    if (!currentSession || currentSession.id !== message.sessionId) {
      setUnreadCount(prev => prev + 1)
      
      // 显示桌面通知
      if (Notification.permission === 'granted') {
        new Notification('新消息', {
          body: message.content,
          icon: '/favicon.ico'
        })
      }
    }
  }, [currentSession])

  // 模拟处理会话分配
  const handleSessionAssigned = useCallback((session: Session) => {
    setActiveSessions(prev => [...prev, session])
    notification.info({
      message: '新会话分配',
      description: `用户 ${session.userInfo.nickname} 的会话已分配给您`,
      placement: 'topRight'
    })
  }, [])

  // 模拟处理会话关闭
  const handleSessionClosed = useCallback((sessionId: string) => {
    setActiveSessions(prev => prev.filter(s => s.id !== sessionId))
    if (currentSession?.id === sessionId) {
      setCurrentSession(null)
    }
  }, [currentSession])

  // 模拟处理通知
  const handleNotification = useCallback((notificationData: any) => {
    setNotifications(prev => [notificationData, ...prev.slice(0, 9)])
    notification.open({
      message: notificationData.title,
      description: notificationData.content,
      placement: 'topRight',
      duration: 4.5
    })
  }, [])

  // 选择会话
  const handleSessionSelect = useCallback((session: Session) => {
    setCurrentSession(session)
    setSelectedMenu('chat')
    // 清除该会话的未读计数
    setUnreadCount(prev => Math.max(0, prev - 1))
  }, [])

  // 模拟客服状态变更
  const handleAgentStatusChange = useCallback((status: 'online' | 'busy' | 'offline') => {
    setAgentStatus(status)
    
    // 模拟通过WebSocket通知状态变更
    sendMessage({
      type: 'agent_status_change',
      status,
      timestamp: Date.now()
    })
    
    notification.success({
      message: '状态更新成功',
      description: `您的状态已更新为${status === 'online' ? '在线' : status === 'busy' ? '忙碌' : '离线'}`,
      placement: 'topRight'
    })
  }, [sendMessage])

  // 模拟退出登录
  const handleLogout = useCallback(() => {
    Modal.confirm({
      title: '确认退出',
      content: '退出后将无法接收新的客服会话，确认退出吗？',
      onOk: () => {
        // 模拟发送下线消息
        sendMessage({
          type: 'agent_offline',
          timestamp: Date.now()
        })
        
        notification.success({
          message: '退出成功',
          description: '您已成功退出系统',
          placement: 'topRight'
        })
        
        // 模拟跳转到登录页
        setTimeout(() => {
          console.log('模拟跳转到登录页')
        }, 1000)
      }
    })
  }, [sendMessage])

  // 菜单项配置
  const menuItems = [
    {
      key: 'sessions',
      icon: <MessageOutlined />,
      label: (
        <Badge count={unreadCount} size="small">
          <span>会话列表</span>
        </Badge>
      )
    },
    {
      key: 'chat',
      icon: <TeamOutlined />,
      label: '当前会话',
      disabled: !currentSession
    },
    {
      key: 'knowledge',
      icon: <BookOutlined />,
      label: '知识库'
    },
    {
      key: 'stats',
      icon: <BarChartOutlined />,
      label: '数据统计'
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置'
    }
  ]

  // 状态菜单
  const statusMenu = {
    items: [
      {
        key: 'online',
        label: (
          <Space>
            <div className="status-dot status-online"></div>
            在线
          </Space>
        ),
        onClick: () => handleAgentStatusChange('online')
      },
      {
        key: 'busy',
        label: (
          <Space>
            <div className="status-dot status-busy"></div>
            忙碌
          </Space>
        ),
        onClick: () => handleAgentStatusChange('busy')
      },
      {
        key: 'offline',
        label: (
          <Space>
            <div className="status-dot status-offline"></div>
            离线
          </Space>
        ),
        onClick: () => handleAgentStatusChange('offline')
      }
    ]
  }

  // 用户菜单
  const userMenu = {
    items: [
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
        onClick: handleLogout
      }
    ]
  }

  // 渲染内容区域
  const renderContent = () => {
    switch (selectedMenu) {
      case 'sessions':
        return (
          <SessionList
            sessions={activeSessions}
            selectedSession={currentSession}
            onSessionSelect={setCurrentSession}
            unreadCount={unreadCount}
          />
        )
      case 'chat':
        return (
          <div style={{ display: 'flex', height: '100%' }}>
            <div style={{ width: '300px', borderRight: '1px solid #f0f0f0' }}>
              <SessionList
                sessions={activeSessions}
                selectedSession={currentSession}
                onSessionSelect={setCurrentSession}
                unreadCount={unreadCount}
              />
            </div>
            <div style={{ flex: 1 }}>
              {currentSession ? (
                <ChatInterface
                  session={currentSession}
                  onSendMessage={sendMessage}
                  onKnowledgeSearch={() => setShowKnowledgeModal(true)}
                />
              ) : (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: '#999'
                }}>
                  请选择一个会话开始聊天
                </div>
              )}
            </div>
          </div>
        )
      case 'knowledge':
        return <KnowledgeBase mode="manage" />
      case 'stats':
        return <StatsDashboard agentId={agentInfo?.id} />
      case 'settings':
        return (
          <Card title="系统设置">
            <p>设置功能开发中...</p>
          </Card>
        )
      default:
        return null
    }
  }

  // 请求通知权限
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  // 模拟加载活跃会话
  useEffect(() => {
    // 模拟异步加载数据
    const loadActiveSessions = () => {
      setTimeout(() => {
        setActiveSessions(mockSessions)
        notification.success({
          message: '会话加载成功',
          description: `已加载 ${mockSessions.length} 个活跃会话`,
          placement: 'topRight'
        })
      }, 1000)
    }

    loadActiveSessions()
  }, [])

  // 模拟定期更新数据
  useEffect(() => {
    const interval = setInterval(() => {
      // 模拟新消息或状态更新
      const randomSession = mockSessions[Math.floor(Math.random() * mockSessions.length)]
      if (Math.random() > 0.8) { // 20%概率模拟新消息
        handleNewMessage({
          id: `msg_${Date.now()}`,
          sessionId: randomSession.id,
          content: '这是一条模拟的新消息',
          type: 'text',
          sender: 'user',
          timestamp: Date.now()
        })
      }
    }, 10000) // 每10秒检查一次

    return () => clearInterval(interval)
  }, [handleNewMessage])

  return (
    <Layout className="customer-service-layout">
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        className="customer-service-sider"
      >
        <div className="logo">
          <div className="logo-icon">
            <MessageOutlined />
          </div>
          {!collapsed && (
            <div className="logo-text">
              <div className="title">智能客服</div>
              <div className="subtitle">Customer Service</div>
            </div>
          )}
        </div>
        
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedMenu]}
          items={menuItems}
          onClick={({ key }) => setSelectedMenu(key)}
        />
        
        {/* 实时状态 */}
        {!collapsed && (
          <div className="realtime-status">
            <div className="status-item">
              <PhoneOutlined className="status-icon" />
              <span>排队: {queueCount}</span>
            </div>
            <div className="status-item">
              <GlobalOutlined className="status-icon" />
              <span>活跃: {activeSessions.length}</span>
            </div>
          </div>
        )}
      </Sider>

      <Layout>
        {/* 头部 */}
        <Header className="customer-service-header">
          <div className="header-left">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="trigger"
            />
            
            <div className="connection-status">
              <div className={`connection-dot ${isConnected ? 'connected' : 'disconnected'}`}></div>
              <span className="connection-text">
                {isConnected ? '已连接' : '连接中...'}
              </span>
            </div>
          </div>

          <div className="header-right">
            <Space size={16}>
              {/* 通知 */}
              <Dropdown
                menu={{
                  items: notifications.map((notif, index) => ({
                    key: index,
                    label: (
                      <div className="notification-item">
                        <div className="notification-title">{notif.title}</div>
                        <div className="notification-content">{notif.content}</div>
                        <div className="notification-time">{formatTime(notif.timestamp)}</div>
                      </div>
                    )
                  }))
                }}
                placement="bottomRight"
                trigger={['click']}
              >
                <Badge count={notifications.length} size="small">
                  <Button type="text" icon={<BellOutlined />} />
                </Badge>
              </Dropdown>

              {/* 状态切换 */}
              <Dropdown menu={statusMenu} placement="bottomRight">
                <Button type="text" className="status-button">
                  <div className={`status-dot status-${agentStatus}`}></div>
                  {!collapsed && (
                    <span className="status-text">
                      {agentStatus === 'online' ? '在线' : agentStatus === 'busy' ? '忙碌' : '离线'}
                    </span>
                  )}
                </Button>
              </Dropdown>

              {/* 用户信息 */}
              <Dropdown menu={userMenu} placement="bottomRight">
                <Button type="text" className="user-button">
                  <Avatar
                    size="small"
                    src={agentInfo?.avatar}
                    icon={<UserOutlined />}
                  />
                  {!collapsed && (
                    <span className="user-name">{agentInfo?.name || '客服'}</span>
                  )}
                </Button>
              </Dropdown>
            </Space>
          </div>
        </Header>

        {/* 内容区域 */}
        <Content className="customer-service-content">
          {renderContent()}
        </Content>
      </Layout>

      {/* 知识库搜索弹窗 */}
      <Modal
        title="知识库搜索"
        open={showKnowledgeModal}
        onCancel={() => setShowKnowledgeModal(false)}
        footer={null}
        width={800}
      >
        <KnowledgeBase />
      </Modal>
    </Layout>
  )
}

export default CustomerService